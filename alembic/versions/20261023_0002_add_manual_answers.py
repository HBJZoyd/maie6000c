"""Store manual answers and citations without changing existing cases.

Revision ID: 20261023_0002
Revises: 20260713_0001
"""

import sqlalchemy as sa
from alembic import op

revision = "20261023_0002"
down_revision = "20260713_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("cases", sa.Column("answer", sa.Text(), nullable=True))
    op.add_column("cases", sa.Column("cite_pages", sa.JSON(), nullable=True))
    op.add_column("cases", sa.Column("sources", sa.JSON(), nullable=True))
    op.add_column("cases", sa.Column("related_images", sa.JSON(), nullable=True))


def downgrade() -> None:
    for column in ("related_images", "sources", "cite_pages", "answer"):
        op.drop_column("cases", column)
