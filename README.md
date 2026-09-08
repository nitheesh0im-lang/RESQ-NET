# RESQ-NET: SOS-to-Robot Disaster Response System

**RESQ-NET** is a disaster-response coordination platform for multi-floor buildings (3 Floors / 9 Rescue Zones) connecting victim emergency distress signals, automated explainable priority scoring, centralized rescue mission dispatching, admin route planning, and sequential 6-Boolean motor control execution for an ESP-12E 3-wheel omni-directional robot.

---

## 🏗️ Project Architecture

```
D:\FOR CAREER\PROJECTS\Omniboy/
├── backend/
│   ├── main.py              # FastAPI Application REST APIs
│   ├── database.py          # SQLite Database Setup (resq_net.db)
│   ├── models.py            # SQLAlchemy Models (User, Incident, Robot, Route, Mission, etc.)
│   ├── schemas.py           # Pydantic Schemas for Validation
│   ├── auth.py              # User & Admin JWT Authentication
│   ├── iot_controller.py    # 6-Boolean Directional Motor Controller & Invariant
│   ├── priority_engine.py   # Priority Scoring Engine
│   ├── route_manager.py     # 3-Floor / 9-Zone Route Manager & Editor
│   ├── route_executor.py    # Sequential Step Execution Loop
│   ├── mission_engine.py    # Rescue Mission Dispatch Engine
│   ├── test_phase1.py       # Automated Verification Unit Tests
│   └── requirements.txt     # Python Dependencies
├── dashboard/               # Admin Rescue Control Center (HTML/CSS/JS)
│   ├── index.html
│   ├── style.css
│   └── app.js
├── victim_app/              # Victim SOS Emergency Application (HTML/CSS/JS)
│   ├── index.html
│   ├── style.css
│   └── app.js
├── esp8266/                 # ESP-12E Omni Robot Firmware
│   └── resq_robot.ino       # Arduino C++ Firmware Sketch
├── docs/                    # Documentation & Presentation Guides
│   └── hackathon_demo.md    # Step-by-Step Hackathon Presentation Script
└── README.md
```

---

## ⚡ How to Run the System

### 1. Launch FastAPI Backend Server
```powershell
cd "D:\FOR CAREER\PROJECTS\Omniboy\backend"
.\venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000
```
- Backend APIs: **[http://127.0.0.1:8000](http://127.0.0.1:8000)**
- Interactive API Docs: **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**

### 2. Open Admin Rescue Operations Dashboard
Open `D:\FOR CAREER\PROJECTS\Omniboy\dashboard\index.html` in Chrome or Edge.

### 3. Open Victim Emergency SOS Mobile App
Open `D:\FOR CAREER\PROJECTS\Omniboy\victim_app\index.html` in Chrome/Edge or smartphone browser.

---

## 🔑 Pre-Seeded Hackathon Credentials

| Role | Username | Password |
| :--- | :--- | :--- |
| **USER / VICTIM** | `victim1` | `user123` |
| **ADMIN / OPERATOR** | `admin1` | `admin123` |

---

## 🤖 6-Boolean Motor Controller Logic

The IoT controller interface (`iot_controller.py` & `/api/iot/state`) enforces that **only one directional Boolean is active at any time**:
- `north`: Move forward
- `south`: Move backward
- `northwest`: Diagonal left
- `southeast`: Diagonal right
- `cw`: Spin Clockwise
- `ccw`: Spin Counter-Clockwise
- `STOP` (All false): Universal Emergency Stop / Step Idle

---

## 📜 Presentation Guide
Read [`docs/hackathon_demo.md`](file:///D:/FOR%20CAREER/PROJECTS/Omniboy/docs/hackathon_demo.md) for the complete 10-step demo script.
