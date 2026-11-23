"""
Schema registry.
"""

from app.schemas.common import SuccessResponse, PaginatedResponse  # noqa
from app.schemas.product import (  # noqa
    ProductCreate, ProductUpdate, ProductResponse, ProductDeleteRequest,
)
from app.schemas.tool import (  # noqa
    ToolCreate, ToolUpdate, ToolResponse, ToolDeleteRequest,
)
from app.schemas.dish import (  # noqa
    DishCreate, DishUpdate, DishActiveUpdate, DishResponse,
    DishIngredientCreate, DishIngredientUpdate, DishIngredientResponse,
    ServingDishCreate, ServingDishUpdate, ServingDishResponse,
)
from app.schemas.event import (  # noqa
    EventCreate, EventUpdate, EventStatusUpdate, EventResponse,
    EventDishCreate, EventDishResponse,
    EventOwnerCreate, EventOwnerResponse,
    EventTrayCreate, EventTrayResponse,
    ShoppingListItem, ShoppingListResponse,
    EquipmentListItem, EquipmentListResponse,
)
from app.schemas.menu import (  # noqa
    MenuTemplateResponse, MenuSubMealResponse, MenuCategoryResponse,
    CategoryDishItem, CategoryDishesResponse,
    ValidateSelectionRequest, ValidateSelectionResponse,
    EventMenuProgress, CategoryProgress,
)
from app.schemas.dashboard import (  # noqa
    DashboardStats, UpcomingEvent, LowStockAlert,
)
from app.schemas.unit_conversion import (  # noqa
    UnitConversionCreate, UnitConversionUpdate, UnitConversionResponse,
    ConversionRequest, ConversionResponse,
)
