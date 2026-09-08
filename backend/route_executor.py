import time
import threading
from sqlalchemy.orm import Session
from database import SessionLocal
from models import MissionModel, MissionStepModel, IncidentModel, RobotModel, RobotLogModel
from iot_controller import iot_controller


class RouteExecutor:
    """
    Background executor thread manager that steps through predefined routes.
    Enforces step execution cycle:
      Set Direction -> Wait duration_sec -> Set STOP -> Advance step.
    """
    def __init__(self):
        self.active_threads = {}

    def start_mission_execution(self, mission_id: str):
        """Spawns execution thread for a dispatched mission."""
        if mission_id in self.active_threads and self.active_threads[mission_id].is_alive():
            return  # Already executing

        t = threading.Thread(target=self._run_mission_loop, args=(mission_id,), daemon=True)
        self.active_threads[mission_id] = t
        t.start()

    def _run_mission_loop(self, mission_id: str):
        """Internal thread loop handling step timing and 6-Boolean state updates."""
        db: Session = SessionLocal()
        try:
            mission = db.query(MissionModel).filter(MissionModel.id == mission_id).first()
            if not mission:
                return

            incident = db.query(IncidentModel).filter(IncidentModel.id == mission.incident_id).first()
            robot = db.query(RobotModel).filter(RobotModel.id == mission.robot_id).first()

            robot.status = "MOVING"
            incident.status = "ROBOT_EN_ROUTE"
            db.commit()

            steps = db.query(MissionStepModel).filter(
                MissionStepModel.mission_id == mission_id
            ).order_by(MissionStepModel.sequence).all()

            for step in steps:
                # Re-fetch mission to check if PAUSED, CANCELLED, or STOPPED
                db.refresh(mission)
                if mission.status in ["PAUSED", "CANCELLED", "FAILED"]:
                    iot_controller.stop_robot()
                    robot.status = "STOPPED" if mission.status == "PAUSED" else "IDLE"
                    db.commit()
                    return

                # Update step status to MOVING
                step.status = "MOVING"
                mission.current_step_index = step.sequence - 1
                db.commit()

                # 1. Activate direction via IoT controller
                iot_controller.set_direction(
                    direction=step.direction,
                    floor=incident.floor,
                    zone=incident.zone
                )

                # 2. Wait for configured step duration in 0.5s ticks to allow pause responsiveness
                duration = step.duration_sec
                elapsed = 0.0
                while elapsed < duration:
                    time.sleep(0.5)
                    elapsed += 0.5
                    db.refresh(mission)
                    if mission.status in ["PAUSED", "CANCELLED", "FAILED"]:
                        iot_controller.stop_robot()
                        robot.status = "STOPPED" if mission.status == "PAUSED" else "IDLE"
                        db.commit()
                        return

                # 3. Stop after step completion
                iot_controller.stop_robot()
                step.status = "COMPLETED"
                db.commit()

            # All steps completed!
            mission.status = "COMPLETED"
            mission.current_step_index = len(steps)
            incident.status = "ROBOT_ARRIVED"
            robot.status = "IDLE"
            robot.estimated_floor = incident.floor
            robot.estimated_zone = incident.zone
            db.commit()

            # Log arrival
            log = RobotLogModel(
                robot_id=robot.id,
                event_type="SYSTEM",
                message=f"Mission {mission_id} COMPLETED. Robot arrived at estimated location: {incident.floor} -> {incident.zone}."
            )
            db.add(log)
            db.commit()

        except Exception as e:
            iot_controller.stop_robot()
            print(f"[RouteExecutor Error] {str(e)}")
        finally:
            db.close()


route_executor = RouteExecutor()
