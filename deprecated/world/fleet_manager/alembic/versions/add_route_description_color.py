"""Add description and color fields to route

Revision ID: route_desc_color
Revises: f26a154d527c
Create Date: 2025-01-09 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'route_desc_color'
down_revision: Union[str, Sequence[str], None] = 'f26a154d527c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add description and color fields to routes table
    op.add_column('routes', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('routes', sa.Column('color', sa.String(7), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove description and color fields from routes table
    op.drop_column('routes', 'color')
    op.drop_column('routes', 'description')