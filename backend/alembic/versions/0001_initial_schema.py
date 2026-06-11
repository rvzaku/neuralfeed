"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-06-10

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sources",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("category", sa.String(32), nullable=False),
        sa.Column("url", sa.String(512), nullable=False),
        sa.Column("access", sa.String(16), nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default="1", nullable=False),
        sa.Column("priority", sa.String(8), server_default="medium", nullable=False),
        sa.Column("refresh_interval", sa.String(16), server_default="daily", nullable=False),
        sa.Column("added_on", sa.Date(), nullable=False),
        sa.Column("last_fetched_at", sa.DateTime(), nullable=True),
        sa.Column("signal_score", sa.Float(), server_default="0.5", nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
    )

    op.create_table(
        "user_preferences",
        sa.Column("key", sa.String(128), primary_key=True),
        sa.Column("value", sa.Text(), nullable=False),
    )

    op.create_table(
        "articles",
        sa.Column("id", sa.String(16), primary_key=True),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("url", sa.String(2048), nullable=False, unique=True),
        sa.Column("source_id", sa.String(64), nullable=False),
        sa.Column("author", sa.String(256), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("published_at", sa.DateTime(), nullable=False),
        sa.Column("fetched_at", sa.DateTime(), nullable=False),
        sa.Column("topic_tags", sa.JSON(), nullable=False),
        sa.Column("is_read", sa.Boolean(), server_default="0", nullable=False),
        sa.Column("is_bookmarked", sa.Boolean(), server_default="0", nullable=False),
        sa.Column("feedback", sa.Integer(), nullable=True),
        sa.Column("trending_score", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("title_hash", sa.String(16), nullable=True),
    )
    op.create_index("ix_articles_source_id", "articles", ["source_id"])
    op.create_index("ix_articles_published_at", "articles", ["published_at"])
    op.create_index("ix_articles_title_hash", "articles", ["title_hash"])

    op.create_table(
        "feedback_log",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("article_id", sa.String(16), nullable=False),
        sa.Column("source_id", sa.String(64), nullable=False),
        sa.Column("value", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_feedback_log_article_id", "feedback_log", ["article_id"])
    op.create_index("ix_feedback_log_source_id", "feedback_log", ["source_id"])


def downgrade() -> None:
    op.drop_table("feedback_log")
    op.drop_index("ix_articles_title_hash", table_name="articles")
    op.drop_index("ix_articles_published_at", table_name="articles")
    op.drop_index("ix_articles_source_id", table_name="articles")
    op.drop_table("articles")
    op.drop_table("user_preferences")
    op.drop_table("sources")
