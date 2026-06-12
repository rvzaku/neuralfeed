"""indexes for feed/stories hot paths

Revision ID: 0010
Revises: 0009
"""

from alembic import op

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_articles_published_at", "articles", ["published_at"])
    op.create_index("ix_articles_source_id", "articles", ["source_id"])


def downgrade() -> None:
    op.drop_index("ix_articles_published_at")
    op.drop_index("ix_articles_source_id")
