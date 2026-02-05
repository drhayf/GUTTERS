"""add_oracle_readings_table

Revision ID: 99c5fd8086d3
Revises: 3a1384306d6e
Create Date: 2026-02-05 23:10:04.057243

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '99c5fd8086d3'
down_revision: Union[str, None] = '3a1384306d6e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'oracle_readings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('card_rank', sa.Integer(), nullable=False),
        sa.Column('card_suit', sa.String(), nullable=False),
        sa.Column('hexagram_number', sa.Integer(), nullable=False),
        sa.Column('hexagram_line', sa.Integer(), nullable=False),
        sa.Column('synthesis_text', sa.Text(), nullable=False),
        sa.Column('diagnostic_question', sa.Text(), nullable=False),
        sa.Column('transit_context', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('accepted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('reflected', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('quest_id', sa.Integer(), nullable=True),
        sa.Column('prompt_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['prompt_id'], ['reflection_prompts.id'], ),
        sa.ForeignKeyConstraint(['quest_id'], ['quests.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_oracle_readings_created_at'), 'oracle_readings', ['created_at'], unique=False)
    op.create_index(op.f('ix_oracle_readings_user_id'), 'oracle_readings', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_oracle_readings_user_id'), table_name='oracle_readings')
    op.drop_index(op.f('ix_oracle_readings_created_at'), table_name='oracle_readings')
    op.drop_table('oracle_readings')
