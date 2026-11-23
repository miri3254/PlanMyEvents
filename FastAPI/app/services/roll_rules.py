"""Original חישוב לחמניות C3:C6; round only the final total upward."""
from fractions import Fraction
from math import ceil

RULES = {
    'regular': (Fraction('1.5'), 'C3', 'מנות * 1.5'),
    'sweet': (Fraction('1.5') / 2 / 2, 'C4', 'מנות / 2 / 2 * 1.5'),
    'shabbat': (Fraction('1.6') * 2, 'C5', 'מנות * 1.6 * 2'),
    'shabbat_split': (Fraction('1.6') * 3, 'C6', 'מנות * 1.6 * 3'),
}


def calculate_rolls(guests, profile):
    factor, cell, expression = RULES[profile]
    raw = max(0, guests or 0) * factor
    return raw, ceil(raw), cell, f'עיגול למעלה({expression})'
