"""
OCR service for extracting ordered text from receipt images.
"""

from __future__ import annotations

import base64
import io
from dataclasses import dataclass
from typing import Any

import numpy as np
from PIL import Image

from app.utils.app_logging import logger

try:
    from paddleocr import PaddleOCR
except ImportError:
    PaddleOCR = None


@dataclass
class OcrPageResult:
    text: str
    lines: list[str]


class OcrService:
    """Wrap PaddleOCR and normalize receipt OCR output."""

    def __init__(self, language: str = "he", use_angle_cls: bool = True):
        self.language = language
        self.use_angle_cls = use_angle_cls
        self._ocr = None

    def _get_engine(self) -> Any:
        if self._ocr is not None:
            return self._ocr

        if PaddleOCR is None:
            raise ValueError("PaddleOCR לא מותקן בשרת. יש להתקין את חבילות ה-OCR לפני סריקת קבלות.")

        try:
            self._ocr = PaddleOCR(use_angle_cls=self.use_angle_cls, lang=self.language)
            return self._ocr
        except Exception as exc:
            logger.error("Failed to initialize PaddleOCR: %s", exc, exc_info=True)
            raise ValueError(f"שירות ה-OCR לא הצליח לעלות: {exc}") from exc

    def extract_text(self, image_base64: str) -> OcrPageResult:
        try:
            image_bytes = base64.b64decode(image_base64)
        except Exception as exc:
            raise ValueError("קובץ התמונה של הקבלה אינו תקין.") from exc

        try:
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            image_array = np.array(image)
        except Exception as exc:
            raise ValueError("לא ניתן היה לטעון את תמונת הקבלה.") from exc

        engine = self._get_engine()

        try:
            result = engine.ocr(image_array, cls=self.use_angle_cls)
        except Exception as exc:
            logger.error("PaddleOCR failed to process receipt image: %s", exc, exc_info=True)
            raise ValueError(f"שגיאה בקריאת הטקסט מהקבלה: {exc}") from exc

        lines = self._extract_ordered_lines(result)
        text = "\n".join(lines).strip()
        return OcrPageResult(text=text, lines=lines)

    def _extract_ordered_lines(self, result: Any) -> list[str]:
        raw_lines: list[tuple[float, float, str]] = []

        if not result:
            return []

        for page in result:
            if not page:
                continue
            for entry in page:
                if not entry or len(entry) < 2:
                    continue
                box, text_info = entry
                if not box or not text_info:
                    continue
                text = str(text_info[0]).strip()
                if not text:
                    continue
                x_positions = [point[0] for point in box]
                y_positions = [point[1] for point in box]
                raw_lines.append((min(y_positions), min(x_positions), text))

        raw_lines.sort(key=lambda item: (round(item[0] / 10) * 10, item[1]))
        return [text for _, _, text in raw_lines]