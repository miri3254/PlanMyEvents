"""
Menu models — templates, sub-meals, categories, and dish-category mappings.
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.db.base import BaseModel


class MenuTemplate(BaseModel):
    """
    Top-level menu definition (e.g. שבת, תפריט בשרי, מגשי אירוח חלבי).
    One row per menu type - now fully dynamic (no longer an ENUM).
    """

    __tablename__ = "menu_templates"

    # Changed from ENUM to String(100) for dynamic menu types
    menu_type = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)          # Hebrew display name
    tablecloth_profile = Column(String(30), nullable=False, default="regular", server_default="regular")
    table_setting_items = Column(JSON, nullable=True)
    description = Column(Text, nullable=True)
    min_guests = Column(Integer, nullable=False, default=1)
    base_price_per_guest = Column(Float, nullable=True)  # NULL for tray menus
    real_dishes_extra_per_guest = Column(Float, nullable=True, default=0.0)  # תוספת לכלים אמיתיים
    is_tray_menu = Column(Boolean, default=False, nullable=False)
    kosher_type = Column(String(50), nullable=False, default="פרווה")  # בשרי/חלבי/פרווה

    # relationships
    sub_meals = relationship(
        "MenuSubMeal",
        back_populates="template",
        cascade="all, delete-orphan",
        order_by="MenuSubMeal.display_order",
    )
    categories = relationship(
        "MenuCategory",
        back_populates="template",
        cascade="all, delete-orphan",
        order_by="MenuCategory.display_order",
    )


class MenuSubMeal(BaseModel):
    """
    Sub-meal within a template (e.g. ליל שבת, סעודת שבת בוקר).
    Only used for Shabbat; other menu types have zero sub-meals.
    """

    __tablename__ = "menu_sub_meals"

    template_id = Column(Integer, ForeignKey("menu_templates.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)         # "ליל שבת"
    display_order = Column(Integer, default=0, nullable=False)
    is_splittable = Column(Boolean, default=False, nullable=False)
    split_extra_charge = Column(Float, nullable=True)  # extra per-guest if split

    # relationships
    template = relationship("MenuTemplate", back_populates="sub_meals")
    categories = relationship(
        "MenuCategory",
        back_populates="sub_meal",
        cascade="all, delete-orphan",
        order_by="MenuCategory.display_order",
    )


class MenuCategory(BaseModel):
    """
    A selection category inside a menu (e.g. סלטים, מנה עיקרית, קינוחים).
    Belongs to either a template directly OR to a sub-meal.
    """

    __tablename__ = "menu_categories"

    template_id = Column(Integer, ForeignKey("menu_templates.id", ondelete="CASCADE"), nullable=True)
    sub_meal_id = Column(Integer, ForeignKey("menu_sub_meals.id", ondelete="CASCADE"), nullable=True)
    name = Column(String(100), nullable=False)         # internal key (salads, fish…)
    name_hebrew = Column(String(255), nullable=False)  # display "סלטים"
    description = Column(Text, nullable=True)          # e.g. "2 לבחירה - חצי סלמון חצי מושט"
    display_order = Column(Integer, default=0, nullable=False)
    quota = Column(Integer, nullable=True)             # NULL = no limit (trays)
    quota_description = Column(String(255), nullable=True)
    guest_count_rules = Column(JSON, nullable=True)    # e.g. {"above_80": {"quota": 3}}
    is_required = Column(Boolean, default=True, nullable=False)

    # Tray-specific fields (NULL for normal menus)
    tray_quantity = Column(Integer, nullable=True)     # units per tray  (e.g. 12)
    tray_price = Column(Float, nullable=True)          # price per tray

    # relationships
    template = relationship("MenuTemplate", back_populates="categories")
    sub_meal = relationship("MenuSubMeal", back_populates="categories")
    dish_mappings = relationship(
        "DishMenuMapping",
        back_populates="category",
        cascade="all, delete-orphan",
    )


class DishMenuMapping(BaseModel):
    """
    Links a Dish to a MenuCategory.
    A single dish can appear in multiple categories / templates.
    """

    __tablename__ = "dish_menu_mappings"

    default_serving_mode = Column(String(20), nullable=True)
    dish_id = Column(Integer, ForeignKey("dishes.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, ForeignKey("menu_categories.id", ondelete="CASCADE"), nullable=False)
    is_upgrade = Column(Boolean, default=False, nullable=False)
    extra_charge = Column(Float, nullable=True)        # cost if upgrade
    display_order = Column(Integer, default=0, nullable=False)

    # relationships
    category = relationship("MenuCategory", back_populates="dish_mappings")
    dish = relationship("Dish", back_populates="menu_mappings")
