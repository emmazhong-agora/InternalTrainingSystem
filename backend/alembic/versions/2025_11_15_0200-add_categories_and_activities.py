"""Add category fields and user activities table

Revision ID: add_categories_activities
Revises: 65c482a68175
Create Date: 2025-11-15 02:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_categories_activities'
down_revision = '65c482a68175'
branch_labels = None
depends_on = None


def upgrade():
    # Add new fields to video_categories table
    with op.batch_alter_table('video_categories', schema=None) as batch_op:
        batch_op.add_column(sa.Column('icon', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('is_active', sa.Integer(), nullable=False, server_default='1'))

    # Create user_activities table
    op.create_table('user_activities',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('video_id', sa.Integer(), nullable=True),
        sa.Column('activity_type', sa.String(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=True),
        sa.Column('activity_data', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['video_id'], ['videos.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    with op.batch_alter_table('user_activities', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_user_activities_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_user_activities_user_id'), ['user_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_user_activities_video_id'), ['video_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_user_activities_activity_type'), ['activity_type'], unique=False)
        batch_op.create_index(batch_op.f('ix_user_activities_created_at'), ['created_at'], unique=False)


def downgrade():
    # Drop user_activities table
    op.drop_table('user_activities')

    # Remove new fields from video_categories table
    with op.batch_alter_table('video_categories', schema=None) as batch_op:
        batch_op.drop_column('is_active')
        batch_op.drop_column('sort_order')
        batch_op.drop_column('icon')
