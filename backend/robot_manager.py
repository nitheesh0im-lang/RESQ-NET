from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models import RobotModel, RobotLogModel

HEARTBEAT_TIMEOUT_SECONDS = 5.0


def initialize_default_robot(db: Session, robot_id: str = "R1", name: str = "ResQ-OmniBot") -> RobotModel:
    """Ensures default rescue robot R1 exists in DB on startup."""
    robot = db.query(RobotModel).filter(RobotModel.id == robot_id).first()
    if not robot:
        robot = RobotModel(
            id=robot_id,
            name=name,
            status="IDLE",
            estimated_floor="Floor 1",
            estimated_zone="Zone 1",
            battery_pct=100,
            last_heartbeat=datetime.utcnow()
        )
        db.add(robot)
        db.commit()
        db.refresh(robot)

        log_event(db, robot_id, "SYSTEM", "Initialized default rescue robot R1 at Floor 1 -> Zone 1 (Estimated)")
    return robot


def log_event(db: Session, robot_id: str, event_type: str, message: str):
    """Log telemetry, command, ACK, or safety event."""
    log = RobotLogModel(
        robot_id=robot_id,
        event_type=event_type,
        message=message,
        timestamp=datetime.utcnow()
    )
    db.add(log)
    db.commit()


def check_robot_heartbeat(db: Session, robot_id: str = "R1") -> RobotModel:
    """Checks if robot communication timed out (> 5s). Automatically triggers safety stop."""
    robot = db.query(RobotModel).filter(RobotModel.id == robot_id).first()
    if not robot:
        return None

    now = datetime.utcnow()
    if robot.last_heartbeat and (now - robot.last_heartbeat).total_seconds() > HEARTBEAT_TIMEOUT_SECONDS:
        if robot.status not in ["OFFLINE", "STOPPED", "ERROR"]:
            robot.status = "OFFLINE"
            db.commit()
            log_event(db, robot_id, "TIMEOUT", f"Safety Watchdog: Robot heartbeat lost (> {HEARTBEAT_TIMEOUT_SECONDS}s). Status set to OFFLINE.")

    return robot


def update_robot_telemetry(
    db: Session,
    robot_id: str,
    status: str,
    estimated_floor: str = None,
    estimated_zone: str = None,
    battery_pct: int = None
) -> RobotModel:
    """Updates robot status, estimated building floor/zone, and heartbeat timestamp."""
    robot = db.query(RobotModel).filter(RobotModel.id == robot_id).first()
    if not robot:
        return None

    robot.status = status
    robot.last_heartbeat = datetime.utcnow()

    if estimated_floor:
        robot.estimated_floor = estimated_floor
    if estimated_zone:
        robot.estimated_zone = estimated_zone

    if battery_pct is not None:
        robot.battery_pct = battery_pct

    db.commit()
    db.refresh(robot)

    log_event(db, robot_id, "TELEMETRY", f"Status: {status} | Position (Estimated): {robot.estimated_floor} -> {robot.estimated_zone} | Battery: {robot.battery_pct}%")
    return robot


def emergency_stop_robot(db: Session, robot_id: str = "R1", reason: str = "Manual Emergency Stop") -> RobotModel:
    """Safety feature: Immediately sets robot status to STOPPED."""
    robot = db.query(RobotModel).filter(RobotModel.id == robot_id).first()
    if robot:
        robot.status = "STOPPED"
        db.commit()
        db.refresh(robot)
        log_event(db, robot_id, "EMERGENCY_STOP", f"EMERGENCY STOP TRIGGERED: {reason}")
    return robot
