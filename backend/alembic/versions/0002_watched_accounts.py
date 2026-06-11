"""add watched_accounts table

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-11

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "watched_accounts",
        sa.Column("id", sa.String(128), primary_key=True),
        sa.Column("platform", sa.String(16), nullable=False),
        sa.Column("handle", sa.String(128), nullable=False),
        sa.Column("display_name", sa.String(256), nullable=False),
        sa.Column("source_of_discovery", sa.String(512), nullable=True),
        sa.Column("enabled", sa.Boolean(), server_default="1", nullable=False),
        sa.Column("added_on", sa.Date(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_index("ix_watched_accounts_platform", "watched_accounts", ["platform"])


def downgrade() -> None:
    op.drop_index("ix_watched_accounts_platform", table_name="watched_accounts")
    op.drop_table("watched_accounts")
