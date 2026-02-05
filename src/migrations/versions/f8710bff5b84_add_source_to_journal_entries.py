"""Add source to journal_entries

Revision ID: f8710bff5b84
Revises: 4387b64bc0cd
Create Date: 2026-01-28 10:29:16.683221

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f8710bff5b84"
down_revision: Union[str, None] = "4387b64bc0cd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("journal_entries", sa.Column("source", sa.String(), nullable=True, server_default="USER"))


def downgrade() -> None:
    op.drop_column("journal_entries", "source")
