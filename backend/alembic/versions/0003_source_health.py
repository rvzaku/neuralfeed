"""add fetch health columns to sources

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-11

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("sources", sa.Column("last_fetch_status", sa.String(8), nullable=True))
    op.add_column("sources", sa.Column("last_fetch_error", sa.Text(), nullable=True))
    op.add_column("sources", sa.Column("last_fetch_count", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("sources", "last_fetch_count")
    op.drop_column("sources", "last_fetch_error")
    op.drop_column("sources", "last_fetch_status")
