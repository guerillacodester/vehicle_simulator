from logging.config import fileConfig
import sys
import os

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import engine_from_config, create_engine
from sqlalchemy import pool
from config.database import get_ssh_tunnel, get_db_config
from dotenv import load_dotenv

from alembic import context

# Import all models
from models.gtfs import Base

# Load .env
load_dotenv()

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
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
    # Set up SSH tunnel and database connection
    tunnel = None
    try:
        # Start SSH tunnel
        tunnel = get_ssh_tunnel()
        tunnel.start()
        
        # Get database config with tunnel
        db_config = get_db_config(tunnel)
        
        # Create connection string
        connection_string = f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['dbname']}"
        
        # Override the config with our dynamic connection string
        config.set_main_option("sqlalchemy.url", connection_string)
        
        connectable = engine_from_config(
            config.get_section(config.config_ini_section, {}),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )

        with connectable.connect() as connection:
            context.configure(
                connection=connection, 
                target_metadata=target_metadata,
                compare_type=True,
                compare_server_default=True
            )

            with context.begin_transaction():
                context.run_migrations()
    finally:
        if tunnel:
            tunnel.stop()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
