"""
Central model registry — import everything so Base.metadata knows all tables.
"""

from app.models.product import Product          # noqa: F401
from app.models.tool import Tool                # noqa: F401
from app.models.dish import (                   # noqa: F401
    Dish,
    DishIngredient,
    ServingDish,
)
from app.models.menu import (                   # noqa: F401
    MenuTemplate,
    MenuSubMeal,
    MenuCategory,
    DishMenuMapping,
)
from app.models.event import (                  # noqa: F401
    DeliveryNoteTemplate,
    Event,
    EventBox,
    EventDeliveryNote,
    EventOwner,
    EventDish,
    EventTraySelection,
)
from app.models.calculation import (            # noqa: F401
    DishCalculationRule,
    DishServingSet,
    DishServingSetItem,
    EventCalculationSettings,
    EventCalculationSnapshot,
    EventDishServingSelection,
    EventManualToolRow,
    ToolReservation,
)
from app.models.audit import AuditLog           # noqa: F401
from app.models.unit_conversion import UnitConversion  # noqa: F401
from app.models.lookup import LookupData               # noqa: F401
