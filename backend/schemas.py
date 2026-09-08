from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


# --- AUTH SCHEMAS ---

class UserRegister(BaseModel):
    name: str = Field(..., example="John Victim")
    username: str = Field(..., example="victim1")
    password: str = Field(..., example="user123")
    role: str = Field("USER", example="USER")  # USER, ADMIN


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    name: str
    role: str


class UserResponse(BaseModel):
    id: str
    name: str
    username: str
    role: str

    class Config:
        from_attributes = True


# --- SOS & INCIDENT SCHEMAS ---

class SOSCreate(BaseModel):
    latitude: Optional[float] = Field(0.0, description="Victim phone GPS Latitude")
    longitude: Optional[float] = Field(0.0, description="Victim phone GPS Longitude")
    floor: str = Field(..., example="Floor 2", description="Floor 1, Floor 2, Floor 3")
    zone: str = Field(..., example="Zone 1", description="Zone 1, Zone 2, Zone 3")
    urgency: str = Field("MEDIUM", example="CRITICAL", description="CRITICAL, HIGH, MEDIUM, LOW")
    message: Optional[str] = Field(None, example="Trapped under desk")
    photo_url: Optional[str] = None


class IncidentResponse(BaseModel):
    id: str
    user_id: str
    latitude: float
    longitude: float
    floor: str
    zone: str
    urgency: str
    message: Optional[str] = None
    priority_score: float
    priority_reason: Optional[str] = None
    status: str
    timestamp: datetime
    photo_url: Optional[str] = None

    class Config:
        from_attributes = True


class PriorityUpdateRequest(BaseModel):
    urgency: Optional[str] = None
    manual_override_score: Optional[float] = None


# --- ROUTE SCHEMAS ---

class RouteStepSchema(BaseModel):
    sequence: int
    direction: str  # NORTH, SOUTH, NORTHWEST, SOUTHEAST, CW, CCW, STOP
    duration_sec: float

    class Config:
        from_attributes = True


class RouteCreate(BaseModel):
    floor: str
    zone: str
    name: str
    steps: List[RouteStepSchema]


class RouteResponse(BaseModel):
    id: str
    floor: str
    zone: str
    name: str
    is_blocked: bool
    steps: List[RouteStepSchema] = []

    class Config:
        from_attributes = True


# --- IOT CONTROLLER SCHEMAS ---

class IoTStateResponse(BaseModel):
    north: bool = False
    south: bool = False
    northwest: bool = False
    southeast: bool = False
    cw: bool = False
    ccw: bool = False
    active_direction: str = "STOP"
    estimated_floor: str = "Floor 1"
    estimated_zone: str = "Zone 1"
    battery_pct: int = 100


# --- ROBOT & MISSION SCHEMAS ---

class RobotResponse(BaseModel):
    id: str
    name: str
    status: str
    estimated_floor: str
    estimated_zone: str
    battery_pct: int
    last_heartbeat: datetime

    class Config:
        from_attributes = True


class MissionStepResponse(BaseModel):
    id: int
    sequence: int
    direction: str
    duration_sec: float
    status: str

    class Config:
        from_attributes = True


class MissionCreateRequest(BaseModel):
    incident_id: str
    robot_id: str = "R1"


class MissionResponse(BaseModel):
    id: str
    incident_id: str
    robot_id: str
    route_id: str
    status: str
    current_step_index: int
    total_steps: int
    created_at: datetime
    steps: List[MissionStepResponse] = []

    class Config:
        from_attributes = True
