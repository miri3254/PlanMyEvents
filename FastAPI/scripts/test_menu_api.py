"""Test the API response for a menu template."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import SessionLocal
from app.services.menu_service import MenuService

db = SessionLocal()
svc = MenuService(db)

# Test the menu that has direct categories
try:
    result = svc.get_template("תפריט בשרי #2")
    print("=== API Response for 'תפריט בשרי #2' ===")
    print(f"id: {result['id']}")
    print(f"menu_type: {result['menu_type']}")
    print(f"name: {result['name']}")
    print(f"sub_meals count: {len(result.get('sub_meals', []))}")
    print(f"categories count: {len(result.get('categories', []))}")
    
    if result.get('categories'):
        print("\nDirect categories:")
        for cat in result['categories']:
            print(f"  - {cat['name_hebrew']} (id={cat['id']}, dishes={len(cat.get('dishes', []))})")
except Exception as e:
    print(f"Error: {e}")

db.close()
