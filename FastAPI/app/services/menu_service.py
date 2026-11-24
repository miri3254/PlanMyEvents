from app.services.table_setting_rules import default_table_setting_items
"""
Menu service — CRUD for menu templates, categories, dish mappings, and validation.
"""

from typing import Optional, List

from sqlalchemy.orm import Session

from app.repositories.menu_repo import MenuRepository
from app.models.menu import MenuTemplate, MenuSubMeal, MenuCategory, DishMenuMapping
from app.models.dish import Dish
from app.core.constants import GUEST_COUNT_RULES
from app.utils.errors import AppException
from app.utils.app_logging import logger
from app.services.tablecloth_rules import LEGACY_PROFILES


class MenuService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = MenuRepository(db)

    # ── Templates ─────────────────────────────────────────────────────

    def get_all_templates(self) -> list[dict]:
        templates = self.repo.get_all_templates()
        return [self._template_response(t) for t in templates]

    def get_template(self, menu_type: str) -> dict:
        t = self.repo.get_template_by_type(menu_type)
        if not t:
            raise AppException(404, "תבנית תפריט לא נמצאה")
        return self._template_response(t)

    def get_template_by_id(self, template_id: int) -> dict:
        t = (
            self.db.query(MenuTemplate)
            .filter(MenuTemplate.id == template_id, MenuTemplate.is_deleted == False)  # noqa: E712
            .first()
        )
        if not t:
            raise AppException(404, "תבנית תפריט לא נמצאה")
        return self._template_response(t)

    def _template_response(self, t: MenuTemplate) -> dict:
        sub_meals = []
        for sm in t.sub_meals:
            categories = []
            for cat in sm.categories:
                mappings = self.repo.get_dishes_for_category(cat.id)
                dishes_data = []
                for m in mappings:
                    dish = self.db.query(Dish).filter(Dish.id == m.dish_id).first()
                    if dish and not dish.is_deleted:
                        dishes_data.append({
                            "id": m.id,
                            "dish_id": m.dish_id,
                            "dish_name": dish.name,
                            "dish_kosher_type": dish.kosher_type.value if hasattr(dish.kosher_type, "value") else str(dish.kosher_type),
                            "default_serving_mode": m.default_serving_mode,
                            "is_upgrade": m.is_upgrade,
                            "extra_charge": m.extra_charge,
                            "base_price": dish.base_price,
                            "dish_client_price": dish.client_price,
                        })
                categories.append({
                    "id": cat.id,
                    "name": cat.name,
                    "name_hebrew": cat.name_hebrew,
                    "display_order": cat.display_order,
                    "quota": cat.quota,
                    "is_required": cat.is_required,
                    "tray_quantity": cat.tray_quantity,
                    "tray_price": cat.tray_price,
                    "guest_count_rules": cat.guest_count_rules,
                    "dish_mappings": dishes_data,
                })
            sub_meals.append({
                "id": sm.id,
                "name": sm.name,
                "display_order": sm.display_order,
                "is_splittable": sm.is_splittable,
                "split_extra_charge": sm.split_extra_charge,
                "categories": categories,
            })
        
        # Direct categories (not inside a sub-meal)
        direct_categories = []
        for cat in t.categories:
            # Only include categories that don't belong to a sub-meal
            if cat.sub_meal_id is None:
                mappings = self.repo.get_dishes_for_category(cat.id)
                dishes_data = []
                for m in mappings:
                    dish = self.db.query(Dish).filter(Dish.id == m.dish_id).first()
                    if dish and not dish.is_deleted:
                        dishes_data.append({
                            "id": m.id,
                            "dish_id": m.dish_id,
                            "dish_name": dish.name,
                            "dish_kosher_type": dish.kosher_type.value if hasattr(dish.kosher_type, "value") else str(dish.kosher_type),
                            "default_serving_mode": m.default_serving_mode,
                            "is_upgrade": m.is_upgrade,
                            "extra_charge": m.extra_charge,
                            "base_price": dish.base_price,
                            "dish_client_price": dish.client_price,
                        })
                direct_categories.append({
                    "id": cat.id,
                    "name": cat.name,
                    "name_hebrew": cat.name_hebrew,
                    "display_order": cat.display_order,
                    "quota": cat.quota,
                    "quota_description": cat.quota_description,
                    "is_required": cat.is_required,
                    "tray_quantity": cat.tray_quantity,
                    "tray_price": cat.tray_price,
                    "guest_count_rules": cat.guest_count_rules,
                    "dish_mappings": dishes_data,
                })
        
        return {
            "id": t.id,
            "menu_type": t.menu_type.value if hasattr(t.menu_type, "value") else str(t.menu_type),
            "name": t.name,
            "tablecloth_profile": t.tablecloth_profile,
            "table_setting_items": t.table_setting_items if t.table_setting_items is not None else default_table_setting_items(t.tablecloth_profile),
            "min_guests": t.min_guests,
            "base_price_per_guest": t.base_price_per_guest,
            "is_tray_menu": t.is_tray_menu,
            "kosher_type": getattr(t, 'kosher_type', 'פרווה') or 'פרווה',
            "sub_meals": sub_meals,
            "categories": direct_categories,
        }

    # ── Dishes for a category (standard vs upgrades) ──────────────────

    def get_all_categories_grouped(self) -> list[dict]:
        """Return all categories grouped by menu template, for dish assignment UI."""
        templates = self.repo.get_all_templates()
        result = []
        for t in templates:
            menu_type = t.menu_type.value if hasattr(t.menu_type, "value") else str(t.menu_type)
            categories = []

            # Direct categories (non-sub-meal templates)
            for cat in (t.categories or []):
                categories.append({
                    "id": cat.id,
                    "name_hebrew": cat.name_hebrew,
                    "name": cat.name,
                    "sub_meal_name": None,
                })

            # Sub-meal categories
            for sm in (t.sub_meals or []):
                for cat in (sm.categories or []):
                    categories.append({
                        "id": cat.id,
                        "name_hebrew": cat.name_hebrew,
                        "name": cat.name,
                        "sub_meal_name": sm.name,
                    })

            result.append({
                "template_id": t.id,
                "menu_type": menu_type,
                "template_name": t.name,
                "categories": categories,
            })
        return result

    def get_dishes_for_category(
        self, category_id: int, include_upgrades: bool = True
    ) -> dict:
        """Return dishes for a category, separated into standard and upgrade lists."""
        category = self.db.query(MenuCategory).filter(MenuCategory.id == category_id).first()
        if not category:
            raise AppException(404, "קטגוריה לא נמצאה")

        mappings = self.repo.get_dishes_for_category(category_id)
        standard_dishes = []
        upgrade_dishes = []

        for m in mappings:
            dish = self.db.query(Dish).filter(Dish.id == m.dish_id).first()
            if dish and not dish.is_deleted:
                dish_info = {
                    "mapping_id": m.id,
                    "dish_id": m.dish_id,
                    "dish_name": dish.name,
                    "dish_kosher_type": dish.kosher_type.value if hasattr(dish.kosher_type, "value") else str(dish.kosher_type),
                    "default_serving_mode": m.default_serving_mode,
                            "is_upgrade": m.is_upgrade,
                    "extra_charge": m.extra_charge,
                    "base_price": dish.base_price,
                    "dish_client_price": dish.client_price,
                    "dish_serving_size": dish.serving_size if hasattr(dish, 'serving_size') else None,
                    "dish_description": dish.description if hasattr(dish, 'description') else None,
                    "display_order": m.display_order,
                }
                if m.is_upgrade:
                    upgrade_dishes.append(dish_info)
                else:
                    standard_dishes.append(dish_info)

        return {
            "category_id": category.id,
            "category_name": category.name,
            "category_name_hebrew": category.name_hebrew,
            "quota": category.quota,
            "quota_description": category.quota_description,
            "standard_dishes": standard_dishes,
            "upgrade_dishes": upgrade_dishes if include_upgrades else [],
        }

    # ── Validation ────────────────────────────────────────────────────

    def validate_selection(self, category_id: int, count: int, guest_count: int = 0) -> dict:
        """Check if a number of selected dishes matches the category quota."""
        cat = self.db.query(MenuCategory).filter(MenuCategory.id == category_id).first()
        if not cat:
            raise AppException(404, "קטגוריה לא נמצאה")

        effective_quota = self._effective_quota(cat, guest_count)
        ok = count <= effective_quota if effective_quota else True
        return {
            "category_id": cat.id,
            "category_name": cat.name_hebrew,
            "quota": effective_quota,
            "selected": count,
            "is_valid": ok,
            "message": "" if ok else f"בקטגוריה '{cat.name_hebrew}' ניתן לבחור עד {effective_quota} מנות, נבחרו {count}",
        }

    def get_category_progress(self, category_id: int, selected_count: int, guest_count: int = 0) -> dict:
        cat = self.db.query(MenuCategory).filter(MenuCategory.id == category_id).first()
        if not cat:
            raise AppException(404, "קטגוריה לא נמצאה")
        effective_quota = self._effective_quota(cat, guest_count)
        return {
            "category_id": cat.id,
            "category_name": cat.name_hebrew,
            "quota": effective_quota,
            "selected": selected_count,
            "remaining": max(0, (effective_quota or 0) - selected_count),
        }

    def _effective_quota(self, cat: MenuCategory, guest_count: int) -> Optional[int]:
        """Apply guest_count_rules to adjust quota dynamically."""
        base_quota = cat.quota
        if not base_quota:
            return None

        rules = cat.guest_count_rules
        if rules and guest_count:
            threshold = rules.get("threshold")
            bonus = rules.get("bonus_quota", 0)
            if threshold and guest_count > threshold:
                return base_quota + bonus

        return base_quota

    # ── Template CRUD ─────────────────────────────────────────────────

    def _validate_table_setting_tools(self, data):
        from app.models.tool import Tool
        for row in data.get("table_setting_items") or []:
            for key in ("real_tool_id", "disposable_tool_id"):
                if row.get(key) and not self.db.query(Tool).filter(Tool.id == row[key], Tool.is_deleted == False).first():
                    raise AppException(422, "כלי עריכה מקושר אינו קיים במלאי")

    def create_template(self, data: dict) -> dict:
        self._validate_table_setting_tools(data)
        # menu_type is derived from name (internal, not exposed to UI)
        data['menu_type'] = data.get('name', '')
        data['tablecloth_profile'] = LEGACY_PROFILES.get(data['menu_type'].strip(), 'regular')
        template = MenuTemplate(**data)
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        logger.info(f"תבנית תפריט נוצרה: {template.name} (ID={template.id})")
        return self._template_response(template)

    def update_template(self, template_id: int, data: dict) -> dict:
        self._validate_table_setting_tools(data)
        # Calculation rules are automatic, not an editable user setting.
        data.pop('tablecloth_profile', None)
        t = (
            self.db.query(MenuTemplate)
            .filter(MenuTemplate.id == template_id, MenuTemplate.is_deleted == False)  # noqa: E712
            .first()
        )
        if not t:
            raise AppException(404, "תבנית תפריט לא נמצאה")
        # Keep menu_type stable when the display name changes. Existing events
        # may still reference this key; lookups also accept the current name.
        for key, value in data.items():
            setattr(t, key, value)
        self.db.commit()
        self.db.refresh(t)
        logger.info(f"תבנית תפריט עודכנה: {t.name} (ID={t.id})")
        return self._template_response(t)

    def delete_template(self, template_id: int) -> dict:
        t = (
            self.db.query(MenuTemplate)
            .filter(MenuTemplate.id == template_id, MenuTemplate.is_deleted == False)  # noqa: E712
            .first()
        )
        if not t:
            raise AppException(404, "תבנית תפריט לא נמצאה")
        t.is_deleted = True
        self.db.commit()
        logger.info(f"תבנית תפריט נמחקה: {t.name} (ID={t.id})")
        return {"message": "תבנית תפריט נמחקה בהצלחה"}

    # ── SubMeal CRUD ──────────────────────────────────────────────────

    def get_sub_meal(self, sub_meal_id: int) -> dict:
        sm = self.db.query(MenuSubMeal).filter(MenuSubMeal.id == sub_meal_id).first()
        if not sm:
            raise AppException(404, "תת-סעודה לא נמצאה")
        return self._sub_meal_response(sm)

    def _sub_meal_response(self, sm: MenuSubMeal) -> dict:
        return {
            "id": sm.id,
            "template_id": sm.template_id,
            "name": sm.name,
            "display_order": sm.display_order,
            "is_splittable": sm.is_splittable,
            "split_extra_charge": sm.split_extra_charge,
            "categories": [
                {
                    "id": cat.id,
                    "name": cat.name,
                    "name_hebrew": cat.name_hebrew,
                    "display_order": cat.display_order,
                    "quota": cat.quota,
                }
                for cat in sm.categories
            ],
        }

    def create_sub_meal(self, data: dict) -> dict:
        # Verify template exists
        template_id = data.get("template_id")
        template = self.db.query(MenuTemplate).filter(MenuTemplate.id == template_id).first()
        if not template:
            raise AppException(404, "תבנית תפריט לא נמצאה")

        sm = MenuSubMeal(**data)
        self.db.add(sm)
        self.db.commit()
        self.db.refresh(sm)
        logger.info(f"תת-סעודה נוצרה: {sm.name} (ID={sm.id}) בתפריט {template.name}")
        return self._sub_meal_response(sm)

    def update_sub_meal(self, sub_meal_id: int, data: dict) -> dict:
        sm = self.db.query(MenuSubMeal).filter(MenuSubMeal.id == sub_meal_id).first()
        if not sm:
            raise AppException(404, "תת-סעודה לא נמצאה")
        for key, value in data.items():
            setattr(sm, key, value)
        self.db.commit()
        self.db.refresh(sm)
        logger.info(f"תת-סעודה עודכנה: {sm.name} (ID={sm.id})")
        return self._sub_meal_response(sm)

    def delete_sub_meal(self, sub_meal_id: int) -> dict:
        sm = self.db.query(MenuSubMeal).filter(MenuSubMeal.id == sub_meal_id).first()
        if not sm:
            raise AppException(404, "תת-סעודה לא נמצאה")
        self.db.delete(sm)  # Hard delete with cascade to categories
        self.db.commit()
        logger.info(f"תת-סעודה נמחקה: {sm.name} (ID={sub_meal_id})")
        return {"message": "תת-סעודה נמחקה בהצלחה"}

    # ── Category CRUD ─────────────────────────────────────────────────

    def create_category(self, data: dict) -> dict:
        cat = MenuCategory(**data)
        self.db.add(cat)
        self.db.commit()
        self.db.refresh(cat)
        logger.info(f"קטגוריה נוצרה: {cat.name_hebrew} (ID={cat.id})")
        return {
            "id": cat.id,
            "name": cat.name,
            "name_hebrew": cat.name_hebrew,
            "description": cat.description,
            "display_order": cat.display_order,
            "quota": cat.quota,
            "is_required": cat.is_required,
        }

    def update_category(self, category_id: int, data: dict) -> dict:
        cat = self.db.query(MenuCategory).filter(MenuCategory.id == category_id).first()
        if not cat:
            raise AppException(404, "קטגוריה לא נמצאה")
        for key, value in data.items():
            setattr(cat, key, value)
        self.db.commit()
        self.db.refresh(cat)
        logger.info(f"קטגוריה עודכנה: {cat.name_hebrew} (ID={cat.id})")
        return {
            "id": cat.id,
            "name": cat.name,
            "name_hebrew": cat.name_hebrew,
            "description": cat.description,
            "display_order": cat.display_order,
            "quota": cat.quota,
            "is_required": cat.is_required,
        }

    def delete_category(self, category_id: int) -> dict:
        cat = self.db.query(MenuCategory).filter(MenuCategory.id == category_id).first()
        if not cat:
            raise AppException(404, "קטגוריה לא נמצאה")
        self.db.delete(cat)
        self.db.commit()
        logger.info(f"קטגוריה נמחקה: {cat.name_hebrew} (ID={cat.id})")
        return {"message": "קטגוריה נמחקה בהצלחה"}

    # ── Dish Mapping CRUD ─────────────────────────────────────────────

    def add_dish_mapping(self, data: dict) -> dict:
        mapping = DishMenuMapping(**data)
        self.db.add(mapping)
        self.db.commit()
        self.db.refresh(mapping)
        dish = self.db.query(Dish).filter(Dish.id == mapping.dish_id).first()
        logger.info(f"מנה שויכה לקטגוריה: dish_id={mapping.dish_id}, category_id={mapping.category_id}")
        return {
            "id": mapping.id,
            "dish_id": mapping.dish_id,
            "category_id": mapping.category_id,
            "default_serving_mode": mapping.default_serving_mode,
            "is_upgrade": mapping.is_upgrade,
            "extra_charge": mapping.extra_charge,
            "display_order": mapping.display_order,
            "dish_name": dish.name if dish else None,
        }

    def update_dish_mapping(self, mapping_id: int, data: dict) -> dict:
        mapping = self.db.query(DishMenuMapping).filter(DishMenuMapping.id == mapping_id).first()
        if not mapping:
            raise AppException(404, "שיוך מנה לא נמצא")
        for key, value in data.items():
            setattr(mapping, key, value)
        self.db.commit()
        self.db.refresh(mapping)
        dish = self.db.query(Dish).filter(Dish.id == mapping.dish_id).first()
        return {
            "id": mapping.id,
            "dish_id": mapping.dish_id,
            "category_id": mapping.category_id,
            "default_serving_mode": mapping.default_serving_mode,
            "is_upgrade": mapping.is_upgrade,
            "extra_charge": mapping.extra_charge,
            "display_order": mapping.display_order,
            "dish_name": dish.name if dish else None,
        }

    def remove_dish_mapping(self, mapping_id: int) -> dict:
        mapping = self.db.query(DishMenuMapping).filter(DishMenuMapping.id == mapping_id).first()
        if not mapping:
            raise AppException(404, "שיוך מנה לא נמצא")
        mapping.is_deleted = True
        self.db.commit()
        logger.info(f"שיוך מנה נמחק: ID={mapping_id}")
        return {"message": "שיוך מנה נמחק בהצלחה"}
