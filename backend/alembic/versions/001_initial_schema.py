"""Initial schema: users, sessions, messages, message_sources, artifacts, ingestion_runs

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-08-25 21:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.CHAR(36), primary_key=True, nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True)
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # 2. Create sessions table with user_id foreign key
    op.create_table(
        'sessions',
        sa.Column('id', sa.CHAR(36), primary_key=True, nullable=False),
        sa.Column('user_id', sa.CHAR(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=True),
        sa.Column('title', sa.String(255), nullable=False, server_default='New Conversation'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('user_metadata', sa.JSON(), nullable=True)
    )
    op.create_index('ix_sessions_user_id', 'sessions', ['user_id'])

    # 3. Create messages table
    op.create_table(
        'messages',
        sa.Column('id', sa.CHAR(36), primary_key=True, nullable=False),
        sa.Column('session_id', sa.CHAR(36), sa.ForeignKey('sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(32), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('model_provider', sa.String(64), nullable=True),
        sa.Column('model_name', sa.String(128), nullable=True),
        sa.Column('latency_ms', sa.Integer(), nullable=True),
        sa.Column('intent_type', sa.String(32), nullable=True, server_default='NORMAL_QA')
    )
    op.create_index('ix_messages_session_id', 'messages', ['session_id'])
    op.create_index('ix_messages_created_at', 'messages', ['created_at'])

    # 4. Create message_sources table
    op.create_table(
        'message_sources',
        sa.Column('id', sa.CHAR(36), primary_key=True, nullable=False),
        sa.Column('message_id', sa.CHAR(36), sa.ForeignKey('messages.id', ondelete='CASCADE'), nullable=False),
        sa.Column('chunk_id', sa.String(128), nullable=False),
        sa.Column('source_title', sa.String(255), nullable=False),
        sa.Column('source_url', sa.String(512), nullable=True),
        sa.Column('speaker', sa.String(128), nullable=True),
        sa.Column('source_type', sa.String(64), nullable=False, server_default='podcast_transcript'),
        sa.Column('relevance_score', sa.Float(), nullable=True),
        sa.Column('rank', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('snippet', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False)
    )
    op.create_index('ix_message_sources_message_id', 'message_sources', ['message_id'])
    op.create_index('ix_message_sources_chunk_id', 'message_sources', ['chunk_id'])

    # 5. Create artifacts table
    op.create_table(
        'artifacts',
        sa.Column('id', sa.CHAR(36), primary_key=True, nullable=False),
        sa.Column('session_id', sa.CHAR(36), sa.ForeignKey('sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('message_id', sa.CHAR(36), sa.ForeignKey('messages.id', ondelete='SET NULL'), nullable=True),
        sa.Column('artifact_type', sa.String(32), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('raw_content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('metadata_json', sa.JSON(), nullable=True)
    )
    op.create_index('ix_artifacts_session_id', 'artifacts', ['session_id'])
    op.create_index('ix_artifacts_message_id', 'artifacts', ['message_id'])

    # 6. Create ingestion_runs table
    op.create_table(
        'ingestion_runs',
        sa.Column('id', sa.CHAR(36), primary_key=True, nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(32), nullable=False, server_default='RUNNING'),
        sa.Column('document_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('chunk_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_summary', sa.Text(), nullable=True),
        sa.Column('run_metadata', sa.JSON(), nullable=True)
    )


def downgrade() -> None:
    op.drop_table('ingestion_runs')
    op.drop_table('artifacts')
    op.drop_table('message_sources')
    op.drop_table('messages')
    op.drop_table('sessions')
    op.drop_table('users')
