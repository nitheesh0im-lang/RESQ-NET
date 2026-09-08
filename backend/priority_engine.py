import math
from datetime import datetime


def calculate_grid_distance(x1: int, y1: int, x2: int, y2: int) -> float:
    """Manhattan distance on 2D grid."""
    return abs(x1 - x2) + abs(y1 - y2)


def evaluate_priority(
    urgency_level: str,
    timestamp: datetime,
    target_x: int,
    target_y: int,
    robot_x: int = 1,
    robot_y: int = 1
) -> tuple[float, str, str]:
    """
    Evaluates incident priority and produces an explainable score + breakdown.
    Returns: (score, calculated_priority_level, reasoning_str)
    """
    # 1. Base score from urgency selection
    urgency_map = {
        "CRITICAL": 85.0,
        "HIGH": 65.0,
        "MEDIUM": 45.0,
        "LOW": 25.0
    }
    base_score = urgency_map.get(urgency_level.upper(), 45.0)

    # 2. Waiting time calculation
    now = datetime.utcnow()
    wait_seconds = (now - timestamp).total_seconds() if timestamp else 0.0
    wait_minutes = round(wait_seconds / 60.0, 1)
    time_bonus = min(wait_minutes * 2.5, 30.0)  # max +30 points for waiting

    # 3. Estimated Distance penalty/bonus (grid distance in meters / cells)
    dist_cells = calculate_grid_distance(target_x, target_y, robot_x, robot_y)
    # Proximity bonus (closer targets get up to +10 points)
    dist_bonus = max(0.0, 10.0 - (dist_cells * 1.5))

    total_score = round(base_score + time_bonus + dist_bonus, 2)

    # Determine final level based on total score threshold
    if total_score >= 80.0:
        final_level = "CRITICAL"
    elif total_score >= 60.0:
        final_level = "HIGH"
    elif total_score >= 40.0:
        final_level = "MEDIUM"
    else:
        final_level = "LOW"

    # Explainable Reasoning String (Strictly honest, no fake AI)
    reasoning = (
        f"Base Urgency ({urgency_level.upper()}): {base_score} pts | "
        f"Wait Time ({wait_minutes} mins): +{round(time_bonus, 1)} pts | "
        f"Robot Grid Dist ({dist_cells} cells): +{round(dist_bonus, 1)} pts proximity bonus"
    )

    return total_score, final_level, reasoning
