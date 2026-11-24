"""Reviewed formula catalogue from the original workbook, SHA 32d788fd…e5b.

Formula inputs stay numeric; the source text is never evaluated as Python.
Fractional bowls are intentional for food; whole serving vessels use another basis.
"""
from fractions import Fraction
from decimal import Decimal, ROUND_HALF_UP
import math

GARNISH_SHEET = 'חישוב תוספות לסלטים ומנות'
FRESH_SHEET = 'חישוב סלטים חיים'
SALAD_SHEET = 'חישוב כמות סלטים לשליחה לאירוע'

PRESETS = {}
for key, name, amount, unit, row in [
    ('pecan', 'פקאן', 60, 'גרם', 5), ('gala', 'געלה', 55, 'גרם', 6),
    ('cranberry_almond', 'חמוציות ושקדים', 35, 'גרם', 7),
    ('blanched_almond', 'שקדים מולבנים', 25, 'גרם', 8),
    ('almond_sesame', 'שקדים ושומשום', 25, 'גרם', 9),
    ('munchies', 'מנצס', 12, 'גרם', 10), ('pine_nuts', 'צנוברים', 6, 'גרם', 11),
    ('rice_topping', 'תערובת שקדים חמוציות וסילאן', 50, 'גרם', 12),
    ('snacks', 'נשנושים — מקדם לבירור', .05, 'חבילה', 13),
    ('citrus_sauce', 'רוטב חסה הדרים', 70, 'מ״ל', 18),
    ('soy_sauce', 'רוטב כרוב סויה', 50, 'מ״ל', 19),
    ('mayo_sauce', 'רוטב חסה מיונז', 70, 'מ״ל', 20),
]:
    PRESETS[key] = dict(key=key, name=name, factor=amount, divisor=8, unit=unit,
                        sheet=GARNISH_SHEET, cell=f'F{row}/H{row}', group='תוספות ורטבים', audience_fraction=1)

for key, name, divisor, column in [
    ('iceberg', 'אייסברג', 30, 'C'), ('lettuce', 'חסה רגילה', 10, 'D'),
    ('purple_cabbage', 'כרוב סגול', 75, 'E'), ('white_cabbage', 'כרוב לבן', 37, 'F'),
    ('cherry', 'עגבניות שרי', 60, 'G'), ('green_onion', 'בצל ירוק', 30, 'H'),
    ('parsley', 'פטרוזיליה', 60, 'I'), ('mushrooms', 'פטריות', 40, 'J'), ('sprouts', 'נבטים עבים', 30, 'K'),
]:
    PRESETS['fresh_'+key] = dict(key='fresh_'+key, name=name, factor=1,
        divisor=divisor, unit=('חבילה' if key in ('iceberg', 'lettuce', 'green_onion', 'parsley', 'mushrooms') else 'ק\"ג'), sheet=FRESH_SHEET, cell=f'{column}5/{column}6', group='סלטים חיים', audience_fraction=1)

PRESETS['salad_liters'] = dict(key='salad_liters', name='סלט לשליחה — ליטר לכל 3 שולחנות',
    factor=1, divisor=24, unit='ליטר', sheet=SALAD_SHEET, cell='C3:C4', group='סלטים לשליחה', audience_fraction=1)
PRESETS['salad_women_liters'] = dict(key='salad_women_liters', name='סלט לנשים — חצי מהכמות לפי האקסל',
    factor=1, divisor=24, unit='ליטר', sheet=SALAD_SHEET, cell='C8:C9', group='סלטים לשליחה', audience_fraction=.5)

def calculate_preset(key, guests, profile, params=None):
    rule = PRESETS[key]
    params = params or {}
    factor = Fraction(str(params.get('factor', rule['factor'])))
    divisor = Fraction(str(params.get('divisor', rule['divisor'])))
    audience = Fraction(str(params.get('audience_fraction', rule['audience_fraction'])))
    if factor < 0 or divisor <= 0 or not 0 <= audience <= 1:
        raise ValueError('Invalid workbook factor, divisor or audience fraction')
    raw = Fraction(max(0, guests)) * audience * factor / divisor / (2 if profile == 'sweet' else 1)
    unit = params.get('unit', rule['unit'])
    quantity = math.ceil(raw) if params.get('round_up') else float(raw)
    formula = f"{guests} × {float(audience):g} × {float(factor):g} / {float(divisor):g}" + (' / 2' if profile == 'sweet' else '')
    return quantity, float(raw), unit, formula

INSTALLMENT_RATES = {1: 1.9, 2: 2.36, 3: 2.74, 4: 3.12, 5: 3.49, 6: 3.87}

def clearing_rate(settings):
    override = getattr(settings, 'credit_card_rate', None)
    return float(override if override is not None else INSTALLMENT_RATES.get(getattr(settings, 'credit_card_installments', 1) or 1, 1.9))

def clearing_fee(amount, settings):
    vat = getattr(settings, 'credit_card_vat_multiplier', None) or 1.18
    return float((Decimal(str(amount or 0)) * Decimal(str(clearing_rate(settings))) / 100 * Decimal(str(vat))).quantize(Decimal('.01'), rounding=ROUND_HALF_UP))

# Only mass↔mass and volume↔volume conversions are implicit. No density guesses.
UNIT_SCALE = {'גרם': ('mass', 1), 'ק״ג': ('mass', 1000), 'ק"ג': ('mass', 1000),
              'מ״ל': ('volume', 1), 'מ"ל': ('volume', 1), 'ליטר': ('volume', 1000)}
def convert_quantity(quantity, source_unit, target_unit):
    if source_unit == target_unit:
        return quantity
    source, target = UNIT_SCALE.get(source_unit), UNIT_SCALE.get(target_unit)
    if source and target and source[0] == target[0]:
        return quantity * source[1] / target[1]
    return None
