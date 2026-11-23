"""
Deep API CRUD flow tests.

These tests intentionally exercise broad endpoint chains against an isolated
in-memory database so route ordering, nested resources, bulk operations, and
validation paths are covered before a customer handoff.
"""

import app.models  # noqa: F401 - registers all SQLAlchemy models
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.enums import EventStatus, KosherType, ProductCategory, ToolCategory, ToolSubCategory, UnitType
from app.db.base import Base
from app.db.session import get_db
from app.main import app


engine_test = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module")
def client():
    Base.metadata.create_all(bind=engine_test)
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine_test)


def assert_ok(response, *statuses):
    assert response.status_code in statuses, response.text
    if response.content:
        return response.json()
    return None


def test_drink_product_and_split_round_trip(client):
    product = create_product(client, name='pooled-juice-api', drink_type='orange_flavored', unit=UnitType.UNIT.value, quantity_in_stock=10)
    assert product['drink_type'] == 'orange_flavored'
    duplicate = client.post('/api/products', json={'name':'another-juice','drink_type':'orange_flavored'})
    assert duplicate.status_code == 409
    e = create_event(client, name='split-drinks-api', event_category='שבת', menu_type='שבת', guest_count=70)
    eid=e['id']
    before=assert_ok(client.get(f'/api/events/{eid}/calculations/summary'),200)
    juice=next(r for r in before['product_requirements'] if r['product_id']==product['id'])
    assert (juice['quantity'],juice['need_to_buy_quantity'])==(18,8)
    assert_ok(client.patch(f'/api/events/{eid}/morning-split',json={'is_morning_split':True}),200)
    after=assert_ok(client.get(f'/api/events/{eid}/calculations/summary'),200)
    juice=next(r for r in after['product_requirements'] if r['product_id']==product['id'])
    assert (juice['quantity'],juice['need_to_buy_quantity'])==(24,14)
    disabled=assert_ok(client.put(f'/api/events/{eid}/calculations/settings',json={'drink_types':{'soda':False}}),200)
    assert not any(r['source_type']=='drink' and r['name']=='סודה' for r in disabled['product_requirements'])
    assert next(r for r in disabled['product_requirements'] if r['product_id']==product['id'])['quantity']==24
    assert_ok(client.delete(f"/api/products/{product['id']}"),200)


def create_product(client, name="deep-product", **overrides):
    payload = {
        "name": name,
        "category": ProductCategory.DRY.value,
        "unit": UnitType.KG.value,
        "package_quantity": 1,
        "price_per_unit": 8.5,
        "estimated_price": 8.5,
        "quantity_in_stock": 2,
        "min_stock_level": 5,
        "supplier": "qa-supplier",
        "brand": "qa-brand",
        "notes": "created by deep CRUD test",
    }
    payload.update(overrides)
    return assert_ok(client.post("/api/products", json=payload), 201)


def create_tool(client, name="deep-tool", **overrides):
    payload = {
        "name": name,
        "brand": "qa-brand",
        "category": ToolCategory.SERVING.value,
        "sub_category": ToolSubCategory.REAL.value,
        "quantity_in_stock": 1,
        "min_stock_level": 3,
        "price_per_unit": 12.0,
        "description": "created by deep CRUD test",
        "color": "white",
        "size": "medium",
    }
    payload.update(overrides)
    return assert_ok(client.post("/api/tools", json=payload), 201)


def create_dish(client, name="deep-dish", **overrides):
    payload = {
        "name": name,
        "description": "deep CRUD dish",
        "kosher_type": KosherType.MEAT.value,
        "base_price": 22.0,
        "client_price": 35.0,
        "serving_size": 8,
        "serving_description": "one tray",
        "waiter_notes": "serve warm",
        "is_active": True,
    }
    payload.update(overrides)
    return assert_ok(client.post("/api/dishes", json=payload), 201)


def create_event(client, name="deep-event", **overrides):
    payload = {
        "name": name,
        "event_category": "qa-category",
        "menu_type": "qa-menu",
        "date": "2026-12-15T20:00:00",
        "event_time": "20:00",
        "address": "1 QA Street",
        "city": "QA City",
        "guest_count": 80,
        "is_real_dishes": True,
        "venue_name": "QA Hall",
        "floor": 2,
        "has_elevator": True,
        "onsite_contact_name": "QA Contact",
        "onsite_contact_phone": "0500000000",
        "check_drinks": True,
        "check_rolls": True,
        "owners": [{"name": "QA Owner", "phone": "0501111111", "email": "qa@example.com"}],
        "boxes": [{"box_type": "small", "quantity": 2, "notes": "qa boxes"}],
    }
    payload.update(overrides)
    return assert_ok(client.post("/api/events", json=payload), 201)


def create_menu_template(client, name="deep-menu", **overrides):
    payload = {
        "name": name,
        "description": "deep CRUD menu",
        "min_guests": 10,
        "base_price_per_guest": 45.0,
        "real_dishes_extra_per_guest": 5.0,
        "is_tray_menu": False,
        "kosher_type": KosherType.PARVE.value,
    }
    payload.update(overrides)
    return assert_ok(client.post("/api/menus", json=payload), 201)


def test_products_crud_bulk_low_stock_and_validation(client):
    product = create_product(client, "deep-product-a")

    assert_ok(client.get(f"/api/products/{product['id']}"), 200)
    listing = assert_ok(client.get("/api/products", params={"search": "deep-product-a"}), 200)
    assert any(row["id"] == product["id"] for row in listing["items"])

    low_stock = assert_ok(client.get("/api/products/low-stock"), 200)
    assert any(row["id"] == product["id"] for row in low_stock)

    updated = assert_ok(
        client.put(
            f"/api/products/{product['id']}",
            json={"quantity_in_stock": 11, "min_stock_level": 2, "price_per_unit": 9.25},
        ),
        200,
    )
    assert updated["quantity_in_stock"] == 11

    bulk = assert_ok(
        client.post(
            "/api/products/bulk",
            json=[
                {"name": "deep-product-b", "category": ProductCategory.DRY.value, "unit": UnitType.UNIT.value},
                {"name": "deep-product-c", "category": ProductCategory.LIQUIDS.value, "unit": UnitType.LITER.value},
            ],
        ),
        201,
    )
    created_ids = bulk.get("created_ids") or bulk.get("ids") or []
    if created_ids:
        assert_ok(client.delete("/api/products/bulk", params={"ids": ",".join(map(str, created_ids))}), 200)

    assert_ok(client.delete(f"/api/products/{product['id']}"), 200)
    assert_ok(client.get(f"/api/products/{product['id']}"), 404)
    assert_ok(client.post("/api/products", json={"name": "", "quantity_in_stock": -1}), 422)


def test_tools_crud_bulk_low_stock_and_validation(client):
    tool = create_tool(client, "deep-tool-a")

    assert_ok(client.get(f"/api/tools/{tool['id']}"), 200)
    listing = assert_ok(client.get("/api/tools", params={"search": "deep-tool-a"}), 200)
    assert any(row["id"] == tool["id"] for row in listing["items"])

    low_stock = assert_ok(client.get("/api/tools/low-stock"), 200)
    assert any(row["id"] == tool["id"] for row in low_stock)

    updated = assert_ok(
        client.put(f"/api/tools/{tool['id']}", json={"quantity_in_stock": 9, "min_stock_level": 2, "color": "black"}),
        200,
    )
    assert updated["quantity_in_stock"] == 9
    assert updated["color"] == "black"

    bulk = assert_ok(
        client.post(
            "/api/tools/bulk",
            json=[
                {"name": "deep-tool-b", "category": ToolCategory.CUPS.value, "sub_category": ToolSubCategory.REAL.value},
                {
                    "name": "deep-tool-c",
                    "category": ToolCategory.PLATES.value,
                    "sub_category": ToolSubCategory.DISPOSABLE.value,
                },
            ],
        ),
        201,
    )
    created_ids = bulk.get("created_ids") or bulk.get("ids") or []
    if created_ids:
        assert_ok(client.delete("/api/tools/bulk", params={"ids": ",".join(map(str, created_ids))}), 200)

    assert_ok(client.delete(f"/api/tools/{tool['id']}"), 200)
    assert_ok(client.get(f"/api/tools/{tool['id']}"), 404)
    assert_ok(client.post("/api/tools", json={"name": "", "quantity_in_stock": -1}), 422)


def test_dish_nested_crud_for_ingredients_equipment_sets_and_rules(client):
    product = create_product(client, "deep-dish-product")
    tool = create_tool(client, "deep-dish-tool")
    dish = create_dish(client, "deep-dish-a")
    dish_id = dish["id"]

    ingredient_response = assert_ok(
        client.post(
            f"/api/dishes/{dish_id}/ingredients",
            json={"product_id": product["id"], "name": product["name"], "quantity": 2.5, "unit": UnitType.KG.value},
        ),
        200,
    )
    ingredient = ingredient_response["ingredients"][-1]
    assert ingredient["product_id"] == product["id"]

    ingredient_response = assert_ok(
        client.put(
            f"/api/dishes/{dish_id}/ingredients/{ingredient['id']}",
            json={"quantity": 3.25, "is_serving_component": True},
        ),
        200,
    )
    assert any(row["id"] == ingredient["id"] and row["quantity"] == 3.25 for row in ingredient_response["ingredients"])
    assert_ok(client.delete(f"/api/dishes/{dish_id}/ingredients/{ingredient['id']}"), 200)

    serving_response = assert_ok(
        client.post(f"/api/dishes/{dish_id}/serving-dishes", json={"tool_id": tool["id"], "name": tool["name"], "quantity": 4}),
        200,
    )
    serving = serving_response["serving_dishes"][-1]
    serving_response = assert_ok(
        client.put(f"/api/dishes/{dish_id}/serving-dishes/{serving['id']}", json={"quantity": 5}),
        200,
    )
    assert any(row["id"] == serving["id"] and row["quantity"] == 5 for row in serving_response["serving_dishes"])
    assert_ok(client.delete(f"/api/dishes/{dish_id}/serving-dishes/{serving['id']}"), 200)

    equipment_response = assert_ok(
        client.post(f"/api/dishes/{dish_id}/equipment", json={"tool_id": tool["id"], "name": tool["name"], "quantity": 1}),
        200,
    )
    equipment = equipment_response["serving_dishes"][-1]
    equipment_response = assert_ok(
        client.put(f"/api/dishes/{dish_id}/equipment/{equipment['id']}", json={"quantity": 2}),
        200,
    )
    assert any(row["id"] == equipment["id"] and row["quantity"] == 2 for row in equipment_response["serving_dishes"])
    assert_ok(client.delete(f"/api/dishes/{dish_id}/equipment/{equipment['id']}"), 200)

    serving_set = assert_ok(
        client.post(
            f"/api/dishes/{dish_id}/serving-sets",
            json={
                "name": "deep serving set",
                "set_type": "serving",
                "is_default": True,
                "dishware_type": "real",
                "items": [
                    {
                        "tool_id": tool["id"],
                        "name": tool["name"],
                        "quantity": 1,
                        "quantity_basis": "table",
                        "is_reusable": True,
                    }
                ],
            },
        ),
        201,
    )
    sets = assert_ok(client.get(f"/api/dishes/{dish_id}/serving-sets"), 200)
    assert any(row["id"] == serving_set["id"] for row in sets)
    serving_set = assert_ok(
        client.put(
            f"/api/dishes/{dish_id}/serving-sets/{serving_set['id']}",
            json={
                "name": "deep serving set updated",
                "set_type": "packaging",
                "is_default": False,
                "items": [{"tool_id": tool["id"], "name": tool["name"], "quantity": 2, "quantity_basis": "event"}],
            },
        ),
        200,
    )
    assert serving_set["set_type"] == "packaging"

    rule = assert_ok(
        client.post(
            f"/api/dishes/{dish_id}/calculation-rules",
            json={
                "rule_type": "guest_multiplier",
                "product_id": product["id"],
                "name": "deep rule",
                "params": {"per_guest": 0.25},
                "is_active": True,
            },
        ),
        201,
    )
    rules = assert_ok(client.get(f"/api/dishes/{dish_id}/calculation-rules"), 200)
    assert any(row["id"] == rule["id"] for row in rules)
    rule = assert_ok(
        client.put(
            f"/api/dishes/{dish_id}/calculation-rules/{rule['id']}",
            json={
                "rule_type": "guest_multiplier",
                "product_id": product["id"],
                "name": "deep rule updated",
                "params": {"per_guest": 0.5},
                "is_active": False,
            },
        ),
        200,
    )
    assert rule["is_active"] is False
    assert_ok(client.delete(f"/api/dishes/{dish_id}/calculation-rules/{rule['id']}"), 200)
    assert_ok(client.delete(f"/api/dishes/{dish_id}/serving-sets/{serving_set['id']}"), 200)

    inactive = assert_ok(client.patch(f"/api/dishes/{dish_id}/active", json={"is_active": False}), 200)
    assert inactive["is_active"] is False
    assert_ok(client.delete(f"/api/dishes/{dish_id}"), 200)
    assert_ok(client.get(f"/api/dishes/{dish_id}"), 404)


def test_menu_template_submeal_category_mapping_full_crud(client):
    dish = create_dish(client, "deep-menu-dish")
    template = create_menu_template(client, "deep-menu-a")

    assert_ok(client.get(f"/api/menus/{template['id']}"), 200)
    by_type = assert_ok(client.get(f"/api/menus/by-type/{template['menu_type']}"), 200)
    assert by_type["id"] == template["id"]

    sub_meal = assert_ok(
        client.post(
            "/api/menus/sub-meals",
            json={"template_id": template["id"], "name": "deep sub meal", "display_order": 1, "is_splittable": True},
        ),
        201,
    )
    assert_ok(client.get(f"/api/menus/sub-meals/{sub_meal['id']}"), 200)
    sub_meal = assert_ok(
        client.put(f"/api/menus/sub-meals/{sub_meal['id']}", json={"name": "deep sub meal updated", "split_extra_charge": 7.5}),
        200,
    )
    assert sub_meal["split_extra_charge"] == 7.5

    category = assert_ok(
        client.post(
            "/api/menus/categories",
            json={
                "template_id": template["id"],
                "sub_meal_id": sub_meal["id"],
                "name": "deep category",
                "name_hebrew": "deep category he",
                "display_order": 1,
                "quota": 2,
                "is_required": True,
                "tray_quantity": 3,
                "tray_price": 20.0,
            },
        ),
        201,
    )
    all_categories = assert_ok(client.get("/api/menus/categories/all"), 200)
    assert any(
        row["id"] == category["id"]
        for template_group in all_categories
        for row in template_group["categories"]
    )

    category_dishes = assert_ok(client.get(f"/api/menus/categories/{category['id']}/dishes"), 200)
    assert category_dishes["standard_dishes"] == []
    mapping = assert_ok(
        client.post(
            "/api/menus/dish-mappings",
            json={"dish_id": dish["id"], "category_id": category["id"], "is_upgrade": False, "display_order": 1},
        ),
        201,
    )
    category_dishes = assert_ok(client.get(f"/api/menus/categories/{category['id']}/dishes"), 200)
    assert any(row["dish_id"] == dish["id"] for row in category_dishes["standard_dishes"])
    mapping = assert_ok(
        client.put(f"/api/menus/dish-mappings/{mapping['id']}", json={"is_upgrade": True, "extra_charge": 12.0}),
        200,
    )
    assert mapping["is_upgrade"] is True

    validation = assert_ok(client.post(f"/api/menus/categories/{category['id']}/validate", params={"count": 1, "guest_count": 80}), 200)
    assert "is_valid" in validation
    assert_ok(client.delete(f"/api/menus/dish-mappings/{mapping['id']}"), 200)

    category = assert_ok(
        client.put(f"/api/menus/categories/{category['id']}", json={"name": "deep category updated", "quota": 3}),
        200,
    )
    assert category["quota"] == 3
    assert_ok(client.delete(f"/api/menus/categories/{category['id']}"), 200)
    assert_ok(client.delete(f"/api/menus/sub-meals/{sub_meal['id']}"), 200)

    template = assert_ok(client.put(f"/api/menus/{template['id']}", json={"description": "updated", "min_guests": 20}), 200)
    assert template["min_guests"] == 20
    assert_ok(client.delete(f"/api/menus/{template['id']}"), 200)
    assert_ok(client.get(f"/api/menus/{template['id']}"), 404)


def test_event_full_crud_with_dishes_trays_calculations_lists_and_pdfs(client):
    product = create_product(client, "deep-event-product", unit=UnitType.UNIT.value, quantity_in_stock=0)
    tool = create_tool(client, "deep-event-tool", category=ToolCategory.TABLECLOTHS.value, quantity_in_stock=0)
    dish = create_dish(client, "deep-event-dish")
    event = create_event(client, "deep-event-a")
    event_id = event["id"]

    serving_set = assert_ok(
        client.post(
            f"/api/dishes/{dish['id']}/serving-sets",
            json={
                "name": "event serving set",
                "set_type": "serving",
                "items": [{"tool_id": tool["id"], "name": tool["name"], "quantity": 1, "quantity_basis": "table"}],
            },
        ),
        201,
    )

    assert_ok(client.get(f"/api/events/{event_id}"), 200)
    ranged = assert_ok(client.get("/api/events/range", params={"start": "2026-12-01", "end": "2026-12-31"}), 200)
    assert any(row["id"] == event_id for row in ranged)

    event = assert_ok(
        client.put(
            f"/api/events/{event_id}",
            json={"guest_count": 90, "notes": "updated event", "owners": [{"name": "QA Owner 2"}]},
        ),
        200,
    )
    assert event["guest_count"] == 90
    event = assert_ok(client.patch(f"/api/events/{event_id}/morning-split", json={"is_morning_split": True}), 200)
    assert event["is_morning_split"] is True

    event = assert_ok(client.post(f"/api/events/{event_id}/dishes", json={"dish_id": dish["id"], "quantity": 12, "notes": "added"}), 200)
    event_dish = event["dishes"][-1]
    event = assert_ok(
        client.put(f"/api/events/{event_id}/dishes/{event_dish['dish_id']}", json={"quantity": 14, "is_gift": True}),
        200,
    )
    assert any(row["id"] == event_dish["id"] and row["quantity"] == 14 for row in event["dishes"])
    assert_ok(client.post(f"/api/events/{event_id}/dishes/finalize"), 200)

    tray_event = assert_ok(client.post(f"/api/events/{event_id}/trays", json={"dish_id": dish["id"], "tray_count": 2}), 200)
    tray = tray_event["tray_selections"][-1]
    tray_event = assert_ok(client.put(f"/api/events/{event_id}/trays/{tray['id']}", json={"tray_count": 3, "price_per_tray": 45}), 200)
    assert any(row["id"] == tray["id"] and row["tray_count"] == 3 for row in tray_event["tray_selections"])

    event = assert_ok(client.patch(f"/api/events/{event_id}/status", json={"status": EventStatus.APPROVED.value}), 200)
    assert event["status"] == EventStatus.APPROVED.value
    assert all(row["is_draft"] is False for row in event["dishes"])
    event = assert_ok(client.patch(f"/api/events/{event_id}/price", json={"final_price": 9999}), 200)
    assert event["final_price"] == 9999
    # Approved events are frozen: same values pass, real changes need draft first.
    assert_ok(client.put(f"/api/events/{event_id}", json={"guest_count": 90, "notes": "same guests ok"}), 200)
    assert client.put(f"/api/events/{event_id}", json={"guest_count": 95}).status_code == 400
    assert client.post(f"/api/events/{event_id}/dishes", json={"dish_id": dish["id"], "quantity": 1}).status_code == 400
    assert client.put(f"/api/events/{event_id}/trays/{tray['id']}", json={"tray_count": 4}).status_code == 400

    summary = assert_ok(
        client.put(
            f"/api/events/{event_id}/calculations/settings",
            json={
                "drinks_enabled": True,
                "drink_types": {"water": True, "soda": False},
                "rolls_enabled": True,
                "roll_splits": [{"name": "plain", "percent": 60}, {"name": "sesame", "percent": 40}],
                "table_shape": "square",
                "tablecloth_tool_id": tool["id"],
                "event_tool_set_items": [{"tool_id": tool["id"], "name": tool["name"], "quantity": 2, "quantity_basis": "event"}],
                "credit_card_enabled": True,
                "credit_card_amount": 123.45,
                "notes": "calculation settings CRUD",
            },
        ),
        200,
    )
    assert summary["settings"]["credit_card_enabled"] is True
    assert_ok(
        client.put(
            f"/api/events/{event_id}/calculations/dish-serving-selections",
            json={"selections": [{"event_dish_id": event_dish["id"], "dish_id": dish["id"], "set_id": serving_set["id"]}]},
        ),
        200,
    )
    assert_ok(
        client.put(
            f"/api/events/{event_id}/calculations/manual-tools",
            json={"rows": [{"tool_id": tool["id"], "quantity": 4, "is_reusable": True, "notes": "manual"}]},
        ),
        200,
    )
    assert_ok(client.post(f"/api/events/{event_id}/calculations/recalculate"), 200)
    assert_ok(client.get(f"/api/events/{event_id}/calculations/summary"), 200)
    assert_ok(client.get(f"/api/events/{event_id}/shopping-list"), 200)
    assert_ok(client.get(f"/api/events/{event_id}/equipment-list"), 200)

    for path in ("delivery-sheet/pdf", "waiter-pdf", "catering-pdf", "shopping-pdf"):
        pdf_response = client.get(f"/api/events/{event_id}/{path}")
        assert pdf_response.status_code == 200, pdf_response.text
        assert "application/pdf" in pdf_response.headers.get("content-type", "")
        assert len(pdf_response.content) > 100

    assert client.delete(f"/api/events/{event_id}/trays/{tray['id']}").status_code == 400
    event = assert_ok(client.patch(f"/api/events/{event_id}/status", json={"status": EventStatus.DRAFT.value}), 200)
    assert event["has_calculation_snapshot"] is False
    assert all(row["is_draft"] is True and row["snapshot_base_price"] is None for row in event["dishes"])
    assert_ok(client.delete(f"/api/events/{event_id}/trays/{tray['id']}"), 200)
    assert_ok(client.delete(f"/api/events/{event_id}/dishes/{event_dish['dish_id']}"), 200)
    assert_ok(client.post(f"/api/events/{event_id}/restore-stock"), 200)
    assert_ok(client.delete(f"/api/events/{event_id}"), 200)
    assert_ok(client.get(f"/api/events/{event_id}"), 404)


def test_lookup_and_unit_conversion_crud_edges(client):
    lookup = assert_ok(client.get("/api/lookup"), 200)
    assert "product_categories" in lookup

    created_lookup = assert_ok(client.post("/api/lookup/product_categories", json={"value": "deep lookup category"}), 201)
    assert created_lookup["success"] is True
    lookup = assert_ok(client.get("/api/lookup"), 200)
    assert "deep lookup category" in lookup["product_categories"]
    index = lookup["product_categories"].index("deep lookup category")
    updated_lookup = assert_ok(client.put(f"/api/lookup/product_categories/{index}", json={"value": "deep lookup category updated"}), 200)
    assert updated_lookup["success"] is True
    lookup = assert_ok(client.get("/api/lookup"), 200)
    assert "deep lookup category updated" in lookup["product_categories"]
    index = lookup["product_categories"].index("deep lookup category updated")
    deleted_lookup = assert_ok(client.delete(f"/api/lookup/product_categories/{index}"), 200)
    assert deleted_lookup["success"] is True
    lookup = assert_ok(client.get("/api/lookup"), 200)
    assert "deep lookup category updated" not in lookup["product_categories"]

    assert_ok(client.post("/api/unit-conversions/seed"), 200)
    conversion = assert_ok(
        client.post(
            "/api/unit-conversions",
            json={"from_unit": UnitType.PACKAGE.value, "to_unit": UnitType.UNIT.value, "factor": 12, "description": "qa package"},
        ),
        201,
    )
    assert_ok(client.get(f"/api/unit-conversions/{conversion['id']}"), 200)
    calculated = assert_ok(
        client.post(
            "/api/unit-conversions/calculate",
            json={"value": 2, "from_unit": UnitType.PACKAGE.value, "to_unit": UnitType.UNIT.value},
        ),
        200,
    )
    assert calculated["convertedValue"] == 24
    conversion = assert_ok(client.put(f"/api/unit-conversions/{conversion['id']}", json={"factor": 10}), 200)
    assert conversion["factor"] == 10
    assert_ok(client.delete(f"/api/unit-conversions/{conversion['id']}"), 200)
    assert_ok(client.get(f"/api/unit-conversions/{conversion['id']}"), 404)
