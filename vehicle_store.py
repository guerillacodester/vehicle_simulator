import json
import sys
from typing import Dict, Any

def load_assignments(path: str) -> Dict[str, Dict[str, Any]]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"[ERROR] Assignments file not found: {path}", file=sys.stderr)
        sys.exit(1)
    if not isinstance(data, dict) or not data:
        print(f"[ERROR] Invalid or empty assignments file: {path}", file=sys.stderr)
        sys.exit(1)
    return data

def select_vehicle(assignments: Dict[str, Dict[str, Any]]) -> str:
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

def get_vehicle_config(assignment_file: str) -> Dict[str, Any]:
    assignments = load_assignments(assignment_file)
    vid = select_vehicle(assignments)
    config = assignments[vid].copy()
    config["vehicle_id"] = vid
    return config
