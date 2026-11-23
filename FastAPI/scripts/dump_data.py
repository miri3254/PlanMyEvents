"""Dump all DB data to JSON file for backup."""
import sqlite3
import json
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'planmyevents.db')
OUT_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'backup_data.json')

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'alembic_version' ORDER BY name")
tables = [r['name'] for r in cur.fetchall()]

all_data = {}
for table in tables:
    cur.execute(f"SELECT * FROM {table}")
    rows = [dict(r) for r in cur.fetchall()]
    all_data[table] = rows
    print(f"  {table}: {len(rows)} rows")

with open(OUT_PATH, 'w', encoding='utf-8') as f:
    json.dump(all_data, f, ensure_ascii=False, default=str, indent=2)

print(f"\nBackup saved to: {OUT_PATH}")
conn.close()
