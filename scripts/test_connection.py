import sys
import os
import paramiko
import psycopg2
from sshtunnel import BaseSSHTunnelForwarderError

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

from config.database import get_ssh_tunnel, get_db_config

def test_connection():
    tunnel = None
    try:
        print("Starting SSH tunnel...")
        tunnel = get_ssh_tunnel()
        tunnel.start()
        
        print(f"Tunnel established on local port {tunnel.local_bind_port}")
        
        print("Testing database connection...")
        conn = psycopg2.connect(**get_db_config(tunnel))
        print("Database connection successful!")
        conn.close()
        
    except BaseSSHTunnelForwarderError as e:
        print(f"SSH tunnel error: {e}")
    except paramiko.SSHException as e:
        print(f"SSH authentication error: {e}")
    except psycopg2.Error as e:
        print(f"Database connection error: {e}")
    finally:
        if tunnel and tunnel.is_active:
            print("Closing tunnel...")
            tunnel.stop()

if __name__ == "__main__":
    test_connection()