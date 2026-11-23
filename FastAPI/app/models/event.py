"""
Event models — the aggregate root of the system.
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import relationship

from app.db.base import BaseModel
from app.core.enums import EventStatus


class Event(BaseModel):
    """
    Central business entity.  All dish / tray / list operations
    go through EventService.
    """

    __tablename__ = "events"

    name = Column(String(255), nullable=False)
    event_category = Column(String(100), nullable=True)
    # Changed from ENUM to String(100) for dynamic menu types
    menu_type = Column(String(100), nullable=False)
    status = Column(SAEnum(EventStatus), default=EventStatus.DRAFT, nullable=False)

    # Date & time
    date = Column(DateTime, nullable=False)
    event_time = Column(String(10), nullable=True)
    hebrew_date = Column(String(100), nullable=True)
    day_sequence_number = Column(Integer, default=1, nullable=False)
    day_sequence_color = Column(String(30), nullable=True)

    # Location
    address = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)

    # Guest & settings
    guest_count = Column(Integer, default=1, nullable=False)
    is_real_dishes = Column(Boolean, default=False, nullable=False)  # כלים אמיתיים או חד"פ

    # Shabbat morning split
    is_morning_split = Column(Boolean, default=False, nullable=False)
    split_extra_charge = Column(Float, nullable=True)

    # Pricing
    base_price_per_guest = Column(Float, nullable=True)  # snapshot from template
    real_dishes_extra_per_guest = Column(Float, nullable=True, default=0.0)  # snapshot - תוספת כלים אמיתיים
    calculated_price = Column(Float, default=0.0, nullable=False)  # מחיר מחושב אוטומטית
    final_price = Column(Float, nullable=True)  # מחיר סופי (ניתן לעריכה)
    discount_percent = Column(Float, nullable=True, default=0.0)  # אחוז הנחה
    discount_amount = Column(Float, nullable=True, default=0.0)  # סכום ההנחה
    total_price = Column(Float, default=0.0, nullable=False)  # deprecated - use calculated_price

    notes = Column(Text, nullable=True)

    # Delivery sheet
    venue_name = Column(String(255), nullable=True)
    floor = Column(Integer, nullable=True)
    has_elevator = Column(Boolean, default=False, nullable=False)
    access_code = Column(String(100), nullable=True)
    onsite_contact_name = Column(String(255), nullable=True)
    onsite_contact_phone = Column(String(50), nullable=True)
    hall_owner_name = Column(String(255), nullable=True)
    hall_owner_phone = Column(String(50), nullable=True)
    has_nearby_parking = Column(Boolean, default=False, nullable=False)
    has_back_entrance = Column(Boolean, default=False, nullable=False)
    requires_carts = Column(Boolean, default=False, nullable=False)
    access_notes = Column(Text, nullable=True)
    dishware_type = Column(String(50), nullable=True)
    delivery_contents_notes = Column(Text, nullable=True)
    last_minute_items = Column(Text, nullable=True)
    equipment_dropoff_location = Column(Text, nullable=True)
    check_refrigerator = Column(Boolean, default=False, nullable=False)
    check_freezer = Column(Boolean, default=False, nullable=False)
    check_hot_plate = Column(Boolean, default=False, nullable=False)
    connect_gas = Column(Boolean, default=False, nullable=False)
    put_in_refrigerator = Column(Boolean, default=False, nullable=False)
    put_in_freezer = Column(Boolean, default=False, nullable=False)
    put_on_hot_plate = Column(Boolean, default=False, nullable=False)
    count_boxes = Column(Boolean, default=False, nullable=False)
    check_drinks = Column(Boolean, default=False, nullable=False)
    check_rolls = Column(Boolean, default=False, nullable=False)
    delivery_special_notes = Column(Text, nullable=True)

    # ── relationships ────────────────────────────────────────────────
    owners = relationship(
        "EventOwner",
        back_populates="event",
        cascade="all, delete-orphan",
        order_by="EventOwner.order",
    )
    dishes = relationship(
        "EventDish",
        back_populates="event",
        cascade="all, delete-orphan",
    )
    tray_selections = relationship(
        "EventTraySelection",
        back_populates="event",
        cascade="all, delete-orphan",
    )
    delivery_notes = relationship(
        "EventDeliveryNote",
        back_populates="event",
        cascade="all, delete-orphan",
    )
    boxes = relationship(
        "EventBox",
        back_populates="event",
        cascade="all, delete-orphan",
        order_by="EventBox.id",
    )


class EventOwner(BaseModel):
    """Dynamic owner / client contact for an event."""

    __tablename__ = "event_owners"

    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    order = Column(Integer, default=0, nullable=False)

    event = relationship("Event", back_populates="owners")


class EventDish(BaseModel):
    """
    Dish selected for an event.
    For normal menus: one row per selected dish per category.
    """

    __tablename__ = "event_dishes"

    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    dish_id = Column(Integer, ForeignKey("dishes.id", ondelete="CASCADE"), nullable=False)
    sub_meal_id = Column(Integer, ForeignKey("menu_sub_meals.id", ondelete="SET NULL"), nullable=True)
    category_id = Column(Integer, ForeignKey("menu_categories.id", ondelete="SET NULL"), nullable=True)

    quantity = Column(Integer, default=1, nullable=False)
    is_upgrade = Column(Boolean, default=False, nullable=False)
    serving_mode = Column(String(20), nullable=True)  # null inherits the menu
    is_gift = Column(Boolean, default=False, nullable=False)
    extra_charge = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    is_draft = Column(Boolean, default=False, nullable=False)

    # Price snapshot — filled when event status → APPROVED
    snapshot_base_price = Column(Float, nullable=True)
    snapshot_client_price = Column(Float, nullable=True)

    # relationships
    event = relationship("Event", back_populates="dishes")
    dish = relationship("Dish")
    sub_meal = relationship("MenuSubMeal")
    category = relationship("MenuCategory")


class EventTraySelection(BaseModel):
    """
    Tray selection for tray menus (מגשי אירוח).
    Each row = "N trays of dish X from category Y".
    """

    __tablename__ = "event_tray_selections"

    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    dish_id = Column(Integer, ForeignKey("dishes.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, ForeignKey("menu_categories.id", ondelete="SET NULL"), nullable=True)

    tray_count = Column(Integer, default=1, nullable=False)
    price_per_tray = Column(Float, nullable=True)     # snapshot
    notes = Column(Text, nullable=True)

    # relationships
    event = relationship("Event", back_populates="tray_selections")
    dish = relationship("Dish")
    category = relationship("MenuCategory")


class DeliveryNoteTemplate(BaseModel):
    """Reusable delivery note selected on events."""

    __tablename__ = "delivery_note_templates"

    note = Column(String(255), nullable=False, unique=True)
    display_order = Column(Integer, default=0, nullable=False)

    event_links = relationship("EventDeliveryNote", back_populates="template")


class EventDeliveryNote(BaseModel):
    """Selected reusable delivery note for an event."""

    __tablename__ = "event_delivery_notes"

    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    template_id = Column(Integer, ForeignKey("delivery_note_templates.id", ondelete="CASCADE"), nullable=False)

    event = relationship("Event", back_populates="delivery_notes")
    template = relationship("DeliveryNoteTemplate", back_populates="event_links")


class EventBox(BaseModel):
    """Box summary row for an event delivery sheet."""

    __tablename__ = "event_boxes"

    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    box_type = Column(String(100), nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    notes = Column(Text, nullable=True)

    event = relationship("Event", back_populates="boxes")
