"""Prepare reviewed workbook catalogue links. Dry run unless --apply; backup first."""
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
    import app.models
    from app.db.engine import engine
    from sqlalchemy.orm import Session
    from app.services.workbook_tool_import import prepare_workbook_tools
    path = Path(engine.url.database or '').resolve()
    if engine.dialect.name != 'sqlite' or not path.is_relative_to(BASE) or not path.is_file():
        raise RuntimeError('Existing local project SQLite database required')
    if args.apply:
        folder = path.parent / 'backups'; folder.mkdir(exist_ok=True)
        backup = folder / f'before_workbook_tools_{datetime.now():%Y%m%d_%H%M%S_%f}.db'
        raw = engine.raw_connection()
        try:
            with sqlite3.connect(backup) as target:
                raw.driver_connection.backup(target)
        finally:
            raw.close()
        print('Backup:', backup)
    with Session(engine) as db:
        print(prepare_workbook_tools(db))
        if args.apply:
            db.commit()
        else:
            db.rollback()
        print('Applied' if args.apply else 'Dry run: rolled back')

if __name__ == '__main__':
    main()
