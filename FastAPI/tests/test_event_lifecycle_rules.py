"""Status/stock lifecycle rules decided 2026-11-23 (see implementation_status.md)."""
import pytest

from tests.test_event_calculations import db, event  # noqa: F401 - fixture reuse
from app.core.enums import EventStatus, UnitType
from app.models.calculation import DishCalculationRule, EventCalculationSnapshot
from app.models.dish import Dish, DishIngredient
from app.models.event import EventDish
from app.models.menu import MenuTemplate
from app.models.product import Product
from app.schemas.event import EventUpdate
from app.services.event_service import EventService
from app.utils.errors import AppException


def _dish_with_replaced_ingredient(db):
    raw = Product(name="raw-onion", unit=UnitType.UNIT, quantity_in_stock=100, package_quantity=1)
    prepared = Product(name="prepared-onion", unit=UnitType.UNIT, quantity_in_stock=100, package_quantity=1)
    db.add_all([raw, prepared])
    db.flush()
    dish = Dish(name="onion-dish", base_price=10)
    db.add(dish)
    db.flush()
    db.add(DishIngredient(dish_id=dish.id, product_id=raw.id, quantity=1, unit=UnitType.UNIT))
    db.add(DishCalculationRule(
        dish_id=dish.id, rule_type="custom_product", product_id=prepared.id, name="prepared-onion",
        params={"basis": "guest", "factor": 1, "unit": "יחידות"}, replaces_ingredient_product_id=raw.id,
    ))
    db.flush()
    return raw, prepared, dish


def test_completion_skips_replaced_ingredient_and_approval_finalizes_drafts(db):
    raw, prepared, dish = _dish_with_replaced_ingredient(db)
    e = event(db, 10)
    db.add(EventDish(event_id=e.id, dish_id=dish.id, quantity=1, is_draft=True))
    db.commit()

    svc = EventService(db)
    approved = svc.change_status(e.id, EventStatus.APPROVED.value)
    assert all(d["is_draft"] is False for d in approved["dishes"])
    svc.change_status(e.id, EventStatus.COMPLETED.value)

    assert db.get(Product, raw.id).quantity_in_stock == 100  # replaced → not deducted
    assert db.get(Product, prepared.id).quantity_in_stock == 90  # 10 guests × 1


def test_back_to_draft_clears_snapshot_and_approved_edit_warns(db):
    _, _, dish = _dish_with_replaced_ingredient(db)
    e = event(db, 10)
    db.add(EventDish(event_id=e.id, dish_id=dish.id, quantity=1, is_draft=True))
    db.commit()
    svc = EventService(db)
    svc.change_status(e.id, EventStatus.APPROVED.value)

    approved_price = db.get(EventDish, e.dishes[0].id).snapshot_base_price
    edited = svc.update_event(e.id, EventUpdate(guest_count=12))  # Q045: allowed, with warning
    assert edited["status"] == EventStatus.APPROVED.value and edited["guest_count"] == 12
    assert any("מאושר" in w for w in edited["warnings"])
    db.get(Dish, dish.id).base_price = 999
    db.commit()
    svc.update_event(e.id, EventUpdate(guest_count=14))
    assert db.get(EventDish, e.dishes[0].id).snapshot_base_price == approved_price  # Q046: prices stay
    unchanged = svc.update_event(e.id, EventUpdate(guest_count=14, notes="same guests"))
    assert not any("מאושר" in w for w in unchanged["warnings"])

    draft = svc.change_status(e.id, EventStatus.DRAFT.value)
    assert draft["has_calculation_snapshot"] is False
    assert db.query(EventCalculationSnapshot).filter_by(event_id=e.id).count() == 0
    assert all(d["is_draft"] and d["snapshot_base_price"] is None for d in draft["dishes"])
    assert svc.update_event(e.id, EventUpdate(guest_count=16))["guest_count"] == 16


@pytest.mark.parametrize("menu,guests,tables", [
    ("אירוע רגיל", 80, 10), ("אירוע רגיל", 81, 11),
    ("שולחן מתוק", 80, 5), ("שולחן מתוק", 81, 6), ("תפריט מתוק", 160, 10),
    ("שבת", 70, 9),
])
def test_single_table_count_everywhere(db, menu, guests, tables):
    e = event(db, guests, menu)
    response = EventService(db).get_event(e.id)
    summary = EventService(db).calculations.summarize(e)
    assert response["table_count"] == summary.table_count == tables
    assert response["waiter_count"] == summary.waiter_count


def test_min_guests_from_menu_template_is_a_warning(db):
    db.add(MenuTemplate(name="שבת", menu_type="שבת", min_guests=30, base_price_per_guest=1))
    db.commit()
    svc = EventService(db)
    template = svc.menu_repo.get_template_by_type("שבת")
    assert svc._min_guests_warning(29, "שבת", template)
    assert svc._min_guests_warning(30, "שבת", template) is None  # constants say 50
    assert svc._min_guests_warning(49, "תפריט מתוק", None)  # no template → constants fallback (150)
    e = event(db, 20, "שבת")
    response = svc.get_event(e.id)  # Q015: below minimum is allowed, with a warning
    assert any("מינימום" in w for w in response["warnings"])


def test_recipe_per_yield_unit_cost_per_person_units_follow_guests(db):
    flour = Product(name="flour", unit=UnitType.UNIT, quantity_in_stock=100, package_quantity=1)
    db.add(flour)
    db.flush()
    dish = Dish(name="kugel", base_price=40, serving_size=8)  # one kugel serves 8
    db.add(dish)
    db.flush()
    db.add(DishIngredient(dish_id=dish.id, product_id=flour.id, quantity=2, unit=UnitType.UNIT))
    e = event(db, 80)
    db.add(EventDish(event_id=e.id, dish_id=dish.id, quantity=10, is_gift=True))  # wizard: ceil(80/8)
    db.commit()

    svc = EventService(db)
    shopping = svc.get_shopping_list(e.id)
    assert next(i for i in shopping["items"] if i["product_id"] == flour.id)["quantity"] == 20  # 2 × 10 units
    assert svc.calculations.summarize(e).production_cost == 3200  # Q008: 40 per person × 80; gift still costs

    db.get(EventDish, e.dishes[0].id).quantity = 3  # manual change
    db.commit()
    svc.update_event(e.id, EventUpdate(guest_count=100))
    assert svc.get_event(e.id)["dishes"][0]["quantity"] == 13  # Q011: always ceil(100/8)

    svc.update_event(e.id, EventUpdate(guest_count=480))  # 60 units × 2 = 120 > 100 in stock
    svc._deduct_inventory(db.get(type(e), e.id))
    assert db.get(Product, flour.id).quantity_in_stock == -20  # Q055: negative stock allowed


def test_dashboard_revenue_uses_final_price(db):
    from app.services.dashboard_service import DashboardService
    e = event(db, 10)
    e.calculated_price, e.total_price, e.final_price = 1000, 1000, 900
    assert DashboardService._event_revenue(e) == 900
    e.final_price = None
    assert DashboardService._event_revenue(e) == 1000


def test_menu_change_reresolves_base_price_and_drops_old_dishes(db):
    db.add_all([
        MenuTemplate(name="menu-a", menu_type="menu-a", base_price_per_guest=50, real_dishes_extra_per_guest=0),
        MenuTemplate(name="menu-b", menu_type="menu-b", base_price_per_guest=80, real_dishes_extra_per_guest=7),
    ])
    db.commit()
    e = event(db, 10, "menu-a")
    old_dish = Dish(name="old-menu-dish")
    db.add(old_dish)
    db.flush()
    db.add(EventDish(event_id=e.id, dish_id=old_dish.id, quantity=1))
    db.commit()
    svc = EventService(db)
    updated = svc.update_event(e.id, EventUpdate(menu_type="menu-b"))
    assert updated["dishes"] == []  # Q029: removed, with a warning
    assert any("התפריט הוחלף" in w for w in updated["warnings"])
    assert updated["base_price_per_guest"] == 80
    assert updated["real_dishes_extra_per_guest"] == 7
    assert updated["calculated_price"] == 800
