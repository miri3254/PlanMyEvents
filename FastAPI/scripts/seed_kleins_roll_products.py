"""Seed Kleins roll products into the local product catalog."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.enums import KosherType, ProductCategory, UnitType
from app.db.session import SessionLocal
from app.models.product import Product


KLEINS_ROLL_PRODUCTS = [
    {"name": "לחמניה קשר", "price_per_unit": 1.8},
    {"name": "לחמנית בצל / שום אצבע", "price_per_unit": 2.7},
    {"name": "לחמניה ביס מיני - 120 גרם", "price_per_unit": 2.4},
    {"name": "לחמניה מיני מיקסים - פרג שומשום מלא, בייגל קטן", "price_per_unit": 1.8},
    {"name": "לחמנית בורגר קטן - 80 גרם", "price_per_unit": 1.8},
    {"name": "לחמנית בורגר קטן - 30-40 גרם", "price_per_unit": 2.4, "package_quantity": 100},
    {"name": "לחמניה קמח מלא", "price_per_unit": 2.4},
    {"name": "לחמניה מיני שום / מתובל - קטן", "price_per_unit": 2.4},
]


def seed() -> tuple[int, int]:
    db = SessionLocal()
    created = 0
    updated = 0
    try:
        for item in KLEINS_ROLL_PRODUCTS:
            product = (
                db.query(Product)
                .filter(Product.name == item["name"])
                .filter(Product.is_deleted == False)  # noqa: E712
                .first()
            )
            if not product:
                product = Product(
                    name=item["name"],
                    category=ProductCategory.DRY,
                    unit=UnitType.UNIT,
                    kosher_type=KosherType.PARVE,
                    quantity_in_stock=0,
                    min_stock_level=20,
                )
                db.add(product)
                created += 1
            else:
                updated += 1

            product.price_per_unit = item["price_per_unit"]
            product.estimated_price = item["price_per_unit"]
            product.package_quantity = item.get("package_quantity")
            product.supplier = "קליינס"
            product.notes = "מחירון קליינס - לחמניות לאירועים"

        db.commit()
        return created, updated
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    created_count, updated_count = seed()
    print(f"Seeded Kleins roll products: created={created_count}, updated={updated_count}")
