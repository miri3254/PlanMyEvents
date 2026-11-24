"""Branded event documents (caterer instructions 2026-11, docs/catering-todo/sources/)."""
import pytest

from tests.test_event_calculations import db, event  # noqa: F401 - fixture reuse
from app.models.calculation import EventCalculationSettings
from app.models.dish import Dish, DishIngredient
from app.models.event import EventBox, EventDish
from app.models.menu import MenuTemplate
from app.models.product import Product
from app.core.enums import UnitType
from app.services.event_documents_service import EventDocumentsService
from app.services.event_service import EventService


def _event_with_dishes(db, guests=80, menu="תפריט בשרי", kosher="בשרי"):
    db.add(MenuTemplate(name=menu, menu_type=menu, kosher_type=kosher, base_price_per_guest=1))
    e = event(db, guests, menu)
    for name, size in (("צ'ולנט בשרי", 20), ("מרק כתום", 1), ("סלט כרוב", 8)):
        dish = Dish(name=name, serving_size=size, serving_description="הוראת הגשה")
        db.add(dish)
        db.flush()
        db.add(EventDish(event_id=e.id, dish_id=dish.id, quantity=-(-guests // size)))
    e.seating_sides = [{"side": "גברים", "places": 50, "arrangement": "ארוכים"}]
    db.add(EventBox(event_id=e.id, box_type="קרטון", quantity=3))
    db.commit()
    db.refresh(e)
    return e


@pytest.mark.parametrize("method", ["serving_instructions_pdf", "packing_list_pdf", "delivery_sheet_pdf", "return_sheet_pdf"])
def test_documents_render_branded_and_small(db, method):
    e = _event_with_dishes(db)
    pdf = getattr(EventDocumentsService(db), method)(e).getvalue()
    assert pdf.startswith(b"%PDF")
    assert len(pdf) < 1_000_000  # downscaled letterhead, not the 3.6 MB source PNG


def test_waiter_tools_follow_dishes_and_kosher(db):
    e = _event_with_dishes(db)
    svc = EventDocumentsService(db)
    ctx = svc._context(e)
    per_event, per_waiter = svc._waiter_tools(e, ctx)
    names = [n for n, _, _ in per_event]
    assert "כף לצ'ולנט" in names and "מצקת למרק" in names  # only because those dishes exist
    assert any("נירוסטה" in n for n, _, _ in per_waiter)  # meat event
    assert all(q == str(ctx["waiters"]) for _, q, _ in per_waiter)


def test_spare_regular_vs_sweet(db):
    svc = EventDocumentsService(db)
    regular = _event_with_dishes(db)
    rows = svc._spare_rows(regular, svc._context(regular))
    assert [q for _, q, _ in rows] == ["1"] * 5
    sweet = event(db, 100, "שולחן מתוק")
    rows = svc._spare_rows(sweet, svc._context(sweet))
    assert rows[0][1] == "50"  # plates per portion beyond the setting (100 - 50 places)
    assert sum(1 for _, _, unit in rows if unit == "חבילה") == 4


def test_tablecloth_split_and_warning(db):
    e = event(db, 80)
    db.add(EventCalculationSettings(event_id=e.id, tablecloth_split={"rectangle": 8, "square": 3}))
    db.commit()
    summary = EventService(db).calculations.summarize(e)
    cloths = {r.name: r.quantity for r in summary.tool_requirements if r.source_type == "tablecloths"}
    assert cloths == {"מפות מלבן": 8, "מפות מרובע": 3}
    assert any("מפות: סומנו" in w for w in summary.warnings)  # 11 marked, 12 required (10 + spare 2)


def test_shopping_list_uses_product_name(db):
    flour = Product(name="קמח", unit=UnitType.UNIT, quantity_in_stock=0, package_quantity=1)
    db.add(flour)
    dish = Dish(name="עוגה", serving_size=10)
    db.add(dish)
    db.flush()
    db.add(DishIngredient(dish_id=dish.id, product_id=flour.id, quantity=2, unit=UnitType.UNIT))
    e = event(db, 20)
    db.add(EventDish(event_id=e.id, dish_id=dish.id, quantity=2))
    db.commit()
    items = EventService(db).get_shopping_list(e.id)["items"]
    assert any(i["name"] == "קמח" for i in items)
    assert not any(i["name"].startswith("product_") for i in items)
