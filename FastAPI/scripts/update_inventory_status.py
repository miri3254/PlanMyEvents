"""
עדכון סטטוס מלאי לכל המוצרים
"""
import sys
import os
from pathlib import Path

# הוספת הנתיב של app לפייתון
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.product import Product


def calculate_inventory_status(product: Product) -> str:
    """חישוב סטטוס מלאי"""
    quantity = product.quantity_in_stock or 0
    min_level = product.min_stock_level or 0
    if quantity <= 0:
        return "אזל"
    elif quantity <= min_level:
        return "מלאי-נמוך"
    return "במלאי"


def update_all_statuses(db: Session):
    """עדכון סטטוס מלאי לכל המוצרים"""
    print("מעדכן סטטוסי מלאי...")
    
    products = db.query(Product).all()
    updated = 0
    
    for product in products:
        new_status = calculate_inventory_status(product)
        if product.inventory_status != new_status:
            product.inventory_status = new_status
            updated += 1
    
    db.commit()
    
    print(f"✓ עודכנו {updated} מוצרים מתוך {len(products)}")
    
    # סיכום
    status_counts = {}
    for product in products:
        status = product.inventory_status or "לא מוגדר"
        status_counts[status] = status_counts.get(status, 0) + 1
    
    print("\nסיכום סטטוסי מלאי:")
    for status, count in status_counts.items():
        print(f"  {status}: {count} מוצרים")


def main():
    db = SessionLocal()
    try:
        update_all_statuses(db)
    except Exception as e:
        print(f"❌ שגיאה: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
