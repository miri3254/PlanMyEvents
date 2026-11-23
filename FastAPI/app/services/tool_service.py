"""
Tool service — CRUD + bulk operations for kitchen/serving tools.
"""

from typing import Optional

from sqlalchemy.orm import Session

from app.repositories.tool_repo import ToolRepository
from app.repositories.audit_repo import AuditRepository
from app.models.tool import Tool
from app.core.enums import AuditAction
from app.schemas.tool import ToolCreate, ToolUpdate, ToolResponse
from app.utils.errors import AppException
from app.utils.app_logging import logger


class ToolService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ToolRepository(db)
        self.audit = AuditRepository(db)

    def _get_or_404(self, tool_id: int) -> Tool:
        tool = self.repo.get_by_id(tool_id)
        if not tool:
            raise AppException(404, "כלי לא נמצא")
        return tool

    def _response(self, tool: Tool) -> dict:
        return ToolResponse.from_model(tool).model_dump()

    # ── LIST / GET ────────────────────────────────────────────────────

    def get_tools(self, **kwargs) -> tuple[list[dict], int]:
        tools, total = self.repo.get_list(**kwargs)
        return [self._response(t) for t in tools], total

    def get_tool(self, tool_id: int) -> dict:
        tool = self._get_or_404(tool_id)
        return self._response(tool)

    def get_low_stock(self) -> list[dict]:
        tools = self.repo.get_low_stock()
        return [self._response(t) for t in tools]

    # ── CREATE / UPDATE / DELETE ──────────────────────────────────────

    def create_tool(self, data: ToolCreate) -> dict:
        db_tool = Tool(**data.model_dump())
        self.repo.create(db_tool)
        self.audit.log("tool", db_tool.id, AuditAction.CREATED.value)
        self.db.commit()
        self.db.refresh(db_tool)
        logger.info(f"כלי נוצר: {db_tool.name} (ID={db_tool.id})")
        return self._response(db_tool)

    def update_tool(self, tool_id: int, data: ToolUpdate) -> dict:
        tool = self._get_or_404(tool_id)
        update_data = data.model_dump(exclude_unset=True)
        self.repo.update(tool, update_data)
        self.audit.log("tool", tool_id, AuditAction.UPDATED.value)
        self.db.commit()
        return self._response(self.repo.get_by_id(tool_id))

    def delete_tool(self, tool_id: int) -> dict:
        tool = self._get_or_404(tool_id)
        self.repo.soft_delete(tool)
        self.audit.log("tool", tool_id, AuditAction.DELETED.value)
        self.db.commit()
        return {"success": True, "message": "הכלי נמחק בהצלחה"}

    # ── BULK ──────────────────────────────────────────────────────────

    def bulk_delete(self, ids: list[int]) -> dict:
        deleted = 0
        for tool_id in ids:
            tool = self.repo.get_by_id(tool_id)
            if tool:
                self.repo.soft_delete(tool)
                self.audit.log("tool", tool_id, AuditAction.DELETED.value)
                deleted += 1
        self.db.commit()
        return {
            "success": True,
            "message": f"Deleted {deleted} tools",
            "count": deleted,
            "deleted_count": deleted,
        }

    def bulk_create(self, items: list[ToolCreate]) -> dict:
        tools = [Tool(**item.model_dump()) for item in items]
        created = self.repo.bulk_create(tools)
        self.db.commit()
        logger.info(f"נוצרו {len(created)} כלים בבאלק")
        return {"success": True, "message": f"נוצרו {len(created)} כלים", "count": len(created)}
