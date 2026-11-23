"""
Backup router — create, list, info, and download database backups.
"""

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.backup_service import BackupService

router = APIRouter(prefix="/backup", tags=["backup"])


def _svc(db: Session = Depends(get_db)) -> BackupService:
    return BackupService(db)


@router.post("")
def create_backup(svc: BackupService = Depends(_svc)):
    return svc.create_backup()


@router.get("")
def list_backups(svc: BackupService = Depends(_svc)):
    return svc.list_backups()


@router.get("/info")
def get_backup_info(svc: BackupService = Depends(_svc)):
    return svc.get_backup_info()


@router.get("/download")
def download_backup(svc: BackupService = Depends(_svc)):
    return svc.download_backup()
