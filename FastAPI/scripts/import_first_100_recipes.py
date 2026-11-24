"""ייבוא חוזר-בטוח של מאה המתכונים הראשונים מהחבילה המאושרת.

ברירת המחדל היא בדיקת-יובש. ``--apply`` יוצר גיבוי SQLite, מחיל את מיגרציית
התפוקה במידת הצורך, מוסיף מוצר חסר ומייבא מתכון ורכיביו בעסקה אחת. הייבוא
אינו משנה אירועים, תפריטים, מלאי או מחירים קיימים.
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

from sqlalchemy import text

BASE = Path(__file__).resolve().parents[1]
ROOT = BASE.parent
BUNDLE = ROOT / "מתכונים" / "recipe-json-2026-11-24"
LIMIT = 100
LATIN = re.compile(r"[A-Za-z]")
NORMALIZE = re.compile(r"[\s\-–—׳״'\"]+")

CATEGORY_MAP = {
    "ירקות ופטריות": "ירקות",
    "מוצרים מוכנים ובסיסי בצק": "בצק",
    "ירקות עלים ועשבי תיבול": "ירקות עלים ועשבי תיבול",
    "פירות": "פירות",
    "קטניות": "קטניות",
    "דגנים פסטה וקמחים": "פסטה וקמחים",
    "מוצרים יבשים אחרים": "מוצרים יבשים",
    "ביצים": "ביצים",
    "מוצרי בשר ועוף": "מוצרי בשר ועוף",
    "דגים": "דגים",
    "מוצרי חלב": "מוצרי חלב",
    "שמנים ושומנים": "שמנים ושומנים",
    "תבלינים ואבקות מרק": "תבלינים ואבקות מרק",
    "רטבים ממרחים וחומץ": "רטבים ממרחים",
    "שימורים וחמוצים": "שימורים",
    "אגוזים זרעים ופירות יבשים": "אגוזים זרעים ופירות יבשים",
    "אפייה קינוחים וממתיקים": "אפייה קינוחים וממתיקים",
    "נוזלים ומשקאות לבישול": "נוזלים",
}

# החלטות שכבר אושרו בשיחה; אף ערך לטיני אינו נכנס למסד הנתונים.
HEBREW_REPLACEMENTS = {
    "ביצים L": "ביצים גדולות",
    "ביצים M": "ביצים בינוניות",
    "או M": "או ביצים בינוניות",
    "תבנית r99": "תבנית מספר 99",
    "כלי 50z-92 kd-09": "כלי רוטב למגשי אירוח",
    "serving": "להגשה",
}


def hebrew(value: str | None) -> str | None:
    if value is None:
        return None
    for original, replacement in HEBREW_REPLACEMENTS.items():
        value = value.replace(original, replacement)
    if LATIN.search(value):
        raise ValueError(f"נמצא טקסט לטיני שאינו מורשה: {value}")
    return value


def normalized(value: str) -> str:
    return NORMALIZE.sub("", value).lower()


def source_description(recipe: dict) -> str:
    source_number = recipe["source_id"].rsplit("_", 1)[-1]
    paragraphs = "–".join(map(str, recipe["source_paragraphs"]))
    return f"מקור: מתכונים {source_number}, פסקאות {paragraphs}."


def combined_notes(recipe: dict) -> str | None:
    notes = [recipe.get("notes"), (recipe.get("yield") or {}).get("notes")]
    cleaned = [hebrew(note.strip()) for note in notes if note and note.strip()]
    return " ".join(dict.fromkeys(cleaned)) or None


def ingredient_note(ingredient: dict) -> str | None:
    """מתרגם דגלי חילוץ פנימיים להערה תמציתית בעברית."""
    condition = ingredient.get("condition")
    if not condition:
        return None
    if condition.startswith("alternative:"):
        return "חלופה"
    if condition.startswith("conflict:") or condition == "yield_conflict":
        return "סתירה במקור"
    if condition.startswith("equivalent"):
        return "מידה חלופית במקור"
    if condition.startswith("range:"):
        return "טווח במקור"
    notes = {
        "ambiguous_source": "נדרש בירור מול המקור",
        "fill_level": "מידה לא מדויקת במקור",
        "filling_review": "נדרש בירור למילוי",
        "frying": "לטיגון",
        "inferred_black_pepper": "סוג הפלפל הוסק מן המקור",
        "mentioned_without_quantity": "כמות לא צוינה",
        "mixture_detail": "רכיב תערובת",
        "mixture_parent": "תערובת",
        "optional": "אופציונלי",
        "optional_decoration": "לקישוט אופציונלי",
        "per_50_people": "לכל חמישים אנשים",
        "per_50_people_review": "לכל חמישים אנשים – נדרש בירור",
        "ratio_only": "יחס בלבד",
        "repeated_alternative": "חלופה חוזרת",
        "serving": "להגשה",
        "serving_batch_scope_unresolved": "היקף ההגשה אינו ברור",
    }
    return notes.get(condition, "נדרש בירור מול המקור")


def backup_database(engine) -> Path:
    source = Path(engine.url.database).resolve()
    folder = source.parent / "backups"
    folder.mkdir(exist_ok=True)
    backup = folder / f"before_first_100_recipes_{datetime.now():%Y%m%d_%H%M%S_%f}.db"
    raw = engine.raw_connection()
    try:
        with sqlite3.connect(backup) as target:
            raw.driver_connection.backup(target)
    finally:
        raw.close()
    return backup


def apply_yield_migration(engine) -> None:
    from alembic import command
    from alembic.config import Config

    with engine.connect() as connection:
        revision = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
    if revision == "r1a2b3c4d5e6":
        return
    if revision != "q0f1a2b3c4d5":
        raise RuntimeError(f"גרסת מסד לא צפויה: {revision}")
    config = Config(str(BASE / "alembic.ini"))
    config.set_main_option("script_location", str(BASE / "alembic"))
    config.set_main_option("sqlalchemy.url", engine.url.render_as_string(hide_password=False).replace("%", "%%"))
    command.upgrade(config, "r1a2b3c4d5e6")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="מבצע ייבוא אחרי גיבוי")
    args = parser.parse_args()
    sys.path.insert(0, str(BASE))

    from app.core.enums import KosherType, ProductCategory, UnitType
    from app.db.engine import engine
    from app.db.session import SessionLocal
    from app.models.dish import Dish, DishIngredient
    from app.models.product import Product

    if engine.dialect.name != "sqlite":
        raise RuntimeError("הייבוא מיועד למסד SQLite מקומי בלבד")
    database = Path(engine.url.database).resolve()
    if not database.is_relative_to(BASE) or not database.is_file():
        raise RuntimeError("מסד הנתונים חייב להיות קובץ קיים בתוך FastAPI")

    recipes = json.loads((BUNDLE / "dishes.json").read_text(encoding="utf-8"))["dishes"][:LIMIT]
    products = {row["product_key"]: row for row in json.loads((BUNDLE / "products.json").read_text(encoding="utf-8"))["products"]}
    required_keys = {ingredient["product_key"] for recipe in recipes for ingredient in recipe["ingredients"]}
    if len(recipes) != LIMIT or not required_keys.issubset(products):
        raise RuntimeError("חבילת החילוץ אינה שלמה")

    for recipe in recipes:
        hebrew(recipe["name"])
        combined_notes(recipe)
        output = recipe.get("yield") or {}
        hebrew(output.get("unit"))
        for ingredient in recipe["ingredients"]:
            hebrew(ingredient["name"])
            ingredient_note(ingredient)

    db = SessionLocal()
    try:
        existing = {normalized(product.name): product for product in db.query(Product).filter(Product.is_deleted.is_(False)).all()}
        new_product_count = sum(normalized(hebrew(products[key]["db_fields"]["name"])) not in existing for key in required_keys)
        existing_recipes = set(db.execute(
            text("SELECT name, description FROM dishes WHERE is_deleted = 0")
        ).all())
        new_recipe_count = sum((hebrew(recipe["name"]), source_description(recipe)) not in existing_recipes for recipe in recipes)
        if not args.apply:
            print(f"מוכן לייבוא: {new_recipe_count} מנות ו-{new_product_count} מוצרים חדשים; הפעלה: --apply")
            return

        backup = backup_database(engine)
        apply_yield_migration(engine)
        # Alembic closes/rebuilds SQLite tables; session data must be refreshed.
        db.close()
        db = SessionLocal()
        existing = {normalized(product.name): product for product in db.query(Product).filter(Product.is_deleted.is_(False)).all()}
        linked_products: dict[str, Product] = {}
        added_products = 0
        for key in sorted(required_keys):
            source = products[key]
            fields = source["db_fields"]
            name = hebrew(fields["name"])
            product = existing.get(normalized(name))
            if product is None:
                category = CATEGORY_MAP[source["recommended_category"]]
                kosher = KosherType.DAIRY if category == "מוצרי חלב" else KosherType.MEAT if category == "מוצרי בשר ועוף" else KosherType.PARVE
                product = Product(
                    name=name,
                    category=ProductCategory(category),
                    unit=UnitType(fields["unit"]),
                    kosher_type=kosher,
                    notes=f"נוסף מחבילת מתכונים מאושרת; קטגוריה: {category}.",
                )
                db.add(product)
                db.flush()
                existing[normalized(name)] = product
                added_products += 1
            linked_products[key] = product

        added_recipes = 0
        linked_ingredients = 0
        for recipe in recipes:
            name = hebrew(recipe["name"])
            description = source_description(recipe)
            dish = db.query(Dish).filter(Dish.name == name, Dish.description == description).one_or_none()
            if dish is not None:
                continue
            output = recipe.get("yield") or {}
            dish = Dish(
                name=name,
                description=description,
                serving_size=recipe.get("serving_size"),
                yield_quantity=output.get("quantity"),
                yield_unit=hebrew(output.get("unit")),
                serving_description=hebrew(recipe["db_fields"].get("serving_description")),
                notes=combined_notes(recipe),
                is_active=False,
            )
            db.add(dish)
            db.flush()
            for ingredient in recipe["ingredients"]:
                db.add(DishIngredient(
                    dish_id=dish.id,
                    product_id=linked_products[ingredient["product_key"]].id,
                    quantity=ingredient.get("quantity"),
                    unit=UnitType(ingredient["api_unit_candidate"]) if ingredient.get("api_unit_candidate") else None,
                    name=None,
                    note=ingredient_note(ingredient),
                    is_serving_component=ingredient.get("is_serving_component", False),
                ))
                linked_ingredients += 1
            added_recipes += 1
        db.commit()
        with engine.connect() as connection:
            assert connection.execute(text("PRAGMA quick_check")).scalar_one() == "ok"
        print(f"הייבוא הושלם: {added_recipes} מנות, {added_products} מוצרים, {linked_ingredients} קישורי רכיבים. גיבוי: {backup}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
