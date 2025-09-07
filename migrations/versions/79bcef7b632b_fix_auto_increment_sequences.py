"""fix_auto_increment_sequences

Revision ID: 79bcef7b632b
Revises: 227d4cbd2e85
Create Date: 2025-09-07 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '79bcef7b632b'
down_revision: Union[str, Sequence[str], None] = '227d4cbd2e85'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Fix auto-increment sequences for all tables."""
    
    # Create sequences and set defaults for routes table
    op.execute("""
        DO $$
        BEGIN
            -- Create sequence if it doesn't exist
            IF NOT EXISTS (SELECT 1 FROM pg_sequences WHERE sequencename = 'routes_id_seq') THEN
                CREATE SEQUENCE routes_id_seq;
                ALTER TABLE routes ALTER COLUMN id SET DEFAULT nextval('routes_id_seq');
                ALTER SEQUENCE routes_id_seq OWNED BY routes.id;
                -- Set the sequence to the current max + 1
                PERFORM setval('routes_id_seq', COALESCE(MAX(id), 0) + 1, false) FROM routes;
            END IF;
        END
        $$;
    """)
    
    # Create sequences and set defaults for vehicles table
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_sequences WHERE sequencename = 'vehicles_id_seq') THEN
                CREATE SEQUENCE vehicles_id_seq;
                ALTER TABLE vehicles ALTER COLUMN id SET DEFAULT nextval('vehicles_id_seq');
                ALTER SEQUENCE vehicles_id_seq OWNED BY vehicles.id;
                PERFORM setval('vehicles_id_seq', COALESCE(MAX(id), 0) + 1, false) FROM vehicles;
            END IF;
        END
        $$;
    """)
    
    # Create sequences and set defaults for stops table
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_sequences WHERE sequencename = 'stops_id_seq') THEN
                CREATE SEQUENCE stops_id_seq;
                ALTER TABLE stops ALTER COLUMN id SET DEFAULT nextval('stops_id_seq');
                ALTER SEQUENCE stops_id_seq OWNED BY stops.id;
                PERFORM setval('stops_id_seq', COALESCE(MAX(id), 0) + 1, false) FROM stops;
            END IF;
        END
        $$;
    """)
    
    # Create sequences and set defaults for timetables table
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_sequences WHERE sequencename = 'timetables_id_seq') THEN
                CREATE SEQUENCE timetables_id_seq;
                ALTER TABLE timetables ALTER COLUMN id SET DEFAULT nextval('timetables_id_seq');
                ALTER SEQUENCE timetables_id_seq OWNED BY timetables.id;
                PERFORM setval('timetables_id_seq', COALESCE(MAX(id), 0) + 1, false) FROM timetables;
            END IF;
        END
        $$;
    """)


def downgrade() -> None:
    """Remove auto-increment sequences."""
    op.execute("ALTER TABLE routes ALTER COLUMN id DROP DEFAULT")
    op.execute("DROP SEQUENCE IF EXISTS routes_id_seq")
    
    op.execute("ALTER TABLE vehicles ALTER COLUMN id DROP DEFAULT")
    op.execute("DROP SEQUENCE IF EXISTS vehicles_id_seq")
    
    op.execute("ALTER TABLE stops ALTER COLUMN id DROP DEFAULT")
    op.execute("DROP SEQUENCE IF EXISTS stops_id_seq")
    
    op.execute("ALTER TABLE timetables ALTER COLUMN id DROP DEFAULT")
    op.execute("DROP SEQUENCE IF EXISTS timetables_id_seq")
