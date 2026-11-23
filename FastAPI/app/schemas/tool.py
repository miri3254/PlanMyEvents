"""
Tool schemas.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ToolCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    brand: Optional[str] = None
    category: str = Field(default="כלי הגשה")
    sub_category: str = Field(default="אמיתי")
    quantity_in_stock: int = Field(default=0, ge=0)
    min_stock_level: int = Field(default=0, ge=0)
    price_per_unit: float = Field(default=0.0, ge=0)
    description: Optional[str] = None
    color: Optional[str] = None
    size: Optional[str] = None


class ToolUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    brand: Optional[str] = None
    category: Optional[str] = None
    sub_category: Optional[str] = None
    quantity_in_stock: Optional[int] = Field(None, ge=0)
    min_stock_level: Optional[int] = Field(None, ge=0)
    price_per_unit: Optional[float] = Field(None, ge=0)
    description: Optional[str] = None
    color: Optional[str] = None
    size: Optional[str] = None


class ToolResponse(BaseModel):
    id: int
    name: str
    brand: Optional[str] = None
    category: str
    sub_category: str
    quantity_in_stock: int = 0
    min_stock_level: int = 0
    inventory_status: str              # computed
    price_per_unit: float = 0.0
    description: Optional[str] = None
    color: Optional[str] = None
    size: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

    @staticmethod
    def from_model(tool) -> "ToolResponse":
        return ToolResponse(
            id=tool.id,
            name=tool.name,
            brand=tool.brand,
            category=tool.category.value if hasattr(tool.category, "value") else str(tool.category),
            sub_category=tool.sub_category.value if hasattr(tool.sub_category, "value") else str(tool.sub_category),
            quantity_in_stock=tool.quantity_in_stock,
            min_stock_level=tool.min_stock_level,
            inventory_status=tool.inventory_status,
            price_per_unit=tool.price_per_unit,
            description=tool.description,
            color=tool.color,
            size=tool.size,
            created_at=tool.created_at,
            updated_at=tool.updated_at,
        )


class ToolListResponse(BaseModel):
    items: list[ToolResponse]
    total: int
    skip: int = 0
    limit: int = 50


class ToolDeleteRequest(BaseModel):
    ids: list[int] = Field(..., min_length=1)
