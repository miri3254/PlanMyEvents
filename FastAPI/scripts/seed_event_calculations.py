"""Idempotently prepare catalog data for event calculations.

Run after the Alembic migration. Existing dish ingredients are never changed.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.session import SessionLocal
from app.core.enums import ProductCategory, ToolCategory, ToolSubCategory, UnitType
from app.models.calculation import DishServingSet, DishServingSetItem
from app.models.dish import Dish
from app.models.product import Product
from app.models.tool import Tool


PRODUCTS = [
    ("פפסי", ProductCategory.LIQUIDS, UnitType.UNIT),
    ("פפסי מקס", ProductCategory.LIQUIDS, UnitType.UNIT),
    ("תפוזים", ProductCategory.LIQUIDS, UnitType.UNIT),
    ("מים בטעמים", ProductCategory.LIQUIDS, UnitType.UNIT),
    ("מים", ProductCategory.LIQUIDS, UnitType.UNIT),
    ("סודה", ProductCategory.LIQUIDS, UnitType.UNIT),
    ("לחמניות", ProductCategory.DRY, UnitType.UNIT),
    ("פקאן", ProductCategory.DRY, UnitType.GRAM),
    ("געלה", ProductCategory.DRY, UnitType.GRAM),
    ("חמוציות ושקדים", ProductCategory.DRY, UnitType.GRAM),
    ("שקדים מולבנים", ProductCategory.DRY, UnitType.GRAM),
    ("שקדים ושומשום", ProductCategory.DRY, UnitType.GRAM),
    ("מנצ'ס", ProductCategory.DRY, UnitType.GRAM),
    ("צנוברים", ProductCategory.DRY, UnitType.GRAM),
    ("תערובת שקדים חמוציות וסילאן", ProductCategory.DRY, UnitType.GRAM),
    ("נשנושים", ProductCategory.DRY, UnitType.UNIT),
]

TOOLS = [
    ("קופסת שאריות 1 ליטר", ToolCategory.SERVING, ToolSubCategory.DISPOSABLE),
    ("מפה מלבנית", ToolCategory.SERVING, ToolSubCategory.REAL),
    ("מפה עגולה", ToolCategory.SERVING, ToolSubCategory.REAL),
    ("מפה מרובעת", ToolCategory.SERVING, ToolSubCategory.REAL),
]


def run() -> None:
    db = SessionLocal()
    try:
        for name, category, unit in PRODUCTS:
            if not db.query(Product).filter(Product.name == name).first():
                db.add(Product(name=name, category=category, unit=unit, quantity_in_stock=0, min_stock_level=0))
        for name, category, sub_category in TOOLS:
            if not db.query(Tool).filter(Tool.name == name).first():
                db.add(Tool(name=name, category=category, sub_category=sub_category, quantity_in_stock=0))
        db.flush()

        for dish in db.query(Dish).all():
            if not dish.serving_dishes:
                continue
            exists = db.query(DishServingSet).filter(
                DishServingSet.dish_id == dish.id,
                DishServingSet.set_type == "serving",
            ).first()
            if exists:
                continue
            serving_set = DishServingSet(
                dish_id=dish.id,
                name="ברירת מחדל (המרה מכלים קיימים)",
                set_type="serving",
                is_default=True,
            )
            serving_set.items = [
                DishServingSetItem(
                    tool_id=row.tool_id,
                    name=row.name,
                    quantity=row.quantity,
                    quantity_basis="dish_unit",
                )
                for row in dish.serving_dishes
            ]
            db.add(serving_set)
        db.commit()
        print("Event calculation catalog prepared successfully")
    finally:
        db.close()


if __name__ == "__main__":
    run()
