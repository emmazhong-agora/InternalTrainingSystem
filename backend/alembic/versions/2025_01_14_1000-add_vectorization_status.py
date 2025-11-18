"""add_vectorization_status_to_videos

Revision ID: a1b2c3d4e5f6
Revises: 082a8ff9166f
Create Date: 2025-01-14 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '082a8ff9166f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add vectorization status fields to videos table
    op.add_column('videos', sa.Column('vectorization_status', sa.String(), nullable=False, server_default='pending'))
    op.add_column('videos', sa.Column('vectorization_error', sa.Text(), nullable=True))
    op.add_column('videos', sa.Column('vectorized_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    # Remove vectorization status fields from videos table
    op.drop_column('videos', 'vectorized_at')
    op.drop_column('videos', 'vectorization_error')
    op.drop_column('videos', 'vectorization_status')
