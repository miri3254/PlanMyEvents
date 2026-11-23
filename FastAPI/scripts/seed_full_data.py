"""
Seed script — creates all 6 menu templates with categories and sample dishes.
Skips any menu types that already exist in the database.

Run from FastAPI/:   python -m scripts.seed_full_data
"""

import sys
import os

# Ensure project root on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.engine import engine
from app.db.base import Base
from app.db.session import SessionLocal
from app.models import *  # noqa: F401,F403
from app.models.menu import MenuTemplate, MenuSubMeal, MenuCategory, DishMenuMapping
from app.models.dish import Dish
from app.core.enums import MenuType, KosherType

# Module-level DB session (set in seed())
db = None


# ================================================================
# Helper functions
# ================================================================
def make_dish(name: str, kosher: KosherType, desc: str = "") -> Dish:
    d = Dish(name=name, kosher_type=kosher, description=desc)
    db.add(d)
    db.flush()
    return d


def make_template(mt: MenuType, name: str, min_g: int, price: float, is_tray: bool = False) -> MenuTemplate:
    t = MenuTemplate(menu_type=mt, name=name, min_guests=min_g, base_price_per_guest=price, is_tray_menu=is_tray)
    db.add(t)
    db.flush()
    return t


def make_sub_meal(template: MenuTemplate, name: str, order: int, splittable: bool = False, split_charge: float = 0) -> MenuSubMeal:
    sm = MenuSubMeal(template_id=template.id, name=name, display_order=order, is_splittable=splittable, split_extra_charge=split_charge)
    db.add(sm)
    db.flush()
    return sm


def make_category(sub_meal: MenuSubMeal, name_he: str, name_en: str, order: int, quota: int = None, required: bool = True, tray_qty: int = None, tray_price: float = None, rules: dict = None) -> MenuCategory:
    c = MenuCategory(
        sub_meal_id=sub_meal.id, name_hebrew=name_he, name=name_en,
        display_order=order, quota=quota, is_required=required,
        tray_quantity=tray_qty, tray_price=tray_price,
        guest_count_rules=rules,
    )
    db.add(c)
    db.flush()
    return c


def map_dish(dish: Dish, category: MenuCategory, upgrade: bool = False, extra: float = 0):
    m = DishMenuMapping(dish_id=dish.id, category_id=category.id, is_upgrade=upgrade, extra_charge=extra)
    db.add(m)


# ================================================================
# Template seed functions
# ================================================================

def seed_shabbat():
    t = make_template(MenuType.SHABBAT, "תפריט שבת", 50, 180.0)

    # ── ליל שבת ──
    sm_friday = make_sub_meal(t, "ליל שבת", 1)

    cat = make_category(sm_friday, "סלטים", "salads", 1, quota=8, rules={"threshold": 80, "bonus_quota": 2})
    for name in ["סלט ירקות קצוץ", "סלט חצילים", "סלט מטבוחה", "חומוס", "טחינה", "סלט כרוב", "סלט גזר מרוקאי", "סלט חציל בשר טלה", "סלט פלפלים קלויים", "סלט נאמנם"]:
        map_dish(make_dish(name, KosherType.PARVE), cat)

    cat = make_category(sm_friday, "מנה ראשונה", "first_course", 2, quota=2)
    for name in ["מרק כדורי בשר", "מרק ירקות", "מרק עוף עם שקדים", "פסטידה בשרית"]:
        map_dish(make_dish(name, KosherType.MEAT), cat)

    cat = make_category(sm_friday, "עיקרית", "main_course", 3, quota=2, rules={"threshold": 80, "bonus_quota": 1})
    for name in ["עוף בגריל", "שניצל תנור", "קציצות כבש", "בקר ביין", "כנפיים מתובלות"]:
        map_dish(make_dish(name, KosherType.MEAT), cat)
    map_dish(make_dish("פילה דג בתנור", KosherType.PARVE), cat, upgrade=True, extra=15)

    cat = make_category(sm_friday, "תוספות", "side_dishes", 4, quota=3)
    for name in ["אורז לבן", "אורז אדום", "קוסקוס", "תפוחי אדמה", "פתיתים"]:
        map_dish(make_dish(name, KosherType.PARVE), cat)

    cat = make_category(sm_friday, "קינוח", "dessert", 5, quota=1, required=False)
    for name in ["עוגת שוקולד", "פירות העונה"]:
        map_dish(make_dish(name, KosherType.PARVE), cat)

    # ── בוקר שבת ──
    sm_morning = make_sub_meal(t, "בוקר שבת", 2, splittable=True, split_charge=25.0)

    cat = make_category(sm_morning, "סלטים", "salads", 1, quota=6)
    for name in ["סלט ירקות טרי", "סלט אבוקדו", "סלט קיסר", "סלט טונה"]:
        map_dish(make_dish(name, KosherType.PARVE), cat)

    cat = make_category(sm_morning, "מאפים", "pastries", 2, quota=3)
    for name in ["בורקס גבינה", "בורקס תפוחי אדמה", "קרואסון", "לחם אחיד"]:
        map_dish(make_dish(name, KosherType.DAIRY), cat)

    cat = make_category(sm_morning, "עיקרית", "main_course", 3, quota=2)
    for name in ["שקשוקה", "חביתה ספרדית", "פסטה שמנת"]:
        map_dish(make_dish(name, KosherType.DAIRY), cat)

    cat = make_category(sm_morning, "תוספות", "side_dishes", 4, quota=2)
    for name in ["אורז לבן", "סלט פסטה"]:
        map_dish(make_dish(name, KosherType.PARVE), cat)

    cat = make_category(sm_morning, "קינוח", "dessert", 5, quota=1, required=False)
    for name in ["מלבי", "סלט פירות"]:
        map_dish(make_dish(name, KosherType.PARVE), cat)


def seed_meat():
    t = make_template(MenuType.MEAT_MENU, "תפריט בשרי", 1, 150.0)
    sm = make_sub_meal(t, "ארוחה", 1)

    cat = make_category(sm, "סלטים", "salads", 1, quota=8, rules={"threshold": 80, "bonus_quota": 2})
    for name in ["סלט טבולה בשרי", "סלט כבד עוף", "סלט חצילים בשרי", "סלט פסטרמה"]:
        map_dish(make_dish(name, KosherType.MEAT), cat)

    cat = make_category(sm, "מנה ראשונה", "first_course", 2, quota=2)
    for name in ["מרק בשר", "קרפצ'יו כבד אווז"]:
        map_dish(make_dish(name, KosherType.MEAT), cat)

    cat = make_category(sm, "עיקרית", "main_course", 3, quota=2, rules={"threshold": 80, "bonus_quota": 1})
    for name in ["סטייק אנטריקוט", "כתף טלה", "עוף ממולא", "צלי בשר"]:
        map_dish(make_dish(name, KosherType.MEAT), cat)

    cat = make_category(sm, "תוספות", "side_dishes", 4, quota=3)
    for name in ["אורז", "ירקות כבושים", "פירה", "תפוחי אדמה אפויים"]:
        map_dish(make_dish(name, KosherType.PARVE), cat)

    cat = make_category(sm, "קינוח", "dessert", 5, quota=1, required=False)
    for name in ["מוס שוקולד פרווה", "סורבה פירות"]:
        map_dish(make_dish(name, KosherType.PARVE), cat)


def seed_dairy():
    t = make_template(MenuType.DAIRY_MENU, "תפריט חלבי", 1, 130.0)
    sm = make_sub_meal(t, "ארוחה", 1)

    cat = make_category(sm, "סלטים", "salads", 1, quota=6)
    for name in ["סלט קפרזה", "סלט יווני", "סלט קיסר חלבי"]:
        map_dish(make_dish(name, KosherType.DAIRY), cat)

    cat = make_category(sm, "מאפים", "pastries", 2, quota=3)
    for name in ["פיצה מרגריטה", "פוקצ'ה", "קיש גבינות"]:
        map_dish(make_dish(name, KosherType.DAIRY), cat)

    cat = make_category(sm, "עיקרית", "main_course", 3, quota=2)
    for name in ["לזניה", "פסטה אלפרדו", "רביולי גבינה"]:
        map_dish(make_dish(name, KosherType.DAIRY), cat)

    cat = make_category(sm, "קינוח", "dessert", 4, quota=2, required=False)
    for name in ["טירמיסו", "עוגת גבינה"]:
        map_dish(make_dish(name, KosherType.DAIRY), cat)


def seed_meat_trays():
    t = make_template(MenuType.MEAT_TRAYS, "מגשי אירוח בשרי", 1, 0, is_tray=True)
    sm = make_sub_meal(t, "מגשים", 1)

    cat = make_category(sm, "מגשים קרים", "cold_trays", 1, tray_price=180.0)
    for name in ["מגש כבד קצוץ", "מגש פסטרמה ונקניקיות", "מגש סלטי בשר"]:
        map_dish(make_dish(name, KosherType.MEAT), cat)

    cat = make_category(sm, "מגשים חמים", "hot_trays", 2, tray_price=220.0)
    for name in ["מגש שניצלים", "מגש כנפיים", "מגש קבב"]:
        map_dish(make_dish(name, KosherType.MEAT), cat)

    cat = make_category(sm, "תוספות", "side_trays", 3, tray_price=120.0)
    for name in ["מגש אורז", "מגש פתיתים", "מגש ירקות אפויים"]:
        map_dish(make_dish(name, KosherType.PARVE), cat)


def seed_dairy_trays():
    t = make_template(MenuType.DAIRY_TRAYS, "מגשי אירוח חלבי", 1, 0, is_tray=True)
    sm = make_sub_meal(t, "מגשים", 1)

    cat = make_category(sm, "מגשים קרים", "cold_trays", 1, tray_price=160.0)
    for name in ["מגש גבינות", "מגש סושי", "מגש סלטים"]:
        map_dish(make_dish(name, KosherType.DAIRY), cat)

    cat = make_category(sm, "מגשים חמים", "hot_trays", 2, tray_price=200.0)
    for name in ["מגש בורקסים", "מגש פסטה", "מגש קישים"]:
        map_dish(make_dish(name, KosherType.DAIRY), cat)

    cat = make_category(sm, "מאפים", "pastry_trays", 3, tray_price=140.0)
    for name in ["מגש מאפים מעורב", "מגש קרואסונים"]:
        map_dish(make_dish(name, KosherType.DAIRY), cat)


def seed_sweet_table():
    t = make_template(MenuType.SWEET_TABLE, "תפריט מתוק", 150, 45.0)
    sm = make_sub_meal(t, "שולחן מתוק", 1)

    cat = make_category(sm, "עוגות", "cakes", 1, quota=4)
    for name in ["עוגת שוקולד בלגי", "עוגת גבינה אפויה", "עוגת תפוחים", "עוגת מוס פירות"]:
        map_dish(make_dish(name, KosherType.DAIRY), cat)

    cat = make_category(sm, "קינוחים אישיים", "mini_desserts", 2, quota=6)
    for name in ["מיני קאפקייקס", "טארטלטים", "אקלרים", "מקרונים", "פטיפורים", "שוקולד בלגי"]:
        map_dish(make_dish(name, KosherType.DAIRY), cat)

    cat = make_category(sm, "פירות", "fruits", 3, quota=2, required=False)
    for name in ["סלסלת פירות מעוטרת", "שיפודי פירות"]:
        map_dish(make_dish(name, KosherType.PARVE), cat)

    cat = make_category(sm, "משקאות", "drinks", 4, quota=3)
    for name in ["קפה ותה", "מיצים טבעיים", "שתייה קלה"]:
        map_dish(make_dish(name, KosherType.PARVE), cat)


# ================================================================
# Main seed orchestrator
# ================================================================
SEED_MAP = {
    MenuType.SHABBAT: seed_shabbat,
    MenuType.MEAT_MENU: seed_meat,
    MenuType.DAIRY_MENU: seed_dairy,
    MenuType.MEAT_TRAYS: seed_meat_trays,
    MenuType.DAIRY_TRAYS: seed_dairy_trays,
    MenuType.SWEET_TABLE: seed_sweet_table,
}


def seed():
    global db
    print("יוצר טבלאות...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        existing_types = {t.menu_type for t in db.query(MenuTemplate).all()}
        missing = [mt for mt in SEED_MAP if mt not in existing_types]

        if not missing:
            print(f"כל 6 התבניות קיימות — מדלג על seed.")
            return

        print(f"נמצאו {len(existing_types)} תבניות קיימות, מוסיף {len(missing)} חסרות...")

        for mt in missing:
            print(f"  מזריע: {mt.value}")
            SEED_MAP[mt]()

        db.commit()
        print("✓ Seed הושלם בהצלחה!")
        print(f"  - תבניות: {db.query(MenuTemplate).count()}")
        print(f"  - תת-ארוחות: {db.query(MenuSubMeal).count()}")
        print(f"  - קטגוריות: {db.query(MenuCategory).count()}")
        print(f"  - מנות: {db.query(Dish).count()}")
        print(f"  - שיוכי מנות: {db.query(DishMenuMapping).count()}")

    except Exception as e:
        db.rollback()
        print(f"שגיאה: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
