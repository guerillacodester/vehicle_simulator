import sys
from pathlib import Path
from configparser import ConfigParser
from typing import Dict, Any

def load_config() -> Dict[str, Any]:
    # Look for config.ini in the config folder (one level up from scripts)
    base_folder = Path(__file__).resolve().parent.parent
    config_file = base_folder / "config" / "config.ini"

    if not config_file.exists():
        print(f"[ERROR] Missing required config.ini in folder: {base_folder / 'config'}", file=sys.stderr)
        sys.exit(1)

    parser = ConfigParser()
    parser.read(config_file, encoding="utf-8")

    if not parser.sections():
        print(f"[ERROR] config.ini must contain at least one section: {config_file}", file=sys.stderr)
        sys.exit(1)

    return {section: dict(parser.items(section)) for section in parser.sections()}
