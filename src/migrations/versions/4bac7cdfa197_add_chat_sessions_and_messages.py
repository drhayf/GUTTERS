"""Add chat sessions and messages

Revision ID: 4bac7cdfa197
Revises: 6375cf08c997
Create Date: 2026-01-24 09:53:40.048215

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = "4bac7cdfa197"
down_revision: Union[str, None] = "6375cf08c997"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Chat sessions table
    op.create_table(
        "chat_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("session_type", sa.String(50), nullable=False),  # 'master', 'journal', 'nutrition'
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("conversation_name", sa.String(255), nullable=True),  # Added for Phase 7d support
        sa.Column("contribute_to_memory", sa.Boolean(), server_default="true"),
        sa.Column("metadata", JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Chat messages table
    op.create_table(
        "chat_messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),  # 'user', 'assistant', 'system'
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("metadata", JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["session_id"], ["chat_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Indexes
    op.create_index("chat_sessions_user_id_idx", "chat_sessions", ["user_id"])
    op.create_index("chat_sessions_type_idx", "chat_sessions", ["session_type"])
    op.create_index("chat_messages_session_id_idx", "chat_messages", ["session_id"])


def downgrade() -> None:
    op.drop_index("chat_messages_session_id_idx", table_name="chat_messages")
    op.drop_index("chat_sessions_type_idx", table_name="chat_sessions")
    op.drop_index("chat_sessions_user_id_idx", table_name="chat_sessions")
    op.drop_table("chat_messages")
    op.drop_table("chat_sessions")
