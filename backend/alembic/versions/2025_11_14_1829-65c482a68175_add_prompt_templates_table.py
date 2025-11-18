"""add_prompt_templates_table

Revision ID: 65c482a68175
Revises: a1b2c3d4e5f6
Create Date: 2025-11-14 18:29:21.242885

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '65c482a68175'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create prompt_templates table for centralized prompt management."""
    op.create_table(
        'prompt_templates',
        sa.Column('id', sa.Integer(), nullable=False),

        # Identification
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),

        # Prompt Content
        sa.Column('system_message', sa.Text(), nullable=False),
        sa.Column('user_message_template', sa.Text(), nullable=True),

        # Configuration
        sa.Column('model', sa.String(length=50), nullable=False, server_default='gpt-4o'),
        sa.Column('temperature', sa.Float(), nullable=False, server_default='0.7'),
        sa.Column('max_tokens', sa.Integer(), nullable=False, server_default='1000'),
        sa.Column('top_p', sa.Float(), nullable=True, server_default='1.0'),

        # Variables & Validation
        sa.Column('variables', sa.JSON(), nullable=True),
        sa.Column('response_format', sa.String(length=20), nullable=True),
        sa.Column('response_schema', sa.JSON(), nullable=True),

        # Version Management
        sa.Column('version', sa.String(length=20), nullable=False, server_default='1.0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),

        # Metadata
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),

        # Usage Statistics
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),

        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for performance
    op.create_index('ix_prompt_templates_id', 'prompt_templates', ['id'])
    op.create_index('ix_prompt_templates_name', 'prompt_templates', ['name'], unique=True)
    op.create_index('ix_prompt_templates_category', 'prompt_templates', ['category'])


def downgrade() -> None:
    """Drop prompt_templates table."""
    op.drop_index('ix_prompt_templates_category', table_name='prompt_templates')
    op.drop_index('ix_prompt_templates_name', table_name='prompt_templates')
    op.drop_index('ix_prompt_templates_id', table_name='prompt_templates')
    op.drop_table('prompt_templates')
