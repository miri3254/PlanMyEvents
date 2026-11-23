"""Apply only the additive menu serving mode migration to the configured local SQLite DB.

Dry run by default. --apply first creates a consistent SQLite backup; no product
records or approved calculation snapshots are changed or merged.
"""
import argparse
from datetime import datetime
from pathlib import Path
import sqlite3
import sys

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    from app.db.engine import engine
    from sqlalchemy import inspect, text
    from alembic.config import Config
    from alembic import command

    if engine.dialect.name != 'sqlite':
        raise RuntimeError('This helper supports local SQLite only')
    source = Path(engine.url.database).resolve()
    if not source.is_relative_to(BASE) or not source.is_file():
        raise RuntimeError('Database must be an existing file within FastAPI')
    with engine.connect() as conn:
        revisions = conn.execute(text('SELECT version_num FROM alembic_version')).scalars().all()
    if revisions == ['p9e0f1a2b3c4']:
        print('Menu serving mode migration already applied')
        return
    if revisions != ['o8d9e0f1a2b3']:
        raise RuntimeError('Unexpected migration baseline; no changes made')
    if any(c['name']=='default_serving_mode' for c in inspect(engine).get_columns('dish_menu_mappings')):
        raise RuntimeError('Column already present at unexpected revision; no changes made')
    if not args.apply:
        print('Ready: additive menu serving mode columns; use --apply')
        return

    folder = source.parent / 'backups'
    folder.mkdir(exist_ok=True)
    backup = folder / f"before_default_serving_mode_{datetime.now():%Y%m%d_%H%M%S_%f}.db"
    raw = engine.raw_connection()
    try:
        with sqlite3.connect(backup) as target:
            raw.driver_connection.backup(target)
    finally:
        raw.close()
    config = Config(str(BASE / 'alembic.ini'))
    config.set_main_option('script_location', str(BASE / 'alembic'))
    config.set_main_option('sqlalchemy.url', engine.url.render_as_string(hide_password=False).replace('%','%%'))
    command.upgrade(config, 'p9e0f1a2b3c4')
    with engine.connect() as conn:
        assert conn.execute(text('PRAGMA quick_check')).scalar() == 'ok'
        assert conn.execute(text('SELECT version_num FROM alembic_version')).scalar() == 'p9e0f1a2b3c4'
    print('Migration applied; database integrity OK. Backup:', backup)


if __name__ == '__main__':
    main()
