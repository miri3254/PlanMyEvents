"""
Product service — CRUD + bulk operations for stock products.
"""

from typing import Optional
from contextlib import contextmanager
from sqlalchemy.exc import IntegrityError

from sqlalchemy.orm import Session

from app.repositories.product_repo import ProductRepository
from app.repositories.audit_repo import AuditRepository
from app.models.product import Product
from app.core.enums import AuditAction, UnitType
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from app.utils.errors import AppException
from app.utils.app_logging import logger


class ProductService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ProductRepository(db)
        self.audit = AuditRepository(db)

    def _get_or_404(self, product_id: int) -> Product:
        product = self.repo.get_by_id(product_id)
        if not product:
            raise AppException(404, "מוצר לא נמצא")
        return product

    def _response(self, product: Product) -> dict:
        return ProductResponse.from_model(product).model_dump()

    # ── LIST / GET ────────────────────────────────────────────────────

    def get_products(self, **kwargs) -> tuple[list[dict], int]:
        products, total = self.repo.get_list(**kwargs)
        return [self._response(p) for p in products], total

    def get_product(self, product_id: int) -> dict:
        product = self._get_or_404(product_id)
        return self._response(product)

    def get_low_stock(self) -> list[dict]:
        products = self.repo.get_low_stock()
        return [self._response(p) for p in products]

    # ── CREATE / UPDATE / DELETE ──────────────────────────────────────

    def _validate_drink(self, payload: dict, product: Product | None = None) -> None:
        kind = payload.get("drink_type", product.drink_type if product else None)
        unit = payload.get("unit", product.unit if product else UnitType.UNIT)
        if not kind:
            return
        if unit != UnitType.UNIT:
            raise AppException(422, "מלאי שתייה מנוהל ביחידות בקבוק בלבד")
        duplicate = self.db.query(Product).filter(
            Product.drink_type == kind, Product.is_deleted == False,  # noqa: E712
            Product.id != (product.id if product else -1),
        ).first()
        if duplicate:
            raise AppException(409, "כבר קיים מוצר מלאי לסוג השתייה הזה; יש לעדכן את המלאי שלו")

    @contextmanager
    def _drink_conflict(self):
        try:
            yield
        except IntegrityError as exc:
            self.db.rollback()
            if "drink_type" not in str(exc.orig):
                raise
            raise AppException(409, "לא ניתן לשמור מוצר כפול לאותו סוג שתייה") from exc

    def create_product(self, data: ProductCreate) -> dict:
        self._validate_drink(data.model_dump())
        db_product = Product(**data.model_dump())
        with self._drink_conflict():
            self.repo.create(db_product)
            self.audit.log("product", db_product.id, AuditAction.CREATED.value)
            self.db.commit()
        self.db.refresh(db_product)
        logger.info(f"מוצר נוצר: {db_product.name} (ID={db_product.id})")
        return self._response(db_product)

    def update_product(self, product_id: int, data: ProductUpdate) -> dict:
        product = self._get_or_404(product_id)
        update_data = data.model_dump(exclude_unset=True)
        self._validate_drink(update_data, product)
        with self._drink_conflict():
            self.repo.update(product, update_data)
            self.audit.log("product", product_id, AuditAction.UPDATED.value)
            self.db.commit()
        return self._response(self.repo.get_by_id(product_id))

    def delete_product(self, product_id: int) -> dict:
        product = self._get_or_404(product_id)
        self.repo.soft_delete(product)
        self.audit.log("product", product_id, AuditAction.DELETED.value)
        self.db.commit()
        return {"success": True, "message": "המוצר נמחק בהצלחה"}

    # ── BULK ──────────────────────────────────────────────────────────

    def bulk_delete(self, ids: list[int]) -> dict:
        deleted = 0
        for product_id in ids:
            product = self.repo.get_by_id(product_id)
            if product:
                self.repo.soft_delete(product)
                self.audit.log("product", product_id, AuditAction.DELETED.value)
                deleted += 1
        self.db.commit()
        return {
            "success": True,
            "message": f"Deleted {deleted} products",
            "count": deleted,
            "deleted_count": deleted,
        }

    def bulk_create(self, items: list[ProductCreate]) -> dict:
        seen = set()
        for item in items:
            self._validate_drink(item.model_dump())
            if item.drink_type and item.drink_type in seen:
                raise AppException(409, "בקשת היבוא כוללת יותר ממוצר אחד לאותו סוג שתייה")
            seen.add(item.drink_type)
        products = [Product(**item.model_dump()) for item in items]
        with self._drink_conflict():
            created = self.repo.bulk_create(products)
            self.db.commit()
        logger.info(f"נוצרו {len(created)} מוצרים בבאלק")
        return {"success": True, "message": f"נוצרו {len(created)} מוצרים", "count": len(created)}
