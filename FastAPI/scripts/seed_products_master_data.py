"""
הזנת נתונים מלאה למוצרים (Master Data Products)
כולל קטגוריות, יחידות מידה, כשרות והגדרות מלאי
"""
import sys
import os
from pathlib import Path

# הוספת הנתיב של app לפייתון
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.product import Product, ProductCategory, UnitType, KosherType


def create_categories(db: Session):
    """
    שלב 1: יצירת קטגוריות מוצרים
    """
    print("\n=== שלב 1: יצירת קטגוריות מוצרים ===")
    
    categories = [
        "ירקות",
        "פירות",
        "בשר ועוף",
        "דגים",
        "מוצרי חלב",
        "מזווה ויבשים",
        "רטבים ותבלינים",
        "מאפה"
    ]
    
    category_map = {}
    for cat_name in categories:
        existing = db.query(ProductCategory).filter(ProductCategory.name == cat_name).first()
        if existing:
            category_map[cat_name] = existing.id
            print(f"   ✓ קטגוריה קיימת: {cat_name}")
        else:
            new_cat = ProductCategory(name=cat_name)
            db.add(new_cat)
            db.flush()
            category_map[cat_name] = new_cat.id
            print(f"   + נוצרה קטגוריה: {cat_name}")
    
    db.commit()
    print(f"\n✓ סך הכל {len(categories)} קטגוריות הוכנו")
    return category_map


def get_min_stock_level(unit: UnitType) -> float:
    """
    חישוב min_stock_level לפי הכלל:
    - ק"ג/ליטר = 2
    - גרם = 500
    - יחידה = 5
    """
    if unit in [UnitType.KG, UnitType.LITER]:
        return 2.0
    elif unit == UnitType.GRAM:
        return 500.0
    elif unit == UnitType.UNIT:
        return 5.0
    else:
        return 5.0  # ברירת מחדל


def seed_products(db: Session, category_map: dict):
    """
    שלב 2: הזנת כל המוצרים עם פרטים מלאים
    """
    print("\n=== שלב 2: הזנת מוצרים ===")
    
    # רשימת מוצרים לפי קטגוריות
    products_data = [
        # ירקות
        ("גזר", "ירקות", UnitType.KG, KosherType.PARVE),
        ("סלרי", "ירקות", UnitType.KG, KosherType.PARVE),
        ("פלפל בצבעים", "ירקות", UnitType.KG, KosherType.PARVE),
        ("תירס גמדי", "ירקות", UnitType.KG, KosherType.PARVE),
        ("נבטים", "ירקות", UnitType.KG, KosherType.PARVE),
        ("שום", "ירקות", UnitType.KG, KosherType.PARVE),
        ("בצל ירוק", "ירקות", UnitType.KG, KosherType.PARVE),
        ("חסה", "ירקות", UnitType.KG, KosherType.PARVE),
        ("פטריות שמפיניון", "ירקות", UnitType.KG, KosherType.PARVE),
        ("עגבניות שרי", "ירקות", UnitType.KG, KosherType.PARVE),
        ("בצל סגול", "ירקות", UnitType.KG, KosherType.PARVE),
        ("כרוב לבן", "ירקות", UnitType.KG, KosherType.PARVE),
        ("כרוב סגול", "ירקות", UnitType.KG, KosherType.PARVE),
        ("סלק", "ירקות", UnitType.KG, KosherType.PARVE),
        ("חציל", "ירקות", UnitType.KG, KosherType.PARVE),
        ("גמבה", "ירקות", UnitType.KG, KosherType.PARVE),
        ("עגבניה", "ירקות", UnitType.KG, KosherType.PARVE),
        ("בטטה", "ירקות", UnitType.KG, KosherType.PARVE),
        ("מלפפון", "ירקות", UnitType.KG, KosherType.PARVE),
        ("פלפל חריף", "ירקות", UnitType.KG, KosherType.PARVE),
        ("קישוא", "ירקות", UnitType.KG, KosherType.PARVE),
        ("בצל", "ירקות", UnitType.KG, KosherType.PARVE),
        ("שעועית ירוקה", "ירקות", UnitType.KG, KosherType.PARVE),
        ("דלעת", "ירקות", UnitType.KG, KosherType.PARVE),
        ("פטרוזיליה", "ירקות", UnitType.KG, KosherType.PARVE),
        ("שמיר", "ירקות", UnitType.KG, KosherType.PARVE),
        ("עלים ירוקים", "ירקות", UnitType.KG, KosherType.PARVE),
        ("תירס", "ירקות", UnitType.KG, KosherType.PARVE),
        ("אפונה", "ירקות", UnitType.KG, KosherType.PARVE),
        
        # פירות
        ("תפוח", "פירות", UnitType.KG, KosherType.PARVE),
        ("אננס", "פירות", UnitType.KG, KosherType.PARVE),
        ("חמוציות", "פירות", UnitType.KG, KosherType.PARVE),
        ("אוכמניות", "פירות", UnitType.KG, KosherType.PARVE),
        ("תות", "פירות", UnitType.KG, KosherType.PARVE),
        ("פירות העונה", "פירות", UnitType.KG, KosherType.PARVE),
        ("צימוקים", "פירות", UnitType.KG, KosherType.PARVE),
        
        # חלבונים - בשר ועוף
        ("בקר", "בשר ועוף", UnitType.KG, KosherType.MEAT),
        ("הודו", "בשר ועוף", UnitType.KG, KosherType.MEAT),
        ("פרגית", "בשר ועוף", UnitType.KG, KosherType.MEAT),
        ("כרעיים עוף", "בשר ועוף", UnitType.KG, KosherType.MEAT),
        ("חזה עוף", "בשר ועוף", UnitType.KG, KosherType.MEAT),
        ("כבד עוף", "בשר ועוף", UnitType.KG, KosherType.MEAT),
        ("המבורגר", "בשר ועוף", UnitType.KG, KosherType.MEAT),
        ("קבב", "בשר ועוף", UnitType.KG, KosherType.MEAT),
        ("נקניקיות", "בשר ועוף", UnitType.KG, KosherType.MEAT),
        ("אסאדו", "בשר ועוף", UnitType.KG, KosherType.MEAT),
        
        # דגים
        ("סלמון", "דגים", UnitType.KG, KosherType.PARVE),
        ("מושט", "דגים", UnitType.KG, KosherType.PARVE),
        ("טונה", "דגים", UnitType.KG, KosherType.PARVE),
        ("הרינג", "דגים", UnitType.KG, KosherType.PARVE),
        ("ביצי דגים", "דגים", UnitType.KG, KosherType.PARVE),
        
        # מוצרי חלב
        ("גבינה צהובה", "מוצרי חלב", UnitType.UNIT, KosherType.DAIRY),
        ("גבינת פטה", "מוצרי חלב", UnitType.UNIT, KosherType.DAIRY),
        ("גבינה בולגרית", "מוצרי חלב", UnitType.UNIT, KosherType.DAIRY),
        ("גבינת חלומי", "מוצרי חלב", UnitType.UNIT, KosherType.DAIRY),
        ("גבינה לבנה", "מוצרי חלב", UnitType.UNIT, KosherType.DAIRY),
        ("קוטג'", "מוצרי חלב", UnitType.UNIT, KosherType.DAIRY),
        ("יוגורט", "מוצרי חלב", UnitType.UNIT, KosherType.DAIRY),
        ("שמנת מתוקה", "מוצרי חלב", UnitType.LITER, KosherType.DAIRY),  # חריג - ליטר
        
        # מזווה ויבשים - בסיס ק"ג
        ("אורז", "מזווה ויבשים", UnitType.KG, KosherType.PARVE),
        ("בורגול", "מזווה ויבשים", UnitType.KG, KosherType.PARVE),
        ("קינואה", "מזווה ויבשים", UnitType.KG, KosherType.PARVE),
        ("פסטה", "מזווה ויבשים", UnitType.KG, KosherType.PARVE),
        ("אטריות", "מזווה ויבשים", UnitType.KG, KosherType.PARVE),
        ("קוסקוס", "מזווה ויבשים", UnitType.KG, KosherType.PARVE),
        ("גריסים", "מזווה ויבשים", UnitType.KG, KosherType.PARVE),
        ("שעועית יבשה", "מזווה ויבשים", UnitType.KG, KosherType.PARVE),
        ("גרגירי חומוס", "מזווה ויבשים", UnitType.KG, KosherType.PARVE),
        ("אגוזי מלך", "מזווה ויבשים", UnitType.KG, KosherType.PARVE),
        ("פקאן", "מזווה ויבשים", UnitType.KG, KosherType.PARVE),
        ("שקדים", "מזווה ויבשים", UnitType.KG, KosherType.PARVE),
        ("שומשום", "מזווה ויבשים", UnitType.KG, KosherType.PARVE),
        ("גרעיני חמניה", "מזווה ויבשים", UnitType.KG, KosherType.PARVE),
        ("פיצוחים", "מזווה ויבשים", UnitType.KG, KosherType.PARVE),
        ("קרוטונים", "מזווה ויבשים", UnitType.KG, KosherType.PARVE),
        ("גרנולה", "מזווה ויבשים", UnitType.KG, KosherType.PARVE),
        ("פירורי לחם", "מזווה ויבשים", UnitType.KG, KosherType.PARVE),
        ("קמח", "מזווה ויבשים", UnitType.KG, KosherType.PARVE),
        ("סוכר", "מזווה ויבשים", UnitType.KG, KosherType.PARVE),
        ("דפי לזניה", "מזווה ויבשים", UnitType.KG, KosherType.PARVE),
        ("עלים לסיגר", "מזווה ויבשים", UnitType.KG, KosherType.PARVE),
        ("בצק פילו", "מזווה ויבשים", UnitType.KG, KosherType.PARVE),
        ("בורקס", "מזווה ויבשים", UnitType.KG, KosherType.PARVE),
        ("פחזניות", "מזווה ויבשים", UnitType.KG, KosherType.PARVE),
        ("חלווה", "מזווה ויבשים", UnitType.KG, KosherType.PARVE),
        
        # מזווה - חריגים בגרם
        ("שוקולד", "מזווה ויבשים", UnitType.GRAM, KosherType.PARVE),
        ("קקאו", "מזווה ויבשים", UnitType.GRAM, KosherType.PARVE),
        ("קפה", "מזווה ויבשים", UnitType.GRAM, KosherType.PARVE),
        ("ג'לטין", "מזווה ויבשים", UnitType.GRAM, KosherType.PARVE),
        ("פקטין", "מזווה ויבשים", UnitType.GRAM, KosherType.PARVE),
        
        # מזווה - חריגים בליטר
        ("קצפת צמחית", "מזווה ויבשים", UnitType.LITER, KosherType.PARVE),
        ("שמן זית", "מזווה ויבשים", UnitType.LITER, KosherType.PARVE),
        ("שמן קנולה", "מזווה ויבשים", UnitType.LITER, KosherType.PARVE),
        
        # רטבים ותבלינים - בסיס ליטר
        ("מיונז", "רטבים ותבלינים", UnitType.LITER, KosherType.PARVE),
        ("טחינה", "רטבים ותבלינים", UnitType.LITER, KosherType.PARVE),
        ("צ'ילי מתוק", "רטבים ותבלינים", UnitType.LITER, KosherType.PARVE),
        ("סילאן", "רטבים ותבלינים", UnitType.LITER, KosherType.PARVE),
        ("דבש", "רטבים ותבלינים", UnitType.LITER, KosherType.PARVE),
        ("חרדל", "רטבים ותבלינים", UnitType.LITER, KosherType.PARVE),
        ("טריאקי", "רטבים ותבלינים", UnitType.LITER, KosherType.PARVE),
        ("פסטו", "רטבים ותבלינים", UnitType.LITER, KosherType.PARVE),
        ("ברביקיו", "רטבים ותבלינים", UnitType.LITER, KosherType.PARVE),
        ("מייפל", "רטבים ותבלינים", UnitType.LITER, KosherType.PARVE),
        ("ריבת חלב", "רטבים ותבלינים", UnitType.LITER, KosherType.PARVE),
        ("ממרח עגבניות מיובשות", "רטבים ותבלינים", UnitType.LITER, KosherType.PARVE),
        
        # רטבים - חריג בגרם
        ("זעתר", "רטבים ותבלינים", UnitType.GRAM, KosherType.PARVE),
        
        # רטבים - חריגים בק"ג
        ("מלפפון חמוץ", "רטבים ותבלינים", UnitType.KG, KosherType.PARVE),
        ("זיתים ירוקים", "רטבים ותבלינים", UnitType.KG, KosherType.PARVE),
        ("זיתים שחורים", "רטבים ותבלינים", UnitType.KG, KosherType.PARVE),
        ("שיפקה", "רטבים ותבלינים", UnitType.KG, KosherType.PARVE),
        
        # מאפה
        ("לחמניות", "מאפה", UnitType.UNIT, KosherType.PARVE),
        ("באגט", "מאפה", UnitType.UNIT, KosherType.PARVE),
        ("פרנה", "מאפה", UnitType.UNIT, KosherType.PARVE),
        ("בייגל", "מאפה", UnitType.UNIT, KosherType.PARVE),
        ("קרואסון", "מאפה", UnitType.UNIT, KosherType.PARVE),
        ("לחם דגנים", "מאפה", UnitType.UNIT, KosherType.PARVE),
        ("בריוש", "מאפה", UnitType.UNIT, KosherType.PARVE),
        ("לחמניות בריוש", "מאפה", UnitType.UNIT, KosherType.PARVE),
        ("טורטיה", "מאפה", UnitType.UNIT, KosherType.PARVE),
        
        # הוספת ביצים שחסרו
        ("ביצים", "מוצרי חלב", UnitType.UNIT, KosherType.PARVE),
    ]
    
    created_count = 0
    skipped_count = 0
    
    for name, category_name, unit, kosher in products_data:
        # בדיקה אם המוצר כבר קיים
        existing = db.query(Product).filter(Product.name == name).first()
        if existing:
            print(f"   ⊘ מוצר קיים: {name}")
            skipped_count += 1
            continue
        
        # יצירת מוצר חדש
        min_stock = get_min_stock_level(unit)
        new_product = Product(
            name=name,
            category_id=category_map[category_name],
            unit=unit,
            kosher_type=kosher,
            quantity_in_stock=0.0,
            min_stock_level=min_stock
        )
        db.add(new_product)
        created_count += 1
        
        if created_count % 20 == 0:
            print(f"   ... נוצרו {created_count} מוצרים עד כה")
    
    db.commit()
    print(f"\n✓ נוצרו {created_count} מוצרים חדשים")
    print(f"⊘ דולגו {skipped_count} מוצרים קיימים")
    return created_count, skipped_count


def print_summary(db: Session):
    """
    שלב 3: הדפסת סיכום ואימות
    """
    print("\n" + "=" * 80)
    print("=== סיכום ואימות ===")
    print("=" * 80)
    
    # סה"כ מוצרים
    total_products = db.query(Product).count()
    print(f"\n📦 סך כל המוצרים במערכת: {total_products}")
    
    # פירוט לפי קטגוריות
    print("\n📊 פירוט מספר מוצרים בכל קטגוריה:")
    print("-" * 50)
    
    categories = db.query(ProductCategory).all()
    category_stats = []
    
    for cat in categories:
        count = db.query(Product).filter(Product.category_id == cat.id).count()
        category_stats.append((cat.name, count))
        print(f"   {cat.name:25} {count:3} מוצרים")
    
    # דוגמה למוצר
    print("\n🔍 דוגמה למוצר (שורה ראשונה):")
    print("-" * 80)
    
    sample = db.query(Product).first()
    if sample:
        cat_name = sample.product_category.name if sample.product_category else "ללא קטגוריה"
        print(f"   שם המוצר:        {sample.name}")
        print(f"   קטגוריה:         {cat_name}")
        print(f"   יחידת מידה:      {sample.unit.value if sample.unit is not None else 'לא מוגדר'}")
        print(f"   כשרות:           {sample.kosher_type.value if sample.kosher_type is not None else 'לא מוגדר'}")
        print(f"   מלאי נוכחי:      {sample.quantity_in_stock}")
        print(f"   מלאי מינימלי:    {sample.min_stock_level}")
    
    print("\n" + "=" * 80)
    print("✅ הזנת הנתונים הושלמה בהצלחה!")
    print("=" * 80 + "\n")


def main():
    """
    תהליך מלא: יצירת קטגוריות והזנת מוצרים
    """
    print("=" * 80)
    print("הזנת נתונים מלאה - Master Data Products")
    print("=" * 80)
    
    db = SessionLocal()
    try:
        # שלב 1: יצירת קטגוריות
        category_map = create_categories(db)
        
        # שלב 2: הזנת מוצרים
        created, skipped = seed_products(db, category_map)
        
        # שלב 3: סיכום ואימות
        print_summary(db)
        
    except Exception as e:
        print(f"\n❌ שגיאה: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
