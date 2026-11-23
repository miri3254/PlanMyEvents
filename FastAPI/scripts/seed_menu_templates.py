"""
Seed Menu Templates Script
Populates the menu_templates and menu_categories tables with the 6 core menu types.
This creates the structure; actual dishes will be populated after receiving menu details.
"""

import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models.menu_template import MenuTemplate, MenuCategory


def seed_menu_templates(db: Session):
    """
    Seed the 6 core menu types with placeholder categories.
    Categories will be updated once actual menu text is provided.
    """
    
    print("🌱 Starting menu template seeding...")
    
    # Clear existing templates (if any)
    existing_count = db.query(MenuTemplate).count()
    if existing_count > 0:
        print(f"⚠️  Found {existing_count} existing templates. Clearing...")
        db.query(MenuCategory).delete()
        db.query(MenuTemplate).delete()
        db.commit()
    
    # Define the 6 core menu types with their Hebrew names
    menu_templates = [
        {
            "menu_type": "SHABBAT",
            "name_hebrew": "שבת מלא",
            "description": "תפריט שבת מלא עם כל המנות המסורתיות - ליל שבת ובוקר",
            "categories": [
                {"name": "salads", "name_hebrew": "סלטים", "display_order": 1, "quota": 5, "is_required": True},
                {"name": "fish", "name_hebrew": "דגים (מנה ראשונה)", "display_order": 2, "quota": 2, "is_required": True},
                {"name": "main_course", "name_hebrew": "עיקריות", "display_order": 3, "quota": 2, "is_required": True},
                {"name": "sides", "name_hebrew": "תוספות", "display_order": 4, "quota": 3, "is_required": True},
                {"name": "desserts", "name_hebrew": "קינוחים", "display_order": 5, "quota": 1, "is_required": True},
            ]
        },
        {
            "menu_type": "MEAT_MENU",
            "name_hebrew": "תפריט בשרי",
            "description": "תפריט בשרי סטנדרטי לאירועים",
            "categories": [
                {"name": "salads", "name_hebrew": "סלטים", "display_order": 1, "quota": 5, "is_required": True},
                {"name": "first_course", "name_hebrew": "ראשונות", "display_order": 2, "quota": 2, "is_required": True},
                {"name": "main_course", "name_hebrew": "עיקריות", "display_order": 3, "quota": 2, "is_required": True},
                {"name": "sides", "name_hebrew": "תוספות", "display_order": 4, "quota": 3, "is_required": True},
                {"name": "desserts", "name_hebrew": "קינוחים", "display_order": 5, "quota": 2, "is_required": True},
            ]
        },
        {
            "menu_type": "DAIRY_MENU",
            "name_hebrew": "תפריט חלבי",
            "description": "תפריט חלבי סטנדרטי לאירועים",
            "categories": [
                {"name": "salads", "name_hebrew": "סלטים", "display_order": 1, "quota": 5, "is_required": True},
                {"name": "first_course", "name_hebrew": "מרקים", "display_order": 2, "quota": 1, "is_required": True},
                {"name": "fish", "name_hebrew": "דגים", "display_order": 3, "quota": 1, "is_required": True},
                {"name": "main_course", "name_hebrew": "עיקריות (מאפה/גרטן)", "display_order": 4, "quota": 2, "is_required": True},
                {"name": "desserts", "name_hebrew": "קינוחים", "display_order": 5, "quota": 1, "is_required": True},
            ]
        },
        {
            "menu_type": "MEAT_TRAYS",
            "name_hebrew": "מגשי בשר",
            "description": "מגשי קייטרינג בשריים",
            "categories": [
                {"name": "meat_trays", "name_hebrew": "מגשי בשר", "display_order": 1, "quota": 3, "is_required": True},
                {"name": "salad_trays", "name_hebrew": "מגשי סלטים", "display_order": 2, "quota": 2, "is_required": True},
                {"name": "side_trays", "name_hebrew": "מגשי תוספות", "display_order": 3, "quota": 2, "is_required": True},
            ]
        },
        {
            "menu_type": "DAIRY_TRAYS",
            "name_hebrew": "מגשי חלב",
            "description": "מגשי קייטרינג חלביים",
            "categories": [
                {"name": "dairy_trays", "name_hebrew": "מגשי חלב", "display_order": 1, "quota": 3, "is_required": True},
                {"name": "fish_trays", "name_hebrew": "מגשי דגים", "display_order": 2, "quota": 2, "is_required": True},
                {"name": "salad_trays", "name_hebrew": "מגשי סלטים", "display_order": 3, "quota": 2, "is_required": True},
            ]
        },
        {
            "menu_type": "SWEET_TABLE",
            "name_hebrew": "שולחן מתוק",
            "description": "שולחן קינוחים ומתוקים",
            "categories": [
                {"name": "salads", "name_hebrew": "סלטים", "display_order": 1, "quota": 5, "is_required": True},
                {"name": "pastries", "name_hebrew": "מאפים", "display_order": 2, "quota": 3, "is_required": True},
                {"name": "side_trays", "name_hebrew": "תוספות", "display_order": 3, "quota": 0, "is_required": False},
            ]
        },
    ]
    
    # Create templates and categories
    created_templates = 0
    created_categories = 0
    
    for template_data in menu_templates:
        # Extract categories before creating template
        categories_data = template_data.pop("categories")
        
        # Create template
        template = MenuTemplate(**template_data)
        db.add(template)
        db.flush()  # Flush to get the template.id
        created_templates += 1
        
        print(f"✅ Created template: {template.name_hebrew} ({template.menu_type})")
        
        # Create categories for this template
        for cat_data in categories_data:
            category = MenuCategory(
                template_id=template.id,
                **cat_data
            )
            db.add(category)
            created_categories += 1
            print(f"   📁 Added category: {category.name_hebrew} (quota: {category.quota})")
    
    # Commit all changes
    db.commit()
    
    print(f"\n✨ Seeding complete!")
    print(f"   Templates created: {created_templates}")
    print(f"   Categories created: {created_categories}")
    print(f"\n📋 Next step: Provide menu text to populate dishes and dish_menu_mappings")


def main():
    """Main execution function"""
    db = SessionLocal()
    try:
        seed_menu_templates(db)
    except Exception as e:
        print(f"❌ Error during seeding: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
