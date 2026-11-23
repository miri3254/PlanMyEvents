"""
סקריפט למילוי DB בנתוני דוגמה
"""
from datetime import datetime, timedelta
from app.core.database import SessionLocal, init_db
from app.models.event import Event, EventDish, EventOwner
from app.models.dish import Dish, DishIngredient, DishEquipment, ServingDish
from app.models.product import Product, ProductCategory
from app.models.tool import Tool
from app.models.menu_template import MenuType
from app.services.lookup_init import initialize_lookup_data


def clear_all_data(db):
    """מחיקת כל הנתונים"""
    print("🗑️  מוחק נתונים קודמים...")
    db.query(EventDish).delete()
    db.query(EventOwner).delete()
    db.query(Event).delete()
    db.query(DishIngredient).delete()
    db.query(DishEquipment).delete()
    db.query(ServingDish).delete()
    db.query(Dish).delete()
    db.query(Product).delete()
    db.query(Tool).delete()
    db.commit()
    print("✅ נתונים קודמים נמחקו")


def populate_products(db):
    """מילוי מוצרים"""
    print("📦 ממלא מוצרים...")
    
    # יצירת קטגוריות מוצרים
    category_names = ["חלבי", "בשרי", "ירקות", "תבלינים ובסיס", "דגים"]
    categories = {}
    for name in category_names:
        cat = db.query(ProductCategory).filter(ProductCategory.name == name).first()
        if not cat:
            cat = ProductCategory(name=name)
            db.add(cat)
            db.flush()
        categories[name] = cat.id
    
    def make_product(name, cat_name, **kwargs):
        return Product(name=name, category_id=categories[cat_name], **kwargs)
    
    products = [
        # חלבי
        make_product("גבינה צהובה", "חלבי", unit="ק״ג", price_per_unit=45.0, 
                package_quantity=0.25, estimated_price=11.25,
                quantity_in_stock=15, min_stock_level=5, inventory_status="במלאי", 
                supplier="תנובה", kosher_type="חלבי"),
        make_product("חלב 3%", "חלבי", unit="ליטר", price_per_unit=6.5, 
                package_quantity=1.0, estimated_price=6.50,
                quantity_in_stock=25, min_stock_level=10, inventory_status="במלאי", 
                supplier="תנובה", kosher_type="חלבי"),
        make_product("שמנת מתוקה", "חלבי", unit="ליטר", price_per_unit=12.0, 
                package_quantity=0.5, estimated_price=6.00,
                quantity_in_stock=8, min_stock_level=5, inventory_status="במלאי", 
                supplier="תנובה", kosher_type="חלבי"),
        make_product("חמאה", "חלבי", unit="ק״ג", price_per_unit=28.0, 
                package_quantity=0.25, estimated_price=7.00,
                quantity_in_stock=4, min_stock_level=5, inventory_status="מלאי-נמוך", 
                supplier="תנובה", kosher_type="חלבי"),
        make_product("גבינה לבנה 5%", "חלבי", unit="ק״ג", price_per_unit=18.0, 
                package_quantity=0.5, estimated_price=9.00,
                quantity_in_stock=12, min_stock_level=5, inventory_status="במלאי", 
                supplier="תנובה", kosher_type="חלבי"),
        
        # בשרי
        make_product("חזה עוף", "בשרי", unit="ק״ג", price_per_unit=32.0, 
                package_quantity=1.0, estimated_price=32.00,
                quantity_in_stock=20, min_stock_level=10, inventory_status="במלאי", 
                supplier="עוף טרי", kosher_type="בשרי"),
        make_product("בשר טחון", "בשרי", unit="ק״ג", price_per_unit=42.0, 
                package_quantity=1.0, estimated_price=42.00,
                quantity_in_stock=3, min_stock_level=5, inventory_status="מלאי-נמוך", 
                supplier="מעדני הצפון", kosher_type="בשרי"),
        make_product("שניצל עוף", "בשרי", unit="ק״ג", price_per_unit=38.0, 
                package_quantity=1.0, estimated_price=38.00,
                quantity_in_stock=18, min_stock_level=8, inventory_status="במלאי", 
                supplier="עוף טרי", kosher_type="בשרי"),
        make_product("כבד עוף", "בשרי", unit="ק״ג", price_per_unit=15.0, 
                package_quantity=1.0, estimated_price=15.00,
                quantity_in_stock=5, min_stock_level=3, inventory_status="במלאי", 
                supplier="עוף טרי", kosher_type="בשרי"),
        
        # ירקות ופירות
        make_product("עגבניות", "ירקות", unit="ק״ג", price_per_unit=8.0, 
                package_quantity=1.0, estimated_price=8.00,
                quantity_in_stock=25, min_stock_level=10, inventory_status="במלאי", 
                supplier="ירקות הגליל"),
        make_product("מלפפונים", "ירקות", unit="ק״ג", price_per_unit=6.0, 
                package_quantity=1.0, estimated_price=6.00,
                quantity_in_stock=20, min_stock_level=10, inventory_status="במלאי", 
                supplier="ירקות הגליל"),
        make_product("בצל", "ירקות", unit="ק״ג", price_per_unit=4.0, 
                package_quantity=1.0, estimated_price=4.00,
                quantity_in_stock=30, min_stock_level=15, inventory_status="במלאי", 
                supplier="ירקות הגליל"),
        make_product("שום", "ירקות", unit="ק״ג", price_per_unit=18.0, 
                package_quantity=0.5, estimated_price=9.00,
                quantity_in_stock=2, min_stock_level=5, inventory_status="מלאי-נמוך", 
                supplier="ירקות הגליל"),
        make_product("פלפל אדום", "ירקות", unit="ק״ג", price_per_unit=12.0, 
                package_quantity=1.0, estimated_price=12.00,
                quantity_in_stock=10, min_stock_level=5, inventory_status="במלאי", 
                supplier="ירקות הגליל"),
        make_product("חסה", "ירקות", unit="יחידות", price_per_unit=5.0, 
                package_quantity=1.0, estimated_price=5.00,
                quantity_in_stock=15, min_stock_level=8, inventory_status="במלאי", 
                supplier="ירקות הגליל"),
        
        # תבלינים ובסיס
        make_product("קמח לבן", "תבלינים ובסיס", unit="ק״ג", price_per_unit=5.0, 
                package_quantity=1.0, estimated_price=5.00,
                quantity_in_stock=50, min_stock_level=20, inventory_status="במלאי", 
                supplier="טחנת קמח", kosher_type="פרווה"),
        make_product("סוכר", "תבלינים ובסיס", unit="ק״ג", price_per_unit=4.0, 
                package_quantity=1.0, estimated_price=4.00,
                quantity_in_stock=40, min_stock_level=20, inventory_status="במלאי", 
                supplier="סוגת", kosher_type="פרווה"),
        make_product("מלח", "תבלינים ובסיס", unit="ק״ג", price_per_unit=2.0, 
                package_quantity=1.0, estimated_price=2.00,
                quantity_in_stock=25, min_stock_level=10, inventory_status="במלאי", 
                supplier="מלח הארץ", kosher_type="פרווה"),
        make_product("שמן זית", "תבלינים ובסיס", unit="ליטר", price_per_unit=35.0, 
                package_quantity=1.0, estimated_price=35.00,
                quantity_in_stock=8, min_stock_level=5, inventory_status="במלאי", 
                supplier="זיתי הכרמל", kosher_type="פרווה"),
        make_product("אורז", "תבלינים ובסיס", unit="ק״ג", price_per_unit=8.0, 
                package_quantity=1.0, estimated_price=8.00,
                quantity_in_stock=45, min_stock_level=20, inventory_status="במלאי", 
                supplier="סוגת", kosher_type="פרווה"),
        make_product("פסטה", "תבלינים ובסיס", unit="ק״ג", price_per_unit=7.0, 
                package_quantity=1.0, estimated_price=7.00,
                quantity_in_stock=35, min_stock_level=15, inventory_status="במלאי", 
                supplier="אסם", kosher_type="פרווה"),
        
        # עוד מוצרים - דגים וימיים
        make_product("פילה סלמון", "דגים", unit="ק״ג", price_per_unit=85.0, 
                package_quantity=1.0, estimated_price=85.00,
                quantity_in_stock=6, min_stock_level=3, inventory_status="במלאי", 
                supplier="דגי הים", kosher_type="פרווה"),
        make_product("פילה אמנון", "דגים", unit="ק״ג", price_per_unit=42.0, 
                package_quantity=1.0, estimated_price=42.00,
                quantity_in_stock=8, min_stock_level=4, inventory_status="במלאי", 
                supplier="דגי הים", kosher_type="פרווה"),
        make_product("טונה קופסה", "דגים", unit="יחידות", price_per_unit=8.5, 
                package_quantity=1.0, estimated_price=8.50,
                quantity_in_stock=30, min_stock_level=15, inventory_status="במלאי", 
                supplier="סטארקיסט", kosher_type="פרווה"),
        
        # ירקות נוספים
        make_product("תפוחי אדמה", "ירקות", unit="ק״ג", price_per_unit=5.0, 
                package_quantity=1.0, estimated_price=5.00,
                quantity_in_stock=40, min_stock_level=20, inventory_status="במלאי", 
                supplier="ירקות הגליל"),
        make_product("גזר", "ירקות", unit="ק״ג", price_per_unit=4.5, 
                package_quantity=1.0, estimated_price=4.50,
                quantity_in_stock=22, min_stock_level=10, inventory_status="במלאי", 
                supplier="ירקות הגליל"),
        make_product("כרובית", "ירקות", unit="ק״ג", price_per_unit=7.0, 
                package_quantity=1.0, estimated_price=7.00,
                quantity_in_stock=12, min_stock_level=8, inventory_status="במלאי", 
                supplier="ירקות הגליל"),
        make_product("ברוקולי", "ירקות", unit="ק״ג", price_per_unit=9.0, 
                package_quantity=1.0, estimated_price=9.00,
                quantity_in_stock=8, min_stock_level=5, inventory_status="במלאי", 
                supplier="ירקות הגליל"),
        make_product("בטטה", "ירקות", unit="ק״ג", price_per_unit=6.5, 
                package_quantity=1.0, estimated_price=6.50,
                quantity_in_stock=18, min_stock_level=10, inventory_status="במלאי", 
                supplier="ירקות הגליל"),
        make_product("פטרוזיליה", "ירקות", unit="אגדים", price_per_unit=3.0, 
                package_quantity=1.0, estimated_price=3.00,
                quantity_in_stock=10, min_stock_level=5, inventory_status="במלאי", 
                supplier="ירקות הגליל"),
        make_product("כוסברה", "ירקות", unit="אגדים", price_per_unit=3.0, 
                package_quantity=1.0, estimated_price=3.00,
                quantity_in_stock=8, min_stock_level=5, inventory_status="במלאי", 
                supplier="ירקות הגליל"),
        
        # חלבי נוסף
        make_product("יוגורט", "חלבי", unit="ליטר", price_per_unit=9.0, 
                package_quantity=1.0, estimated_price=9.00,
                quantity_in_stock=20, min_stock_level=10, inventory_status="במלאי", 
                supplier="תנובה", kosher_type="חלבי"),
        make_product("גבינת פטה", "חלבי", unit="ק״ג", price_per_unit=38.0, 
                package_quantity=0.2, estimated_price=7.60,
                quantity_in_stock=6, min_stock_level=4, inventory_status="במלאי", 
                supplier="תנובה", kosher_type="חלבי"),
        make_product("גבינת מוצרלה", "חלבי", unit="ק״ג", price_per_unit=42.0, 
                package_quantity=0.25, estimated_price=10.50,
                quantity_in_stock=8, min_stock_level=5, inventory_status="במלאי", 
                supplier="תנובה", kosher_type="חלבי"),
        make_product("קצפת", "חלבי", unit="ליטר", price_per_unit=15.0, 
                package_quantity=0.5, estimated_price=7.50,
                quantity_in_stock=5, min_stock_level=3, inventory_status="במלאי", 
                supplier="תנובה", kosher_type="חלבי"),
        
        # בשרי נוסף
        make_product("שוקיים עוף", "בשרי", unit="ק״ג", price_per_unit=28.0, 
                package_quantity=1.0, estimated_price=28.00,
                quantity_in_stock=15, min_stock_level=8, inventory_status="במלאי", 
                supplier="עוף טרי", kosher_type="בשרי"),
        make_product("נקניקיות", "בשרי", unit="ק״ג", price_per_unit=35.0, 
                package_quantity=0.5, estimated_price=17.50,
                quantity_in_stock=10, min_stock_level=5, inventory_status="במלאי", 
                supplier="מעדני הצפון", kosher_type="בשרי"),
        make_product("קבב", "בשרי", unit="ק״ג", price_per_unit=48.0, 
                package_quantity=1.0, estimated_price=48.00,
                quantity_in_stock=7, min_stock_level=5, inventory_status="במלאי", 
                supplier="מעדני הצפון", kosher_type="בשרי"),
        
        # תבלינים ובסיס נוספים
        make_product("פפריקה", "תבלינים ובסיס", unit="גרם", price_per_unit=0.08, 
                package_quantity=50.0, estimated_price=4.00,
                quantity_in_stock=500, min_stock_level=200, inventory_status="במלאי", 
                supplier="פרישמן", kosher_type="פרווה"),
        make_product("כמון", "תבלינים ובסיס", unit="גרם", price_per_unit=0.12, 
                package_quantity=50.0, estimated_price=6.00,
                quantity_in_stock=300, min_stock_level=150, inventory_status="במלאי", 
                supplier="פרישמן", kosher_type="פרווה"),
        make_product("כורכום", "תבלינים ובסיס", unit="גרם", price_per_unit=0.10, 
                package_quantity=50.0, estimated_price=5.00,
                quantity_in_stock=400, min_stock_level=200, inventory_status="במלאי", 
                supplier="פרישמן", kosher_type="פרווה"),
    ]
    
    db.add_all(products)
    db.commit()
    print(f"✅ נוספו {len(products)} מוצרים")
    return products


def populate_tools(db):
    """מילוי כלים וציוד"""
    print("🔧 ממלא כלים וציוד...")
    
    tools = [
        # כלי הכנה - אמיתי
        Tool(name="סכין שף גדול", category="הכנה", sub_category="אמיתי", 
             quantity_in_stock=15, min_stock_level=10, inventory_status="במלאי", 
             price_per_unit=120.0, description="סכין שף מקצועי 20 ס״מ"),
        Tool(name="קרש חיתוך גדול", category="הכנה", sub_category="אמיתי", 
             quantity_in_stock=12, min_stock_level=8, inventory_status="במלאי", 
             price_per_unit=45.0),
        Tool(name="מערבל חשמלי", category="הכנה", sub_category="אמיתי", 
             quantity_in_stock=5, min_stock_level=3, inventory_status="במלאי", 
             price_per_unit=350.0, description="מערבל עוצמתי למנות גדולות"),
        Tool(name="סיר ענק 50 ליטר", category="הכנה", sub_category="אמיתי", 
             quantity_in_stock=8, min_stock_level=5, inventory_status="במלאי", 
             price_per_unit=280.0),
        Tool(name="מחבת גדולה", category="הכנה", sub_category="אמיתי", 
             quantity_in_stock=10, min_stock_level=6, inventory_status="במלאי", 
             price_per_unit=95.0, size="40 ס״מ"),
        
        # כלי הגשה - אמיתי
        Tool(name="צלחת פורצלן לבנה", category="הגשה", sub_category="אמיתי", 
             quantity_in_stock=200, min_stock_level=150, inventory_status="במלאי", 
             price_per_unit=15.0, color="לבן", size="27 ס״מ"),
        Tool(name="צלחת פורצלן שוליים זהב", category="הגשה", sub_category="אמיתי", 
             quantity_in_stock=150, min_stock_level=100, inventory_status="במלאי", 
             price_per_unit=25.0, color="לבן-זהב", size="27 ס״מ"),
        Tool(name="קערת הגשה עגולה גדולה", category="הגשה", sub_category="אמיתי", 
             quantity_in_stock=50, min_stock_level=30, inventory_status="במלאי", 
             price_per_unit=45.0, size="35 ס״מ"),
        Tool(name="קערת הגשה מלבנית", category="הגשה", sub_category="אמיתי", 
             quantity_in_stock=40, min_stock_level=25, inventory_status="במלאי", 
             price_per_unit=55.0, size="40x25 ס״מ"),
        Tool(name="מגש הגשה כסף", category="הגשה", sub_category="אמיתי", 
             quantity_in_stock=35, min_stock_level=20, inventory_status="במלאי", 
             price_per_unit=85.0, color="כסף", size="45 ס״מ"),
        
        # כלי הגשה - חד״פ
        Tool(name="צלחת חד״פ לבנה", category="הגשה", sub_category="חד״פ", 
             quantity_in_stock=1000, min_stock_level=500, inventory_status="במלאי", 
             price_per_unit=1.5, color="לבן", size="26 ס״מ"),
        Tool(name="צלחת חד״פ זהב מפוארת", category="הגשה", sub_category="חד״פ", 
             quantity_in_stock=800, min_stock_level=400, inventory_status="במלאי", 
             price_per_unit=2.8, color="זהב", size="26 ס״מ"),
        Tool(name="כוס פלסטיק שקופה", category="הגשה", sub_category="חד״פ", 
             quantity_in_stock=1500, min_stock_level=800, inventory_status="במלאי", 
             price_per_unit=0.5, size="300 מ״ל"),
        Tool(name="סכו״ם חד״פ סט", category="הגשה", sub_category="חד״פ", 
             quantity_in_stock=1200, min_stock_level=600, inventory_status="במלאי", 
             price_per_unit=1.2, description="סט סכין+מזלג+כפית"),
        
        # מפות
        Tool(name="מפת שולחן לבנה", category="מפות", sub_category="אמיתי", 
             quantity_in_stock=80, min_stock_level=50, inventory_status="במלאי", 
             price_per_unit=35.0, color="לבן", size="3x1.5 מטר"),
        Tool(name="מפת שולחן שמנת", category="מפות", sub_category="אמיתי", 
             quantity_in_stock=60, min_stock_level=40, inventory_status="במלאי", 
             price_per_unit=35.0, color="שמנת", size="3x1.5 מטר"),
        Tool(name="מפת שולחן חד״פ", category="מפות", sub_category="חד״פ", 
             quantity_in_stock=300, min_stock_level=150, inventory_status="במלאי", 
             price_per_unit=8.0, color="לבן", size="2.5x1.2 מטר"),
        
        # ציוד שירות
        Tool(name="מחמם מזון נירוסטה", category="ציוד שירות", sub_category="אמיתי", 
             quantity_in_stock=25, min_stock_level=15, inventory_status="במלאי", 
             price_per_unit=180.0, description="מחמם עם נרות"),
        Tool(name="קערת קירור עם קרח", category="ציוד שירות", sub_category="אמיתי", 
             quantity_in_stock=20, min_stock_level=12, inventory_status="במלאי", 
             price_per_unit=95.0),
        Tool(name="מתקן עמידה למזון", category="ציוד שירות", sub_category="אמיתי", 
             quantity_in_stock=15, min_stock_level=10, inventory_status="במלאי", 
             price_per_unit=120.0, description="3 קומות"),
    ]
    
    db.add_all(tools)
    db.commit()
    print(f"✅ נוספו {len(tools)} כלים")
    return tools


def populate_dishes(db, products, tools):
    """מילוי מנות עם רכיבים וציוד"""
    print("🍽️  ממלא מנות...")
    
    # מציאת מוצרים וכלים לפי שם
    def find_product(name):
        return db.query(Product).filter(Product.name.contains(name)).first()
    
    def find_tool(name):
        return db.query(Tool).filter(Tool.name.contains(name)).first()
    
    # מנה 1: סלט ישראלי
    salad_dish = Dish(
        name="סלט ישראלי טרי",
        category="סלטים",
        kosher_type="פרווה",
        description="סלט ירקות טרי וצבעוני",
        price_per_unit=18.0,
        serving_size=1.0,
        is_active=1
    )
    db.add(salad_dish)
    db.flush()
    
    # רכיבים לסלט
    db.add_all([
        DishIngredient(dish_id=salad_dish.id, product_id=find_product("עגבניות").id, 
                      name="עגבניות", quantity=0.3, unit="ק״ג"),
        DishIngredient(dish_id=salad_dish.id, product_id=find_product("מלפפונים").id, 
                      name="מלפפונים", quantity=0.2, unit="ק״ג"),
        DishIngredient(dish_id=salad_dish.id, product_id=find_product("בצל").id, 
                      name="בצל", quantity=0.05, unit="ק״ג"),
        DishIngredient(dish_id=salad_dish.id, product_id=find_product("שמן זית").id, 
                      name="שמן זית", quantity=0.02, unit="ליטר"),
    ])
    
    # ציוד לסלט
    db.add_all([
        DishEquipment(dish_id=salad_dish.id, tool_id=find_tool("סכין שף").id, 
                     name="סכין שף", quantity=1),
        DishEquipment(dish_id=salad_dish.id, tool_id=find_tool("קרש חיתוך").id, 
                     name="קרש חיתוך", quantity=1),
    ])
    
    # כלי הגשה לסלט
    db.add_all([
        ServingDish(dish_id=salad_dish.id, tool_id=find_tool("קערת הגשה עגולה").id, 
                   name="קערת הגשה", quantity=1),
    ])
    
    # מנה 2: שניצל עוף
    schnitzel_dish = Dish(
        name="שניצל עוף פריך",
        category="עיקרית",
        kosher_type="בשרי",
        description="שניצל עוף בציפוי פריך",
        price_per_unit=35.0,
        serving_size=1.0,
        is_active=1
    )
    db.add(schnitzel_dish)
    db.flush()
    
    db.add_all([
        DishIngredient(dish_id=schnitzel_dish.id, product_id=find_product("שניצל עוף").id, 
                      name="שניצל עוף", quantity=0.25, unit="ק״ג"),
        DishIngredient(dish_id=schnitzel_dish.id, product_id=find_product("קמח").id, 
                      name="קמח לציפוי", quantity=0.05, unit="ק״ג"),
        DishIngredient(dish_id=schnitzel_dish.id, product_id=find_product("מלח").id, 
                      name="מלח", quantity=0.002, unit="ק״ג"),
    ])
    
    db.add_all([
        DishEquipment(dish_id=schnitzel_dish.id, tool_id=find_tool("מחבת").id, 
                     name="מחבת גדולה", quantity=1),
    ])
    
    db.add_all([
        ServingDish(dish_id=schnitzel_dish.id, tool_id=find_tool("צלחת פורצלן לבנה").id, 
                   name="צלחת פורצלן", quantity=1),
    ])
    
    # מנה 3: פסטה ברטבי שמנת
    pasta_dish = Dish(
        name="פסטה ברטבי שמנת ופטריות",
        category="עיקרית",
        kosher_type="חלבי",
        description="פסטה קרמית עם פטריות טריות",
        price_per_unit=42.0,
        serving_size=1.0,
        is_active=1
    )
    db.add(pasta_dish)
    db.flush()
    
    db.add_all([
        DishIngredient(dish_id=pasta_dish.id, product_id=find_product("פסטה").id, 
                      name="פסטה", quantity=0.15, unit="ק״ג"),
        DishIngredient(dish_id=pasta_dish.id, product_id=find_product("שמנת").id, 
                      name="שמנת מתוקה", quantity=0.1, unit="ליטר"),
        DishIngredient(dish_id=pasta_dish.id, product_id=find_product("חמאה").id, 
                      name="חמאה", quantity=0.02, unit="ק״ג"),
        DishIngredient(dish_id=pasta_dish.id, product_id=find_product("שום").id, 
                      name="שום", quantity=0.01, unit="ק״ג"),
    ])
    
    db.add_all([
        DishEquipment(dish_id=pasta_dish.id, tool_id=find_tool("סיר ענק").id, 
                     name="סיר גדול", quantity=1),
        DishEquipment(dish_id=pasta_dish.id, tool_id=find_tool("מחבת").id, 
                     name="מחבת", quantity=1),
    ])
    
    db.add_all([
        ServingDish(dish_id=pasta_dish.id, tool_id=find_tool("קערת הגשה מלבנית").id, 
                   name="קערת הגשה מלבנית", quantity=1),
    ])
    
    # מנה 4: אורז עם ירקות
    rice_dish = Dish(
        name="אורז בסמטי עם ירקות צבעוניים",
        category="תוספת",
        kosher_type="פרווה",
        description="אורז ריחני עם ירקות צבעוניים",
        price_per_unit=22.0,
        serving_size=1.0,
        is_active=1
    )
    db.add(rice_dish)
    db.flush()
    
    db.add_all([
        DishIngredient(dish_id=rice_dish.id, product_id=find_product("אורז").id, 
                      name="אורז", quantity=0.1, unit="ק״ג"),
        DishIngredient(dish_id=rice_dish.id, product_id=find_product("פלפל אדום").id, 
                      name="פלפל אדום", quantity=0.05, unit="ק״ג"),
        DishIngredient(dish_id=rice_dish.id, product_id=find_product("בצל").id, 
                      name="בצל", quantity=0.03, unit="ק״ג"),
    ])
    
    db.add_all([
        DishEquipment(dish_id=rice_dish.id, tool_id=find_tool("סיר ענק").id, 
                     name="סיר", quantity=1),
    ])
    
    db.add_all([
        ServingDish(dish_id=rice_dish.id, tool_id=find_tool("קערת הגשה עגולה").id, 
                   name="קערת הגשה", quantity=1),
    ])
    
    # מנה 5: חזה עוף בתנור
    chicken_dish = Dish(
        name="חזה עוף בתנור עם תבלינים",
        category="עיקרית",
        kosher_type="בשרי",
        description="חזה עוף רך ועסיסי",
        price_per_unit=38.0,
        serving_size=1.0,
        is_active=1
    )
    db.add(chicken_dish)
    db.flush()
    
    db.add_all([
        DishIngredient(dish_id=chicken_dish.id, product_id=find_product("חזה עוף").id, 
                      name="חזה עוף", quantity=0.3, unit="ק״ג"),
        DishIngredient(dish_id=chicken_dish.id, product_id=find_product("שמן זית").id, 
                      name="שמן זית", quantity=0.02, unit="ליטר"),
        DishIngredient(dish_id=chicken_dish.id, product_id=find_product("שום").id, 
                      name="שום", quantity=0.01, unit="ק״ג"),
    ])
    
    db.add_all([
        ServingDish(dish_id=chicken_dish.id, tool_id=find_tool("צלחת פורצלן שוליים זהב").id, 
                   name="צלחת פורצלן יוקרתית", quantity=1),
        ServingDish(dish_id=chicken_dish.id, tool_id=find_tool("מגש הגשה כסף").id, 
                   name="מגש הגשה", quantity=1),
    ])
    
    # מנה 6: סלמון בתנור
    salmon_dish = Dish(
        name="פילה סלמון בתנור עם לימון",
        category="עיקרית",
        kosher_type="פרווה",
        description="סלמון עסיסי עם לימון ותבלינים",
        price_per_unit=65.0,
        serving_size=1.0,
        is_active=1
    )
    db.add(salmon_dish)
    db.flush()
    db.add_all([
        DishIngredient(dish_id=salmon_dish.id, product_id=find_product("סלמון").id, 
                      name="פילה סלמון", quantity=0.25, unit="ק״ג"),
        DishIngredient(dish_id=salmon_dish.id, product_id=find_product("שמן זית").id, 
                      name="שמן זית", quantity=0.015, unit="ליטר"),
    ])
    db.add_all([
        ServingDish(dish_id=salmon_dish.id, tool_id=find_tool("צלחת פורצלן לבנה").id, 
                   name="צלחת פורצלן", quantity=1),
    ])
    
    # מנה 7: תפוחי אדמה אפויים
    potato_dish = Dish(
        name="תפוחי אדמה אפויים עם שמן זית",
        category="תוספת",
        kosher_type="פרווה",
        description="תפוחי אדמה זהובים ופריכים",
        price_per_unit=15.0,
        serving_size=1.0,
        is_active=1
    )
    db.add(potato_dish)
    db.flush()
    db.add_all([
        DishIngredient(dish_id=potato_dish.id, product_id=find_product("תפוחי אדמה").id, 
                      name="תפוחי אדמה", quantity=0.3, unit="ק״ג"),
        DishIngredient(dish_id=potato_dish.id, product_id=find_product("שמן זית").id, 
                      name="שמן זית", quantity=0.02, unit="ליטר"),
    ])
    db.add_all([
        ServingDish(dish_id=potato_dish.id, tool_id=find_tool("קערת הגשה עגולה").id, 
                   name="קערת הגשה", quantity=1),
    ])
    
    # מנה 8: סלט קולסלאו
    coleslaw_dish = Dish(
        name="סלט קולסלאו",
        category="סלטים",
        kosher_type="פרווה",
        description="סלט כרוב טרי ורענן",
        price_per_unit=16.0,
        serving_size=1.0,
        is_active=1
    )
    db.add(coleslaw_dish)
    db.flush()
    db.add_all([
        DishIngredient(dish_id=coleslaw_dish.id, product_id=find_product("כרובית").id, 
                      name="כרוב", quantity=0.2, unit="ק״ג"),
        DishIngredient(dish_id=coleslaw_dish.id, product_id=find_product("גזר").id, 
                      name="גזר", quantity=0.1, unit="ק״ג"),
    ])
    db.add_all([
        ServingDish(dish_id=coleslaw_dish.id, tool_id=find_tool("קערת הגשה עגולה").id, 
                   name="קערת הגשה", quantity=1),
    ])
    
    # מנה 9: קבב על האש
    kebab_dish = Dish(
        name="קבב על האש",
        category="עיקרית",
        kosher_type="בשרי",
        description="קבב מתובל ועסיסי",
        price_per_unit=45.0,
        serving_size=1.0,
        is_active=1
    )
    db.add(kebab_dish)
    db.flush()
    db.add_all([
        DishIngredient(dish_id=kebab_dish.id, product_id=find_product("קבב").id, 
                      name="קבב", quantity=0.3, unit="ק״ג"),
        DishIngredient(dish_id=kebab_dish.id, product_id=find_product("בצל").id, 
                      name="בצל", quantity=0.05, unit="ק״ג"),
    ])
    db.add_all([
        ServingDish(dish_id=kebab_dish.id, tool_id=find_tool("מגש הגשה כסף").id, 
                   name="מגש הגשה", quantity=1),
    ])
    
    # מנה 10: שוקיים בתנור
    drumstick_dish = Dish(
        name="שוקיים בתנור עם דבש",
        category="עיקרית",
        kosher_type="בשרי",
        description="שוקיים מתוקים וקרמליים",
        price_per_unit=32.0,
        serving_size=1.0,
        is_active=1
    )
    db.add(drumstick_dish)
    db.flush()
    db.add_all([
        DishIngredient(dish_id=drumstick_dish.id, product_id=find_product("שוקיים").id, 
                      name="שוקיים עוף", quantity=0.4, unit="ק״ג"),
        DishIngredient(dish_id=drumstick_dish.id, product_id=find_product("סוכר").id, 
                      name="דבש/סוכר", quantity=0.02, unit="ק״ג"),
    ])
    db.add_all([
        ServingDish(dish_id=drumstick_dish.id, tool_id=find_tool("מגש הגשה כסף").id, 
                   name="מגש הגשה", quantity=1),
    ])
    
    # מנה 11: גבינת פטה בתנור
    feta_dish = Dish(
        name="גבינת פטה אפויה",
        category="ראשונה",
        kosher_type="חלבי",
        description="גבינת פטה חמה עם עגבניות",
        price_per_unit=28.0,
        serving_size=1.0,
        is_active=1
    )
    db.add(feta_dish)
    db.flush()
    db.add_all([
        DishIngredient(dish_id=feta_dish.id, product_id=find_product("פטה").id, 
                      name="גבינת פטה", quantity=0.15, unit="ק״ג"),
        DishIngredient(dish_id=feta_dish.id, product_id=find_product("עגבניות").id, 
                      name="עגבניות", quantity=0.1, unit="ק״ג"),
    ])
    db.add_all([
        ServingDish(dish_id=feta_dish.id, tool_id=find_tool("קערת הגשה עגולה").id, 
                   name="קערת הגשה", quantity=1),
    ])
    
    # מנה 12: לזניה
    lasagna_dish = Dish(
        name="לזניה איטלקית",
        category="עיקרית",
        kosher_type="חלבי",
        description="לזניה עם רוטב עגבניות וגבינות",
        price_per_unit=48.0,
        serving_size=1.0,
        is_active=1
    )
    db.add(lasagna_dish)
    db.flush()
    db.add_all([
        DishIngredient(dish_id=lasagna_dish.id, product_id=find_product("פסטה").id, 
                      name="פסטה ללזניה", quantity=0.15, unit="ק״ג"),
        DishIngredient(dish_id=lasagna_dish.id, product_id=find_product("מוצרלה").id, 
                      name="גבינת מוצרלה", quantity=0.2, unit="ק״ג"),
        DishIngredient(dish_id=lasagna_dish.id, product_id=find_product("עגבניות").id, 
                      name="עגבניות", quantity=0.15, unit="ק״ג"),
    ])
    db.add_all([
        ServingDish(dish_id=lasagna_dish.id, tool_id=find_tool("קערת הגשה מלבנית").id, 
                   name="קערת הגשה מלבנית", quantity=1),
    ])
    
    # מנה 13: נקניקיות בתנור
    sausage_dish = Dish(
        name="נקניקיות בתנור עם בצל",
        category="עיקרית",
        kosher_type="בשרי",
        description="נקניקיות עסיסיות עם בצל מקורמל",
        price_per_unit=36.0,
        serving_size=1.0,
        is_active=1
    )
    db.add(sausage_dish)
    db.flush()
    db.add_all([
        DishIngredient(dish_id=sausage_dish.id, product_id=find_product("נקניקיות").id, 
                      name="נקניקיות", quantity=0.3, unit="ק״ג"),
        DishIngredient(dish_id=sausage_dish.id, product_id=find_product("בצל").id, 
                      name="בצל", quantity=0.1, unit="ק״ג"),
    ])
    db.add_all([
        ServingDish(dish_id=sausage_dish.id, tool_id=find_tool("קערת הגשה מלבנית").id, 
                   name="קערת הגשה", quantity=1),
    ])
    
    # מנה 14: אמנון מוקפץ
    tilapia_dish = Dish(
        name="פילה אמנון מוקפץ",
        category="עיקרית",
        kosher_type="פרווה",
        description="דג אמנון טרי עם שום ופטרוזיליה",
        price_per_unit=38.0,
        serving_size=1.0,
        is_active=1
    )
    db.add(tilapia_dish)
    db.flush()
    db.add_all([
        DishIngredient(dish_id=tilapia_dish.id, product_id=find_product("אמנון").id, 
                      name="פילה אמנון", quantity=0.25, unit="ק״ג"),
        DishIngredient(dish_id=tilapia_dish.id, product_id=find_product("שום").id, 
                      name="שום", quantity=0.01, unit="ק״ג"),
        DishIngredient(dish_id=tilapia_dish.id, product_id=find_product("פטרוזיליה").id, 
                      name="פטרוזיליה", quantity=0.5, unit="אגדים"),
    ])
    db.add_all([
        ServingDish(dish_id=tilapia_dish.id, tool_id=find_tool("צלחת פורצלן לבנה").id, 
                   name="צלחת פורצלן", quantity=1),
    ])
    
    # מנה 15: בטטה אפויה
    sweet_potato_dish = Dish(
        name="בטטה אפויה",
        category="תוספת",
        kosher_type="פרווה",
        description="בטטה מתוקה ועסיסית",
        price_per_unit=18.0,
        serving_size=1.0,
        is_active=1
    )
    db.add(sweet_potato_dish)
    db.flush()
    db.add_all([
        DishIngredient(dish_id=sweet_potato_dish.id, product_id=find_product("בטטה").id, 
                      name="בטטה", quantity=0.3, unit="ק״ג"),
        DishIngredient(dish_id=sweet_potato_dish.id, product_id=find_product("שמן זית").id, 
                      name="שמן זית", quantity=0.015, unit="ליטר"),
    ])
    db.add_all([
        ServingDish(dish_id=sweet_potato_dish.id, tool_id=find_tool("קערת הגשה עגולה").id, 
                   name="קערת הגשה", quantity=1),
    ])
    
    # מנה 16: ברוקולי מאודה
    broccoli_dish = Dish(
        name="ברוקולי מאודה עם שום",
        category="תוספת",
        kosher_type="פרווה",
        description="ברוקולי טרי מאודה",
        price_per_unit=20.0,
        serving_size=1.0,
        is_active=1
    )
    db.add(broccoli_dish)
    db.flush()
    db.add_all([
        DishIngredient(dish_id=broccoli_dish.id, product_id=find_product("ברוקולי").id, 
                      name="ברוקולי", quantity=0.25, unit="ק״ג"),
        DishIngredient(dish_id=broccoli_dish.id, product_id=find_product("שום").id, 
                      name="שום", quantity=0.01, unit="ק״ג"),
    ])
    db.add_all([
        ServingDish(dish_id=broccoli_dish.id, tool_id=find_tool("קערת הגשה עגולה").id, 
                   name="קערת הגשה", quantity=1),
    ])
    
    # מנה 17: גזר מתוק
    carrot_dish = Dish(
        name="גזר מתוק בתנור",
        category="תוספת",
        kosher_type="פרווה",
        description="גזר אפוי עם דבש",
        price_per_unit=16.0,
        serving_size=1.0,
        is_active=1
    )
    db.add(carrot_dish)
    db.flush()
    db.add_all([
        DishIngredient(dish_id=carrot_dish.id, product_id=find_product("גזר").id, 
                      name="גזר", quantity=0.3, unit="ק״ג"),
        DishIngredient(dish_id=carrot_dish.id, product_id=find_product("סוכר").id, 
                      name="דבש/סוכר", quantity=0.02, unit="ק״ג"),
    ])
    db.add_all([
        ServingDish(dish_id=carrot_dish.id, tool_id=find_tool("קערת הגשה עגולה").id, 
                   name="קערת הגשה", quantity=1),
    ])
    
    # מנה 18: סלט יוגורט
    yogurt_salad_dish = Dish(
        name="סלט יוגורט עם מלפפון",
        category="סלטים",
        kosher_type="חלבי",
        description="סלט יוגורט רענן",
        price_per_unit=22.0,
        serving_size=1.0,
        is_active=1
    )
    db.add(yogurt_salad_dish)
    db.flush()
    db.add_all([
        DishIngredient(dish_id=yogurt_salad_dish.id, product_id=find_product("יוגורט").id, 
                      name="יוגורט", quantity=0.15, unit="ליטר"),
        DishIngredient(dish_id=yogurt_salad_dish.id, product_id=find_product("מלפפונים").id, 
                      name="מלפפונים", quantity=0.1, unit="ק״ג"),
    ])
    db.add_all([
        ServingDish(dish_id=yogurt_salad_dish.id, tool_id=find_tool("קערת הגשה עגולה").id, 
                   name="קערת הגשה", quantity=1),
    ])
    
    # מנה 19: סלט טונה
    tuna_salad_dish = Dish(
        name="סלט טונה",
        category="סלטים",
        kosher_type="פרווה",
        description="סלט טונה עשיר",
        price_per_unit=25.0,
        serving_size=1.0,
        is_active=1
    )
    db.add(tuna_salad_dish)
    db.flush()
    db.add_all([
        DishIngredient(dish_id=tuna_salad_dish.id, product_id=find_product("טונה").id, 
                      name="טונה קופסה", quantity=2, unit="יחידות"),
        DishIngredient(dish_id=tuna_salad_dish.id, product_id=find_product("בצל").id, 
                      name="בצל", quantity=0.05, unit="ק״ג"),
    ])
    db.add_all([
        ServingDish(dish_id=tuna_salad_dish.id, tool_id=find_tool("קערת הגשה עגולה").id, 
                   name="קערת הגשה", quantity=1),
    ])
    
    # מנה 20: סלט גבינה צהובה
    cheese_salad_dish = Dish(
        name="סלט גבינה צהובה",
        category="סלטים",
        kosher_type="חלבי",
        description="סלט עם גבינה צהובה וירקות",
        price_per_unit=26.0,
        serving_size=1.0,
        is_active=1
    )
    db.add(cheese_salad_dish)
    db.flush()
    db.add_all([
        DishIngredient(dish_id=cheese_salad_dish.id, product_id=find_product("גבינה צהובה").id, 
                      name="גבינה צהובה", quantity=0.1, unit="ק״ג"),
        DishIngredient(dish_id=cheese_salad_dish.id, product_id=find_product("עגבניות").id, 
                      name="עגבניות", quantity=0.15, unit="ק״ג"),
        DishIngredient(dish_id=cheese_salad_dish.id, product_id=find_product("חסה").id, 
                      name="חסה", quantity=1, unit="יחידות"),
    ])
    db.add_all([
        ServingDish(dish_id=cheese_salad_dish.id, tool_id=find_tool("קערת הגשה עגולה").id, 
                   name="קערת הגשה", quantity=1),
    ])
    
    # מנה 21: כבד עוף מטוגן
    liver_dish = Dish(
        name="כבד עוף מטוגן",
        category="ראשונה",
        kosher_type="בשרי",
        description="כבד עוף עם בצל מקורמל",
        price_per_unit=32.0,
        serving_size=1.0,
        is_active=1
    )
    db.add(liver_dish)
    db.flush()
    db.add_all([
        DishIngredient(dish_id=liver_dish.id, product_id=find_product("כבד עוף").id, 
                      name="כבד עוף", quantity=0.25, unit="ק״ג"),
        DishIngredient(dish_id=liver_dish.id, product_id=find_product("בצל").id, 
                      name="בצל", quantity=0.1, unit="ק״ג"),
    ])
    db.add_all([
        ServingDish(dish_id=liver_dish.id, tool_id=find_tool("קערת הגשה מלבנית").id, 
                   name="קערת הגשה", quantity=1),
    ])
    
    # מנה 22: המבורגר ביתי
    burger_dish = Dish(
        name="המבורגר ביתי",
        category="עיקרית",
        kosher_type="בשרי",
        description="המבורגר עסיסי ממוצק",
        price_per_unit=38.0,
        is_active=1
    )
    db.add(burger_dish)
    db.flush()
    db.add_all([
        DishIngredient(dish_id=burger_dish.id, product_id=find_product("בשר טחון").id, 
                      name="בשר טחון", quantity=0.2, unit="ק״ג"),
        DishIngredient(dish_id=burger_dish.id, product_id=find_product("בצל").id, 
                      name="בצל", quantity=0.03, unit="ק״ג"),
    ])
    db.add_all([
        ServingDish(dish_id=burger_dish.id, tool_id=find_tool("צלחת פורצלן לבנה").id, 
                   name="צלחת פורצלן", quantity=1),
    ])
    
    # מנה 23: סלט חסה עם רוטב
    lettuce_salad_dish = Dish(
        name="סלט חסה עם רוטב ויניגרט",
        category="סלטים",
        kosher_type="פרווה",
        description="סלט חסה טרי ורענן",
        price_per_unit=14.0,
        is_active=1
    )
    db.add(lettuce_salad_dish)
    db.flush()
    db.add_all([
        DishIngredient(dish_id=lettuce_salad_dish.id, product_id=find_product("חסה").id, 
                      name="חסה", quantity=1.5, unit="יחידות"),
        DishIngredient(dish_id=lettuce_salad_dish.id, product_id=find_product("שמן זית").id, 
                      name="שמן זית", quantity=0.02, unit="ליטר"),
    ])
    db.add_all([
        ServingDish(dish_id=lettuce_salad_dish.id, tool_id=find_tool("קערת הגשה עגולה").id, 
                   name="קערת הגשה", quantity=1),
    ])
    
    # מנה 24: ירקות צלויים
    roasted_veg_dish = Dish(
        name="ירקות צלויים בתנור",
        category="תוספת",
        kosher_type="פרווה",
        description="תערובת ירקות צבעונית",
        price_per_unit=24.0,
        is_active=1
    )
    db.add(roasted_veg_dish)
    db.flush()
    db.add_all([
        DishIngredient(dish_id=roasted_veg_dish.id, product_id=find_product("פלפל אדום").id, 
                      name="פלפל אדום", quantity=0.1, unit="ק״ג"),
        DishIngredient(dish_id=roasted_veg_dish.id, product_id=find_product("בצל").id, 
                      name="בצל", quantity=0.1, unit="ק״ג"),
        DishIngredient(dish_id=roasted_veg_dish.id, product_id=find_product("גזר").id, 
                      name="גזר", quantity=0.1, unit="ק״ג"),
    ])
    db.add_all([
        ServingDish(dish_id=roasted_veg_dish.id, tool_id=find_tool("קערת הגשה מלבנית").id, 
                   name="קערת הגשה", quantity=1),
    ])
    
    # מנה 25: פיצה גבינה
    pizza_dish = Dish(
        name="פיצה גבינה",
        category="עיקרית",
        kosher_type="חלבי",
        description="פיצה איטלקית עם מוצרלה",
        price_per_unit=40.0,
        is_active=1
    )
    db.add(pizza_dish)
    db.flush()
    db.add_all([
        DishIngredient(dish_id=pizza_dish.id, product_id=find_product("קמח").id, 
                      name="קמח", quantity=0.15, unit="ק״ג"),
        DishIngredient(dish_id=pizza_dish.id, product_id=find_product("מוצרלה").id, 
                      name="גבינת מוצרלה", quantity=0.15, unit="ק״ג"),
        DishIngredient(dish_id=pizza_dish.id, product_id=find_product("עגבניות").id, 
                      name="עגבניות", quantity=0.1, unit="ק״ג"),
    ])
    db.add_all([
        ServingDish(dish_id=pizza_dish.id, tool_id=find_tool("מגש הגשה כסף").id, 
                   name="מגש הגשה", quantity=1),
    ])
    
    all_dishes = [salad_dish, schnitzel_dish, pasta_dish, rice_dish, chicken_dish,
                  salmon_dish, potato_dish, coleslaw_dish, kebab_dish, drumstick_dish,
                  feta_dish, lasagna_dish, sausage_dish, tilapia_dish, sweet_potato_dish,
                  broccoli_dish, carrot_dish, yogurt_salad_dish, tuna_salad_dish, cheese_salad_dish,
                  liver_dish, burger_dish, lettuce_salad_dish, roasted_veg_dish, pizza_dish]
    
    db.commit()
    print(f"✅ נוספו {len(all_dishes)} מנות עם כל הרכיבים והציוד")
    
    return all_dishes


def populate_events(db, dishes):
    """מילוי אירועים"""
    print("🎉 ממלא אירועים...")
    
    today = datetime.now()
    
    # אירוע 1: חתונה עתידית - עם 2 בעלי אירוע (חתן וכלה)
    event1 = Event(
        name="חתונת יוסי ושרה",
        menu_type=MenuType.MEAT_MENU,
        status="pending",
        date=today + timedelta(days=30),
        hebrew_date="ט״ו באדר התשפ״ו",
        guest_count=250,
        address="דרך המשי 45",
        city="תל אביב",
        notes="חתונה גדולה, דרישות כשרות למהדרין",
        total_price=75000.0
    )
    db.add(event1)
    db.flush()
    
    # בעלי אירוע לחתונה
    db.add_all([
        EventOwner(event_id=event1.id, name="יוסי כהן", phone="050-1234567", email="yossi@email.com", order=1),
        EventOwner(event_id=event1.id, name="שרה לוי", phone="050-2345678", email="sara@email.com", order=2),
    ])
    
    # הוספת מנות לאירוע
    db.add_all([
        EventDish(event_id=event1.id, dish_id=dishes[0].id, quantity=250, notes="לכל אורח"),  # סלט
        EventDish(event_id=event1.id, dish_id=dishes[4].id, quantity=250, notes="מנה עיקרית"),  # חזה עוף
        EventDish(event_id=event1.id, dish_id=dishes[3].id, quantity=250, notes="תוספת"),  # אורז
    ])
    
    # אירוע 2: בר מצווה קרובה - עם בעל אירוע אחד (אבא)
    event2 = Event(
        name="בר מצווה של דניאל לוי",
        menu_type=MenuType.MEAT_MENU,
        status="scheduled",
        date=today + timedelta(days=14),
        hebrew_date="ב׳ באדר התשפ״ו",
        guest_count=120,
        address="רחוב הרב קוק 10",
        city="בני ברק",
        notes="קהל דתי, כשרות מהדרין",
        total_price=35000.0
    )
    db.add(event2)
    db.flush()
    
    # בעל אירוע אחד
    db.add(EventOwner(event_id=event2.id, name="משה לוי", phone="052-9876543", email="moshe.levi@gmail.com", order=1))
    
    db.add_all([
        EventDish(event_id=event2.id, dish_id=dishes[0].id, quantity=120),  # סלט
        EventDish(event_id=event2.id, dish_id=dishes[1].id, quantity=120),  # שניצל
        EventDish(event_id=event2.id, dish_id=dishes[3].id, quantity=120),  # אורז
    ])
    
    # אירוע 3: שבע ברכות - עם 3 בעלי אירוע (חתן, כלה, והורים)
    event3 = Event(
        name="שבע ברכות משפחת גולדשטיין",
        menu_type=MenuType.SHABBAT,
        status="pending",
        date=today + timedelta(days=5),
        hebrew_date="כ״ה בשבט התשפ״ו",
        guest_count=80,
        address="רחוב ויצמן 25",
        city="רמת גן",
        notes="ארוחת ערב מפוארת",
        total_price=18000.0
    )
    db.add(event3)
    db.flush()
    
    # 3 בעלי אירוע
    db.add_all([
        EventOwner(event_id=event3.id, name="יעקב גולדשטיין", phone="054-5551234", email="yaakov@email.com", order=1),
        EventOwner(event_id=event3.id, name="מרים גולדשטיין", phone="054-5551235", order=2),
        EventOwner(event_id=event3.id, name="אברהם גולדשטיין (אבא)", phone="054-5551236", email="avraham@email.com", order=3),
    ])
    
    db.add_all([
        EventDish(event_id=event3.id, dish_id=dishes[0].id, quantity=80),  # סלט
        EventDish(event_id=event3.id, dish_id=dishes[2].id, quantity=80),  # פסטה
    ])
    
    # אירוע 4: אירוע שאושר - עם בעל אירוע אחד
    event4 = Event(
        name="ברית של משפחת רוזנברג",
        menu_type=MenuType.DAIRY_MENU,
        status="completed",
        date=today - timedelta(days=10),
        hebrew_date="י״ב בשבט התשפ״ו",
        guest_count=60,
        address="רחוב הרצל 1",
        city="ירושלים",
        notes="ברית בוקר - ארוחת בוקר קלה",
        total_price=8000.0
    )
    db.add(event4)
    db.flush()
    
    db.add(EventOwner(event_id=event4.id, name="דוד רוזנברג", phone="053-7778888", email="david.r@email.com", order=1))
    
    db.add_all([
        EventDish(event_id=event4.id, dish_id=dishes[0].id, quantity=60),
    ])
    
    # אירוע 5: אירוע עתידי בלי בעלי אירוע עדיין
    event5 = Event(
        name="חגיגת יום הולדת 50 - משפחת כץ",
        menu_type=MenuType.MEAT_TRAYS,
        status="pending",
        date=today + timedelta(days=45),
        guest_count=100,
        notes="מסיבת הפתעה, צריך לתאם עוד פרטים",
        total_price=0.0
    )
    db.add(event5)
    
    # אירוע 6: אירוע חדש עם 4 בעלי אירוע (מספר שותפים)
    event6 = Event(
        name="אירוע חברה - סיום פרויקט",
        menu_type=MenuType.MEAT_MENU,
        status="scheduled",
        date=today + timedelta(days=20),
        hebrew_date="ח׳ באדר התשפ״ו",
        guest_count=150,
        address="שדרות רוטשילד 99",
        city="תל אביב",
        notes="אירוע עסקי חגיגי לסיום פרויקט גדול",
        total_price=45000.0
    )
    db.add(event6)
    db.flush()
    
    # 4 בעלי אירוע - שותפים בחברה
    db.add_all([
        EventOwner(event_id=event6.id, name="אמיר בן דוד", phone="050-1111111", email="amir@company.com", order=1),
        EventOwner(event_id=event6.id, name="יונתן שמש", phone="050-2222222", email="yonatan@company.com", order=2),
        EventOwner(event_id=event6.id, name="נועה ישראלי", phone="050-3333333", email="noa@company.com", order=3),
        EventOwner(event_id=event6.id, name="רונית אברהמי", phone="050-4444444", email="ronit@company.com", order=4),
    ])
    
    db.commit()
    print(f"✅ נוספו 6 אירועים")


def main():
    """הפונקציה הראשית"""
    print("=" * 50)
    print("🚀 מתחיל מילוי נתונים ל-DB")
    print("=" * 50)
    
    # אתחול DB
    init_db()
    
    db = SessionLocal()
    try:
        # אתחול נתוני lookup
        print("\n📋 מאתחל נתוני Lookup...")
        initialize_lookup_data(db)
        
        # מחיקת נתונים קודמים
        clear_all_data(db)
        
        # מילוי נתונים
        products = populate_products(db)
        tools = populate_tools(db)
        dishes = populate_dishes(db, products, tools)
        populate_events(db, dishes)
        
        print("\n" + "=" * 50)
        print("✅ המילוי הושלם בהצלחה!")
        print("=" * 50)
        print(f"\n📊 סיכום:")
        print(f"   • {len(products)} מוצרים")
        print(f"   • {len(tools)} כלים וציוד")
        print(f"   • {len(dishes)} מנות")
        print(f"   • 5 אירועים")
        print(f"\n🌐 כעת תוכל לפתוח את Swagger ולראות את הכל:")
        print(f"   http://localhost:8000/docs")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ שגיאה: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
