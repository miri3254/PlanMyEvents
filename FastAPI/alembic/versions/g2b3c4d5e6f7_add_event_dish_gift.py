"""Add gift flag to event dishes.

Revision ID: g2b3c4d5e6f7
Revises: b3d5f7a9c1e2
"""

from alembic import op
import sqlalchemy as sa


revision = "g2b3c4d5e6f7"
down_revision = "b3d5f7a9c1e2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "event_dishes",
        sa.Column("is_gift", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("event_dishes", "is_gift")
