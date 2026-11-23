"""
Menu repository — templates, categories, dish mappings.
"""

from typing import Optional, List

from sqlalchemy.orm import Session, joinedload, selectinload

from app.repositories.base_repo import BaseRepository
from app.models.menu import MenuTemplate, MenuCategory, MenuSubMeal, DishMenuMapping


class MenuRepository(BaseRepository[MenuTemplate]):
    def __init__(self, db: Session):
        super().__init__(MenuTemplate, db)

    def get_template_by_type(self, menu_type: str) -> Optional[MenuTemplate]:
        opts = [
            selectinload(MenuTemplate.sub_meals).selectinload(MenuSubMeal.categories),
            selectinload(MenuTemplate.categories),
        ]
        # Search by name first (UI now stores template name in events.menu_type)
        result = (
            self._active()
            .options(*opts)
            .filter(MenuTemplate.name == menu_type)
            .first()
        )
        if result:
            return result
        # Fallback to legacy menu_type field
        return (
            self._active()
            .options(*opts)
            .filter(MenuTemplate.menu_type == menu_type)
            .first()
        )

    def get_all_templates(self) -> List[MenuTemplate]:
        return (
            self._active()
            .options(
                selectinload(MenuTemplate.sub_meals).selectinload(MenuSubMeal.categories),
                selectinload(MenuTemplate.categories),
            )
            .all()
        )

    def get_category_by_id(self, category_id: int) -> Optional[MenuCategory]:
        return self.db.query(MenuCategory).filter(MenuCategory.id == category_id).first()

    def get_category_by_name(self, template_id: int, name: str) -> Optional[MenuCategory]:
        """Find category by internal name within a template (including sub-meals)."""
        return (
            self.db.query(MenuCategory)
            .filter(
                MenuCategory.name == name,
                (MenuCategory.template_id == template_id)
                | (
                    MenuCategory.sub_meal_id.in_(
                        self.db.query(MenuSubMeal.id).filter(
                            MenuSubMeal.template_id == template_id
                        )
                    )
                ),
            )
            .first()
        )

    def get_dishes_for_category(self, category_id: int) -> List[DishMenuMapping]:
        return (
            self.db.query(DishMenuMapping)
            .options(joinedload(DishMenuMapping.dish))
            .filter(
                DishMenuMapping.category_id == category_id,
                DishMenuMapping.is_deleted == False,  # noqa: E712
            )
            .order_by(DishMenuMapping.display_order)
            .all()
        )

    def get_sub_meal(self, sub_meal_id: int) -> Optional[MenuSubMeal]:
        return self.db.query(MenuSubMeal).filter(MenuSubMeal.id == sub_meal_id).first()
