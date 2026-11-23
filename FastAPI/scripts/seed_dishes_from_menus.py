"""
Seed Dishes from Full Menu Data
Populates dishes and dish_menu_mappings based on complete menu specifications.
"""

import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.dish import Dish, DishMenuMapping
from app.models.menu_template import MenuTemplate, MenuCategory


def seed_dishes_and_mappings(db: Session):
    """
    Seed all dishes and their menu mappings based on the full menu data.
    """
    
    print("🌱 Starting dish and mapping seeding...")
    
    # Clear existing dishes and mappings
    existing_dishes = db.query(Dish).count()
    if existing_dishes > 0:
        print(f"⚠️  Found {existing_dishes} existing dishes. Clearing...")
        db.query(DishMenuMapping).delete()
        db.query(Dish).delete()
        db.commit()
    
    created_dishes = 0
    created_mappings = 0
    
    # ===== SALADS (Shared across SHABBAT, DAIRY_MENU, SWEET_TABLE) =====
    print("\n📁 Creating Salads...")
    
    salads_data = [
        "גזר חריף ונשנושים", "גזר סלרי ופלפלים מתוק", "תירס בייבי ונבטים גזר",
        "גזר שום ושמיר", "גזר צ'ילי וירוקים", "גזר חמוציות ופקאן",
        "סלט וולדורף", "פטריות/נבטים הדר ושקדים", "חסה דובדבנים ובצל סגול",
        "חסה פירות מתוק", "כרוב עם שקדים קלויים", "כרוב עשבי תיבול",
        "כרוב מעורב עם אגוזים", "כרוב סגול חמוץ מתוק", "רצועות סלק ותפוח",
        "חצילים בסגנון 'כבד'", "סירות חצילים טחינה", "חצילים עגבניות חריף",
        "חצילים טחינה צלויים", "קוביות חצילים כבושים", "חצילים במיונז",
        "חצילים בטטה צ'ילי מתוק", "בטטה סילאן ושומשום", "טחינה עשבי תיבול",
        "חומוס קלאסי", "טפנד זיתים", "מטבוחה חריפה", "סלט ערבי",
        "דובדבנים בצל וגרעיני חמניה", "מיקס מלפפונים", "מלפפון כבוש שמיר",
        "חמוטה (ירקות כבושים מעורבים)", "מלפפונים במיונז", "זיתים ברוטב אדום",
        "זיתים ופטריות כבושים", "טבולה קלאסי", "בורגול עשבי תיבול מתוק",
        "קינואה ירוקה", "סלט ישראלי"
    ]
    
    salad_dishes = []
    for i, name in enumerate(salads_data, 1):
        dish = Dish(
            name=name,
            category="סלטים",
            kosher_type="פרווה",
            is_active=1,
            serving_size=1.0,
            estimated_price=8.0
        )
        db.add(dish)
        db.flush()
        salad_dishes.append(dish)
        created_dishes += 1
        
        # Map to SHABBAT (quota: 5)
        mapping = DishMenuMapping(
            dish_id=dish.id,
            menu_type="SHABBAT",
            category_name="salads",
            is_upgrade=False,
            display_order=i
        )
        db.add(mapping)
        created_mappings += 1
        
        # Map to SWEET_TABLE (quota: 5)
        mapping = DishMenuMapping(
            dish_id=dish.id,
            menu_type="SWEET_TABLE",
            category_name="salads",
            is_upgrade=False,
            display_order=i
        )
        db.add(mapping)
        created_mappings += 1
    
    print(f"   ✅ Created {len(salad_dishes)} salad dishes")
    
    # ===== DAIRY SALADS (Additional for DAIRY_MENU) =====
    print("\n📁 Creating Dairy-Specific Salads...")
    
    dairy_salads = [
        ("סלט יווני", "Greek"),
        ("סלט קלאסי", "Classic"),
        ("אגוזים וסלק", "Nut & Beet"),
        ("כפרי (דבש/חרדל)", "Country (Honey/Mustard)"),
        ("בריאות (פירות/אגוזים)", "Health (Fruit/Nuts)")
    ]
    
    for i, (name_he, name_en) in enumerate(dairy_salads, len(salads_data) + 1):
        dish = Dish(
            name=name_he,
            description=name_en,
            category="סלטים",
            kosher_type="חלבי",
            is_active=1,
            serving_size=1.0,
            estimated_price=12.0
        )
        db.add(dish)
        db.flush()
        created_dishes += 1
        
        # Map only to DAIRY_MENU
        mapping = DishMenuMapping(
            dish_id=dish.id,
            menu_type="DAIRY_MENU",
            category_name="salads",
            is_upgrade=False,
            display_order=i
        )
        db.add(mapping)
        created_mappings += 1
    
    print(f"   ✅ Created {len(dairy_salads)} dairy salad dishes")
    
    # ===== FISH (SHABBAT & DAIRY_MENU) =====
    print("\n📁 Creating Fish Dishes...")
    
    fish_salmon = [
        ("סלמון פסטו", "Salmon Pesto"),
        ("סלמון צ'ילי", "Salmon Chili"),
        ("סלמון חרדל/דבש", "Salmon Mustard/Honey"),
        ("סלמון עשבי תיבול", "Salmon Herbs"),
        ("סלמון טריאקי", "Salmon Teriyaki")
    ]
    
    fish_musht = [
        ("מושט חריף", "Musht Spicy"),
        ("מושט מתוק", "Musht Sweet"),
        ("מושט פירורי לחם", "Musht Crumbs")
    ]
    
    for i, (name_he, name_en) in enumerate(fish_salmon + fish_musht, 1):
        dish = Dish(
            name=name_he,
            description=name_en,
            category="דגים",
            kosher_type="פרווה",
            is_active=1,
            serving_size=1.0,
            estimated_price=35.0
        )
        db.add(dish)
        db.flush()
        created_dishes += 1
        
        # Map to SHABBAT fish category (quota: 2)
        mapping = DishMenuMapping(
            dish_id=dish.id,
            menu_type="SHABBAT",
            category_name="fish",
            is_upgrade=False,
            display_order=i
        )
        db.add(mapping)
        created_mappings += 1
        
        # Map to DAIRY_MENU fish category (quota: 1)
        mapping = DishMenuMapping(
            dish_id=dish.id,
            menu_type="DAIRY_MENU",
            category_name="fish",
            is_upgrade=False,
            display_order=i
        )
        db.add(mapping)
        created_mappings += 1
    
    # Add "All Salmon Menu" upgrade for SHABBAT
    all_salmon = Dish(
        name="תפריט סלמון מלא",
        description="All Salmon Menu - Premium Upgrade",
        category="דגים",
        kosher_type="פרווה",
        is_active=1,
        serving_size=1.0,
        estimated_price=50.0
    )
    db.add(all_salmon)
    db.flush()
    created_dishes += 1
    
    mapping = DishMenuMapping(
        dish_id=all_salmon.id,
        menu_type="SHABBAT",
        category_name="fish",
        is_upgrade=True,
        extra_charge=15.0,
        display_order=100
    )
    db.add(mapping)
    created_mappings += 1
    
    print(f"   ✅ Created {len(fish_salmon) + len(fish_musht) + 1} fish dishes")
    
    # ===== MAIN COURSES (SHABBAT) =====
    print("\n📁 Creating Shabbat Main Courses...")
    
    shabbat_mains = [
        ("רולדה בקר", "Beef Roll"),
        ("רולדה הודו", "Turkey Roll"),
        ("פרגית", "Pargit"),
        ("עוף מתוק", "Sweet Chicken"),
        ("עוף ברביקיו", "BBQ Chicken"),
        ("עוף חריף", "Spicy Chicken"),
        ("שניצל", "Schnitzel"),
        ("שניצל מיני", "Mini Schnitzel"),
        ("חזה פסטרמה", "Pastrami Breast"),
        ("סטייק חריף", "Spicy Steak"),
        ("סטייק מתוק", "Sweet Steak"),
        ("סטייק בציפוי אגוזים", "Nut-Crust Steak"),
        ("חזה ממולא", "Stuffed Breast"),
        ("צ'ולנט", "Cholent")
    ]
    
    for i, (name_he, name_en) in enumerate(shabbat_mains, 1):
        dish = Dish(
            name=name_he,
            description=name_en,
            category="עיקרית",
            kosher_type="בשרי",
            is_active=1,
            serving_size=1.0,
            estimated_price=40.0
        )
        db.add(dish)
        db.flush()
        created_dishes += 1
        
        # Map to SHABBAT main_course (quota: 2, or 3 if >80 guests)
        mapping = DishMenuMapping(
            dish_id=dish.id,
            menu_type="SHABBAT",
            category_name="main_course",
            is_upgrade=False,
            display_order=i
        )
        db.add(mapping)
        created_mappings += 1
    
    # Add "Beef Slices #5" upgrade
    beef_5 = Dish(
        name="פרוסות בקר #5",
        description="Beef Slices #5 - Premium Upgrade",
        category="עיקרית",
        kosher_type="בשרי",
        is_active=1,
        serving_size=1.0,
        estimated_price=60.0
    )
    db.add(beef_5)
    db.flush()
    created_dishes += 1
    
    mapping = DishMenuMapping(
        dish_id=beef_5.id,
        menu_type="SHABBAT",
        category_name="main_course",
        is_upgrade=True,
        extra_charge=20.0,
        display_order=100
    )
    db.add(mapping)
    created_mappings += 1
    
    # Also map to MEAT_MENU
    mapping = DishMenuMapping(
        dish_id=beef_5.id,
        menu_type="MEAT_MENU",
        category_name="main_course",
        is_upgrade=True,
        extra_charge=20.0,
        display_order=100
    )
    db.add(mapping)
    created_mappings += 1
    
    print(f"   ✅ Created {len(shabbat_mains) + 1} main course dishes")
    
    # ===== SIDES (Shared across SHABBAT, SWEET_TABLE) =====
    print("\n📁 Creating Side Dishes...")
    
    sides_data = [
        ("קניש ירקות", "Veggie Knish"),
        ("צ'ולנט", "Cholent"),
        ("קוגל ירושלמי", "Jerusalem Kugel"),
        ("קוגל תפוחי אדמה", "Potato Kugel"),
        ("אורז (שקדים/ירקות/עשבי תיבול)", "Rice (Almonds/Veg/Herbs)"),
        ("קוסקוס", "Couscous"),
        ("קינואה", "Quinoa"),
        ("טבולה", "Tabouli"),
        ("בורגול", "Bulgur"),
        ("תפוחי אדמה חריפים", "Spicy Potatoes"),
        ("תפוחי אדמה שום", "Garlic Potatoes"),
        ("מופקה (אטריות מוקפצות)", "Mopkah (Stir-fry Noodles)"),
        ("סופלה בטטה", "Sweet Potato Soufflé"),
        ("סופלה בצל", "Onion Soufflé"),
        ("סופלה תפוח/דבש", "Apple/Honey Soufflé"),
        ("שעועית פירורי לחם", "Beans with Crumbs"),
        ("שעועית עגבניות", "Beans in Tomato"),
        ("אנטיפסטי", "Antipasti")
    ]
    
    for i, (name_he, name_en) in enumerate(sides_data, 1):
        dish = Dish(
            name=name_he,
            description=name_en,
            category="תוספת",
            kosher_type="פרווה",
            is_active=1,
            serving_size=1.0,
            estimated_price=15.0
        )
        db.add(dish)
        db.flush()
        created_dishes += 1
        
        # Map to SHABBAT sides (quota: 3)
        mapping = DishMenuMapping(
            dish_id=dish.id,
            menu_type="SHABBAT",
            category_name="sides",
            is_upgrade=False,
            display_order=i
        )
        db.add(mapping)
        created_mappings += 1
        
        # Map to SWEET_TABLE sides (quota: unlimited based on description)
        mapping = DishMenuMapping(
            dish_id=dish.id,
            menu_type="SWEET_TABLE",
            category_name="side_trays",
            is_upgrade=False,
            display_order=i
        )
        db.add(mapping)
        created_mappings += 1
    
    print(f"   ✅ Created {len(sides_data)} side dishes")
    
    # ===== PASTRIES (SWEET_TABLE) =====
    print("\n📁 Creating Pastry Dishes...")
    
    pastries_data = [
        ("בלינצ'ס תפוחי אדמה", "Potato Blintzes"),
        ("טורטייה ירקות", "Veggie Tortilla"),
        ("בורקס סהרונים", "Moon Bourekas"),
        ("פחזניה ירקות", "Veggie Cream Puff"),
        ("קרואסון ירקות", "Veggie Croissant"),
        ("מוסקה (פרווה)", "Moussaka (Parve)"),
        ("פשטידה אישית ירקות", "Personal Veggie Pie"),
        ("קיש אישי", "Personal Quiche"),
        ("פלפל ממולא", "Stuffed Pepper")
    ]
    
    for i, (name_he, name_en) in enumerate(pastries_data, 1):
        dish = Dish(
            name=name_he,
            description=name_en,
            category="מאפה",
            kosher_type="פרווה",
            is_active=1,
            serving_size=1.0,
            estimated_price=18.0
        )
        db.add(dish)
        db.flush()
        created_dishes += 1
        
        # Map to SWEET_TABLE pastries (quota: 3)
        mapping = DishMenuMapping(
            dish_id=dish.id,
            menu_type="SWEET_TABLE",
            category_name="pastries",
            is_upgrade=False,
            display_order=i
        )
        db.add(mapping)
        created_mappings += 1
    
    print(f"   ✅ Created {len(pastries_data)} pastry dishes")
    
    # ===== SOUPS (DAIRY_MENU) =====
    print("\n📁 Creating Soup Dishes...")
    
    soups_data = [
        ("מרק כתום (בטטה)", "Orange (Sweet Potato)"),
        ("מרק בצל ופרוסות לחם", "Onion & Croutons"),
        ("מרק פטריות ושעורה", "Mushroom & Barley"),
        ("מרק ירקות", "Vegetable"),
        ("מרק קטניות", "Legume")
    ]
    
    for i, (name_he, name_en) in enumerate(soups_data, 1):
        dish = Dish(
            name=name_he,
            description=name_en,
            category="מרק",
            kosher_type="חלבי",
            is_active=1,
            serving_size=1.0,
            estimated_price=12.0
        )
        db.add(dish)
        db.flush()
        created_dishes += 1
        
        # Map to DAIRY_MENU first_course (quota: 1)
        mapping = DishMenuMapping(
            dish_id=dish.id,
            menu_type="DAIRY_MENU",
            category_name="first_course",
            is_upgrade=False,
            display_order=i
        )
        db.add(mapping)
        created_mappings += 1
    
    print(f"   ✅ Created {len(soups_data)} soup dishes")
    
    # ===== DAIRY MAINS =====
    print("\n📁 Creating Dairy Main Dishes...")
    
    dairy_mains = [
        ("לזניה רוזה", "Rosa Lasagna", False),
        ("פסטה אלפרדו", "Alfredo Pasta", False),
        ("גרטן תפוחי אדמה אלפרדו", "Alfredo Gratin Potatoes", False),
        ("תפוחי אדמה שום", "Garlic Potatoes", False),
        ("צ'יפס ביתי", "Home Fries", False),
        ("פשטידת בטטה", "Sweet Potato Pie", False),
        ("פשטידת פטריות", "Mushroom Pie", False),
        ("קיש גבינות", "Cheese Quiche", False),
        ("פשטידת זיתים וקוטג'", "Olive & Cottage Pie", False),
        ("דג בציפוי אגוזים", "Nut-crust Fish", True),  # Upgrade
        ("פלפלים סילאן", "Silan Peppers", True),  # Upgrade
        ("תוספת גבינה", "Extra Cheese topping", True)  # Upgrade
    ]
    
    for i, (name_he, name_en, is_upgrade) in enumerate(dairy_mains, 1):
        dish = Dish(
            name=name_he,
            description=name_en,
            category="עיקרית",
            kosher_type="חלבי",
            is_active=1,
            serving_size=1.0,
            estimated_price=30.0 if not is_upgrade else 40.0
        )
        db.add(dish)
        db.flush()
        created_dishes += 1
        
        # Map to DAIRY_MENU main_course (quota: 2)
        mapping = DishMenuMapping(
            dish_id=dish.id,
            menu_type="DAIRY_MENU",
            category_name="main_course",
            is_upgrade=is_upgrade,
            extra_charge=10.0 if is_upgrade else None,
            display_order=100 + i if is_upgrade else i
        )
        db.add(mapping)
        created_mappings += 1
    
    print(f"   ✅ Created {len(dairy_mains)} dairy main dishes")
    
    # ===== DESSERTS (SHABBAT, DAIRY_MENU) =====
    print("\n📁 Creating Dessert Dishes...")
    
    desserts_data = [
        ("מוס שוקולד", "Chocolate Mousse"),
        ("טירמיסו", "Tiramisu"),
        ("עוגת גבינה", "Cheesecake"),
        ("פירות עונה", "Seasonal Fruits"),
        ("גלידה", "Ice Cream")
    ]
    
    for i, (name_he, name_en) in enumerate(desserts_data, 1):
        dish = Dish(
            name=name_he,
            description=name_en,
            category="קינוח",
            kosher_type="חלבי",
            is_active=1,
            serving_size=1.0,
            estimated_price=15.0
        )
        db.add(dish)
        db.flush()
        created_dishes += 1
        
        # Map to SHABBAT desserts (quota: 2)
        mapping = DishMenuMapping(
            dish_id=dish.id,
            menu_type="SHABBAT",
            category_name="desserts",
            is_upgrade=False,
            display_order=i
        )
        db.add(mapping)
        created_mappings += 1
        
        # Map to DAIRY_MENU desserts (quota: 1)
        mapping = DishMenuMapping(
            dish_id=dish.id,
            menu_type="DAIRY_MENU",
            category_name="desserts",
            is_upgrade=False,
            display_order=i
        )
        db.add(mapping)
        created_mappings += 1
    
    print(f"   ✅ Created {len(desserts_data)} dessert dishes")
    
    # ===== MEAT TRAYS =====
    print("\n📁 Creating Meat Tray Items...")
    
    meat_trays = [
        ("בגט אסאדו", "Asado Baguette"),
        ("בגט עוף", "Chicken Baguette"),
        ("בגט שניצל", "Schnitzel Baguette"),
        ("המבורגר מיני", "Mini Burger"),
        ("סנדוויץ' סושי", "Sushi Sandwich"),
        ("כבד (1 ליטר)", "Liver (1L)"),
        ("רצועות שניצל (1 ליטר)", "Schnitzel strips (1L)")
    ]
    
    for i, (name_he, name_en) in enumerate(meat_trays, 1):
        dish = Dish(
            name=name_he,
            description=name_en,
            category="מגש",
            kosher_type="בשרי",
            is_active=1,
            serving_size=1.0,
            estimated_price=120.0
        )
        db.add(dish)
        db.flush()
        created_dishes += 1
        
        # Map to MEAT_TRAYS
        mapping = DishMenuMapping(
            dish_id=dish.id,
            menu_type="MEAT_TRAYS",
            category_name="meat_trays",
            is_upgrade=False,
            display_order=i
        )
        db.add(mapping)
        created_mappings += 1
    
    print(f"   ✅ Created {len(meat_trays)} meat tray items")
    
    # Commit all changes
    db.commit()
    
    print(f"\n✨ Seeding complete!")
    print(f"   Dishes created: {created_dishes}")
    print(f"   Menu mappings created: {created_mappings}")
    print(f"\n📋 Database is ready with full menu data!")


def main():
    """Main execution function"""
    db = SessionLocal()
    try:
        seed_dishes_and_mappings(db)
    except Exception as e:
        print(f"❌ Error during seeding: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
