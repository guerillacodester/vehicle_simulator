"""
database.py
-----------
SQLAlchemy engine + session factory with SSH tunneling.
Uses config.ini for DB host/port/default_db and .env for credentials.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import sys
import os
from pathlib import Path

# Add project root and scripts to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "scripts"))

from scripts.config_loader import load_config
import paramiko, socket, threading
from dotenv import load_dotenv

# Load .env
load_dotenv()

Base = declarative_base()
SessionLocal = None

class Forwarder(threading.Thread):
    daemon = True
    def __init__(self, transport, local_port, remote_host, remote_port):
        super().__init__()
        self.transport = transport
        self.local_port = local_port
        self.remote_host = remote_host
        self.remote_port = remote_port
        self.sock = None
        self._stop = threading.Event()

    def run(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("127.0.0.1", self.local_port))
        self.sock.listen(1)
        while not self._stop.is_set():
            try:
                client, _ = self.sock.accept()
                chan = self.transport.open_channel(
                    "direct-tcpip",
                    (self.remote_host, self.remote_port),
                    client.getsockname(),
                )
                threading.Thread(target=self._pipe, args=(client, chan), daemon=True).start()
                threading.Thread(target=self._pipe, args=(chan, client), daemon=True).start()
            except Exception:
                break

    def _pipe(self, src, dst):
        try:
            while True:
                data = src.recv(1024)
                if not data:
                    break
                dst.sendall(data)
        except Exception:
            pass
        finally:
            src.close()
            dst.close()

    def stop(self):
        self._stop.set()
        if self.sock:
            self.sock.close()

def init_engine():
    global SessionLocal

    cfg = load_config()
    
    # Use our existing config structure
    ssh_cfg = cfg.get("SSH", {})
    db_cfg = cfg.get("DATABASE", {})

    # SSH configuration
    ssh_host = ssh_cfg.get("host", "arknetglobal.com")
    ssh_port = int(ssh_cfg.get("port", 22))
    ssh_user = ssh_cfg.get("user", "david")
    ssh_pass = os.getenv("SSH_PASS", "Cabbyminnie5!")

    # Database configuration
    db_user = os.getenv("DB_USER", "david")
    db_pass = os.getenv("DB_PASS", "Ga25w123!")
    db_host = db_cfg.get("host", "localhost")
    db_port = int(db_cfg.get("port", 5432))
    db_name = db_cfg.get("default_db", "arknettransit")
    local_port = int(db_cfg.get("local_port", 6543))

    # SSH connection
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(ssh_host, port=ssh_port, username=ssh_user, password=ssh_pass)

    # Tunnel
    forwarder = Forwarder(ssh_client.get_transport(), local_port, db_host, db_port)
    forwarder.start()

    # Engine
    DATABASE_URL = f"postgresql+psycopg2://{db_user}:{db_pass}@127.0.0.1:{local_port}/{db_name}"
    engine = create_engine(DATABASE_URL, echo=False, future=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    return engine

# Additional helper functions for migrations
def get_session():
    """Get a database session"""
    if not SessionLocal:
        init_engine()
    return SessionLocal()

def get_engine():
    """Get the database engine"""
    return init_engine()
