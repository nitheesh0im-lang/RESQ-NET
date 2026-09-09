import os
import threading
from typing import Dict, Any

# Configurable API key (can be passed via env or user key)
IOT_API_KEY = os.environ.get("IOT_API_KEY", "6915c48d430f3deb738a6bbeecc8f817f0041b1f6785a76c5d054831b14dd8ed")

class IoTController:
    """
    6-Boolean Motor Direction Controller abstraction for ESP-12E omni-directional robot.
    Guarantees that ONLY ONE directional Boolean is active at any given moment.
    """
    def __init__(self):
        self._lock = threading.Lock()
        self.north = False
        self.south = False
        self.northwest = False
        self.southeast = False
        self.cw = False
        self.ccw = False
        self.active_direction = "STOP"
        self.estimated_floor = "Floor 1"
        self.estimated_zone = "Zone 1"
        self.battery_pct = 100

    def stop_robot(self) -> Dict[str, Any]:
        """Universal Emergency STOP: Resets all 6 movement Booleans to False immediately."""
        with self._lock:
            self.north = False
            self.south = False
            self.northwest = False
            self.southeast = False
            self.cw = False
            self.ccw = False
            self.active_direction = "STOP"
            return self.get_state()

    def set_direction(self, direction: str, floor: str = None, zone: str = None) -> Dict[str, Any]:
        """
        Sets a specific direction active while resetting all other directional Booleans to False.
        Enforces strict single-direction safety invariant.
        """
        with self._lock:
            # 1. Reset all fields to False first
            self.north = False
            self.south = False
            self.northwest = False
            self.southeast = False
            self.cw = False
            self.ccw = False

            dir_upper = direction.upper()
            if dir_upper == "NORTH":
                self.north = True
                self.active_direction = "NORTH"
            elif dir_upper == "SOUTH":
                self.south = True
                self.active_direction = "SOUTH"
            elif dir_upper == "NORTHWEST":
                self.northwest = True
                self.active_direction = "NORTHWEST"
            elif dir_upper == "SOUTHEAST":
                self.southeast = True
                self.active_direction = "SOUTHEAST"
            elif dir_upper == "CW":
                self.cw = True
                self.active_direction = "CW"
            elif dir_upper == "CCW":
                self.ccw = True
                self.active_direction = "CCW"
            else:
                self.active_direction = "STOP"

            if floor:
                self.estimated_floor = floor
            if zone:
                self.estimated_zone = zone

            return self.get_state()

    def get_state(self) -> Dict[str, Any]:
        """Returns the current 6-Boolean directional status."""
        return {
            "north": self.north,
            "south": self.south,
            "northwest": self.northwest,
            "southeast": self.southeast,
            "cw": self.cw,
            "ccw": self.ccw,
            "active_direction": self.active_direction,
            "estimated_floor": self.estimated_floor,
            "estimated_zone": self.estimated_zone,
            "battery_pct": self.battery_pct
        }


# Global Singleton Instances for physical hardware and Unity simulator
iot_controller = IoTController()
sim_controller = IoTController()
