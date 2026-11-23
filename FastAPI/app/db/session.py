"""
Database session factory and FastAPI dependency.
"""

from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from app.db.engine import engine

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency — yields a DB session and ensures cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
