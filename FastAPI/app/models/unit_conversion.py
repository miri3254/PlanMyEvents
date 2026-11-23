"""
UnitConversion model — stores unit conversion factors.

System conversions (is_system=True):
  - Fixed conversions like kg→gram, liter→ml
  - Cannot be deleted or have factor changed by user

User conversions (is_system=False):
  - User-defined conversions like tablespoon→gram
  - Can be added, edited, and deleted by user
"""

from sqlalchemy import Column, String, Float, Boolean, UniqueConstraint
from sqlalchemy import Enum as SAEnum

from app.db.base import BaseModel
from app.core.enums import UnitType


class UnitConversion(BaseModel):
    """
    Defines how to convert from one unit to another.
    
    Example:
      from_unit=TABLESPOON, to_unit=GRAM, factor=15.0
      means: 1 tablespoon = 15 grams
    """

    __tablename__ = "unit_conversions"
    __table_args__ = (
        UniqueConstraint('from_unit', 'to_unit', name='uix_from_to_unit'),
    )

    from_unit = Column(SAEnum(UnitType), nullable=False)
    to_unit = Column(SAEnum(UnitType), nullable=False)
    factor = Column(Float, nullable=False)
    is_system = Column(Boolean, default=False, nullable=False)
    description = Column(String(255), nullable=True)
