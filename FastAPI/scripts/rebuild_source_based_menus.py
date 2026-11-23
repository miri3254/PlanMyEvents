"""Rebuild menu assignments strictly from each dish's source file."""

from __future__ import annotations

import shutil
import sqlite3
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "FastAPI" / "data" / "planmyevents.db"
REPORT = ROOT / "מתכונים" / "שיוך_תפריטים_לפי_קבצי_המקור.md"
NOW = datetime.now().isoformat(sep=" ", timespec="seconds")

MENUS = {
    "HOSTING_TRAYS": ("מגשי אירוח", "DAIRY", 1),
    "MEAT_EVENTS": ("אירוע בשרי", "MEAT", 0),
    "SHABBAT": ("תפריט שבת", "PARVE", 0),
    "HANUKKAH_5786": ("תפריט מנצח – חנוכה תשפ״ו", "MEAT", 0),
}

CATEGORIES = {
    "HOSTING_TRAYS": [
        ("source_hosting_salads", "סלטים ומטבלים"),
        ("source_hosting_savory", "מנות ומאפים מלוחים"),
        ("source_hosting_breads", "לחמים ותוספות"),
        ("source_hosting_desserts", "קינוחים"),
    ],
    "MEAT_EVENTS": [
        ("source_meat_salads", "סלטים ורטבים"),
        ("source_meat_soups", "מרקים"),
        ("source_meat_mains", "מנות עיקריות ודגים"),
        ("source_meat_sides", "תוספות"),
        ("source_meat_desserts", "קינוחים"),
    ],
    "SHABBAT": [("source_shabbat_sides", "תוספות לשבת")],
    "HANUKKAH_5786": [
        ("source_hanukkah_mains", "מנות עיקריות"),
        ("source_hanukkah_sides", "תוספות"),
        ("source_hanukkah_drinks", "משקאות וקינוחים"),
    ],
}

DESSERT_WORDS = ("אקלר", "בראונ", "קרם", "מוזלי", "מוס ", "סופלה", "עוג", "סיגרי", "שייק", "בלינצ")
BREAD_WORDS = ("פוקאצ", "פיצ", "לחמ")
SOUP_WORDS = ("מרק ",)
SALAD_WORDS = ("סלט ", "בורגול", "קינואה", "טפנד", "עגבניות חי", "ירקות חתוכים", "גבינת שמנת")
MAIN_WORDS = ("פרגיות", "עוף ", "שניצל", "סלמון")


def source_of(description: str | None) -> str:
    if not description:
        return ""
    first = description.splitlines()[0]
    return first.removeprefix("מקור: ").strip()


def menu_for_source(name: str, source: str) -> str:
    if source.startswith("מגשי אירוח מתכונים איך מכינים"):
        return "HOSTING_TRAYS"
    if "מתכונים לאירוע בשרי" in source:
        return "MEAT_EVENTS"
    if "קוגל תפוח אדמה" in source:
        return "SHABBAT"
    if source.startswith("תפריט מנצח מתכונים והוראות חנוכה"):
        return "HANUKKAH_5786"
    raise ValueError(f"אין תפריט מקור עבור {name}: {source}")


def category_for(menu: str, name: str) -> str:
    if menu == "HOSTING_TRAYS":
        if any(word in name for word in DESSERT_WORDS): return "source_hosting_desserts"
        if any(word in name for word in BREAD_WORDS): return "source_hosting_breads"
        if any(word in name for word in SALAD_WORDS): return "source_hosting_salads"
        return "source_hosting_savory"
    if menu == "MEAT_EVENTS":
        if any(word in name for word in DESSERT_WORDS): return "source_meat_desserts"
        if any(word in name for word in SOUP_WORDS): return "source_meat_soups"
        if any(word in name for word in MAIN_WORDS): return "source_meat_mains"
        if any(word in name for word in SALAD_WORDS): return "source_meat_salads"
        return "source_meat_sides"
    if menu == "SHABBAT":
        return "source_shabbat_sides"
    if name == "שייק פירות":
        return "source_hanukkah_drinks"
    if any(word in name for word in MAIN_WORDS):
        return "source_hanukkah_mains"
    return "source_hanukkah_sides"


def insert(cur, table: str, fields: list[str], values: list[object]) -> int:
    cols = fields + ["created_at", "updated_at", "is_deleted"]
    vals = values + [NOW, NOW, 0]
    quoted = ",".join(f'"{col}"' for col in cols)
    cur.execute(f'INSERT INTO "{table}" ({quoted}) VALUES ({",".join("?" for _ in cols)})', vals)
    return cur.lastrowid


def ensure_template(cur, menu_type: str) -> int:
    name, kosher, tray = MENUS[menu_type]
    description = "תפריט שנבנה ישירות לפי תיקיית וקובץ המקור של כל מתכון."
    row = cur.execute("SELECT id FROM menu_templates WHERE menu_type=?", (menu_type,)).fetchone()
    if row:
        cur.execute("UPDATE menu_templates SET name=?,description=?,kosher_type=?,is_tray_menu=?,is_deleted=0,deleted_at=NULL,updated_at=? WHERE id=?", (name, description, kosher, tray, NOW, row[0]))
        return row[0]
    return insert(cur, "menu_templates", ["menu_type","name","description","min_guests","base_price_per_guest","is_tray_menu","kosher_type","real_dishes_extra_per_guest"], [menu_type,name,description,1,None,tray,kosher,0])


def main() -> None:
    backup = DB.with_name(f"{DB.stem}_before_source_menus_{datetime.now():%Y%m%d_%H%M%S}{DB.suffix}")
    shutil.copy2(DB, backup)
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    try:
        cur.execute("BEGIN")
        # Retire every previous generated mapping/category. Recipes and ingredients stay intact.
        cur.execute("UPDATE dish_menu_mappings SET is_deleted=1,deleted_at=?,updated_at=? WHERE is_deleted=0", (NOW, NOW))
        cur.execute("UPDATE menu_categories SET is_deleted=1,deleted_at=?,updated_at=? WHERE is_deleted=0", (NOW, NOW))
        cur.execute("UPDATE menu_templates SET is_deleted=1,deleted_at=?,updated_at=? WHERE is_deleted=0", (NOW, NOW))

        template_ids = {key: ensure_template(cur, key) for key in MENUS}
        category_ids: dict[str, int] = {}
        for menu, specs in CATEGORIES.items():
            for order, (key, label) in enumerate(specs, 1):
                category_ids[key] = insert(cur, "menu_categories", ["template_id","sub_meal_id","name","name_hebrew","description","display_order","quota","quota_description","guest_count_rules","is_required","tray_quantity","tray_price"], [template_ids[menu],None,key,label,"שיוך לפי קובץ המקור",order,None,None,None,1,None,None])

        by_category: defaultdict[str, int] = defaultdict(int)
        assignments: list[tuple[str,str,str,str]] = []
        dishes = cur.execute("SELECT id,name,description,kosher_type FROM dishes WHERE is_deleted=0 ORDER BY id").fetchall()
        for dish_id, name, description, kosher in dishes:
            source = source_of(description)
            menu = menu_for_source(name, source)
            category = category_for(menu, name)
            # Hard safety: a dairy dish can only originate from the hosting-tray files.
            if kosher == "DAIRY" and menu != "HOSTING_TRAYS":
                raise ValueError(f"מנה חלבית מחוץ למגשי אירוח: {name} -> {source}")
            by_category[category] += 1
            insert(cur, "dish_menu_mappings", ["dish_id","category_id","is_upgrade","extra_charge","display_order"], [dish_id,category_ids[category],0,0,by_category[category]])
            assignments.append((MENUS[menu][0], dict(CATEGORIES[menu])[category], name, source))

        # Retire only generated demo events, then create one event per source menu.
        demo_ids = [r[0] for r in cur.execute("SELECT id FROM events WHERE name LIKE 'אירוע דוגמה%' OR name LIKE 'אירוע לדוגמה%' OR name LIKE 'אירוע דמה%' ").fetchall()]
        for event_id in demo_ids:
            cur.execute("UPDATE events SET is_deleted=1,deleted_at=?,updated_at=? WHERE id=?", (NOW,NOW,event_id))
            cur.execute("UPDATE event_dishes SET is_deleted=1,deleted_at=?,updated_at=? WHERE event_id=?", (NOW,NOW,event_id))
            cur.execute("UPDATE event_owners SET is_deleted=1,deleted_at=?,updated_at=? WHERE event_id=?", (NOW,NOW,event_id))
        for offset, menu in enumerate(MENUS, 1):
            event_id = insert(cur, "events", ["name","event_category","menu_type","status","date","event_time","city","guest_count","is_morning_split","total_price","notes","is_real_dishes","calculated_price","day_sequence_number","has_elevator","has_nearby_parking","has_back_entrance","requires_carts","check_refrigerator","check_freezer","check_hot_plate","connect_gas","put_in_refrigerator","put_in_freezer","put_on_hot_plate","count_boxes","check_drinks","check_rolls"], [f"אירוע דוגמה לפי מקור – {MENUS[menu][0]}",MENUS[menu][0],menu,"DRAFT",(datetime.now()+timedelta(days=40+offset*7)).isoformat(sep=" "),"18:00","ירושלים",50,0,0,"נבנה לפי קבצי המקור",1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0])
            insert(cur, "event_owners", ["event_id","name","phone","email","order"], [event_id,"לקוח לדוגמה","050-0000000",None,0])
            category_set = [category_ids[key] for key, _ in CATEGORIES[menu]]
            for category_id in category_set:
                for dish_id, in cur.execute("SELECT dish_id FROM dish_menu_mappings WHERE category_id=? AND is_deleted=0 ORDER BY display_order LIMIT 2", (category_id,)).fetchall():
                    insert(cur, "event_dishes", ["event_id","dish_id","sub_meal_id","category_id","quantity","is_upgrade","is_gift","extra_charge","notes","is_draft"], [event_id,dish_id,None,category_id,1,0,0,0,"בחירה לפי תפריט המקור",0])

        lines = ["# שיוך תפריטים לפי קבצי המקור", "", "כל מנה משויכת לתפריט אחד בלבד, לפי התיקייה והקובץ שמופיעים בתיאור המקור שלה.", ""]
        for menu_name in [value[0] for value in MENUS.values()]:
            lines += [f"## {menu_name}", ""]
            for assigned_menu, category, name, source in assignments:
                if assigned_menu == menu_name:
                    lines.append(f"- **{category}:** {name} — `{source}`")
            lines.append("")
        REPORT.write_text("\n".join(lines), encoding="utf-8-sig")
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    print(f"Rebuilt {len(assignments)} source-based mappings. Backup: {backup}")


if __name__ == "__main__":
    main()
