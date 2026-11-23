"""Quick test script to verify dish import"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import SessionLocal
from app.models.dish import Dish

db = SessionLocal()

# Get first dish
dish = db.query(Dish).first()

print(f"✅ Dish Details:")
print(f"   Name: {dish.name}")
print(f"   Category: {dish.category}")
print(f"   Kosher Type: {dish.kosher_type}")
print(f"   Serving Size: {dish.serving_size}")
print(f"   Serving Description: {dish.serving_description}")
print(f"   Waiter Notes: {dish.waiter_notes}")
print(f"\n📊 Relationships:")
print(f"   Ingredients: {len(dish.ingredients)}")
for ing in dish.ingredients:
    print(f"      - {ing.name} ({ing.quantity} {ing.unit})")
print(f"   Menu Mappings: {len(dish.menu_mappings)}")
for mapping in dish.menu_mappings:
    print(f"      - {mapping.menu_type.value} / {mapping.category_name} (order: {mapping.display_order})")

db.close()
