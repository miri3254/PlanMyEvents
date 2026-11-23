"""Drop Shabbat meal split settings.

Revision ID: h1c2d3e4f5a6
Revises: g2b3c4d5e6f7
"""

from alembic import op
import sqlalchemy as sa


revision = "h1c2d3e4f5a6"
down_revision = "g2b3c4d5e6f7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("event_calculation_settings", schema=None) as batch_op:
        batch_op.drop_column("shabbat_meal_counts")


def downgrade() -> None:
    with op.batch_alter_table("event_calculation_settings", schema=None) as batch_op:
        batch_op.add_column(sa.Column("shabbat_meal_counts", sa.JSON(), nullable=True))
