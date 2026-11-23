"""
Menu schemas — templates, sub-meals, categories.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime


# ─── MenuCategory ─────────────────────────────────────────────────────

class MenuCategoryResponse(BaseModel):
    id: int
    name: str
    name_hebrew: str
    description: Optional[str] = None
    display_order: int = 0
    quota: Optional[int] = None
    quota_description: Optional[str] = None
    guest_count_rules: Optional[dict] = None
    is_required: bool = True
    tray_quantity: Optional[int] = None
    tray_price: Optional[float] = None

    model_config = {"from_attributes": True}


# ─── MenuSubMeal ──────────────────────────────────────────────────────

class MenuSubMealResponse(BaseModel):
    id: int
    name: str
    display_order: int = 0
    is_splittable: bool = False
    split_extra_charge: Optional[float] = None
    categories: List[MenuCategoryResponse] = []

    model_config = {"from_attributes": True}


# ─── MenuTemplate ────────────────────────────────────────────────────

class MenuTemplateResponse(BaseModel):
    table_setting_items: Optional[list[dict]] = None
    tablecloth_profile: str = 'regular'
    id: int
    menu_type: str
    name: str
    description: Optional[str] = None
    min_guests: int = 1
    base_price_per_guest: Optional[float] = None
    real_dishes_extra_per_guest: Optional[float] = 0.0  # תוספת כלים אמיתיים לסועד
    is_tray_menu: bool = False
    kosher_type: str = "פרווה"  # בשרי/חלבי/פרווה
    sub_meals: List[MenuSubMealResponse] = []
    categories: List[MenuCategoryResponse] = []   # direct categories (non-sub-meal)

    model_config = {"from_attributes": True}

    @staticmethod
    def from_model(template) -> "MenuTemplateResponse":
        sub_meals = []
        for sm in template.sub_meals:
            cats = [MenuCategoryResponse.model_validate(c) for c in sm.categories]
            sub_meals.append(MenuSubMealResponse(
                id=sm.id,
                name=sm.name,
                display_order=sm.display_order,
                is_splittable=sm.is_splittable,
                split_extra_charge=sm.split_extra_charge,
                categories=cats,
            ))

        # Direct categories (those not belonging to a sub-meal)
        direct_cats = [
            MenuCategoryResponse.model_validate(c)
            for c in template.categories
            if c.sub_meal_id is None
        ]

        return MenuTemplateResponse(
            id=template.id,
            menu_type=template.menu_type.value if hasattr(template.menu_type, "value") else str(template.menu_type),
            name=template.name,
            tablecloth_profile=template.tablecloth_profile,
            table_setting_items=template.table_setting_items,
            description=template.description,
            min_guests=template.min_guests,
            base_price_per_guest=template.base_price_per_guest,
            real_dishes_extra_per_guest=getattr(template, 'real_dishes_extra_per_guest', 0.0) or 0.0,
            is_tray_menu=template.is_tray_menu,
            kosher_type=getattr(template, 'kosher_type', 'פרווה') or 'פרווה',
            sub_meals=sub_meals,
            categories=direct_cats,
        )


# ─── Dish-for-category listing ───────────────────────────────────────

class CategoryDishItem(BaseModel):
    """A dish as it appears within a specific menu category."""
    dish_id: int
    name: str
    description: Optional[str] = None
    kosher_type: str = "פרווה"
    is_upgrade: bool = False
    extra_charge: Optional[float] = None
    client_price: Optional[float] = None
    serving_size: float = 1.0
    display_order: int = 0


class CategoryDishesResponse(BaseModel):
    category_id: int
    category_name: str
    category_name_hebrew: str
    quota: Optional[int] = None
    quota_description: Optional[str] = None
    standard_dishes: List[CategoryDishItem] = []
    upgrade_dishes: List[CategoryDishItem] = []


# ─── Validation ───────────────────────────────────────────────────────

class ValidateSelectionRequest(BaseModel):
    event_id: int
    category_name: str
    dish_ids: List[int]


class ValidateSelectionResponse(BaseModel):
    valid: bool
    quota: Optional[int] = None
    current_count: int = 0
    message: Optional[str] = None


# ─── Progress ─────────────────────────────────────────────────────────

class CategoryProgress(BaseModel):
    category_id: int
    category_name: str
    name_hebrew: str
    quota: Optional[int] = None
    selected_count: int = 0
    is_complete: bool = False


class EventMenuProgress(BaseModel):
    event_id: int
    menu_type: str
    total_categories: int = 0
    completed_categories: int = 0
    progress_percent: float = 0.0
    categories: List[CategoryProgress] = []
    sub_meals: Optional[List[dict]] = None
