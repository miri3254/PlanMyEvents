"""
Ollama client for converting receipt OCR text into structured JSON.
"""

from __future__ import annotations

import json

import httpx

from app.schemas.receipt import ExistingProduct
from app.utils.app_logging import logger


class OllamaService:
    """Client wrapper for local Ollama receipt parsing."""

    def __init__(self, base_url: str, model: str, timeout_seconds: float = 60.0):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    def parse_receipt_text(self, raw_text: str, existing_products: list[ExistingProduct]) -> str:
        if not raw_text.strip():
            raise ValueError("לא התקבל טקסט לעיבוד הקבלה.")

        product_list = "\n".join(f"- {product.name} (id: {product.id})" for product in existing_products)
        prompt = (
            "אתה מערכת שממירה טקסט OCR של קבלת קנייה בעברית ל-JSON תקין בלבד.\n"
            "החזר אובייקט JSON בלבד ללא Markdown וללא הסברים.\n"
            "מבנה התשובה חייב להיות:\n"
            "{\n"
            '  "items": [\n'
            "    {\n"
            '      "name": "שם המוצר",\n'
            '      "quantity": 1,\n'
            '      "unit_price": 0\n'
            "    }\n"
            "  ]\n"
            "}\n"
            "כללים:\n"
            "- אם כמות חסרה, הנח 1.\n"
            "- אם יש מחיר כולל וכמות, חשב מחיר ליחידה.\n"
            "- התעלם משורות שאינן מוצרי קנייה כמו סהכ, מעמ, כתובת, טלפון.\n"
            "- שמור את שם המוצר כפי שמופיע ככל האפשר.\n"
            "- אם אינך בטוח, החזר פחות פריטים ולא טקסט חופשי.\n"
            f"רשימת מוצרים קיימים במערכת לעזרה בהתאמה:\n{product_list or '- אין מוצרים קיימים'}\n\n"
            f"טקסט ה-OCR:\n{raw_text}"
        )

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.1
            }
        }

        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(f"{self.base_url}/api/generate", json=payload)
                response.raise_for_status()
        except httpx.ConnectError as exc:
            raise ValueError("Ollama לא זמין. ודא שהשירות המקומי פועל על הכתובת שהוגדרה.") from exc
        except httpx.HTTPStatusError as exc:
            logger.error("Ollama returned HTTP error: %s", exc.response.text)
            raise ValueError(f"Ollama החזיר שגיאה: {exc.response.status_code}") from exc
        except httpx.HTTPError as exc:
            raise ValueError(f"שגיאת תקשורת מול Ollama: {exc}") from exc

        try:
            data = response.json()
        except json.JSONDecodeError as exc:
            logger.error("Failed to parse Ollama response as JSON: %s", response.text)
            raise ValueError("Ollama החזיר תשובה לא תקינה.") from exc

        model_response = str(data.get("response", "")).strip()
        if not model_response:
            raise ValueError("Ollama לא החזיר תוכן לעיבוד הקבלה.")

        return model_response