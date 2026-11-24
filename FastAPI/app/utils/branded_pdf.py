"""Branded (Ginsberger letterhead) PDF building blocks for event documents.

Caterer request (docs/catering-todo/sources/caterer-document-instructions-2026-11.md):
every print/export carries the logo and design. First page uses assets/blank.png
(large logo), next pages assets/blank_pages.png (small logo). Content frames sit
inside the white area of each letterhead.
"""
from __future__ import annotations

from io import BytesIO
from typing import Iterable, Optional, Sequence

from reportlab.lib.colors import HexColor, white
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import (
    BaseDocTemplate, Frame, KeepTogether, NextPageTemplate, PageTemplate, Paragraph, Spacer, Table, TableStyle,
)
from xml.sax.saxutils import escape

from app.utils.pdf_generator import BLANK_FIRST_PAGE_PATH, BLANK_OTHER_PAGES_PATH, _bidi, _register_hebrew_fonts

PAGE_W, PAGE_H = A4
ORANGE = HexColor("#f7931e")
DARK = HexColor("#2f2f2f")
MUTED = HexColor("#6b7280")
LINE = HexColor("#e5c9a8")
HEAD_BG = HexColor("#fdf0e1")
ZEBRA = HexColor("#fffaf4")

# White-area frames measured on the letterhead images (A4 points).
SIDE = 64
FIRST_FRAME = (SIDE, 140, PAGE_W - 2 * SIDE, PAGE_H - 140 - 192)
OTHER_FRAME = (SIDE, 48, PAGE_W - 2 * SIDE, PAGE_H - 48 - 140)
CONTENT_W = PAGE_W - 2 * SIDE


def _styles():
    _register_hebrew_fonts()
    base = dict(fontName="HebrewRegular", alignment=TA_RIGHT, textColor=DARK)
    return {
        "title": ParagraphStyle("t", **{**base, "fontName": "HebrewBold", "fontSize": 20, "leading": 26, "alignment": TA_CENTER}),
        "subtitle": ParagraphStyle("st", **{**base, "fontSize": 12, "leading": 16, "alignment": TA_CENTER, "textColor": MUTED}),
        "h2": ParagraphStyle("h2", **{**base, "fontName": "HebrewBold", "fontSize": 13, "leading": 17, "textColor": white}),
        "label": ParagraphStyle("lb", **{**base, "fontName": "HebrewBold", "fontSize": 9.5, "leading": 12.5}),
        "cell": ParagraphStyle("c", **{**base, "fontSize": 9.5, "leading": 12.5}),
        "small": ParagraphStyle("s", **{**base, "fontSize": 8.5, "leading": 11, "textColor": MUTED}),
        "head": ParagraphStyle("hd", **{**base, "fontName": "HebrewBold", "fontSize": 9.5, "leading": 12.5}),
        "body": ParagraphStyle("b", **{**base, "fontSize": 10.5, "leading": 15}),
        "note": ParagraphStyle("n", **{**base, "fontSize": 10, "leading": 14, "textColor": HexColor("#9a3412")}),
    }


STYLES = None


def styles():
    global STYLES
    if STYLES is None:
        STYLES = _styles()
    return STYLES


def rtl(text, style: ParagraphStyle, width: float) -> Paragraph:
    """Wrap Hebrew text by logical words first, then reorder each line (keeps line order correct)."""
    text = "" if text is None else str(text)
    usable = max(20.0, width - 4)
    lines: list[str] = []
    for raw_line in text.split("\n"):
        words, current = raw_line.split(" "), ""
        for word in words:
            candidate = f"{current} {word}".strip()
            if current and stringWidth(candidate, style.fontName, style.fontSize) > usable:
                lines.append(current)
                current = word
            else:
                current = candidate
        lines.append(current)
    return Paragraph("<br/>".join(escape(_bidi(line)) for line in lines), style)


_IMAGE_CACHE: dict[str, object] = {}


def _letterhead_image(path: str):
    """Downscaled JPEG of the letterhead (the source PNGs are 3–4 MB; keeps each PDF small)."""
    if path not in _IMAGE_CACHE:
        from PIL import Image
        from reportlab.lib.utils import ImageReader
        with Image.open(path) as img:
            img = img.convert("RGB")
            img.thumbnail((1240, 1754))
            out = BytesIO()
            img.save(out, format="JPEG", quality=82, optimize=True)
        out.seek(0)
        _IMAGE_CACHE[path] = ImageReader(out)
    return _IMAGE_CACHE[path]


def _letterhead(first: bool):
    path = BLANK_FIRST_PAGE_PATH if first else BLANK_OTHER_PAGES_PATH

    def draw(canvas, doc):
        canvas.saveState()
        try:
            canvas.drawImage(_letterhead_image(path), 0, 0, width=PAGE_W, height=PAGE_H, preserveAspectRatio=False)
        except Exception:
            canvas.setStrokeColor(ORANGE)
            canvas.setLineWidth(6)
            canvas.rect(14, 14, PAGE_W - 28, PAGE_H - 28)
        footer = getattr(doc, "footer_text", "")
        canvas.setFont("HebrewRegular", 8)
        canvas.setFillColor(MUTED)
        y = 122 if first else 36
        canvas.drawCentredString(PAGE_W / 2, y, f"{doc.page}")
        if footer:
            canvas.drawRightString(PAGE_W - SIDE, y, _bidi(footer))
        canvas.restoreState()

    return draw


def build(flowables: list, footer_text: str = "") -> BytesIO:
    buffer = BytesIO()
    doc = BaseDocTemplate(buffer, pagesize=A4, leftMargin=0, rightMargin=0, topMargin=0, bottomMargin=0)
    doc.footer_text = footer_text
    doc.addPageTemplates([
        PageTemplate(id="first", frames=[Frame(*FIRST_FRAME, id="f1", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)],
                     onPage=_letterhead(True)),
        PageTemplate(id="other", frames=[Frame(*OTHER_FRAME, id="f2", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)],
                     onPage=_letterhead(False)),
    ])
    doc.build([NextPageTemplate("other"), *flowables])
    buffer.seek(0)
    return buffer


# ── blocks ────────────────────────────────────────────────────────────

def title(text: str, subtitle: Optional[str] = None) -> list:
    st = styles()
    out = [rtl(text, st["title"], CONTENT_W)]
    if subtitle:
        out.append(rtl(subtitle, st["subtitle"], CONTENT_W))
    out.append(Spacer(1, 10))
    return out


def section(text: str) -> Table:
    t = Table([[rtl(text, styles()["h2"], CONTENT_W - 16)]], colWidths=[CONTENT_W])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), ORANGE),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8), ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t


def info_grid(pairs: Sequence[tuple[str, object]], columns: int = 2) -> Table:
    """Label/value pairs laid out right-to-left in `columns` pairs per row."""
    st = styles()
    pairs = [(k, v) for k, v in pairs if v not in (None, "", [])]
    label_w, value_w = 2.9 * cm, CONTENT_W / columns - 2.9 * cm
    rows = []
    for i in range(0, len(pairs), columns):
        visual = []  # right → left: label1, value1, label2, value2 ...
        for label, value in pairs[i:i + columns]:
            visual += [rtl(label, st["label"], label_w), rtl(value, st["cell"], value_w)]
        visual += ["", ""] * (columns - len(pairs[i:i + columns]))
        rows.append(list(reversed(visual)))
    if not rows:
        return Spacer(1, 0)
    widths = list(reversed([label_w, value_w] * columns))
    t = Table(rows, colWidths=widths)
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, -1), 0.3, LINE),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4), ("LEFTPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def table(headers: Sequence[str], rows: Iterable[Sequence[object]], widths_cm: Sequence[float],
          checkbox: bool = False, small_cols: Sequence[int] = (), checkbox_label: str = "סומן") -> Table:
    """RTL table: headers/rows are given right→left; widths in cm (scaled to the content width)."""
    st = styles()
    headers = list(headers) + ([checkbox_label] if checkbox else [])
    widths = list(widths_cm) + ([1.2] if checkbox else [])
    scale = CONTENT_W / (sum(widths) * cm)
    col_w = [w * cm * scale for w in widths]
    data = [[rtl(h, st["head"], w) for h, w in zip(headers, col_w)]]
    for row in rows:
        cells = []
        for idx, (value, w) in enumerate(zip(list(row) + ([""] if checkbox else []), col_w)):
            if hasattr(value, "wrap") or isinstance(value, list):
                cells.append(value)
            else:
                cells.append(rtl("" if value is None else value, st["small"] if idx in small_cols else st["cell"], w))
        data.append(cells)
    data = [list(reversed(r)) for r in data]
    col_w = list(reversed(col_w))
    t = Table(data, colWidths=col_w, repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), HEAD_BG),
        ("GRID", (0, 0), (-1, -1), 0.4, LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4), ("LEFTPADDING", (0, 0), (-1, -1), 4),
    ]
    for r in range(2, len(data), 2):
        style.append(("BACKGROUND", (0, r), (-1, r), ZEBRA))
    t.setStyle(TableStyle(style))
    return t


def checklist(items: Iterable[str]) -> Table:
    """Items with an empty box to tick by hand (drawn box, no font glyph needed)."""
    st = styles()
    text_w = CONTENT_W - 0.9 * cm
    rows = [[rtl(item, st["body"], text_w), ""] for item in items if item]
    if not rows:
        return Spacer(1, 0)
    rows = [list(reversed(r)) for r in rows]
    t = Table(rows, colWidths=[0.9 * cm, text_w])
    style = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]
    for r in range(len(rows)):
        style.append(("BOX", (0, r), (0, r), 0.8, DARK))
    t.setStyle(TableStyle(style))
    return t


def paragraph(text: str, kind: str = "body") -> Paragraph:
    return rtl(text, styles()[kind], CONTENT_W)


def numbered(items: Sequence[str]) -> list:
    return [rtl(f"{i}. {text}", styles()["body"], CONTENT_W) for i, text in enumerate(items, start=1)]


def titled(heading: str, *parts) -> KeepTogether:
    """Section heading kept on the same page as the start of its content."""
    return KeepTogether([section(heading), gap(3), *parts])


def block(*parts) -> KeepTogether:
    flat = []
    for p in parts:
        flat.extend(p if isinstance(p, list) else [p])
    return KeepTogether(flat)


def gap(height: float = 8) -> Spacer:
    return Spacer(1, height)
