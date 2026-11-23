from app.core.database import SessionLocal
from sqlalchemy import text

# Open a database session
db = SessionLocal()

# Update the invalid value
db.execute(text("UPDATE products SET unit = 'KG' WHERE unit = 'יחידות'"))
db.commit()

# Close the session
db.close()

print("Invalid values updated successfully.")