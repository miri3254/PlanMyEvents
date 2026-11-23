"""
בניית עץ תפריטים מלא - 6 MenuTypes עם כל הקטגוריות
מסיר את כל הנתונים הקיימים ובונה מחדש את מבנה התפריטים המלא
"""
import sys
import os
from pathlib import Path

# הוספת הנתיב של app לפייתון
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.models.menu_template import MenuType, MenuTemplate, MenuCategory
from app.models.dish import Dish, DishIngredient, DishEquipment, ServingDish, DishMenuMapping
# from app.models.product import Product


def delete_all_data(db: Session):
    """
    שלב 2: ניקוי נתונים - מחיקה לצמיתות של כל הנתונים
    """
    print("\n=== שלב 2: ניקוי נתונים ===")
    
    tables_to_clean = [
        ("DishMenuMapping", DishMenuMapping),
        ("ServingDish", ServingDish),
        ("DishEquipment", DishEquipment),
        ("DishIngredient", DishIngredient),
        ("Dish", Dish),
        ("MenuCategory", MenuCategory),
        ("MenuTemplate", MenuTemplate),
    ]
    
    for table_name, model in tables_to_clean:
        try:
            deleted = db.query(model).delete()
            db.commit()
            print(f"✓ נמחקו {deleted} רשומות מטבלת {table_name}")
        except Exception as e:
            print(f"✗ שגיאה במחיקת {table_name}: {str(e)}")
            db.rollback()
    
    print("\n✓ כל הנתונים נמחקו בהצלחה!")


def create_menu_tree(db: Session):
    """
    שלב 3: בניית עץ התפריטים המלא (6 MenuTypes)
    """
    print("\n=== שלב 3: בניית עץ התפריטים המלא ===")
    
    # תפריט 1: שבת
    print("\n1️⃣ יוצר תפריט: שבת")
    shabbat_template = MenuTemplate(
        menu_type=MenuType.SHABBAT,
        name_hebrew="שבת",
        description="תפריט שבת מסורתי - ליל שבת ושבת בוקר"
    )
    db.add(shabbat_template)
    db.flush()
    
    shabbat_categories = [
        {"name": "friday_salads", "name_hebrew": "ליל שבת-סלטים", "quota": 5, "display_order": 1},
        {"name": "friday_first", "name_hebrew": "ליל שבת-מנה ראשונה", "quota": 1, "display_order": 2},
        {"name": "friday_main", "name_hebrew": "ליל שבת-עיקרית", "quota": 1, "display_order": 3},
        {"name": "friday_sides", "name_hebrew": "ליל שבת-תוספות", "quota": 3, "display_order": 4},
        {"name": "saturday_salads", "name_hebrew": "שבת בוקר-סלטים", "quota": 5, "display_order": 5},
        {"name": "saturday_main", "name_hebrew": "שבת בוקר-עיקרית", "quota": 1, "display_order": 6},
    ]
    
    for cat_data in shabbat_categories:
        category = MenuCategory(
            template_id=shabbat_template.id,
            **cat_data
        )
        db.add(category)
    
    print(f"   ✓ נוצרו {len(shabbat_categories)} קטגוריות")
    
    # תפריט 2: שולחן מתוק
    print("\n2️⃣ יוצר תפריט: שולחן מתוק")
    sweet_template = MenuTemplate(
        menu_type=MenuType.SWEET_TABLE,
        name_hebrew="שולחן מתוק",
        description="שולחן מתוק לאירועים"
    )
    db.add(sweet_template)
    db.flush()
    
    sweet_categories = [
        {"name": "salads", "name_hebrew": "סלטים", "quota": 3, "display_order": 1},
        {"name": "pastries", "name_hebrew": "מאפים", "quota": 4, "display_order": 2},
        {"name": "sides", "name_hebrew": "תוספות", "quota": 2, "display_order": 3},
    ]
    
    for cat_data in sweet_categories:
        category = MenuCategory(
            template_id=sweet_template.id,
            **cat_data
        )
        db.add(category)
    
    print(f"   ✓ נוצרו {len(sweet_categories)} קטגוריות")
    
    # תפריט 3: מגשי אירוח חלבי
    print("\n3️⃣ יוצר תפריט: מגשי אירוח חלבי")
    dairy_trays_template = MenuTemplate(
        menu_type=MenuType.DAIRY_TRAYS,
        name_hebrew="מגשי אירוח חלבי",
        description="מגשי אירוח חלבי לאירועים"
    )
    db.add(dairy_trays_template)
    db.flush()
    
    dairy_trays_categories = [
        {"name": "sandwiches", "name_hebrew": "כריכים", "quota": 3, "display_order": 1},
        {"name": "pastries", "name_hebrew": "מאפים וטורטיות", "quota": 3, "display_order": 2},
        {"name": "sides", "name_hebrew": "תוספות ומוקרמים", "quota": 3, "display_order": 3},
        {"name": "salads", "name_hebrew": "סלטים", "quota": 4, "display_order": 4},
        {"name": "spreads", "name_hebrew": "ממרחים", "quota": 2, "display_order": 5},
        {"name": "cheeses", "name_hebrew": "גבינות", "quota": 3, "display_order": 6},
        {"name": "desserts", "name_hebrew": "קינוחים", "quota": 2, "display_order": 7},
    ]
    
    for cat_data in dairy_trays_categories:
        category = MenuCategory(
            template_id=dairy_trays_template.id,
            **cat_data
        )
        db.add(category)
    
    print(f"   ✓ נוצרו {len(dairy_trays_categories)} קטגוריות")
    
    # תפריט 4: מגשי אירוח בשרי
    print("\n4️⃣ יוצר תפריט: מגשי אירוח בשרי")
    meat_trays_template = MenuTemplate(
        menu_type=MenuType.MEAT_TRAYS,
        name_hebrew="מגשי אירוח בשרי",
        description="מגשי אירוח בשרי לאירועים"
    )
    db.add(meat_trays_template)
    db.flush()
    
    meat_trays_categories = [
        {"name": "sandwiches", "name_hebrew": "כריכים", "quota": 3, "display_order": 1},
        {"name": "salads", "name_hebrew": "סלטים", "quota": 4, "display_order": 2},
        {"name": "sides", "name_hebrew": "תוספות", "quota": 3, "display_order": 3},
        {"name": "meats", "name_hebrew": "בשרים ועופות", "quota": 3, "display_order": 4},
        {"name": "fish", "name_hebrew": "דגים", "quota": 2, "display_order": 5},
        {"name": "desserts", "name_hebrew": "קינוחים", "quota": 2, "display_order": 6},
    ]
    
    for cat_data in meat_trays_categories:
        category = MenuCategory(
            template_id=meat_trays_template.id,
            **cat_data
        )
        db.add(category)
    
    print(f"   ✓ נוצרו {len(meat_trays_categories)} קטגוריות")
    
    # תפריט 5: בשרי (אירועים)
    print("\n5️⃣ יוצר תפריט: בשרי (אירועים)")
    meat_menu_template = MenuTemplate(
        menu_type=MenuType.MEAT_MENU,
        name_hebrew="בשרי (אירועים)",
        description="תפריט בשרי מלא לאירועים"
    )
    db.add(meat_menu_template)
    db.flush()
    
    meat_menu_categories = [
        {"name": "salads", "name_hebrew": "סלטים", "quota": 5, "display_order": 1},
        {"name": "first_course", "name_hebrew": "מנה ראשונה", "quota": 1, "display_order": 2},
        {"name": "main_course", "name_hebrew": "עיקרית", "quota": 1, "display_order": 3},
        {"name": "sides", "name_hebrew": "תוספות", "quota": 3, "display_order": 4},
        {"name": "desserts", "name_hebrew": "קינוחים", "quota": 1, "display_order": 5},
    ]
    
    for cat_data in meat_menu_categories:
        category = MenuCategory(
            template_id=meat_menu_template.id,
            **cat_data
        )
        db.add(category)
    
    print(f"   ✓ נוצרו {len(meat_menu_categories)} קטגוריות")
    
    # תפריט 6: חלבי (אירועים)
    print("\n6️⃣ יוצר תפריט: חלבי (אירועים)")
    dairy_menu_template = MenuTemplate(
        menu_type=MenuType.DAIRY_MENU,
        name_hebrew="חלבי (אירועים)",
        description="תפריט חלבי מלא לאירועים"
    )
    db.add(dairy_menu_template)
    db.flush()
    
    dairy_menu_categories = [
        {"name": "salads", "name_hebrew": "סלטים", "quota": 5, "display_order": 1},
        {"name": "soups", "name_hebrew": "מרקים", "quota": 1, "display_order": 2},
        {"name": "fish", "name_hebrew": "עיקרית-דגים", "quota": 1, "display_order": 3},
        {"name": "casseroles", "name_hebrew": "מוקרמים ומאפים", "quota": 2, "display_order": 4},
        {"name": "vegetables", "name_hebrew": "ירקות", "quota": 2, "display_order": 5},
        {"name": "desserts", "name_hebrew": "קינוחים", "quota": 1, "display_order": 6},
    ]
    
    for cat_data in dairy_menu_categories:
        category = MenuCategory(
            template_id=dairy_menu_template.id,
            **cat_data
        )
        db.add(category)
    
    print(f"   ✓ נוצרו {len(dairy_menu_categories)} קטגוריות")
    
    db.commit()
    print("\n✓ כל התפריטים נוצרו בהצלחה!")


def verify_menu_tree(db: Session):
    """
    אימות שהעץ נבנה בהצלחה
    """
    print("\n=== אימות מבנה התפריטים ===")
    
    templates = db.query(MenuTemplate).all()
    print(f"\n📋 סך הכל נוצרו {len(templates)} תפריטים:")
    
    total_categories = 0
    for template in templates:
        categories_count = len(template.categories)
        total_categories += categories_count
        print(f"\n{template.name_hebrew} ({template.menu_type.value}):")
        print(f"   מספר קטגוריות: {categories_count}")
        for cat in template.categories:
            print(f"   {cat.display_order}. {cat.name_hebrew} (מכסה: {cat.quota})")
    
    print(f"\n✓ סך הכל {total_categories} קטגוריות נוצרו בהצלחה!")
    print("\n=== המערכת מוכנה לשימוש! ===")


def main():
    """
    תהליך מלא: ניקוי ובניית עץ תפריטים
    """
    print("=" * 60)
    print("בניית עץ תפריטים מלא - 6 MenuTypes")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        # שלב 2: ניקוי נתונים
        delete_all_data(db)
        
        # שלב 3: בניית עץ התפריטים
        create_menu_tree(db)
        
        # אימות
        verify_menu_tree(db)
        
        print("\n✅ התהליך הושלם בהצלחה!")
        
    except Exception as e:
        print(f"\n❌ שגיאה: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
