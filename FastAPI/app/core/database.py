from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import Settings
from app.db.base import Base

settings = Settings()

engine = create_async_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)
# Re-export Base for backwards compatibility
__all__ = ['engine', 'SessionLocal', 'Base']
