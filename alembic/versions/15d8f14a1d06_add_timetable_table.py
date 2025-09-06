"""Add timetable table

Revision ID: 15d8f14a1d06
Revises: 
Create Date: 2025-09-06 02:08:57.585732

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '15d8f14a1d06'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'timetables',
        sa.Column('timetable_id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('vehicle_id', sa.UUID(), nullable=False),
        sa.Column('route_id', sa.UUID(), nullable=False),
        sa.Column('departure_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('arrival_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['vehicle_id'], ['vehicles.vehicle_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['route_id'], ['routes.route_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('timetable_id'),
    )

    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('timetables')

