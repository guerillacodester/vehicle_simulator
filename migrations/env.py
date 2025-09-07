from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from config_loader import load_config
import paramiko
import socket
import threading
import os
from dotenv import load_dotenv

from alembic import context

# Import database SSH tunnel from database.py
from world.fleet_manager.database import Forwarder

# Load .env
load_dotenv()

# Load ssh config
config_ini = load_config()
db_config = config_ini['DATABASE']
ssh_config = config_ini['SSH']

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
from models import Base
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    # Set up SSH tunnel
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    # Connect to SSH server
    ssh_password = os.getenv('SSH_PASS')
    ssh_client.connect(
        ssh_config['host'],
        port=int(ssh_config.get('port', 22)),
        username=ssh_config['user'],
        password=ssh_password
    )
    
    # Create tunnel
    transport = ssh_client.get_transport()
    forwarder = Forwarder(
        transport,
        int(db_config['local_port']),
        db_config['host'],
        int(db_config['port'])
    )
    forwarder.start()

    try:
        connectable = engine_from_config(
            config.get_section(config.config_ini_section, {}),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )

        with connectable.connect() as connection:
            context.configure(
                connection=connection, target_metadata=target_metadata
            )

            with context.begin_transaction():
                context.run_migrations()
    finally:
        forwarder._stop.set()
        if forwarder.sock:
            forwarder.sock.close()
        ssh_client.close()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
