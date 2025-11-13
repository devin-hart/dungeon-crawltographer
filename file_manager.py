import json
import os
from typing import Dict, Tuple

from data_models import Cell, IconType
import config

def save_map_data(filename: str, floors: Dict[int, Dict[Tuple[int, int], Cell]], current_floor: int, current_pos: Tuple[int, int], rotation: int):
    """Save the current map to a file."""
    if not os.path.isabs(filename):
        filename = os.path.join(os.getcwd(), filename)

    os.makedirs(os.path.dirname(filename), exist_ok=True)

    data = {
        "floors": {},
        "current_floor": current_floor,
        "current_pos": current_pos,
        "rotation": rotation
    }

    for floor, cells in floors.items():
        data["floors"][str(floor)] = {}
        for (x, y), cell in cells.items():
            if cell.explored:
                data["floors"][str(floor)][f"{x},{y}"] = {
                    "icon": cell.icon.value,
                    "label": cell.label,
                    "locked": cell.locked
                }

    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Map saved to {filename}")

def load_map_data(filename: str) -> Dict:
    """Load a map from a file and return its data."""
    if not os.path.isabs(filename):
        filename = os.path.join(os.getcwd(), filename)

    try:
        with open(filename, 'r') as f:
            data = json.load(f)

        loaded_data = {
            "floors": {},
            "current_floor": data.get("current_floor", 0),
            "current_pos": tuple(data.get("current_pos", (config.GRID_SIZE // 2, config.GRID_SIZE // 2))),
            "rotation": data.get("rotation", 0),
        }

        for floor_str, cells in data["floors"].items():
            floor = int(floor_str)
            loaded_data["floors"][floor] = {}
            for pos_str, cell_data in cells.items():
                x, y = map(int, pos_str.split(','))
                # Pass data as kwargs to the Cell constructor
                loaded_cell_data = {
                    "explored": True,
                    "icon": IconType(cell_data["icon"]),
                    "label": cell_data.get("label", ""),
                    "locked": cell_data.get("locked", False) # Default to False if not in file
                }
                loaded_data["floors"][floor][(x, y)] = Cell(**loaded_cell_data)

        print(f"Map loaded from {filename}")
        return loaded_data
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        print(f"Error loading map from {filename}: {e}")
        return None