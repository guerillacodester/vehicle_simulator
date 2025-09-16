"""add_unique_constraint_gps_device_assignment

Revision ID: c9ea82bdfdcb
Revises: 2ec964fc3bef
Create Date: 2025-09-12 21:21:41.347237

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c9ea82bdfdcb'
down_revision: Union[str, Sequence[str], None] = '2ec964fc3bef'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add unique constraint to prevent same GPS device from being assigned to multiple vehicles
    op.create_unique_constraint(
        'uq_vehicles_assigned_gps_device_id', 
        'vehicles', 
        ['assigned_gps_device_id']
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Remove unique constraint
    op.drop_constraint('uq_vehicles_assigned_gps_device_id', 'vehicles', type_='unique')
