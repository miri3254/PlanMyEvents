"""
Receipt scanning schemas — for AI receipt scanning.
"""

from pydantic import BaseModel, Field
from typing import Optional


class ExistingProduct(BaseModel):
    """Simplified product for matching purposes."""
    id: int
    name: str
    stock: float = Field(default=0.0)

    model_config = {"from_attributes": True, "populate_by_name": True}


class ScannedItem(BaseModel):
    """A single item extracted from the receipt by AI."""
    matched_product_id: Optional[int] = None
    name: str
    quantity: float
    unit_price: float
    is_new: bool = True
    current_stock: float = 0.0


class ReceiptScanRequest(BaseModel):
    """Request body for receipt scanning."""
    images: list[str] = Field(..., description="Base64 encoded images of receipt pages")
    existing_products: list[ExistingProduct] = Field(..., description="Existing products for matching")


class ReceiptScanResponse(BaseModel):
    """Response with scanned items."""
    items: list[ScannedItem]
    raw_text: Optional[str] = None


class InventoryBulkUpdateItem(BaseModel):
    """Item for bulk inventory update."""
    matched_product_id: Optional[int] = None
    name: str
    edited_name: str
    quantity: float
    unit_price: float
    is_new: bool = True
    current_stock: float = 0.0


class InventoryBulkUpdateRequest(BaseModel):
    """Request body for bulk inventory update."""
    items: list[InventoryBulkUpdateItem]


class InventoryProduct(BaseModel):
    """Product with inventory info for frontend."""
    id: int
    name: str
    stock: float

    model_config = {"from_attributes": True}
