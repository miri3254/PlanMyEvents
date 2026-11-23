import sqlite3

conn = sqlite3.connect('data/planmyevents.db')
cursor = conn.cursor()

# Check if menu_type column exists in events
cursor.execute("PRAGMA table_info(events)")
columns = cursor.fetchall()
print("Events table columns:")
for col in columns:
    print(f"  - {col[1]} ({col[2]})")

# Check event_dishes for is_draft
print("\nEvent_dishes table columns:")
cursor.execute("PRAGMA table_info(event_dishes)")
columns = cursor.fetchall()
for col in columns:
    print(f"  - {col[1]} ({col[2]})")

conn.close()
