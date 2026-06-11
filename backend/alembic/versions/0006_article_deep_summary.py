"""add deep summary columns to articles

Revision ID: 0006
Revises: 0005
Create Date: 2026-06-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("articles", sa.Column("ai_deep_summary", sa.Text(), nullable=True))
    op.add_column("articles", sa.Column("ai_deep_summary_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("articles", "ai_deep_summary_at")
    op.drop_column("articles", "ai_deep_summary")
