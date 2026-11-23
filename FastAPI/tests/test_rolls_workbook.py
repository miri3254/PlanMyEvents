"""Original חישוב לחמניות C3:C6, including final upward rounding."""
from fractions import Fraction
from math import ceil
import pytest
from tests.test_event_calculations import db, event
from app.models.menu import MenuTemplate
from app.schemas.calculation import EventCalculationSettingsUpdate
from app.services.event_calculation_service import EventCalculationService

FORMULAS = {
    'regular': ('C3', lambda n: n * Fraction('1.5')),
    'sweet': ('C4', lambda n: n / 2 / 2 * Fraction('1.5')),
    'shabbat': ('C5', lambda n: n * Fraction('1.6') * 2),
    'shabbat_split': ('C6', lambda n: n * Fraction('1.6') * 3),
}


@pytest.mark.parametrize('guests', [0, 1, 3, 8, 9, 65, 70, 75, 80, 300])
@pytest.mark.parametrize('profile', FORMULAS)
def test_rolls_are_automatic_from_menu_not_event_description(db, guests, profile):
    menu = MenuTemplate(name='תפריט בדיקה', menu_type='TEST', tablecloth_profile=profile)
    db.add(menu)
    row = event(db, guests=guests, category='שבת שבע ברכות')
    row.menu_type = 'TEST'
    db.commit()
    service = EventCalculationService(db)
    # Historical off switch must not prevent the now-automatic calculation.
    service.update_settings(row.id, EventCalculationSettingsUpdate(rolls_enabled=False))
    rolls = [r for r in service.summarize(row).product_requirements if r.source_type == 'rolls']
    cell, formula = FORMULAS[profile]
    assert sum(r.quantity for r in rolls) == ceil(formula(Fraction(guests)))
    assert rolls[0].raw_quantity == float(formula(Fraction(guests)))
    assert rolls[0].details['source_cell'] == cell
    menu.name = 'שם אחר'
    row.event_category = 'שולחן מתוק'
    db.commit()
    assert sum(r.quantity for r in service.summarize(row).product_requirements if r.source_type == 'rolls') == ceil(formula(Fraction(guests)))


@pytest.mark.parametrize('profile', FORMULAS)
def test_splitting_roll_types_preserves_rounded_total(db, profile):
    db.add(MenuTemplate(name='בדיקה', menu_type='TEST', tablecloth_profile=profile))
    row = event(db, guests=70)
    row.menu_type = 'TEST'
    db.commit()
    service = EventCalculationService(db)
    service.update_settings(row.id, EventCalculationSettingsUpdate(roll_splits=[
        {'name': 'א', 'percent': 33}, {'name': 'ב', 'percent': 67}]))
    rolls = [r for r in service.summarize(row).product_requirements if r.source_type == 'rolls']
    assert sum(r.quantity for r in rolls) == ceil(FORMULAS[profile][1](Fraction(70)))
    assert all(r.quantity == int(r.quantity) for r in rolls)
