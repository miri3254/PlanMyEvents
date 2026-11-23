"""Approved workbook rules: חישוב שתיה, C6:G9 (2026-11-17).

Keep the historical orange_flavored key for saved event settings; it now means
one pooled juice product, never separate flavor inventory. Fractions prevent
rounding a mathematically whole bottle up due to floating point noise.
"""
from fractions import Fraction

DRINK_TYPES = {
    "pepsi": {"name": "פפסי", "round": "up", "column": "C"},
    "pepsi_max": {"name": "פפסי מקס", "round": "up", "column": "D"},
    "orange_flavored": {"name": "מיץ", "round": "up", "column": "E"},
    "water": {"name": "מים", "round": "down", "column": "F"},
    "soda": {"name": "סודה", "round": "down", "column": "G"},
}

# (source row, flavored divisor steps, water/soda divisor steps, multiplier)
DRINK_RULES = {
    "regular": (6, (3, 3), (3, 5), Fraction(1)),
    "sweet": (7, (3, 5), (3, 5), Fraction(1)),
    "shabbat": (8, (2, 4), (2, 5), Fraction(2)),
    "shabbat_split": (9, (2, 4), (2, 5), Fraction("2.7")),
}


def drink_quantity(profile: str, key: str, guests: int):
    row, flavored, plain, multiplier = DRINK_RULES[profile]
    divisors = plain if key in ("water", "soda") else flavored
    raw = Fraction(max(0, guests))
    formula = "מנות"
    for divisor in divisors:
        raw /= divisor
        formula += f" / {divisor}"
    if multiplier != 1:
        raw *= multiplier
        formula += f" * {float(multiplier):g}"
    rounding = "למעלה" if DRINK_TYPES[key]["round"] == "up" else "למטה"
    return raw, f"{formula}; עיגול {rounding}", f"{DRINK_TYPES[key]['column']}{row}"
