"""Prepare the five approved drink products; dry run unless --apply is supplied.

Reuses classified products or an unambiguous exact-name match. Never merges
stock, changes units, restores deleted records, or overwrites prices.
"""
import argparse
from datetime import datetime
from pathlib import Path
import sqlite3
import sys

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

from sqlalchemy.orm import Session
from app.core.enums import ProductCategory, UnitType, AuditAction
from app.models.product import Product
from app.models.lookup import LookupData
from app.repositories.audit_repo import AuditRepository
from app.services.drink_rules import DRINK_TYPES


def prepare_products(db):
    products = db.query(Product).filter(Product.is_deleted == False).all()
    plan = []
    for kind, rule in DRINK_TYPES.items():
        matches = [p for p in products if p.drink_type == kind]
        names = [p for p in products if p.name == rule['name']]
        if not matches:
            matches = names
        if len(matches) > 1:
            raise ValueError(f"Ambiguous drink product: {rule['name']}")
        product = matches[0] if matches else None
        if product and (product.unit != UnitType.UNIT or product.drink_type not in (None, kind)):
            raise ValueError(f"Conflicting units/type: {rule['name']}")
        if product and any(p.id != product.id for p in names):
            raise ValueError(f"Name already used by another product: {rule['name']}")
        plan.append((kind, rule['name'], product))

    result = []
    audit = AuditRepository(db)
    for kind, name, product in plan:
        created = product is None
        changed = created or (product.name, product.category, product.drink_type) != (name, ProductCategory.DRINKS, kind)
        if created:
            product = Product(name=name, unit=UnitType.UNIT, quantity_in_stock=0)
            db.add(product)
        if changed:
            product.name = name
            product.category = ProductCategory.DRINKS
            product.drink_type = kind
            db.flush()
            audit.log('product', product.id, (AuditAction.CREATED if created else AuditAction.UPDATED).value)
        result.append({'id': product.id, 'name': name, 'action': 'created' if created else 'updated' if changed else 'unchanged', 'stock': product.quantity_in_stock})

    # Persisted custom lookup lists override enum defaults; retain their entries.
    rows = db.query(LookupData).filter(LookupData.category == 'product_categories').all()
    if rows and not any(r.value == ProductCategory.DRINKS.value for r in rows):
        db.add(LookupData(category='product_categories', value=ProductCategory.DRINKS.value,
                          display_order=max(r.display_order or 0 for r in rows) + 1, is_default=1))
    db.flush()
    return result


def main():
    import json
    from app.db.engine import engine
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    source = Path(engine.url.database).resolve()
    if engine.dialect.name != 'sqlite' or not source.is_relative_to(BASE) or not source.is_file():
        raise RuntimeError('Only the existing configured local SQLite file is supported')
    if args.apply:
        backup = source.parent / 'backups' / f'before_drink_products_{datetime.now():%Y%m%d_%H%M%S_%f}.db'
        backup.parent.mkdir(exist_ok=True)
        raw = engine.raw_connection()
        try:
            with sqlite3.connect(backup) as target:
                raw.driver_connection.backup(target)
        finally:
            raw.close()
        print('Backup:', backup)
    with Session(engine) as db:
        result = prepare_products(db)
        if args.apply:
            db.commit()
        else:
            db.rollback()
        print(json.dumps(result, ensure_ascii=False))
        print('Applied' if args.apply else 'Dry run: rolled back; use --apply to save')


if __name__ == '__main__':
    main()
