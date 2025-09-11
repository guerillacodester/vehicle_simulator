"""Add vehicle driver relationship

Revision ID: abc123456789
Revises: f26a154d527c
Create Date: 2025-09-11 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'abc123456789'
down_revision: Union[str, Sequence[str], None] = 'route_desc_color'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add assigned_driver_id column to vehicles table
    op.add_column('vehicles', 
        sa.Column('assigned_driver_id', 
                  postgresql.UUID(as_uuid=True), 
                  nullable=True))
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_vehicles_assigned_driver_id',
        'vehicles', 'drivers',
        ['assigned_driver_id'], ['driver_id'])


def downgrade() -> None:
    # Remove foreign key constraint
    op.drop_constraint('fk_vehicles_assigned_driver_id', 'vehicles', type_='foreignkey')
    
    # Remove assigned_driver_id column
    op.drop_column('vehicles', 'assigned_driver_id')