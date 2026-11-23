"""Routers package — all API route modules."""

from app.routers.events import router as events_router
from app.routers.dishes import router as dishes_router
from app.routers.products import router as products_router
from app.routers.tools import router as tools_router
from app.routers.menus import router as menus_router
from app.routers.dashboard import router as dashboard_router
from app.routers.backup import router as backup_router
from app.routers.lookup import router as lookup_router
from app.routers.unit_conversions import router as unit_conversions_router

__all__ = [
    "events_router",
    "dishes_router",
    "products_router",
    "tools_router",
    "menus_router",
    "dashboard_router",
    "backup_router",
    "lookup_router",
    "unit_conversions_router",
]
