"""
Dish schemas — dish, ingredients, serving dishes.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime


# ─── Ingredient ───────────────────────────────────────────────────────

class DishIngredientCreate(BaseModel):
    product_id: Optional[int] = None
    name: Optional[str] = Field(None, max_length=255)
    quantity: float = Field(default=1.0, ge=0)
    unit: str = Field(default="יחידות", max_length=50)
    is_serving_component: bool = False


class DishIngredientUpdate(BaseModel):
    product_id: Optional[int] = None
    name: Optional[str] = Field(None, max_length=255)
    quantity: Optional[float] = Field(None, ge=0)
    unit: Optional[str] = Field(None, max_length=50)
    is_serving_component: Optional[bool] = None


class DishIngredientResponse(BaseModel):
    id: int
    product_id: Optional[int] = None
    name: Optional[str] = None
    quantity: float
    unit: str
    is_serving_component: bool = False
    product: Optional[Any] = None     # ProductResponse when loaded

    model_config = {"from_attributes": True}


# ─── Serving Dish ─────────────────────────────────────────────────────

class ServingDishCreate(BaseModel):
    tool_id: Optional[int] = None
    name: Optional[str] = Field(None, max_length=255)
    quantity: int = Field(default=1, ge=1)


class ServingDishUpdate(BaseModel):
    tool_id: Optional[int] = None
    name: Optional[str] = Field(None, max_length=255)
    quantity: Optional[int] = Field(None, ge=1)


class ServingDishResponse(BaseModel):
    id: int
    tool_id: Optional[int] = None
    name: Optional[str] = None
    quantity: int
    tool: Optional[Any] = None

    model_config = {"from_attributes": True}


# ─── Dish Menu Mapping Info ───────────────────────────────────────────

class DishMenuMappingInfo(BaseModel):
    """Info about which menu categories a dish is linked to."""
    mapping_id: int
    category_id: int
    category_name_hebrew: str
    menu_type: str
    template_name: str
    sub_meal_name: Optional[str] = None
    is_upgrade: bool = False
    extra_charge: Optional[float] = None
    display_order: int = 0


# ─── Dish ─────────────────────────────────────────────────────────────

class DishCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    kosher_type: str = Field(default="פרווה")
    base_price: Optional[float] = Field(None, ge=0)
    client_price: Optional[float] = Field(None, ge=0)
    serving_size: float = Field(default=1.0, ge=0)
    serving_description: Optional[str] = None
    waiter_notes: Optional[str] = None
    is_active: bool = True
    ingredients: Optional[List["DishIngredientCreate"]] = []
    serving_dishes: Optional[List["ServingDishCreate"]] = []


class DishUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    kosher_type: Optional[str] = None
    base_price: Optional[float] = Field(None, ge=0)
    client_price: Optional[float] = Field(None, ge=0)
    serving_size: Optional[float] = Field(None, ge=0)
    serving_description: Optional[str] = None
    waiter_notes: Optional[str] = None
    is_active: Optional[bool] = None


class DishActiveUpdate(BaseModel):
    is_active: bool


class DishResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    kosher_type: str = "פרווה"
    base_price: Optional[float] = None
    client_price: Optional[float] = None
    serving_size: float = 1.0
    serving_description: Optional[str] = None
    waiter_notes: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    ingredients: List[DishIngredientResponse] = []
    serving_dishes: List[ServingDishResponse] = []
    menu_mappings: List[DishMenuMappingInfo] = []

    model_config = {"from_attributes": True}

    @staticmethod
    def from_model(dish, product_map: dict | None = None, tool_map: dict | None = None) -> "DishResponse":
        """Build a full response from an ORM dish with eager-loaded relationships."""
        from app.schemas.product import ProductResponse
        from app.schemas.tool import ToolResponse

        ingredients = []
        for i in dish.ingredients:
            prod = None
            if i.product and i.product_id:
                prod = ProductResponse.from_model(i.product)
            ingredients.append(DishIngredientResponse(
                id=i.id,
                product_id=i.product_id,
                name=i.name,
                quantity=i.quantity,
                unit=i.unit.value if hasattr(i.unit, "value") else str(i.unit),
                is_serving_component=i.is_serving_component,
                product=prod,
            ))

        serving = []
        for s in dish.serving_dishes:
            t = None
            if s.tool and s.tool_id:
                t = ToolResponse.from_model(s.tool)
            serving.append(ServingDishResponse(
                id=s.id,
                tool_id=s.tool_id,
                name=s.name,
                quantity=s.quantity,
                tool=t,
            ))

        # Build menu mappings info
        mappings_info = []
        if hasattr(dish, 'menu_mappings') and dish.menu_mappings:
            for m in dish.menu_mappings:
                if m.is_deleted:
                    continue
                cat = m.category if hasattr(m, 'category') and m.category else None
                if not cat:
                    continue
                # Determine template: category may be linked via sub_meal or directly
                template = None
                sub_meal_name = None
                if hasattr(cat, 'sub_meal') and cat.sub_meal:
                    sub_meal_name = cat.sub_meal.name
                    template = cat.sub_meal.template if hasattr(cat.sub_meal, 'template') else None
                if not template and hasattr(cat, 'template') and cat.template:
                    template = cat.template
                mappings_info.append(DishMenuMappingInfo(
                    mapping_id=m.id,
                    category_id=cat.id,
                    category_name_hebrew=cat.name_hebrew,
                    menu_type=template.menu_type.value if template and hasattr(template.menu_type, 'value') else str(template.menu_type) if template else '',
                    template_name=template.name if template else '',
                    sub_meal_name=sub_meal_name,
                    is_upgrade=m.is_upgrade,
                    extra_charge=m.extra_charge,
                    display_order=m.display_order,
                ))

        return DishResponse(
            id=dish.id,
            name=dish.name,
            description=dish.description,
            kosher_type=dish.kosher_type.value if hasattr(dish.kosher_type, "value") else str(dish.kosher_type),
            base_price=dish.base_price,
            client_price=dish.client_price,
            serving_size=dish.serving_size,
            serving_description=dish.serving_description,
            waiter_notes=dish.waiter_notes,
            is_active=dish.is_active,
            created_at=dish.created_at,
            updated_at=dish.updated_at,
            ingredients=ingredients,
            serving_dishes=serving,
            menu_mappings=mappings_info,
        )


class DishListResponse(BaseModel):
    items: List[DishResponse]
    total: int
    skip: int = 0
    limit: int = 50
