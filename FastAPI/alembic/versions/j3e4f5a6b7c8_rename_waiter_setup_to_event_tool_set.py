"""Rename waiter setup items to event tool set items.

Revision ID: j3e4f5a6b7c8
Revises: i2d3e4f5a6b7
"""

from alembic import op


revision = "j3e4f5a6b7c8"
down_revision = "i2d3e4f5a6b7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("event_calculation_settings", schema=None) as batch_op:
        batch_op.alter_column("waiter_setup_items", new_column_name="event_tool_set_items")


def downgrade() -> None:
    with op.batch_alter_table("event_calculation_settings", schema=None) as batch_op:
        batch_op.alter_column("event_tool_set_items", new_column_name="waiter_setup_items")
