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
}


# ─── Product categories ──────────────────────────────────────────────

class ProductCategory(str, Enum):
    DAIRY = "מוצרי חלב"
    MEAT = "מוצרי בשר"
    LEGUMES = "קטניות"
    LIQUIDS = "נוזלים"
    DRINKS = "שתיה"
    DRY = "מוצרים יבשים"
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
