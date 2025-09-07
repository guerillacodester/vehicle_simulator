from sshtunnel import SSHTunnelForwarder
from typing import Dict
import logging

# Configure logging
logging.getLogger('paramiko').setLevel(logging.WARNING)
logging.getLogger('cryptography').setLevel(logging.WARNING)

# Database connection settings
DB_NAME = "arknettransit"
DB_USER = "david"
DB_PASS = "Ga25w123!"

# SSH tunnel settings
SSH_HOST = "arknetglobal.com"
SSH_PORT = 22
SSH_USER = "david"
SSH_PASS = "Cabbyminnie5!"

def get_ssh_tunnel() -> SSHTunnelForwarder:
    """Create SSH tunnel to database server"""
    return SSHTunnelForwarder(
        (SSH_HOST, SSH_PORT),
        ssh_username=SSH_USER,
        ssh_password=SSH_PASS,
        remote_bind_address=('127.0.0.1', 5432),
        local_bind_address=('127.0.0.1', 6543),
        mute_exceptions=False
    )

def get_db_config(tunnel: SSHTunnelForwarder = None) -> Dict[str, str]:
    """Get database configuration using tunnel if provided"""
    return {
        "dbname": DB_NAME,
        "user": DB_USER,
        "password": DB_PASS,
        "host": "127.0.0.1",
        "port": str(tunnel.local_bind_port if tunnel else "5432")
    }