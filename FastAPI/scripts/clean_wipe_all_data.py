"""
Clean Wipe All Data Script
Performs a complete hard reset of all demo/test data in the database.
Deletes all tables in the correct order to avoid SQLite foreign key constraint errors.

DANGER: This is a DESTRUCTIVE operation that cannot be undone!
Use only when you need a completely clean slate.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy.orm import Session
from app.core.database import engine, SessionLocal
from app.models.dish import Dish, DishIngredient, DishEquipment, ServingDish, DishMenuMapping
from app.models.event import Event, EventDish, EventOwner
from app.models.product import Product
from app.models.tool import Tool
from app.models.lookup import LookupData
from app.models.menu_template import MenuTemplate, MenuCategory


def clean_wipe_all_data(db: Session):
    """
    Completely wipe all data from the database.
    Tables are deleted in reverse dependency order to avoid foreign key errors.
    """
    print("=" * 70)
    print("CLEAN WIPE - HARD RESET OF ALL DATA")
    print("=" * 70)
    print("\n⚠️  This will DELETE ALL DATA from the following tables:")
    print("   • event_dishes, event_owners, events")
    print("   • dish_ingredients, dish_equipment, serving_dishes")
    print("   • dish_menu_mappings, dishes")
    print("   • products, tools")
    print("   • menu_categories, menu_templates")
    print("   • lookup_data")
    print("\n" + "=" * 70)
    
    total_deleted = 0
    
    # Step 1: Transaction tables (highest level dependencies)
    print("\n[Step 1] Deleting transaction/association tables...")
    
    # Event-related associations
    deleted = db.query(EventDish).delete()
    print(f"  ✓ event_dishes: {deleted} records deleted")
    total_deleted += deleted
    
    deleted = db.query(EventOwner).delete()
    print(f"  ✓ event_owners: {deleted} records deleted")
    total_deleted += deleted
    
    # Dish-related associations
    deleted = db.query(DishIngredient).delete()
    print(f"  ✓ dish_ingredients: {deleted} records deleted")
    total_deleted += deleted
    
    deleted = db.query(DishEquipment).delete()
    print(f"  ✓ dish_equipment: {deleted} records deleted")
    total_deleted += deleted
    
    deleted = db.query(ServingDish).delete()
    print(f"  ✓ serving_dishes: {deleted} records deleted")
    total_deleted += deleted
    
    deleted = db.query(DishMenuMapping).delete()
    print(f"  ✓ dish_menu_mappings: {deleted} records deleted")
    total_deleted += deleted
    
    # Step 2: Main entity tables (with foreign keys to other tables)
    print("\n[Step 2] Deleting main entity tables...")
    
    deleted = db.query(Event).delete()
    print(f"  ✓ events: {deleted} records deleted")
    total_deleted += deleted
    
    deleted = db.query(Dish).delete()
    print(f"  ✓ dishes: {deleted} records deleted")
    total_deleted += deleted
    
    # Step 3: Resource tables (products, tools)
    print("\n[Step 3] Deleting resource tables...")
    
    deleted = db.query(Product).delete()
    print(f"  ✓ products: {deleted} records deleted")
    total_deleted += deleted
    
    deleted = db.query(Tool).delete()
    print(f"  ✓ tools: {deleted} records deleted")
    total_deleted += deleted
    
    # Step 4: Menu system tables (categories before templates)
    print("\n[Step 4] Deleting menu system tables...")
    
    deleted = db.query(MenuCategory).delete()
    print(f"  ✓ menu_categories: {deleted} records deleted")
    total_deleted += deleted
    
    deleted = db.query(MenuTemplate).delete()
    print(f"  ✓ menu_templates: {deleted} records deleted")
    total_deleted += deleted
    
    # Step 5: Lookup data (configuration/metadata)
    print("\n[Step 5] Deleting lookup/configuration tables...")
    
    deleted = db.query(LookupData).delete()
    print(f"  ✓ lookup_data: {deleted} records deleted")
    total_deleted += deleted
    
    # Commit all deletions
    db.commit()
    
    print("\n" + "=" * 70)
    print(f"✓ CLEAN WIPE COMPLETE - {total_deleted} total records deleted")
    print("=" * 70)
    print("\nDatabase is now completely empty.")
    print("\nNext Steps:")
    print("1. Run seed_menu_templates.py to recreate menu structure")
    print("2. Run populate_db.py to add fresh demo data")
    print("3. Or manually add your production data")
    print()


def verify_empty(db: Session):
    """
    Verify that all tables are actually empty after wipe.
    """
    print("\n" + "=" * 70)
    print("VERIFICATION - Checking if database is empty...")
    print("=" * 70)
    
    tables_to_check = [
        ("event_dishes", EventDish),
        ("event_owners", EventOwner),
        ("events", Event),
        ("dish_ingredients", DishIngredient),
        ("dish_equipment", DishEquipment),
        ("serving_dishes", ServingDish),
        ("dish_menu_mappings", DishMenuMapping),
        ("dishes", Dish),
        ("products", Product),
        ("tools", Tool),
        ("menu_categories", MenuCategory),
        ("menu_templates", MenuTemplate),
        ("lookup_data", LookupData),
    ]
    
    all_empty = True
    for table_name, model in tables_to_check:
        count = db.query(model).count()
        status = "✓ EMPTY" if count == 0 else f"⚠️  {count} records remaining"
        print(f"  {table_name:<25} {status}")
        if count > 0:
            all_empty = False
    
    print("=" * 70)
    if all_empty:
        print("✓ All tables are empty - database successfully wiped!")
    else:
        print("⚠️  Some tables still have data - check foreign key constraints")
    print("=" * 70)


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("⚠️  DANGER ZONE - COMPLETE DATABASE WIPE")
    print("=" * 70)
    print("\nThis script will DELETE ALL DATA from your database.")
    print("This includes:")
    print("  • All events and their associated data")
    print("  • All dishes and their recipes/ingredients")
    print("  • All products and inventory")
    print("  • All tools and equipment")
    print("  • All menu templates and categories")
    print("  • All lookup/configuration data")
    print("\n⚠️  THIS OPERATION CANNOT BE UNDONE!")
    print("=" * 70)
    
    response = input("\nType 'DELETE ALL DATA' to confirm: ")
    
    if response != "DELETE ALL DATA":
        print("\n❌ Wipe cancelled - database unchanged.")
        sys.exit(0)
    
    print("\n🔄 Starting clean wipe...")
    
    db = SessionLocal()
    try:
        clean_wipe_all_data(db)
        verify_empty(db)
    except Exception as e:
        print(f"\n❌ Error during wipe: {e}")
        print("\nRolling back changes...")
        db.rollback()
        print("❌ Wipe failed - database may be in inconsistent state")
        sys.exit(1)
    finally:
        db.close()
    
    print("\n✓ Script completed successfully")
