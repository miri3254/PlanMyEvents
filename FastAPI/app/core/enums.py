"""
All application enums.

Convention:
  - Python name  = ENGLISH identifier (used in code)
  - .value       = Hebrew string (stored in DB and shown in UI)
"""

from enum import Enum


# ─── Event ────────────────────────────────────────────────────────────

class EventStatus(str, Enum):
    DRAFT = "טיוטה"
    APPROVED = "מאושר"
    COMPLETED = "הסתיים"
    CANCELLED = "בוטל"


# ─── Menu ─────────────────────────────────────────────────────────────
# MenuType is now a free-text string (stored as menu_template.name)
# The MenuType enum is removed - use plain strings everywhere

# ─── Kosher ───────────────────────────────────────────────────────────

class KosherType(str, Enum):
    PARVE = "פרווה"
    MEAT = "בשרי"
    DAIRY = "חלבי"


# ─── Unit Categories ──────────────────────────────────────────────────

class UnitCategory(str, Enum):
    """Category of unit - determines which units can be converted to each other"""
    WEIGHT = "משקל"
    VOLUME = "נפח"
    COUNT = "כמות"


# ─── Units ────────────────────────────────────────────────────────────

class UnitType(str, Enum):
    KG = 'ק"ג'
    GRAM = "גרם"
    MG = 'מ"ג'
    LITER = "ליטר"
    ML = 'מ"ל'
    UNIT = "יחידות"
    PACKAGE = "אריזה"
    TRAY = "מגש"
    CUP = "כוס"
    TABLESPOON = "כף"
    TEASPOON = "כפית"
    PINCH = "קורט"
    BUNDLE = "חבילה"
    # Count units used verbatim in the caterer's recipes (2026-11-24); no weight conversion implied.
    CLOVE = "שן"
    CAN = "קופסה"
    BAG = "שקית"
    BOTTLE = "בקבוק"
    BUNCH = "צרור"
    STALK = "גבעול"
    BASKET = "סלסלה"
    SLEEVE = "שרוול"


# Mapping of units to their category - used for conversion validation
UNIT_CATEGORY_MAP = {
    UnitType.KG: UnitCategory.WEIGHT,
    UnitType.GRAM: UnitCategory.WEIGHT,
    UnitType.MG: UnitCategory.WEIGHT,
    UnitType.LITER: UnitCategory.VOLUME,
    UnitType.ML: UnitCategory.VOLUME,
    UnitType.UNIT: UnitCategory.COUNT,
    UnitType.PACKAGE: UnitCategory.COUNT,
    UnitType.TRAY: UnitCategory.COUNT,
    UnitType.CUP: UnitCategory.VOLUME,
    UnitType.TABLESPOON: UnitCategory.WEIGHT,  # Can be converted to grams
    UnitType.TEASPOON: UnitCategory.WEIGHT,    # Can be converted to grams
    UnitType.PINCH: UnitCategory.WEIGHT,       # Can be converted to grams
    UnitType.BUNDLE: UnitCategory.COUNT,
    UnitType.CLOVE: UnitCategory.COUNT,
    UnitType.CAN: UnitCategory.COUNT,
    UnitType.BAG: UnitCategory.COUNT,
    UnitType.BOTTLE: UnitCategory.COUNT,
    UnitType.BUNCH: UnitCategory.COUNT,
    UnitType.STALK: UnitCategory.COUNT,
    UnitType.BASKET: UnitCategory.COUNT,
    UnitType.SLEEVE: UnitCategory.COUNT,
}


# ─── Product categories ──────────────────────────────────────────────

class ProductCategory(str, Enum):
    # Caterer-approved list (2026-11-24). Enum NAMES are what SQLite stores.
    VEGETABLES = "ירקות"
    DOUGH = "בצק"
    LEAFY_HERBS = "ירקות עלים ועשבי תיבול"
    FRUITS = "פירות"
    LEGUMES = "קטניות"
    GRAINS = "דגנים"
    PASTA_FLOURS = "פסטה וקמחים"
    DRY = "מוצרים יבשים"
    EGGS = "ביצים"
    MEAT = "מוצרי בשר ועוף"
    FISH = "דגים"
    DAIRY = "מוצרי חלב"
    OILS_FATS = "שמנים ושומנים"
    SPICES = "תבלינים ואבקות מרק"
    SAUCES_SPREADS = "רטבים ממרחים"
    CANNED = "שימורים"
    NUTS_SEEDS = "אגוזים זרעים ופירות יבשים"
    BAKING_SWEETS = "אפייה קינוחים וממתיקים"
    LIQUIDS = "נוזלים"
    DRINKS = "שתיה"  # kept: drink products (drink_type) drive the drinks calculation
    # Legacy category retained so existing products can still be read and edited.
    FROZEN = "קפואים"


# ─── Tool categories ─────────────────────────────────────────────────

class ToolCategory(str, Enum):
    PLATES = "צלחות"
    CUPS = "כוסות"
    CUTLERY = 'סכו"ם'
    TABLECLOTHS = "מפות"
    SERVING = "כלי הגשה"


class ToolSubCategory(str, Enum):
    REAL = "אמיתי"
    DISPOSABLE = "חד פעמי"


# ─── Audit ────────────────────────────────────────────────────────────

class AuditAction(str, Enum):
    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"
    STATUS_CHANGED = "status_changed"
    FINALIZED = "finalized"
