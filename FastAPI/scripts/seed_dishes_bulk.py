"""
Bulk Insert Dishes Script
Imports dishes from JSON with proper upsert logic, ingredient handling, and menu mappings.
Follows strict transaction safety and enum validation.
"""

import sys
from pathlib import Path
import json

# Add parent directory to path to import app modules
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.core.database import SessionLocal, engine
from app.models.dish import Dish, DishIngredient, DishMenuMapping
from app.models.menu_template import MenuType


def validate_menu_type(menu_type_str: str) -> MenuType:
    """
    Validate and convert string menu_type to MenuType enum.
    Raises ValueError if invalid.
    """
    try:
        return MenuType[menu_type_str]
    except KeyError:
        raise ValueError(f"Invalid menu_type: {menu_type_str}. Valid values: {[e.name for e in MenuType]}")


def upsert_dish(db: Session, dish_data: dict) -> Dish:
    """
    Upsert a single dish: create if doesn't exist, update if exists.
    Returns the Dish instance (new or existing).
    """
    # Check if dish exists by name
    existing_dish = db.query(Dish).filter(Dish.name == dish_data["name"]).first()
    
    if existing_dish:
        print(f"  ♻️  Updating existing dish: {dish_data['name']}")
        # Update existing fields
        existing_dish.category = dish_data.get("category", existing_dish.category)
        existing_dish.kosher_type = dish_data.get("kosher_type", existing_dish.kosher_type)
        existing_dish.description = dish_data.get("description", existing_dish.description)
        existing_dish.serving_size = dish_data.get("serving_size", existing_dish.serving_size)
        existing_dish.serving_description = dish_data.get("serving_description", existing_dish.serving_description)
        existing_dish.waiter_notes = dish_data.get("waiter_notes", existing_dish.waiter_notes)
        existing_dish.is_active = dish_data.get("is_active", existing_dish.is_active)
        existing_dish.price_per_unit = dish_data.get("price_per_unit", existing_dish.price_per_unit)
        existing_dish.estimated_price = dish_data.get("estimated_price", existing_dish.estimated_price)
        existing_dish.client_price = dish_data.get("client_price", existing_dish.client_price)
        existing_dish.image_url = dish_data.get("image_url", existing_dish.image_url)
        return existing_dish
    else:
        print(f"  ✨ Creating new dish: {dish_data['name']}")
        # Create new dish
        new_dish = Dish(
            name=dish_data["name"],
            category=dish_data.get("category", ""),
            kosher_type=dish_data.get("kosher_type", "פרווה"),
            description=dish_data.get("description"),
            serving_size=dish_data.get("serving_size", 1.0),
            serving_description=dish_data.get("serving_description"),
            waiter_notes=dish_data.get("waiter_notes"),
            is_active=dish_data.get("is_active", 1),
            price_per_unit=dish_data.get("price_per_unit"),
            estimated_price=dish_data.get("estimated_price"),
            client_price=dish_data.get("client_price"),
            image_url=dish_data.get("image_url")
        )
        db.add(new_dish)
        return new_dish


def sync_ingredients(db: Session, dish: Dish, ingredients_data: list):
    """
    Clear existing ingredients and add new ones from JSON.
    Must be called within a transaction.
    """
    # Clear existing ingredients
    db.query(DishIngredient).filter(DishIngredient.dish_id == dish.id).delete()
    
    # Add new ingredients
    for ingredient_data in ingredients_data:
        new_ingredient = DishIngredient(
            dish_id=dish.id,
            product_id=ingredient_data.get("product_id"),  # May be None
            name=ingredient_data.get("name"),
            quantity=ingredient_data.get("quantity", 1.0),
            unit=ingredient_data.get("unit", "יחידות")
        )
        db.add(new_ingredient)
    
    if ingredients_data:
        print(f"    🥗 Synced {len(ingredients_data)} ingredients")


def sync_menu_mappings(db: Session, dish: Dish, mappings_data: list):
    """
    Sync menu mappings: update existing or create new.
    Does NOT delete existing mappings that are not in this JSON.
    """
    for mapping_data in mappings_data:
        # Validate and convert menu_type to enum
        menu_type_enum = validate_menu_type(mapping_data["menu_type"])
        category_name = mapping_data["category_name"]
        
        # Check if this specific mapping already exists
        existing_mapping = db.query(DishMenuMapping).filter(
            DishMenuMapping.dish_id == dish.id,
            DishMenuMapping.menu_type == menu_type_enum,
            DishMenuMapping.category_name == category_name
        ).first()
        
        if existing_mapping:
            # Update existing mapping
            existing_mapping.display_order = mapping_data.get("display_order", existing_mapping.display_order)
            existing_mapping.client_price = mapping_data.get("client_price", existing_mapping.client_price)
            existing_mapping.estimated_price = mapping_data.get("estimated_price", existing_mapping.estimated_price)
            existing_mapping.is_upgrade = mapping_data.get("is_upgrade", existing_mapping.is_upgrade)
            existing_mapping.extra_charge = mapping_data.get("extra_charge", existing_mapping.extra_charge)
        else:
            # Create new mapping
            new_mapping = DishMenuMapping(
                dish_id=dish.id,
                menu_type=menu_type_enum,
                category_name=category_name,
                display_order=mapping_data.get("display_order", 0),
                client_price=mapping_data.get("client_price"),
                estimated_price=mapping_data.get("estimated_price"),
                is_upgrade=mapping_data.get("is_upgrade", False),
                extra_charge=mapping_data.get("extra_charge", 0.0)
            )
            db.add(new_mapping)
    
    if mappings_data:
        print(f"    📋 Synced {len(mappings_data)} menu mappings")


def bulk_import_dishes(db: Session, dishes_json: dict):
    """
    Main function to bulk import dishes from JSON.
    Wraps everything in a transaction for data integrity.
    """
    items = dishes_json.get("items", [])
    print(f"\n🚀 Starting bulk import of {len(items)} dishes...\n")
    
    success_count = 0
    error_count = 0
    
    try:
        for idx, dish_data in enumerate(items, 1):
            try:
                print(f"[{idx}/{len(items)}] Processing: {dish_data['name']}")
                
                # Step 1: Upsert dish
                dish = upsert_dish(db, dish_data)
                
                # Step 2: Flush to get dish.id (critical for foreign keys)
                db.flush()
                
                # Step 3: Sync ingredients (clear old, add new)
                ingredients_data = dish_data.get("ingredients", [])
                if ingredients_data:
                    sync_ingredients(db, dish, ingredients_data)
                
                # Step 4: Sync menu mappings (update or create, don't delete)
                mappings_data = dish_data.get("menu_mappings", [])
                if mappings_data:
                    sync_menu_mappings(db, dish, mappings_data)
                
                success_count += 1
                print(f"    ✅ Success!\n")
                
            except ValueError as ve:
                print(f"    ❌ Validation Error: {ve}\n")
                error_count += 1
                raise  # Re-raise to trigger rollback
            except Exception as e:
                print(f"    ❌ Error processing dish: {e}\n")
                error_count += 1
                raise  # Re-raise to trigger rollback
        
        # Commit transaction if all succeeded
        db.commit()
        print(f"\n🎉 Bulk import completed successfully!")
        print(f"   ✅ {success_count} dishes processed")
        
    except Exception as e:
        # Rollback on any error
        db.rollback()
        print(f"\n❌ Transaction rolled back due to error!")
        print(f"   Error: {e}")
        print(f"   ✅ {success_count} dishes processed before error")
        print(f"   ❌ {error_count} dishes failed")
        raise


def main():
    """
    Main entry point for the script.
    Reads JSON from stdin or file.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Bulk import dishes from JSON")
    parser.add_argument("--file", type=str, help="Path to JSON file (or use stdin)")
    parser.add_argument("--json", type=str, help="JSON string directly")
    args = parser.parse_args()
    
    # Read JSON
    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            dishes_json = json.load(f)
    elif args.json:
        dishes_json = json.loads(args.json)
    else:
        print("📥 Reading JSON from stdin (paste JSON and press Ctrl+D on Unix or Ctrl+Z on Windows)...")
        dishes_json = json.load(sys.stdin)
    
    # Create database session with autoflush=False
    db = SessionLocal()
    try:
        bulk_import_dishes(db, dishes_json)
    finally:
        db.close()


if __name__ == "__main__":
    main()
