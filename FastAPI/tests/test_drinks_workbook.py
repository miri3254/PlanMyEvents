"""Regression against original workbook formulas, not the implementation table."""
import ast
import json
import math
import operator
from fractions import Fraction
from pathlib import Path

import pytest
from sqlalchemy.exc import IntegrityError

from tests.test_event_calculations import db, event
from app.models.product import Product
from app.models.calculation import EventCalculationSnapshot
from app.core.enums import EventStatus, UnitType
from app.schemas.product import ProductCreate, ProductUpdate
from app.schemas.calculation import EventCalculationSettingsUpdate
from app.services.product_service import ProductService
from app.services.event_service import EventService
from app.services.event_calculation_service import EventCalculationService
from app.utils.errors import AppException

SOURCE = json.loads((Path(__file__).parent / 'fixtures/drinks_workbook.json').read_text(encoding='utf8'))
OPS = {ast.Div: operator.truediv, ast.Mult: operator.mul, ast.Add: operator.add}


def excel_value(ref, guests):
    if ref == 'B5':
        return Fraction(guests)
    def walk(node):
        if isinstance(node, ast.Name):
            return excel_value(node.id, guests)
        if isinstance(node, ast.Constant):
            return Fraction(str(node.value))
        return OPS[type(node.op)](walk(node.left), walk(node.right))
    return walk(ast.parse(SOURCE['formulas'][ref], mode='eval').body)


@pytest.mark.parametrize('guests', [0, 1, 8, 9, 15, 40, 70, 80, 250, 300])
@pytest.mark.parametrize('category,split,row', [
    ('אירוע רגיל', False, 6), ('שולחן מתוק', False, 7),
    ('שבת', False, 8), ('שבת', True, 9),
])
def test_all_workbook_cells_and_totals(db, guests, category, split, row):
    e = event(db, guests, category)
    e.is_morning_split = split
    summary = EventCalculationService(db).summarize(e)
    actual = {r.name: r for r in summary.product_requirements if r.source_type == 'drink'}
    expected = {}
    raw_total = 0
    for col, name in zip('CDEFG', ['פפסי', 'פפסי מקס', 'מיץ', 'מים', 'סודה']):
        raw = excel_value(f'{col}{row}', guests)
        raw_total += raw
        qty = math.ceil(raw) if col in 'CDE' else math.floor(raw)
        if qty:
            expected[name] = qty
            assert actual[name].raw_quantity == pytest.approx(float(raw), abs=.0001)
            assert actual[name].details['source_cell'] == f'{col}{row}'
    assert {k: v.quantity for k, v in actual.items()} == expected
    assert raw_total == excel_value(f'J{row}', guests)
    if row != 7:  # I7 is intentionally empty in the source.
        assert sum(excel_value(f'{c}{row}', guests) for c in 'CDE') == excel_value(f'I{row}', guests)


@pytest.mark.parametrize('category,split', [('אירוע רגיל', False), ('שולחן מתוק', False), ('שבת', False), ('שבת', True)])
def test_disabled_drink_never_redistributes(db, category, split):
    e = event(db, 70, category); e.is_morning_split = split
    svc = EventCalculationService(db)
    before = {r.name:r.quantity for r in svc.summarize(e).product_requirements if r.source_type=='drink'}
    svc.update_settings(e.id, EventCalculationSettingsUpdate(drink_types={'soda':False}))
    after = {r.name:r.quantity for r in svc.summarize(e).product_requirements if r.source_type=='drink'}
    before.pop('סודה')
    assert after == before


def test_pooled_juice_stock_survives_rename_and_deducts_once(db):
    ps = ProductService(db)
    p = ps.create_product(ProductCreate(name='מיץ', drink_type='orange_flavored', quantity_in_stock=6, package_quantity=6))
    p = ps.update_product(p['id'], ProductUpdate(name='מיץ מעורב'))
    assert p['drink_type'] == 'orange_flavored'
    e = event(db, 70)
    svc = EventCalculationService(db)
    svc.update_settings(e.id, EventCalculationSettingsUpdate(orange_flavored_mode='orange'))  # legacy ignored
    juice = next(r for r in svc.summarize(e).product_requirements if r.product_id == p['id'])
    assert (juice.quantity,juice.available_in_stock,juice.need_to_buy_quantity,juice.packages_to_buy)==(8,6,2,1)
    shopping = EventService(db).get_shopping_list(e.id)
    assert len([r for r in shopping['items'] if r['product_id']==p['id']]) == 1
    db.get(Product,p['id']).quantity_in_stock = 20
    EventService(db)._deduct_inventory(e)
    assert db.get(Product,p['id']).quantity_in_stock == 12


def test_duplicate_and_wrong_unit_rejected_and_soft_delete_releases_type(db):
    svc = ProductService(db)
    p = svc.create_product(ProductCreate(name='מיץ',drink_type='orange_flavored'))
    with pytest.raises(AppException) as error:
        svc.create_product(ProductCreate(name='מיץ תפוחים',drink_type='orange_flavored'))
    assert error.value.status_code == 409
    with pytest.raises(AppException):
        svc.update_product(p['id'],ProductUpdate(unit='ליטר'))
    with pytest.raises(AppException):
        svc.bulk_create([ProductCreate(name='מים א',drink_type='water'),ProductCreate(name='מים ב',drink_type='water')])
    assert not db.query(Product).filter(Product.drink_type=='water').all()
    svc.delete_product(p['id'])
    replacement = svc.create_product(ProductCreate(name='מיץ',drink_type='orange_flavored'))
    assert replacement['id'] != p['id']
    svc.update_product(replacement['id'],ProductUpdate(drink_type=None))
    assert svc.get_product(replacement['id'])['drink_type'] is None


def test_database_blocks_duplicate_drink_type(db):
    db.add_all([Product(name='א',drink_type='water'),Product(name='ב',drink_type='water')])
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()


def test_ambiguous_or_wrong_unit_legacy_stock_is_not_used(db):
    db.add_all([Product(name='מיץ',unit=UnitType.LITER,quantity_in_stock=100),Product(name='מים'),Product(name='מים')])
    db.flush()
    s = EventCalculationService(db).summarize(event(db,70))
    for row in s.product_requirements:
        if row.name in ('מיץ','מים'):
            assert row.product_id is None and row.available_in_stock == 0
    assert any('מיץ' in w for w in s.warnings)


def test_existing_approved_snapshot_is_not_reinterpreted(db):
    e = event(db,70); e.status=EventStatus.APPROVED
    db.add(EventCalculationSnapshot(event_id=e.id,calculation_type='product_requirements',payload=[
        {'source_type':'drink','item_type':'product','name':'תפוזים','quantity':4,'unit':'יחידות'}]))
    db.flush()
    s=EventCalculationService(db).summarize(e)
    assert s.has_approved_snapshot
    assert [(r.name,r.quantity) for r in s.product_requirements]==[('תפוזים',4)]


def test_drink_migration_preserves_existing_stock():
    import importlib.util
    from sqlalchemy import create_engine, inspect
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    path=Path(__file__).parents[1]/'alembic/versions/k4f5a6b7c8d9_add_product_drink_type.py'
    spec=importlib.util.spec_from_file_location('drink_migration',path)
    migration=importlib.util.module_from_spec(spec); spec.loader.exec_module(migration)
    engine=create_engine('sqlite://')
    with engine.begin() as conn:
        conn.exec_driver_sql('CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT, quantity_in_stock FLOAT, is_deleted BOOLEAN DEFAULT 0)')
        conn.exec_driver_sql("INSERT INTO products VALUES (1,'existing',123,0)")
        with Operations.context(MigrationContext.configure(conn)):
            migration.upgrade()
        assert conn.exec_driver_sql('SELECT quantity_in_stock,drink_type FROM products').one()==(123,None)
        assert any(i['name']=='uq_products_active_drink_type' for i in inspect(conn).get_indexes('products'))
