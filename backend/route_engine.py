import heapq
from typing import List, Tuple, Dict, Any, Optional

# Grid dimensions: 5x5 default
GRID_WIDTH = 5
GRID_HEIGHT = 5


def cell_name_to_coords(cell_name: str) -> Tuple[int, int]:
    """Converts cell string like 'B2' or 'D4' to (x, y) coordinates."""
    cell = cell_name.strip().upper()
    if len(cell) < 2:
        return (0, 0)
    row_char = cell[0]  # 'A', 'B', 'C', 'D', 'E'
    col_str = cell[1:]  # '1', '2', '3', '4', '5'

    y = ord(row_char) - ord('A')
    try:
        x = int(col_str) - 1
    except ValueError:
        x = 0

    x = max(0, min(GRID_WIDTH - 1, x))
    y = max(0, min(GRID_HEIGHT - 1, y))
    return (x, y)


def coords_to_cell_name(x: int, y: int) -> str:
    """Converts (x, y) coordinates to cell string like 'B2'."""
    row_char = chr(ord('A') + min(GRID_HEIGHT - 1, max(0, y)))
    col_num = min(GRID_WIDTH, max(1, x + 1))
    return f"{row_char}{col_num}"


def heuristic(a: Tuple[int, int], b: Tuple[int, int]) -> int:
    """Manhattan distance heuristic for grid pathfinding."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def plan_route(
    start: Tuple[int, int],
    target: Tuple[int, int],
    obstacles: List[Tuple[int, int]] = None
) -> List[Dict[str, Any]]:
    """
    A* (A-Star) Pathfinding algorithm for 2D disaster grid map.
    Returns sequential movement steps with estimated direction and distance.
    NOTE: Robot position and physical distance are ESTIMATED calibrated values.
    """
    if obstacles is None:
        obstacles = []

    start_x, start_y = start
    target_x, target_y = target

    # Bounds check
    start_x = max(0, min(GRID_WIDTH - 1, start_x))
    start_y = max(0, min(GRID_HEIGHT - 1, start_y))
    target_x = max(0, min(GRID_WIDTH - 1, target_x))
    target_y = max(0, min(GRID_HEIGHT - 1, target_y))

    if (start_x, start_y) == (target_x, target_y):
        return []

    obstacle_set = set(obstacles)
    if (target_x, target_y) in obstacle_set:
        # Target cell is blocked; pathfinding fails or reaches adjacent
        pass

    # Directions: (dx, dy, direction_name)
    # Note: Grid Y increases downwards (A=0, B=1, C=2, D=3, E=4)
    # Moving SOUTH means Y increases (+1), NORTH means Y decreases (-1)
    # Moving EAST means X increases (+1), WEST means X decreases (-1)
    neighbors_def = [
        (0, -1, "NORTH"),
        (0, 1, "SOUTH"),
        (1, 0, "EAST"),
        (-1, 0, "WEST")
    ]

    open_set = []
    heapq.heappush(open_set, (0, (start_x, start_y)))

    came_from: Dict[Tuple[int, int], Tuple[Tuple[int, int], str]] = {}
    g_score: Dict[Tuple[int, int], float] = {(start_x, start_y): 0.0}
    f_score: Dict[Tuple[int, int], float] = {(start_x, start_y): heuristic((start_x, start_y), (target_x, target_y))}

    found = False
    while open_set:
        _, current = heapq.heappop(open_set)

        if current == (target_x, target_y):
            found = True
            break

        for dx, dy, move_dir in neighbors_def:
            neighbor = (current[0] + dx, current[1] + dy)

            # Check grid boundaries
            if not (0 <= neighbor[0] < GRID_WIDTH and 0 <= neighbor[1] < GRID_HEIGHT):
                continue
            # Check obstacle
            if neighbor in obstacle_set:
                continue

            tentative_g = g_score[current] + 1.0

            if neighbor not in g_score or tentative_g < g_score[neighbor]:
                came_from[neighbor] = (current, move_dir)
                g_score[neighbor] = tentative_g
                f_score[neighbor] = tentative_g + heuristic(neighbor, (target_x, target_y))
                heapq.heappush(open_set, (f_score[neighbor], neighbor))

    if not found:
        return []  # Path blocked or impossible

    # Reconstruct path
    path_directions = []
    curr = (target_x, target_y)
    while curr in came_from:
        prev_node, move_dir = came_from[curr]
        path_directions.append(move_dir)
        curr = prev_node

    path_directions.reverse()

    # Consolidate consecutive movements in same direction or break into 1m step segments
    steps = []
    seq = 1
    for direction in path_directions:
        steps.append({
            "sequence": seq,
            "direction": direction,
            "distance_m": 1.0,  # Estimated 1.0 meter cell length
            "estimated_duration_sec": 2.5  # Estimated time per cell step
        })
        seq += 1

    return steps
