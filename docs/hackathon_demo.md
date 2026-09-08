# RESQ-NET College Hackathon Demonstration Script

This document provides a step-by-step presentation script to demonstrate the **RESQ-NET SOS-to-Robot Disaster Response System** during your college hackathon.

---

## 🚀 Step 1: System Overview & Architecture (1 Minute)

"Good morning judges! We are presenting **RESQ-NET**, an automated disaster response coordination system for multi-floor buildings.

In disaster scenarios, victim location and quick rescue dispatch save lives. RESQ-NET connects:
1. **Victim Mobile SOS Interface**: Captures real GPS and building location (Floor/Zone).
2. **FastAPI Priority & Navigation Control Engine**: Uses explainable priority scoring and manages 3 floors (9 rescue zones).
3. **Admin Rescue Operations Dashboard**: Features real-time 3-floor building map, route editor, software digital simulation, and live telemetry.
4. **6-Boolean Omni-Directional IoT Motor Controller**: Controls an ESP-12E 3-wheel omni-directional robot via sequential Boolean timing logic while enforcing strict single-direction motor safety."

---

## 📱 Step 2: Victim SOS Distress Submission (1 Minute)

1. Open `D:\FOR CAREER\PROJECTS\Omniboy\victim_app\index.html` in Chrome/Edge or smartphone browser.
2. Select **Floor**: `Floor 2` | **Zone**: `Zone 1`.
3. Select **Urgency**: `🔴 CRITICAL (Trapped / Injury)`.
4. Message: `"Trapped near window in room 204"`.
5. Click the Big Red **🚨 SOS BUTTON**.
6. **Point out to judges**:
   - The real-time rescue tracker appears immediately.
   - Initial status reads: `SOS Received at Rescue Operations`.

---

## 💻 Step 3: Admin Rescue Control Operations (2 Minutes)

1. Open `D:\FOR CAREER\PROJECTS\Omniboy\dashboard\index.html` in a separate browser window.
2. Observe the left panel: The new SOS request `INC-XXXX` appears at the top of the priority list with a high explainable score (e.g. `85.0`).
3. Click on the SOS incident.
4. **Point out to judges**:
   - The central 3-floor map automatically highlights **Floor 2 -> Zone 1** with a red `VICTIM LOCATED` marker.
   - The estimated position of the robot is clearly shown.

---

## 🛠️ Step 4: Admin Route Editor & Software Digital Simulation (2 Minutes)

1. On the Admin Dashboard, look at the **Admin Route Editor** panel.
2. Select `Floor 2` and `Zone 1`.
3. Highlight the predefined steps:
   - Step 1: `NORTH` (20 seconds)
   - Step 2: `CW` (30 seconds)
   - Step 3: `NORTH` (10 seconds)
   - Step 4: `STOP` (0 seconds)
4. Show how easy it is for an operator to add or modify step direction and duration. Click **[ Save Route ]**.
5. Click **[ 🎯 SIMULATE ROUTE ]**:
   - The digital software simulator runs a dry-run preview progress animation across the map.

---

## 🤖 Step 5: Real Robot Dispatch & 6-Boolean Motor Telemetry (2 Minutes)

1. Click **[ 🚀 DISPATCH REAL ROBOT ]**.
2. Observe the right panel **6-Boolean Directional Monitor**:
   - When Step 1 runs, `NORTH` turns **ON (ACTIVE)** with a green glow, while `SOUTH`, `NORTHWEST`, `SOUTHEAST`, `CW`, `CCW` remain strictly **OFF**.
   - When Step 2 runs, `NORTH` automatically turns **OFF** and `CW` turns **ON (ACTIVE)**.
3. Switch back to the Victim App window:
   - The status tracker has automatically updated to **`ResQ-OmniBot En-Route to Your Zone!`**.
4. Once all steps finish:
   - Victim App displays **`🚨 ROBOT HAS ARRIVED AT YOUR ZONE!`**.

---

## 🚨 Step 6: Universal Emergency STOP Safety Demonstration (1 Minute)

1. Click the red **[ 🚨 EMERGENCY STOP ]** button at the top header.
2. Point out that:
   - All 6 directional Booleans instantly reset to `false`.
   - The backend logs the emergency event.
   - Robot motor outputs are safely shut off.

---

## 🔌 Hardware ESP-12E Setup (Optional Physical Robot Demo)

1. Open `D:\FOR CAREER\PROJECTS\Omniboy\esp8266\resq_robot.ino` in Arduino IDE.
2. Update `WIFI_SSID`, `WIFI_PASSWORD`, and `SERVER_URL` with your laptop's local IP (e.g. `http://192.168.1.100:8000/api/iot/state`).
3. Upload sketch to ESP-12E NodeMCU.
4. Power omni-directional robot chassis via battery.
5. The ESP-12E polls `/api/iot/state` every 500ms and executes physical motor movements!
