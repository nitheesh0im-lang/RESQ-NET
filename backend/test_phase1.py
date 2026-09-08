"""
Phase 1 Unit Verification Test Suite for RESQ-NET 3-Floor / 9-Zone System
Tests Database Initialization, User & Admin Auth, SOS Creation, 9-Zone Routes, and 6-Boolean IoT Controller.
"""

import unittest
from datetime import datetime

from database import init_db, SessionLocal
from models import UserModel, IncidentModel, RobotModel, RouteModel, RouteStepModel, MissionModel, MissionStepModel
from auth import hash_password, verify_password, create_access_token
from priority_engine import evaluate_priority
from route_manager import seed_default_9zone_routes, get_route_by_floor_zone, save_or_update_route
from iot_controller import iot_controller
from robot_manager import initialize_default_robot, emergency_stop_robot
from mission_engine import create_mission_for_incident, pause_mission, resume_mission


class TestPhase1System(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Initialize database schema."""
        init_db()

    def setUp(self):
        self.db = SessionLocal()
        # Clean tables in child-to-parent order for repeatable tests
        self.db.query(MissionStepModel).delete()
        self.db.query(MissionModel).delete()
        self.db.query(IncidentModel).delete()
        self.db.query(RouteStepModel).delete()
        self.db.query(RouteModel).delete()
        self.db.query(UserModel).delete()
        self.db.query(RobotModel).delete()
        self.db.commit()

        # Seed defaults
        initialize_default_robot(self.db, robot_id="R1")
        seed_default_9zone_routes(self.db)

        # Seed test user & admin
        self.victim_user = UserModel(
            id="USR-V1", name="Test Victim", username="victim_test",
            password_hash=hash_password("user123"), role="USER"
        )
        self.admin_user = UserModel(
            id="USR-A1", name="Test Admin", username="admin_test",
            password_hash=hash_password("admin123"), role="ADMIN"
        )
        self.db.add_all([self.victim_user, self.admin_user])
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def test_01_user_authentication(self):
        """Verify user registration, password hashing, and JWT token generation."""
        self.assertTrue(verify_password("user123", self.victim_user.password_hash))
        self.assertFalse(verify_password("wrongpass", self.victim_user.password_hash))

        token = create_access_token({"sub": self.victim_user.id, "role": self.victim_user.role})
        self.assertIsNotNone(token)

    def test_02_seed_9zone_routes(self):
        """Verify that all 9 rescue zones have predefined routes in DB."""
        routes = self.db.query(RouteModel).all()
        self.assertEqual(len(routes), 9)

        # Verify F2-Z1 route
        f2z1 = get_route_by_floor_zone(self.db, "Floor 2", "Zone 1")
        self.assertIsNotNone(f2z1)
        self.assertEqual(len(f2z1.steps), 4)
        self.assertEqual(f2z1.steps[0].direction, "NORTH")
        self.assertEqual(f2z1.steps[0].duration_sec, 20.0)

    def test_03_iot_controller_safety_invariant(self):
        """Verify that 6-Boolean motor controller ONLY allows 1 direction active at a time."""
        # 1. Set NORTH
        state1 = iot_controller.set_direction("NORTH", "Floor 2", "Zone 1")
        self.assertTrue(state1["north"])
        self.assertFalse(state1["south"])
        self.assertFalse(state1["cw"])
        self.assertEqual(state1["active_direction"], "NORTH")

        # 2. Set CW
        state2 = iot_controller.set_direction("CW")
        self.assertFalse(state2["north"])  # NORTH must automatically reset to False
        self.assertTrue(state2["cw"])
        self.assertEqual(state2["active_direction"], "CW")

        # 3. Emergency STOP
        state_stop = iot_controller.stop_robot()
        self.assertFalse(state_stop["north"])
        self.assertFalse(state_stop["cw"])
        self.assertEqual(state_stop["active_direction"], "STOP")

    def test_04_admin_route_editor(self):
        """Verify Admin can update steps for F2-Z1 without modifying source code."""
        updated_steps = [
            {"sequence": 1, "direction": "NORTHWEST", "duration_sec": 12.0},
            {"sequence": 2, "direction": "CW", "duration_sec": 25.0},
            {"sequence": 3, "direction": "STOP", "duration_sec": 0.0}
        ]
        route = save_or_update_route(self.db, "Floor 2", "Zone 1", "Updated F2-Z1", updated_steps)
        self.assertEqual(len(route.steps), 3)
        self.assertEqual(route.steps[0].direction, "NORTHWEST")

    def test_05_sos_and_mission_compilation(self):
        """Verify SOS creation, mission compilation, and background execution dispatch."""
        sos = IncidentModel(
            id="INC-UNIT01",
            user_id="USR-V1",
            latitude=13.0827,
            longitude=80.2707,
            floor="Floor 2",
            zone="Zone 1",
            urgency="CRITICAL",
            message="Trapped in room",
            priority_score=85.0,
            priority_reason="Test reason",
            status="SOS_RECEIVED",
            timestamp=datetime.utcnow()
        )
        self.db.add(sos)
        self.db.commit()

        mission = create_mission_for_incident(self.db, "INC-UNIT01", "R1")
        self.assertIsNotNone(mission)
        self.assertEqual(mission.status, "ACTIVE")
        self.assertGreater(len(mission.steps), 0)

        # Pause mission
        paused = pause_mission(self.db, mission.id)
        self.assertEqual(paused.status, "PAUSED")
        self.assertEqual(iot_controller.get_state()["active_direction"], "STOP")


if __name__ == "__main__":
    unittest.main()
