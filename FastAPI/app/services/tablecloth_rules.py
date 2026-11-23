"""חישוב מפות C3:C6: evaluate first, round up, then ceil(base / 6) spare."""
from fractions import Fraction
from math import ceil

RULES = {
    'regular': (Fraction(1, 8), 'C3', 'מנות / 8'),
    'sweet': (Fraction(1, 16), 'C4', 'מנות / 2 / 8'),
    'shabbat': (Fraction(2, 8), 'C5', 'מנות / 8 * 2'),
    'shabbat_split': (Fraction(3, 8), 'C6', 'מנות / 8 * 3'),
}

# Exact legacy template keys only; event_category is deliberately never read.
LEGACY_PROFILES = {
    'SHABBAT': 'shabbat', 'שבת': 'shabbat', 'תפריט שבת': 'shabbat',
    'שולחן מתוק': 'sweet', 'אירוע מתוק': 'sweet',
    'שבת מפוצל': 'shabbat_split', 'שבת מפוצלת': 'shabbat_split',
}


def calculate_tablecloths(guests, profile):
    factor, cell, formula = RULES[profile]
    raw = max(0, guests or 0) * factor
    base = ceil(raw)
    spare = ceil(Fraction(base, 6))
    return raw, base, spare, cell, formula
