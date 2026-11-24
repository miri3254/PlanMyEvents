"""
Event schemas.
"""

from pydantic import BaseModel, Field
from typing import Any, Optional, List, Literal
from datetime import datetime


# ─── Owner ────────────────────────────────────────────────────────────

class EventOwnerCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=255)
    order: int = Field(default=0, ge=0)


class EventOwnerResponse(BaseModel):
    id: int
    event_id: int
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    order: int = 0
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class DeliveryNoteTemplateResponse(BaseModel):
    id: int
    note: str
    display_order: int = 0

    model_config = {"from_attributes": True}


class EventBoxCreate(BaseModel):
    box_type: str = Field(..., min_length=1, max_length=100)
    quantity: int = Field(default=1, ge=1)
    notes: Optional[str] = None


class EventBoxResponse(BaseModel):
    id: int
    event_id: int
    box_type: str
    quantity: int = 1
    notes: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class EventDeliveryNoteResponse(BaseModel):
    id: int
    event_id: int
    template_id: int
    note: str

    model_config = {"from_attributes": True}


# ─── Event Dish ───────────────────────────────────────────────────────

class EventDishCreate(BaseModel):
    serving_mode: Optional[Literal["personal", "central"]] = None
    dish_id: int
    sub_meal_id: Optional[int] = None
    category_id: Optional[int] = None
    quantity: int = Field(default=1, ge=1)
    is_upgrade: bool = False
    is_gift: bool = False
    extra_charge: Optional[float] = None
    notes: Optional[str] = None


class EventDishUpdate(BaseModel):
    serving_mode: Optional[Literal["personal", "central"]] = None
    sub_meal_id: Optional[int] = None
    category_id: Optional[int] = None
    quantity: Optional[int] = Field(None, ge=1)
    is_upgrade: Optional[bool] = None
    is_gift: Optional[bool] = None
    extra_charge: Optional[float] = None
    notes: Optional[str] = None


class EventDishBulkRequest(BaseModel):
    dishes: List[EventDishCreate]
    is_draft: bool = True
    replace: bool = False


class EventDishResponse(BaseModel):
    serving_mode: Optional[Literal["personal", "central"]] = None
    id: int
    event_id: int
    dish_id: int
    sub_meal_id: Optional[int] = None
    category_id: Optional[int] = None
    quantity: int = 1
    is_upgrade: bool = False
    is_gift: bool = False
    extra_charge: Optional[float] = None
    notes: Optional[str] = None
    is_draft: bool = False
    snapshot_base_price: Optional[float] = None
    snapshot_client_price: Optional[float] = None
    created_at: Optional[datetime] = None

    # Joined info
    dish_name: Optional[str] = None
    dish_kosher_type: Optional[str] = None
    category_name_hebrew: Optional[str] = None
    sub_meal_name: Optional[str] = None
    current_base_price: Optional[float] = None  # מחיר עלות נוכחי של המנה (fallback לפני snapshot)

    model_config = {"from_attributes": True}


# ─── Tray Selection ──────────────────────────────────────────────────

class EventTrayCreate(BaseModel):
    dish_id: int
    category_id: Optional[int] = None
    tray_count: int = Field(default=1, ge=1)
    notes: Optional[str] = None


class EventTrayUpdate(BaseModel):
    dish_id: Optional[int] = None
    category_id: Optional[int] = None
    tray_count: Optional[int] = Field(None, ge=1)
    price_per_tray: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = None


class EventTrayResponse(BaseModel):
    id: int
    event_id: int
    dish_id: int
    category_id: Optional[int] = None
    tray_count: int = 1
    price_per_tray: Optional[float] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None

    dish_name: Optional[str] = None
    category_name_hebrew: Optional[str] = None

    model_config = {"from_attributes": True}


# ─── Event ────────────────────────────────────────────────────────────

class EventCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    event_category: Optional[str] = Field(None, min_length=1, max_length=100)
    menu_type: str
    date: datetime
    event_time: Optional[str] = Field(None, max_length=10)
    hebrew_date: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    guest_count: int = Field(default=1, ge=1)
    is_real_dishes: bool = False  # כלים אמיתיים (לא חד"פ)
    is_morning_split: bool = False
    notes: Optional[str] = None
    owners: Optional[List[EventOwnerCreate]] = None
    venue_name: Optional[str] = Field(None, max_length=255)
    floor: Optional[int] = None
    has_elevator: bool = False
    access_code: Optional[str] = Field(None, max_length=100)
    onsite_contact_name: Optional[str] = Field(None, max_length=255)
    onsite_contact_phone: Optional[str] = Field(None, max_length=50)
    hall_owner_name: Optional[str] = Field(None, max_length=255)
    hall_owner_phone: Optional[str] = Field(None, max_length=50)
    has_nearby_parking: bool = False
    has_back_entrance: bool = False
    requires_carts: bool = False
    access_notes: Optional[str] = None
    seating_sides: Optional[list[dict[str, Any]]] = None  # [{side, places, arrangement}]
    dishware_type: Optional[str] = Field(None, max_length=50)
    delivery_contents_notes: Optional[str] = None
    last_minute_items: Optional[str] = None
    equipment_dropoff_location: Optional[str] = None
    check_refrigerator: bool = False
    check_freezer: bool = False
    check_hot_plate: bool = False
    connect_gas: bool = False
    put_in_refrigerator: bool = False
    put_in_freezer: bool = False
    put_on_hot_plate: bool = False
    count_boxes: bool = False
    check_drinks: bool = False
    check_rolls: bool = False
    delivery_special_notes: Optional[str] = None
    selected_delivery_note_template_ids: Optional[List[int]] = None
    boxes: Optional[List[EventBoxCreate]] = None


class EventUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    event_category: Optional[str] = Field(None, min_length=1, max_length=100)
    menu_type: Optional[str] = None
    status: Optional[str] = None
    date: Optional[datetime] = None
    event_time: Optional[str] = None
    hebrew_date: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    guest_count: Optional[int] = Field(None, ge=1)
    is_real_dishes: Optional[bool] = None  # כלים אמיתיים
    is_morning_split: Optional[bool] = None
    notes: Optional[str] = None
    final_price: Optional[float] = Field(None, ge=0)  # מחיר סופי (ניתן לעריכה)
    owners: Optional[List[EventOwnerCreate]] = None
    venue_name: Optional[str] = None
    floor: Optional[int] = None
    has_elevator: Optional[bool] = None
    access_code: Optional[str] = None
    onsite_contact_name: Optional[str] = None
    onsite_contact_phone: Optional[str] = None
    hall_owner_name: Optional[str] = None
    hall_owner_phone: Optional[str] = None
    has_nearby_parking: Optional[bool] = None
    has_back_entrance: Optional[bool] = None
    requires_carts: Optional[bool] = None
    access_notes: Optional[str] = None
    seating_sides: Optional[list[dict[str, Any]]] = None  # [{side, places, arrangement}]
    dishware_type: Optional[str] = None
    delivery_contents_notes: Optional[str] = None
    last_minute_items: Optional[str] = None
    equipment_dropoff_location: Optional[str] = None
    check_refrigerator: Optional[bool] = None
    check_freezer: Optional[bool] = None
    check_hot_plate: Optional[bool] = None
    connect_gas: Optional[bool] = None
    put_in_refrigerator: Optional[bool] = None
    put_in_freezer: Optional[bool] = None
    put_on_hot_plate: Optional[bool] = None
    count_boxes: Optional[bool] = None
    check_drinks: Optional[bool] = None
    check_rolls: Optional[bool] = None
    delivery_special_notes: Optional[str] = None
    selected_delivery_note_template_ids: Optional[List[int]] = None
    boxes: Optional[List[EventBoxCreate]] = None


class EventStatusUpdate(BaseModel):
    status: str


class EventPriceUpdate(BaseModel):
    """Schema for updating only the final price of an event."""
    final_price: float = Field(..., ge=0, description="מחיר סופי לאירוע")


class MorningSplitUpdate(BaseModel):
    is_morning_split: bool


class EventResponse(BaseModel):
    id: int
    name: str
    event_category: Optional[str] = None
    menu_type: str
    status: str
    date: Optional[datetime] = None
    event_time: Optional[str] = None
    hebrew_date: Optional[str] = None
    day_sequence_number: int = 1
    day_sequence_color: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    guest_count: int = 1
    is_real_dishes: bool = False  # כלים אמיתיים
    is_morning_split: bool = False
    split_extra_charge: Optional[float] = None
    
    # Pricing fields
    base_price_per_guest: Optional[float] = None
    real_dishes_extra_per_guest: Optional[float] = 0.0  # תוספת כלים אמיתיים
    calculated_price: float = 0.0  # מחיר מחושב אוטומטית
    final_price: Optional[float] = None  # מחיר סופי (ניתן לעריכה)
    discount_percent: Optional[float] = 0.0  # אחוז הנחה
    discount_amount: Optional[float] = 0.0  # סכום ההנחה
    total_price: float = 0.0  # legacy field
    
    notes: Optional[str] = None
    venue_name: Optional[str] = None
    floor: Optional[int] = None
    has_elevator: bool = False
    access_code: Optional[str] = None
    onsite_contact_name: Optional[str] = None
    onsite_contact_phone: Optional[str] = None
    hall_owner_name: Optional[str] = None
    hall_owner_phone: Optional[str] = None
    has_nearby_parking: bool = False
    has_back_entrance: bool = False
    requires_carts: bool = False
    access_notes: Optional[str] = None
    seating_sides: Optional[list[dict[str, Any]]] = None  # [{side, places, arrangement}]
    dishware_type: Optional[str] = None
    delivery_contents_notes: Optional[str] = None
    last_minute_items: Optional[str] = None
    equipment_dropoff_location: Optional[str] = None
    check_refrigerator: bool = False
    check_freezer: bool = False
    check_hot_plate: bool = False
    connect_gas: bool = False
    put_in_refrigerator: bool = False
    put_in_freezer: bool = False
    put_on_hot_plate: bool = False
    count_boxes: bool = False
    check_drinks: bool = False
    check_rolls: bool = False
    delivery_special_notes: Optional[str] = None
    selected_delivery_note_template_ids: List[int] = []
    delivery_notes: List[EventDeliveryNoteResponse] = []
    boxes: List[EventBoxResponse] = []
    total_boxes: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # חישובים אוטומטיים
    waiter_count: int = 0   # 2 מלצרים לכל 50 סועדים
    table_count: int = 0    # שולחן לכל 8 סועדים

    dishes: List[EventDishResponse] = []
    owners: List[EventOwnerResponse] = []
    tray_selections: List[EventTrayResponse] = []
    calculation_settings: Optional[Any] = None
    has_calculation_snapshot: bool = False
    warnings: list[str] = []  # rule breaches shown to the user (not blocks)

    model_config = {"from_attributes": True}


# ─── Shopping / Equipment lists ───────────────────────────────────────

class ShoppingListItem(BaseModel):
    product_id: Optional[int] = None
    name: str
    quantity: float                            # כמות כוללת נדרשת (ביחידות המוצר)
    unit: str                                  # יחידת המוצר (ק"ג, ליטר וכו')
    category: Optional[str] = None
    estimated_price: float = 0.0
    package_quantity: Optional[float] = None   # כמות ביחידה/אריזה
    quantity_in_stock: float = 0.0             # כמה יש במלאי
    need_to_buy_quantity: float = 0.0          # כמה צריך לקנות (אחרי חיסור מלאי)
    packages_to_buy: int = 0                   # כמה חבילות/מארזים צריך לקנות
    source_type: Optional[str] = None
    formula_label: Optional[str] = None
    raw_quantity: Optional[float] = None


class ShoppingListResponse(BaseModel):
    event_id: int
    event_name: str
    items: List[ShoppingListItem]
    total_estimated_price: float


class EquipmentListItem(BaseModel):
    tool_id: Optional[int] = None
    name: str
    quantity: int
    category: Optional[str] = None
    available_in_stock: int = 0
    need_to_buy: int = 0
    source_type: Optional[str] = None
    formula_label: Optional[str] = None
    raw_quantity: Optional[float] = None
    is_reusable: bool = False
    reserved_quantity: int = 0
    available_after_reservations: int = 0
    shortage: int = 0


class EquipmentListResponse(BaseModel):
    event_id: int
    event_name: str
    items: List[EquipmentListItem]


class EventListResponse(BaseModel):
    items: List[EventResponse]
    total: int
    skip: int = 0
    limit: int = 50
