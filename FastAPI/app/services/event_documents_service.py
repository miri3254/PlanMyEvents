"""Printed event documents (branded): serving instructions, packing list, driver out/return sheets.

Business source: docs/catering-todo/sources/caterer-document-instructions-2026-11.md and the
workbook tool sheets ("חישוב כלים"). All quantities come from EventCalculationService —
documents never recompute business formulas, they only arrange the calculated rows.
"""
from __future__ import annotations

from collections import OrderedDict
from io import BytesIO
from typing import Any

from sqlalchemy.orm import Session

from app.models.dish import Dish
from app.models.event import Event, EventDeliveryNote
from app.models.menu import MenuCategory, MenuSubMeal
from app.services.event_calculation_service import EventCalculationService
from app.utils import branded_pdf as B
from app.utils.pdf_generator import _is_waiter_cutlery

# Workbook "חישוב כלים" E8/E9/E11/E5 (table-setting instructions), verbatim meaning.
SETTING_REGULAR = ("צלחת קטנה וגדולה מהסוג היפה (לא מהפשוטות של הספייר וההגשה האישית) + כוס מהסוג היפה + "
                   "מפית מדוגמת + 2 סכינים + 2 מזלגות מהסוג היפה + מלחייה + ברכונים באמצע")
SETTING_SWEET = ("עריכה של חצי מכמות המנות: צלחת קטנה מהסוג היפה (לא מהפשוטות של הספייר וההגשה האישית) + "
                 "כוס מהסוג היפה + מפית, סכין ומזלג מהסוג היפה + מלחייה + ברכונים באמצע")
SETTING_EXTRA = ("בשולחן מתוק כל המנות הנוספות, וכן באירוע רגיל אם האורחים מבקשים צלחת נוספת / נשבר / נוספו אורחים "
                 "וכדומה – להביא מהסוג הפשוט יותר")
SETTING_TABLES = ("סידור שולחנות לפי מה שכתוב בדף: מזרח / מרובעים / ח' וכדומה. מפות לפי הצורך: שולחן מרובע או רחב – "
                  "מפות מרובעות; צר וארוך – מלבניות (מזרח בדרך כלל במלבן)")
CENTRAL_RULE = "כלים מרכזיים: כלי אחד לכל 8 מקומות ערוכים"

PER_EVENT_WAITER_TOOLS = ["פלטה", "כף שטוחה למלצר מטבח", "כף גדולה למלצר מטבח", "סכין",
                          "מחתה עמוקה לאורז וכדומה", "מצקת לרוטב"]
PER_WAITER_TOOLS = ["מגש שחור למנה ראשונה ואיסוף", "מלקחיים"]
EXTRAS = ["כפפות", "אשפתונים", "מלחיות", "מלח", "ברכונים"]
RETURN_FIXED = ["סירים", "טרמפוטים", "צידניות", "שתייה סגורה", "חד\"פ סגור"]

STAGES = [
    ("שלב 1 – מהמטבח לרכב", [
        "לקחת ארגז אחד בכל פעם.",
        "אם הקרטונים קלים, יציבים ולא גדושים – אפשר לסחוב אחד על השני בהצלבה.",
        "להרים כל ארגז בשתי ידיים.",
        "לשמור שהארגז יישאר ישר בהליכה ובהנחה.",
        "אם כבד – לבקש עזרה. לא לגרור.",
        "שקיות – לשים בתוך קרטון שלא ייקרעו.",
        "מוצרים לקירור/הקפאה – להוציא אחרונים מהמטבח וראשונים מהרכב, ולהכניס מיד למקרר/מקפיא של האולם.",
    ]),
    ("שלב 2 – הנחה ברכב", [
        "לשמור מראש מקום לסירים אם יש, לפי הגדלים.",
        "חם ליד חם וקר ליד קר, שלא יחמיץ או יימס.",
        "צידניות וקרטונים סגורים קשיחים – אפשר אחד על השני.",
        "דברים עדינים – לא אחד על השני כלל. אסור לשים כבד על רך.",
        "למלא חללים ברכב בקרטון/שקיות כדי שלא יזוזו בנסיעה.",
        "לא לדחוס בכוח מה שלא נכנס – לחפש פתרון, לא לדחוס, לכווץ ולהזיק.",
    ]),
    ("שלב 3 – נסיעה", [
        "להאט בסיבובים ובפסי האטה.",
        "לדאוג שלא תהיה שמש על האוכל כל הנסיעה.",
        "להדליק מזגן על טורבו כל הנסיעה והחנייה.",
    ]),
    ("שלב 4 – מהרכב למקום האירוע", [
        "לקחת בכל פעם ארגז אחד בלבד.",
        "אם הקרטונים קלים, יציבים ולא גדושים – אפשר לסחוב אחד על השני בהצלבה.",
        "להרים כל ארגז בשתי ידיים.",
        "לשמור את הארגז ישר גם בסחיבה וגם בהנחה.",
        "אם כבד – מבקשים עזרה מהמלצרים.",
        "לא לגרור.",
        "אין לבקש עזרה מבעלי השמחה בשום אופן.",
        "שקיות – לסחוב בתוך קרטון.",
    ]),
    ("שלב 5 – הנחה במקום האירוע", [
        "מוצרים לקירור/הקפאה – להכניס מיד למקרר/מקפיא.",
        "סירים שממשיכים לחימום – להדליק את הפלטה, לוודא שהיא עובדת ולהניח עליה.",
    ]),
]
AESTHETICS = ("האסתטיקה והמקצועיות של עובדי העסק הן חלק חשוב בנראות העסק ובפרט ברושם הראשוני. אם משהו נשבר, נשפך "
              "או איבד את צורתו – נפגעים השם והנראות של כל העסק ולא רק המנה. עדיף לקחת עוד 2 דקות בזהירות "
              "מאשר שעתיים של תיקונים (ולא תמיד אפשר לתקן).")
BEFORE_LEAVING = [
    "להתעדכן מול המשרד לגבי שינויים של הרגע האחרון.",
    "לספור את הארגזים ולהשוות לכמות הרשומה בדף.",
    "לוודא שהשתייה והלחמניות הועמסו.",
    "מוצרים לקירור/הקפאה הועמסו אחרונים.",
]
ON_ARRIVAL = [
    "מוצרים לקירור/הקפאה הוכנסו מיד למקרר/מקפיא.",
    "המקפיא עובד – אם לא, לחבר אותו ולבדוק שנדלק.",
    "הפלטה דולקת – אם לא, לחבר אותה ולבדוק שנדלקת.",
    "ספירת ארגזים והשוואה לכמות בדף – הכל הגיע.",
    "השתייה במקרר – אם לא, להכניס למקפיא.",
    "הלחמניות הגיעו – אם לא, לעדכן מיד את מנהל המשרד.",
    "הציוד הונח רק במקום המוגדר, בתיאום עם איש הקשר בשטח.",
    "ספירה חוזרת, השלמת הבדיקות ואישור איש הקשר – לפני העזיבה.",
    "הודעה לבעלי הקייטרינג שהמשלוח נמסר והכל סודר.",
]
RETURN_INSTRUCTIONS = [
    "לבדוק על השולחנות, במטבח ובפינות שלא נשאר שום מוצר של הקייטרינג.",
    "לבדוק שלא חוזר לקייטרינג משהו שאינו של הקייטרינג.",
    "אם יש שאלה על מוצר מסוים – להתקשר למנהל המשרד לברר.",
    "לבדוק שכל כלי המלצר נארזו לפי המספור. אם חסר – לדווח מיד.",
    "לבדוק את מספר המפות.",
    "לבדוק שכל הצידניות חזרו.",
    "לא לדפוק באמצע הלילה – להשאיר בחוץ ולעדכן מיד טלפונית אם עונים.",
]


def _fmt(value) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value or "")
    return str(int(number)) if number.is_integer() else f"{number:.2f}".rstrip("0").rstrip(".")


def _get(row, key):
    return row.get(key) if isinstance(row, dict) else getattr(row, key, None)


def _yes(value) -> str:
    return "כן" if value else "לא"


class EventDocumentsService:
    def __init__(self, db: Session):
        self.db = db
        self.calc = EventCalculationService(db)

    # ── data ──────────────────────────────────────────────────────────
    def _context(self, event: Event) -> dict[str, Any]:
        summary = self.calc.summarize(event)
        profile, template = self.calc._menu_calculation_profile(event)
        return {
            "summary": summary,
            "profile": profile,
            "template": template,
            "is_sweet": profile == "sweet",
            "places": self.calc._place_setting_count(event),
            "waiters": self.calc.waiter_count(event),
            "tables": self.calc.table_count(event),
        }

    def _header_pairs(self, event: Event, ctx: dict, driver: bool = False) -> list[tuple[str, Any]]:
        owners = " | ".join(f"{o.name} {o.phone or ''}".strip() for o in event.owners)
        pairs = [
            ("תאריך", event.date.strftime("%d/%m/%Y") if event.date else ""),
            ("שעה", event.event_time),
            ("תאריך עברי", event.hebrew_date),
            ("תפריט", event.menu_type),
            ("אולם / מקום", event.venue_name),
            ("כתובת", ", ".join(p for p in [event.address, event.city] if p)),
            ("קומה", f"{event.floor}{' (יש מעלית)' if event.has_elevator else ''}" if event.floor not in (None, "") else None),
            ("קוד כניסה", event.access_code),
            ("בעל האולם", event.hall_owner_name),
            ("טלפון בעל האולם", event.hall_owner_phone),
            ("איש קשר במקום", event.onsite_contact_name),
            ("טלפון איש קשר", event.onsite_contact_phone),
            ("בעלי האירוע", owners),
            ("סוג כלים", event.dishware_type or ("כלים אמיתיים" if event.is_real_dishes else "חד פעמי")),
        ]
        if not driver:
            pairs += [("סועדים", event.guest_count), ("מקומות ערוכים", ctx["places"]),
                      ("שולחנות", ctx["tables"]), ("מלצרים", ctx["waiters"])]
        return pairs

    def _category(self, ed) -> tuple[int, str, str]:
        cat = self.db.get(MenuCategory, ed.category_id) if ed.category_id else None
        sub = self.db.get(MenuSubMeal, ed.sub_meal_id) if ed.sub_meal_id else None
        if not cat and ed.dish and ed.dish.menu_mappings:
            cat = ed.dish.menu_mappings[0].category
        name = (cat.name_hebrew if cat else None) or "מנות נוספות"
        return ((sub.display_order if sub else 0) * 1000 + (cat.display_order if cat else 999), name, sub.name if sub else "")

    def dishes(self, event: Event, ctx: dict) -> "OrderedDict[str, list[dict]]":
        tools_by_dish = self.calc.serving_tools_for_document(event)
        selections = self.calc._selection_map(event.id, "serving")
        addons: dict[int, list[str]] = {}
        for row in ctx["summary"].product_requirements:
            dish_id = (_get(row, "details") or {}).get("dish_id")
            if dish_id:
                addons.setdefault(dish_id, []).append(f"{_get(row, 'name')} {_fmt(_get(row, 'quantity'))} {_get(row, 'unit') or ''}".strip())
        rows = []
        for ed in event.dishes:
            dish = ed.dish or self.db.get(Dish, ed.dish_id)
            if not dish:
                continue
            order, category, sub_meal = self._category(ed)
            mode = None
            try:
                chosen = selections.get(("dish", ed.id)) or selections.get(("dish_id", ed.dish_id))
                serving_set = self.calc._resolve_serving_set(event, ed.dish_id, chosen, ed)
                mode = serving_set.serving_mode if serving_set else None
            except Exception:
                serving_set = None
            mode = ed.serving_mode or mode
            tools = [t for t in tools_by_dish.get(ed.id, []) if t.get("name")]
            if not tools and not serving_set:
                tools = [{"name": sd.name or (sd.tool.name if getattr(sd, "tool", None) else ""), "quantity": sd.quantity} for sd in dish.serving_dishes]
            vessels = [f"{t['name']} ×{_fmt(t['quantity'])}" for t in tools if t.get("name") and not _is_waiter_cutlery(t["name"])]
            cutlery = [f"{t['name']} ×{_fmt(t['quantity'])}" for t in tools if t.get("name") and _is_waiter_cutlery(t["name"])]
            serving_size = dish.serving_size or 1
            flags = [label for flag, label in ((ed.is_gift, "מתנה"), (ed.is_upgrade, "שדרוג")) if flag]
            rows.append({
                "order": order, "category": f"{sub_meal} – {category}" if sub_meal else category,
                "name": dish.name + (f" ({', '.join(flags)})" if flags else ""),
                "quantity": f"{_fmt(ed.quantity)} יחידות" + (f"\n(יחידה = {_fmt(serving_size)} סועדים)" if serving_size != 1 else ""),
                "mode": {"personal": "אישי", "central": "מרכזי"}.get(mode or "", ""),
                "vessels": "\n".join(vessels), "cutlery": "\n".join(cutlery),
                "instructions": "\n".join(p for p in [dish.serving_description, dish.waiter_notes] if p),
                "addons": "\n".join(addons.get(dish.id, [])),
                "notes": ed.notes or "",
            })
        grouped: "OrderedDict[str, list[dict]]" = OrderedDict()
        for row in sorted(rows, key=lambda r: (r["order"], r["name"])):
            grouped.setdefault(row["category"], []).append(row)
        return grouped

    def _reqs(self, ctx, kind: str, sources: tuple[str, ...] = ()) -> list:
        rows = ctx["summary"].tool_requirements if kind == "tool" else ctx["summary"].product_requirements
        return [r for r in rows if not sources or any(str(_get(r, "source_type") or "").startswith(s) for s in sources)]

    @staticmethod
    def _row(req) -> tuple[str, str, str]:
        return _get(req, "name") or "", _fmt(_get(req, "quantity")), _get(req, "unit") or "יחידות"

    def _spare_rows(self, event: Event, ctx: dict) -> list[tuple[str, str, str]]:
        if ctx["is_sweet"]:
            extra = max(0, (event.guest_count or 0) - ctx["places"])
            rows = [(f"{name} (פשוטים) – לכל מנה מעבר לעריכה", _fmt(extra), "יחידות") for name in ("צלחות", "מזלגות", "כוסות")]
            rows += [("מפיות פשוטות – ספייר", "1", "חבילה"), ("מזלגות – ספייר", "1", "חבילה"),
                     ("סכינים – ספייר", "1", "חבילה"), ("כפות – ספייר", "1", "חבילה")]
            return rows
        return [(f"{name} (פשוטים) – ספייר", "1", "מכל סוג") for name in ("צלחות", "מפיות", "מזלגות", "סכינים", "כוסות")]

    def _waiter_tools(self, event: Event, ctx: dict) -> tuple[list, list]:
        names = " ".join((ed.dish.name if ed.dish else "") for ed in event.dishes).replace("'", "").replace("׳", "")
        per_event = list(PER_EVENT_WAITER_TOOLS)
        if any(token in names for token in ("צולנט", "חמין")):
            per_event.append("כף לצ'ולנט")
        if "מרק" in names:
            per_event.append("מצקת למרק")
        per_waiter = list(PER_WAITER_TOOLS)
        kosher = (ctx["template"].kosher_type if ctx["template"] else "") or ""
        if kosher in ("בשרי", "חלבי"):
            per_waiter.append(f"מגש נירוסטה לחלוקת שניצל/דג (אירוע {kosher})")
        return [(n, "1", "") for n in per_event], [(n, _fmt(ctx["waiters"]), f"1 לכל מלצר × {ctx['waiters']}") for n in per_waiter]

    # ── documents ─────────────────────────────────────────────────────
    def _seating(self, event: Event) -> list:
        sides = [s for s in (event.seating_sides or []) if s.get("side") or s.get("places")]
        if not sides:
            return [B.paragraph("לא הוזנה חלוקת מקומות לפי צד.", "small")]
        return [B.table(["צד", "מקומות", "צורת סידור"], [(s.get("side"), _fmt(s.get("places")), s.get("arrangement")) for s in sides], [5, 3, 8])]

    def serving_instructions_pdf(self, event: Event) -> BytesIO:
        ctx = self._context(event)
        f = B.title("הוראות הגשה ועריכה", event.name)
        f += [B.section("פרטי האירוע והאולם"), B.gap(4), B.info_grid(self._header_pairs(event, ctx)), B.gap()]
        f += [B.section("חלוקת מקומות בכל צד"), B.gap(4), *self._seating(event), B.gap()]
        setting = [B.section("הוראות עריכה"), B.gap(4),
                   B.paragraph(SETTING_SWEET if ctx["is_sweet"] else SETTING_REGULAR),
                   B.paragraph(SETTING_EXTRA, "note"), B.paragraph(SETTING_TABLES, "small"), B.paragraph(CENTRAL_RULE, "small")]
        setting_tools = self._reqs(ctx, "tool", ("table_setting", "event_tool_set"))
        if setting_tools:
            setting.append(B.table(["כלי עריכה", "כמות", "יחידה"], [self._row(r) for r in setting_tools], [9, 3, 3]))
        f += [*setting, B.gap()]
        for category, rows in self.dishes(event, ctx).items():
            f += [B.titled(category, B.table(
                ["מנה והוראות הגשה", "כמות", "הגשה", "כלי הגשה", "סכו\"ם", "תוספות", "הערות"],
                [(B.rtl(r["name"], B.styles()["label"], 140) if not r["instructions"] else
                  [B.rtl(r["name"], B.styles()["label"], 140), B.rtl(r["instructions"], B.styles()["small"], 140)],
                  r["quantity"], r["mode"], r["vessels"], r["cutlery"], r["addons"], r["notes"]) for r in rows],
                [5.2, 1.9, 1.3, 3, 2.4, 2.6, 2.2], small_cols=(1, 5, 6))), B.gap()]
        f += self._accompanying(event, ctx)
        if event.notes:
            f += [B.section("הערות מיוחדות לאירוע"), B.gap(4), B.paragraph(event.notes), B.gap()]
        f.append(B.paragraph("בהצלחה!", "label"))
        return B.build(f, footer_text=f"{event.name} – הוראות הגשה")

    def _accompanying(self, event: Event, ctx: dict) -> list:
        products = [self._row(r) for r in self._reqs(ctx, "product") if not (_get(r, "details") or {}).get("dish_id")]
        cloths = [self._row(r) for r in self._reqs(ctx, "tool", ("tablecloths",))]
        rows = [(n, q, u) for n, q, u in cloths + products]
        if not rows:
            return []
        return [B.titled("מוצרים נלווים לאירוע (מפות, שתייה, לחמניות וכו')", B.table(["פריט", "כמות", "יחידה"], rows, [9, 3, 3])), B.gap()]

    def packing_list_pdf(self, event: Event) -> BytesIO:
        ctx = self._context(event)
        f = B.title("רשימת אריזה", event.name)
        f += [B.info_grid(self._header_pairs(event, ctx)), B.gap()]

        def part(title: str, rows: list, headers=("פריט", "כמות", "יחידה / הערה")):
            if rows:
                f.extend([B.titled(title, B.table(list(headers), rows, [8.5, 3, 4], checkbox=True, checkbox_label="נארז")), B.gap()])

        food = []
        for category, rows in self.dishes(event, ctx).items():
            food += [(r["name"] if category == "מנות נוספות" else f"{r['name']} – {category}", r["quantity"], r["addons"].replace("\n", ", ")) for r in rows]
        part("אוכל", food, ("מנה", "כמות", "תוספות למנה"))
        part("שתייה, לחמניות ומוצרים נלווים",
             [self._row(r) for r in self._reqs(ctx, "product") if not (_get(r, "details") or {}).get("dish_id")])
        cloths = [self._row(r) for r in self._reqs(ctx, "tool", ("tablecloths",))]
        part("מפות (סך הכל לפי מנות ÷ 8 + ספייר; חלוקה למלבן/מרובע לפי הסימון באירוע)", cloths)
        part("כלי עריכה", [self._row(r) for r in self._reqs(ctx, "tool", ("table_setting", "event_tool_set"))])
        part("כלים מרכזיים וכלי הגשה (לפי המנות שנבחרו)", [self._row(r) for r in self._reqs(ctx, "tool", ("serving", "tray_packaging"))])
        part("ספייר – אריזה פשוטה", self._spare_rows(event, ctx))
        per_event, per_waiter = self._waiter_tools(event, ctx)
        part("כלי מלצר – 1 לאירוע", per_event)
        part("כלי מלצר – לכל מלצר", per_waiter)
        part("תוספות", [(n, "", "") for n in EXTRAS])
        part("פריטים שהוספו ידנית", [self._row(r) for r in self._reqs(ctx, "tool", ("manual",))])
        boxes = [(b.box_type, _fmt(b.quantity), b.notes or "") for b in event.boxes]
        part("קרטונים", boxes)
        return B.build(f, footer_text=f"{event.name} – רשימת אריזה")

    def delivery_sheet_pdf(self, event: Event) -> BytesIO:
        ctx = self._context(event)
        f = B.title("דף הוראות למוביל – הלוך", event.name)
        f += [B.section("פרטי האירוע ואנשי קשר"), B.gap(4), B.info_grid(self._header_pairs(event, ctx, driver=True)), B.gap()]
        f += [B.section("גישה ופריקה"), B.gap(4), B.info_grid([
            ("חניה קרובה", _yes(event.has_nearby_parking)), ("כניסה אחורית", _yes(event.has_back_entrance)),
            ("דרוש עגלות", _yes(event.requires_carts)), ("מעלית", _yes(event.has_elevator)),
            ("הערות גישה", event.access_notes), ("מיקום פריקה והנחת ציוד", event.equipment_dropoff_location),
        ]), B.gap()]
        boxes = [(b.box_type, _fmt(b.quantity), b.notes or "", "") for b in event.boxes]
        total = sum(b.quantity or 0 for b in event.boxes)
        f += [B.section(f"קרטונים – סה\"כ במערכת: {total}"), B.gap(3)]
        if boxes:
            f.append(B.table(["סוג ארגז", "כמות במערכת", "הערה", "נספר בפועל"], boxes, [5, 3, 5, 3]))
        f += [B.paragraph("סה\"כ ארגזים שנספרו בפועל: ____________"), B.gap()]
        notes = [link.template.note for link in self.db.query(EventDeliveryNote).filter(EventDeliveryNote.event_id == event.id) if link.template]
        special = [label for flag, label in (
            (getattr(event, "check_refrigerator", False), "לבדוק מקרר"), (getattr(event, "check_freezer", False), "לבדוק מקפיא"), (getattr(event, "check_hot_plate", False), "לבדוק פלטה"),
            (getattr(event, "connect_gas", False), "לחבר גז"), (getattr(event, "put_in_refrigerator", False), "להכניס למקרר"), (getattr(event, "put_in_freezer", False), "להכניס למקפיא"),
            (getattr(event, "put_on_hot_plate", False), "להניח על הפלטה"), (getattr(event, "count_boxes", False), "לספור ארגזים"), (getattr(event, "check_drinks", False), "לבדוק שתייה"),
            (getattr(event, "check_rolls", False), "לבדוק לחמניות")) if flag]
        extra_texts = [t for t in (getattr(event, "delivery_contents_notes", None), getattr(event, "last_minute_items", None), getattr(event, "delivery_special_notes", None)) if t]
        f += [B.block(B.section("בדיקה לפני היציאה מהמטבח"), B.gap(3), B.checklist(BEFORE_LEAVING)), B.gap()]
        f += [B.block(B.section("בדיקה בהגעה למקום האירוע"), B.gap(3), B.checklist(ON_ARRIVAL)), B.gap()]
        if special or notes:
            f += [B.block(B.section("בדיקות מיוחדות לאירוע הזה"), B.gap(3), B.checklist(special + notes)), B.gap()]
        if extra_texts:
            f += [B.section("הערות למשלוח"), B.gap(3), *[B.paragraph(t) for t in extra_texts], B.gap()]
        f += [B.section("הוראות הובלה"), B.gap(4)]
        for stage, lines in STAGES:
            f += [B.block(B.paragraph(stage, "label"), *B.numbered(lines)), B.gap(4)]
            if stage.startswith("שלב 4"):
                f += [B.paragraph(AESTHETICS, "note"), B.gap(4)]
        f += [B.section("אישור מסירה"), B.gap(4), B.paragraph("שם המאשר במקום: ____________________   שעת מסירה: __________"),
              B.paragraph("המוביל הודיע לבעלי הקייטרינג שהמשלוח נמסר: כן / לא")]
        return B.build(f, footer_text=f"{event.name} – מוביל הלוך")

    def return_sheet_pdf(self, event: Event) -> BytesIO:
        ctx = self._context(event)
        f = B.title("דף למוביל – חזור", event.name)
        f += [B.info_grid(self._header_pairs(event, ctx, driver=True)[:9]), B.gap()]
        reusable = [self._row(r) for r in self._reqs(ctx, "tool")
                    if _get(r, "is_reusable")]
        per_event, per_waiter = self._waiter_tools(event, ctx)
        rows = [(n, q, u, "") for n, q, u in reusable + per_event + per_waiter]
        rows += [(name, "", "", "") for name in RETURN_FIXED]
        f += [B.section("פריטים שאמורים לחזור לקייטרינג"), B.gap(3),
              B.table(["פריט", "יצא", "יחידה", "חזר בפועל"], rows, [8, 2, 3, 3]), B.gap()]
        f += [B.block(B.section("הוראות למוביל חזור"), B.gap(3), B.checklist(RETURN_INSTRUCTIONS)), B.gap()]
        f += [B.paragraph("חסר / הערות: ______________________________________________"),
              B.paragraph("שם המוביל: ________________   שעת החזרה: __________")]
        return B.build(f, footer_text=f"{event.name} – מוביל חזור")
