"""
Backup service — safe SQLite database backup.

Performs WAL checkpoint before copying the DB file.
"""

import shutil
from datetime import datetime
from pathlib import Path

from fastapi.responses import FileResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.utils.app_logging import logger


class BackupService:
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()

    def _get_db_path(self) -> Path:
        url = self.settings.DATABASE_URL
        # sqlite:///data/planmyevents.db -> data/planmyevents.db
        path_str = url.replace("sqlite:///", "")
        return Path(path_str)

    def create_backup(self) -> dict:
        db_path = self._get_db_path()
        if not db_path.exists():
            return {"success": False, "message": "קובץ מסד נתונים לא נמצא"}

        # Checkpoint WAL to make sure all data is in the main file
        try:
            self.db.execute(text("PRAGMA wal_checkpoint(FULL)"))
        except Exception as e:
            logger.warning(f"WAL checkpoint failed: {e}")

        # Create backup directory
        backup_dir = db_path.parent / "backups"
        backup_dir.mkdir(exist_ok=True)

        # Copy file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"planmyevents_backup_{timestamp}.db"
        backup_path = backup_dir / backup_name

        try:
            shutil.copy2(str(db_path), str(backup_path))
            logger.info(f"גיבוי נוצר: {backup_path}")
            return {
                "success": True,
                "message": f"גיבוי נוצר בהצלחה: {backup_name}",
                "backup_path": str(backup_path),
                "timestamp": timestamp,
            }
        except Exception as e:
            logger.error(f"שגיאת גיבוי: {e}")
            return {"success": False, "message": f"שגיאה ביצירת גיבוי: {str(e)}"}

    def list_backups(self) -> list[dict]:
        db_path = self._get_db_path()
        backup_dir = db_path.parent / "backups"
        if not backup_dir.exists():
            return []

        backups = []
        for f in sorted(backup_dir.glob("*.db"), reverse=True):
            stat = f.stat()
            backups.append({
                "name": f.name,
                "path": str(f),
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            })
        return backups

    def get_backup_info(self) -> dict:
        """Return info about the main database file."""
        db_path = self._get_db_path()
        if not db_path.exists():
            return {
                "exists": False,
                "size_bytes": 0,
                "size_mb": 0,
                "last_modified": None,
                "path": str(db_path),
            }
        stat = db_path.stat()
        return {
            "exists": True,
            "size_bytes": stat.st_size,
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "last_modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "path": str(db_path),
        }

    def download_backup(self):
        """Return the database file for download."""
        db_path = self._get_db_path()
        if not db_path.exists():
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="קובץ מסד נתונים לא נמצא")

        # Checkpoint WAL before download
        try:
            self.db.execute(text("PRAGMA wal_checkpoint(FULL)"))
        except Exception as e:
            logger.warning(f"WAL checkpoint failed: {e}")

        return FileResponse(
            path=str(db_path),
            filename=f"planmyevents_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db",
            media_type="application/octet-stream",
        )
