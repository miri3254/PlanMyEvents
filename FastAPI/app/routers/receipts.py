"""
Receipt router — AI-powered receipt scanning endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.config import get_settings
from app.services.ocr_service import OcrService
from app.services.ollama_service import OllamaService
from app.services.receipt_ai_service import ReceiptAIService
from app.services.product_service import ProductService
from app.schemas.receipt import (
    ReceiptScanRequest,
    ReceiptScanResponse,
    ExistingProduct,
    InventoryBulkUpdateRequest,
    InventoryProduct
)
from app.schemas.product import ProductCreate, ProductUpdate
from app.utils.app_logging import logger

router = APIRouter(prefix="/receipts", tags=["receipts"])

settings = get_settings()


def _get_ai_service() -> ReceiptAIService:
    """Create the local receipt scanning pipeline service."""
    ocr_service = OcrService(
        language=settings.OCR_LANGUAGE,
        use_angle_cls=settings.OCR_USE_ANGLE_CLS,
    )
    ollama_service = OllamaService(
        base_url=settings.OLLAMA_BASE_URL,
        model=settings.OLLAMA_MODEL,
    )
    return ReceiptAIService(ocr_service=ocr_service, ollama_service=ollama_service)


def _get_product_service(db: Session = Depends(get_db)) -> ProductService:
    return ProductService(db)


@router.post("/scan", response_model=ReceiptScanResponse)
def scan_receipt(
    request: ReceiptScanRequest,
    ai_service: ReceiptAIService = Depends(_get_ai_service)
):
    """
    Scan a receipt using AI and extract product items.
    
    - **images**: Base64 encoded images of receipt pages (max 2 pages)
    - **existing_products**: List of existing products for matching
    
    Returns a list of scanned items with matching info.
    """
    try:
        logger.info(f"Scanning receipt with {len(request.images)} images")
        
        # Convert to ExistingProduct objects for the service
        existing_products = [
            ExistingProduct(id=p.id, name=p.name, stock=p.stock)
            for p in request.existing_products
        ]
        
        # Scan the receipt
        items, raw_text = ai_service.scan_receipt(request.images, existing_products)
        
        logger.info(f"Scanned {len(items)} items from receipt")
        return ReceiptScanResponse(items=items, raw_text=raw_text)
        
    except ValueError as e:
        # User-friendly error message from the service
        logger.warning(f"Receipt scan validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error scanning receipt: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"שגיאה בסריקת הקבלה: {str(e)}")


@router.get("/products/inventory", response_model=list[InventoryProduct])
def get_inventory_products(
    product_service: ProductService = Depends(_get_product_service)
):
    """
    Get all products for inventory matching in receipt scan dialog.
    Returns simplified product list with id, name, and stock.
    """
    products, _ = product_service.get_products(skip=0, limit=1000)
    return [
        InventoryProduct(
            id=p["id"],
            name=p["name"],
            stock=p.get("quantity_in_stock", 0)
        )
        for p in products
    ]


@router.post("/inventory/bulk-update")
def bulk_update_inventory(
    request: InventoryBulkUpdateRequest,
    product_service: ProductService = Depends(_get_product_service)
):
    """
    Bulk update inventory from scanned receipt items.
    
    - Updates stock for existing products
    - Creates new products if is_new=True
    """
    try:
        updated_count = 0
        created_count = 0
        
        for item in request.items:
            if item.matched_product_id:
                # Update existing product stock
                product = product_service.get_product(item.matched_product_id)
                if product:
                    new_stock = product.get("quantity_in_stock", 0) + item.quantity
                    update_data = ProductUpdate(
                        name=product.get("name"),
                        package_quantity=product.get("package_quantity"),
                        price_per_unit=product.get("price_per_unit"),
                        estimated_price=product.get("estimated_price"),
                        quantity_in_stock=new_stock,
                        min_stock_level=product.get("min_stock_level"),
                    )
                    product_service.update_product(item.matched_product_id, update_data)
                    updated_count += 1
            elif item.is_new:
                # Create new product
                new_product = ProductCreate(
                    name=item.edited_name or item.name,
                    package_quantity=None,
                    quantity_in_stock=item.quantity,
                    price_per_unit=item.unit_price,
                    estimated_price=item.unit_price,
                )
                product_service.create_product(new_product)
                created_count += 1
        
        logger.info(f"Bulk inventory update: {updated_count} updated, {created_count} created")
        
        return {
            "success": True,
            "updated": updated_count,
            "created": created_count
        }
        
    except Exception as e:
        logger.error(f"Error in bulk inventory update: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"שגיאה בעדכון המלאי: {str(e)}")
