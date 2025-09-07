from sshtunnel import SSHTunnelForwarder
from typing import Dict
import logging

# Disable paramiko logging
logging.getLogger('paramiko').setLevel(logging.WARNING)
# Disable cryptography deprecation warnings
logging.getLogger('cryptography').setLevel(logging.WARNING)

def get_ssh_tunnel() -> SSHTunnelForwarder:
    """Create SSH tunnel to database server"""
    return SSHTunnelForwarder(
        ('arknetglobal.com', 22),
        ssh_username='david',
        ssh_password='Cabbyminnie5!',
        remote_bind_address=('127.0.0.1', 5432),
        local_bind_address=('127.0.0.1', 6543),
        mute_exceptions=False
    )

def get_db_config(tunnel: SSHTunnelForwarder = None) -> Dict[str, str]:
    """Get database configuration using tunnel if provided"""
    return {
        "dbname": "arknettransit",
        "user": "david",           # Changed back to SSH username
        "password": "Ga25w123!", # Using SSH password for DB
        "host": "127.0.0.1",
        "port": str(tunnel.local_bind_port if tunnel else "5432")
    }