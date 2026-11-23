"""Add event calculation settings, rules, sets, snapshots and reservations.

Revision ID: a2c4e6f8b0d1
Revises: f1a2b3c4d5e6
"""

from alembic import op
import sqlalchemy as sa


revision = "a2c4e6f8b0d1"
down_revision = "f1a2b3c4d5e6"
branch_labels = None
depends_on = None


def common_columns():
    return (
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("deleted_at", sa.DateTime()),
    )


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    required_tables = {
        "event_calculation_settings", "event_calculation_snapshots", "dish_serving_sets",
        "dish_serving_set_items", "event_dish_serving_selections", "dish_calculation_rules",
        "event_manual_tool_rows", "tool_reservations",
    }
    # Desktop startup uses metadata.create_all. If it ran before Alembic, all
    # tables already exist and the migration only has to add its indexes.
    if required_tables.issubset(set(inspector.get_table_names())):
        snapshot_indexes = {row["name"] for row in inspector.get_indexes("event_calculation_snapshots")}
        if "ix_event_calc_snapshot_event_type" not in snapshot_indexes:
            op.create_index("ix_event_calc_snapshot_event_type", "event_calculation_snapshots", ["event_id", "calculation_type"], unique=True)
        reservation_indexes = {row["name"] for row in inspector.get_indexes("tool_reservations")}
        if "ix_tool_reservation_date_tool" not in reservation_indexes:
            op.create_index("ix_tool_reservation_date_tool", "tool_reservations", ["reserved_for_date", "tool_id"])
        return

    op.create_table(
        "event_calculation_settings", *common_columns(),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("events.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("drinks_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("drink_types", sa.JSON()),
        sa.Column("orange_flavored_mode", sa.String(20), nullable=False, server_default="both"),
        sa.Column("rolls_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("roll_splits", sa.JSON()),
        sa.Column("table_shape", sa.String(30), nullable=False, server_default="rectangle"),
        sa.Column("tablecloth_tool_id", sa.Integer(), sa.ForeignKey("tools.id", ondelete="SET NULL")),
        sa.Column("use_rectangular_for_square", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("table_overrides", sa.JSON()),
        sa.Column("credit_card_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("credit_card_amount", sa.Float()),
        sa.Column("shabbat_meal_counts", sa.JSON()),
        sa.Column("notes", sa.Text()),
    )
    op.create_table(
        "event_calculation_snapshots", *common_columns(),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("events.id", ondelete="CASCADE"), nullable=False),
        sa.Column("calculation_type", sa.String(80), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
    )
    op.create_index("ix_event_calc_snapshot_event_type", "event_calculation_snapshots", ["event_id", "calculation_type"], unique=True)
    op.create_table(
        "dish_serving_sets", *common_columns(),
        sa.Column("dish_id", sa.Integer(), sa.ForeignKey("dishes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("set_type", sa.String(30), nullable=False, server_default="serving"),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("dishware_type", sa.String(50)),
        sa.Column("notes", sa.Text()),
    )
    op.create_table(
        "dish_serving_set_items", *common_columns(),
        sa.Column("set_id", sa.Integer(), sa.ForeignKey("dish_serving_sets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tool_id", sa.Integer(), sa.ForeignKey("tools.id", ondelete="SET NULL")),
        sa.Column("name", sa.String(255)),
        sa.Column("quantity", sa.Float(), nullable=False, server_default="1"),
        sa.Column("quantity_basis", sa.String(30), nullable=False, server_default="dish_unit"),
        sa.Column("is_reusable", sa.Boolean()),
    )
    op.create_table(
        "event_dish_serving_selections", *common_columns(),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("events.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_dish_id", sa.Integer(), sa.ForeignKey("event_dishes.id", ondelete="CASCADE")),
        sa.Column("event_tray_selection_id", sa.Integer(), sa.ForeignKey("event_tray_selections.id", ondelete="CASCADE")),
        sa.Column("dish_id", sa.Integer(), sa.ForeignKey("dishes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("set_id", sa.Integer(), sa.ForeignKey("dish_serving_sets.id", ondelete="SET NULL")),
        sa.Column("set_type", sa.String(30), nullable=False, server_default="serving"),
    )
    op.create_table(
        "dish_calculation_rules", *common_columns(),
        sa.Column("dish_id", sa.Integer(), sa.ForeignKey("dishes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rule_type", sa.String(80), nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id", ondelete="SET NULL")),
        sa.Column("name", sa.String(255)),
        sa.Column("params", sa.JSON()),
        sa.Column("replaces_ingredient_product_id", sa.Integer(), sa.ForeignKey("products.id", ondelete="SET NULL")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_table(
        "event_manual_tool_rows", *common_columns(),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("events.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tool_id", sa.Integer(), sa.ForeignKey("tools.id", ondelete="SET NULL")),
        sa.Column("name", sa.String(255)),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_reusable", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("notes", sa.Text()),
    )
    op.create_table(
        "tool_reservations", *common_columns(),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("events.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tool_id", sa.Integer(), sa.ForeignKey("tools.id", ondelete="CASCADE"), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("reserved_for_date", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="active"),
    )
    op.create_index("ix_tool_reservation_date_tool", "tool_reservations", ["reserved_for_date", "tool_id"])


def downgrade() -> None:
    op.drop_index("ix_tool_reservation_date_tool", table_name="tool_reservations")
    for table in [
        "tool_reservations", "event_manual_tool_rows", "dish_calculation_rules",
        "event_dish_serving_selections", "dish_serving_set_items", "dish_serving_sets",
    ]:
        op.drop_table(table)
    op.drop_index("ix_event_calc_snapshot_event_type", table_name="event_calculation_snapshots")
    op.drop_table("event_calculation_snapshots")
    op.drop_table("event_calculation_settings")
