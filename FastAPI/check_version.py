import sqlite3

conn = sqlite3.connect('data/planmyevents.db')
cursor = conn.cursor()
cursor.execute("SELECT * FROM alembic_version")
version = cursor.fetchall()
print("Alembic version:")
for row in version:
    print(f"  - {row[0]}")
conn.close()
