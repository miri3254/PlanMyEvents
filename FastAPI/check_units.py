from app.core.enums import UnitType
from app.db.session import SessionLocal
from app.models.product import Product


db = SessionLocal()

products = db.query(Product).all()

unit_groups = {}
invalid_units = []

for product in products:
    unit_str = str(product.unit) if product.unit else "NULL"
    unit_groups.setdefault(unit_str, []).append(product.id)

    try:
        if product.unit:
            valid = any(product.unit == member.value for member in UnitType)
            if not valid:
                invalid_units.append((product.id, product.name, product.unit))
    except Exception:
        invalid_units.append((product.id, product.name, str(product.unit)))

print("=== Unit Value Distribution ===")
for unit, ids in sorted(unit_groups.items()):
    if len(ids) > 5:
        print(f"{unit:20s}: {len(ids):3d} products (IDs: {ids[:5]}...)")
    else:
        print(f"{unit:20s}: {len(ids):3d} products (IDs: {ids})")

print("\n=== Valid UnitType Enum Values ===")
for member in UnitType:
    print(f"  {member.name:12s} = \"{member.value}\"")

if invalid_units:
    print(f"\n=== {len(invalid_units)} INVALID Unit Values Found ===")
    for product_id, name, unit in invalid_units[:20]:
        print(f"  ID {product_id:3d}: {name:30s} - unit=\"{unit}\"")
else:
    print("\nAll unit values are valid!")

db.close()
