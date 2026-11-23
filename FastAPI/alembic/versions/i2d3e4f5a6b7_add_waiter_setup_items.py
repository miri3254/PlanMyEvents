"""Add waiter setup items to event calculation settings.

Revision ID: i2d3e4f5a6b7
Revises: h1c2d3e4f5a6
"""

from alembic import op
import sqlalchemy as sa


revision = "i2d3e4f5a6b7"
down_revision = "h1c2d3e4f5a6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("event_calculation_settings", schema=None) as batch_op:
        batch_op.add_column(sa.Column("waiter_setup_items", sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("event_calculation_settings", schema=None) as batch_op:
        batch_op.drop_column("waiter_setup_items")
