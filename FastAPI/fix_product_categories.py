#!/usr/bin/env python3
"""
Script to update products with missing categories in the database.
Run this from the FastAPI directory: python fix_product_categories.py
"""

import sqlite3
from pathlib import Path

def fix_product_categories():
    """Update products that don't have a category"""

    db_path = Path("./data/planmyevents.db")

    if not db_path.exists():
        print(f"❌ Database file does not exist: {db_path.absolute()}")
        return False

    print(f"✅ Database file exists: {db_path.absolute()}")

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # First, ensure we have a default category
        cursor.execute("SELECT id FROM product_categories WHERE name = 'מוצרי מזון' LIMIT 1")
        default_category = cursor.fetchone()

        if not default_category:
            print("📝 Creating default category 'מוצרי מזון'...")
            cursor.execute("INSERT INTO product_categories (name) VALUES ('מוצרי מזון')")
            default_category_id = cursor.lastrowid
            print(f"✅ Created category with ID: {default_category_id}")
        else:
            default_category_id = default_category[0]
            print(f"✅ Default category exists with ID: {default_category_id}")

        # Find products with NULL category_id
        cursor.execute("SELECT id, name FROM products WHERE category_id IS NULL")
        products_without_category = cursor.fetchall()

        if not products_without_category:
            print("✅ All products already have categories!")
            return True

        print(f"📝 Found {len(products_without_category)} products without categories:")
        for product_id, name in products_without_category[:10]:  # Show first 10
            print(f"  - ID {product_id}: {name}")
        if len(products_without_category) > 10:
            print(f"  ... and {len(products_without_category) - 10} more")

        # Update all products without category to use the default
        cursor.execute("""
            UPDATE products
            SET category_id = ?
            WHERE category_id IS NULL
        """, (default_category_id,))

        updated_count = cursor.rowcount
        conn.commit()

        print(f"✅ Updated {updated_count} products with default category 'מוצרי מזון'")

        # Verify the fix
        cursor.execute("SELECT COUNT(*) FROM products WHERE category_id IS NULL")
        remaining_null = cursor.fetchone()[0]

        if remaining_null == 0:
            print("✅ All products now have categories!")
            return True
        else:
            print(f"❌ Still {remaining_null} products without categories")
            return False

    except Exception as e:
        print(f"❌ Error fixing product categories: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("🔧 Fixing Product Categories in PlanMyEvents Database")
    print("=" * 55)
    success = fix_product_categories()
    exit(0 if success else 1)