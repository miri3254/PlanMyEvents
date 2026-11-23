"""
Dish repository — data access for Dish and sub-entities.
"""

from typing import Optional, List

from sqlalchemy.orm import Session, selectinload, joinedload

from app.repositories.base_repo import BaseRepository
from app.models.dish import Dish, DishIngredient, ServingDish
from app.models.menu import DishMenuMapping, MenuCategory, MenuSubMeal, MenuTemplate


class DishRepository(BaseRepository[Dish]):
    def __init__(self, db: Session):
        super().__init__(Dish, db)

    def _eager_query(self):
        return self._active().options(
            selectinload(Dish.ingredients).joinedload(DishIngredient.product),
            selectinload(Dish.serving_dishes).joinedload(ServingDish.tool),
            selectinload(Dish.menu_mappings)
                .joinedload(DishMenuMapping.category)
                .joinedload(MenuCategory.sub_meal)
                .joinedload(MenuSubMeal.template),
            selectinload(Dish.menu_mappings)
                .joinedload(DishMenuMapping.category)
                .joinedload(MenuCategory.template),
        )

    def get_with_relations(self, dish_id: int) -> Optional[Dish]:
        return self._eager_query().filter(Dish.id == dish_id).first()

    def get_list(
        self,
        category: Optional[str] = None,
        kosher_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[List[Dish], int]:
        q = self._eager_query()
        count_q = self._active()

        if is_active is not None:
            q = q.filter(Dish.is_active == is_active)
            count_q = count_q.filter(Dish.is_active == is_active)
        if kosher_type:
            q = q.filter(Dish.kosher_type == kosher_type)
            count_q = count_q.filter(Dish.kosher_type == kosher_type)
        if search:
            q = q.filter(Dish.name.contains(search))
            count_q = count_q.filter(Dish.name.contains(search))

        total = count_q.count()
        dishes = q.offset(skip).limit(limit).all()
        return dishes, total

    # ── ingredients ───────────────────────────────────────────────────

    def get_ingredient(self, dish_id: int, ingredient_id: int) -> Optional[DishIngredient]:
        return (
            self.db.query(DishIngredient)
            .filter(DishIngredient.id == ingredient_id, DishIngredient.dish_id == dish_id)
            .first()
        )

    def add_ingredient(self, ingredient: DishIngredient) -> DishIngredient:
        self.db.add(ingredient)
        self.db.flush()
        return ingredient

    def delete_ingredient(self, ingredient: DishIngredient) -> None:
        self.db.delete(ingredient)
        self.db.flush()

    # ── serving dishes ────────────────────────────────────────────────

    def get_serving_dish(self, dish_id: int, serving_id: int) -> Optional[ServingDish]:
        return (
            self.db.query(ServingDish)
            .filter(ServingDish.id == serving_id, ServingDish.dish_id == dish_id)
            .first()
        )

    def add_serving_dish(self, serving: ServingDish) -> ServingDish:
        self.db.add(serving)
        self.db.flush()
        return serving

    def delete_serving_dish(self, serving: ServingDish) -> None:
        self.db.delete(serving)
        self.db.flush()
