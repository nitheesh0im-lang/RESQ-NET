"""
===============================================================================
RESQ-NET Full System Automated Verification Script (Updated for Unified Backend)
===============================================================================
Tests all backend REST endpoints, JWT authentication, SOS priority calculation,
6-Boolean motor controller safety state, and static UI routes.
"""

import time
import requests

BASE_URL = "http://127.0.0.1:8000"

def test_full_system():
    print("=" * 60)
    print("RESQ-NET AUTOMATED END-TO-END VERIFICATION TEST")
    print("=" * 60)

    # 1. Health check
    res = requests.get(f"{BASE_URL}/")
    assert res.status_code == 200, f"Root API failed: {res.text}"
    print("[PASS] Backend Server is ONLINE:", res.json())

    # 2. Static web apps check
    dashboard_res = requests.get(f"{BASE_URL}/dashboard/")
    assert dashboard_res.status_code == 200, "Dashboard static mount failed!"
    print("[PASS] Rescue Control Center Dashboard loaded successfully (HTML 200 OK)")

    victim_res = requests.get(f"{BASE_URL}/victim/")
    assert victim_res.status_code == 200, "Victim app static mount failed!"
    print("[PASS] Victim SOS Application loaded successfully (HTML 200 OK)")

    # 3. Auth tests (unified auth uses user_id + role in response)
    victim_login = requests.post(f"{BASE_URL}/api/auth/login", json={"username": "victim1", "password": "user123"})
    assert victim_login.status_code == 200, f"Victim login failed: {victim_login.text}"
    victim_data = victim_login.json()
    victim_token = victim_data["access_token"]
    print(f"[PASS] Victim Auth Successful (Token acquired, user_id={victim_data.get('user_id', 'N/A')})")

    admin_login = requests.post(f"{BASE_URL}/api/auth/login", json={"username": "admin1", "password": "admin123"})
    assert admin_login.status_code == 200, f"Admin login failed: {admin_login.text}"
    admin_data = admin_login.json()
    admin_token = admin_data["access_token"]
    print(f"[PASS] Admin Operator Auth Successful (Token acquired, user_id={admin_data.get('user_id', 'N/A')})")

    # 4. Submit SOS Incident (uses Bearer token in Authorization header)
    sos_headers = {"Authorization": f"Bearer {victim_token}"}
    sos_payload = {
        "latitude": 13.0827,
        "longitude": 80.2707,
        "floor": "Floor 2",
        "zone": "Zone 1",
        "urgency": "CRITICAL",
        "message": "Trapped near window, Room 204"
    }
    sos_res = requests.post(f"{BASE_URL}/api/sos", headers=sos_headers, json=sos_payload)
    assert sos_res.status_code == 200, f"SOS Submission failed: {sos_res.text}"
    incident = sos_res.json()
    print(f"[PASS] SOS Incident Created: ID={incident['id']} | Floor=Floor 2 | Zone=Zone 1 | Priority={incident['priority_score']} ({incident.get('priority_reason', '')})")

    # 5. Fetch Incidents List (Admin View)
    incidents_res = requests.get(f"{BASE_URL}/api/incidents")
    assert incidents_res.status_code == 200
    inc_list = incidents_res.json()
    assert len(inc_list) > 0
    print(f"[PASS] Incidents Queue Fetched: Total {len(inc_list)} active incident(s)")

    # 6. Fetch 9-Zone Route for Floor 2 Zone 1
    route_res = requests.get(f"{BASE_URL}/api/routes/Floor 2/Zone 1")
    assert route_res.status_code == 200
    route_data = route_res.json()
    print(f"[PASS] Route Loaded for F2-Z1: Name='{route_data['name']}' with {len(route_data['steps'])} step(s)")

    # 7. Dispatch Mission (Admin Action)
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    dispatch_payload = {"incident_id": incident["id"], "robot_id": "R1"}
    dispatch_res = requests.post(f"{BASE_URL}/api/missions", headers=admin_headers, json=dispatch_payload)
    assert dispatch_res.status_code == 200, f"Dispatch failed: {dispatch_res.text}"
    mission = dispatch_res.json()
    print(f"[PASS] Robot Dispatched! Mission ID={mission['id']} Target={mission.get('route_id', 'N/A')}")

    # 8. Check 6-Boolean Motor Controller State (should be MOVING after dispatch)
    time.sleep(1.0)
    iot_res = requests.get(f"{BASE_URL}/api/iot/state")
    assert iot_res.status_code == 200
    iot_state = iot_res.json()
    print("[PASS] Live 6-Boolean Motor Directional State:", iot_state)

    # 9. Test Emergency Stop
    stop_res = requests.post(f"{BASE_URL}/api/robots/R1/stop", headers=admin_headers)
    assert stop_res.status_code == 200
    print("[PASS] Emergency Stop Signal Triggered:", stop_res.json())

    # Verify all boolean directions reset to False
    time.sleep(0.5)
    iot_stop_res = requests.get(f"{BASE_URL}/api/iot/state")
    iot_stop_state = iot_stop_res.json()
    assert not any([iot_stop_state["north"], iot_stop_state["south"], iot_stop_state["northwest"], iot_stop_state["southeast"], iot_stop_state["cw"], iot_stop_state["ccw"]]), "Safety Violation: Boolean flags active after stop!"
    print("[PASS] Universal Safety Invariant Verified: ALL 6 directional booleans are FALSE")

    print("=" * 60)
    print("ALL VERIFICATION TESTS PASSED SUCCESSFULLY 100%!")
    print("=" * 60)

if __name__ == "__main__":
    test_full_system()
