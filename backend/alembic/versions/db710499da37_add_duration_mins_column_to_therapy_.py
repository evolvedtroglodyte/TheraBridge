"""add duration_mins column to therapy_sessions

Revision ID: db710499da37
Revises: l2m3n4o5p6q7
Create Date: 2025-12-19 06:34:12.057239

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'db710499da37'
down_revision: Union[str, Sequence[str], None] = 'l2m3n4o5p6q7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add duration_mins column and populate from existing duration_seconds."""
    # Add duration_mins column (nullable)
    op.add_column('therapy_sessions', sa.Column(
        'duration_mins',
        sa.Integer(),
        nullable=True
    ))

    # Populate from existing duration_seconds
    # Use raw SQL to update existing rows
    # ROUND() ensures we get integer minutes from seconds
    op.execute("""
        UPDATE therapy_sessions
        SET duration_mins = ROUND(duration_seconds::numeric / 60)
        WHERE duration_seconds IS NOT NULL
    """)


def downgrade() -> None:
    """Remove duration_mins column."""
    op.drop_column('therapy_sessions', 'duration_mins')
