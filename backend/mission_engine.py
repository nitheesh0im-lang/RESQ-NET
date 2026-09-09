import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from models import MissionModel, MissionStepModel, IncidentModel, RobotModel, RouteModel, RouteStepModel
from iot_controller import iot_controller
from route_executor import route_executor


def create_mission_for_incident(
    db: Session,
    incident_id: str,
    robot_id: str = "R1"
) -> Optional[MissionModel]:
    """Compiles a rescue mission from the incident's predefined 3-floor / 9-zone route and dispatches execution."""
    incident = db.query(IncidentModel).filter(IncidentModel.id == incident_id).first()
    robot = db.query(RobotModel).filter(RobotModel.id == robot_id).first()

    if not incident or not robot:
        return None

    # Find matching predefined route for floor & zone
    route = db.query(RouteModel).filter(
        RouteModel.floor == incident.floor,
        RouteModel.zone == incident.zone
    ).first()

    if not route:
        return None

    # Check if active mission exists
    active_mission = db.query(MissionModel).filter(
        MissionModel.robot_id == robot_id,
        MissionModel.status.in_(["ACTIVE", "PENDING"])
    ).first()

    if active_mission:
        active_mission.status = "PAUSED"
        db.commit()

    mission_id = f"MIS-{uuid.uuid4().hex[:6].upper()}"

    route_steps = db.query(RouteStepModel).filter(
        RouteStepModel.route_id == route.id
    ).order_by(RouteStepModel.sequence).all()

    mission = MissionModel(
        id=mission_id,
        incident_id=incident_id,
        robot_id=robot_id,
        route_id=route.id,
        status="ACTIVE",
        current_step_index=0,
        total_steps=len(route_steps),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(mission)
    db.commit()

    for r_step in route_steps:
        m_step = MissionStepModel(
            mission_id=mission_id,
            sequence=r_step.sequence,
            direction=r_step.direction,
            duration_sec=r_step.duration_sec,
            status="PENDING"
        )
        db.add(m_step)

    incident.status = "ROBOT_DISPATCHED"
    robot.status = "MOVING"
    db.commit()
    db.refresh(mission)

    # Start execution loop in background
    route_executor.start_mission_execution(mission_id)
    return mission


def pause_mission(db: Session, mission_id: str) -> Optional[MissionModel]:
    """Pauses active mission and activates universal emergency stop."""
    mission = db.query(MissionModel).filter(MissionModel.id == mission_id).first()
    if not mission:
        return None

    mission.status = "PAUSED"
    robot = db.query(RobotModel).filter(RobotModel.id == mission.robot_id).first()
    if robot:
        robot.status = "STOPPED"
    db.commit()
    iot_controller.stop_robot()
    return mission


def pause_active_missions(db: Session, robot_id: str = "R1") -> Optional[MissionModel]:
    """Pauses all active/pending missions for the given robot and stops motors."""
    active_missions = db.query(MissionModel).filter(
        MissionModel.robot_id == robot_id,
        MissionModel.status.in_(["ACTIVE", "PENDING"])
    ).all()

    if not active_missions:
        return None

    for m in active_missions:
        m.status = "PAUSED"

    robot = db.query(RobotModel).filter(RobotModel.id == robot_id).first()
    if robot:
        robot.status = "STOPPED"

    db.commit()
    iot_controller.stop_robot()
    return active_missions[0]


def resume_mission(db: Session, mission_id: str) -> Optional[MissionModel]:
    """Resumes paused mission and restarts background executor thread."""
    mission = db.query(MissionModel).filter(MissionModel.id == mission_id).first()
    if not mission:
        return None

    mission.status = "ACTIVE"
    robot = db.query(RobotModel).filter(RobotModel.id == mission.robot_id).first()
    if robot:
        robot.status = "MOVING"
    db.commit()

    route_executor.start_mission_execution(mission_id)
    return mission


def resume_paused_missions(db: Session, robot_id: str = "R1") -> Optional[MissionModel]:
    """Resumes any paused missions for the given robot."""
    paused_mission = db.query(MissionModel).filter(
        MissionModel.robot_id == robot_id,
        MissionModel.status == "PAUSED"
    ).order_by(MissionModel.updated_at.desc()).first()

    if not paused_mission:
        return None

    paused_mission.status = "ACTIVE"
    robot = db.query(RobotModel).filter(RobotModel.id == robot_id).first()
    if robot:
        robot.status = "MOVING"
    db.commit()

    route_executor.start_mission_execution(paused_mission.id)
    return paused_mission


def emergency_stop_all(db: Session, robot_id: str = "R1"):
    """Emergency Stop: Cancels all active/pending/paused missions AND locks all 6 booleans OFF."""
    active_missions = db.query(MissionModel).filter(
        MissionModel.robot_id == robot_id,
        MissionModel.status.in_(["ACTIVE", "PENDING", "PAUSED"])
    ).all()

    for m in active_missions:
        m.status = "CANCELLED"

    robot = db.query(RobotModel).filter(RobotModel.id == robot_id).first()
    if robot:
        robot.status = "STOPPED"

    db.commit()
    iot_controller.stop_robot()
    return robot
