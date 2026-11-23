"""
Tool model — kitchen equipment, serving vessels, cutlery, etc.
"""

from sqlalchemy import Column, String, Integer, Float, Text
from sqlalchemy import Enum as SAEnum

from app.db.base import BaseModel
from app.core.enums import ToolCategory, ToolSubCategory
from app.core.constants import INVENTORY_OUT_OF_STOCK, INVENTORY_LOW_STOCK, INVENTORY_IN_STOCK


class Tool(BaseModel):
    """
    A reusable or disposable tool (e.g. "צלחת פורצלן לבנה", "כוס חד פעמית").
    inventory_status is NOT stored — computed dynamically.
    """

    __tablename__ = "tools"

    name = Column(String(255), nullable=False)
    brand = Column(String(255), nullable=True)
    category = Column(SAEnum(ToolCategory), default=ToolCategory.SERVING, nullable=False)
    sub_category = Column(SAEnum(ToolSubCategory), default=ToolSubCategory.REAL, nullable=False)
    quantity_in_stock = Column(Integer, default=0, nullable=False)
    min_stock_level = Column(Integer, default=0, nullable=False)
    price_per_unit = Column(Float, default=0.0, nullable=False)
    description = Column(Text, nullable=True)
    color = Column(String(50), nullable=True)
    size = Column(String(50), nullable=True)

    @property
    def inventory_status(self) -> str:
        """Computed inventory status — never persisted."""
        if self.quantity_in_stock <= 0:
            return INVENTORY_OUT_OF_STOCK
        if self.quantity_in_stock <= self.min_stock_level:
            return INVENTORY_LOW_STOCK
        return INVENTORY_IN_STOCK
