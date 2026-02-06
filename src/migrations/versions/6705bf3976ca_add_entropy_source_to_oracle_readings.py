"""add_entropy_source_to_oracle_readings

Revision ID: 6705bf3976ca
Revises: 99c5fd8086d3
Create Date: 2026-02-06 13:46:50.070200

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6705bf3976ca'
down_revision: Union[str, None] = '99c5fd8086d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'oracle_readings',
        sa.Column('entropy_source', sa.String(20), nullable=True, server_default='LOCAL_CHAOS')
    )


def downgrade() -> None:
    op.drop_column('oracle_readings', 'entropy_source')
