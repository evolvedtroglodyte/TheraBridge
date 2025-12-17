"""create auth tables

Revision ID: 7cce0565853d
Revises:
Create Date: 2025-12-17 06:44:10.804009

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '7cce0565853d'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create users and sessions tables for authentication."""

    # Create UserRole enum type
    user_role_enum = postgresql.ENUM('THERAPIST', 'PATIENT', 'ADMIN', name='userrole', create_type=True)
    user_role_enum.create(op.get_bind(), checkfirst=True)

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('full_name', sa.String(), nullable=False),
        sa.Column('role', user_role_enum, nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )

    # Create unique constraint and index on email
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # Create sessions table for refresh tokens
    op.create_table(
        'sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('refresh_token', sa.String(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('is_revoked', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )

    # Create unique constraint on refresh_token
    op.create_unique_constraint('uq_sessions_refresh_token', 'sessions', ['refresh_token'])

    # Create foreign key with CASCADE delete
    op.create_foreign_key(
        'fk_sessions_user_id',
        'sessions',
        'users',
        ['user_id'],
        ['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    """Drop users and sessions tables."""
    # Drop tables in reverse order (sessions first due to foreign key)
    op.drop_table('sessions')
    op.drop_table('users')

    # Drop enum type
    user_role_enum = postgresql.ENUM('THERAPIST', 'PATIENT', 'ADMIN', name='userrole')
    user_role_enum.drop(op.get_bind(), checkfirst=True)
