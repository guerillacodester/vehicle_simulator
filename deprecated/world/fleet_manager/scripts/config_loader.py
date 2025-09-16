"""
Config Loader for Fleet Manager
------------------------------
Minimal config loader to support fleet_manager functionality.
"""

import os
from pathlib import Path

def load_config():
    """
    Load configuration for fleet_manager.
    Returns a config dictionary compatible with fleet_manager expectations.
    """
    config = {
        "SSH": {
            "host": os.getenv("SSH_HOST", "arknetglobal.com"),
            "port": int(os.getenv("SSH_PORT", "22")),
            "user": os.getenv("SSH_USER", "david"),
        },
        "DATABASE": {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": int(os.getenv("DB_PORT", "5432")),
            "name": os.getenv("DB_NAME", "arknet_db"),
            "user": os.getenv("DB_USER", "arknet_user"),
            "password": os.getenv("DB_PASSWORD", ""),
        }
    }
    
    return config
