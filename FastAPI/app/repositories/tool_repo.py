"""
Tool repository.
"""

from typing import Optional, List

from sqlalchemy.orm import Session

from app.repositories.base_repo import BaseRepository
from app.models.tool import Tool


class ToolRepository(BaseRepository[Tool]):
    def __init__(self, db: Session):
        super().__init__(Tool, db)

    def get_list(
        self,
        category: Optional[str] = None,
        sub_category: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[List[Tool], int]:
        q = self._active()
        if category:
            q = q.filter(Tool.category == category)
        if sub_category:
            q = q.filter(Tool.sub_category == sub_category)
        if search:
            q = q.filter(Tool.name.contains(search))
        total = q.count()
        tools = q.offset(skip).limit(limit).all()
        return tools, total

    def get_low_stock(self) -> List[Tool]:
        return (
            self._active()
            .filter(Tool.quantity_in_stock <= Tool.min_stock_level)
            .all()
        )

    def bulk_create(self, tools: List[Tool]) -> List[Tool]:
        self.db.add_all(tools)
        self.db.flush()
        return tools
