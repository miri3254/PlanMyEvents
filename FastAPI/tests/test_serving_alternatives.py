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


def test_menu_default_and_event_override_survive_dishware_switch(setup):
    from app.models.menu import MenuCategory, DishMenuMapping
    db, menu, dish, tool, event, ed = setup
    category = MenuCategory(template_id=menu.id, name='main', name_hebrew='עיקרית')
    db.add(category); db.flush()
    ed.category_id = category.id
    mapping = DishMenuMapping(dish_id=dish.id, category_id=category.id, default_serving_mode='personal')
    db.add(mapping)
    central = variant(db, dish, tool)
    personal = variant(db, dish, tool, mode='personal', default=False)
    real_central = variant(db, dish, tool, kind='real')
    svc = EventCalculationService(db)
    assert svc._resolve_serving_set(event, dish.id).id == personal.id
    ed.serving_mode = 'central'; db.commit(); db.expire_all()
    assert svc._resolve_serving_set(event, dish.id).id == central.id
    event.is_real_dishes = True
    assert svc._resolve_serving_set(event, dish.id).id == real_central.id
    ed.serving_mode = None
    assert svc._resolve_serving_set(event, dish.id) is None
    warnings = []
    assert svc._calculate_serving_sets(event, None, [], warnings) == []
    assert warnings
    event.is_real_dishes = False
    svc.snapshot_event(event); event.status = EventStatus.APPROVED; db.commit()
    frozen = svc.summarize(event).tool_requirements
    mapping.default_serving_mode = 'central'; db.commit()
    assert svc.summarize(event).tool_requirements == frozen


def test_explicit_mode_without_configured_tools_never_uses_legacy(setup):
    from app.models.dish import ServingDish
    db, menu, dish, tool, event, ed = setup
    db.add(ServingDish(dish_id=dish.id, tool_id=tool.id, name='old', quantity=1))
    ed.serving_mode = 'personal'; db.commit()
    svc = EventCalculationService(db)
    warnings = []
    assert svc._calculate_serving_sets(event, None, [], warnings) == []
    assert warnings and svc.serving_tools_for_document(event)[ed.id] == []


def test_manual_tools_material_from_inventory_validation_before_replace(setup):
    from app.models.calculation import EventManualToolRow
    from app.schemas.calculation import EventManualToolRowUpdate
    db, menu, dish, tool, event, ed = setup
    svc = EventCalculationService(db)
    svc.replace_manual_tools(event.id, [EventManualToolRowUpdate(tool_id=tool.id, quantity=3, is_reusable=False)])
    db.commit()
    row = db.query(EventManualToolRow).filter_by(event_id=event.id).one()
    assert row.is_reusable is True  # Catalog material wins, no guessed/unchecked checkbox.
    with pytest.raises(Exception):
        svc.replace_manual_tools(event.id, [EventManualToolRowUpdate(tool_id=99999)])
    assert db.query(EventManualToolRow).filter_by(event_id=event.id).one().quantity == 3
    assert svc._manual_tools(event, [])[0].quantity == 3


def test_default_in_submeal_category(setup):
    from app.models.menu import MenuSubMeal, MenuCategory, DishMenuMapping
    db, menu, dish, tool, event, ed = setup
    meal = MenuSubMeal(template_id=menu.id, name='בוקר')
    db.add(meal); db.flush()
    category = MenuCategory(sub_meal_id=meal.id, name='main', name_hebrew='עיקרית')
    db.add(category); db.flush()
    db.add(DishMenuMapping(dish_id=dish.id, category_id=category.id, default_serving_mode='personal'))
    ed.category_id = category.id; ed.sub_meal_id = meal.id
    variant(db, dish, tool)
    personal = variant(db, dish, tool, mode='personal', default=False)
    assert EventCalculationService(db)._resolve_serving_set(event, dish.id).id == personal.id


def test_serving_override_targets_exact_event_row(setup):
    from app.services.event_service import EventService
    from app.schemas.event import EventDishUpdate
    db, menu, dish, tool, event, ed = setup
    second = EventDish(event_id=event.id, dish_id=dish.id, quantity=1)
    db.add(second); db.commit()
    svc = EventService(db)
    svc.update_event_dish(event.id, dish.id, EventDishUpdate(serving_mode='personal'), second.id)
    db.refresh(ed); db.refresh(second)
    assert ed.serving_mode is None and second.serving_mode == 'personal'
    with pytest.raises(Exception):
        svc.update_event_dish(event.id, dish.id, EventDishUpdate(serving_mode='central'), 999999)
    assert second.serving_mode == 'personal'
