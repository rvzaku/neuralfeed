"""add cached ai summary columns to articles

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-11

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("articles", sa.Column("ai_summary", sa.Text(), nullable=True))
    op.add_column("articles", sa.Column("ai_summary_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("articles", "ai_summary_at")
    op.drop_column("articles", "ai_summary")
