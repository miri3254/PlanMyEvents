"""Add delivery sheet fields

Revision ID: e9f4a1b2c3d4
Revises: d8a1f3c9e2b4
Create Date: 2026-06-02
"""
from datetime import datetime, timezone

from alembic import op
import sqlalchemy as sa


revision = "e9f4a1b2c3d4"
down_revision = "d8a1f3c9e2b4"
branch_labels = None
depends_on = None


DEFAULT_NOTES = [
    "לקחת מקפיא",
    "לבדוק מקרר",
    "לבדוק פלטה",
    "לעבור גז",
    "לספור ארגזים",
    "להוציא מהמקפיא",
    "לבדוק שתיה",
    "לבדוק לחמניות",
]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def upgrade() -> None:
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    existing_tables = set(inspector.get_table_names())
    existing_event_columns = {column["name"] for column in inspector.get_columns("events")}

    with op.batch_alter_table("events", schema=None) as batch_op:
        columns = [
            ("floor", sa.Column("floor", sa.Integer(), nullable=True)),
            ("has_elevator", sa.Column("has_elevator", sa.Boolean(), nullable=False, server_default="0")),
            ("access_code", sa.Column("access_code", sa.String(length=100), nullable=True)),
            ("onsite_contact_name", sa.Column("onsite_contact_name", sa.String(length=255), nullable=True)),
            ("onsite_contact_phone", sa.Column("onsite_contact_phone", sa.String(length=50), nullable=True)),
            ("hall_owner_name", sa.Column("hall_owner_name", sa.String(length=255), nullable=True)),
            ("hall_owner_phone", sa.Column("hall_owner_phone", sa.String(length=50), nullable=True)),
            ("has_nearby_parking", sa.Column("has_nearby_parking", sa.Boolean(), nullable=False, server_default="0")),
            ("has_back_entrance", sa.Column("has_back_entrance", sa.Boolean(), nullable=False, server_default="0")),
            ("requires_carts", sa.Column("requires_carts", sa.Boolean(), nullable=False, server_default="0")),
            ("access_notes", sa.Column("access_notes", sa.Text(), nullable=True)),
            ("dishware_type", sa.Column("dishware_type", sa.String(length=50), nullable=True)),
            ("equipment_dropoff_location", sa.Column("equipment_dropoff_location", sa.Text(), nullable=True)),
            ("check_refrigerator", sa.Column("check_refrigerator", sa.Boolean(), nullable=False, server_default="0")),
            ("check_freezer", sa.Column("check_freezer", sa.Boolean(), nullable=False, server_default="0")),
            ("check_hot_plate", sa.Column("check_hot_plate", sa.Boolean(), nullable=False, server_default="0")),
            ("connect_gas", sa.Column("connect_gas", sa.Boolean(), nullable=False, server_default="0")),
            ("put_in_refrigerator", sa.Column("put_in_refrigerator", sa.Boolean(), nullable=False, server_default="0")),
            ("put_in_freezer", sa.Column("put_in_freezer", sa.Boolean(), nullable=False, server_default="0")),
            ("put_on_hot_plate", sa.Column("put_on_hot_plate", sa.Boolean(), nullable=False, server_default="0")),
            ("count_boxes", sa.Column("count_boxes", sa.Boolean(), nullable=False, server_default="0")),
            ("check_drinks", sa.Column("check_drinks", sa.Boolean(), nullable=False, server_default="0")),
            ("check_rolls", sa.Column("check_rolls", sa.Boolean(), nullable=False, server_default="0")),
            ("delivery_special_notes", sa.Column("delivery_special_notes", sa.Text(), nullable=True)),
        ]
        for column_name, column in columns:
            if column_name not in existing_event_columns:
                batch_op.add_column(column)

    if "delivery_note_templates" not in existing_tables:
        op.create_table(
            "delivery_note_templates",
            sa.Column("note", sa.String(length=255), nullable=False),
            sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="0"),
            sa.Column("deleted_at", sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("note"),
        )
    if "event_delivery_notes" not in existing_tables:
        op.create_table(
            "event_delivery_notes",
            sa.Column("event_id", sa.Integer(), nullable=False),
            sa.Column("template_id", sa.Integer(), nullable=False),
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="0"),
            sa.Column("deleted_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["template_id"], ["delivery_note_templates.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("event_id", "template_id", name="uix_event_delivery_note"),
        )
    if "event_boxes" not in existing_tables:
        op.create_table(
            "event_boxes",
            sa.Column("event_id", sa.Integer(), nullable=False),
            sa.Column("box_type", sa.String(length=100), nullable=False),
            sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="0"),
            sa.Column("deleted_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )

    connection.execute(
        sa.text(
            """
            UPDATE events
            SET dishware_type = CASE
                WHEN is_real_dishes = 1 THEN 'כלים אמיתיים'
                ELSE 'חד פעמי'
            END
            WHERE dishware_type IS NULL
            """
        )
    )

    now = _now()
    for index, note in enumerate(DEFAULT_NOTES, start=1):
        connection.execute(
            sa.text(
                """
                INSERT OR IGNORE INTO delivery_note_templates
                    (note, display_order, created_at, updated_at, is_deleted)
                VALUES
                    (:note, :display_order, :created_at, :updated_at, 0)
                """
            ),
            {
                "note": note,
                "display_order": index,
                "created_at": now,
                "updated_at": now,
            },
        )


def downgrade() -> None:
    op.drop_table("event_boxes")
    op.drop_table("event_delivery_notes")
    op.drop_table("delivery_note_templates")
    with op.batch_alter_table("events", schema=None) as batch_op:
        batch_op.drop_column("delivery_special_notes")
        batch_op.drop_column("check_rolls")
        batch_op.drop_column("check_drinks")
        batch_op.drop_column("count_boxes")
        batch_op.drop_column("put_on_hot_plate")
        batch_op.drop_column("put_in_freezer")
        batch_op.drop_column("put_in_refrigerator")
        batch_op.drop_column("connect_gas")
        batch_op.drop_column("check_hot_plate")
        batch_op.drop_column("check_freezer")
        batch_op.drop_column("check_refrigerator")
        batch_op.drop_column("equipment_dropoff_location")
        batch_op.drop_column("dishware_type")
        batch_op.drop_column("access_notes")
        batch_op.drop_column("requires_carts")
        batch_op.drop_column("has_back_entrance")
        batch_op.drop_column("has_nearby_parking")
        batch_op.drop_column("hall_owner_phone")
        batch_op.drop_column("hall_owner_name")
        batch_op.drop_column("onsite_contact_phone")
        batch_op.drop_column("onsite_contact_name")
        batch_op.drop_column("access_code")
        batch_op.drop_column("has_elevator")
        batch_op.drop_column("floor")
