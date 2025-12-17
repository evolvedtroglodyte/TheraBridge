"""Add authentication schema and refresh token tracking

Revision ID: 42ef48f739a4
Revises: 808b6192c57c
Create Date: 2025-12-17 09:01:37.557

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '42ef48f739a4'
down_revision: Union[str, Sequence[str], None] = '808b6192c57c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - no changes needed as authentication was added in previous migration."""
    # The authentication schema (users table, auth_sessions table) was already added
    # in migration 808b6192c57c. This migration is a placeholder for tracking.
    pass


def downgrade() -> None:
    """Downgrade schema."""
    # No downgrade needed as no changes were made
    pass
