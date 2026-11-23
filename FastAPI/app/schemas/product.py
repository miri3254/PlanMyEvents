"""
Product schemas.
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime

DrinkType = Literal["pepsi", "pepsi_max", "orange_flavored", "water", "soda"]


class ProductCreate(BaseModel):
    drink_type: Optional[DrinkType] = None
    name: str = Field(..., min_length=1, max_length=255)
    category: str = Field(default="מוצרים יבשים")
    unit: str = Field(default="יחידות")
    package_quantity: Optional[float] = Field(None, ge=0)
    price_per_unit: Optional[float] = Field(None, ge=0)
    estimated_price: Optional[float] = Field(None, ge=0)
    quantity_in_stock: float = Field(default=0.0, ge=0)
    min_stock_level: float = Field(default=0.0, ge=0)
    supplier: Optional[str] = None
    brand: Optional[str] = None
    barcode: Optional[str] = None
    notes: Optional[str] = None
    description: Optional[str] = None
    kosher_type: str = Field(default="פרווה")


class ProductUpdate(BaseModel):
    drink_type: Optional[DrinkType] = None
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    category: Optional[str] = None
    unit: Optional[str] = None
    package_quantity: Optional[float] = Field(None, ge=0)
    price_per_unit: Optional[float] = Field(None, ge=0)
    estimated_price: Optional[float] = Field(None, ge=0)
    quantity_in_stock: Optional[float] = Field(None, ge=0)
    min_stock_level: Optional[float] = Field(None, ge=0)
    supplier: Optional[str] = None
    brand: Optional[str] = None
    barcode: Optional[str] = None
    notes: Optional[str] = None
    description: Optional[str] = None
    kosher_type: Optional[str] = None


class ProductResponse(BaseModel):
    drink_type: Optional[DrinkType] = None
    id: int
    name: str
    category: str
    unit: str
    package_quantity: Optional[float] = None
    price_per_unit: Optional[float] = None
    estimated_price: Optional[float] = None
    quantity_in_stock: float = 0.0
    min_stock_level: float = 0.0
    inventory_status: str              # computed
    supplier: Optional[str] = None
    brand: Optional[str] = None
    barcode: Optional[str] = None
    notes: Optional[str] = None
    description: Optional[str] = None
    kosher_type: str = "פרווה"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

    @staticmethod
    def from_model(product) -> "ProductResponse":
        return ProductResponse(
            id=product.id,
            name=product.name,
            drink_type=product.drink_type,
            category=product.category.value if hasattr(product.category, "value") else str(product.category),
            unit=product.unit.value if hasattr(product.unit, "value") else str(product.unit),
            package_quantity=product.package_quantity,
            price_per_unit=product.price_per_unit,
            estimated_price=product.estimated_price,
            quantity_in_stock=product.quantity_in_stock,
            min_stock_level=product.min_stock_level,
            inventory_status=product.inventory_status,
            supplier=product.supplier,
            brand=product.brand,
            barcode=product.barcode,
            notes=product.notes,
            description=product.description,
            kosher_type=product.kosher_type.value if hasattr(product.kosher_type, "value") else str(product.kosher_type),
            created_at=product.created_at,
            updated_at=product.updated_at,
        )


class ProductListResponse(BaseModel):
    items: list[ProductResponse]
    total: int
    skip: int = 0
    limit: int = 50


class ProductDeleteRequest(BaseModel):
    ids: list[int] = Field(..., min_length=1)
