"""
Event calculation models.

These tables keep event-wide calculation settings, dish serving/packaging
alternatives, approved snapshots, manual tool rows, and reusable reservations.
"""

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from app.db.base import BaseModel


class EventCalculationSettings(BaseModel):
    __tablename__ = "event_calculation_settings"

    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False, unique=True)

    drinks_enabled = Column(Boolean, default=True, nullable=False)
    drink_types = Column(JSON, nullable=True)
    orange_flavored_mode = Column(String(20), default="both", nullable=False)

    rolls_enabled = Column(Boolean, default=True, nullable=False)
    roll_splits = Column(JSON, nullable=True)

    table_shape = Column(String(30), default="rectangle", nullable=False)
    tablecloth_tool_id = Column(Integer, ForeignKey("tools.id", ondelete="SET NULL"), nullable=True)
    use_rectangular_for_square = Column(Boolean, default=False, nullable=False)
    table_overrides = Column(JSON, nullable=True)
    event_tool_set_items = Column(JSON, nullable=True)

    credit_card_enabled = Column(Boolean, default=False, nullable=False)
    credit_card_amount = Column(Float, nullable=True)
    credit_card_installments = Column(Integer, default=1, server_default='1', nullable=False)
    credit_card_rate = Column(Float, nullable=True)
    credit_card_vat_multiplier = Column(Float, default=1.18, server_default='1.18', nullable=False)

    notes = Column(Text, nullable=True)


class EventCalculationSnapshot(BaseModel):
    __tablename__ = "event_calculation_snapshots"

    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    calculation_type = Column(String(80), nullable=False)
    payload = Column(JSON, nullable=False)


class DishServingSet(BaseModel):
    __tablename__ = "dish_serving_sets"

    dish_id = Column(Integer, ForeignKey("dishes.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    set_type = Column(String(30), default="serving", nullable=False)  # serving | packaging
    is_default = Column(Boolean, default=False, nullable=False)
    dishware_type = Column(String(50), nullable=True)
    serving_mode = Column(String(20), nullable=True)  # personal | central; null preserves legacy sets
    notes = Column(Text, nullable=True)

    items = relationship(
        "DishServingSetItem",
        back_populates="set",
        cascade="all, delete-orphan",
    )


class DishServingSetItem(BaseModel):
    __tablename__ = "dish_serving_set_items"

    set_id = Column(Integer, ForeignKey("dish_serving_sets.id", ondelete="CASCADE"), nullable=False)
    tool_id = Column(Integer, ForeignKey("tools.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(255), nullable=True)
    quantity = Column(Float, default=1.0, nullable=False)
    quantity_basis = Column(String(30), default="dish_unit", nullable=False)
    is_reusable = Column(Boolean, nullable=True)

    set = relationship("DishServingSet", back_populates="items")
    tool = relationship("Tool")


class EventDishServingSelection(BaseModel):
    __tablename__ = "event_dish_serving_selections"

    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    event_dish_id = Column(Integer, ForeignKey("event_dishes.id", ondelete="CASCADE"), nullable=True)
    event_tray_selection_id = Column(Integer, ForeignKey("event_tray_selections.id", ondelete="CASCADE"), nullable=True)
    dish_id = Column(Integer, ForeignKey("dishes.id", ondelete="CASCADE"), nullable=False)
    set_id = Column(Integer, ForeignKey("dish_serving_sets.id", ondelete="SET NULL"), nullable=True)
    set_type = Column(String(30), default="serving", nullable=False)


class DishCalculationRule(BaseModel):
    __tablename__ = "dish_calculation_rules"

    dish_id = Column(Integer, ForeignKey("dishes.id", ondelete="CASCADE"), nullable=False)
    rule_type = Column(String(80), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(255), nullable=True)
    params = Column(JSON, nullable=True)
    replaces_ingredient_product_id = Column(Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)


class EventManualToolRow(BaseModel):
    __tablename__ = "event_manual_tool_rows"

    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    tool_id = Column(Integer, ForeignKey("tools.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(255), nullable=True)
    quantity = Column(Integer, default=1, nullable=False)
    is_reusable = Column(Boolean, default=False, nullable=False)
    notes = Column(Text, nullable=True)


class ToolReservation(BaseModel):
    __tablename__ = "tool_reservations"

    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    tool_id = Column(Integer, ForeignKey("tools.id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    reserved_for_date = Column(DateTime, nullable=False)
    status = Column(String(30), default="active", nullable=False)
