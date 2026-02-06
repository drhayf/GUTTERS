"""add_embeddings_table_with_pgvector

Revision ID: 6375cf08c997
Revises: 867203d5c5fc
Create Date: 2026-01-24 01:04:55.626752

"""
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '6375cf08c997'
down_revision: Union[str, None] = '867203d5c5fc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import JSONB


def upgrade() -> None:
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    # Create embeddings table
    op.create_table(
        'embeddings',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('embedding', Vector(1536), nullable=True),
        sa.Column('content_metadata', JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('ix_embeddings_user_id', 'embeddings', ['user_id'], unique=False)
    op.create_index('ix_embeddings_content_metadata', 'embeddings', ['content_metadata'], postgresql_using='gin')

    # HNSW index for vector similarity (pgvector specific)
    op.execute(
        'CREATE INDEX embeddings_embedding_idx ON embeddings '
        'USING hnsw (embedding vector_cosine_ops)'
    )


def downgrade() -> None:
    op.execute('DROP INDEX IF EXISTS embeddings_embedding_idx')
    op.drop_index('ix_embeddings_content_metadata', table_name='embeddings')
    op.drop_index('ix_embeddings_user_id', table_name='embeddings')
    op.drop_table('embeddings')
    # We might not want to drop the extension if other things use it,
    # but for completeness in a clean downgrade:
    # op.execute('DROP EXTENSION IF EXISTS vector')
