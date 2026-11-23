"""Schemas for event calculation settings, results, and serving sets."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, model_validator


class EventCalculationSettingsBase(BaseModel):
    drinks_enabled: bool = True
    drink_types: Optional[dict[str, bool]] = None
    orange_flavored_mode: str = Field(default="both", pattern="^(orange|flavored|both)$")
    rolls_enabled: bool = True
    roll_splits: Optional[list[dict[str, Any]]] = None
    table_shape: str = Field(default="rectangle", pattern="^(square|round|rectangle)$")
    tablecloth_tool_id: Optional[int] = None
    use_rectangular_for_square: bool = False
    table_overrides: Optional[list[dict[str, Any]]] = None
    event_tool_set_items: Optional[list[dict[str, Any]]] = None
    credit_card_enabled: bool = False
    credit_card_amount: Optional[float] = Field(None, ge=0)
    credit_card_installments: int = Field(1, ge=1, le=6)
    credit_card_rate: Optional[float] = Field(None, ge=0, le=100)
    credit_card_vat_multiplier: float = Field(1.18, ge=1, le=2)
    notes: Optional[str] = None


class EventCalculationSettingsUpdate(EventCalculationSettingsBase):
    @model_validator(mode="after")
    def validate_roll_splits(self):
        if self.roll_splits:
            total = sum(float(row.get("percent") or 0) for row in self.roll_splits)
            if round(total, 4) != 100:
                raise ValueError("roll_splits percentages must sum to 100")
        return self


class EventCalculationSettingsResponse(EventCalculationSettingsBase):
    id: int
    event_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class CalculationRequirement(BaseModel):
    source_type: str
    item_type: str
    name: str
    quantity: float
    unit: str
    formula_label: Optional[str] = None
    raw_quantity: Optional[float] = None
    product_id: Optional[int] = None
    tool_id: Optional[int] = None
    category: Optional[str] = None
    is_reusable: bool = False
    available_in_stock: float = 0
    reserved_quantity: float = 0
    available_after_reservations: float = 0
    shortage: float = 0
    estimated_price: float = 0
    package_quantity: Optional[float] = None
    need_to_buy_quantity: float = 0
    packages_to_buy: int = 0
    details: Optional[dict[str, Any]] = None


class CalculationCharge(BaseModel):
    source_type: str
    name: str
    amount: float
    formula_label: Optional[str] = None
    details: Optional[dict[str, Any]] = None


class EventCalculationSummary(BaseModel):
    event_id: int
    event_name: str
    settings: Optional[EventCalculationSettingsResponse] = None
    has_approved_snapshot: bool = False
    waiter_count: int = 0
    table_count: int = 0
    production_cost: Optional[float] = None
    estimated_profit: Optional[float] = None
    revenue: Optional[float] = None
    table_formula_label: Optional[str] = None
    waiter_formula_label: Optional[str] = None
    product_requirements: list[CalculationRequirement] = []
    tool_requirements: list[CalculationRequirement] = []
    charge_requirements: list[CalculationCharge] = []
    warnings: list[str] = []
    formula_trace: list[dict[str, Any]] = []


class DishServingSetItemBase(BaseModel):
    tool_id: Optional[int] = None
    name: Optional[str] = Field(None, max_length=255)
    quantity: float = Field(default=1, ge=0)
    quantity_basis: str = Field(default="dish_unit", pattern="^(event|table|guest|dish_unit|tray|place_setting|serving_group)$")
    is_reusable: Optional[bool] = None


class DishServingSetItemCreate(DishServingSetItemBase):
    pass


class DishServingSetItemResponse(DishServingSetItemBase):
    id: int
    set_id: int

    model_config = {"from_attributes": True}


class DishServingSetCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    set_type: str = Field(default="serving", pattern="^(serving|packaging)$")
    is_default: bool = False
    dishware_type: Optional[str] = Field(None, max_length=50)
    serving_mode: Optional[str] = Field(None, pattern="^(personal|central)$")
    notes: Optional[str] = None
    items: list[DishServingSetItemCreate] = []


class DishServingSetResponse(BaseModel):
    id: int
    dish_id: int
    name: str
    set_type: str
    is_default: bool
    dishware_type: Optional[str] = None
    serving_mode: Optional[str] = None
    notes: Optional[str] = None
    items: list[DishServingSetItemResponse] = []

    model_config = {"from_attributes": True}


class DishCalculationRuleCreate(BaseModel):
    rule_type: str = Field(..., min_length=1, max_length=80)
    product_id: Optional[int] = None
    name: Optional[str] = Field(None, max_length=255)
    params: Optional[dict[str, Any]] = None
    replaces_ingredient_product_id: Optional[int] = None
    is_active: bool = True


class DishCalculationRuleResponse(DishCalculationRuleCreate):
    id: int
    dish_id: int

    model_config = {"from_attributes": True}


class EventDishServingSelectionUpdate(BaseModel):
    event_dish_id: Optional[int] = None
    event_tray_selection_id: Optional[int] = None
    dish_id: int
    set_id: Optional[int] = None
    set_type: str = Field(default="serving", pattern="^(serving|packaging)$")


class EventManualToolRowUpdate(BaseModel):
    tool_id: Optional[int] = None
    name: Optional[str] = Field(None, max_length=255)
    quantity: int = Field(default=1, ge=1)
    is_reusable: bool = False
    notes: Optional[str] = None


class EventManualToolRowsRequest(BaseModel):
    rows: list[EventManualToolRowUpdate] = []


class EventDishServingSelectionsRequest(BaseModel):
    selections: list[EventDishServingSelectionUpdate] = []
