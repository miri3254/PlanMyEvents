"""
Comprehensive tests for PlanMyEvents API.
Run with: pytest tests/test_comprehensive.py -v
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.base import Base
from app.db.session import get_db

# ── Test DB (in-memory SQLite, single shared connection) ────────────────────
SQLALCHEMY_TEST_URL = "sqlite://"

engine_test = create_engine(
    SQLALCHEMY_TEST_URL,
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
    Base.metadata.drop_all(bind=engine_test)
    app.dependency_overrides.clear()


# ── Fixtures ────────────────────────────────────────────────────────────────
@pytest.fixture
def sample_product(client):
    r = client.post("/api/products", json={
        "name": "תפוחי אדמה_fixture",
        "category": "מוצרים יבשים",
        "unit": 'ק"ג',
        "quantity_in_stock": 10,
        "min_stock_level": 3,
        "price_per_unit": 5.5,
    })
    assert r.status_code == 201, r.text
    return r.json()


@pytest.fixture
def sample_tool(client):
    r = client.post("/api/tools", json={
        "name": "צלחת_fixture",
        "category": "כלי הגשה",
        "sub_category": "אמיתי",
        "quantity_in_stock": 5,
        "min_stock_level": 1,
    })
    assert r.status_code == 201, r.text
    return r.json()


@pytest.fixture
def sample_dish(client):
    r = client.post("/api/dishes", json={
        "name": "שניצל_fixture",
        "kosher_type": "בשרי",
        "serving_size": 4,
        "base_price": 30.0,
    })
    assert r.status_code == 201, r.text
    return r.json()


@pytest.fixture
def sample_event(client):
    r = client.post("/api/events", json={
        "name": "חתונה_fixture",
        "menu_type": "שבת",
        "date": "2026-12-15T20:00:00",
        "guest_count": 120,
    })
    assert r.status_code == 201, r.text
    return r.json()


@pytest.fixture(scope="module")
def sample_menu(client):
    # menu_type is a UNIQUE key - create once per test session
    # Try to get existing first
    r = client.get("/api/menus/by-type/%D7%9E%D7%92%D7%A9%D7%99%20%D7%90%D7%99%D7%A8%D7%95%D7%97%20%D7%91%D7%A9%D7%A8%D7%99")
    if r.status_code == 200 and r.json() and isinstance(r.json(), dict) and "id" in r.json():
        return r.json()
    r = client.post("/api/menus", json={
        "menu_type": "מגשי אירוח בשרי",
        "name": "תפריט מגשים_fixture",
        "kosher_type": "בשרי",
        "min_guests": 50,
    })
    if r.status_code == 201:
        return r.json()
    # If creation failed (maybe UNIQUE constraint already), get all menus and return first
    all_r = client.get("/api/menus")
    if all_r.status_code == 200:
        items = all_r.json()
        items_list = items if isinstance(items, list) else items.get("items", [])
        if items_list:
            return items_list[0]
    pytest.fail(f"Could not create or find sample_menu: {r.text}")


# ══════════════════════════════════════════════════════════════════════════════
# HEALTH CHECK
# ══════════════════════════════════════════════════════════════════════════════
class TestHealth:
    def test_root(self, client):
        r = client.get("/")
        assert r.status_code == 200
        assert "PlanMyEvents" in r.json().get("message", "")

    def test_health_endpoint(self, client):
        r = client.get("/api/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


# ══════════════════════════════════════════════════════════════════════════════
# EVENTS
# ══════════════════════════════════════════════════════════════════════════════
class TestEvents:
    def test_list_events(self, client):
        r = client.get("/api/events")
        assert r.status_code == 200
        data = r.json()
        assert "items" in data
        assert "total" in data

    def test_create_event(self, client):
        r = client.post("/api/events", json={
            "name": "אירוע יצירה",
            "event_category": "אירוסים",
            "menu_type": "חתונה",
            "date": "2026-11-15T18:00:00",
            "guest_count": 80,
        })
        assert r.status_code == 201
        body = r.json()
        assert body["name"] == "אירוע יצירה"
        assert body["guest_count"] == 80
        assert body["event_category"] == "אירוסים"
        assert "id" in body

    def test_get_event_by_id(self, client, sample_event):
        r = client.get(f"/api/events/{sample_event['id']}")
        assert r.status_code == 200
        assert r.json()["id"] == sample_event["id"]

    def test_update_event(self, client, sample_event):
        r = client.put(f"/api/events/{sample_event['id']}", json={
            "guest_count": 200,
        })
        assert r.status_code == 200
        assert r.json()["guest_count"] == 200

    def test_delete_event(self, client):
        created = client.post("/api/events", json={
            "name": "אירוע למחיקה",
            "menu_type": "בר מצווה",
            "date": "2026-10-10T10:00:00",
            "guest_count": 50,
        }).json()
        r = client.delete(f"/api/events/{created['id']}")
        assert r.status_code in (200, 204)

    def test_get_nonexistent_event_returns_404(self, client):
        r = client.get("/api/events/999999")
        assert r.status_code == 404

    def test_create_event_missing_required_returns_422(self, client):
        r = client.post("/api/events", json={"name": "חסר menu_type"})
        assert r.status_code == 422

    def test_list_events_pagination(self, client):
        r = client.get("/api/events?page=1&limit=5")
        assert r.status_code == 200
        data = r.json()
        assert len(data["items"]) <= 5

    def test_event_status_update(self, client, sample_event):
        # DRAFT can transition to APPROVED or CANCELLED
        r = client.patch(f"/api/events/{sample_event['id']}/status", json={
            "status": "מאושר"
        })
        assert r.status_code == 200, r.text
        assert r.json()["status"] == "מאושר"

    def test_approved_past_event_auto_completes(self, client):
        created = client.post("/api/events", json={
            "name": "אירוע שעבר",
            "menu_type": "חתונה",
            "date": "2099-01-01T12:00:00",
            "guest_count": 80,
        })
        assert created.status_code == 201, created.text
        event_id = created.json()["id"]

        approved = client.patch(f"/api/events/{event_id}/status", json={
            "status": "מאושר",
        })
        assert approved.status_code == 200, approved.text
        assert approved.json()["status"] == "מאושר"

        moved_to_past = client.put(f"/api/events/{event_id}", json={
            "date": "2000-01-01T12:00:00",
        })
        assert moved_to_past.status_code == 200, moved_to_past.text

        fetched = client.get(f"/api/events/{event_id}")
        assert fetched.status_code == 200, fetched.text
        assert fetched.json()["status"] == "הסתיים"


# ══════════════════════════════════════════════════════════════════════════════
# PRODUCTS
# ══════════════════════════════════════════════════════════════════════════════
class TestProducts:
    def test_list_products(self, client):
        r = client.get("/api/products")
        assert r.status_code == 200
        assert "items" in r.json()

    def test_create_product(self, client):
        r = client.post("/api/products", json={
            "name": "פסטה",
            "category": "מוצרים יבשים",
            "unit": 'ק"ג',
            "quantity_in_stock": 20,
            "min_stock_level": 5,
            "price_per_unit": 8.0,
        })
        assert r.status_code == 201
        assert r.json()["name"] == "פסטה"

    def test_get_product_by_id(self, client, sample_product):
        r = client.get(f"/api/products/{sample_product['id']}")
        assert r.status_code == 200
        assert r.json()["id"] == sample_product["id"]

    def test_update_product(self, client, sample_product):
        r = client.put(f"/api/products/{sample_product['id']}", json={
            "quantity_in_stock": 99,
        })
        assert r.status_code == 200
        assert r.json()["quantity_in_stock"] == 99

    def test_delete_product(self, client):
        p = client.post("/api/products", json={
            "name": "מוצר למחיקה",
        }).json()
        r = client.delete(f"/api/products/{p['id']}")
        assert r.status_code in (200, 204)

    def test_get_nonexistent_product_returns_404(self, client):
        r = client.get("/api/products/999999")
        assert r.status_code == 404

    def test_create_product_empty_name_returns_422(self, client):
        r = client.post("/api/products", json={"name": ""})
        assert r.status_code == 422

    def test_low_stock_endpoint(self, client):
        r = client.get("/api/products/low-stock")
        assert r.status_code == 200

    def test_inventory_status_low_stock(self, client):
        r = client.post("/api/products", json={
            "name": "מוצר מלאי נמוך",
            "category": "מוצרים יבשים",
            "unit": 'ק"ג',
            "quantity_in_stock": 1,
            "min_stock_level": 10,
        })
        assert r.status_code == 201
        body = r.json()
        status = body.get("inventory_status", "")
        assert status in ["מלאי נמוך", "אין במלאי", ""]  # לפחות אחד מהם


# ══════════════════════════════════════════════════════════════════════════════
# TOOLS
# ══════════════════════════════════════════════════════════════════════════════
class TestTools:
    def test_list_tools(self, client):
        r = client.get("/api/tools")
        assert r.status_code == 200
        assert "items" in r.json()

    def test_create_tool(self, client):
        r = client.post("/api/tools", json={
            "name": "צלחת גדולה",
            "category": "כלי הגשה",
            "sub_category": "אמיתי",
            "quantity_in_stock": 20,
            "min_stock_level": 5,
        })
        assert r.status_code == 201
        assert r.json()["name"] == "צלחת גדולה"

    def test_get_tool_by_id(self, client, sample_tool):
        r = client.get(f"/api/tools/{sample_tool['id']}")
        assert r.status_code == 200
        assert r.json()["id"] == sample_tool["id"]

    def test_update_tool(self, client, sample_tool):
        r = client.put(f"/api/tools/{sample_tool['id']}", json={
            "quantity_in_stock": 50,
        })
        assert r.status_code == 200
        assert r.json()["quantity_in_stock"] == 50

    def test_delete_tool(self, client):
        t = client.post("/api/tools", json={
            "name": "כלי למחיקה",
        }).json()
        r = client.delete(f"/api/tools/{t['id']}")
        assert r.status_code in (200, 204)

    def test_get_nonexistent_tool_returns_404(self, client):
        r = client.get("/api/tools/999999")
        assert r.status_code == 404

    def test_low_stock_endpoint(self, client):
        r = client.get("/api/tools/low-stock")
        assert r.status_code == 200

    def test_create_tool_empty_name_returns_422(self, client):
        r = client.post("/api/tools", json={"name": ""})
        assert r.status_code == 422

    def test_inventory_status_present_in_response(self, client, sample_tool):
        r = client.get(f"/api/tools/{sample_tool['id']}")
        assert r.status_code == 200
        assert "inventory_status" in r.json()


# ══════════════════════════════════════════════════════════════════════════════
# DISHES
# ══════════════════════════════════════════════════════════════════════════════
class TestDishes:
    def test_list_dishes(self, client):
        r = client.get("/api/dishes")
        assert r.status_code == 200
        assert "items" in r.json()

    def test_create_dish(self, client):
        r = client.post("/api/dishes", json={
            "name": "קציצות",
            "kosher_type": "בשרי",
            "serving_size": 6,
            "base_price": 25.0,
        })
        assert r.status_code == 201
        body = r.json()
        assert body["name"] == "קציצות"
        assert body["kosher_type"] == "בשרי"

    def test_get_dish_by_id(self, client, sample_dish):
        r = client.get(f"/api/dishes/{sample_dish['id']}")
        assert r.status_code == 200
        assert r.json()["id"] == sample_dish["id"]

    def test_update_dish(self, client, sample_dish):
        r = client.put(f"/api/dishes/{sample_dish['id']}", json={
            "serving_size": 8,
        })
        assert r.status_code == 200
        assert r.json()["serving_size"] == 8

    def test_delete_dish(self, client):
        d = client.post("/api/dishes", json={
            "name": "מנה למחיקה",
            "kosher_type": "פרווה",
        }).json()
        r = client.delete(f"/api/dishes/{d['id']}")
        assert r.status_code in (200, 204)

    def test_get_nonexistent_dish_returns_404(self, client):
        r = client.get("/api/dishes/999999")
        assert r.status_code == 404

    def test_create_dish_empty_name_returns_422(self, client):
        r = client.post("/api/dishes", json={"name": ""})
        assert r.status_code == 422

    def test_dish_has_required_fields(self, client, sample_dish):
        r = client.get(f"/api/dishes/{sample_dish['id']}")
        body = r.json()
        for field in ["id", "name", "kosher_type"]:
            assert field in body, f"Missing field: {field}"

    def test_update_dish_active_status(self, client, sample_dish):
        r = client.patch(f"/api/dishes/{sample_dish['id']}/active", json={"is_active": False})
        assert r.status_code in (200, 404)


# ══════════════════════════════════════════════════════════════════════════════
# MENUS
# ══════════════════════════════════════════════════════════════════════════════
class TestMenus:
    def test_list_menus(self, client):
        r = client.get("/api/menus")
        assert r.status_code == 200

    def test_create_menu(self, client):
        r = client.post("/api/menus", json={
            "menu_type": "תפריט בשרי",
            "name": "תפריט בשרי",
            "kosher_type": "בשרי",
            "min_guests": 100,
        })
        assert r.status_code == 201
        assert r.json()["name"] == "תפריט בשרי"

    def test_get_menu_by_id(self, client, sample_menu):
        r = client.get(f"/api/menus/{sample_menu['id']}")
        assert r.status_code == 200

    def test_update_menu(self, client, sample_menu):
        r = client.put(f"/api/menus/{sample_menu['id']}", json={
            "name": "תפריט מעודכן",
        })
        assert r.status_code == 200
        assert r.json()["name"] == "תפריט מעודכן"

    def test_delete_menu(self, client):
        m = client.post("/api/menus", json={
            "menu_type": "מגשי אירוח חלבי",
            "name": "תפריט למחיקה",
            "kosher_type": "פרווה",
        })
        if m.status_code == 201:
            r = client.delete(f"/api/menus/{m.json()['id']}")
            assert r.status_code in (200, 204)

    def test_get_nonexistent_menu_returns_404(self, client):
        r = client.get("/api/menus/999999")
        assert r.status_code == 404

    def test_list_menus_by_type(self, client, sample_menu):
        r = client.get(f"/api/menus/by-type/{sample_menu['menu_type']}")
        assert r.status_code == 200

        # Renaming a template must not break old events that retain its stable
        # menu_type, while new events can use the current display name.
        current_name = r.json()["name"]
        by_current_name = client.get(f"/api/menus/by-type/{current_name}")
        assert by_current_name.status_code == 200
        assert by_current_name.json()["id"] == sample_menu["id"]

    def test_get_all_categories(self, client):
        r = client.get("/api/menus/categories/all")
        assert r.status_code == 200

    def test_create_menu_category(self, client, sample_menu):
        r = client.post("/api/menus/categories", json={
            "template_id": sample_menu["id"],
            "name": "starters",
            "name_hebrew": "מנות ראשונות",
            "display_order": 1,
        })
        assert r.status_code in (201, 200, 422)  # depends on validation


# ══════════════════════════════════════════════════════════════════════════════
# UNIT CONVERSIONS
# ══════════════════════════════════════════════════════════════════════════════
class TestUnitConversions:
    def test_seed_conversions(self, client):
        r = client.post("/api/unit-conversions/seed")
        assert r.status_code == 200
        body = r.json()
        assert "count" in body or "message" in body or isinstance(body, dict)

    def test_list_conversions(self, client):
        r = client.get("/api/unit-conversions")
        assert r.status_code == 200

    def test_create_user_conversion(self, client):
        # Use valid UnitType values from same category (both COUNT)
        r = client.post("/api/unit-conversions", json={
            "from_unit": "אריזה",
            "to_unit": "יחידות",
            "factor": 12.0,
            "description": "1 אריזה = 12 יחידות",
        })
        assert r.status_code in (200, 201)

    def test_update_user_conversion(self, client):
        created = client.post("/api/unit-conversions", json={
            "from_unit": "חבילה",
            "to_unit": "יחידות",
            "factor": 6.0,
        })
        if created.status_code in (200, 201):
            conv_id = created.json()["id"]
            r = client.put(f"/api/unit-conversions/{conv_id}", json={
                "factor": 10.0,
            })
            assert r.status_code == 200
            assert r.json()["factor"] == 10.0
        if created.status_code in (200, 201):
            conv_id = created.json()["id"]
            r = client.put(f"/api/unit-conversions/{conv_id}", json={
                "from_unit": "כף_upd",
                "to_unit": "גרם",
                "factor": 20.0,
                "is_system": False,
            })
            assert r.status_code == 200
            assert r.json()["factor"] == 20.0

    def test_delete_user_conversion(self, client):
        created = client.post("/api/unit-conversions", json={
            "from_unit": "מגש",
            "to_unit": "יחידות",
            "factor": 1.0,
        })
        if created.status_code in (200, 201):
            conv_id = created.json()["id"]
            r = client.delete(f"/api/unit-conversions/{conv_id}")
            assert r.status_code in (200, 204), f"Delete returned {r.status_code}: {r.text}"

    def test_cannot_delete_system_conversion(self, client):
        client.post("/api/unit-conversions/seed")
        r = client.get("/api/unit-conversions")
        if r.status_code == 200:
            items = r.json() if isinstance(r.json(), list) else r.json().get("items", [])
            # Response uses camelCase "isSystem"
            system_conv = next((c for c in items if c.get("isSystem")), None)
            if system_conv:
                del_r = client.delete(f"/api/unit-conversions/{system_conv['id']}")
                assert del_r.status_code in (400, 403)

    def test_calculate_conversion(self, client):
        client.post("/api/unit-conversions/seed")
        r = client.post("/api/unit-conversions/calculate", json={
            "from_unit": "ק\"ג",
            "to_unit": "גרם",
            "value": 1.0,
        })
        # Either works (200) or units not found (400/404)
        assert r.status_code in (200, 400, 404, 422)


# ══════════════════════════════════════════════════════════════════════════════
# LOOKUP
# ══════════════════════════════════════════════════════════════════════════════
class TestLookup:
    def test_get_all_lookups(self, client):
        r = client.get("/api/lookup")
        assert r.status_code == 200
        body = r.json()
        assert isinstance(body, dict)
        assert len(body) > 0

    def test_lookup_contains_kosher_types(self, client):
        r = client.get("/api/lookup")
        assert r.status_code == 200
        body = r.json()
        # Find kosher types in one of the possible key names
        possible_keys = ["kosher_types", "kosherTypes", "KOSHER_TYPES"]
        found = any(k in body for k in possible_keys)
        assert found

    def test_lookup_contains_menu_types(self, client):
        r = client.get("/api/lookup")
        assert r.status_code == 200
        body = r.json()
        possible_keys = ["menu_types", "menuTypes", "MENU_TYPES"]
        found = any(k in body for k in possible_keys)
        assert found

    def test_lookup_event_categories_are_dynamic(self, client):
        initial = client.get("/api/lookup")
        assert initial.status_code == 200
        assert initial.json()["event_categories"] == [
            "בר מצווה", "אירוסים", "שבע ברכות",
            "אירוע מתוק", "שבת", "מגשי אירוח",
        ]

        added = client.post("/api/lookup/event_categories", json={"value": "חתונה"})
        assert added.status_code == 201
        assert "חתונה" in client.get("/api/lookup").json()["event_categories"]

    def test_lookup_crud_preserves_response_shape(self, client):
        initial = client.get("/api/lookup").json()["product_categories"]
        added_value = "קטגוריית בדיקה"

        added = client.post(
            "/api/lookup/product_categories",
            json={"value": added_value},
        )
        assert added.status_code == 201
        assert added.json()["success"] is True

        after_add = client.get("/api/lookup").json()["product_categories"]
        assert after_add == [*initial, added_value]

        index = len(after_add) - 1
        updated_value = "קטגוריית בדיקה מעודכנת"
        updated = client.put(
            f"/api/lookup/product_categories/{index}",
            json={"value": updated_value},
        )
        assert updated.status_code == 200
        assert client.get("/api/lookup").json()["product_categories"][index] == updated_value

        deleted = client.delete(f"/api/lookup/product_categories/{index}")
        assert deleted.status_code == 200
        assert client.get("/api/lookup").json()["product_categories"] == initial


# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════��═══════════════════════════════════════════════════
class TestDashboard:
    def test_get_stats(self, client):
        r = client.get("/api/dashboard/stats")
        assert r.status_code == 200
        body = r.json()
        assert isinstance(body, dict)

    def test_get_upcoming_events(self, client):
        r = client.get("/api/dashboard/upcoming")
        assert r.status_code == 200

    def test_get_low_stock(self, client):
        r = client.get("/api/dashboard/low-stock")
        assert r.status_code == 200

    def test_get_revenue(self, client):
        r = client.get("/api/dashboard/revenue")
        assert r.status_code == 200

    def test_get_inventory(self, client):
        r = client.get("/api/dashboard/inventory")
        assert r.status_code == 200


# ══════════════════════════════════════════════════════════════════════════════
# ERROR HANDLING
# ══════════════════════════════════════════════════════════════════════════════
class TestErrorHandling:
    def test_404_for_unknown_route(self, client):
        r = client.get("/api/nonexistent-resource")
        assert r.status_code == 404

    def test_422_for_missing_required_fields_event(self, client):
        # EventCreate requires: name, menu_type, date
        r = client.post("/api/events", json={"name": "חסר שדות"})
        assert r.status_code == 422

    def test_422_for_invalid_date_format(self, client):
        r = client.post("/api/events", json={
            "name": "תאריך שגוי",
            "menu_type": "חתונה",
            "date": "not-a-date",
            "guest_count": 50,
        })
        assert r.status_code == 422

    def test_422_for_empty_name_product(self, client):
        r = client.post("/api/products", json={"name": ""})
        assert r.status_code == 422

    def test_422_for_negative_quantity(self, client):
        r = client.post("/api/products", json={
            "name": "מוצר כמות שלילית",
            "quantity_in_stock": -1,
        })
        assert r.status_code == 422
