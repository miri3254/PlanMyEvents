import os
import sys
from sqlalchemy import create_engine, text, inspect

# הוספת נתיב הפרויקט כדי ש-app יזוהה
sys.path.append(os.getcwd())

from app.core.config import settings

def check_table_counts():
    engine = create_engine(settings.DATABASE_URL)
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    print(f"Checking database: {settings.DATABASE_URL}")
    print("-" * 30)
    
    with engine.connect() as connection:
        for table in tables:
            # דילוג על טבלת המערכת של אלמביק
            if table == "alembic_version":
                continue
                
            # שימוש ב-text() כדי למנוע את שגיאת ObjectNotExecutableError
            query = text(f"SELECT COUNT(*) FROM {table}")
            result = connection.execute(query).scalar()
            print(f"Table: {table: <20} | Rows: {result}")

if __name__ == "__main__":
    check_table_counts()