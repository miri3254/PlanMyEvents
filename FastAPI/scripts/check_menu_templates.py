"""Check current menu templates state."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import SessionLocal
from app.models.menu import MenuTemplate

db = SessionLocal()

# Check current state
templates = db.query(MenuTemplate).filter(MenuTemplate.is_deleted == False).order_by(MenuTemplate.id).all()
print('=== Current Menu Templates ===')
for t in templates:
    print(f'ID={t.id} | menu_type="{t.menu_type}" | name="{t.name}"')

db.close()
