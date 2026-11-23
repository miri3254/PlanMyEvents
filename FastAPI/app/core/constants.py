"""
Application-wide constants.
NOTE: Now that menu types are dynamic, MIN_GUESTS and GUEST_COUNT_RULES
use Hebrew string keys directly. New menu types will have their min_guests
defined in the menu_templates table instead.
"""

# Default minimum guest counts for existing (legacy) menu types
# For new dynamic menus, min_guests is defined per MenuTemplate row
MIN_GUESTS: dict[str, int] = {
    "שבת": 50,
    "תפריט מתוק": 150,
    "תפריט בשרי": 1,
    "תפריט חלבי": 1,
    "מגשי אירוח בשרי": 1,
    "מגשי אירוח חלבי": 1,
}

# Allowed status transitions  (from → list of allowed targets)
ALLOWED_STATUS_TRANSITIONS: dict[str, list[str]] = {
    "טיוטה": ["מאושר", "בוטל"],
    "מאושר": ["הסתיים", "בוטל", "טיוטה"],
    "הסתיים": [],
    "בוטל": ["טיוטה"],
}

# Dynamic quota rules keyed by menu_type value
# e.g. for meat menu with >80 guests the main_course quota bumps to 3
GUEST_COUNT_RULES: dict[str, dict] = {
    "תפריט בשרי": {
        "main_course": {"above": 80, "quota": 3},
    },
    "שבת": {
        "main_course": {"above": 80, "quota": 3},
    },
}

# Inventory status thresholds (computed, never stored)
INVENTORY_OUT_OF_STOCK = "אזל"
INVENTORY_LOW_STOCK = "מלאי נמוך"
INVENTORY_IN_STOCK = "במלאי"
