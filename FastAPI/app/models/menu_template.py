"""
Menu Template Models (legacy stub - active models are in app/models/menu.py)
This file is kept for backward-compat with old scripts only.
Do NOT use for new code.
"""
# All active menu models have been moved to app/models/menu.py
# MenuType enum has been removed - menu_type is now a plain string (template name)


class MenuCategory(Base):
    """
    Menu Category - defines a category within a menu template
    Each category has a name, quota, and display order
    """
    __tablename__ = "menu_categories"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("menu_templates.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)  # Internal name e.g., "salads"
    name_hebrew = Column(String(255), nullable=False)  # Display name e.g., "סלטים"
    description = Column(Text)  # Optional description
    display_order = Column(Integer, nullable=False, default=0)  # Order in wizard
    quota = Column(Integer, nullable=False, default=0)  # Base quota (e.g., 5 salads)
    is_required = Column(Boolean, default=True)  # Must complete this category?

    # Relationships
    template = relationship("MenuTemplate", back_populates="categories")

    def __repr__(self):
        return f"<MenuCategory {self.name_hebrew} - Quota: {self.quota}>"
