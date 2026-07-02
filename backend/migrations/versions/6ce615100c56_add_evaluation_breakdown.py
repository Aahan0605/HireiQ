"""add evaluation breakdown

Revision ID: 6ce615100c56
Revises: 5ce615100c55
Create Date: 2026-07-02 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6ce615100c56'
down_revision: Union[str, Sequence[str], None] = '5ce615100c55'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('candidates', sa.Column('evaluation_breakdown', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('candidates', 'evaluation_breakdown')
