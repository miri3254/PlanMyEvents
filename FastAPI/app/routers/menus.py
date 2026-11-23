"""
Menus router — CRUD for menu templates, categories, and dish mappings.
"""

from typing import Optional, Literal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.menu_service import MenuService

router = APIRouter(prefix="/menus", tags=["menus"])


def _svc(db: Session = Depends(get_db)) -> MenuService:
    return MenuService(db)


# ── Schemas for create / update ───────────────────────────────────────

class TableSettingItemSchema(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    quantity: float = Field(ge=0)
    quantity_basis: Literal["place_setting", "serving_group"] = "place_setting"
    disposable_tool_id: Optional[int] = Field(None, gt=0)
    real_tool_id: Optional[int] = Field(None, gt=0)


class MenuTemplateCreateSchema(BaseModel):
    table_setting_items: Optional[list[TableSettingItemSchema]] = None
    name: str
    description: Optional[str] = None
    min_guests: int = 1
    base_price_per_guest: Optional[float] = None
    is_tray_menu: bool = False
    kosher_type: str = "פרווה"  # בשרי/חלבי/פרווה


class MenuTemplateUpdateSchema(BaseModel):
    table_setting_items: Optional[list[TableSettingItemSchema]] = None
    name: Optional[str] = None
    description: Optional[str] = None
    min_guests: Optional[int] = None
    base_price_per_guest: Optional[float] = None
    is_tray_menu: Optional[bool] = None
    kosher_type: Optional[str] = None  # בשרי/חלבי/פרווה


class MenuCategoryCreateSchema(BaseModel):
    template_id: Optional[int] = None
    sub_meal_id: Optional[int] = None
    name: str
    name_hebrew: str
    description: Optional[str] = None
    display_order: int = 0
    quota: Optional[int] = None
    quota_description: Optional[str] = None
    is_required: bool = True
    tray_quantity: Optional[int] = None
    tray_price: Optional[float] = None


class MenuCategoryUpdateSchema(BaseModel):
    name: Optional[str] = None
    name_hebrew: Optional[str] = None
    description: Optional[str] = None
    display_order: Optional[int] = None
    quota: Optional[int] = None
    quota_description: Optional[str] = None
    is_required: Optional[bool] = None
    tray_quantity: Optional[int] = None
    tray_price: Optional[float] = None


class DishMappingCreateSchema(BaseModel):
    default_serving_mode: Optional[Literal["personal", "central"]] = None
    dish_id: int
    category_id: int
    is_upgrade: bool = False
    extra_charge: Optional[float] = None
    display_order: int = 0


class DishMappingUpdateSchema(BaseModel):
    default_serving_mode: Optional[Literal["personal", "central"]] = None
    is_upgrade: Optional[bool] = None
    extra_charge: Optional[float] = None
    display_order: Optional[int] = None


class SubMealCreateSchema(BaseModel):
    template_id: int
    name: str
    display_order: int = 0
    is_splittable: bool = False
    split_extra_charge: Optional[float] = None


class SubMealUpdateSchema(BaseModel):
    name: Optional[str] = None
    display_order: Optional[int] = None
    is_splittable: Optional[bool] = None
    split_extra_charge: Optional[float] = None


# ── Templates ─────────────────────────────────────────────────────────

@router.get("")
def get_all_templates(svc: MenuService = Depends(_svc)):
    return svc.get_all_templates()


@router.get("/by-type/{menu_type}")
def get_template_by_type(menu_type: str, svc: MenuService = Depends(_svc)):
    return svc.get_template(menu_type)


@router.get("/{template_id}")
def get_template_by_id(template_id: int, svc: MenuService = Depends(_svc)):
    return svc.get_template_by_id(template_id)


@router.post("", status_code=201)
def create_template(data: MenuTemplateCreateSchema, svc: MenuService = Depends(_svc)):
    return svc.create_template(data.model_dump())


@router.put("/{template_id}")
def update_template(template_id: int, data: MenuTemplateUpdateSchema, svc: MenuService = Depends(_svc)):
    return svc.update_template(template_id, data.model_dump(exclude_unset=True))


@router.delete("/{template_id}")
def delete_template(template_id: int, svc: MenuService = Depends(_svc)):
    return svc.delete_template(template_id)


# ── Sub-Meals (סעודות משנה) ───────────────────────────────────────────

@router.get("/sub-meals/{sub_meal_id}")
def get_sub_meal(sub_meal_id: int, svc: MenuService = Depends(_svc)):
    return svc.get_sub_meal(sub_meal_id)


@router.post("/sub-meals", status_code=201)
def create_sub_meal(data: SubMealCreateSchema, svc: MenuService = Depends(_svc)):
    return svc.create_sub_meal(data.model_dump())


@router.put("/sub-meals/{sub_meal_id}")
def update_sub_meal(sub_meal_id: int, data: SubMealUpdateSchema, svc: MenuService = Depends(_svc)):
    return svc.update_sub_meal(sub_meal_id, data.model_dump(exclude_unset=True))


@router.delete("/sub-meals/{sub_meal_id}")
def delete_sub_meal(sub_meal_id: int, svc: MenuService = Depends(_svc)):
    return svc.delete_sub_meal(sub_meal_id)


# ── Categories ────────────────────────────────────────────────────────

@router.get("/categories/all")
def get_all_categories_grouped(svc: MenuService = Depends(_svc)):
    """All categories grouped by menu type — used for dish assignment UI."""
    return svc.get_all_categories_grouped()


@router.get("/categories/{category_id}/dishes")
def get_dishes_for_category(
    category_id: int,
    include_upgrades: bool = Query(True),
    svc: MenuService = Depends(_svc),
):
    return svc.get_dishes_for_category(category_id, include_upgrades)


@router.post("/categories", status_code=201)
def create_category(data: MenuCategoryCreateSchema, svc: MenuService = Depends(_svc)):
    return svc.create_category(data.model_dump())


@router.put("/categories/{category_id}")
def update_category(category_id: int, data: MenuCategoryUpdateSchema, svc: MenuService = Depends(_svc)):
    return svc.update_category(category_id, data.model_dump(exclude_unset=True))


@router.delete("/categories/{category_id}")
def delete_category(category_id: int, svc: MenuService = Depends(_svc)):
    return svc.delete_category(category_id)


@router.post("/categories/{category_id}/validate")
def validate_selection(
    category_id: int,
    count: int = Query(...),
    guest_count: int = Query(0),
    svc: MenuService = Depends(_svc),
):
    return svc.validate_selection(category_id, count, guest_count)


# ── Dish Mappings ─────────────────────────────────────────────────────

@router.post("/dish-mappings", status_code=201)
def add_dish_mapping(data: DishMappingCreateSchema, svc: MenuService = Depends(_svc)):
    return svc.add_dish_mapping(data.model_dump())


@router.put("/dish-mappings/{mapping_id}")
def update_dish_mapping(mapping_id: int, data: DishMappingUpdateSchema, svc: MenuService = Depends(_svc)):
    return svc.update_dish_mapping(mapping_id, data.model_dump(exclude_unset=True))


@router.delete("/dish-mappings/{mapping_id}")
def remove_dish_mapping(mapping_id: int, svc: MenuService = Depends(_svc)):
    return svc.remove_dish_mapping(mapping_id)
