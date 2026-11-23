"""
Dish models — dish, ingredients, serving dishes.
"""

from sqlalchemy import Column, String, Float, Boolean, Text, Integer, ForeignKey
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import relationship

from app.db.base import BaseModel
from app.core.enums import KosherType, UnitType


class Dish(BaseModel):
    """
    A dish in the catalogue (e.g. "סלמון ברוטב פסטו").
    Category is determined via DishMenuMapping — one dish can appear
    under different categories in different menus.
    """

    __tablename__ = "dishes"

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    kosher_type = Column(SAEnum(KosherType), default=KosherType.PARVE, nullable=False)

    # Pricing
    base_price = Column(Float, nullable=True)         # internal cost
    client_price = Column(Float, nullable=True)       # price shown to client

    # Serving
    serving_size = Column(Float, default=1.0, nullable=False)  # serves N guests
    serving_description = Column(Text, nullable=True)
    waiter_notes = Column(Text, nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)

    # ── relationships ────────────────────────────────────────────────
    ingredients = relationship(
        "DishIngredient",
        back_populates="dish",
        cascade="all, delete-orphan",
    )
    serving_dishes = relationship(
        "ServingDish",
        back_populates="dish",
        cascade="all, delete-orphan",
    )
    menu_mappings = relationship(
        "DishMenuMapping",
        back_populates="dish",
        cascade="all, delete-orphan",
    )


class DishIngredient(BaseModel):
    """Recipe ingredient — links to an optional Product for stock tracking."""

    __tablename__ = "dish_ingredients"

    dish_id = Column(Integer, ForeignKey("dishes.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(255), nullable=True)          # free-text name if no product
    quantity = Column(Float, default=1.0, nullable=False)
    unit = Column(SAEnum(UnitType), default=UnitType.UNIT, nullable=False)
    is_serving_component = Column(Boolean, default=False, nullable=False)

    # relationships
    dish = relationship("Dish", back_populates="ingredients")
    product = relationship("Product")


class ServingDish(BaseModel):
    """Serving vessel / platter used when presenting this dish."""

    __tablename__ = "serving_dishes"

    dish_id = Column(Integer, ForeignKey("dishes.id", ondelete="CASCADE"), nullable=False)
    tool_id = Column(Integer, ForeignKey("tools.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(255), nullable=True)
    quantity = Column(Integer, default=1, nullable=False)

    # relationships
    dish = relationship("Dish", back_populates="serving_dishes")
    tool = relationship("Tool")
