from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.db.base import Base


class LookupData(Base):
    """
    נתוני בסיס - טבלה גנרית לכל הרשימות הקבועות
    כל רשימה מזוהה לפי category ומכילה ערכים
    """
    __tablename__ = "lookup_data"
    
    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(100), nullable=False, index=True)
    value = Column(String(255), nullable=False)
    display_order = Column(Integer, default=0)
    is_default = Column(Integer, default=0)  # 1 = ברירת מחדל
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


# קטגוריות lookup זמינות
LOOKUP_CATEGORIES = {
    "dish_categories": "קטגוריות מנות",
    "kosher_types": "סוגי כשרות",
    "measurement_units": "יחידות מידה",
    "product_categories": "קטגוריות מוצרים",
    "inventory_statuses": "סטטוסי מלאי",
    "menu_types": "סוגי תפריט",  # Replaced event_types with menu_types
    "event_categories": "קטגוריות אירוע",
    "event_statuses": "סטטוסי אירוע",
    "tool_categories": "קטגוריות כלים",
    "tool_sub_categories": "תת-קטגוריות כלים",
    "dish_yield_units": "יחידות תפוקה למנה",
}

# ערכי ברירת מחדל
DEFAULT_LOOKUP_VALUES = {
    "dish_categories": ["עיקרית", "ראשונה", "תוספת", "קינוח", "משקה", "חטיף"],
    "kosher_types": ["חלבי", "בשרי", "פרווה"],
    "measurement_units": ["גרם", "ליטר", "יחידות", "כפות", "כוסות", "מ\"ל", "ק\"ג"],
    "product_categories": ["מוצרי מזון", "משקאות", "חטיפים", "מוצרי חלב", "ירקות", "פירות", "בשר", "דגים", "תבלינים", "אחר"],
    "inventory_statuses": ["במלאי", "אזל", "מלאי-נמוך"],
    "menu_types": [],  # נטען דינמית מ-menu_templates.name
    "event_categories": ["בר מצווה", "אירוסים", "שבע ברכות", "אירוע מתוק", "שבת", "מגשי אירוח"],
    "event_statuses": ["טיוטה", "מתוכנן", "בהכנה", "הושלם", "בוטל"],
    "tool_categories": ["מלי הגשה", "צלחות", "סכו\"ם", "כוסות", "קערות", "מגשים", "סירים", "אחר"],
    "tool_sub_categories": ["חד\"פ", "אמיתי"]
}
