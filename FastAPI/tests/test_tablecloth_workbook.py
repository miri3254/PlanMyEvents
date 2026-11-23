from fractions import Fraction
from math import ceil
import importlib

import pytest
from sqlalchemy import create_engine, text
from alembic.migration import MigrationContext
from alembic.operations import Operations
from tests.test_event_calculations import db, event
from app.models.menu import MenuTemplate
from app.services.event_calculation_service import EventCalculationService
from app.services.menu_service import MenuService
from app.schemas.calculation import EventCalculationSettingsUpdate

# Original workbook C3:C6, independently evaluated in the assertion below.
FORMULAS = {'regular': 'C2/8', 'sweet': 'C2/2/8', 'shabbat': 'C2/8*2', 'shabbat_split': 'C2/8*3'}


@pytest.mark.parametrize('guests', [0, 1, 8, 9, 48, 49, 65, 70, 80, 300])
@pytest.mark.parametrize('profile', FORMULAS)
def test_original_formulas_and_spares(db, guests, profile):
    db.add(MenuTemplate(name='תפריט בדיקה', menu_type='TEST', tablecloth_profile=profile))
    row = event(db, guests=guests, category='שבת שבע ברכות')
    row.menu_type = 'TEST'
    db.commit()
    service = EventCalculationService(db)
    service.update_settings(row.id, EventCalculationSettingsUpdate(table_shape='square', use_rectangular_for_square=True))
    cloth = next(r for r in service.summarize(row).tool_requirements if r.source_type == 'tablecloths')
    raw = eval(FORMULAS[profile], {'__builtins__': {}}, {'C2': Fraction(guests)})
    base = ceil(raw)
    assert cloth.raw_quantity == float(raw)
    assert cloth.quantity == base + ceil(Fraction(base, 6))
    assert cloth.details['profile'] == profile


def test_template_rule_survives_rename_and_category_does_not_control_it(db):
    menu = MenuTemplate(name='שבת', menu_type='SHABBAT', tablecloth_profile='regular')
    db.add(menu)
    row = event(db, guests=70, category='שולחן מתוק')
    row.menu_type = 'SHABBAT'
    db.commit()
    service = EventCalculationService(db)
    def quantity():
        return next(r.quantity for r in service.summarize(row).tool_requirements if r.source_type == 'tablecloths')
    assert quantity() == 11
    MenuService(db).update_template(menu.id, {'name': 'שם חדש', 'tablecloth_profile': 'sweet'})
    assert quantity() == 11  # user edits cannot override the automatic rule
    row.event_category = 'שבת'
    assert quantity() == 11
    row.menu_type = 'unknown menu'
    assert quantity() == 11


@pytest.mark.parametrize('name,profile,total', [('שולחן מתוק','sweet',6), ('שבת','shabbat',21), ('אירוע בשרי','regular',11)])
def test_menu_creation_automatically_links_tablecloths(db, name, profile, total):
    created = MenuService(db).create_template({'name': name})
    assert created['tablecloth_profile'] == profile
    row = event(db, guests=70, category='תיאור בלבד')
    row.menu_type = created['menu_type']
    db.commit()
    service = EventCalculationService(db)
    cloth = next(r for r in service.summarize(row).tool_requirements if r.source_type == 'tablecloths')
    assert cloth.quantity == total  # no calculation settings need to be selected


def test_migration_classifies_existing_templates_without_rewriting_other_data():
    engine = create_engine('sqlite://')
    from pathlib import Path
    spec = importlib.util.spec_from_file_location('tablecloth_migration', Path(__file__).parents[1] / 'alembic/versions/l5a6b7c8d9e0_menu_tablecloth_profile.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with engine.begin() as conn:
        conn.execute(text('CREATE TABLE menu_templates (id INTEGER PRIMARY KEY, menu_type TEXT, name TEXT, base_price_per_guest FLOAT)'))
        conn.execute(text('INSERT INTO menu_templates VALUES (1, :key, :name, 100), (2, :sweet, :sweet, 55), (3, :regular, :regular, 77)'), {'key': 'SHABBAT', 'name': 'תפריט שבת', 'sweet': 'שולחן מתוק', 'regular': 'אחר'})
        with Operations.context(MigrationContext.configure(conn)):
            module.upgrade()
        assert conn.execute(text('SELECT tablecloth_profile, base_price_per_guest FROM menu_templates ORDER BY id')).all() == [('shabbat', 100), ('sweet', 55), ('regular', 77)]
