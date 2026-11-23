"""
Data Reset Script
Wipes existing dishes, event_dishes, and resets lookup categories for menu system migration.
Use this to prepare for the new menu-driven structure with 6 core menu types.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy.orm import Session
from app.core.database import engine, SessionLocal
from app.models.dish import Dish, DishIngredient, DishEquipment, ServingDish
from app.models.event import EventDish
from app.models.lookup import LookupData


def reset_data(db: Session):
    """
    Reset data for menu system migration
    """
    print("=" * 60)
    print("DATA RESET - Menu System Migration")
    print("=" * 60)
    
    # 1. Delete all event-dish associations
    print("\n[1/5] Deleting event-dish associations...")
    deleted_event_dishes = db.query(EventDish).delete()
    print(f"✓ Deleted {deleted_event_dishes} event-dish associations")
    
    # 2. Delete all dish-related data (cascades will handle ingredients, equipment, serving_dishes)
    print("\n[2/5] Deleting all dishes (and related data)...")
    deleted_dishes = db.query(Dish).delete()
    print(f"✓ Deleted {deleted_dishes} dishes")
    
    # 3. Delete old event_types from lookup_data
    print("\n[3/5] Removing old event types from lookup...")
    deleted_event_types = db.query(LookupData).filter(
        LookupData.category == "event_types"
    ).delete()
    print(f"✓ Removed {deleted_event_types} old event type entries")
    
    # 4. Delete old dish_categories from lookup_data
    print("\n[4/5] Removing old dish categories from lookup...")
    deleted_categories = db.query(LookupData).filter(
        LookupData.category == "dish_categories"
    ).delete()
    print(f"✓ Removed {deleted_categories} old dish category entries")
    
    # 5. Add new menu types to lookup_data
    print("\n[5/5] Adding new menu types to lookup...")
    menu_types = [
        {"category": "menu_types", "value": "SHABBAT", "order": 1, "is_default": 0},
        {"category": "menu_types", "value": "MEAT_MENU", "order": 2, "is_default": 1},
        {"category": "menu_types", "value": "DAIRY_MENU", "order": 3, "is_default": 0},
        {"category": "menu_types", "value": "MEAT_TRAYS", "order": 4, "is_default": 0},
        {"category": "menu_types", "value": "DAIRY_TRAYS", "order": 5, "is_default": 0},
        {"category": "menu_types", "value": "SWEET_TABLE", "order": 6, "is_default": 0},
    ]
    
    for mt in menu_types:
        lookup_entry = LookupData(
            category=mt["category"],
            value=mt["value"],
            display_order=mt["order"],
            is_default=mt["is_default"]
        )
        db.add(lookup_entry)
    
    print(f"✓ Added {len(menu_types)} new menu types")
    
    # Commit all changes
    db.commit()
    
    print("\n" + "=" * 60)
    print("✓ DATA RESET COMPLETE")
    print("=" * 60)
    print("\nNext Steps:")
    print("1. Run the Alembic migration to create new tables")
    print("2. Run seed_menu_templates.py to create menu templates")
    print("3. Provide menu data to populate dishes with menu mappings")
    print()


if __name__ == "__main__":
    print("\n⚠️  WARNING: This will DELETE all dishes and event-dish associations!")
    print("This is a ONE-WAY operation and cannot be undone.")
    response = input("\nAre you sure you want to continue? (yes/no): ")
    
    if response.lower() != "yes":
        print("❌ Reset cancelled.")
        sys.exit(0)
    
    db = SessionLocal()
    try:
        reset_data(db)
    except Exception as e:
        print(f"\n❌ Error during reset: {e}")
        db.rollback()
        raise
    finally:
        db.close()
