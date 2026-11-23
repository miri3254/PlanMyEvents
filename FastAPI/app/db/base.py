"""
Shared declarative base with soft-delete and timestamp columns.
Every model inherits from BaseModel.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Boolean, DateTime
from sqlalchemy.orm import DeclarativeBase


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Raw SQLAlchemy declarative base (for metadata only)."""
    pass


class BaseModel(Base):
    """
    Abstract base inherited by all application tables.

    Provides:
      id          – auto-increment primary key
      created_at  – set on insert
      updated_at  – set on insert and updated on every commit
      is_deleted  – soft-delete flag (default False)
      deleted_at  – timestamp of soft-delete (NULL when active)
    """

    __abstract__ = True

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
