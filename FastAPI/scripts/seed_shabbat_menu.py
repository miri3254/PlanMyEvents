"""
Seed script — Shabbat catering menu
Inserts: Products, Tools (serving dishes), Dishes, DishIngredients,
         ServingDish, MenuTemplate, MenuSubMeals, MenuCategories, DishMenuMappings.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy.orm import Session
from app.db.engine import engine
from app.db.base import Base, BaseModel
from app.db.session import SessionLocal

# ── Models ───────────────────────────────────────────────────────────
from app.models.product import Product
from app.models.tool import Tool
from app.models.dish import Dish, DishIngredient, DishEquipment, ServingDish
from app.models.menu import MenuTemplate, MenuSubMeal, MenuCategory, DishMenuMapping
from app.core.enums import (
    KosherType, UnitType, ProductCategory,
    MenuType, ToolCategory, ToolSubCategory,
)

# ── Ensure tables exist ─────────────────────────────────────────────
Base.metadata.create_all(bind=engine)


# =====================================================================
#  HELPER
# =====================================================================
_product_cache: dict[str, Product] = {}
_tool_cache: dict[str, Tool] = {}


def get_or_create_product(
    db: Session, name: str, category: ProductCategory,
    unit: UnitType = UnitType.KG, kosher: KosherType = KosherType.PARVE,
    notes: str = ""
) -> Product:
    if name in _product_cache:
        return _product_cache[name]
    p = Product(
        name=name, category=category, unit=unit,
        kosher_type=kosher, quantity_in_stock=0, min_stock_level=1,
        notes=notes,
    )
    db.add(p)
    db.flush()
    _product_cache[name] = p
    return p


def get_or_create_tool(
    db: Session, name: str,
    cat: ToolCategory = ToolCategory.SERVING,
    sub: ToolSubCategory = ToolSubCategory.REAL,
    qty: int = 20, desc: str = "",
) -> Tool:
    if name in _tool_cache:
        return _tool_cache[name]
    t = Tool(
        name=name, category=cat, sub_category=sub,
        quantity_in_stock=qty, min_stock_level=5,
        description=desc,
    )
    db.add(t)
    db.flush()
    _tool_cache[name] = t
    return t


def make_dish(
    db: Session, name: str, desc: str, kosher: KosherType,
    waiter_notes: str = "", serving_desc: str = "",
) -> Dish:
    d = Dish(
        name=name, description=desc, kosher_type=kosher,
        waiter_notes=waiter_notes, serving_description=serving_desc,
        is_active=True, serving_size=1.0,
    )
    db.add(d)
    db.flush()
    return d


def link_ingredient(
    db: Session, dish: Dish, product: Product,
    qty: float, unit: UnitType,
) -> DishIngredient:
    di = DishIngredient(
        dish_id=dish.id, product_id=product.id,
        name=product.name, quantity=qty, unit=unit,
    )
    db.add(di)
    return di


def link_serving(db: Session, dish: Dish, tool: Tool, qty: int = 1) -> ServingDish:
    sd = ServingDish(dish_id=dish.id, tool_id=tool.id, name=tool.name, quantity=qty)
    db.add(sd)
    return sd


# =====================================================================
#  MAIN SEED
# =====================================================================
def seed(db: Session):

    # ─────────────────────────────────────────────────────────────────
    #  1. PRODUCTS  (extracted from dish names)
    # ─────────────────────────────────────────────────────────────────
    print("📦 יוצר מוצרים...")

    # ── ירקות ────────────────────────────────────────────────────────
    VEG = ProductCategory.DRY          # closest available category
    p_gezer      = get_or_create_product(db, "גזר",               VEG, UnitType.KG,   notes="גזר טרי - לסלטים")
    p_seleri     = get_or_create_product(db, "סלרי",              VEG, UnitType.KG,   notes="סלרי טרי")
    p_pilpel     = get_or_create_product(db, "פלפל צבעוני",       VEG, UnitType.KG,   notes="פלפלים בצבעים")
    p_tiras      = get_or_create_product(db, "תירס גמדי",         VEG, UnitType.UNIT, notes="תירס גמדי שלם")
    p_nivatim    = get_or_create_product(db, "נבטים",             VEG, UnitType.KG,   notes="נבטי שעועית / חומוס")
    p_shamir     = get_or_create_product(db, "שמיר",              VEG, UnitType.BUNDLE,notes="חבילת שמיר טרי")
    p_shum       = get_or_create_product(db, "שום",               VEG, UnitType.KG,   notes="ראשי שום")
    p_pilpel_h   = get_or_create_product(db, "פלפל חריף",         VEG, UnitType.KG,   notes="פלפל חריף אדום/ירוק")
    p_alim       = get_or_create_product(db, "עלים ירוקים",       VEG, UnitType.BUNDLE,notes="תערובת עלים ירוקים")
    p_limon      = get_or_create_product(db, "לימון",             VEG, UnitType.KG,   notes="לימון טרי")
    p_batzal_y   = get_or_create_product(db, "בצל ירוק",          VEG, UnitType.BUNDLE,notes="חבילת בצל ירוק")
    p_hasa       = get_or_create_product(db, "חסה",               VEG, UnitType.UNIT, notes="ראש חסה")
    p_pitriyot   = get_or_create_product(db, "פטריות שמפיניון",   VEG, UnitType.KG,   notes="פטריות לבנות טריות")
    p_sherry     = get_or_create_product(db, "עגבניות שרי",       VEG, UnitType.KG,   notes="עגבניות שרי")
    p_batzal_s   = get_or_create_product(db, "בצל סגול",          VEG, UnitType.KG,   notes="בצל סגול")
    p_tapuah     = get_or_create_product(db, "תפוח",              VEG, UnitType.KG,   notes="תפוח ירוק / אדום")
    p_ananas     = get_or_create_product(db, "אננס",              VEG, UnitType.UNIT, notes="אננס טרי או משומר")
    p_yerakot    = get_or_create_product(db, "ירקות מעורב",       VEG, UnitType.KG,   notes="תערובת ירקות למרק")
    p_tapuadama  = get_or_create_product(db, "תפוחי אדמה",       VEG, UnitType.KG,   notes="תפו\"א")

    # ── פירות יבשים / אגוזים / יבשים ────────────────────────────────
    DRY = ProductCategory.DRY
    p_hamuziot   = get_or_create_product(db, "חמוציות",           DRY, UnitType.KG,   notes="חמוציות מיובשות")
    p_pecan      = get_or_create_product(db, "פקאן",              DRY, UnitType.KG,   notes="אגוזי פקאן")
    p_egozim     = get_or_create_product(db, "אגוזי מלך",         DRY, UnitType.KG,   notes="אגוזי מלך קלויים")
    p_shkedim    = get_or_create_product(db, "שקדים",             DRY, UnitType.KG,   notes="שקדים פרוסים")
    p_sumsum     = get_or_create_product(db, "שומשום",            DRY, UnitType.KG,   notes="שומשום לבן / שחור")
    p_pirurim    = get_or_create_product(db, "פירורי לחם",        DRY, UnitType.KG,   notes="פירורי לחם לציפוי")
    p_atriyot    = get_or_create_product(db, "אטריות",            DRY, UnitType.KG,   notes="אטריות ביצה דקות")
    p_shkedmarak = get_or_create_product(db, "שקדי מרק",          DRY, UnitType.KG,   notes="שקדי מרק קריספי")
    p_orez       = get_or_create_product(db, "אורז",              DRY, UnitType.KG,   notes="אורז בסמטי / לבן")
    p_shokolad   = get_or_create_product(db, "שוקולד",            DRY, UnitType.KG,   notes="שוקולד מריר / חלב")
    p_ukhmaniyot = get_or_create_product(db, "אוכמניות",          DRY, UnitType.KG,   notes="אוכמניות קפואות / טריות")
    p_kneidlach  = get_or_create_product(db, "קנידעלך",           DRY, UnitType.UNIT, notes="כדורי קנידעלך מוכנים / תערובת")
    p_grisim     = get_or_create_product(db, "גריסים",            DRY, UnitType.KG,   notes="גריסי פנינה")
    p_manchess   = get_or_create_product(db, "מנצ'ס",             DRY, UnitType.KG,   notes="חטיף מנצ'ס פיקנטי")
    p_peirot     = get_or_create_product(db, "פירות מעורב",       DRY, UnitType.KG,   notes="תערובת פירות עונתיים")

    # ── קטניות ───────────────────────────────────────────────────────
    LEG = ProductCategory.LEGUMES
    p_shuit      = get_or_create_product(db, "שעועית",            LEG, UnitType.KG,   notes="שעועית לבנה יבשה")

    # ── נוזלים / רטבים ───────────────────────────────────────────────
    LIQ = ProductCategory.LIQUIDS
    p_pesto      = get_or_create_product(db, "רוטב פסטו",         LIQ, UnitType.ML,   notes="פסטו בזיליקום")
    p_chili      = get_or_create_product(db, "צ'ילי",             LIQ, UnitType.ML,   notes="רוטב צ'ילי מתוק")
    p_dvash      = get_or_create_product(db, "דבש",               LIQ, UnitType.KG,   notes="דבש טהור")
    p_hardal     = get_or_create_product(db, "חרדל",              LIQ, UnitType.ML,   notes="חרדל דיז'ון")
    p_teriyaki   = get_or_create_product(db, "רוטב טריאקי",       LIQ, UnitType.ML,   notes="רוטב טריאקי יפני")
    p_isbeitivul = get_or_create_product(db, "עשבי תיבול",        LIQ, UnitType.BUNDLE,notes="תערובת עשבי תיבול טריים")

    # ── דגים ─────────────────────────────────────────────────────────
    FISH = ProductCategory.FROZEN
    p_salmon     = get_or_create_product(db, "סלמון",             FISH, UnitType.KG,  notes="פילה סלמון טרי / קפוא")
    p_musht      = get_or_create_product(db, "מושט",              FISH, UnitType.KG,  notes="דג מושט שלם")
    p_tuna       = get_or_create_product(db, "טונה",              FISH, UnitType.KG,  notes="פילה טונה")

    # ── בשר ──────────────────────────────────────────────────────────
    MEAT = ProductCategory.MEAT
    p_bakar      = get_or_create_product(db, "בשר בקר",           MEAT, UnitType.KG,  KosherType.MEAT, notes="בקר לרולדות / צ'ולנט")
    p_hodoo      = get_or_create_product(db, "הודו",              MEAT, UnitType.KG,  KosherType.MEAT, notes="חזה / שוק הודו")
    p_pargit     = get_or_create_product(db, "פרגית",             MEAT, UnitType.KG,  KosherType.MEAT, notes="פרגיות עוף")
    p_of         = get_or_create_product(db, "עוף",               MEAT, UnitType.KG,  KosherType.MEAT, notes="חלקי עוף")
    p_kaved      = get_or_create_product(db, "כבד",               MEAT, UnitType.KG,  KosherType.MEAT, notes="כבד עוף")
    p_beitzim    = get_or_create_product(db, "ביצים",             MEAT, UnitType.UNIT, KosherType.PARVE, notes="ביצים גדולות")
    p_pastrama   = get_or_create_product(db, "פסטרמה",            MEAT, UnitType.KG,  KosherType.MEAT, notes="פסטרמה ביתית")
    p_shnitzel   = get_or_create_product(db, "שניצל עוף",         MEAT, UnitType.KG,  KosherType.MEAT, notes="שניצלים / שניצלונים")

    # ── חלבי ─────────────────────────────────────────────────────────
    DAIRY = ProductCategory.DAIRY
    p_katzefet   = get_or_create_product(db, "קצפת",              DAIRY, UnitType.ML, KosherType.DAIRY, notes="קצפת מתוקה להקצפה")

    db.flush()
    print(f"   ✔ {len(_product_cache)} מוצרים נוצרו")

    # ─────────────────────────────────────────────────────────────────
    #  2. TOOLS  (serving vessels)
    # ─────────────────────────────────────────────────────────────────
    print("🍽️  יוצר כלי הגשה...")

    SRV = ToolCategory.SERVING
    PLT = ToolCategory.PLATES
    CUP = ToolCategory.CUPS
    REAL = ToolSubCategory.REAL
    DISP = ToolSubCategory.DISPOSABLE

    t_salad_bowl   = get_or_create_tool(db, "קערת סלט עגולה",          SRV, REAL, 30, "קערת זכוכית עגולה בינונית לסלטים")
    t_salad_long   = get_or_create_tool(db, "קערת סלט מלבנית",        SRV, REAL, 20, "קערה מלבנית לסלטים מוארכים")
    t_fish_plate   = get_or_create_tool(db, "מגש דג מלבני",           SRV, REAL, 15, "מגש קרמיקה מלבני לדגים")
    t_fish_round   = get_or_create_tool(db, "צלחת הגשה עגולה גדולה",  SRV, REAL, 15, "צלחת פורצלן עגולה להגשת דגים")
    t_soup_tureen  = get_or_create_tool(db, "סיר מרק עם מכסה",        SRV, REAL, 10, "סיר הגשה למרק עם מצקת")
    t_soup_bowl    = get_or_create_tool(db, "קערת מרק אישית",         PLT, REAL, 100,"קערת מרק עמוקה")
    t_main_platter = get_or_create_tool(db, "מגש הגשה גדול",          SRV, REAL, 20, "מגש נירוסטה גדול למנות עיקריות")
    t_warmer       = get_or_create_tool(db, "כלי חימום (ווֹרמר)",      SRV, REAL, 8,  "ווֹרמר עם נרות חימום")
    t_side_bowl    = get_or_create_tool(db, "קערת תוספות עמוקה",       SRV, REAL, 25, "קערת הגשה עמוקה לאורז / קוגל")
    t_dessert_cup  = get_or_create_tool(db, "כוסית קינוח",            CUP, DISP, 200,"כוסית שקופה למוס")
    t_cholent_pot  = get_or_create_tool(db, "סיר צ'ולנט גדול",        SRV, REAL, 6,  "סיר הגשה עמוק לצ'ולנט")
    t_egg_plate    = get_or_create_tool(db, "מגש ביצים וכבד",         SRV, REAL, 10, "מגש הגשה שטוח לביצים וכבד")
    t_pastry_tray  = get_or_create_tool(db, "מגש מאפים",              SRV, REAL, 15, "מגש עגול למאפים ופשטידות")

    db.flush()
    print(f"   ✔ {len(_tool_cache)} כלי הגשה נוצרו")

    # ─────────────────────────────────────────────────────────────────
    #  3. DISHES  + ingredients + serving dishes
    # ─────────────────────────────────────────────────────────────────
    print("🥗 יוצר מנות...")

    # ═══════════════════════  S A L A D S  ═══════════════════════════
    salad_dishes = []

    # --- 1 ---
    d = make_dish(db, "רצועות גזר בתיבול פיקנטי ומנצ'ס",
        "רצועות גזר חתוכות דק בתיבול פיקנטי עם מנצ'ס קריספי",
        KosherType.PARVE,
        waiter_notes="להגיש בקערה עגולה, לפזר מנצ'ס רק לפני ההגשה",
        serving_desc="קערת סלט אחת ל-10 אורחים")
    link_ingredient(db, d, p_gezer, 2.0, UnitType.KG)
    link_ingredient(db, d, p_manchess, 0.3, UnitType.KG)
    link_serving(db, d, t_salad_bowl, 1)
    salad_dishes.append(d)

    # --- 2 ---
    d = make_dish(db, "רצועות גזר, סלרי ופלפל בצבעים - ברוטב מתקתק",
        "רצועות גזר וסלרי עם פלפלים צבעוניים ברוטב מתקתק",
        KosherType.PARVE,
        waiter_notes="לערבב היטב לפני ההגשה, הרוטב שוקע",
        serving_desc="קערת סלט מלבנית, 1 ל-10 אורחים")
    link_ingredient(db, d, p_gezer, 1.5, UnitType.KG)
    link_ingredient(db, d, p_seleri, 0.5, UnitType.KG)
    link_ingredient(db, d, p_pilpel, 1.0, UnitType.KG)
    link_serving(db, d, t_salad_long, 1)
    salad_dishes.append(d)

    # --- 3 ---
    d = make_dish(db, "גזר, תירס גמדי, נבטים - בתיבול מעודן",
        "סלט גזר עם תירס גמדי ונבטים בתיבול קל ומעודן",
        KosherType.PARVE,
        waiter_notes="להגיש צונן, לקשט בעלי כוסברה",
        serving_desc="קערת סלט עגולה, 1 ל-10 אורחים")
    link_ingredient(db, d, p_gezer, 1.5, UnitType.KG)
    link_ingredient(db, d, p_tiras, 10.0, UnitType.UNIT)
    link_ingredient(db, d, p_nivatim, 0.3, UnitType.KG)
    link_serving(db, d, t_salad_bowl, 1)
    salad_dishes.append(d)

    # --- 4 ---
    d = make_dish(db, "גזר פיקנטי בשמיר ושום",
        "גזר מגורר בתיבול פיקנטי עם שמיר טרי ושום",
        KosherType.PARVE,
        waiter_notes="להגיש בקערה קטנה, הטעם מתחזק עם הזמן",
        serving_desc="קערת סלט עגולה, 1 ל-10 אורחים")
    link_ingredient(db, d, p_gezer, 2.0, UnitType.KG)
    link_ingredient(db, d, p_shamir, 2.0, UnitType.BUNDLE)
    link_ingredient(db, d, p_shum, 0.1, UnitType.KG)
    link_serving(db, d, t_salad_bowl, 1)
    salad_dishes.append(d)

    # --- 5 ---
    d = make_dish(db, "גזר, פלפל חריף, עלים ירוקים - בלימון ושום",
        "סלט גזר חריף עם פלפל חריף, עלים ירוקים, לימון ושום",
        KosherType.PARVE,
        waiter_notes="סלט חריף! לסמן בשלט. לסחוט לימון טרי לפני הגשה",
        serving_desc="קערת סלט מלבנית, 1 ל-10 אורחים")
    link_ingredient(db, d, p_gezer, 1.5, UnitType.KG)
    link_ingredient(db, d, p_pilpel_h, 0.3, UnitType.KG)
    link_ingredient(db, d, p_alim, 1.0, UnitType.BUNDLE)
    link_ingredient(db, d, p_limon, 0.5, UnitType.KG)
    link_ingredient(db, d, p_shum, 0.1, UnitType.KG)
    link_serving(db, d, t_salad_long, 1)
    salad_dishes.append(d)

    # --- 6 ---
    d = make_dish(db, "גזר ובצל ירוק - בתיבול מעודן חמוציות ופקאנים",
        "סלט גזר עם בצל ירוק, חמוציות מיובשות ופקאנים קלויים",
        KosherType.PARVE,
        waiter_notes="לפזר פקאנים רק לפני ההגשה כדי לשמור על קריספיות",
        serving_desc="קערת סלט עגולה, 1 ל-10 אורחים")
    link_ingredient(db, d, p_gezer, 1.5, UnitType.KG)
    link_ingredient(db, d, p_batzal_y, 2.0, UnitType.BUNDLE)
    link_ingredient(db, d, p_hamuziot, 0.2, UnitType.KG)
    link_ingredient(db, d, p_pecan, 0.2, UnitType.KG)
    link_serving(db, d, t_salad_bowl, 1)
    salad_dishes.append(d)

    # --- 7 ---
    d = make_dish(db, "וולדורף - תפוח, אננס, סלרי, אגוזי מלך - בקצפת מתוקה",
        "סלט וולדורף קלאסי עם תפוח, אננס, סלרי ואגוזי מלך בקצפת",
        KosherType.DAIRY,
        waiter_notes="חלבי! להגיש מקורר. לערבב קצפת רק ברגע האחרון",
        serving_desc="קערת סלט עגולה, 1 ל-10 אורחים")
    link_ingredient(db, d, p_tapuah, 1.0, UnitType.KG)
    link_ingredient(db, d, p_ananas, 1.0, UnitType.UNIT)
    link_ingredient(db, d, p_seleri, 0.5, UnitType.KG)
    link_ingredient(db, d, p_egozim, 0.2, UnitType.KG)
    link_ingredient(db, d, p_katzefet, 300.0, UnitType.ML)
    link_serving(db, d, t_salad_bowl, 1)
    salad_dishes.append(d)

    # --- 8 ---
    d = make_dish(db, "חסה, נבטים, פטריות שמפיניון - ברוטב הדרים ושקדים",
        "סלט חסה ירוקה עם נבטים, פטריות שמפיניון פרוסות, רוטב הדרים ושקדים",
        KosherType.PARVE,
        waiter_notes="לפזר שקדים פרוסים למעלה. רוטב בצד",
        serving_desc="קערת סלט מלבנית, 1 ל-10 אורחים")
    link_ingredient(db, d, p_hasa, 3.0, UnitType.UNIT)
    link_ingredient(db, d, p_nivatim, 0.3, UnitType.KG)
    link_ingredient(db, d, p_pitriyot, 0.5, UnitType.KG)
    link_ingredient(db, d, p_shkedim, 0.15, UnitType.KG)
    link_ingredient(db, d, p_limon, 0.3, UnitType.KG)
    link_serving(db, d, t_salad_long, 1)
    salad_dishes.append(d)

    # --- 9 ---
    d = make_dish(db, "חסה, שרי, נבטים, בצל סגול - במתבל ונשנושים",
        "סלט חסה עם עגבניות שרי, נבטים ובצל סגול במתבל ונשנושים",
        KosherType.PARVE,
        waiter_notes="להוסיף שקיקי נשנושים מעל לפני ההגשה",
        serving_desc="קערת סלט עגולה, 1 ל-10 אורחים")
    link_ingredient(db, d, p_hasa, 3.0, UnitType.UNIT)
    link_ingredient(db, d, p_sherry, 0.5, UnitType.KG)
    link_ingredient(db, d, p_nivatim, 0.2, UnitType.KG)
    link_ingredient(db, d, p_batzal_s, 0.3, UnitType.KG)
    link_serving(db, d, t_salad_bowl, 1)
    salad_dishes.append(d)

    # --- 10 ---
    d = make_dish(db, "חסה ופירות בסגנון מתקתק בקישוט פקאן",
        "סלט חסה עם פירות עונתיים בסגנון מתקתק, מקושט בפקאן קלוי",
        KosherType.PARVE,
        waiter_notes="להגיש מקורר, עם רוטב בצד. פקאן מלמעלה",
        serving_desc="קערת סלט מלבנית, 1 ל-10 אורחים")
    link_ingredient(db, d, p_hasa, 3.0, UnitType.UNIT)
    link_ingredient(db, d, p_peirot, 1.0, UnitType.KG)
    link_ingredient(db, d, p_pecan, 0.15, UnitType.KG)
    link_serving(db, d, t_salad_long, 1)
    salad_dishes.append(d)

    # ═══════════════════════  F I S H  ═══════════════════════════════
    fish_dishes = []

    d = make_dish(db, "סלמון ברוטב פסטו",
        "פילה סלמון אפוי ברוטב פסטו בזיליקום ביתי",
        KosherType.PARVE,
        waiter_notes="להגיש חם על מגש מלבני. רוטב פסטו בצד",
        serving_desc="מגש דג מלבני, חצי כמות מנות")
    link_ingredient(db, d, p_salmon, 3.0, UnitType.KG)
    link_ingredient(db, d, p_pesto, 200.0, UnitType.ML)
    link_serving(db, d, t_fish_plate, 1)
    fish_dishes.append(d)

    d = make_dish(db, "סלמון בשומשום וצ'ילי",
        "פילה סלמון בציפוי שומשום עם רוטב צ'ילי מתוק",
        KosherType.PARVE,
        waiter_notes="להגיש חם. שומשום צריך להיות קריספי",
        serving_desc="מגש דג מלבני, חצי כמות מנות")
    link_ingredient(db, d, p_salmon, 3.0, UnitType.KG)
    link_ingredient(db, d, p_sumsum, 0.2, UnitType.KG)
    link_ingredient(db, d, p_chili, 100.0, UnitType.ML)
    link_serving(db, d, t_fish_plate, 1)
    fish_dishes.append(d)

    d = make_dish(db, "סלמון בדבש וחרדל",
        "פילה סלמון אפוי בגלייז דבש וחרדל דיז'ון",
        KosherType.PARVE,
        waiter_notes="להגיש חם, לוודא שהגלייז נוצץ",
        serving_desc="צלחת הגשה עגולה")
    link_ingredient(db, d, p_salmon, 3.0, UnitType.KG)
    link_ingredient(db, d, p_dvash, 0.2, UnitType.KG)
    link_ingredient(db, d, p_hardal, 100.0, UnitType.ML)
    link_serving(db, d, t_fish_round, 1)
    fish_dishes.append(d)

    d = make_dish(db, "סלמון בעשבי תיבול",
        "פילה סלמון אפוי עם עשבי תיבול טריים",
        KosherType.PARVE,
        waiter_notes="לקשט בעלי עשבי תיבול טריים",
        serving_desc="צלחת הגשה עגולה")
    link_ingredient(db, d, p_salmon, 3.0, UnitType.KG)
    link_ingredient(db, d, p_isbeitivul, 3.0, UnitType.BUNDLE)
    link_serving(db, d, t_fish_round, 1)
    fish_dishes.append(d)

    d = make_dish(db, "סלמון בטריאקי ושומשום",
        "פילה סלמון ברוטב טריאקי יפני עם שומשום",
        KosherType.PARVE,
        waiter_notes="להגיש חם, לפזר שומשום שחור מעל",
        serving_desc="מגש דג מלבני")
    link_ingredient(db, d, p_salmon, 3.0, UnitType.KG)
    link_ingredient(db, d, p_teriyaki, 150.0, UnitType.ML)
    link_ingredient(db, d, p_sumsum, 0.15, UnitType.KG)
    link_serving(db, d, t_fish_plate, 1)
    fish_dishes.append(d)

    d = make_dish(db, "מושט בטעם פיקנטי",
        "דג מושט שלם בתיבול פיקנטי חריף-מתוק",
        KosherType.PARVE,
        waiter_notes="להגיש שלם על מגש. לציין שהדג שלם עם עצמות",
        serving_desc="מגש דג מלבני, חצי כמות מנות")
    link_ingredient(db, d, p_musht, 3.0, UnitType.KG)
    link_serving(db, d, t_fish_plate, 1)
    fish_dishes.append(d)

    d = make_dish(db, "מושט מתוק",
        "דג מושט שלם ברוטב מתוק עדין",
        KosherType.PARVE,
        waiter_notes="להגיש שלם. רוטב מתוק בצד",
        serving_desc="מגש דג מלבני, חצי כמות מנות")
    link_ingredient(db, d, p_musht, 3.0, UnitType.KG)
    link_ingredient(db, d, p_dvash, 0.1, UnitType.KG)
    link_serving(db, d, t_fish_plate, 1)
    fish_dishes.append(d)

    d = make_dish(db, "מושט בציפוי פירורים",
        "דג מושט בציפוי פירורי לחם קריספי",
        KosherType.PARVE,
        waiter_notes="להגיש חם מיד. הציפוי מאבד קריספיות",
        serving_desc="מגש דג מלבני")
    link_ingredient(db, d, p_musht, 3.0, UnitType.KG)
    link_ingredient(db, d, p_pirurim, 0.5, UnitType.KG)
    link_serving(db, d, t_fish_plate, 1)
    fish_dishes.append(d)

    # ═══════════════════════  S O U P  ═══════════════════════════════
    soup_dishes = []

    d = make_dish(db, "מרק עוף וירקות עשיר + קנידעלך + אטריות + שקדי מרק",
        "מרק עוף עשיר בירקות עם קנידעלך, אטריות ביצה ושקדי מרק",
        KosherType.MEAT,
        waiter_notes="להגיש רותח בסיר עם מצקת. קנידעלך ואטריות בתוך המרק, שקדי מרק בצד בקערה נפרדת",
        serving_desc="סיר מרק + קערות אישיות")
    link_ingredient(db, d, p_of, 2.0, UnitType.KG)
    link_ingredient(db, d, p_yerakot, 2.0, UnitType.KG)
    link_ingredient(db, d, p_kneidlach, 50.0, UnitType.UNIT)
    link_ingredient(db, d, p_atriyot, 0.5, UnitType.KG)
    link_ingredient(db, d, p_shkedmarak, 0.3, UnitType.KG)
    link_serving(db, d, t_soup_tureen, 1)
    link_serving(db, d, t_soup_bowl, 10)
    soup_dishes.append(d)

    # ═══════════════════════  M A I N S  ═════════════════════════════
    main_dishes = []

    d = make_dish(db, "רולדת בקר",
        "רולדת בשר בקר ממולאת ואפויה, פרוסה לפרוסות",
        KosherType.MEAT,
        waiter_notes="להגיש פרוסה על מגש חם עם ווֹרמר. לקשט בעלי רוזמרין",
        serving_desc="מגש הגשה גדול + ווֹרמר")
    link_ingredient(db, d, p_bakar, 4.0, UnitType.KG)
    link_serving(db, d, t_main_platter, 1)
    link_serving(db, d, t_warmer, 1)
    main_dishes.append(d)

    d = make_dish(db, "רולדת הודו",
        "רולדת חזה הודו ממולאת ואפויה, פרוסה לפרוסות",
        KosherType.MEAT,
        waiter_notes="להגיש פרוסה על מגש חם. לקשט בקישוטי ירק",
        serving_desc="מגש הגשה גדול + ווֹרמר")
    link_ingredient(db, d, p_hodoo, 4.0, UnitType.KG)
    link_serving(db, d, t_main_platter, 1)
    link_serving(db, d, t_warmer, 1)
    main_dishes.append(d)

    d = make_dish(db, "פרגית",
        "פרגיות עוף עסיסיות בתיבול מיוחד, אפויות בתנור",
        KosherType.MEAT,
        waiter_notes="להגיש חם על מגש. לוודא שהפרגיות שלמות ולא יבשות",
        serving_desc="מגש הגשה גדול + ווֹרמר")
    link_ingredient(db, d, p_pargit, 5.0, UnitType.KG)
    link_serving(db, d, t_main_platter, 1)
    link_serving(db, d, t_warmer, 1)
    main_dishes.append(d)

    d = make_dish(db, "עוף בסגנון מתוק",
        "חלקי עוף אפויים בסגנון מתוק עם רוטב דבש",
        KosherType.MEAT,
        waiter_notes="להגיש חם. הרוטב ניגר - להניח מגש תחתון",
        serving_desc="מגש הגשה גדול + ווֹרמר")
    link_ingredient(db, d, p_of, 5.0, UnitType.KG)
    link_ingredient(db, d, p_dvash, 0.3, UnitType.KG)
    link_serving(db, d, t_main_platter, 1)
    link_serving(db, d, t_warmer, 1)
    main_dishes.append(d)

    d = make_dish(db, "עוף ברביקיו",
        "חלקי עוף ברוטב ברביקיו עשיר, אפויים בתנור",
        KosherType.MEAT,
        waiter_notes="להגיש חם על מגש גדול עם ווֹרמר",
        serving_desc="מגש הגשה גדול + ווֹרמר")
    link_ingredient(db, d, p_of, 5.0, UnitType.KG)
    link_serving(db, d, t_main_platter, 1)
    link_serving(db, d, t_warmer, 1)
    main_dishes.append(d)

    # ═══════════════════════  S I D E S  ═════════════════════════════
    side_dishes = []

    d = make_dish(db, "קניש ירקות",
        "קניש ביתי ממולא ירקות אפויים",
        KosherType.PARVE,
        waiter_notes="להגיש חם על מגש. 1-2 יחידות לאורח",
        serving_desc="מגש מאפים")
    link_ingredient(db, d, p_yerakot, 2.0, UnitType.KG)
    link_ingredient(db, d, p_tapuadama, 1.0, UnitType.KG)
    link_serving(db, d, t_pastry_tray, 1)
    side_dishes.append(d)

    d = make_dish(db, 'קוגל תפו"א',
        "קוגל תפוחי אדמה קלאסי אפוי בתנור עד להזהבה",
        KosherType.PARVE,
        waiter_notes="להגיש חם. לחתוך ריבועים לפני הגשה",
        serving_desc="קערת תוספות עמוקה")
    link_ingredient(db, d, p_tapuadama, 3.0, UnitType.KG)
    link_ingredient(db, d, p_beitzim, 6.0, UnitType.UNIT)
    link_serving(db, d, t_side_bowl, 1)
    side_dishes.append(d)

    d = make_dish(db, "אורז בתוספת שקדים וחמוציות",
        "אורז בסמטי עם שקדים פרוסים וחמוציות מיובשות",
        KosherType.PARVE,
        waiter_notes="לנפנף לפני הגשה. שקדים וחמוציות צריכים להיות נראים למעלה",
        serving_desc="קערת תוספות עמוקה")
    link_ingredient(db, d, p_orez, 2.0, UnitType.KG)
    link_ingredient(db, d, p_shkedim, 0.2, UnitType.KG)
    link_ingredient(db, d, p_hamuziot, 0.15, UnitType.KG)
    link_serving(db, d, t_side_bowl, 1)
    side_dishes.append(d)

    d = make_dish(db, "אורז עשיר בירקות",
        "אורז בסמטי מוקפץ עם ירקות מוקפצים",
        KosherType.PARVE,
        waiter_notes="להגיש חם. לפזר עלי פטרוזיליה",
        serving_desc="קערת תוספות עמוקה")
    link_ingredient(db, d, p_orez, 2.0, UnitType.KG)
    link_ingredient(db, d, p_yerakot, 1.0, UnitType.KG)
    link_serving(db, d, t_side_bowl, 1)
    side_dishes.append(d)

    # ═══════════════════════  D E S S E R T S  ═══════════════════════
    dessert_dishes = []

    d = make_dish(db, "מוס שוקולד קטיפתי",
        "מוס שוקולד קטיפתי עשיר בכוסית אישית",
        KosherType.PARVE,
        waiter_notes="להגיש מקורר בכוסיות אישיות. לקשט שוקולד מגורר",
        serving_desc="כוסית קינוח אישית")
    link_ingredient(db, d, p_shokolad, 1.0, UnitType.KG)
    link_serving(db, d, t_dessert_cup, 10)
    dessert_dishes.append(d)

    d = make_dish(db, "מוס לימון ואוכמניות",
        "מוס לימון קל עם אוכמניות טריות בכוסית אישית",
        KosherType.PARVE,
        waiter_notes="להגיש מקורר. לקשט באוכמניות טריות ונענע",
        serving_desc="כוסית קינוח אישית")
    link_ingredient(db, d, p_limon, 0.5, UnitType.KG)
    link_ingredient(db, d, p_ukhmaniyot, 0.5, UnitType.KG)
    link_serving(db, d, t_dessert_cup, 10)
    dessert_dishes.append(d)

    # ═════════════  שבת בוקר — מנה ראשונה  ═════════════════════════
    boker_starter_dishes = []

    d = make_dish(db, "ביצים + כבד",
        "ביצים קשות עם כבד עוף קצוץ",
        KosherType.MEAT,
        waiter_notes="להגיש על מגש שטוח. ביצים חצויות עם כבד מלמעלה",
        serving_desc="מגש ביצים וכבד")
    link_ingredient(db, d, p_beitzim, 25.0, UnitType.UNIT)
    link_ingredient(db, d, p_kaved, 1.0, UnitType.KG)
    link_serving(db, d, t_egg_plate, 1)
    boker_starter_dishes.append(d)

    # ═════════════  שבת בוקר — שדרוגים  ═════════════════════════════
    boker_upgrade_dishes = []

    d = make_dish(db, "קציצות טונה",
        "קציצות טונה ביתיות מטוגנות",
        KosherType.PARVE,
        waiter_notes="להגיש חם על מגש עם לימון בצד",
        serving_desc="מגש דג מלבני")
    link_ingredient(db, d, p_tuna, 2.0, UnitType.KG)
    link_ingredient(db, d, p_pirurim, 0.3, UnitType.KG)
    link_serving(db, d, t_fish_plate, 1)
    boker_upgrade_dishes.append(d)

    # ═════════════  שבת בוקר — מנה עיקרית  ═════════════════════════
    boker_main_dishes = []

    d = make_dish(db, "צ'ולנט עסיסי + קישקע + גריסים ושעועית + בשר בקר קוביות",
        "צ'ולנט שבת מסורתי עם קישקע, גריסי פנינה, שעועית לבנה ובשר בקר",
        KosherType.MEAT,
        waiter_notes="להגיש רותח בסיר גדול עם מצקת. לערבב לפני ההגשה",
        serving_desc="סיר צ'ולנט גדול")
    link_ingredient(db, d, p_bakar, 3.0, UnitType.KG)
    link_ingredient(db, d, p_grisim, 1.0, UnitType.KG)
    link_ingredient(db, d, p_shuit, 1.0, UnitType.KG)
    link_ingredient(db, d, p_tapuadama, 2.0, UnitType.KG)
    link_serving(db, d, t_cholent_pot, 1)
    boker_main_dishes.append(d)

    # ═════ שבת בוקר — 2 סוגי בשרי לבחירה ═════
    boker_meat_dishes = []

    d = make_dish(db, "שניצלים",
        "שניצלי עוף פריכים מטוגנים",
        KosherType.MEAT,
        waiter_notes="להגיש חם על מגש גדול",
        serving_desc="מגש הגשה גדול")
    link_ingredient(db, d, p_shnitzel, 3.0, UnitType.KG)
    link_ingredient(db, d, p_pirurim, 0.5, UnitType.KG)
    link_serving(db, d, t_main_platter, 1)
    boker_meat_dishes.append(d)

    d = make_dish(db, "שניצלונים",
        "שניצלוני עוף קטנים ופריכים",
        KosherType.MEAT,
        waiter_notes="להגיש חם. מתאים גם לילדים",
        serving_desc="מגש הגשה גדול")
    link_ingredient(db, d, p_shnitzel, 3.0, UnitType.KG)
    link_ingredient(db, d, p_pirurim, 0.5, UnitType.KG)
    link_serving(db, d, t_main_platter, 1)
    boker_meat_dishes.append(d)

    d = make_dish(db, "פסטרמה ביתית",
        "פסטרמה ביתית מעושנת, פרוסה דק",
        KosherType.MEAT,
        waiter_notes="להגיש בטמפרטורת החדר על מגש",
        serving_desc="מגש הגשה גדול")
    link_ingredient(db, d, p_pastrama, 3.0, UnitType.KG)
    link_serving(db, d, t_main_platter, 1)
    boker_meat_dishes.append(d)

    # רולדת הודו כבר קיימת ב-main_dishes — נשתמש בה גם כאן

    # ═════ שבת בוקר — 1 לבחירה (פשטידות/קוגל) ═════
    boker_pastry_dishes = []

    d = make_dish(db, 'פשטידת תפו"א',
        "פשטידת תפוחי אדמה אפויה בתנור עד הזהבה",
        KosherType.PARVE,
        waiter_notes="להגיש חמה, חתוכה לריבועים",
        serving_desc="מגש מאפים")
    link_ingredient(db, d, p_tapuadama, 3.0, UnitType.KG)
    link_ingredient(db, d, p_beitzim, 6.0, UnitType.UNIT)
    link_serving(db, d, t_pastry_tray, 1)
    boker_pastry_dishes.append(d)

    d = make_dish(db, "קוגל אטריות ירושלמי",
        "קוגל אטריות ירושלמי קרמלי ופריך",
        KosherType.PARVE,
        waiter_notes="להגיש חם. לחתוך פרוסות לפני ההגשה",
        serving_desc="מגש מאפים")
    link_ingredient(db, d, p_atriyot, 1.5, UnitType.KG)
    link_ingredient(db, d, p_beitzim, 8.0, UnitType.UNIT)
    link_serving(db, d, t_pastry_tray, 1)
    boker_pastry_dishes.append(d)

    db.flush()
    total_dishes = (len(salad_dishes) + len(fish_dishes) + len(soup_dishes)
                    + len(main_dishes) + len(side_dishes) + len(dessert_dishes)
                    + len(boker_starter_dishes) + len(boker_upgrade_dishes)
                    + len(boker_main_dishes) + len(boker_meat_dishes)
                    + len(boker_pastry_dishes))
    print(f"   ✔ {total_dishes} מנות נוצרו עם מרכיבים וכלי הגשה")

    # ─────────────────────────────────────────────────────────────────
    #  4. MENU TEMPLATE  — שבת
    # ─────────────────────────────────────────────────────────────────
    print("📋 יוצר תבנית תפריט שבת...")

    template = MenuTemplate(
        menu_type=MenuType.SHABBAT,
        name="תפריט שבת",
        description="קייטרינג בוטיק לאירועים ומוסדות — שבע ברכות, שבת חתן, אויפרוף, בר מצווה וכד'. הזמנת מינימום 50 מנות.",
        min_guests=50,
        base_price_per_guest=None,
        is_tray_menu=False,
    )
    db.add(template)
    db.flush()

    # ── Sub-meals ────────────────────────────────────────────────────
    sm_leil = MenuSubMeal(
        template_id=template.id,
        name="ליל שבת",
        display_order=1,
    )
    sm_boker = MenuSubMeal(
        template_id=template.id,
        name="סעודת שבת בוקר",
        display_order=2,
    )
    db.add_all([sm_leil, sm_boker])
    db.flush()

    # ── Categories — ליל שבת ─────────────────────────────────────────
    cat_leil_salads = MenuCategory(
        template_id=template.id, sub_meal_id=sm_leil.id,
        name="salads", name_hebrew="סלטים",
        description="5 לבחירה",
        display_order=1, quota=5, is_required=True,
    )
    cat_leil_fish = MenuCategory(
        template_id=template.id, sub_meal_id=sm_leil.id,
        name="fish", name_hebrew="מנה ראשונה - דג",
        description="2 לבחירה — חצי כמות סלמון וחצי מושט",
        display_order=2, quota=2, is_required=True,
    )
    cat_leil_soup = MenuCategory(
        template_id=template.id, sub_meal_id=sm_leil.id,
        name="soup", name_hebrew="מרק",
        description="מרק עוף וירקות עשיר",
        display_order=3, quota=1, is_required=True,
    )
    cat_leil_main = MenuCategory(
        template_id=template.id, sub_meal_id=sm_leil.id,
        name="main", name_hebrew="מנה עיקרית",
        description="2 לבחירה, מעל 80 מנות — 3 לבחירה",
        display_order=4, quota=2, is_required=True,
        guest_count_rules={"above_80": {"quota": 3}},
    )
    cat_leil_sides = MenuCategory(
        template_id=template.id, sub_meal_id=sm_leil.id,
        name="sides", name_hebrew="תוספות",
        description="3 לבחירה",
        display_order=5, quota=3, is_required=True,
    )
    cat_leil_dessert = MenuCategory(
        template_id=template.id, sub_meal_id=sm_leil.id,
        name="dessert", name_hebrew="קינוחים",
        description="1 לבחירה",
        display_order=6, quota=1, is_required=True,
    )
    db.add_all([
        cat_leil_salads, cat_leil_fish, cat_leil_soup,
        cat_leil_main, cat_leil_sides, cat_leil_dessert,
    ])
    db.flush()

    # ── Categories — סעודת שבת בוקר ─────────────────────────────────
    cat_boker_salads = MenuCategory(
        template_id=template.id, sub_meal_id=sm_boker.id,
        name="salads", name_hebrew="סלטים",
        description="5 לבחירה (אותה רשימה כמו בליל שבת)",
        display_order=1, quota=5, is_required=True,
    )
    cat_boker_starter = MenuCategory(
        template_id=template.id, sub_meal_id=sm_boker.id,
        name="starter", name_hebrew="מנה ראשונה",
        description="ביצים + כבד",
        display_order=2, quota=1, is_required=True,
    )
    cat_boker_main = MenuCategory(
        template_id=template.id, sub_meal_id=sm_boker.id,
        name="cholent", name_hebrew="מנה עיקרית — צ'ולנט",
        description="צ'ולנט עסיסי + קישקע + גריסים ושעועית + בשר בקר קוביות",
        display_order=3, quota=1, is_required=True,
    )
    cat_boker_meat = MenuCategory(
        template_id=template.id, sub_meal_id=sm_boker.id,
        name="meat_selection", name_hebrew="בשרי לבחירה",
        description="2 סוגי בשרי לבחירה: שניצלים / שניצלונים / פסטרמה ביתית / רולדה הודו",
        display_order=4, quota=2, is_required=True,
    )
    cat_boker_pastry = MenuCategory(
        template_id=template.id, sub_meal_id=sm_boker.id,
        name="pastry", name_hebrew="פשטידה / קוגל",
        description="1 לבחירה: פשטידת תפו\"א / קוגל אטריות ירושלמי",
        display_order=5, quota=1, is_required=True,
    )
    cat_boker_dessert = MenuCategory(
        template_id=template.id, sub_meal_id=sm_boker.id,
        name="dessert", name_hebrew="קינוחים",
        description="1 לבחירה (אותה רשימה כמו בליל שבת)",
        display_order=6, quota=1, is_required=True,
    )
    # upgrade category for boker
    cat_boker_fish_upgrade = MenuCategory(
        template_id=template.id, sub_meal_id=sm_boker.id,
        name="fish_upgrade", name_hebrew="שדרוג - דג",
        description="סלמון / קציצות טונה / מושט בציפוי פירורים (בתוספת תשלום)",
        display_order=7, quota=1, is_required=False,
    )
    db.add_all([
        cat_boker_salads, cat_boker_starter, cat_boker_main,
        cat_boker_meat, cat_boker_pastry, cat_boker_dessert,
        cat_boker_fish_upgrade,
    ])
    db.flush()

    print(f"   ✔ תבנית שבת + 2 תתי-ארוחות + {6+7} קטגוריות")

    # ─────────────────────────────────────────────────────────────────
    #  5. DISH ↔ CATEGORY MAPPINGS
    # ─────────────────────────────────────────────────────────────────
    print("🔗 מקשר מנות לקטגוריות...")

    order = 0
    # ── ליל שבת — סלטים ──
    for i, dish in enumerate(salad_dishes, 1):
        db.add(DishMenuMapping(dish_id=dish.id, category_id=cat_leil_salads.id, display_order=i))
    # ── ליל שבת — דגים ──
    for i, dish in enumerate(fish_dishes, 1):
        db.add(DishMenuMapping(dish_id=dish.id, category_id=cat_leil_fish.id, display_order=i))
    # ── ליל שבת — מרק ──
    for i, dish in enumerate(soup_dishes, 1):
        db.add(DishMenuMapping(dish_id=dish.id, category_id=cat_leil_soup.id, display_order=i))
    # ── ליל שבת — עיקרית ──
    for i, dish in enumerate(main_dishes, 1):
        db.add(DishMenuMapping(dish_id=dish.id, category_id=cat_leil_main.id, display_order=i))
    # ── ליל שבת — תוספות ──
    for i, dish in enumerate(side_dishes, 1):
        db.add(DishMenuMapping(dish_id=dish.id, category_id=cat_leil_sides.id, display_order=i))
    # ── ליל שבת — קינוחים ──
    for i, dish in enumerate(dessert_dishes, 1):
        db.add(DishMenuMapping(dish_id=dish.id, category_id=cat_leil_dessert.id, display_order=i))

    # ── שבת בוקר — סלטים (אותם סלטים) ──
    for i, dish in enumerate(salad_dishes, 1):
        db.add(DishMenuMapping(dish_id=dish.id, category_id=cat_boker_salads.id, display_order=i))
    # ── שבת בוקר — מנה ראשונה ──
    for i, dish in enumerate(boker_starter_dishes, 1):
        db.add(DishMenuMapping(dish_id=dish.id, category_id=cat_boker_starter.id, display_order=i))
    # ── שבת בוקר — צ'ולנט ──
    for i, dish in enumerate(boker_main_dishes, 1):
        db.add(DishMenuMapping(dish_id=dish.id, category_id=cat_boker_main.id, display_order=i))
    # ── שבת בוקר — בשרי לבחירה ──
    for i, dish in enumerate(boker_meat_dishes, 1):
        db.add(DishMenuMapping(dish_id=dish.id, category_id=cat_boker_meat.id, display_order=i))
    # רולדת הודו גם בבחירת הבשרי
    db.add(DishMenuMapping(
        dish_id=main_dishes[1].id,  # רולדת הודו
        category_id=cat_boker_meat.id,
        display_order=len(boker_meat_dishes) + 1,
    ))
    # ── שבת בוקר — פשטידה/קוגל ──
    for i, dish in enumerate(boker_pastry_dishes, 1):
        db.add(DishMenuMapping(dish_id=dish.id, category_id=cat_boker_pastry.id, display_order=i))
    # ── שבת בוקר — קינוחים (אותם קינוחים) ──
    for i, dish in enumerate(dessert_dishes, 1):
        db.add(DishMenuMapping(dish_id=dish.id, category_id=cat_boker_dessert.id, display_order=i))

    # ── שבת בוקר — שדרוג דג ──
    # סלמון (first fish dish)
    db.add(DishMenuMapping(
        dish_id=fish_dishes[0].id,  # סלמון ברוטב פסטו
        category_id=cat_boker_fish_upgrade.id,
        is_upgrade=True, extra_charge=15.0, display_order=1,
    ))
    # קציצות טונה
    db.add(DishMenuMapping(
        dish_id=boker_upgrade_dishes[0].id,
        category_id=cat_boker_fish_upgrade.id,
        is_upgrade=True, extra_charge=15.0, display_order=2,
    ))
    # מושט בציפוי פירורים
    db.add(DishMenuMapping(
        dish_id=fish_dishes[7].id,  # מושט בציפוי פירורים
        category_id=cat_boker_fish_upgrade.id,
        is_upgrade=True, extra_charge=12.0, display_order=3,
    ))

    # ── ליל שבת — שדרוג "כל המנות סלמון" ──
    # This is noted in the menu as an upgrade option for ליל שבת fish

    db.flush()
    print("   ✔ כל המנות מקושרות לקטגוריות")

    # ── COMMIT ───────────────────────────────────────────────────────
    db.commit()
    print()
    print("=" * 60)
    print("✅  הנתונים הוכנסו בהצלחה!")
    print("=" * 60)
    print()
    print(f"  📦  מוצרים:      {len(_product_cache)}")
    print(f"  🍽️   כלי הגשה:    {len(_tool_cache)}")
    print(f"  🥗  מנות:        {total_dishes}")
    print(f"  📋  תבנית שבת:   1")
    print(f"  🍽️   תתי-ארוחות: 2 (ליל שבת + שבת בוקר)")
    print(f"  📁  קטגוריות:    13")
    print()


# =====================================================================
if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed(db)
    except Exception as e:
        db.rollback()
        print(f"❌ שגיאה: {e}")
        raise
    finally:
        db.close()
