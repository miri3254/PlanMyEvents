"""
Dish service — CRUD for the dish catalog and its sub-entities.
"""

from typing import Optional

from sqlalchemy.orm import Session

from app.repositories.dish_repo import DishRepository
from app.repositories.audit_repo import AuditRepository
from app.models.dish import Dish, DishIngredient, ServingDish
from app.core.enums import AuditAction
from app.schemas.dish import (
    DishCreate, DishUpdate, DishResponse,
    DishIngredientCreate, DishIngredientUpdate,
    ServingDishCreate, ServingDishUpdate,
)
from app.utils.errors import AppException
from app.utils.app_logging import logger


class DishService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = DishRepository(db)
        self.audit = AuditRepository(db)

    def _get_or_404(self, dish_id: int) -> Dish:
        dish = self.repo.get_with_relations(dish_id)
        if not dish:
            raise AppException(404, "מנה לא נמצאה")
        return dish

    def _response(self, dish: Dish) -> dict:
        return DishResponse.from_model(dish).model_dump()

    def _sync_kosher_type(self, dish: Dish) -> None:
        """Derive a dish's kosher type from its linked products."""
        ingredient_types = {
            ingredient.product.kosher_type.value
            for ingredient in dish.ingredients
            if ingredient.product is not None
        }
        if "בשרי" in ingredient_types and "חלבי" not in ingredient_types:
            dish.kosher_type = "בשרי"
        elif "חלבי" in ingredient_types and "בשרי" not in ingredient_types:
            dish.kosher_type = "חלבי"
        elif ingredient_types == {"פרווה"}:
            dish.kosher_type = "פרווה"

    # ── LIST / GET ────────────────────────────────────────────────────

    def get_dishes(self, **kwargs) -> tuple[list[dict], int]:
        dishes, total = self.repo.get_list(**kwargs)
        return [self._response(d) for d in dishes], total

    def get_dish(self, dish_id: int) -> dict:
        dish = self._get_or_404(dish_id)
        return self._response(dish)

    # ── CREATE / UPDATE / DELETE ──────────────────────────────────────

    def create_dish(self, data: DishCreate) -> dict:
        dish_data = data.model_dump(exclude={"ingredients", "serving_dishes"})
        db_dish = Dish(**dish_data)
        self.repo.create(db_dish)
        self.db.flush()

        if data.ingredients:
            for ing_data in data.ingredients:
                ing = DishIngredient(dish_id=db_dish.id, **ing_data.model_dump())
                self.repo.add_ingredient(ing)

        self._sync_kosher_type(db_dish)

        if data.serving_dishes:
            for sd_data in data.serving_dishes:
                sd = ServingDish(dish_id=db_dish.id, **sd_data.model_dump())
                self.repo.add_serving_dish(sd)

        self.audit.log("dish", db_dish.id, AuditAction.CREATED.value)
        self.db.commit()
        self.db.refresh(db_dish)

        logger.info(f"מנה נוצרה: {db_dish.name} (ID={db_dish.id})")
        return self._response(self.repo.get_with_relations(db_dish.id))

    def update_dish(self, dish_id: int, data: DishUpdate) -> dict:
        dish = self._get_or_404(dish_id)
        update_data = data.model_dump(exclude_unset=True)
        self.repo.update(dish, update_data)
        self.audit.log("dish", dish_id, AuditAction.UPDATED.value)
        self.db.commit()
        return self._response(self.repo.get_with_relations(dish_id))

    def delete_dish(self, dish_id: int) -> dict:
        dish = self._get_or_404(dish_id)
        self.repo.soft_delete(dish)
        self.audit.log("dish", dish_id, AuditAction.DELETED.value)
        self.db.commit()
        return {"success": True, "message": "המנה נמחקה בהצלחה"}

    # ── INGREDIENTS ───────────────────────────────────────────────────

    def add_ingredient(self, dish_id: int, data: DishIngredientCreate) -> dict:
        self._get_or_404(dish_id)
        ing = DishIngredient(dish_id=dish_id, **data.model_dump())
        self.repo.add_ingredient(ing)
        self.db.flush()
        self._sync_kosher_type(self._get_or_404(dish_id))
        self.db.commit()
        return self._response(self.repo.get_with_relations(dish_id))

    def update_ingredient(self, dish_id: int, ingredient_id: int, data: DishIngredientUpdate) -> dict:
        self._get_or_404(dish_id)
        ing = self.repo.get_ingredient(dish_id, ingredient_id)
        if not ing:
            raise AppException(404, "מרכיב לא נמצא")
        for k, v in data.model_dump(exclude_unset=True).items():
            if hasattr(ing, k):
                setattr(ing, k, v)
        self.db.flush()
        self._sync_kosher_type(dish)
        self.db.commit()
        return self._response(self.repo.get_with_relations(dish_id))

    def remove_ingredient(self, dish_id: int, ingredient_id: int) -> dict:
        self._get_or_404(dish_id)
        ing = self.repo.get_ingredient(dish_id, ingredient_id)
        if not ing:
            raise AppException(404, "מרכיב לא נמצא")
        self.repo.delete_ingredient(ing)
        self.db.flush()
        self._sync_kosher_type(dish)
        self.db.commit()
        return {"success": True, "message": "המרכיב הוסר בהצלחה"}

    # ── SERVING DISHES ────────────────────────────────────────────────

    def add_serving_dish(self, dish_id: int, data: ServingDishCreate) -> dict:
        self._get_or_404(dish_id)
        sd = ServingDish(dish_id=dish_id, **data.model_dump())
        self.repo.add_serving_dish(sd)
        self.db.commit()
        return self._response(self.repo.get_with_relations(dish_id))

    def update_serving_dish(self, dish_id: int, serving_id: int, data: ServingDishUpdate) -> dict:
        self._get_or_404(dish_id)
        sd = self.repo.get_serving_dish(dish_id, serving_id)
        if not sd or sd.dish_id != dish_id:
            raise AppException(404, "כלי הגשה לא נמצא")
        for k, v in data.model_dump(exclude_unset=True).items():
            if hasattr(sd, k):
                setattr(sd, k, v)
        self.db.commit()
        return self._response(self.repo.get_with_relations(dish_id))

    def remove_serving_dish(self, dish_id: int, serving_id: int) -> dict:
        self._get_or_404(dish_id)
        sd = self.repo.get_serving_dish(dish_id, serving_id)
        if not sd or sd.dish_id != dish_id:
            raise AppException(404, "כלי הגשה לא נמצא")
        self.repo.delete_serving_dish(sd)
        self.db.commit()
        return {"success": True, "message": "כלי ההגשה הוסר בהצלחה"}
