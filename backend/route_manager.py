from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from models import RouteModel, RouteStepModel


def seed_default_9zone_routes(db: Session):
    """Pre-populates the database with initial routes for all 9 building rescue zones."""
    default_routes_data = [
        {
            "floor": "Floor 1", "zone": "Zone 1", "name": "F1-Z1 Route",
            "steps": [
                {"sequence": 1, "direction": "NORTH", "duration_sec": 15.0},
                {"sequence": 2, "direction": "EAST", "duration_sec": 10.0},
                {"sequence": 3, "direction": "STOP", "duration_sec": 0.0}
            ]
        },
        {
            "floor": "Floor 1", "zone": "Zone 2", "name": "F1-Z2 Route",
            "steps": [
                {"sequence": 1, "direction": "NORTH", "duration_sec": 25.0},
                {"sequence": 2, "direction": "CW", "duration_sec": 15.0},
                {"sequence": 3, "direction": "STOP", "duration_sec": 0.0}
            ]
        },
        {
            "floor": "Floor 1", "zone": "Zone 3", "name": "F1-Z3 Route",
            "steps": [
                {"sequence": 1, "direction": "NORTHWEST", "duration_sec": 20.0},
                {"sequence": 2, "direction": "NORTH", "duration_sec": 15.0},
                {"sequence": 3, "direction": "STOP", "duration_sec": 0.0}
            ]
        },
        {
            "floor": "Floor 2", "zone": "Zone 1", "name": "F2-Z1 Route",
            "steps": [
                {"sequence": 1, "direction": "NORTH", "duration_sec": 20.0},
                {"sequence": 2, "direction": "CW", "duration_sec": 30.0},
                {"sequence": 3, "direction": "NORTH", "duration_sec": 10.0},
                {"sequence": 4, "direction": "STOP", "duration_sec": 0.0}
            ]
        },
        {
            "floor": "Floor 2", "zone": "Zone 2", "name": "F2-Z2 Route",
            "steps": [
                {"sequence": 1, "direction": "NORTH", "duration_sec": 15.0},
                {"sequence": 2, "direction": "SOUTHEAST", "duration_sec": 20.0},
                {"sequence": 3, "direction": "STOP", "duration_sec": 0.0}
            ]
        },
        {
            "floor": "Floor 2", "zone": "Zone 3", "name": "F2-Z3 Route",
            "steps": [
                {"sequence": 1, "direction": "NORTH", "duration_sec": 30.0},
                {"sequence": 2, "direction": "CCW", "duration_sec": 15.0},
                {"sequence": 3, "direction": "STOP", "duration_sec": 0.0}
            ]
        },
        {
            "floor": "Floor 3", "zone": "Zone 1", "name": "F3-Z1 Route",
            "steps": [
                {"sequence": 1, "direction": "NORTH", "duration_sec": 25.0},
                {"sequence": 2, "direction": "CW", "duration_sec": 20.0},
                {"sequence": 3, "direction": "NORTHWEST", "duration_sec": 15.0},
                {"sequence": 4, "direction": "STOP", "duration_sec": 0.0}
            ]
        },
        {
            "floor": "Floor 3", "zone": "Zone 2", "name": "F3-Z2 Route",
            "steps": [
                {"sequence": 1, "direction": "NORTH", "duration_sec": 35.0},
                {"sequence": 2, "direction": "STOP", "duration_sec": 0.0}
            ]
        },
        {
            "floor": "Floor 3", "zone": "Zone 3", "name": "F3-Z3 Route",
            "steps": [
                {"sequence": 1, "direction": "SOUTHEAST", "duration_sec": 25.0},
                {"sequence": 2, "direction": "CW", "duration_sec": 20.0},
                {"sequence": 3, "direction": "STOP", "duration_sec": 0.0}
            ]
        }
    ]

    for data in default_routes_data:
        route_id = f"RT-{data['floor'].replace(' ', '')}-{data['zone'].replace(' ', '')}"
        existing = db.query(RouteModel).filter(RouteModel.id == route_id).first()
        if not existing:
            route = RouteModel(
                id=route_id,
                floor=data["floor"],
                zone=data["zone"],
                name=data["name"],
                is_blocked=False
            )
            db.add(route)
            db.commit()

            for step_data in data["steps"]:
                step = RouteStepModel(
                    route_id=route_id,
                    sequence=step_data["sequence"],
                    direction=step_data["direction"],
                    duration_sec=step_data["duration_sec"]
                )
                db.add(step)
            db.commit()


def get_route_by_floor_zone(db: Session, floor: str, zone: str) -> Optional[RouteModel]:
    """Fetch route details for a given floor and zone."""
    return db.query(RouteModel).filter(
        RouteModel.floor == floor,
        RouteModel.zone == zone
    ).first()


def save_or_update_route(
    db: Session,
    floor: str,
    zone: str,
    name: str,
    steps_data: List[Dict[str, Any]]
) -> RouteModel:
    """Admin Route Editor: Creates or updates predefined steps for a rescue zone."""
    route_id = f"RT-{floor.replace(' ', '')}-{zone.replace(' ', '')}"
    route = db.query(RouteModel).filter(RouteModel.id == route_id).first()

    if not route:
        route = RouteModel(id=route_id, floor=floor, zone=zone, name=name, is_blocked=False)
        db.add(route)
    else:
        route.name = name

    db.commit()

    # Clear old steps
    db.query(RouteStepModel).filter(RouteStepModel.route_id == route_id).delete()
    db.commit()

    # Insert updated steps
    for seq, step_info in enumerate(steps_data, 1):
        step = RouteStepModel(
            route_id=route_id,
            sequence=seq,
            direction=step_info["direction"].upper(),
            duration_sec=float(step_info["duration_sec"])
        )
        db.add(step)

    db.commit()
    db.refresh(route)
    return route
