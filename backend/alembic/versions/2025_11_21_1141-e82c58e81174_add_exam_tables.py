"""add_exam_tables

Revision ID: e82c58e81174
Revises: add_categories_activities
Create Date: 2025-11-21 11:41:06.525511

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e82c58e81174'
down_revision: Union[str, None] = 'add_categories_activities'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create exams table
    op.create_table(
        'exams',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('time_limit_minutes', sa.Integer(), nullable=True),
        sa.Column('pass_threshold_percentage', sa.Float(), nullable=False, server_default='70.0'),
        sa.Column('max_attempts', sa.Integer(), nullable=True),
        sa.Column('status', sa.Enum('DRAFT', 'PUBLISHED', 'ARCHIVED', name='examstatus'), nullable=False, server_default='DRAFT'),
        sa.Column('available_from', sa.DateTime(timezone=True), nullable=True),
        sa.Column('available_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('show_correct_answers', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('randomize_questions', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('randomize_options', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_exams_id'), 'exams', ['id'], unique=False)
    op.create_index(op.f('ix_exams_title'), 'exams', ['title'], unique=False)

    # Create exam_questions table
    op.create_table(
        'exam_questions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('exam_id', sa.Integer(), nullable=False),
        sa.Column('question_type', sa.Enum('MULTIPLE_CHOICE', 'TRUE_FALSE', 'SHORT_ANSWER', name='questiontype'), nullable=False),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('points', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('options', sa.Text(), nullable=True),
        sa.Column('correct_answer', sa.Text(), nullable=False),
        sa.Column('explanation', sa.Text(), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('source_video_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['exam_id'], ['exams.id'], ),
        sa.ForeignKeyConstraint(['source_video_id'], ['videos.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_exam_questions_id'), 'exam_questions', ['id'], unique=False)

    # Create exam_video_associations table
    op.create_table(
        'exam_video_associations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('exam_id', sa.Integer(), nullable=False),
        sa.Column('video_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['exam_id'], ['exams.id'], ),
        sa.ForeignKeyConstraint(['video_id'], ['videos.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_exam_video_associations_id'), 'exam_video_associations', ['id'], unique=False)

    # Create exam_attempts table
    op.create_table(
        'exam_attempts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('exam_id', sa.Integer(), nullable=False),
        sa.Column('user_email', sa.String(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('time_spent_seconds', sa.Integer(), nullable=True),
        sa.Column('total_points', sa.Float(), nullable=True),
        sa.Column('earned_points', sa.Float(), nullable=True),
        sa.Column('score_percentage', sa.Float(), nullable=True),
        sa.Column('passed', sa.Boolean(), nullable=True),
        sa.Column('is_completed', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['exam_id'], ['exams.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_exam_attempts_id'), 'exam_attempts', ['id'], unique=False)
    op.create_index(op.f('ix_exam_attempts_user_email'), 'exam_attempts', ['user_email'], unique=False)

    # Create exam_answers table
    op.create_table(
        'exam_answers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('attempt_id', sa.Integer(), nullable=False),
        sa.Column('question_id', sa.Integer(), nullable=False),
        sa.Column('answer_text', sa.Text(), nullable=True),
        sa.Column('is_correct', sa.Boolean(), nullable=True),
        sa.Column('points_earned', sa.Float(), nullable=True),
        sa.Column('manually_graded', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('grader_feedback', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['attempt_id'], ['exam_attempts.id'], ),
        sa.ForeignKeyConstraint(['question_id'], ['exam_questions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_exam_answers_id'), 'exam_answers', ['id'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order (to handle foreign key constraints)
    op.drop_index(op.f('ix_exam_answers_id'), table_name='exam_answers')
    op.drop_table('exam_answers')

    op.drop_index(op.f('ix_exam_attempts_user_email'), table_name='exam_attempts')
    op.drop_index(op.f('ix_exam_attempts_id'), table_name='exam_attempts')
    op.drop_table('exam_attempts')

    op.drop_index(op.f('ix_exam_video_associations_id'), table_name='exam_video_associations')
    op.drop_table('exam_video_associations')

    op.drop_index(op.f('ix_exam_questions_id'), table_name='exam_questions')
    op.drop_table('exam_questions')

    op.drop_index(op.f('ix_exams_title'), table_name='exams')
    op.drop_index(op.f('ix_exams_id'), table_name='exams')
    op.drop_table('exams')

    # Drop custom enum types
    op.execute('DROP TYPE IF EXISTS examstatus')
    op.execute('DROP TYPE IF EXISTS questiontype')
