"""Initial schema

Revision ID: 20241020_01
Revises:
Create Date: 2024-10-20
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20241020_01"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "folders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("parent_id", sa.Integer(), sa.ForeignKey("folders.id", ondelete="CASCADE")),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    )
    op.create_unique_constraint("uq_folder_path_owner", "folders", ["name", "parent_id", "owner_id"])

    op.create_table(
        "videos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("path", sa.String(length=1024), nullable=False),
        sa.Column("folder_id", sa.Integer(), sa.ForeignKey("folders.id", ondelete="SET NULL")),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("duration", sa.Float()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_unique_constraint("uq_video_path", "videos", ["path"])

    op.create_table(
        "learning_progress",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("video_id", sa.Integer(), sa.ForeignKey("videos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("last_position", sa.Float(), nullable=False),
        sa.Column("completed", sa.Boolean(), nullable=False),
        sa.Column("first_watched_at", sa.DateTime()),
        sa.Column("last_watched_at", sa.DateTime()),
    )
    op.create_unique_constraint("uq_progress_user_video", "learning_progress", ["user_id", "video_id"])

    op.create_table(
        "knowledge_base",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("video_id", sa.Integer(), sa.ForeignKey("videos.id", ondelete="CASCADE"), unique=True),
        sa.Column("json_content", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("vector_ids", postgresql.JSONB(astext_type=sa.Text())),
    )


def downgrade() -> None:
    op.drop_table("knowledge_base")
    op.drop_constraint("uq_progress_user_video", "learning_progress", type_="unique")
    op.drop_table("learning_progress")
    op.drop_constraint("uq_video_path", "videos", type_="unique")
    op.drop_table("videos")
    op.drop_constraint("uq_folder_path_owner", "folders", type_="unique")
    op.drop_table("folders")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
