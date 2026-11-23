"""Enrich the existing catalogue with menus, serving tools and sample events.

The operation is additive/idempotent and never deletes existing business data.
"""

from __future__ import annotations

import shutil
import sqlite3
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "FastAPI" / "data" / "planmyevents.db"
REPORT = ROOT / "מתכונים" / "חלוקת_המתכונים_לתפריטים.md"
NOW = datetime.now().isoformat(sep=" ", timespec="seconds")


MENU_DEFINITIONS = {
    "HOSTING_TRAYS": {
        "name": "מגשי אירוח חלבי",
        "kosher": "DAIRY",
        "tray": 1,
        "description": "מגשי אירוח: סלטים, מאפים ומנות חלביות, לחמים וקינוחים אישיים.",
        "categories": [
            ("tray_salads", "סלטים ומטבלים", 1, None),
            ("tray_savory", "מאפים ומנות חלביות", 2, None),
            ("tray_breads", "לחמים ותוספות", 3, None),
            ("tray_desserts", "קינוחים אישיים", 4, None),
        ],
    },
    "MEAT_EVENTS": {
        "name": "אירוע בשרי",
        "kosher": "MEAT",
        "tray": 0,
        "description": "תפריט אירוע בשרי מלא: פתיחה, סלטים, עיקריות, תוספות וקינוחי פרווה.",
        "categories": [
            ("meat_salads", "סלטים ופתיחים", 1, 6),
            ("meat_soups", "מרקים", 2, 1),
            ("meat_mains", "מנות עיקריות", 3, 2),
            ("meat_sides", "תוספות חמות ולחמים", 4, 3),
            ("meat_desserts", "קינוחי פרווה", 5, 2),
        ],
    },
    "SHABBAT": {
        "name": "תפריט שבת",
        "kosher": "MEAT",
        "tray": 0,
        "description": "תפריט לשבת עם סלטים, דגים, מנות עיקריות, תוספות וקינוחים.",
        "categories": [
            ("shabbat_salads", "סלטים", 1, 6),
            ("shabbat_fish", "דגים ופתיחים", 2, 1),
            ("shabbat_mains", "מנות עיקריות", 3, 2),
            ("shabbat_sides", "תוספות", 4, 3),
            ("shabbat_desserts", "קינוחי פרווה", 5, 2),
        ],
    },
    "SWEET_TABLE": {
        "name": "שולחן מתוק",
        "kosher": "PARVE",
        "tray": 1,
        "description": "מבחר קינוחים אישיים, עוגות, מוסים ומאפים מתוקים לשולחן מתוק.",
        "categories": [
            ("sweet_individual", "קינוחים אישיים וכוסות", 1, None),
            ("sweet_cakes", "עוגות וחיתוכיות", 2, None),
            ("sweet_pastry", "מאפים מתוקים", 3, None),
            ("sweet_drinks", "פירות ומשקאות", 4, None),
        ],
    },
}


MEAT_MAINS = {"פרגיות במרינדת הדרים", "עוף ברביקיו", "שניצל פריך"}
FISH = {"סלמון בעשבי תיבול", "טורטייה סלמון מעושן"}
SOUPS = {"מרק כתום", "מרק אפונה וירקות", "מרק עדשים"}
DESSERTS = {
    "אקלרים בשמנת ושוקולד", "בראוניז", "כוסות קרם אוכמניות", "מוזלי",
    "מוס שמנת", "סופלה שוקולד", "עוגת גבינה אישית בריבת חלב",
    "עוגת גבינה שלוש שכבות", "עוגת קפה ושוקולד", "סיגרי פילו וחלבה",
    "שייק פירות", "בלינצ'ס שמנת",
}
BREADS = {"פוקאצ'ות", "פיציות", "לחמניות בטעמים", "לחמניות ביס"}
HOT_SIDES = {
    "פסטה מוקרמת", "תפוחי אדמה מוקרמים", "הום פרייז", "קוביות בטטה בצ'ילי",
    "אורז עם ירקות", "קוגל תפוחי אדמה", "תפוחי אדמה פריזיאניים",
    "שעועית ירוקה ושומשום", "פלפל ממולא", "טורטיות ירקות ופירה",
    "ירקות אנטיפסטי",
}
DAIRY_SAVORY = {
    "טורטייה גבינות קריספית", "טורטייה טונה וירקות", "טורטייה סלמון מעושן",
    "טורטייה פלפל קלוי וגבינת שמנת", "לזניה אישית",
    "מוסקת חצילים בגבינת שמנת", "מיני קישים", "קישים גדולים",
    "פשטידת פטריות וגבינות", "פשטידת קישואים", "פסטה מוקרמת",
    "תפוחי אדמה מוקרמים", "שקשוקה", "פיציות",
}


def is_salad(name: str) -> bool:
    return name.startswith("סלט ") or name in {
        "בורגול וירקות", "ירקות חתוכים", "קינואה וירקות", "עגבניות חי",
        "טפנד זיתים", "גבינת שמנת בטעמים",
    }


def is_parve_dessert(name: str, kosher: str) -> bool:
    return name in DESSERTS and kosher == "PARVE"


def category_keys(name: str, kosher: str) -> list[str]:
    keys: list[str] = []
    if is_salad(name):
        keys += ["tray_salads", "meat_salads", "shabbat_salads"]
    if name in DAIRY_SAVORY:
        keys.append("tray_savory")
    if name in BREADS or name in HOT_SIDES:
        keys.append("tray_breads")
    if name in DESSERTS:
        keys.append("tray_desserts")
    if name in SOUPS:
        keys.append("meat_soups")
    if name in MEAT_MAINS:
        keys += ["meat_mains", "shabbat_mains"]
    if name in FISH:
        keys.append("shabbat_fish")
    if name in HOT_SIDES or name in BREADS:
        keys += ["meat_sides", "shabbat_sides"]
    if is_parve_dessert(name, kosher):
        keys += ["meat_desserts", "shabbat_desserts"]
    if name in DESSERTS:
        if name in {"בראוניז", "עוגת גבינה שלוש שכבות", "עוגת קפה ושוקולד"}:
            keys.append("sweet_cakes")
        elif name == "סיגרי פילו וחלבה":
            keys.append("sweet_pastry")
        elif name == "שייק פירות":
            keys.append("sweet_drinks")
        else:
            keys.append("sweet_individual")
    return list(dict.fromkeys(keys))


def insert(cur: sqlite3.Cursor, table: str, fields: list[str], values: list[object]) -> int:
    cols = fields + ["created_at", "updated_at", "is_deleted"]
    vals = values + [NOW, NOW, 0]
    marks = ",".join("?" for _ in cols)
    quoted_cols = ",".join(f'"{column}"' for column in cols)
    cur.execute(f'INSERT INTO "{table}" ({quoted_cols}) VALUES ({marks})', vals)
    return cur.lastrowid


def ensure_template(cur: sqlite3.Cursor, menu_type: str, definition: dict) -> int:
    row = cur.execute("SELECT id FROM menu_templates WHERE menu_type=? AND is_deleted=0", (menu_type,)).fetchone()
    if row:
        cur.execute(
            "UPDATE menu_templates SET name=?, description=?, kosher_type=?, is_tray_menu=?, updated_at=? WHERE id=?",
            (definition["name"], definition["description"], definition["kosher"], definition["tray"], NOW, row[0]),
        )
        return row[0]
    return insert(cur, "menu_templates", ["menu_type", "name", "description", "min_guests", "base_price_per_guest", "is_tray_menu", "kosher_type", "real_dishes_extra_per_guest"], [menu_type, definition["name"], definition["description"], 10, None, definition["tray"], definition["kosher"], 0])


def ensure_category(cur: sqlite3.Cursor, template_id: int, spec: tuple) -> int:
    key, hebrew, order, quota = spec
    row = cur.execute("SELECT id FROM menu_categories WHERE template_id=? AND name=? AND is_deleted=0", (template_id, key)).fetchone()
    if row:
        cur.execute("UPDATE menu_categories SET name_hebrew=?, display_order=?, quota=?, updated_at=? WHERE id=?", (hebrew, order, quota, NOW, row[0]))
        return row[0]
    return insert(cur, "menu_categories", ["template_id", "sub_meal_id", "name", "name_hebrew", "description", "display_order", "quota", "quota_description", "guest_count_rules", "is_required", "tray_quantity", "tray_price"], [template_id, None, key, hebrew, f"קטגוריה שנבנתה ממתכוני המקור: {hebrew}", order, quota, f"לבחירה: {quota}" if quota else None, None, 1, None, None])


def serving_tool(name: str) -> str:
    if name in SOUPS:
        return "מרקית"
    if is_salad(name):
        return "קערה"
    if name in DESSERTS:
        return "צלחת קטנה" if name not in {"כוסות קרם אוכמניות", "מוס שמנת", "מוזלי"} else "כלי הגשה אישי"
    return "מגש"


def write_report(cur: sqlite3.Cursor, category_ids: dict[str, int]) -> None:
    lines = ["# חלוקת המתכונים לתפריטים", "", "החלוקה מבוססת על תיקיות המקור, שמות הקבצים, שמות המתכונים, סוג הכשרות ואופן ההגשה.", ""]
    for menu_type, definition in MENU_DEFINITIONS.items():
        lines += [f"## {definition['name']}", "", definition["description"], ""]
        for key, hebrew, _, _ in definition["categories"]:
            dishes = [r[0] for r in cur.execute("SELECT d.name FROM dishes d JOIN dish_menu_mappings m ON m.dish_id=d.id WHERE m.category_id=? AND d.is_deleted=0 AND m.is_deleted=0 ORDER BY m.display_order,d.name", (category_ids[key],))]
            lines += [f"### {hebrew}", ""] + [f"- {name}" for name in dishes] + [""]
    lines += ["## היקף המידע במערכת", ""]
    for table, label in [("products", "מוצרים וחומרי גלם"), ("tools", "כלים"), ("dishes", "מנות"), ("menu_templates", "תפריטים"), ("events", "אירועים")]:
        count = cur.execute(f'SELECT COUNT(*) FROM {table} WHERE is_deleted=0').fetchone()[0]
        lines.append(f"- {label}: {count}")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8-sig")


def main() -> None:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = DB.with_name(f"{DB.stem}_before_catalog_enrichment_{stamp}{DB.suffix}")
    shutil.copy2(DB, backup)
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    try:
        cur.execute("BEGIN")
        category_ids: dict[str, int] = {}
        template_ids: dict[str, int] = {}
        for menu_type, definition in MENU_DEFINITIONS.items():
            template_ids[menu_type] = ensure_template(cur, menu_type, definition)
            for spec in definition["categories"]:
                category_ids[spec[0]] = ensure_category(cur, template_ids[menu_type], spec)

        dishes = cur.execute("SELECT id,name,kosher_type FROM dishes WHERE is_deleted=0 ORDER BY id").fetchall()
        order_by_category: defaultdict[str, int] = defaultdict(int)
        for dish_id, name, kosher in dishes:
            for key in category_keys(name, kosher):
                category_id = category_ids[key]
                exists = cur.execute("SELECT id FROM dish_menu_mappings WHERE dish_id=? AND category_id=? AND is_deleted=0", (dish_id, category_id)).fetchone()
                if not exists:
                    order_by_category[key] += 1
                    insert(cur, "dish_menu_mappings", ["dish_id", "category_id", "is_upgrade", "extra_charge", "display_order"], [dish_id, category_id, 0, 0, order_by_category[key]])

            tool_name = serving_tool(name)
            tool = cur.execute("SELECT id FROM tools WHERE name=? AND is_deleted=0", (tool_name,)).fetchone()
            if tool:
                for table in ("serving_dishes", "dish_equipment"):
                    exists = cur.execute(f"SELECT id FROM {table} WHERE dish_id=? AND tool_id=? AND is_deleted=0", (dish_id, tool[0])).fetchone()
                    if not exists:
                        insert(cur, table, ["dish_id", "tool_id", "name", "quantity"], [dish_id, tool[0], tool_name, 1])

        # Add provenance and usage context to every ingredient product.
        for product_id, product_name in cur.execute("SELECT id,name FROM products WHERE is_deleted=0").fetchall():
            used_by = [r[0] for r in cur.execute("SELECT DISTINCT d.name FROM dishes d JOIN dish_ingredients i ON i.dish_id=d.id WHERE i.product_id=? AND d.is_deleted=0 ORDER BY d.name", (product_id,))]
            if used_by:
                description = "חומר גלם ממתכוני המקור. משמש במנות: " + ", ".join(used_by)
                cur.execute("UPDATE products SET description=?, updated_at=? WHERE id=?", (description, NOW, product_id))

        # One complete sample workflow for every new menu.
        for offset, (menu_type, definition) in enumerate(MENU_DEFINITIONS.items(), 1):
            event_name = f"אירוע לדוגמה – {definition['name']}"
            existing = cur.execute("SELECT id FROM events WHERE name=? AND is_deleted=0", (event_name,)).fetchone()
            if existing:
                event_id = existing[0]
            else:
                event_id = insert(cur, "events", ["name", "event_category", "menu_type", "status", "date", "event_time", "city", "guest_count", "is_morning_split", "total_price", "notes", "is_real_dishes", "calculated_price", "day_sequence_number", "has_elevator", "has_nearby_parking", "has_back_entrance", "requires_carts", "check_refrigerator", "check_freezer", "check_hot_plate", "connect_gas", "put_in_refrigerator", "put_in_freezer", "put_on_hot_plate", "count_boxes", "check_drinks", "check_rolls"], [event_name, definition["name"], menu_type, "DRAFT", (datetime.now() + timedelta(days=30 + offset * 7)).isoformat(sep=" "), "18:00", "ירושלים", 50, 0, 0, "אירוע דוגמה שנבנה ממאגר המתכונים המלא", 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
                insert(cur, "event_owners", ["event_id", "name", "phone", "email", "order"], [event_id, "לקוח לדוגמה", "050-0000000", None, 0])
            if not cur.execute("SELECT 1 FROM event_dishes WHERE event_id=? AND is_deleted=0", (event_id,)).fetchone():
                for key, _, _, _ in definition["categories"]:
                    category_id = category_ids[key]
                    candidates = cur.execute("SELECT dish_id FROM dish_menu_mappings WHERE category_id=? AND is_deleted=0 ORDER BY display_order LIMIT 2", (category_id,)).fetchall()
                    for (dish_id,) in candidates:
                        insert(cur, "event_dishes", ["event_id", "dish_id", "sub_meal_id", "category_id", "quantity", "is_upgrade", "is_gift", "extra_charge", "notes", "is_draft"], [event_id, dish_id, None, category_id, 1, 0, 0, 0, "בחירת דוגמה מתוך התפריט", 0])

        write_report(cur, category_ids)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    print(f"Catalog enriched. Backup: {backup}")
    print(f"Report: {REPORT}")


if __name__ == "__main__":
    main()
