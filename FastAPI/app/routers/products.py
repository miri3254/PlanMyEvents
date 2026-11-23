"""
Products router — CRUD + bulk + low-stock.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.product_service import ProductService
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse, ProductListResponse
from app.schemas.common import SuccessResponse, BulkOperationResponse

router = APIRouter(prefix="/products", tags=["products"])


def _svc(db: Session = Depends(get_db)) -> ProductService:
    return ProductService(db)


@router.get("", response_model=ProductListResponse)
def get_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    search: Optional[str] = None,
    category: Optional[str] = None,
    svc: ProductService = Depends(_svc),
):
    items, total = svc.get_products(skip=skip, limit=limit, search=search, category=category)
    return {"items": items, "total": total, "skip": skip, "limit": limit}


@router.get("/low-stock", response_model=list[ProductResponse])
def get_low_stock(svc: ProductService = Depends(_svc)):
    return svc.get_low_stock()


@router.delete("/bulk", response_model=BulkOperationResponse)
def bulk_delete(ids: str = Query(...), svc: ProductService = Depends(_svc)):
    product_ids = [int(item) for item in ids.split(",") if item.strip()]
    return svc.bulk_delete(product_ids)


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, svc: ProductService = Depends(_svc)):
    return svc.get_product(product_id)


@router.post("", status_code=201, response_model=ProductResponse)
def create_product(data: ProductCreate, svc: ProductService = Depends(_svc)):
    return svc.create_product(data)


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(product_id: int, data: ProductUpdate, svc: ProductService = Depends(_svc)):
    return svc.update_product(product_id, data)


@router.delete("/{product_id}", response_model=SuccessResponse)
def delete_product(product_id: int, svc: ProductService = Depends(_svc)):
    return svc.delete_product(product_id)


@router.post("/bulk", status_code=201, response_model=BulkOperationResponse)
def bulk_create(items: list[ProductCreate], svc: ProductService = Depends(_svc)):
    return svc.bulk_create(items)

