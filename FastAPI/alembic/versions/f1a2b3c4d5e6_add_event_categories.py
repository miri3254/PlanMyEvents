"""Add dynamic event categories.

Revision ID: f1a2b3c4d5e6
Revises: e9f4a1b2c3d4
"""

from alembic import op
import sqlalchemy as sa


revision = "f1a2b3c4d5e6"
down_revision = "e9f4a1b2c3d4"
branch_labels = None
depends_on = None


DEFAULT_CATEGORIES = [
    "בר מצווה",
    "אירוסים",
    "שבע ברכות",
    "אירוע מתוק",
    "שבת",
    "מגשי אירוח",
]


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    event_columns = {column["name"] for column in inspector.get_columns("events")}
    if "event_category" not in event_columns:
        with op.batch_alter_table("events") as batch_op:
            batch_op.add_column(sa.Column("event_category", sa.String(length=100), nullable=True))

    lookup = sa.table(
        "lookup_data",
        sa.column("category", sa.String),
        sa.column("value", sa.String),
        sa.column("display_order", sa.Integer),
        sa.column("is_default", sa.Integer),
    )
    existing = {
        row[0]
        for row in op.get_bind().execute(
            sa.select(lookup.c.value).where(lookup.c.category == "event_categories")
        )
    }
    missing_categories = [
            {
                "category": "event_categories",
                "value": value,
                "display_order": index,
                "is_default": 1,
            }
            for index, value in enumerate(DEFAULT_CATEGORIES)
            if value not in existing
        ]
    if missing_categories:
        op.bulk_insert(lookup, missing_categories)


def downgrade() -> None:
    op.execute("DELETE FROM lookup_data WHERE category = 'event_categories'")
    with op.batch_alter_table("events") as batch_op:
        batch_op.drop_column("event_category")
