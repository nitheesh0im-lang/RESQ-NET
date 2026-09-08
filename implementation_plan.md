# RESQ-NET: SOS-to-Robot Disaster Response System — Master Implementation Plan

**Project Location**: `D:\FOR CAREER\PROJECTS\Omniboy`  
*(All backend services, database files, dashboard, victim app, and simulation modules will reside strictly within this directory. No scratch files will be placed on the C: drive).*

---

## 1. Executive Summary & Core Objective

**RESQ-NET** is a streamlined, reliable disaster response platform connecting victim SOS distress calls to a multi-floor, 9-zone omni-directional robot navigation engine.

### Key Innovations & Scope
- **3-Floor / 9-Zone Map Architecture**: Floors 1, 2, 3 with Zones 1, 2, 3 on each floor (`F1-Z1` through `F3-Z3`).
- **Role-Based Workflows**: Separate **Victim / User App** (SOS dispatch, status tracking) and **Admin / Rescue Control Center** (SOS monitoring, route editing, simulation, execution, emergency override).
- **Explainable Priority Engine**: Automated priority assignment (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`) with human-readable rationale based on urgency level and waiting time.
- **Dynamic Re-Prioritization & Emergency Override**: System alerts Admin when a higher-priority SOS arrives during an active mission, enabling mission pause and high-priority dispatch.
- **Strict Boolean API Controller (`iot_controller.py`)**: Interfacing with the 3-wheel omni robot using 6 directional fields (`north`, `south`, `northwest`, `southeast`, `cw`, `ccw`) with strict safety transitions: `ALL FALSE -> TARGET TRUE (Duration) -> ALL FALSE`.
- **Digital Mission Simulator**: Interactive digital twin simulation on a 3-floor visual map before physical dispatch.
- **Software-Based Replanning**: Admin marking corridors/zones as `BLOCKED` triggers alternative predefined route selection.
- **No Hardware GPS Claimed on Robot**: Victim phone provides GPS coordinates; robot location is explicitly labeled as **Estimated Robot Position**.

---

## 2. Project Directory Structure

```text
D:\FOR CAREER\PROJECTS\Omniboy\
├── backend/
│   ├── database.py          # SQLAlchemy SQLite connection & session management
│   ├── models.py            # Database tables (User, Incident, Robot, Route, RouteStep, Mission, MissionStep)
│   ├── schemas.py           # Pydantic schemas for API request/response validation
│   ├── auth.py              # JWT authentication & role-based access control (USER / ADMIN)
│   ├── priority_engine.py   # Rule-based explainable priority scoring
│   ├── route_manager.py     # Floor/Zone route CRUD, step sequencing & virtual replanning
│   ├── route_executor.py    # Sequential command timing & progression pipeline
│   ├── iot_controller.py    # Strict Boolean state machine for 6-direction motor API
│   ├── mission_engine.py    # Master state machine (DISPATCH, PAUSE, RESUME, STOP, REPLAN)
│   ├── main.py              # FastAPI REST endpoints & static file routing
│   ├── requirements.txt     # Python dependencies
│   └── resq_net.db          # SQLite Database
├── dashboard/               # Admin / Rescue Control Center UI (Responsive Web App)
├── victim_app/              # Victim / User SOS UI (Mobile-friendly Web App)
├── simulation/              # Digital Twin Robot Simulator Visualizer
├── esp8266/                 # ESP-12E / ESP8266 REST/WebSocket bridge documentation & sample configuration
├── docs/                    # Architecture documentation & API specs
└── README.md                # System documentation & setup guide
```

---

## 3. Database Schema (`models.py`)

1. **`User`**: `id`, `name`, `username`, `password_hash`, `role` (`USER` / `ADMIN`)
2. **`Incident`**: `id`, `user_id`, `latitude`, `longitude`, `floor` (1..3), `zone` (1..3), `urgency` (`CRITICAL`/`HIGH`/`MEDIUM`/`LOW`), `message`, `status` (`PENDING`, `NOTIFIED`, `DISPATCHED`, `EN_ROUTE`, `ARRIVED`), `timestamp`
3. **`Robot`**: `id`, `name`, `status` (`IDLE`, `MOVING`, `PAUSED`, `STOPPED`, `ARRIVED`), `estimated_floor`, `estimated_zone`, `last_heartbeat`
4. **`Route`**: `id`, `floor`, `zone`, `name` (e.g. `F2-Z1 Main Route`)
5. **`RouteStep`**: `id`, `route_id`, `sequence`, `direction` (`NORTH`, `SOUTH`, `NORTHWEST`, `SOUTHEAST`, `CW`, `CCW`, `STOP`), `duration_sec`
6. **`Mission`**: `id`, `incident_id`, `robot_id`, `status` (`CREATED`, `ACTIVE`, `PAUSED`, `COMPLETED`, `CANCELLED`), `current_step`
7. **`MissionStep`**: `id`, `mission_id`, `sequence`, `direction`, `duration_sec`, `status` (`PENDING`, `RUNNING`, `COMPLETED`)

---

## 4. Multi-Phase Development Roadmap

### Phase 1: Backend Core, Database & Authentication
- Initialize FastAPI app with SQLAlchemy SQLite database.
- Implement JWT Auth (`auth.py`) for `USER` and `ADMIN` roles.
- Define models, schemas, and password hashing.
- Expose `/api/auth/login` and `/api/sos` endpoints.

### Phase 2: 3-Floor / 9-Zone Route System
- Seed database with default 9 rescue zone routes (`F1-Z1` through `F3-Z3`).
- Build `route_manager.py` to allow Admin route creation, editing, step additions/deletions, and storing steps in database.
- Implement priority engine (`priority_engine.py`) calculating priorities (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`) with explainable reason logs.

### Phase 3: Admin / Rescue Control Center Dashboard
- Build responsive Admin UI in `dashboard/`:
  - **Live SOS Incident Queue**: Display victim location (GPS + Floor/Zone), urgency, message, priority ranking.
  - **3-Floor Interactive Map**: Switch between Floor 1, 2, and 3; render start point, zones, highlighted route, and estimated robot location.
  - **Route Editor Modal**: Create/edit route steps with visual order (`NORTH 20s` -> `CW 30s` -> `NORTH 10s` -> `STOP`).
  - **Mission Command Console**: Buttons for `SIMULATE`, `DISPATCH`, `PAUSE`, `RESUME`, `REPLAN`, and `EMERGENCY STOP`.
  - **Mission History Timeline**: Event-by-event timeline (`SOS RECEIVED` -> `ROBOT DISPATCHED` -> `STEP 1` -> `ARRIVED`).

### Phase 4: User / Victim SOS Application
- Build minimal, ultra-clean Victim UI in `victim_app/`:
  - Login screen.
  - Simple drop-downs for Floor (Floor 1..3) and Zone (Zone 1..3).
  - Optional Emergency Level & Message inputs.
  - Prominent `🚨 SEND SOS` trigger button.
  - Automatic HTML5 Geolocation API capture for phone GPS (`latitude`, `longitude`).
  - Real-time status progression tracker (`SOS SENT` -> `SOS RECEIVED` -> `ADMIN NOTIFIED` -> `ROBOT DISPATCHED` -> `ROBOT EN ROUTE` -> `ROBOT ARRIVED`).

### Phase 5: Boolean API Motor Controller (`iot_controller.py`)
- Implement 6-direction Boolean state machine: `north`, `south`, `northwest`, `southeast`, `cw`, `ccw`.
- Strict execution rules:
  1. Force ALL 6 fields to `false`.
  2. Set target field to `true`.
  3. Wait for `duration_sec`.
  4. Force ALL 6 fields to `false`.
- Universal Safety Stop method: Immediately sets all 6 fields to `false` on emergency stop, pause, or error.
- REST endpoint `/api/robots/boolean-state` returning current active Boolean map for ESP-12E polling/streaming.

### Phase 6: Digital Twin Robot Simulator
- Build route simulation mode in `simulation/`:
  - Admin presses `SIMULATE`.
  - Software robot moves across the 3-floor map step-by-step according to step directions & timing.
  - Visual step progress log: `START` -> `NORTH (20s)` -> `CW (30s)` -> `NORTH (10s)` -> `ARRIVED AT ZONE`.
  - Enables `[DISPATCH REAL ROBOT]` button upon simulator completion.

### Phase 7: Dynamic Re-Prioritization & Virtual Replanning
- Multi-SOS Handler: When a new `CRITICAL` SOS arrives while a lower priority mission is active, prompt Admin to `PAUSE CURRENT MISSION` and `DISPATCH CRITICAL MISSION`.
- Corridor Obstacle Replanning: Admin can toggle zone/corridor status to `BLOCKED`, allowing quick selection of alternative predefined routes.

### Phase 8: Hardware Integration Bridge & End-to-End Testing
- Prepare `esp8266/` code bridge documentation matching ESP-12E motor pins (`D5, D6`, `D3, D4`, `D0, D1`, speed 150).
- Comprehensive end-to-end testing of full workflow from SOS creation -> Admin dispatch -> Digital Twin/API execution -> Arrival acknowledgment.

---

## 5. Verification & Acceptance Criteria

1. **Strict Directory Isolation**: Every single line of code and configuration resides inside `D:\FOR CAREER\PROJECTS\Omniboy`.
2. **Boolean API Safety**: Verification that `iot_controller` never allows multiple movement fields to be true simultaneously.
3. **Role Security**: Verification that Victim role cannot access Admin route editing or robot dispatch endpoints.
4. **End-to-End Hackathon Demo Flow**:
   - Victim selects Floor 2, Zone 1 -> Press SOS -> Status shows "SOS SENT".
   - Admin receives notification -> Views F2-Z1 route -> Runs `SIMULATE` -> Clicks `DISPATCH`.
   - Backend executes step 1 (`NORTH`), step 2 (`CW`), step 3 (`NORTH`), step 4 (`STOP`).
   - Victim app and Admin dashboard display "ROBOT ARRIVED".

---

## Next Steps

> [!IMPORTANT]
> Awaiting your explicit approval on this Master Implementation Plan before starting **PHASE 1 (Backend Core, Database & Authentication)**.
