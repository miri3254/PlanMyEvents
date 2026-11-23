"""
Product repository.
"""

from typing import Optional, List

from sqlalchemy.orm import Session

from app.repositories.base_repo import BaseRepository
from app.models.product import Product
from app.core.constants import INVENTORY_OUT_OF_STOCK, INVENTORY_LOW_STOCK


class ProductRepository(BaseRepository[Product]):
    def __init__(self, db: Session):
        super().__init__(Product, db)

    def get_list(
        self,
        category: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[List[Product], int]:
        q = self._active()
        if category:
            q = q.filter(Product.category == category)
        if search:
            q = q.filter(Product.name.contains(search))
        total = q.count()
        products = q.offset(skip).limit(limit).all()
        return products, total

    def get_low_stock(self) -> List[Product]:
        return (
            self._active()
            .filter(Product.quantity_in_stock <= Product.min_stock_level)
            .all()
        )

    def bulk_create(self, products: List[Product]) -> List[Product]:
        self.db.add_all(products)
        self.db.flush()
        return products
