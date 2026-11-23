from datetime import datetime
from types import SimpleNamespace
import math
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import app.models
from app.db.base import Base
from app.models.dish import Dish
from app.models.menu import MenuTemplate
from app.models.event import Event, EventDish
from app.models.product import Product
from app.models.tool import Tool
from app.models.calculation import DishCalculationRule, DishServingSet, EventCalculationSettings
from app.core.enums import UnitType
from app.services.event_calculation_service import EventCalculationService
from app.services.workbook_rules import PRESETS, calculate_preset, clearing_fee, convert_quantity
from app.services.workbook_tool_import import prepare_workbook_tools

@pytest.fixture
def data():
    engine = create_engine('sqlite://')
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        menu = MenuTemplate(name='בדיקה', menu_type='test', tablecloth_profile='regular')
        dish = Dish(name='אורז עם ירקות')
        event = Event(name='בדיקה', menu_type='test', guest_count=81, date=datetime(2030, 1, 1))
        db.add_all([menu, dish, event]); db.flush()
        db.add(EventDish(event_id=event.id, dish_id=dish.id, quantity=1)); db.commit()
        yield db, menu, dish, event

@pytest.mark.parametrize('key', list(PRESETS))
def test_all_presets_fractional_original_formulas(key):
    p = PRESETS[key]
    expected = 250 * p['audience_fraction'] * p['factor'] / p['divisor']
    assert calculate_preset(key, 250, 'regular')[0] == pytest.approx(expected)
    assert calculate_preset(key, 250, 'sweet')[0] == pytest.approx(expected / 2)
    assert calculate_preset(key, 250, 'sweet', {'round_up': True})[0] == math.ceil(expected / 2)

def test_known_source_cells_and_units():
    assert calculate_preset('pecan', 250, 'sweet')[:3] == (937.5, 937.5, 'גרם')
    assert calculate_preset('citrus_sauce', 250, 'regular')[0] == 2187.5
    assert calculate_preset('fresh_white_cabbage', 250, 'regular')[0] == pytest.approx(250/37)
    assert calculate_preset('salad_liters', 250, 'sweet')[0] == pytest.approx(250/48)
    assert calculate_preset('salad_women_liters', 250, 'sweet')[0] == pytest.approx(250/96)
    assert convert_quantity(937.5, 'גרם', 'ק"ג') == .9375
    assert convert_quantity(2187.5, 'מ״ל', 'ליטר') == 2.1875
    assert convert_quantity(1, 'ליטר', 'ק"ג') is None

@pytest.mark.parametrize('installments,rate', [(1,1.9),(2,2.36),(3,2.74),(4,3.12),(5,3.49),(6,3.87)])
def test_clearing_original_rates(installments, rate):
    settings = SimpleNamespace(credit_card_installments=installments, credit_card_rate=None, credit_card_vat_multiplier=1.18)
    assert clearing_fee(10000, settings) == pytest.approx(rate * 118)
    settings.credit_card_rate = 2
    assert clearing_fee(10000, settings) == 236

def test_import_idempotent_preserves_owner_and_real_source(data):
    db, menu, dish, event = data
    first = prepare_workbook_tools(db); db.commit()
    assert first['variants_created'] == 2
    svc = EventCalculationService(db)
    disposable = svc._resolve_serving_set(event, dish.id)
    assert 'כלנית' in disposable.items[0].tool.name
    assert svc._calculate_serving_sets(event, None, [], [])[0].quantity == 11
    event.is_real_dishes = True
    real = svc._resolve_serving_set(event, dish.id)
    assert 'לאורז' in real.items[0].tool.name
    assert 'חישוב כלים אמיתיים' in real.notes and '45' in real.notes
    real.items[0].quantity = 3
    real.items[0].tool.quantity_in_stock = 20
    db.commit()
    second = prepare_workbook_tools(db); db.commit()
    assert all(value == 0 for value in second.values())
    assert real.items[0].quantity == 3 and real.items[0].tool.quantity_in_stock == 20
    assert len(menu.table_setting_items) == 7
    # Personal cutlery + shared bowls are different bases.
    rows = svc._calculate_table_settings(event, [])
    assert rows[-1].quantity == 11 and rows[0].quantity == 81

def test_explicit_empty_layout_not_replaced(data):
    db, menu, dish, event = data
    menu.table_setting_items = []
    prepare_workbook_tools(db)
    assert menu.table_setting_items == []

def test_stock_normalization_and_unknown_unit(data):
    db, menu, dish, event = data
    product = Product(name='פקאן', unit=UnitType.KG, quantity_in_stock=1)
    db.add(product); db.flush()
    rule = DishCalculationRule(dish_id=dish.id, rule_type='workbook', name='פקאן', product_id=product.id, params={'formula_key':'pecan'})
    db.add(rule); db.commit()
    svc = EventCalculationService(db)
    row = next(r for r in svc.summarize(event, use_snapshot=False).product_requirements if r.source_type == 'workbook')
    assert row.quantity == pytest.approx(.6075) and row.unit == 'ק"ג'
    assert row.need_to_buy_quantity == 0
    rule.params = {'formula_key': 'fresh_iceberg'}; db.commit()
    summary = svc.summarize(event, use_snapshot=False)
    assert not any(r.source_type == 'workbook' for r in summary.product_requirements)
    assert any('חסרה יחידת מידה' in w for w in summary.warnings)
    rule.params = {'formula_key': 'citrus_sauce'}; db.commit()
    summary = svc.summarize(event, use_snapshot=False)
    row = next(r for r in summary.product_requirements if r.source_type == 'workbook')
    assert row.product_id is None  # Never subtract litres from kilograms.

def test_crackers_sweet_only_and_ceil(data):
    db, menu, dish, event = data
    prepare_workbook_tools(db)
    svc = EventCalculationService(db)
    assert svc._calculate_crackers(event, []) == []
    menu.tablecloth_profile = 'sweet'
    row = svc._calculate_crackers(event, [])[0]
    assert row.quantity == 6 and row.raw_quantity == 81/16
    assert row.product_id and row.unit == 'חבילה'
