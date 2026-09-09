"""
===============================================================================
RESQ-NET: Unified FastAPI Backend for SOS-to-Robot Disaster Response
===============================================================================
This main.py uses all modular files (database, models, auth, iot_controller,
route_manager, mission_engine, robot_manager, route_executor) so that:
  - The API JSON endpoints
  - The ESP8266 robot polling
  - The test suite
all share the SAME single system.
===============================================================================
"""

import os
import sys
import time
import socket
import uuid
import threading
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional

# Ensure backend folder is in Python search path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

# --- Import shared modular components ---
from database import Base, engine, SessionLocal, get_db, init_db
from models import (
    UserModel, IncidentModel, RobotModel,
    RouteModel, RouteStepModel,
    MissionModel, MissionStepModel, RobotLogModel
)
from auth import (
    hash_password, verify_password, create_access_token,
    get_current_user, require_admin
)
from schemas import (
    UserRegister, UserLogin, TokenResponse, UserResponse,
    SOSCreate, IncidentResponse, PriorityUpdateRequest,
    RouteCreate, RouteStepSchema, RouteResponse,
    IoTStateResponse,
    RobotResponse,
    MissionCreateRequest, MissionResponse,
)
from iot_controller import iot_controller, sim_controller
from priority_engine import evaluate_priority
from route_manager import seed_default_9zone_routes, get_route_by_floor_zone, save_or_update_route
from robot_manager import initialize_default_robot, emergency_stop_robot, log_event
from mission_engine import (
    create_mission_for_incident, pause_mission, resume_mission,
    pause_active_missions, resume_paused_missions, emergency_stop_all
)

from sqlalchemy.orm import Session

# =============================================================================
# FASTAPI APPLICATION
# =============================================================================
app = FastAPI(
    title="RESQ-NET Backend API",
    description="Unified Hackathon-Ready Disaster Response API",
    version="3.0.0"
)

allowed_origins_env = os.environ.get("ALLOWED_ORIGINS", "")
if allowed_origins_env:
    origins = [origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()]
    allow_credentials = True
else:
    origins = ["*"]
    allow_credentials = False

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# STARTUP: Initialize DB, Seed Data, Print Server Info
# =============================================================================
@app.on_event("startup")
def startup_event():
    # 1. Create all tables from the shared models
    init_db()

    db = SessionLocal()
    try:
        # 2. Seed default users (configurable via environment variables)
        seed_victim_user = os.environ.get("USER_USERNAME", "victim1")
        seed_victim_pass = os.environ.get("USER_PASSWORD", "user123")
        seed_admin_user = os.environ.get("ADMIN_USERNAME", "admin1")
        seed_admin_pass = os.environ.get("ADMIN_PASSWORD", "admin123")

        if not db.query(UserModel).filter(UserModel.username == seed_victim_user).first():
            db.add(UserModel(
                id="U1", name="Victim One", username=seed_victim_user,
                password_hash=hash_password(seed_victim_pass), role="USER"
            ))
        if not db.query(UserModel).filter(UserModel.username == seed_admin_user).first():
            db.add(UserModel(
                id="A1", name="Admin Operator", username=seed_admin_user,
                password_hash=hash_password(seed_admin_pass), role="ADMIN"
            ))
        db.commit()

        # 3. Seed 9-zone rescue routes
        seed_default_9zone_routes(db)

        # 4. Initialize default robot R1
        initialize_default_robot(db, robot_id="R1")

    finally:
        db.close()

    # 5. Print server info with detected IP
    try:
        ip = socket.gethostbyname(socket.gethostname())
    except Exception:
        ip = "127.0.0.1"
    print("\n=============================================================")
    print(f" RESQ-NET SERVER ONLINE!")
    print(f" Local Laptop IP: {ip}")
    print(f" Set SERVER_URL in resq_robot.ino to: http://{ip}:8000/api/iot/state")
    print(f" Dashboard UI: http://{ip}:8000/dashboard/")
    print(f" Victim SOS App: http://{ip}:8000/victim/")
    print(f" API Docs: http://{ip}:8000/docs")
    print("=============================================================\n")


# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.get("/")
def root():
    return {"message": "RESQ-NET Disaster Backend Server Active", "status": "ONLINE", "version": "3.0.0"}


# -----------------------------------------------------------------------------
# 1. AUTH APIs
# -----------------------------------------------------------------------------
@app.post("/api/auth/register", response_model=TokenResponse)
def register_user(payload: UserRegister, db: Session = Depends(get_db)):
    existing = db.query(UserModel).filter(UserModel.username == payload.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    user_id = f"USR-{uuid.uuid4().hex[:6].upper()}"
    user = UserModel(
        id=user_id,
        name=payload.name,
        username=payload.username,
        password_hash=hash_password(payload.password),
        role=payload.role.upper()
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": user.id, "role": user.role})
    return TokenResponse(
        access_token=token, token_type="bearer",
        user_id=user.id, name=user.name, role=user.role
    )


@app.post("/api/auth/login", response_model=TokenResponse)
def login_user(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.username == payload.username).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Invalid username or password")

    token = create_access_token({"sub": user.id, "role": user.role})
    return TokenResponse(
        access_token=token, token_type="bearer",
        user_id=user.id, name=user.name, role=user.role
    )


# -----------------------------------------------------------------------------
# 2. SOS INCIDENT APIs
# -----------------------------------------------------------------------------
@app.post("/api/sos", response_model=IncidentResponse)
def submit_sos(payload: SOSCreate, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    inc_id = f"INC-{uuid.uuid4().hex[:6].upper()}"
    score, level, reason = evaluate_priority(
        urgency_level=payload.urgency,
        timestamp=datetime.utcnow(),
        target_x=1, target_y=1
    )

    incident = IncidentModel(
        id=inc_id,
        user_id=current_user.id,
        latitude=payload.latitude or 0.0,
        longitude=payload.longitude or 0.0,
        floor=payload.floor,
        zone=payload.zone,
        urgency=payload.urgency.upper(),
        message=payload.message,
        photo_url=payload.photo_url,
        priority_score=score,
        priority_reason=reason,
        status="SOS_RECEIVED",
        timestamp=datetime.utcnow()
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return incident


@app.get("/api/incidents", response_model=List[IncidentResponse])
def list_incidents(db: Session = Depends(get_db)):
    return db.query(IncidentModel).order_by(IncidentModel.priority_score.desc()).all()


@app.get("/api/incidents/{incident_id}", response_model=IncidentResponse)
def get_incident(incident_id: str, db: Session = Depends(get_db)):
    inc = db.query(IncidentModel).filter(IncidentModel.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    return inc


@app.patch("/api/incidents/{incident_id}/status")
def update_incident_status(incident_id: str, new_status: str = Query(...), admin: UserModel = Depends(require_admin), db: Session = Depends(get_db)):
    inc = db.query(IncidentModel).filter(IncidentModel.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    inc.status = new_status.upper()
    db.commit()
    return {"id": inc.id, "status": inc.status}


@app.delete("/api/incidents/{incident_id}")
def delete_incident(incident_id: str, admin: UserModel = Depends(require_admin), db: Session = Depends(get_db)):
    inc = db.query(IncidentModel).filter(IncidentModel.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")

    # Clean up associated missions & mission steps
    missions = db.query(MissionModel).filter(MissionModel.incident_id == incident_id).all()
    for m in missions:
        db.query(MissionStepModel).filter(MissionStepModel.mission_id == m.id).delete()
        db.delete(m)

    db.delete(inc)
    db.commit()
    return {"status": "SUCCESS", "deleted_id": incident_id}


@app.delete("/api/incidents")
def clear_all_incidents(admin: UserModel = Depends(require_admin), db: Session = Depends(get_db)):
    db.query(MissionStepModel).delete()
    db.query(MissionModel).delete()
    db.query(IncidentModel).delete()
    db.commit()
    return {"status": "SUCCESS", "message": "All test incidents cleared"}


# -----------------------------------------------------------------------------
# 3. ROUTE MANAGER APIs
# -----------------------------------------------------------------------------
@app.get("/api/routes/{floor}/{zone}", response_model=RouteResponse)
def get_route(floor: str, zone: str, db: Session = Depends(get_db)):
    route = get_route_by_floor_zone(db, floor, zone)
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    return route


@app.get("/api/routes", response_model=List[RouteResponse])
def list_all_routes(db: Session = Depends(get_db)):
    return db.query(RouteModel).all()


@app.put("/api/routes/{floor}/{zone}", response_model=RouteResponse)
def update_route(floor: str, zone: str, payload: RouteCreate, admin: UserModel = Depends(require_admin), db: Session = Depends(get_db)):
    steps_data = [{"sequence": s.sequence, "direction": s.direction, "duration_sec": s.duration_sec} for s in payload.steps]
    route = save_or_update_route(db, floor, zone, payload.name, steps_data)
    return route


# -----------------------------------------------------------------------------
# 4. MISSION DISPATCH APIs
# -----------------------------------------------------------------------------
@app.post("/api/missions", response_model=MissionResponse)
def dispatch_mission(payload: MissionCreateRequest, admin: UserModel = Depends(require_admin), db: Session = Depends(get_db)):
    incident = db.query(IncidentModel).filter(IncidentModel.id == payload.incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    mission = create_mission_for_incident(db, payload.incident_id, payload.robot_id)
    if not mission:
        raise HTTPException(status_code=500, detail="Could not create mission (route or robot missing)")
    return mission


@app.get("/api/missions", response_model=List[MissionResponse])
def list_missions(db: Session = Depends(get_db)):
    return db.query(MissionModel).order_by(MissionModel.created_at.desc()).all()


@app.get("/api/missions/{mission_id}", response_model=MissionResponse)
def get_mission(mission_id: str, db: Session = Depends(get_db)):
    mission = db.query(MissionModel).filter(MissionModel.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    return mission


@app.post("/api/missions/pause")
def pause_any_mission_endpoint(admin: UserModel = Depends(require_admin), db: Session = Depends(get_db)):
    mission = pause_active_missions(db, "R1")
    if not mission:
        iot_controller.stop_robot()
        return {"status": "PAUSED", "message": "No active mission running, motors stopped."}
    return {"status": "PAUSED", "mission_id": mission.id}


@app.post("/api/missions/{mission_id}/pause")
def pause_mission_endpoint(mission_id: str, admin: UserModel = Depends(require_admin), db: Session = Depends(get_db)):
    mission = pause_mission(db, mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    return {"status": "PAUSED", "mission_id": mission.id}


@app.post("/api/missions/resume")
def resume_any_mission_endpoint(admin: UserModel = Depends(require_admin), db: Session = Depends(get_db)):
    mission = resume_paused_missions(db, "R1")
    if not mission:
        raise HTTPException(status_code=404, detail="No paused mission found to resume.")
    return {"status": "RESUMED", "mission_id": mission.id}


@app.post("/api/missions/{mission_id}/resume")
def resume_mission_endpoint(mission_id: str, admin: UserModel = Depends(require_admin), db: Session = Depends(get_db)):
    mission = resume_mission(db, mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    return {"status": "RESUMED", "mission_id": mission.id}


# -----------------------------------------------------------------------------
# 5. 6-BOOLEAN IOT POLLING API (Used by ESP-12E and Dashboard)
# -----------------------------------------------------------------------------
@app.get("/api/iot/state", response_model=IoTStateResponse)
def get_iot_state():
    """The ESP8266 polls this endpoint every 300ms to get the current motor direction."""
    return iot_controller.get_state()


@app.get("/api/iot/set/{direction}")
@app.post("/api/iot/set/{direction}")
def set_manual_direction(direction: str):
    """Manual direction control from dashboard or testing."""
    result = iot_controller.set_direction(direction.upper())
    return {"status": "SUCCESS", "active_direction": result["active_direction"], "iot_state": result}


# -----------------------------------------------------------------------------
# 5B. UNITY 3D SIMULATION API (Used by Unity Engine)
# -----------------------------------------------------------------------------
@app.get("/api/simulation/state", response_model=IoTStateResponse)
def get_simulation_state():
    """Unity 3D Engine polls this endpoint every 300ms during software simulation."""
    return sim_controller.get_state()


@app.get("/api/simulation/set/{direction}")
@app.post("/api/simulation/set/{direction}")
def set_simulation_direction(direction: str):
    """Dashboard simulation controller sets direction for Unity 3D engine."""
    result = sim_controller.set_direction(direction.upper())
    return {"status": "SUCCESS", "active_direction": result["active_direction"], "simulation_state": result}


# -----------------------------------------------------------------------------
# 6. ROBOT STATUS & EMERGENCY STOP APIs
# -----------------------------------------------------------------------------
@app.get("/api/robots/{robot_id}", response_model=RobotResponse)
def get_robot_status(robot_id: str, db: Session = Depends(get_db)):
    robot = db.query(RobotModel).filter(RobotModel.id == robot_id).first()
    if not robot:
        raise HTTPException(status_code=404, detail="Robot not found")
    return robot


@app.post("/api/robots/{robot_id}/stop")
@app.post("/api/emergency-stop")
def emergency_stop(robot_id: str = "R1", admin: UserModel = Depends(require_admin), db: Session = Depends(get_db)):
    """Universal Emergency Stop — cancels all active missions and locks all 6 motor booleans OFF permanently."""
    emergency_stop_all(db, robot_id)
    return {"status": "STOPPED", "message": "Universal Emergency Stop Executed — All 6 motor booleans locked OFF", "robot_id": robot_id}


# -----------------------------------------------------------------------------
# 7. MOUNT STATIC WEB APPS (Dashboard & Victim SOS App)
# -----------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
dashboard_path = BASE_DIR / "dashboard"
victim_app_path = BASE_DIR / "victim_app"

if dashboard_path.exists():
    app.mount("/dashboard", StaticFiles(directory=str(dashboard_path), html=True), name="dashboard")

if victim_app_path.exists():
    app.mount("/victim", StaticFiles(directory=str(victim_app_path), html=True), name="victim_app")
