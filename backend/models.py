from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, Text, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database import Base


class UserModel(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False, default="USER")  # USER, ADMIN
    created_at = Column(DateTime, default=datetime.utcnow)

    incidents = relationship("IncidentModel", back_populates="user")


class IncidentModel(Base):
    __tablename__ = "incidents"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    latitude = Column(Float, nullable=False, default=0.0)
    longitude = Column(Float, nullable=False, default=0.0)
    floor = Column(String, nullable=False, default="Floor 1")  # Floor 1, Floor 2, Floor 3
    zone = Column(String, nullable=False, default="Zone 1")    # Zone 1, Zone 2, Zone 3
    urgency = Column(String, nullable=False, default="MEDIUM") # CRITICAL, HIGH, MEDIUM, LOW
    message = Column(Text, nullable=True)
    priority_score = Column(Float, nullable=False, default=0.0)
    priority_reason = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="SOS_RECEIVED")  # SOS_RECEIVED, ADMIN_NOTIFIED, ROBOT_DISPATCHED, ROBOT_EN_ROUTE, ROBOT_ARRIVED, RESOLVED
    timestamp = Column(DateTime, default=datetime.utcnow)
    photo_url = Column(Text, nullable=True)

    user = relationship("UserModel", back_populates="incidents")
    missions = relationship("MissionModel", back_populates="incident")


class RobotModel(Base):
    __tablename__ = "robots"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False, default="ResQ-OmniBot")
    status = Column(String, nullable=False, default="IDLE")  # ONLINE, OFFLINE, IDLE, MOVING, PAUSED, STOPPED, ERROR
    estimated_floor = Column(String, nullable=False, default="Floor 1")
    estimated_zone = Column(String, nullable=False, default="Zone 1")
    battery_pct = Column(Integer, nullable=False, default=100)
    last_heartbeat = Column(DateTime, default=datetime.utcnow)

    missions = relationship("MissionModel", back_populates="robot")


class RouteModel(Base):
    __tablename__ = "routes"

    id = Column(String, primary_key=True, index=True)
    floor = Column(String, nullable=False)  # Floor 1, Floor 2, Floor 3
    zone = Column(String, nullable=False)   # Zone 1, Zone 2, Zone 3
    name = Column(String, nullable=False)
    is_blocked = Column(Boolean, nullable=False, default=False)

    steps = relationship("RouteStepModel", back_populates="route", cascade="all, delete-orphan", order_by="RouteStepModel.sequence")
    missions = relationship("MissionModel", back_populates="route")


class RouteStepModel(Base):
    __tablename__ = "route_steps"

    id = Column(Integer, primary_key=True, autoincrement=True)
    route_id = Column(String, ForeignKey("routes.id"), nullable=False)
    sequence = Column(Integer, nullable=False)
    direction = Column(String, nullable=False)  # NORTH, SOUTH, NORTHWEST, SOUTHEAST, CW, CCW, STOP
    duration_sec = Column(Float, nullable=False, default=10.0)

    route = relationship("RouteModel", back_populates="steps")


class MissionModel(Base):
    __tablename__ = "missions"

    id = Column(String, primary_key=True, index=True)
    incident_id = Column(String, ForeignKey("incidents.id"), nullable=False)
    robot_id = Column(String, ForeignKey("robots.id"), nullable=False)
    route_id = Column(String, ForeignKey("routes.id"), nullable=False)
    status = Column(String, nullable=False, default="PENDING")  # PENDING, ACTIVE, PAUSED, COMPLETED, CANCELLED, FAILED
    current_step_index = Column(Integer, nullable=False, default=0)
    total_steps = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    incident = relationship("IncidentModel", back_populates="missions")
    robot = relationship("RobotModel", back_populates="missions")
    route = relationship("RouteModel", back_populates="missions")
    steps = relationship("MissionStepModel", back_populates="mission", cascade="all, delete-orphan", order_by="MissionStepModel.sequence")


class MissionStepModel(Base):
    __tablename__ = "mission_steps"

    id = Column(Integer, primary_key=True, autoincrement=True)
    mission_id = Column(String, ForeignKey("missions.id"), nullable=False)
    sequence = Column(Integer, nullable=False)
    direction = Column(String, nullable=False)  # NORTH, SOUTH, NORTHWEST, SOUTHEAST, CW, CCW, STOP
    duration_sec = Column(Float, nullable=False, default=10.0)
    status = Column(String, nullable=False, default="PENDING")  # PENDING, MOVING, COMPLETED, FAILED

    mission = relationship("MissionModel", back_populates="steps")


class RobotLogModel(Base):
    __tablename__ = "robot_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    robot_id = Column(String, nullable=False)
    event_type = Column(String, nullable=False)  # TELEMETRY, COMMAND, ACK, TIMEOUT, EMERGENCY_STOP, AUTH
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
