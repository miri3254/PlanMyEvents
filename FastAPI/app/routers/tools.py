"""
Tools router — CRUD + bulk + low-stock.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.tool_service import ToolService
from app.schemas.tool import ToolCreate, ToolUpdate, ToolResponse, ToolListResponse
from app.schemas.common import SuccessResponse, BulkOperationResponse

router = APIRouter(prefix="/tools", tags=["tools"])


def _svc(db: Session = Depends(get_db)) -> ToolService:
    return ToolService(db)


@router.get("", response_model=ToolListResponse)
def get_tools(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    search: Optional[str] = None,
    category: Optional[str] = None,
    sub_category: Optional[str] = None,
    svc: ToolService = Depends(_svc),
):
    items, total = svc.get_tools(
        skip=skip, limit=limit, search=search,
        category=category, sub_category=sub_category,
    )
    return {"items": items, "total": total, "skip": skip, "limit": limit}


@router.get("/low-stock", response_model=list[ToolResponse])
def get_low_stock(svc: ToolService = Depends(_svc)):
    return svc.get_low_stock()


@router.delete("/bulk", response_model=BulkOperationResponse)
def bulk_delete(ids: str = Query(...), svc: ToolService = Depends(_svc)):
    tool_ids = [int(item) for item in ids.split(",") if item.strip()]
    return svc.bulk_delete(tool_ids)


@router.get("/{tool_id}", response_model=ToolResponse)
def get_tool(tool_id: int, svc: ToolService = Depends(_svc)):
    return svc.get_tool(tool_id)


@router.post("", status_code=201, response_model=ToolResponse)
def create_tool(data: ToolCreate, svc: ToolService = Depends(_svc)):
    return svc.create_tool(data)


@router.put("/{tool_id}", response_model=ToolResponse)
def update_tool(tool_id: int, data: ToolUpdate, svc: ToolService = Depends(_svc)):
    return svc.update_tool(tool_id, data)


@router.delete("/{tool_id}", response_model=SuccessResponse)
def delete_tool(tool_id: int, svc: ToolService = Depends(_svc)):
    return svc.delete_tool(tool_id)


@router.post("/bulk", status_code=201, response_model=BulkOperationResponse)
def bulk_create(items: list[ToolCreate], svc: ToolService = Depends(_svc)):
    return svc.bulk_create(items)
