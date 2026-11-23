"""
PlanMyEvents — FastAPI application entry point.

Creates tables, registers routers, and sets up global error handling.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.engine import engine
from app.db.base import Base
from app.db.session import SessionLocal
from app.models import *  # noqa: F401,F403  — ensure all models registered
from app.routers import (
    events_router,
    dishes_router,
    products_router,
    tools_router,
    menus_router,
    dashboard_router,
    backup_router,
    lookup_router,
    unit_conversions_router,
)
from app.routers.receipts import router as receipts_router
from app.services.unit_conversion_service import UnitConversionService
from app.utils.errors import AppException, app_exception_handler
from app.utils.app_logging import logger


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ───────────────────────────────────────────────────────
    logger.info("יוצר טבלאות מסד הנתונים…")
    Base.metadata.create_all(bind=engine)
    
    # Seed system unit conversions
    logger.info("טוען המרות יחידות מידה מערכתיות…")
    db = SessionLocal()
    try:
        unit_conv_service = UnitConversionService(db)
        count = unit_conv_service.seed_system_conversions()
        if count > 0:
            logger.info(f"הוספו {count} המרות יחידות מידה")
        else:
            logger.info("המרות יחידות מידה כבר קיימות")
    except Exception as e:
        logger.error(f"שגיאה בטעינת המרות יחידות מידה: {e}", exc_info=True)
    finally:
        db.close()
    
    logger.info("Application ready")
    yield
    # ── Shutdown ──────────────────────────────────────────────────────
    logger.info("Application shutting down")


app = FastAPI(
    title="PlanMyEvents API",
    description="ניהול אירועים, מנות, מוצרים וכלים — לקייטרינג כשר",
    version="2.0.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Exception handler ────────────────────────────────────────────────
app.add_exception_handler(AppException, app_exception_handler)

# ── Routers ──────────────────────────────────────────────────────────
API_PREFIX = "/api"
app.include_router(events_router, prefix=API_PREFIX)
app.include_router(dishes_router, prefix=API_PREFIX)
app.include_router(products_router, prefix=API_PREFIX)
app.include_router(tools_router, prefix=API_PREFIX)
app.include_router(menus_router, prefix=API_PREFIX)
app.include_router(dashboard_router, prefix=API_PREFIX)
app.include_router(backup_router, prefix=API_PREFIX)
app.include_router(lookup_router, prefix=API_PREFIX)
app.include_router(unit_conversions_router, prefix=API_PREFIX)
app.include_router(receipts_router, prefix=API_PREFIX)


@app.get("/")
def root():
    return {"message": "PlanMyEvents API v2.0 — ברוכים הבאים"}


@app.get("/api/health")
def health():
    return {"status": "ok"}
