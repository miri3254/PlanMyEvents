"""Safely calculate missing dish costs from linked product prices.

The stored ``Dish.base_price`` is a cost per guest. A dish is priced only
when every linked recipe ingredient has a quantity, product, price and an
explicit conversion path to the product's stock unit. The recipe total is
then divided by its serving size. Existing manual dish prices are protected
unless ``--overwrite`` is supplied.

Run without arguments for a read-only preview. ``--apply`` first creates a
SQLite backup, seeds the editable kitchen-measurement defaults, and persists
only prices that can be calculated completely.
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path


BASE = Path(__file__).resolve().parents[1]
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))


def backup_database(engine) -> Path:
    """Create a recoverable copy before changing the local SQLite database."""
    source = Path(engine.url.database).resolve()
    backups = source.parent / "backups"
    backups.mkdir(exist_ok=True)
    backup = backups / f"before_calculating_dish_prices_{datetime.now():%Y%m%d_%H%M%S_%f}.db"
    raw_connection = engine.raw_connection()
    try:
        with sqlite3.connect(backup) as target:
            raw_connection.driver_connection.backup(target)
    finally:
        raw_connection.close()
    return backup


def product_unit_price(product) -> float | None:
    """Return the price for one of the product's stored units."""
    if product.price_per_unit is not None:
        return float(product.price_per_unit)
    if product.estimated_price is None:
        return None
    package_quantity = float(product.package_quantity or 1)
    if package_quantity <= 0:
        return None
    return float(product.estimated_price) / package_quantity


def calculate_dish_price(dish, conversion_service) -> tuple[float | None, str | None]:
    """Calculate one full recipe cost per guest, otherwise give one reason."""
    if not dish.ingredients:
        return None, "ללא רכיבים"
    if dish.serving_size is None or dish.serving_size <= 0:
        return None, "תפוקה לסועדים חסרה"

    total_recipe_cost = 0.0
    for ingredient in dish.ingredients:
        if ingredient.quantity is None or ingredient.unit is None:
            return None, "כמות או יחידה חסרה"
        if ingredient.product is None:
            return None, "מוצר מקושר חסר"
        unit_price = product_unit_price(ingredient.product)
        if unit_price is None:
            return None, "מחיר מוצר חסר"
        try:
            converted_quantity, _ = conversion_service.convert(
                float(ingredient.quantity), ingredient.unit, ingredient.product.unit
            )
        except Exception:
            return None, "המרת יחידות חסרה"
        total_recipe_cost += unit_price * converted_quantity

    return round(total_recipe_cost / float(dish.serving_size), 2), None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="שומר מחירים חדשים לאחר גיבוי")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="מחשב מחדש גם מחיר עלות קיים (ברירת המחדל שומרת על מחיר ידני)",
    )
    args = parser.parse_args()

    from app.core.enums import AuditAction
    from app.db.engine import engine
    from app.db.session import SessionLocal
    from app.models.audit import AuditLog
    from app.models.dish import Dish
    from app.services.unit_conversion_service import UnitConversionService

    if engine.dialect.name != "sqlite":
        raise RuntimeError("הסקריפט מיועד למסד SQLite המקומי בלבד")
    database = Path(engine.url.database).resolve()
    if not database.is_relative_to(BASE) or not database.is_file():
        raise RuntimeError("מסד הנתונים חייב להיות קובץ קיים תחת FastAPI")

    db = SessionLocal()
    try:
        backup = None
        conversion_service = UnitConversionService(db)
        if args.apply:
            backup = backup_database(engine)
            added_conversions = conversion_service.seed_system_conversions()
        else:
            added_conversions = 0

        dishes = (
            db.query(Dish)
            .filter(Dish.is_deleted.is_(False))
            .order_by(Dish.id)
            .all()
        )
        calculated: list[tuple[Dish, float]] = []
        skipped = Counter()
        for dish in dishes:
            if dish.base_price is not None and not args.overwrite:
                skipped["מחיר קיים נשמר"] += 1
                continue
            price, reason = calculate_dish_price(dish, conversion_service)
            if price is None:
                skipped[reason or "לא חושב"] += 1
                continue
            calculated.append((dish, price))

        if not args.apply:
            print(f"תצוגה בלבד: ניתן לחשב {len(calculated)} מחירי עלות מתוך {len(dishes)} מנות.")
            if skipped:
                print("לא חושבו: " + ", ".join(f"{reason} ({count})" for reason, count in sorted(skipped.items())))
            print("להחלה לאחר גיבוי: python scripts/recalc_dish_prices.py --apply")
            return

        for dish, price in calculated:
            previous_price = dish.base_price
            dish.base_price = price
            db.add(AuditLog(
                entity_type="dish",
                entity_id=dish.id,
                action=AuditAction.UPDATED.value,
                details={"source": "recipe_cost_calculation", "previous_base_price": previous_price, "base_price": price},
            ))
        db.commit()
        with engine.connect() as connection:
            integrity = connection.exec_driver_sql("PRAGMA quick_check").scalar_one()
        if integrity != "ok":
            raise RuntimeError(f"בדיקת שלמות המסד נכשלה: {integrity}")

        print(
            f"עודכנו {len(calculated)} מחירי עלות; נוספו {added_conversions} המרות ניתנות לעריכה. "
            f"גיבוי: {backup}"
        )
        if skipped:
            print("לא חושבו: " + ", ".join(f"{reason} ({count})" for reason, count in sorted(skipped.items())))
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
