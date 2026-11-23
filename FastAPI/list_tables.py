from app.core.database import SessionLocal
from sqlalchemy import inspect

# Open a database session
db = SessionLocal()

# Inspect the database
inspector = inspect(db.get_bind())
tables = inspector.get_table_names()

# Print all tables
print("Tables in the database:", tables)

# Close the session
db.close()
