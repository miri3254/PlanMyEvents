"""
Shared / common schemas used across multiple modules.
"""

from pydantic import BaseModel
from typing import Generic, TypeVar, List

T = TypeVar("T")


class SuccessResponse(BaseModel):
    """Generic success message."""
    success: bool = True
    message: str


class BulkOperationResponse(SuccessResponse):
    """Generic response for bulk writes."""
    count: int = 0
    deleted_count: int | None = None


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated list wrapper."""
    items: List[T]
    total: int
    skip: int
    limit: int
