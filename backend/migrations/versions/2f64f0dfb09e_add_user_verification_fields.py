"""add_user_verification_fields

Revision ID: 2f64f0dfb09e
Revises: 9e920e6fe270
Create Date: 2026-06-10 20:31:33.116213

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2f64f0dfb09e'
down_revision: Union[str, Sequence[str], None] = '9e920e6fe270'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('is_verified', sa.Boolean(), nullable=True))
    op.add_column('users', sa.Column('verification_token', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('verification_token_expires', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('password_reset_token', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('password_reset_expires', sa.DateTime(), nullable=True))
    # Backfill existing users to be verified
    op.execute("UPDATE users SET is_verified = 1")


def downgrade() -> None:
    op.drop_column('users', 'password_reset_expires')
    op.drop_column('users', 'password_reset_token')
    op.drop_column('users', 'verification_token_expires')
    op.drop_column('users', 'verification_token')
    op.drop_column('users', 'is_verified')

