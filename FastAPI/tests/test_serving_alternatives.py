from datetime import datetime
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import app.models
from app.db.base import Base
from app.models.menu import MenuTemplate
from app.models.dish import Dish
from app.models.event import Event, EventDish
from app.models.tool import Tool
from app.models.calculation import DishServingSet, DishServingSetItem
from app.core.enums import EventStatus
from app.services.event_calculation_service import EventCalculationService
from app.routers.dishes import create_serving_set, update_serving_set
from app.schemas.calculation import DishServingSetCreate

@pytest.fixture
def setup():
    engine = create_engine('sqlite://')
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine)() as db:
        menu = MenuTemplate(name='sweet test', menu_type='sweet-test', tablecloth_profile='sweet')
        dish = Dish(name='בלינצס')
        tool = Tool(name='אובל')
        event = Event(name='test', menu_type='sweet-test', guest_count=81, date=datetime(2030, 1, 1), status=EventStatus.DRAFT)
        db.add_all([menu, dish, tool, event]); db.flush()
        ed = EventDish(event_id=event.id, dish_id=dish.id, quantity=1)
        db.add(ed); db.commit()
        yield db, menu, dish, tool, event, ed

def variant(db, dish, tool, kind='disposable', mode='central', default=True):
    return create_serving_set(dish.id, DishServingSetCreate(name=kind+mode, dishware_type=kind,
        serving_mode=mode, is_default=default, items=[dict(tool_id=tool.id, quantity=1, quantity_basis='serving_group')]), db)

def test_defaults_scoped_by_dishware_and_roundtrip(setup):
    db, menu, dish, tool, event, ed = setup
    disposable = variant(db, dish, tool)
    real = variant(db, dish, tool, 'real')
    db.refresh(disposable)
    assert disposable.is_default and real.is_default
    updated = update_serving_set(dish.id, real.id, DishServingSetCreate(name='edited', dishware_type='real', serving_mode='personal', is_default=True,
        items=[dict(tool_id=tool.id, quantity=2, quantity_basis='guest')]), db)
    assert updated.serving_mode == 'personal' and updated.items[0].quantity == 2

def test_auto_selection_and_switch_preserves_mode(setup):
    db, menu, dish, tool, event, ed = setup
    disposable = variant(db, dish, tool)
    personal = variant(db, dish, tool, 'real', 'personal')
    central = variant(db, dish, tool, 'real', 'central', False)
    svc = EventCalculationService(db)
    assert svc._resolve_serving_set(event, dish.id).id == disposable.id
    event.is_real_dishes = True
    assert svc._resolve_serving_set(event, dish.id).id == personal.id
    assert svc._resolve_serving_set(event, dish.id, disposable.id).id == central.id
    db.delete(central); db.flush()
    assert svc._resolve_serving_set(event, dish.id, disposable.id) is None

def test_sweet_groups_and_category_does_not_override_menu(setup):
    db, menu, dish, tool, event, ed = setup
    variant(db, dish, tool)
    event.event_category = 'אירוע רגיל'
    svc = EventCalculationService(db)
    rows = svc._calculate_serving_sets(event, None, [], [])
    assert rows[0].quantity == 6  # 81/2 -> 41 places -> 6 groups
    menu.tablecloth_profile = 'regular'; event.event_category = 'שולחן מתוק'
    assert svc._calculate_serving_sets(event, None, [], [])[0].quantity == 11

def test_place_settings_automatic_and_explicit_inventory_only(setup):
    db, menu, dish, tool, event, ed = setup
    svc = EventCalculationService(db)
    warnings = []
    rows = svc._calculate_table_settings(event, warnings)
    assert len(rows) == 5 and all(row.quantity == 41 for row in rows)
    assert len(warnings) == 5
    menu.table_setting_items = [dict(name='אובל', quantity=2, disposable_tool_id=tool.id)]
    result = svc.summarize(event, use_snapshot=False)
    row = next(row for row in result.tool_requirements if row.source_type == 'table_setting')
    assert row.tool_id == tool.id and row.quantity == 82
    event.is_real_dishes = True
    row = svc._enrich_tool_requirements(event, svc._calculate_table_settings(event, []))[0]
    assert row.tool_id is None  # Never infer the wrong material by matching its name.

def test_aggregation_retains_each_dish_for_documents(setup):
    db, menu, dish, tool, event, ed = setup
    variant(db, dish, tool)
    menu.table_setting_items = [dict(name='אובל', quantity=1, disposable_tool_id=tool.id)]
    svc = EventCalculationService(db)
    result = svc.summarize(event, use_snapshot=False)
    row = next(row for row in result.tool_requirements if row.tool_id == tool.id)
    assert row.quantity == 47
    assert len(row.details['contributions']) == 2
    assert svc.serving_tools_for_document(event)[ed.id] == [dict(name='אובל', quantity=6)]

def test_other_dish_selection_rejected_before_delete(setup):
    db, menu, dish, tool, event, ed = setup
    selected = variant(db, dish, tool)
    svc = EventCalculationService(db)
    valid = dict(dish_id=dish.id, set_id=selected.id, set_type='serving')
    svc.replace_serving_selections(event.id, [valid])
    with pytest.raises(Exception):
        svc.replace_serving_selections(event.id, [{**valid, 'dish_id': dish.id + 999}])
    assert svc._selection_map(event.id, 'serving')[('dish_id', dish.id)] == selected.id


def test_approved_snapshot_preserves_serving_tools(setup):
    db, menu, dish, tool, event, ed = setup
    selected = variant(db, dish, tool)
    svc = EventCalculationService(db)
    svc.snapshot_event(event)
    event.status = EventStatus.APPROVED
    db.flush()
    selected.items[0].quantity = 10
    event.guest_count = 160
    assert svc.serving_tools_for_document(event)[ed.id] == [dict(name='אובל', quantity=6)]


def test_legacy_event_layout_is_not_double_counted(setup):
    db, menu, dish, tool, event, ed = setup
    svc = EventCalculationService(db)
    settings = svc.get_settings(event.id)
    settings.event_tool_set_items = [dict(tool_id=tool.id, quantity_per_guest=1)]
    warnings = []
    assert svc._calculate_table_settings(event, warnings) == []
    assert warnings


def test_menu_inventory_mapping_persists(setup):
    from app.routers.menus import MenuTemplateUpdateSchema
    from app.services.menu_service import MenuService
    db, menu, dish, tool, event, ed = setup
    payload = MenuTemplateUpdateSchema(table_setting_items=[dict(name='כוס', quantity=2, real_tool_id=tool.id)])
    MenuService(db).update_template(menu.id, payload.model_dump(exclude_unset=True))
    db.expire_all()
    assert MenuService(db).get_template_by_id(menu.id)['table_setting_items'][0]['real_tool_id'] == tool.id
