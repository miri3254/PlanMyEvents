"""
Receipt AI service that orchestrates OCR and local LLM parsing.
"""

import json
import re

from app.schemas.receipt import ExistingProduct, ScannedItem
from app.services.ocr_service import OcrService
from app.services.ollama_service import OllamaService
from app.utils.app_logging import logger


class ReceiptAIService:
    """
    Receipt scanning orchestration service.
    Uses PaddleOCR for text extraction and Ollama for JSON structuring.
    """

    def __init__(self, ocr_service: OcrService, ollama_service: OllamaService):
        self.ocr_service = ocr_service
        self.ollama_service = ollama_service

    def scan_receipt(
        self,
        images: list[str],
        existing_products: list[ExistingProduct]
    ) -> tuple[list[ScannedItem], str]:
        """
        Scan receipt images and extract product items.
        """
        if not images:
            raise ValueError("לא נשלחו תמונות לסריקת הקבלה.")

        try:
            page_texts: list[str] = []
            for image in images:
                page_result = self.ocr_service.extract_text(image)
                if page_result.text:
                    page_texts.append(page_result.text)

            raw_text = "\n\n".join(page_texts).strip()
            if not raw_text:
                raise ValueError("לא זוהה טקסט בקבלה. ודא שהמסמך ברור וקריא.")

            ai_response = self.ollama_service.parse_receipt_text(raw_text, existing_products)
            items = self._parse_ai_response(ai_response, existing_products)

            if not items:
                logger.warning("No items found in receipt scan")
                raise ValueError("לא זוהו מוצרים בקבלה. ודא שהתמונה ברורה וקריאה.")

            return items, raw_text

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error processing local receipt pipeline: {e}")
            raise ValueError(f"שגיאה בסריקת הקבלה: {str(e)}")

    def _parse_ai_response(
        self,
        ai_response: str,
        existing_products: list[ExistingProduct]
    ) -> list[ScannedItem]:
        """Parse AI response and match with existing products."""
        try:
            # Extract JSON from response (might have markdown code blocks)
            json_match = re.search(r'\{[\s\S]*\}', ai_response)
            if not json_match:
                logger.error(f"No JSON found in AI response: {ai_response[:200]}")
                return []
            
            data = json.loads(json_match.group())
            items = data.get("items", [])
            
            # Create lookup dict for existing products
            product_lookup = {p.name.lower(): p for p in existing_products}
            
            scanned_items = []
            for item in items:
                name = item.get("name", "")
                quantity = float(item.get("quantity", 1))
                unit_price = float(item.get("unit_price", 0))
                
                # Try to match with existing product
                matched_product = None
                name_lower = name.lower()
                
                # Exact match
                if name_lower in product_lookup:
                    matched_product = product_lookup[name_lower]
                else:
                    # Partial match - check if product name contains the scanned name
                    for prod_name, prod in product_lookup.items():
                        if name_lower in prod_name or prod_name in name_lower:
                            matched_product = prod
                            break
                
                scanned_items.append(ScannedItem(
                    matched_product_id=matched_product.id if matched_product else None,
                    name=name,
                    quantity=quantity,
                    unit_price=unit_price,
                    is_new=matched_product is None,
                    current_stock=matched_product.stock if matched_product else 0.0
                ))
            
            return scanned_items

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI JSON response: {e}")
            return []
        except Exception as e:
            logger.error(f"Error parsing AI response: {e}")
            return []
