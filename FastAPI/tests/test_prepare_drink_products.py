import pytest
from tests.test_event_calculations import db
from app.core.enums import ProductCategory, UnitType
from app.models.product import Product
from app.models.lookup import LookupData
from app.schemas.product import ProductResponse
from scripts.prepare_drink_products import prepare_products


def test_preparation_reuses_stock_and_is_repeatable(db):
    juice = Product(name='מיץ תפוזים', drink_type='orange_flavored', unit=UnitType.UNIT,
                    quantity_in_stock=17, price_per_unit=8, category=ProductCategory.LIQUIDS)
    water = Product(name='מים', unit=UnitType.UNIT, quantity_in_stock=9)
    oil = Product(name='שמן', unit=UnitType.UNIT, category=ProductCategory.LIQUIDS)
    db.add_all([juice, water, oil, LookupData(category='product_categories', value='נוזלים')])
    db.commit()
    original_ids = juice.id, water.id
    first = prepare_products(db)
    db.commit()
    assert sum(r['action'] == 'created' for r in first) == 3
    assert (juice.id, water.id) == original_ids
    assert (juice.name, juice.quantity_in_stock, juice.price_per_unit) == ('מיץ', 17, 8)
    assert water.quantity_in_stock == 9
    assert oil.category == ProductCategory.LIQUIDS
    assert ProductResponse.from_model(juice).category == 'שתיה'
    assert all(r['action'] == 'unchanged' for r in prepare_products(db))
    assert db.query(Product).count() == 6
    assert db.query(LookupData).filter_by(value='שתיה').count() == 1


def test_ambiguous_existing_product_aborts_before_changes(db):
    db.add_all([Product(name='סודה'), Product(name='סודה')])
    db.commit()
    with pytest.raises(ValueError, match='Ambiguous'):
        prepare_products(db)
    assert db.query(Product).count() == 2
