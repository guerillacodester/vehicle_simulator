import json
import sys
from typing import Dict, Any

def load_assignments(path: str = "assignments.json") -> Dict[str, Dict[str, Any]]:
    """
    Load the assignments JSON file.
    Returns a dict keyed by vehicle ID.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict) or not data:
            raise ValueError("Assignments must be a non-empty JSON object.")
        return data
    except FileNotFoundError:
        sys.exit(f"Assignments file not found: {path}")
    except json.JSONDecodeError as e:
        sys.exit(f"Invalid JSON in assignments file '{path}': {e}")


def select_vehicle(assignments: Dict[str, Dict[str, Any]]) -> str:
    """
    Choose a vehicle deterministically from assignments:
      1) any with "default": true (if tie, lexicographically first)
      2) else any with "active": true (if tie, lexicographically first)
      3) else if only one, use it
      4) else lexicographically first ID
    """
    defaults = [vid for vid, cfg in assignments.items() if cfg.get("default") is True]
    if defaults:
        return sorted(defaults)[0]

    actives = [vid for vid, cfg in assignments.items() if cfg.get("active") is True]
    if actives:
        return sorted(actives)[0]

    vids = list(assignments.keys())
    if len(vids) == 1:
        return vids[0]
    return sorted(vids)[0]


def get_vehicle_config(path: str = "assignments.json") -> Dict[str, Any]:
    """
    Load assignments.json and return the selected vehicle config.
    """
    assignments = load_assignments(path)
    vehicle_id = select_vehicle(assignments)
    config = assignments[vehicle_id]
    config["vehicle_id"] = vehicle_id  # inject ID for reference
    return config
