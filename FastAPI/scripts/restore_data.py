"""
Restore all data into the database.
Run with: python scripts/restore_data.py

This script:
1. Clears all existing data (preserves table structure)
2. Inserts all backed-up data with correct IDs
3. Works with the CLEAN schema (no legacy fields)

Data snapshot from: 2026-02-04
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import text
from app.core.database import SessionLocal, engine


# ============================================================
# DATA
# ============================================================

PRODUCT_CATEGORIES = [
    {"id": 1, "name": "ירקות"},
    {"id": 2, "name": "פירות"},
    {"id": 3, "name": "בשר ועוף"},
    {"id": 4, "name": "דגים"},
    {"id": 5, "name": "מוצרי חלב"},
    {"id": 6, "name": "מזווה ויבשים"},
    {"id": 7, "name": "רטבים ותבלינים"},
    {"id": 8, "name": "מאפה"},
]

PRODUCTS = [
    {"id": 1, "name": "גזר", "category_id": 1, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 2, "name": "סלרי", "category_id": 1, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 3, "name": "פלפל בצבעים", "category_id": 1, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 4, "name": "תירס גמדי", "category_id": 1, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 5, "name": "נבטים", "category_id": 1, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 6, "name": "שום", "category_id": 1, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 7, "name": "בצל ירוק", "category_id": 1, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 8, "name": "חסה", "category_id": 1, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 9, "name": "פטריות שמפיניון", "category_id": 1, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 10, "name": "עגבניות שרי", "category_id": 1, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 11, "name": "בצל סגול", "category_id": 1, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 12, "name": "כרוב לבן", "category_id": 1, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 13, "name": "כרוב סגול", "category_id": 1, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 14, "name": "סלק", "category_id": 1, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 15, "name": "חציל", "category_id": 1, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 16, "name": "גמבה", "category_id": 1, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 17, "name": "עגבניה", "category_id": 1, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 18, "name": "בטטה", "category_id": 1, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 19, "name": "מלפפון", "category_id": 1, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 20, "name": "פלפל חריף", "category_id": 1, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 21, "name": "קישוא", "category_id": 1, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 22, "name": "בצל", "category_id": 1, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 23, "name": "שעועית ירוקה", "category_id": 1, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 24, "name": "דלעת", "category_id": 1, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 25, "name": "פטרוזיליה", "category_id": 1, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 26, "name": "שמיר", "category_id": 1, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 27, "name": "עלים ירוקים", "category_id": 1, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 28, "name": "תפוח", "category_id": 2, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 29, "name": "אננס", "category_id": 2, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 30, "name": "חמוציות", "category_id": 2, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 31, "name": "אוכמניות", "category_id": 2, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 32, "name": "תות", "category_id": 2, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 33, "name": "פירות העונה", "category_id": 2, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 34, "name": "צימוקים", "category_id": 2, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 35, "name": "בקר", "category_id": 3, "unit": "KG", "kosher_type": "MEAT", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 36, "name": "הודו", "category_id": 3, "unit": "KG", "kosher_type": "MEAT", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 37, "name": "פרגית", "category_id": 3, "unit": "KG", "kosher_type": "MEAT", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 38, "name": "כרעיים עוף", "category_id": 3, "unit": "KG", "kosher_type": "MEAT", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 39, "name": "חזה עוף", "category_id": 3, "unit": "KG", "kosher_type": "MEAT", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 40, "name": "כבד עוף", "category_id": 3, "unit": "KG", "kosher_type": "MEAT", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 41, "name": "המבורגר", "category_id": 3, "unit": "KG", "kosher_type": "MEAT", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 42, "name": "קבב", "category_id": 3, "unit": "KG", "kosher_type": "MEAT", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 43, "name": "נקניקיות", "category_id": 3, "unit": "KG", "kosher_type": "MEAT", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 44, "name": "סלמון", "category_id": 4, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 45, "name": "מושט", "category_id": 4, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 46, "name": "טונה", "category_id": 4, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 47, "name": "הרינג", "category_id": 4, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 48, "name": "גבינה צהובה", "category_id": 5, "unit": "UNIT", "kosher_type": "DAIRY", "min_stock_level": 5.0, "inventory_status": "אזל"},
    {"id": 49, "name": "גבינת פטה", "category_id": 5, "unit": "UNIT", "kosher_type": "DAIRY", "min_stock_level": 5.0, "inventory_status": "אזל"},
    {"id": 50, "name": "גבינה בולגרית", "category_id": 5, "unit": "UNIT", "kosher_type": "DAIRY", "min_stock_level": 5.0, "inventory_status": "אזל"},
    {"id": 51, "name": "גבינת חלומי", "category_id": 5, "unit": "UNIT", "kosher_type": "DAIRY", "min_stock_level": 5.0, "inventory_status": "אזל"},
    {"id": 52, "name": "גבינה לבנה", "category_id": 5, "unit": "UNIT", "kosher_type": "DAIRY", "min_stock_level": 5.0, "inventory_status": "אזל"},
    {"id": 53, "name": "קוטג'", "category_id": 5, "unit": "UNIT", "kosher_type": "DAIRY", "min_stock_level": 5.0, "inventory_status": "אזל"},
    {"id": 54, "name": "יוגורט", "category_id": 5, "unit": "UNIT", "kosher_type": "DAIRY", "min_stock_level": 5.0, "inventory_status": "אזל"},
    {"id": 55, "name": "שמנת מתוקה", "category_id": 5, "unit": "LITER", "kosher_type": "DAIRY", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 56, "name": "אורז", "category_id": 6, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 57, "name": "בורגול", "category_id": 6, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 58, "name": "קינואה", "category_id": 6, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 59, "name": "פסטה", "category_id": 6, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 60, "name": "אטריות", "category_id": 6, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 61, "name": "קוסקוס", "category_id": 6, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 62, "name": "גריסים", "category_id": 6, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 63, "name": "שעועית יבשה", "category_id": 6, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 64, "name": "גרגירי חומוס", "category_id": 6, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 65, "name": "אגוזי מלך", "category_id": 6, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 66, "name": "פקאן", "category_id": 6, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 67, "name": "שקדים", "category_id": 6, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 68, "name": "שומשום", "category_id": 6, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 69, "name": "גרעיני חמניה", "category_id": 6, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 70, "name": "פיצוחים", "category_id": 6, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 71, "name": "קרוטונים", "category_id": 6, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 72, "name": "גרנולה", "category_id": 6, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 73, "name": "פירורי לחם", "category_id": 6, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 74, "name": "קמח", "category_id": 6, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 75, "name": "סוכר", "category_id": 6, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 76, "name": "דפי לזניה", "category_id": 6, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 77, "name": "עלים לסיגר", "category_id": 6, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 78, "name": "בצק פילו", "category_id": 6, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 79, "name": "שוקולד", "category_id": 6, "unit": "GRAM", "kosher_type": "PARVE", "min_stock_level": 500.0, "inventory_status": "אזל"},
    {"id": 80, "name": "קקאו", "category_id": 6, "unit": "GRAM", "kosher_type": "PARVE", "min_stock_level": 500.0, "inventory_status": "אזל"},
    {"id": 81, "name": "קפה", "category_id": 6, "unit": "GRAM", "kosher_type": "PARVE", "min_stock_level": 500.0, "inventory_status": "אזל"},
    {"id": 82, "name": "קצפת צמחית", "category_id": 6, "unit": "LITER", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 83, "name": "שמן זית", "category_id": 6, "unit": "LITER", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 84, "name": "שמן קנולה", "category_id": 6, "unit": "LITER", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 85, "name": "מיונז", "category_id": 7, "unit": "LITER", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 86, "name": "טחינה", "category_id": 7, "unit": "LITER", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 87, "name": "צ'ילי מתוק", "category_id": 7, "unit": "LITER", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 88, "name": "סילאן", "category_id": 7, "unit": "LITER", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 89, "name": "דבש", "category_id": 7, "unit": "LITER", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 90, "name": "חרדל", "category_id": 7, "unit": "LITER", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 91, "name": "טריאקי", "category_id": 7, "unit": "LITER", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 92, "name": "פסטו", "category_id": 7, "unit": "LITER", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 93, "name": "ברביקיו", "category_id": 7, "unit": "LITER", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 94, "name": "מייפל", "category_id": 7, "unit": "LITER", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 95, "name": "ריבת חלב", "category_id": 7, "unit": "LITER", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 96, "name": "זעתר", "category_id": 7, "unit": "GRAM", "kosher_type": "PARVE", "min_stock_level": 500.0, "inventory_status": "אזל"},
    {"id": 97, "name": "מלפפון חמוץ", "category_id": 7, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 98, "name": "זיתים ירוקים", "category_id": 7, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 99, "name": "זיתים שחורים", "category_id": 7, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 100, "name": "שיפקה", "category_id": 7, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "אזל"},
    {"id": 101, "name": "לחמניות", "category_id": 8, "unit": "UNIT", "kosher_type": "PARVE", "min_stock_level": 5.0, "inventory_status": "אזל"},
    {"id": 102, "name": "באגט", "category_id": 8, "unit": "UNIT", "kosher_type": "PARVE", "min_stock_level": 5.0, "inventory_status": "אזל"},
    {"id": 103, "name": "פרנה", "category_id": 8, "unit": "UNIT", "kosher_type": "PARVE", "min_stock_level": 5.0, "inventory_status": "אזל"},
    {"id": 104, "name": "בייגל", "category_id": 8, "unit": "UNIT", "kosher_type": "PARVE", "min_stock_level": 5.0, "inventory_status": "אזל"},
    {"id": 105, "name": "קרואסון", "category_id": 8, "unit": "UNIT", "kosher_type": "PARVE", "min_stock_level": 5.0, "inventory_status": "אזל"},
    {"id": 106, "name": "לחם דגנים", "category_id": 8, "unit": "UNIT", "kosher_type": "PARVE", "min_stock_level": 5.0, "inventory_status": "אזל"},
    {"id": 107, "name": "בריוש", "category_id": 8, "unit": "UNIT", "kosher_type": "PARVE", "min_stock_level": 5.0, "inventory_status": "אזל"},
    {"id": 108, "name": "טורטיה", "category_id": 8, "unit": "UNIT", "kosher_type": "PARVE", "min_stock_level": 5.0, "inventory_status": "אזל"},
    {"id": 109, "name": "ביצים", "category_id": 5, "unit": "UNIT", "kosher_type": "PARVE", "min_stock_level": 5.0, "inventory_status": "אזל"},
    {"id": 110, "name": "תירס", "category_id": 1, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0, "inventory_status": "במלאי", "package_quantity": 123.0, "estimated_price": 456.0, "supplier": "123", "brand": "אסם"},
    {"id": 111, "name": "אפונה", "category_id": 1, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0},
    {"id": 112, "name": "אסאדו", "category_id": 3, "unit": "KG", "kosher_type": "MEAT", "min_stock_level": 2.0},
    {"id": 113, "name": "ביצי דגים", "category_id": 4, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0},
    {"id": 114, "name": "בורקס", "category_id": 6, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0},
    {"id": 115, "name": "פחזניות", "category_id": 6, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0},
    {"id": 116, "name": "חלווה", "category_id": 6, "unit": "KG", "kosher_type": "PARVE", "min_stock_level": 2.0},
    {"id": 117, "name": "ג'לטין", "category_id": 6, "unit": "GRAM", "kosher_type": "PARVE", "min_stock_level": 500.0},
    {"id": 118, "name": "פקטין", "category_id": 6, "unit": "GRAM", "kosher_type": "PARVE", "min_stock_level": 500.0},
    {"id": 119, "name": "ממרח עגבניות מיובשות", "category_id": 7, "unit": "LITER", "kosher_type": "PARVE", "min_stock_level": 2.0},
    {"id": 120, "name": "לחמניות בריוש", "category_id": 8, "unit": "UNIT", "kosher_type": "PARVE", "min_stock_level": 5.0},
]

MENU_TEMPLATES = [
    {"id": 1, "menu_type": "SHABBAT", "name_hebrew": "שבת", "description": "תפריט שבת מסורתי - ליל שבת ושבת בוקר"},
    {"id": 2, "menu_type": "SWEET_TABLE", "name_hebrew": "שולחן מתוק", "description": "שולחן מתוק לאירועים"},
    {"id": 3, "menu_type": "DAIRY_TRAYS", "name_hebrew": "מגשי אירוח חלבי", "description": "מגשי אירוח חלבי לאירועים"},
    {"id": 4, "menu_type": "MEAT_TRAYS", "name_hebrew": "מגשי אירוח בשרי", "description": "מגשי אירוח בשרי לאירועים"},
    {"id": 5, "menu_type": "MEAT_MENU", "name_hebrew": "בשרי (אירועים)", "description": "תפריט בשרי מלא לאירועים"},
    {"id": 6, "menu_type": "DAIRY_MENU", "name_hebrew": "חלבי (אירועים)", "description": "תפריט חלבי מלא לאירועים"},
]

MENU_CATEGORIES = [
    {"id": 1, "template_id": 1, "name": "friday_salads", "name_hebrew": "ליל שבת-סלטים", "display_order": 1, "quota": 5, "is_required": 1},
    {"id": 2, "template_id": 1, "name": "friday_first", "name_hebrew": "ליל שבת-מנה ראשונה", "display_order": 2, "quota": 1, "is_required": 1},
    {"id": 3, "template_id": 1, "name": "friday_main", "name_hebrew": "ליל שבת-עיקרית", "display_order": 3, "quota": 1, "is_required": 1},
    {"id": 4, "template_id": 1, "name": "friday_sides", "name_hebrew": "ליל שבת-תוספות", "display_order": 4, "quota": 3, "is_required": 1},
    {"id": 5, "template_id": 1, "name": "saturday_salads", "name_hebrew": "שבת בוקר-סלטים", "display_order": 5, "quota": 5, "is_required": 1},
    {"id": 6, "template_id": 1, "name": "saturday_main", "name_hebrew": "שבת בוקר-עיקרית", "display_order": 6, "quota": 1, "is_required": 1},
    {"id": 7, "template_id": 2, "name": "salads", "name_hebrew": "סלטים", "display_order": 1, "quota": 3, "is_required": 1},
    {"id": 8, "template_id": 2, "name": "pastries", "name_hebrew": "מאפים", "display_order": 2, "quota": 4, "is_required": 1},
    {"id": 9, "template_id": 2, "name": "sides", "name_hebrew": "תוספות", "display_order": 3, "quota": 2, "is_required": 1},
    {"id": 10, "template_id": 3, "name": "sandwiches", "name_hebrew": "כריכים", "display_order": 1, "quota": 3, "is_required": 1},
    {"id": 11, "template_id": 3, "name": "pastries", "name_hebrew": "מאפים וטורטיות", "display_order": 2, "quota": 3, "is_required": 1},
    {"id": 12, "template_id": 3, "name": "sides", "name_hebrew": "תוספות ומוקרמים", "display_order": 3, "quota": 3, "is_required": 1},
    {"id": 13, "template_id": 3, "name": "salads", "name_hebrew": "סלטים", "display_order": 4, "quota": 4, "is_required": 1},
    {"id": 14, "template_id": 3, "name": "spreads", "name_hebrew": "ממרחים", "display_order": 5, "quota": 2, "is_required": 1},
    {"id": 15, "template_id": 3, "name": "cheeses", "name_hebrew": "גבינות", "display_order": 6, "quota": 3, "is_required": 1},
    {"id": 16, "template_id": 3, "name": "desserts", "name_hebrew": "קינוחים", "display_order": 7, "quota": 2, "is_required": 1},
    {"id": 17, "template_id": 4, "name": "sandwiches", "name_hebrew": "כריכים", "display_order": 1, "quota": 3, "is_required": 1},
    {"id": 18, "template_id": 4, "name": "salads", "name_hebrew": "סלטים", "display_order": 2, "quota": 4, "is_required": 1},
    {"id": 19, "template_id": 4, "name": "sides", "name_hebrew": "תוספות", "display_order": 3, "quota": 3, "is_required": 1},
    {"id": 20, "template_id": 4, "name": "meats", "name_hebrew": "בשרים ועופות", "display_order": 4, "quota": 3, "is_required": 1},
    {"id": 21, "template_id": 4, "name": "fish", "name_hebrew": "דגים", "display_order": 5, "quota": 2, "is_required": 1},
    {"id": 22, "template_id": 4, "name": "desserts", "name_hebrew": "קינוחים", "display_order": 6, "quota": 2, "is_required": 1},
    {"id": 23, "template_id": 5, "name": "salads", "name_hebrew": "סלטים", "display_order": 1, "quota": 5, "is_required": 1},
    {"id": 24, "template_id": 5, "name": "first_course", "name_hebrew": "מנה ראשונה", "display_order": 2, "quota": 1, "is_required": 1},
    {"id": 25, "template_id": 5, "name": "main_course", "name_hebrew": "עיקרית", "display_order": 3, "quota": 1, "is_required": 1},
    {"id": 26, "template_id": 5, "name": "sides", "name_hebrew": "תוספות", "display_order": 4, "quota": 3, "is_required": 1},
    {"id": 27, "template_id": 5, "name": "desserts", "name_hebrew": "קינוחים", "display_order": 5, "quota": 1, "is_required": 1},
    {"id": 28, "template_id": 6, "name": "salads", "name_hebrew": "סלטים", "display_order": 1, "quota": 5, "is_required": 1},
    {"id": 29, "template_id": 6, "name": "soups", "name_hebrew": "מרקים", "display_order": 2, "quota": 1, "is_required": 1},
    {"id": 30, "template_id": 6, "name": "fish", "name_hebrew": "עיקרית-דגים", "display_order": 3, "quota": 1, "is_required": 1},
    {"id": 31, "template_id": 6, "name": "casseroles", "name_hebrew": "מוקרמים ומאפים", "display_order": 4, "quota": 2, "is_required": 1},
    {"id": 32, "template_id": 6, "name": "vegetables", "name_hebrew": "ירקות", "display_order": 5, "quota": 2, "is_required": 1},
    {"id": 33, "template_id": 6, "name": "desserts", "name_hebrew": "קינוחים", "display_order": 6, "quota": 1, "is_required": 1},
]

# Dishes data loaded from backup_data.json
DISHES_DATA = None  # Will be loaded from JSON file
DISH_INGREDIENTS_DATA = None
DISH_MENU_MAPPINGS_DATA = None
LOOKUP_DATA = None
EVENTS_DATA = None


def load_from_json():
    """Load complex data from the JSON backup file"""
    import json
    json_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'backup_data.json')
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data


def restore_all():
    """Restore all data into the database"""
    db = SessionLocal()
    backup = load_from_json()
    
    try:
        print("🗑️  Clearing all existing data...")
        # Delete in correct order (children first)
        tables_to_clear = [
            "dish_ingredients", "dish_equipment", "serving_dishes", "dish_menu_mappings",
            "event_dishes", "event_owners", "events",
            "dishes", "products", "product_categories",
            "menu_categories", "menu_templates",
            "lookup_data", "tools"
        ]
        for table in tables_to_clear:
            db.execute(text(f"DELETE FROM {table}"))
        db.commit()
        print("   ✅ All tables cleared")
        
        # 1. Product categories
        print("\n📦 Restoring product_categories...")
        for cat in PRODUCT_CATEGORIES:
            db.execute(text(
                "INSERT INTO product_categories (id, name) VALUES (:id, :name)"
            ), cat)
        db.commit()
        print(f"   ✅ {len(PRODUCT_CATEGORIES)} categories")
        
        # 2. Products
        print("📦 Restoring products...")
        for p in PRODUCTS:
            db.execute(text("""
                INSERT INTO products (id, name, category_id, unit, kosher_type, 
                    min_stock_level, inventory_status, quantity_in_stock,
                    package_quantity, price_per_unit, estimated_price,
                    supplier, brand, barcode, notes, description)
                VALUES (:id, :name, :category_id, :unit, :kosher_type,
                    :min_stock_level, :inventory_status, 0,
                    :package_quantity, :price_per_unit, :estimated_price,
                    :supplier, :brand, :barcode, :notes, :description)
            """), {
                "id": p["id"], "name": p["name"], "category_id": p["category_id"],
                "unit": p["unit"], "kosher_type": p["kosher_type"],
                "min_stock_level": p.get("min_stock_level", 0),
                "inventory_status": p.get("inventory_status"),
                "package_quantity": p.get("package_quantity"),
                "price_per_unit": p.get("price_per_unit"),
                "estimated_price": p.get("estimated_price"),
                "supplier": p.get("supplier"),
                "brand": p.get("brand"),
                "barcode": p.get("barcode"),
                "notes": p.get("notes"),
                "description": p.get("description"),
            })
        db.commit()
        print(f"   ✅ {len(PRODUCTS)} products")
        
        # 3. Menu templates
        print("📦 Restoring menu_templates...")
        for t in MENU_TEMPLATES:
            db.execute(text(
                "INSERT INTO menu_templates (id, menu_type, name_hebrew, description) VALUES (:id, :menu_type, :name_hebrew, :description)"
            ), t)
        db.commit()
        print(f"   ✅ {len(MENU_TEMPLATES)} templates")
        
        # 4. Menu categories
        print("📦 Restoring menu_categories...")
        for mc in MENU_CATEGORIES:
            db.execute(text("""
                INSERT INTO menu_categories (id, template_id, name, name_hebrew, display_order, quota, is_required)
                VALUES (:id, :template_id, :name, :name_hebrew, :display_order, :quota, :is_required)
            """), mc)
        db.commit()
        print(f"   ✅ {len(MENU_CATEGORIES)} categories")
        
        # 5. Dishes (from JSON)
        dishes = backup.get("dishes", [])
        print(f"📦 Restoring dishes...")
        for d in dishes:
            db.execute(text("""
                INSERT INTO dishes (id, name, category, kosher_type, description,
                    price_per_unit, estimated_price, client_price, serving_size,
                    serving_description, waiter_notes, is_active, image_url)
                VALUES (:id, :name, :category, :kosher_type, :description,
                    :price_per_unit, :estimated_price, :client_price, :serving_size,
                    :serving_description, :waiter_notes, :is_active, :image_url)
            """), d)
        db.commit()
        print(f"   ✅ {len(dishes)} dishes")
        
        # 6. Dish ingredients (from JSON)
        ingredients = backup.get("dish_ingredients", [])
        print(f"📦 Restoring dish_ingredients...")
        for ing in ingredients:
            db.execute(text("""
                INSERT INTO dish_ingredients (id, dish_id, product_id, name, quantity, unit, is_serving_component)
                VALUES (:id, :dish_id, :product_id, :name, :quantity, :unit, :is_serving_component)
            """), ing)
        db.commit()
        print(f"   ✅ {len(ingredients)} ingredients")
        
        # 7. Dish menu mappings (from JSON)
        mappings = backup.get("dish_menu_mappings", [])
        print(f"📦 Restoring dish_menu_mappings...")
        for m in mappings:
            db.execute(text("""
                INSERT INTO dish_menu_mappings (id, dish_id, menu_type, category_name,
                    is_upgrade, extra_charge, client_price, estimated_price, display_order)
                VALUES (:id, :dish_id, :menu_type, :category_name,
                    :is_upgrade, :extra_charge, :client_price, :estimated_price, :display_order)
            """), m)
        db.commit()
        print(f"   ✅ {len(mappings)} mappings")
        
        # 8. Lookup data (from JSON)
        lookups = backup.get("lookup_data", [])
        print(f"📦 Restoring lookup_data...")
        for l in lookups:
            db.execute(text("""
                INSERT INTO lookup_data (id, category, value, display_order, is_default)
                VALUES (:id, :category, :value, :display_order, :is_default)
            """), l)
        db.commit()
        print(f"   ✅ {len(lookups)} lookup entries")
        
        # 9. Events (from JSON, migrated: event_type → menu_type)
        events = backup.get("events", [])
        print(f"📦 Restoring events...")
        EVENT_TYPE_TO_MENU_TYPE = {
            "שבת": "SHABBAT",
            "בשרי": "MEAT_MENU",
            "חלבי": "DAIRY_MENU",
        }
        for e in events:
            menu_type = e.get("menu_type") or EVENT_TYPE_TO_MENU_TYPE.get(e.get("event_type"))
            db.execute(text("""
                INSERT INTO events (id, name, menu_type, status, date, event_time,
                    hebrew_date, address, city, guest_count, is_disposable, notes, total_price)
                VALUES (:id, :name, :menu_type, :status, :date, :event_time,
                    :hebrew_date, :address, :city, :guest_count, :is_disposable, :notes, :total_price)
            """), {
                "id": e["id"], "name": e["name"], "menu_type": menu_type,
                "status": e["status"], "date": e["date"], "event_time": e.get("event_time"),
                "hebrew_date": e.get("hebrew_date"), "address": e.get("address"),
                "city": e.get("city"), "guest_count": e.get("guest_count", 1),
                "is_disposable": e.get("is_disposable", 0),
                "notes": e.get("notes", ""), "total_price": e.get("total_price", 0),
            })
        db.commit()
        print(f"   ✅ {len(events)} events (event_type migrated → menu_type)")
        
        # 10. Event owners (from JSON)
        owners = backup.get("event_owners", [])
        if owners:
            print(f"📦 Restoring event_owners...")
            for o in owners:
                db.execute(text("""
                    INSERT INTO event_owners (id, event_id, name, phone, email, "order")
                    VALUES (:id, :event_id, :name, :phone, :email, :order)
                """), o)
            db.commit()
            print(f"   ✅ {len(owners)} owners")
        
        # 11. Event dishes (from JSON)
        event_dishes = backup.get("event_dishes", [])
        if event_dishes:
            print(f"📦 Restoring event_dishes...")
            for ed in event_dishes:
                db.execute(text("""
                    INSERT INTO event_dishes (id, event_id, dish_id, quantity, is_draft, notes)
                    VALUES (:id, :event_id, :dish_id, :quantity, :is_draft, :notes)
                """), ed)
            db.commit()
            print(f"   ✅ {len(event_dishes)} event dishes")
        
        # Reset SQLite autoincrement sequences
        print("\n🔄 Resetting autoincrement sequences...")
        for table in ["product_categories", "products", "menu_templates", "menu_categories",
                       "dishes", "dish_ingredients", "dish_menu_mappings", "lookup_data",
                       "events", "event_owners", "event_dishes"]:
            db.execute(text(f"DELETE FROM sqlite_sequence WHERE name='{table}'"))
            db.execute(text(f"""
                INSERT OR REPLACE INTO sqlite_sequence (name, seq) 
                SELECT '{table}', MAX(id) FROM {table}
            """))
        db.commit()
        print("   ✅ Sequences reset")
        
        print("\n✅ All data restored successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    restore_all()
