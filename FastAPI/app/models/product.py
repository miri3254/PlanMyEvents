"""
Product model — raw ingredients in stock.
"""

from sqlalchemy import Column, String, Float, Text, Index, text
from sqlalchemy import Enum as SAEnum

from app.db.base import BaseModel
from app.core.enums import ProductCategory, KosherType, UnitType
from app.core.constants import INVENTORY_OUT_OF_STOCK, INVENTORY_LOW_STOCK, INVENTORY_IN_STOCK


class Product(BaseModel):
    """
    A purchasable product (e.g. "קמח", "שמן זית", "סלמון טרי").
    inventory_status is NOT stored — computed dynamically.
    """

    __tablename__ = "products"
    __table_args__ = (
        Index("uq_products_active_drink_type", "drink_type", unique=True,
              sqlite_where=text("is_deleted = 0 AND drink_type IS NOT NULL"),
              postgresql_where=text("is_deleted = false AND drink_type IS NOT NULL")),
    )

    name = Column(String(255), nullable=False)
    drink_type = Column(String(30), nullable=True)
    category = Column(SAEnum(ProductCategory), default=ProductCategory.DRY, nullable=False)
    unit = Column(SAEnum(UnitType), default=UnitType.UNIT, nullable=False)
    package_quantity = Column(Float, nullable=True)
    price_per_unit = Column(Float, nullable=True)
    estimated_price = Column(Float, nullable=True)
    quantity_in_stock = Column(Float, default=0.0, nullable=False)
    min_stock_level = Column(Float, default=0.0, nullable=False)
    supplier = Column(String(255), nullable=True)
    brand = Column(String(255), nullable=True)
    barcode = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    kosher_type = Column(SAEnum(KosherType), default=KosherType.PARVE, nullable=False)

    @property
    def inventory_status(self) -> str:
        """Computed inventory status — never persisted."""
        if self.quantity_in_stock <= 0:
            return INVENTORY_OUT_OF_STOCK
        if self.quantity_in_stock <= self.min_stock_level:
            return INVENTORY_LOW_STOCK
        return INVENTORY_IN_STOCK
