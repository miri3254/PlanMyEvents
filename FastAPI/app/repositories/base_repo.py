"""
Base repository — generic CRUD with soft-delete support.
"""

from datetime import datetime, timezone
from typing import TypeVar, Generic, Type, Optional, List

from sqlalchemy.orm import Session
from app.db.base import BaseModel

T = TypeVar("T", bound=BaseModel)


class BaseRepository(Generic[T]):
    """
    Generic repository.  All queries automatically filter out
    soft-deleted rows (is_deleted = False).
    """

    def __init__(self, model: Type[T], db: Session):
        self.model = model
        self.db = db

    # ── helpers ───────────────────────────────────────────────────────

    def _active(self):
        """Base query filtering out soft-deleted rows."""
        return self.db.query(self.model).filter(self.model.is_deleted == False)  # noqa: E712

    # ── read ──────────────────────────────────────────────────────────

    def get_by_id(self, entity_id: int) -> Optional[T]:
        return self._active().filter(self.model.id == entity_id).first()

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by=None,
    ) -> List[T]:
        q = self._active()
        if order_by is not None:
            q = q.order_by(order_by)
        return q.offset(skip).limit(limit).all()

    def count(self) -> int:
        return self._active().count()

    # ── write ─────────────────────────────────────────────────────────

    def create(self, entity: T) -> T:
        self.db.add(entity)
        self.db.flush()
        return entity

    def update(self, entity: T, data: dict) -> T:
        for key, value in data.items():
            if hasattr(entity, key):
                setattr(entity, key, value)
        self.db.flush()
        return entity

    def soft_delete(self, entity: T) -> T:
        entity.is_deleted = True
        entity.deleted_at = datetime.now(timezone.utc)
        self.db.flush()
        return entity

    def hard_delete(self, entity: T) -> None:
        self.db.delete(entity)
        self.db.flush()
