from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401 - registers all metadata
from app.core.enums import EventStatus, KosherType, ProductCategory, UnitType
from app.db.base import Base
from app.models.product import Product
from app.models.tool import Tool
from app.models.event import Event
from app.schemas.calculation import EventCalculationSettingsUpdate
from app.services.event_calculation_service import EventCalculationService


@pytest.fixture()
def db():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


def event(db, guests=80, category="אירוע רגיל"):
    row = Event(
        name="בדיקת חישוב",
        event_category=category,
        menu_type=category,
        guest_count=guests,
        date=datetime(2026, 7, 1, 18, 0),
        status=EventStatus.DRAFT,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def test_regular_drinks_round_up_and_down(db):
    row = event(db, guests=80)
    summary = EventCalculationService(db).summarize(row)
    drinks = [item for item in summary.product_requirements if item.source_type == "drink"]
    quantities = {item.name: item.quantity for item in drinks}
    assert quantities["פפסי"] == 9
    assert quantities["פפסי מקס"] == 9
    assert quantities["מים"] == 5
    assert quantities["סודה"] == 5
    assert quantities["מיץ"] == 9
    assert "תפוזים" not in quantities
    assert "מים בטעמים" not in quantities


def test_roll_split_preserves_exact_total(db):
    row = event(db, guests=75)  # ceil(75 * 1.5) = 113
    service = EventCalculationService(db)
    service.update_settings(row.id, EventCalculationSettingsUpdate(
        roll_splits=[{"name": "א", "percent": 60}, {"name": "ב", "percent": 40}]
    ))
    summary = service.summarize(row)
    rolls = [item for item in summary.product_requirements if item.source_type == "rolls"]
    assert [item.quantity for item in rolls] == [68, 45]
    assert sum(item.quantity for item in rolls) == 113


def test_roll_split_can_use_inventory_product(db):
    product = Product(
        name="לחמניה קשר",
        category=ProductCategory.DRY,
        unit=UnitType.UNIT,
        kosher_type=KosherType.PARVE,
        quantity_in_stock=10,
        price_per_unit=1.8,
    )
    db.add(product)
    db.commit()
    db.refresh(product)

    row = event(db, guests=10)  # ceil(10 * 1.5) = 15
    service = EventCalculationService(db)
    service.update_settings(row.id, EventCalculationSettingsUpdate(
        roll_splits=[{"name": "", "percent": 100, "source": "product", "product_id": product.id}]
    ))

    roll = next(item for item in service.summarize(row).product_requirements if item.source_type == "rolls")
    assert roll.product_id == product.id
    assert roll.name == "לחמניה קשר"
    assert roll.quantity == 15
    assert roll.need_to_buy_quantity == 5
    assert roll.estimated_price == pytest.approx(9)


def test_manual_roll_split_uses_manual_unit_price(db):
    row = event(db, guests=10)  # ceil(10 * 1.5) = 15
    service = EventCalculationService(db)
    service.update_settings(row.id, EventCalculationSettingsUpdate(
        roll_splits=[{
            "name": "לחמניה מיוחדת",
            "percent": 100,
            "source": "manual",
            "price_per_unit": 2.4,
        }]
    ))

    roll = next(item for item in service.summarize(row).product_requirements if item.source_type == "rolls")
    assert roll.product_id is None
    assert roll.name == "לחמניה מיוחדת"
    assert roll.need_to_buy_quantity == 15
    assert roll.estimated_price == pytest.approx(36)


def test_sweet_tablecloths_use_workbook_half_and_one_spare_per_six(db):
    row = event(db, guests=300, category="אירוע מתוק")
    service = EventCalculationService(db)
    service.update_settings(row.id, EventCalculationSettingsUpdate(table_shape="rectangle"))
    summary = service.summarize(row)
    cloth = next(item for item in summary.tool_requirements if item.source_type == "tablecloths")
    assert cloth.quantity == 23  # ceil(300 / 2 / 8) + ceil(19 / 6)
    assert cloth.name == "מפות מלבן"
    assert "שולחן מלבן" in cloth.formula_label


def test_tablecloth_shape_label_changes_to_round(db):
    row = event(db, guests=80)
    service = EventCalculationService(db)

    service.update_settings(row.id, EventCalculationSettingsUpdate(table_shape="rectangle"))
    rectangle_summary = service.summarize(row)
    rectangle_cloth = next(
        item for item in rectangle_summary.tool_requirements if item.source_type == "tablecloths"
    )

    service.update_settings(row.id, EventCalculationSettingsUpdate(table_shape="round"))
    round_summary = service.summarize(row)
    round_cloth = next(
        item for item in round_summary.tool_requirements if item.source_type == "tablecloths"
    )

    assert rectangle_cloth.name == "מפות מלבן"
    assert round_cloth.name == "מפות עגול"
    assert "שולחן עגול" in round_cloth.formula_label


def test_selected_tablecloth_tool_still_shows_shape_label(db):
    tool = Tool(name="מפת בד", quantity_in_stock=0)
    db.add(tool)
    db.commit()
    db.refresh(tool)

    row = event(db, guests=80)
    service = EventCalculationService(db)
    service.update_settings(
        row.id,
        EventCalculationSettingsUpdate(table_shape="round", tablecloth_tool_id=tool.id),
    )

    cloth = next(
        item for item in service.summarize(row).tool_requirements if item.source_type == "tablecloths"
    )
    assert cloth.name == "מפת בד עגול"


def test_credit_card_fee(db):
    row = event(db)
    service = EventCalculationService(db)
    service.update_settings(row.id, EventCalculationSettingsUpdate(
        credit_card_enabled=True, credit_card_amount=7797
    ))
    charge = service.summarize(row).charge_requirements[0]
    assert charge.amount == pytest.approx(174.81, abs=0.01)


def test_approved_snapshot_does_not_change(db):
    row = event(db, guests=80)
    service = EventCalculationService(db)
    original = service.summarize(row)
    row.status = EventStatus.APPROVED
    service.snapshot_event(row)
    db.commit()
    row.guest_count = 300
    db.commit()
    frozen = service.summarize(row)
    assert frozen.has_approved_snapshot is True
    assert [x.quantity for x in frozen.product_requirements] == [x.quantity for x in original.product_requirements]
    assert [x.quantity for x in frozen.tool_requirements] == [x.quantity for x in original.tool_requirements]
