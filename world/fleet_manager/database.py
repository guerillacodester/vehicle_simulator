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
sys.path.insert(0, str(project_root / "world" / "fleet_manager" / "scripts"))

try:
    from .scripts.config_loader import load_config
except ImportError:
    # When called from alembic, use absolute import
    from scripts.config_loader import load_config
import sshtunnel
from dotenv import load_dotenv

# Monkey patch to fix paramiko 4.x DSSKey compatibility
def patch_paramiko_for_dss_compatibility():
    """Patch paramiko to handle missing DSSKey for compatibility with paramiko 4.x"""
    try:
        import paramiko
        # If DSSKey doesn't exist, create a dummy class to prevent import errors
        if not hasattr(paramiko, 'DSSKey'):
            class DummyDSSKey:
                @staticmethod
                def from_private_key_file(*args, **kwargs):
                    raise NotImplementedError("DSS keys are not supported in paramiko 4.x")
                @staticmethod  
                def from_private_key(*args, **kwargs):
                    raise NotImplementedError("DSS keys are not supported in paramiko 4.x")
            paramiko.DSSKey = DummyDSSKey
    except ImportError:
        pass

# Apply the patch
patch_paramiko_for_dss_compatibility()

# Load .env
load_dotenv()

Base = declarative_base()
SessionLocal = None
tunnel = None  # Global tunnel instance

def init_engine():
    global SessionLocal, tunnel

    try:
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

        # Create SSH tunnel using sshtunnel (with DSSKey patch applied)
        tunnel = sshtunnel.SSHTunnelForwarder(
            (ssh_host, ssh_port),
            ssh_username=ssh_user,
            ssh_password=ssh_pass,
            remote_bind_address=(db_host, db_port),
            local_bind_address=('127.0.0.1', local_port)
        )
        
        # Start the tunnel
        tunnel.start()        # Engine
        DATABASE_URL = f"postgresql+psycopg2://{db_user}:{db_pass}@127.0.0.1:{local_port}/{db_name}"
        engine = create_engine(DATABASE_URL, echo=False, future=True)
        SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
        return engine
        
    except Exception as e:
        print(f"Database connection failed: {e}")
        # Return None to indicate failure - calling code should handle this
        return None# Additional helper functions for migrations
def get_session():
    """Get a database session"""
    if not SessionLocal:
        init_engine()
    return SessionLocal()

def get_engine():
    """Get the database engine"""
    return init_engine()
