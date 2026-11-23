"""Expand the event delivery sheet.

Revision ID: b3d5f7a9c1e2
Revises: a2c4e6f8b0d1
"""

from alembic import op
import sqlalchemy as sa


revision = "b3d5f7a9c1e2"
down_revision = "a2c4e6f8b0d1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("events", schema=None) as batch_op:
        batch_op.add_column(sa.Column("venue_name", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("delivery_contents_notes", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("last_minute_items", sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("events", schema=None) as batch_op:
        batch_op.drop_column("last_minute_items")
        batch_op.drop_column("delivery_contents_notes")
        batch_op.drop_column("venue_name")
