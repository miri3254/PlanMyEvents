"""
UnitConversion schemas.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class UnitConversionCreate(BaseModel):
    """Schema for creating a new unit conversion."""
    from_unit: str = Field(..., description="Source unit (Hebrew value)")
    to_unit: str = Field(..., description="Target unit (Hebrew value)")
    factor: float = Field(..., gt=0, description="Conversion factor")
    description: Optional[str] = Field(None, max_length=255)


class UnitConversionUpdate(BaseModel):
    """Schema for updating a unit conversion (only factor and description can be changed)."""
    factor: Optional[float] = Field(None, gt=0)
    description: Optional[str] = Field(None, max_length=255)


class UnitConversionResponse(BaseModel):
    """Schema for unit conversion response."""
    id: int
    from_unit: str
    to_unit: str
    factor: float
    is_system: bool
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConversionRequest(BaseModel):
    """Schema for requesting a unit conversion calculation."""
    value: float = Field(..., description="Value to convert")
    from_unit: str = Field(..., description="Source unit")
    to_unit: str = Field(..., description="Target unit")


class ConversionResponse(BaseModel):
    """Schema for conversion calculation result."""
    original_value: float
    original_unit: str
    converted_value: float
    target_unit: str
    conversion_path: list[str] = Field(default_factory=list, description="Units used in conversion chain")
