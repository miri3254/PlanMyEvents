"""
PDF Generator for waiter instructions.
Creates professionally styled PDF documents in Hebrew RTL.
"""

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, KeepTogether, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.colors import black, grey, HexColor
from reportlab.lib.enums import TA_RIGHT, TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from bidi.algorithm import get_display

from io import BytesIO
from typing import Optional, List, Dict, Any
import os
import math

WAITER_TABLE_BORDER = HexColor("#d5dbe8")
WAITER_TABLE_HEADER = HexColor("#e9edf7")
WAITER_TABLE_TEXT = HexColor("#15192d")
WAITER_WARM_BG = HexColor("#fff5e8")
WAITER_WARM_BORDER = HexColor("#ead8c3")
WAITER_WARM_TEXT = HexColor("#7b3f00")

EVENT_SEQUENCE_COLOR_HEX = {
    "orange": "#f97316",
    "green": "#22c55e",
    "purple": "#a855f7",
    "sky": "#0ea5e9",
    "red": "#ef4444",
}


def _event_sequence_text_color(sequence_color: Optional[str]) -> HexColor:
    return HexColor(EVENT_SEQUENCE_COLOR_HEX.get(sequence_color or "", "#374151"))


def _bidi(text: str) -> str:
    """המרת טקסט לתצוגה RTL עם החזרת str"""
    return str(get_display(text))


# ========================================
# הגדרות נתיבים
# ========================================

# נתיב לתמונת בלאנק לדף הראשון
BLANK_FIRST_PAGE_PATH = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "assets", "blank.png"))
# נתיב לתמונת בלאנק לשאר הדפים
BLANK_OTHER_PAGES_PATH = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "assets", "blank_pages.png"))

# נתיב לפונט עברי
HEBREW_FONT_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "fonts", "Heebo-Regular.ttf")
HEBREW_FONT_BOLD_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "fonts", "Heebo-Bold.ttf")


def _register_hebrew_fonts():
    """רישום פונטים עבריים אם לא נרשמו"""
    try:
        pdfmetrics.getFont('HebrewRegular')
    except KeyError:
        if os.path.exists(HEBREW_FONT_PATH):
            pdfmetrics.registerFont(TTFont('HebrewRegular', HEBREW_FONT_PATH))
        else:
            raise FileNotFoundError(
                f"לא נמצא פונט עברי בנתיב: {HEBREW_FONT_PATH}\n"
                "יש להוריד פונט עברי (כמו Heebo או Assistant) ולהציב אותו בנתיב הנכון."
            )
    
    try:
        pdfmetrics.getFont('HebrewBold')
    except KeyError:
        if os.path.exists(HEBREW_FONT_BOLD_PATH):
            pdfmetrics.registerFont(TTFont('HebrewBold', HEBREW_FONT_BOLD_PATH))
        else:
            if os.path.exists(HEBREW_FONT_PATH):
                pdfmetrics.registerFont(TTFont('HebrewBold', HEBREW_FONT_PATH))


def _get_hebrew_styles():
    """יצירת סגנונות עיצוב לעברית - מקצועי ונקי"""
    styles = getSampleStyleSheet()
    
    # כותרת ראשית גדולה (לעמוד הראשון)
    main_title_style = ParagraphStyle(
        'HebrewMainTitle',
        parent=styles['Heading1'],
        fontName='HebrewBold',
        fontSize=22,
        leading=28,
        alignment=TA_CENTER,
        spaceAfter=18,
        textColor=HexColor('#1a1a2e')
    )
    
    # כותרת ראשית
    title_style = ParagraphStyle(
        'HebrewTitle',
        parent=styles['Heading1'],
        fontName='HebrewBold',
        fontSize=18,
        leading=24,
        alignment=TA_CENTER,
        spaceAfter=14,
        textColor=HexColor('#1a1a2e')
    )
    
    # כותרת משנית
    subtitle_style = ParagraphStyle(
        'HebrewSubtitle',
        parent=styles['Normal'],
        fontName='HebrewRegular',
        fontSize=11,
        leading=16,
        alignment=TA_CENTER,
        spaceAfter=20,
        textColor=HexColor('#444444')
    )
    
    # כותרת קטגוריה ראשית
    category_main_style = ParagraphStyle(
        'HebrewCategoryMain',
        parent=styles['Heading2'],
        fontName='HebrewBold',
        fontSize=14,
        leading=18,
        alignment=TA_RIGHT,
        spaceBefore=14,
        spaceAfter=8,
        textColor=HexColor('#2c3e50'),
        borderWidth=0,
        borderPadding=0,
    )
    
    # כותרת מנה
    dish_title_style = ParagraphStyle(
        'HebrewDishTitle',
        parent=styles['Heading2'],
        fontName='HebrewBold',
        fontSize=12,
        leading=16,
        alignment=TA_RIGHT,
        spaceBefore=8,
        spaceAfter=4,
        textColor=HexColor('#1a1a2e'),
    )
    
    # טקסט רגיל
    normal_style = ParagraphStyle(
        'HebrewNormal',
        parent=styles['Normal'],
        fontName='HebrewRegular',
        fontSize=10,
        leading=14,
        alignment=TA_RIGHT,
        textColor=black
    )
    
    # טקסט פרטי אירוע
    event_detail_style = ParagraphStyle(
        'HebrewEventDetail',
        parent=styles['Normal'],
        fontName='HebrewRegular',
        fontSize=10,
        leading=15,
        alignment=TA_RIGHT,
        textColor=HexColor('#333333'),
        leftIndent=8
    )
    
    # כותרת משנה לפרטי אירוע
    section_title_style = ParagraphStyle(
        'HebrewSectionTitle',
        parent=styles['Heading3'],
        fontName='HebrewBold',
        fontSize=12,
        leading=16,
        alignment=TA_RIGHT,
        textColor=HexColor('#2c3e50'),
        spaceBefore=10,
        spaceAfter=5,
        borderWidth=0,
        borderPadding=0,
    )
    
    # הערה מודגשת למלצר
    note_style = ParagraphStyle(
        'HebrewNote',
        parent=styles['Normal'],
        fontName='HebrewBold',
        fontSize=10,
        leading=14,
        alignment=TA_RIGHT,
        textColor=HexColor('#c0392b'),
        spaceBefore=2,
        spaceAfter=2,
        leftIndent=12,
        borderWidth=0,
        borderPadding=0,
    )
    
    # הערות כלליות לאירוע
    event_notes_style = ParagraphStyle(
        'HebrewEventNotes',
        parent=styles['Normal'],
        fontName='HebrewRegular',
        fontSize=10,
        leading=14,
        alignment=TA_RIGHT,
        textColor=HexColor('#555555'),
        spaceBefore=3,
        spaceAfter=3,
        leftIndent=8,
        rightIndent=8,
        borderWidth=0,
        borderPadding=0,
    )
    
    # כותרת קטגוריה
    category_style = ParagraphStyle(
        'HebrewCategory',
        parent=styles['Heading3'],
        fontName='HebrewBold',
        fontSize=11,
        leading=14,
        alignment=TA_RIGHT,
        textColor=HexColor('#2c3e50'),
        spaceBefore=20,
        spaceAfter=3
    )
    
    # פריט ברשימה
    list_item_style = ParagraphStyle(
        'HebrewListItem',
        parent=styles['Normal'],
        fontName='HebrewRegular',
        fontSize=9,
        leading=13,
        alignment=TA_RIGHT,
        leftIndent=15,
        textColor=HexColor('#333333')
    )
    
    # פרטי מנה
    dish_detail_style = ParagraphStyle(
        'HebrewDishDetail',
        parent=styles['Normal'],
        fontName='HebrewRegular',
        fontSize=9,
        leading=13,
        alignment=TA_RIGHT,
        leftIndent=18,
        textColor=HexColor('#444444'),
        spaceBefore=1,
        spaceAfter=1
    )
    
    # label מודגש
    label_style = ParagraphStyle(
        'HebrewLabel',
        parent=styles['Normal'],
        fontName='HebrewBold',
        fontSize=9,
        leading=13,
        alignment=TA_RIGHT,
        textColor=HexColor('#2c3e50')
    )
    
    # פרטי בעל אירוע
    owner_style = ParagraphStyle(
        'HebrewOwner',
        parent=styles['Normal'],
        fontName='HebrewRegular',
        fontSize=10,
        leading=14,
        alignment=TA_RIGHT,
        leftIndent=10,
        textColor=HexColor('#333333'),
        spaceBefore=2,
        spaceAfter=2
    )
    
    # סוג כלים - מודגש עם רקע רק מאחורי הטקסט
    dishes_type_style = ParagraphStyle(
        'HebrewDishesType',
        parent=styles['Normal'],
        fontName='HebrewBold',
        fontSize=11,
        leading=16,
        alignment=TA_RIGHT,
        textColor=HexColor('#1a5f2a'),
        spaceBefore=20,
        spaceAfter=6,
        borderWidth=0,
        borderPadding=0,
    )

    table_category_style = ParagraphStyle(
        'WaiterTableCategory',
        parent=styles['Normal'],
        fontName='HebrewBold',
        fontSize=12,
        leading=15,
        alignment=TA_RIGHT,
        textColor=WAITER_TABLE_TEXT,
    )

    table_header_style = ParagraphStyle(
        'WaiterTableHeader',
        parent=styles['Normal'],
        fontName='HebrewBold',
        fontSize=8.5,
        leading=11,
        alignment=TA_RIGHT,
        textColor=HexColor('#343b4c'),
    )

    table_cell_style = ParagraphStyle(
        'WaiterTableCell',
        parent=styles['Normal'],
        fontName='HebrewRegular',
        fontSize=8.6,
        leading=11,
        alignment=TA_RIGHT,
        textColor=HexColor('#3e4657'),
    )

    table_cell_small_style = ParagraphStyle(
        'WaiterTableCellSmall',
        parent=table_cell_style,
        fontSize=8,
        leading=10,
        textColor=HexColor('#5c6474'),
        spaceBefore=1,
    )

    table_dish_name_style = ParagraphStyle(
        'WaiterTableDishName',
        parent=table_cell_style,
        fontName='HebrewBold',
        fontSize=9,
        leading=11,
        textColor=WAITER_TABLE_TEXT,
    )

    table_note_style = ParagraphStyle(
        'WaiterTableNote',
        parent=table_cell_style,
        fontName='HebrewBold',
        fontSize=8,
        leading=10,
        textColor=HexColor('#9d2c20'),
    )

    setup_title_style = ParagraphStyle(
        'WaiterSetupTitle',
        parent=styles['Normal'],
        fontName='HebrewBold',
        fontSize=11,
        leading=14,
        alignment=TA_RIGHT,
        textColor=WAITER_WARM_TEXT,
    )

    setup_cell_style = ParagraphStyle(
        'WaiterSetupCell',
        parent=styles['Normal'],
        fontName='HebrewRegular',
        fontSize=8.7,
        leading=11,
        alignment=TA_RIGHT,
        textColor=HexColor('#3e4657'),
    )
    
    return {
        'main_title': main_title_style,
        'title': title_style,
        'subtitle': subtitle_style,
        'category_main': category_main_style,
        'dish_title': dish_title_style,
        'normal': normal_style,
        'event_detail': event_detail_style,
        'section_title': section_title_style,
        'note': note_style,
        'event_notes': event_notes_style,
        'category': category_style,
        'list_item': list_item_style,
        'dish_detail': dish_detail_style,
        'label': label_style,
        'owner': owner_style,
        'dishes_type': dishes_type_style,
        'table_category': table_category_style,
        'table_header': table_header_style,
        'table_cell': table_cell_style,
        'table_cell_small': table_cell_small_style,
        'table_dish_name': table_dish_name_style,
        'table_note': table_note_style,
        'setup_title': setup_title_style,
        'setup_cell': setup_cell_style,
    }


def _draw_waiter_page_background(canvas, doc, blank_path: Optional[str] = None, is_first_page: bool = False, simple_mode: bool = False):
    """ציור תמונת בלאנק (רקע) בכל דף"""
    canvas.saveState()
    
    # במצב פשוט - רק מספור עמודים בלי רקע צבעוני
    if simple_mode:
        canvas.setFont('HebrewRegular', 10)
        canvas.setFillColor(grey)
        page_num = canvas.getPageNumber()
        canvas.drawCentredString(A4[0] / 2, 1.2*cm, f"- {page_num} -")
        canvas.restoreState()
        return
    
    if blank_path and os.path.exists(blank_path):
        try:
            canvas.drawImage(
                blank_path, 
                0, 0, 
                width=A4[0], 
                height=A4[1],
                preserveAspectRatio=False,
                mask='auto'
            )
        except Exception:
            _draw_decorative_frame(canvas, is_first_page)
    else:
        _draw_decorative_frame(canvas, is_first_page)
    
    # מספר עמוד
    canvas.setFont('HebrewRegular', 10)
    canvas.setFillColor(grey)
    page_num = canvas.getPageNumber()
    canvas.drawCentredString(A4[0] / 2, 1.2*cm, f"- {page_num} -")
    
    canvas.restoreState()


def _draw_decorative_frame(canvas, is_first_page: bool = False):
    """ציור מסגרת דקורטיבית כשאין תמונת רקע"""
    page_width, page_height = A4
    
    primary_color = HexColor('#2c3e50')
    secondary_color = HexColor('#3498db')
    accent_color = HexColor('#e8f4f8')
    
    if is_first_page:
        header_height = 3.5*cm
        
        canvas.setFillColor(primary_color)
        canvas.rect(0, page_height - header_height, page_width, header_height, fill=1, stroke=0)
        
        canvas.setStrokeColor(secondary_color)
        canvas.setLineWidth(3)
        canvas.line(0, page_height - header_height, page_width, page_height - header_height)
        
        canvas.setStrokeColor(accent_color)
        canvas.setLineWidth(1)
        canvas.line(0, page_height - header_height - 5, page_width, page_height - header_height - 5)
        
        canvas.setStrokeColor(primary_color)
        canvas.setLineWidth(2)
        canvas.rect(0.8*cm, 0.8*cm, page_width - 1.6*cm, page_height - header_height - 1.2*cm, fill=0, stroke=1)
        
        footer_height = 1.5*cm
        canvas.setFillColor(accent_color)
        canvas.rect(0, 0, page_width, footer_height, fill=1, stroke=0)
        
        canvas.setStrokeColor(secondary_color)
        canvas.setLineWidth(1)
        canvas.line(0, footer_height, page_width, footer_height)
        
    else:
        header_height = 2*cm
        footer_height = 1.5*cm
        
        canvas.setFillColor(primary_color)
        canvas.rect(0, page_height - header_height, page_width, header_height, fill=1, stroke=0)
        
        canvas.setStrokeColor(secondary_color)
        canvas.setLineWidth(2)
        canvas.line(0, page_height - header_height, page_width, page_height - header_height)
        
        canvas.setFillColor(accent_color)
        canvas.rect(0, 0, page_width, footer_height, fill=1, stroke=0)
        
        canvas.setStrokeColor(secondary_color)
        canvas.setLineWidth(1)
        canvas.line(0, footer_height, page_width, footer_height)
        
        canvas.setStrokeColor(HexColor('#bdc3c7'))
        canvas.setLineWidth(0.5)
        content_margin = 1*cm
        canvas.rect(
            content_margin, 
            footer_height + 0.5*cm, 
            page_width - 2*content_margin, 
            page_height - header_height - footer_height - 1*cm, 
            fill=0, 
            stroke=1
        )




def _format_waiter_tool_name(tool: Any) -> str:
    if isinstance(tool, dict):
        name = str(tool.get("name") or "").strip()
        qty = tool.get("quantity", 1)
        if qty and qty > 1:
            return f"{name} (x{qty})"
        return name
    return str(tool or "").strip()


def _is_waiter_cutlery(tool_name: str) -> bool:
    cutlery_terms = ("מזלג", "סכין", "כף", "כפית", "מלקחיים", "סכו", "תרווד")
    return any(term in tool_name for term in cutlery_terms)


def _split_waiter_serving_tools(serving_dishes: Any) -> tuple[str, str]:
    if not serving_dishes:
        return "", ""

    tools = serving_dishes if isinstance(serving_dishes, list) else [serving_dishes]
    cutlery: List[str] = []
    serving: List[str] = []

    for tool in tools:
        name = _format_waiter_tool_name(tool)
        if not name:
            continue
        if _is_waiter_cutlery(name):
            cutlery.append(name)
        else:
            serving.append(name)

    return " + ".join(cutlery), " + ".join(serving)


def _waiter_cell(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(_bidi(text or ""), style)


def _waiter_dish_cell(dish: dict, styles: dict) -> list:
    flowables = [_waiter_cell(str(dish.get("name") or ""), styles["table_dish_name"])]
    serving_desc = dish.get("serving_description") or dish.get("description") or ""
    if serving_desc:
        flowables.append(_waiter_cell(str(serving_desc), styles["table_cell_small"]))
    return flowables


def _add_category_dishes_table(elements: list, category: str, dishes: list, styles: dict):
    heading = Table(
        [[_waiter_cell(category, styles["table_category"])]],
        colWidths=[17.2 * cm],
        hAlign="RIGHT",
    )
    heading.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), WAITER_TABLE_HEADER),
        ("BOX", (0, 0), (-1, -1), 0.7, WAITER_TABLE_BORDER),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))

    rows = [[
        _waiter_cell("דגש", styles["table_header"]),
        _waiter_cell("מנה / הוראות", styles["table_header"]),
        _waiter_cell("כלי הגשה", styles["table_header"]),
        _waiter_cell("סכו\"ם", styles["table_header"]),
    ]]

    for dish in dishes:
        cutlery_text, serving_text = _split_waiter_serving_tools(dish.get("serving_dishes", []))
        notes = dish.get("notes") or dish.get("waiter_notes") or ""
        rows.append([
            _waiter_cell(str(notes), styles["table_note"]),
            _waiter_dish_cell(dish, styles),
            _waiter_cell(serving_text, styles["table_cell"]),
            _waiter_cell(cutlery_text, styles["table_cell"]),
        ])

    table = Table(
        rows,
        colWidths=[2.25 * cm, 7.7 * cm, 4.1 * cm, 3.15 * cm],
        repeatRows=1,
        hAlign="RIGHT",
    )
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.45, WAITER_TABLE_BORDER),
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#f8fafc")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))

    elements.append(heading)
    elements.append(table)
    elements.append(Spacer(1, 10))


def _add_event_tool_set_section(elements: list, styles: dict, event_tool_set_items: Optional[list] = None):
    setup_items = []
    for item in event_tool_set_items or []:
        name = str(item.get("name") or "").strip()
        quantity = item.get("calculated_quantity")
        if not name:
            continue
        if quantity is None:
            setup_items.append(name)
        else:
            setup_items.append(f"{quantity:g} {name}" if isinstance(quantity, (int, float)) else f"{quantity} {name}")
    if not setup_items:
        return

    heading = Table(
        [[_waiter_cell("סט כלים לאירוע", styles["setup_title"])]],
        colWidths=[17.2 * cm],
        hAlign="RIGHT",
    )
    heading.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), WAITER_WARM_BG),
        ("BOX", (0, 0), (-1, -1), 0.7, WAITER_WARM_BORDER),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))

    rows = []
    for row_index in range(math.ceil(len(setup_items) / 3)):
        row = []
        for item_index in range(row_index * 3, row_index * 3 + 3):
            row.append(_waiter_cell(setup_items[item_index], styles["setup_cell"]) if item_index < len(setup_items) else "")
        rows.append(row)

    table = Table(rows, colWidths=[5.73 * cm, 5.73 * cm, 5.73 * cm], hAlign="RIGHT")
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.45, WAITER_WARM_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))

    elements.append(KeepTogether([heading, table]))
    elements.append(Spacer(1, 12))


def generate_waiter_pdf(
    event_name: str,
    event_date: str,
    hebrew_date: Optional[str],
    guest_count: int,
    location: Optional[str],
    dishes_data: list,
    blank_path: Optional[str] = None,
    hall_name: Optional[str] = None,
    city: Optional[str] = None,
    owners: Optional[List[Dict[str, str]]] = None,
    event_notes: Optional[str] = None,
    is_disposable: Optional[bool] = None,
    simple_mode: bool = False,
    waiter_count: Optional[int] = None,
    table_count: Optional[int] = None,
    event_sequence_label: Optional[str] = None,
    event_sequence_color: Optional[str] = None,
    event_tool_set_items: Optional[list] = None,
    document_title: str = "הוראות הגשה",
) -> BytesIO:
    """
    יצירת PDF להדפסה עבור מלצרים - מבנה מקצועי
    
    עמוד ראשון: פרטי האירוע הכלליים
    שאר העמודים: הוראות הגשה לפי קטגוריות
    
    Args:
        event_name: שם האירוע
        event_date: תאריך האירוע (מעוצב)
        hebrew_date: תאריך עברי (אופציונלי)
        guest_count: מספר אורחים
        location: כתובת האירוע
        dishes_data: רשימת מנות עם פרטי הגשה
        blank_path: נתיב לתמונת בלאנק (אופציונלי)
        hall_name: שם האולם
        city: עיר
        owners: רשימת בעלי האירוע
        event_notes: הערות מיוחדות לאירוע
        is_disposable: האם כלים חד"פ
    
    Returns:
        BytesIO buffer עם ה-PDF
    """
    buffer = BytesIO()
    
    _register_hebrew_fonts()
    styles = _get_hebrew_styles()
    
    first_page_blank = blank_path if blank_path else BLANK_FIRST_PAGE_PATH
    other_pages_blank = BLANK_OTHER_PAGES_PATH
    
    if first_page_blank and not first_page_blank.lower().endswith('.png'):
        first_page_blank = first_page_blank.replace('.pdf', '.png')
    if other_pages_blank and not other_pages_blank.lower().endswith('.png'):
        other_pages_blank = other_pages_blank.replace('.pdf', '.png')
    
    if not first_page_blank or not os.path.exists(first_page_blank):
        first_page_blank = None
    if not other_pages_blank or not os.path.exists(other_pages_blank):
        other_pages_blank = None
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=4*cm,
        bottomMargin=2.5*cm
    )
    
    elements = []
    
    # ========================================
    # עמוד ראשון - פרטי האירוע
    # ========================================
    elements.append(Spacer(1, 110))

    title_text = _bidi(document_title)
    elements.append(Paragraph(title_text, styles['main_title']))
    elements.append(Spacer(1, 10))
    
    event_title = _bidi(event_name)
    event_name_style = ParagraphStyle(
        'EventName',
        parent=styles['title'],
        fontSize=16,
        textColor=HexColor('#34495e')
    )
    elements.append(Paragraph(event_title, event_name_style))
    elements.append(Spacer(1, 18))
    
    # פרטי האירוע
    section_title = _bidi("פרטי האירוע")
    elements.append(Paragraph(section_title, styles['section_title']))
    
    # תאריך
    date_display = event_date
    if hebrew_date:
        date_display = f"{event_date} | {hebrew_date}"
    date_text = _bidi(f"תאריך: {date_display}")
    elements.append(Paragraph(date_text, styles['event_detail']))

    if event_sequence_label:
        sequence_text = _bidi(event_sequence_label)
        sequence_style = ParagraphStyle(
            'EventSequence',
            parent=styles['event_detail'],
            fontName='HebrewBold',
            textColor=_event_sequence_text_color(event_sequence_color),
        )
        elements.append(Paragraph(sequence_text, sequence_style))
    
    # מיקום
    full_location = location or ""
    if city:
        full_location = f"{location}, {city}" if location else city
    if full_location:
        location_text = _bidi(f"מיקום: {full_location}")
        elements.append(Paragraph(location_text, styles['event_detail']))
    
    # שם האולם
    if hall_name:
        hall_text = _bidi(f"אולם: {hall_name}")
        elements.append(Paragraph(hall_text, styles['event_detail']))
    
    # מספר סועדים
    guests_text = _bidi(f"מספר סועדים: {guest_count}")
    elements.append(Paragraph(guests_text, styles['event_detail']))

    # חישובים אוטומטיים - מלצרים ושולחנות
    if waiter_count is not None:
        waiter_text = _bidi(f"מספר מלצרים: {waiter_count}  (2 מלצרים לכל 50 סועדים)")
        elements.append(Paragraph(waiter_text, styles['event_detail']))
    if table_count is not None:
        table_text = _bidi(f"מספר שולחנות: {table_count}  (שולחן לכל 8 סועדים; שולחן מתוק - חצי)")
        elements.append(Paragraph(table_text, styles['event_detail']))

    # סוג הכלים
    if is_disposable is not None:
        elements.append(Spacer(1, 24))  # 2 שורות לפני
        dishes_label = "כלים חד פעמיים" if is_disposable else "כלים אמיתיים"
        dishes_type_text = _bidi(f"סוג כלים: {dishes_label}")
        elements.append(Paragraph(dishes_type_text, styles['dishes_type']))
        elements.append(Spacer(1, 24))  # 2 שורות אחרי
    
    # פרטי בעלי האירוע
    if owners and len(owners) > 0:
        owners_title = _bidi("פרטי בעל/י האירוע")
        elements.append(Paragraph(owners_title, styles['section_title']))
        
        for owner in owners:
            owner_name = owner.get('name', '')
            owner_phone = owner.get('phone', '')
            if owner_name:
                owner_info = f"שם: {owner_name}"
                if owner_phone:
                    owner_info += f"  |  טלפון: {owner_phone}"
                owner_text = _bidi(owner_info)
                elements.append(Paragraph(owner_text, styles['owner']))
        
        elements.append(Spacer(1, 15))
    
    # הערות מיוחדות לאירוע
    if event_notes:
        notes_title = _bidi("הערות מיוחדות לאירוע")
        elements.append(Paragraph(notes_title, styles['section_title']))
        
        notes_text = _bidi(event_notes)
        elements.append(Paragraph(notes_text, styles['event_notes']))
    
    # ========================================
    # מעבר לעמוד חדש - הוראות הגשה
    # ========================================
    elements.append(PageBreak())
    
    serving_title = _bidi(document_title)
    elements.append(Paragraph(serving_title, styles['title']))
    elements.append(Spacer(1, 12))
    _add_event_tool_set_section(elements, styles, event_tool_set_items)
    
    # קיבוץ מנות לפי קטגוריות
    category_order = ['סלטים', 'מנות ראשונות', 'מנה ראשונה', 'תוספות', 'מנות אחרונות', 'מנה אחרונה', 'שתיה']
    
    dishes_by_category: Dict[str, List[Dict[str, Any]]] = {}
    for dish in dishes_data:
        cat = dish.get('category', 'אחר')
        if cat not in dishes_by_category:
            dishes_by_category[cat] = []
        dishes_by_category[cat].append(dish)
    
    processed_categories = set()
    
    for cat in category_order:
        if cat in dishes_by_category:
            _add_category_dishes_table(elements, cat, dishes_by_category[cat], styles)
            processed_categories.add(cat)
    
    for cat, dishes in dishes_by_category.items():
        if cat not in processed_categories:
            _add_category_dishes_table(elements, cat, dishes, styles)
    
    # ========================================
    # סיום
    # ========================================
    elements.append(Spacer(1, 20))
    
    footer_text = _bidi("בהצלחה!")
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['normal'],
        fontName='HebrewBold',
        fontSize=12,
        alignment=TA_CENTER,
        textColor=HexColor('#2c3e50')
    )
    elements.append(Paragraph(footer_text, footer_style))
    
    # ========================================
    # בניית ה-PDF
    # ========================================
    page_counter = {'current': 0}
    
    def on_first_page(canvas, doc):
        page_counter['current'] = 1
        _draw_waiter_page_background(canvas, doc, first_page_blank, is_first_page=True, simple_mode=simple_mode)
    
    def on_later_pages(canvas, doc):
        page_counter['current'] += 1
        _draw_waiter_page_background(canvas, doc, other_pages_blank, is_first_page=False, simple_mode=simple_mode)
    
    doc.build(
        elements, 
        onFirstPage=on_first_page,
        onLaterPages=on_later_pages
    )
    
    buffer.seek(0)
    return buffer




def generate_shopping_pdf(
    event_name: str,
    event_date: str,
    guest_count: int,
    shopping_items: list,
    equipment_items: list,
    event_sequence_label: Optional[str] = None,
    event_sequence_color: Optional[str] = None,
) -> BytesIO:
    """Create a clean RTL shopping-list PDF with minimal color."""
    buffer = BytesIO()
    _register_hebrew_fonts()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.35 * cm,
        leftMargin=1.35 * cm,
        topMargin=1.55 * cm,
        bottomMargin=1.55 * cm,
    )

    page_width = A4[0] - 2.7 * cm
    line_color = HexColor("#d5dbe8")
    header_bg = HexColor("#eef1f5")
    alt_bg = HexColor("#fbfcfe")
    text_color = HexColor("#15192d")
    muted_color = HexColor("#5c6474")

    title_style = ParagraphStyle(
        "ShoppingSolidTitle",
        fontName="HebrewBold",
        fontSize=20,
        leading=26,
        alignment=TA_CENTER,
        textColor=text_color,
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "ShoppingSolidSubtitle",
        fontName="HebrewRegular",
        fontSize=10,
        leading=13,
        alignment=TA_CENTER,
        textColor=muted_color,
        spaceAfter=10,
    )
    section_style = ParagraphStyle(
        "ShoppingSolidSection",
        fontName="HebrewBold",
        fontSize=12,
        leading=15,
        alignment=TA_RIGHT,
        textColor=text_color,
    )
    header_style = ParagraphStyle(
        "ShoppingSolidHeader",
        fontName="HebrewBold",
        fontSize=8.5,
        leading=11,
        alignment=TA_CENTER,
        textColor=HexColor("#343b4c"),
    )
    cell_style = ParagraphStyle(
        "ShoppingSolidCell",
        fontName="HebrewRegular",
        fontSize=8.6,
        leading=11,
        alignment=TA_RIGHT,
        textColor=text_color,
    )
    cell_center_style = ParagraphStyle(
        "ShoppingSolidCellCenter",
        parent=cell_style,
        alignment=TA_CENTER,
    )
    cell_bold_center_style = ParagraphStyle(
        "ShoppingSolidCellBoldCenter",
        parent=cell_center_style,
        fontName="HebrewBold",
    )
    hint_style = ParagraphStyle(
        "ShoppingSolidHint",
        parent=cell_style,
        fontSize=7.4,
        leading=9,
        textColor=muted_color,
        spaceBefore=1,
    )

    def value(item: Any, key: str, default: Any = None) -> Any:
        if isinstance(item, dict):
            return item.get(key, default)
        return getattr(item, key, default)

    def fmt_num(raw: Any) -> str:
        if raw is None:
            return ""
        try:
            number = float(raw)
        except (TypeError, ValueError):
            return str(raw)
        if number.is_integer():
            return str(int(number))
        return f"{number:.3f}".rstrip("0").rstrip(".")

    def p(text: Any, style: ParagraphStyle = cell_style) -> Paragraph:
        return Paragraph(_bidi(str(text or "")), style)

    def name_cell(item: Any, name_key: str = "name") -> list:
        cell = [p(value(item, name_key, ""), cell_style)]
        details = [part for part in [value(item, "source_type"), value(item, "formula_label")] if part]
        if details:
            cell.append(p(" | ".join(str(part) for part in details), hint_style))
        return cell

    def section_heading(title: str, note: str = "") -> Table:
        table = Table(
            [[p(title, section_style), p(note, hint_style)]],
            colWidths=[page_width * 0.42, page_width * 0.58],
            hAlign="RIGHT",
        )
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), header_bg),
            ("BOX", (0, 0), (-1, -1), 0.6, line_color),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        return table

    def make_table(rows: list, col_widths: list) -> Table:
        commands = [
            ("GRID", (0, 0), (-1, -1), 0.45, line_color),
            ("BACKGROUND", (0, 0), (-1, 0), HexColor("#f8fafc")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]
        for row_index in range(2, len(rows), 2):
            commands.append(("BACKGROUND", (0, row_index), (-1, row_index), alt_bg))
        table = Table(rows, colWidths=col_widths, repeatRows=1, hAlign="RIGHT")
        table.setStyle(TableStyle(commands))
        return table

    elements = []
    elements.append(Paragraph(_bidi("רשימת קניות לאירוע"), title_style))
    elements.append(Paragraph(_bidi(event_name), title_style))
    detail_text = f"תאריך: {event_date}   |   מספר סועדים: {guest_count}"
    elements.append(Paragraph(_bidi(detail_text), subtitle_style))
    if event_sequence_label:
        sequence_style = ParagraphStyle(
            "ShoppingSolidSequence",
            parent=subtitle_style,
            fontName="HebrewBold",
            textColor=_event_sequence_text_color(event_sequence_color),
        )
        elements.append(Paragraph(_bidi(event_sequence_label), sequence_style))

    detail_rows = [[
        p("סטטוס", header_style),
        p("לפני קנייה", cell_bold_center_style),
        p("סועדים", header_style),
        p(fmt_num(guest_count), cell_bold_center_style),
        p("תאריך", header_style),
        p(event_date, cell_bold_center_style),
    ]]
    detail_rows = [[
        p(event_date, cell_bold_center_style),
        p("תאריך", header_style),
        p(fmt_num(guest_count), cell_bold_center_style),
        p("סועדים", header_style),
        p("לפני קנייה", cell_bold_center_style),
        p("סטטוס", header_style),
    ]]
    detail_table = Table(
        detail_rows,
        colWidths=[page_width * 0.38, page_width * 0.10, page_width * 0.14, page_width * 0.10, page_width * 0.18, page_width * 0.10],
        hAlign="RIGHT",
    )
    detail_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.45, line_color),
        ("BACKGROUND", (0, 0), (-1, -1), HexColor("#ffffff")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    elements.append(detail_table)
    elements.append(Spacer(1, 12))

    elements.append(section_heading("חומרי גלם", "מוצר, כמות נדרשת, מלאי ומה לקנות בפועל"))
    if shopping_items:
        rows = [[
            p("לקנות", header_style),
            p("גודל אריזה", header_style),
            p("במלאי", header_style),
            p("נדרש", header_style),
            p("קטגוריה", header_style),
            p("מוצר", header_style),
        ]]
        sorted_items = sorted(
            shopping_items,
            key=lambda item: (str(value(item, "category") or ""), str(value(item, "name") or "")),
        )
        for item in sorted_items:
            package_quantity = value(item, "package_quantity")
            packages_to_buy = int(value(item, "packages_to_buy", 0) or 0)
            need_qty = value(item, "need_to_buy_quantity", 0)
            quantity = value(item, "quantity", 0)
            stock = value(item, "quantity_in_stock", 0)
            unit = value(item, "unit", "")
            try:
                fallback_need = max(0.0, float(quantity or 0) - float(stock or 0))
            except (TypeError, ValueError):
                fallback_need = 0.0

            if packages_to_buy > 0 and package_quantity:
                buy_display = f"{packages_to_buy} חב׳"
            elif packages_to_buy > 0:
                buy_display = f"{packages_to_buy} {unit}".strip()
            elif float(need_qty or 0) > 0:
                buy_display = f"{fmt_num(need_qty)} {unit}".strip()
            elif fallback_need > 0:
                buy_display = f"{fmt_num(fallback_need)} {unit}".strip()
            else:
                buy_display = "אין חוסר"
            rows.append([
                p(buy_display, cell_bold_center_style),
                p(fmt_num(package_quantity) if package_quantity else "-", cell_center_style),
                p(fmt_num(value(item, "quantity_in_stock", 0)), cell_center_style),
                p(f"{fmt_num(value(item, 'quantity', 0))} {unit}".strip(), cell_bold_center_style),
                p(value(item, "category") or "כללי", cell_center_style),
                name_cell(item),
            ])

        elements.append(make_table(
            rows,
            [
                page_width * 0.16,
                page_width * 0.13,
                page_width * 0.11,
                page_width * 0.13,
                page_width * 0.14,
                page_width * 0.33,
            ],
        ))
    else:
        elements.append(p("אין חומרי גלם לרשימה זו", cell_style))

    elements.append(Spacer(1, 12))
    elements.append(section_heading("כלים וציוד", "כלי הגשה, סכו\"ם וציוד נלווה"))
    if equipment_items:
        rows_eq = [[
            p("להשלים", header_style),
            p("במלאי", header_style),
            p("נדרש", header_style),
            p("סוג", header_style),
            p("פריט", header_style),
        ]]
        sorted_equipment = sorted(
            equipment_items,
            key=lambda item: (str(value(item, "category") or ""), str(value(item, "name") or "")),
        )
        for item in sorted_equipment:
            need_to_buy = int(value(item, "need_to_buy", 0) or value(item, "shortage", 0) or 0)
            rows_eq.append([
                p(str(need_to_buy) if need_to_buy > 0 else "אין חוסר", cell_bold_center_style),
                p(fmt_num(value(item, "available_in_stock", 0)), cell_center_style),
                p(fmt_num(value(item, "quantity", 0)), cell_bold_center_style),
                p(value(item, "category") or "", cell_center_style),
                name_cell(item),
            ])

        elements.append(make_table(
            rows_eq,
            [
                page_width * 0.16,
                page_width * 0.13,
                page_width * 0.13,
                page_width * 0.16,
                page_width * 0.42,
            ],
        ))
    else:
        elements.append(p("אין כלים וציוד לרשימה זו", cell_style))

    def on_page(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(line_color)
        canvas.setLineWidth(0.7)
        canvas.line(1.35 * cm, A4[1] - 0.8 * cm, A4[0] - 1.35 * cm, A4[1] - 0.8 * cm)
        canvas.setFont("HebrewRegular", 9)
        canvas.setFillColor(grey)
        canvas.drawCentredString(A4[0] / 2, 1.0 * cm, f"- {canvas.getPageNumber()} -")
        canvas.restoreState()

    doc.build(elements, onFirstPage=on_page, onLaterPages=on_page)
    buffer.seek(0)
    return buffer


def generate_delivery_sheet_pdf(
    event_data: Dict[str, Any],
    event_date: str,
    event_sequence_label: Optional[str] = None,
    event_sequence_color: Optional[str] = None,
) -> BytesIO:
    """Create a printable, RTL delivery checklist for the driver."""
    buffer = BytesIO()
    _register_hebrew_fonts()
    styles = _get_hebrew_styles()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.4 * cm,
        leftMargin=1.4 * cm,
        topMargin=1.3 * cm,
        bottomMargin=1.3 * cm,
    )

    elements = []
    elements.append(Paragraph(_bidi("דף הוראות למשלוחן – קייטרינג"), styles["main_title"]))
    elements.append(Paragraph(_bidi(event_data.get("name") or ""), styles["title"]))
    elements.append(Spacer(1, 6))

    if event_sequence_label:
        color_names = {
            "orange": "כתום", "green": "ירוק", "purple": "סגול",
            "sky": "תכלת", "red": "אדום",
        }
        color_hex = EVENT_SEQUENCE_COLOR_HEX.get(event_sequence_color or "", "#374151")
        sequence_style = ParagraphStyle(
            "DeliveryEventSequence",
            parent=styles["event_detail"],
            fontName="HebrewBold",
            fontSize=14,
            alignment=TA_CENTER,
            textColor=HexColor("#ffffff"),
        )
        label = event_sequence_label
        if event_sequence_color in color_names:
            label += f" – צבע {color_names[event_sequence_color]}"
        banner = Table([[Paragraph(_bidi(label), sequence_style)]], colWidths=[17.8 * cm])
        banner.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), HexColor(color_hex)),
            ("BOX", (0, 0), (-1, -1), 1, HexColor(color_hex)),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ]))
        elements.append(banner)
        elements.append(Spacer(1, 8))

    def add_section(title: str) -> None:
        elements.append(Spacer(1, 8))
        elements.append(Paragraph(_bidi(title), styles["section_title"]))

    def add_line(label: str, value: Any) -> None:
        if value is None or value == "":
            return
        if isinstance(value, bool):
            value = "כן" if value else "לא"
        elements.append(Paragraph(_bidi(f"{label}: {value}"), styles["event_detail"]))

    def add_check_line(text: str, checked: bool = False) -> None:
        mark = "☑" if checked else "□"
        elements.append(Paragraph(_bidi(f"{mark} {text}"), styles["event_detail"]))

    add_section("פרטי האירוע והמיקום")
    add_line("תאריך", event_date)
    add_line("שעה", event_data.get("event_time"))
    add_line("שם האולם/המקום", event_data.get("venue_name"))
    add_line("כתובת", event_data.get("address"))
    add_line("עיר", event_data.get("city"))
    add_line("קומה", event_data.get("floor"))
    add_line("מעלית", event_data.get("has_elevator"))
    add_line("קוד/מפתח", event_data.get("access_code"))

    add_section("אנשי קשר")
    add_line("איש קשר במקום", event_data.get("onsite_contact_name"))
    add_line("טלפון איש קשר", event_data.get("onsite_contact_phone"))
    add_line("בעל אולם", event_data.get("hall_owner_name"))
    add_line("טלפון בעל אולם", event_data.get("hall_owner_phone"))
    for index, owner in enumerate(event_data.get("owners") or [], start=1):
        owner_label = f"בעל/ת אירוע {index}"
        owner_text = owner.get("name") or ""
        if owner.get("phone"):
            owner_text += f" | {owner.get('phone')}"
        add_line(owner_label, owner_text)

    add_section("גישה ופריקה")
    add_line("חניה קרובה", event_data.get("has_nearby_parking"))
    add_line("כניסה אחורית", event_data.get("has_back_entrance"))
    add_line("דרוש עגלות", event_data.get("requires_carts"))
    add_line("הערות גישה", event_data.get("access_notes"))
    add_line("סוג כלים", event_data.get("dishware_type"))
    add_line("מיקום הפריקה והנחת הציוד", event_data.get("equipment_dropoff_location"))
    add_line("תכולה ומוצרים נלווים", event_data.get("delivery_contents_notes"))
    add_line("להוציא ברגע האחרון", event_data.get("last_minute_items"))

    boxes = event_data.get("boxes") or []
    add_section(f"בדיקת העמסה – סה\"כ לפי המערכת: {event_data.get('total_boxes') or 0} ארגזים")
    header_style = ParagraphStyle(
        "DeliveryTableHeader", parent=styles["event_detail"], fontName="HebrewBold",
        alignment=TA_CENTER, textColor=HexColor("#ffffff"), fontSize=9,
    )
    cell_style = ParagraphStyle(
        "DeliveryTableCell", parent=styles["event_detail"], fontSize=9, leading=12,
    )
    box_rows = [[
        Paragraph(_bidi("נספר בפועל"), header_style),
        Paragraph(_bidi("הערה"), header_style),
        Paragraph(_bidi("כמות במערכת"), header_style),
        Paragraph(_bidi("סוג ארגז"), header_style),
    ]]
    for box in boxes:
        box_rows.append([
            Paragraph("________", cell_style),
            Paragraph(_bidi(box.get("notes") or ""), cell_style),
            Paragraph(str(box.get("quantity") or 0), cell_style),
            Paragraph(_bidi(box.get("box_type") or ""), cell_style),
        ])
    if not boxes:
        box_rows.append([
            Paragraph("________", cell_style), Paragraph("", cell_style),
            Paragraph("0", cell_style), Paragraph(_bidi("לא הוזנו ארגזים"), cell_style),
        ])
    box_table = Table(box_rows, colWidths=[3.1 * cm, 6.1 * cm, 3.1 * cm, 5.5 * cm], repeatRows=1)
    box_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#334155")),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#94a3b8")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    elements.append(box_table)
    elements.append(Spacer(1, 5))
    add_line("סה\"כ ארגזים שנספרו בפועל", "____________")

    checklist = [
        ("לבדוק מקרר", "check_refrigerator"),
        ("לבדוק מקפיא", "check_freezer"),
        ("לבדוק פלטה", "check_hot_plate"),
        ("לחבר גז", "connect_gas"),
        ("להכניס למקרר", "put_in_refrigerator"),
        ("להכניס למקפיא", "put_in_freezer"),
        ("לשים על פלטה", "put_on_hot_plate"),
        ("לספור ארגזים", "count_boxes"),
        ("לבדוק שתיה", "check_drinks"),
        ("לבדוק לחמניות", "check_rolls"),
    ]
    selected_checks = [label for label, key in checklist if event_data.get(key)]
    add_section("פעולות ובדיקות מיוחדות לאירוע")
    if selected_checks:
        for label, key in checklist:
            if event_data.get(key):
                add_check_line(label)
    else:
        elements.append(Paragraph(_bidi("אין בדיקות חובה שסומנו"), styles["event_detail"]))

    notes = [item.get("note") for item in event_data.get("delivery_notes") or [] if item.get("note")]
    if notes:
        add_section("הערות קבועות")
        for note in notes:
            elements.append(Paragraph(_bidi(f"• {note}"), styles["event_detail"]))

    if event_data.get("delivery_special_notes"):
        add_section("הערות מיוחדות")
        elements.append(Paragraph(_bidi(event_data["delivery_special_notes"]), styles["event_notes"]))

    add_section("הוראות קבועות – חובה בכל משלוח")
    fixed_instructions = [
        "לפני היציאה: להתעדכן מול המשרד לגבי שינויים של הרגע האחרון.",
        "לספור את כל הארגזים ולהשוות לכמות הרשומה בדף.",
        "מוצרים לקירור או להקפאה יוצאים אחרונים מהמטבח ונפרקים ראשונים.",
        "בפריקה: להעביר מיד מוצרים קרים למקרר ומוצרים קפואים למקפיא.",
        "לבדוק פיזית שהמקרר, המקפיא או הפלטה שנדרשו עובדים כראוי.",
        "להניח ציוד רק במקום המוגדר ובתיאום עם איש הקשר בשטח.",
        "אין לעזוב לפני ספירה חוזרת, השלמת הבדיקות ואישור איש הקשר.",
        "לאחר המסירה: להודיע לבעלי הקייטרינג שהמשלוח נמסר והכול סודר.",
    ]
    for instruction in fixed_instructions:
        add_check_line(instruction)

    add_section("אישור מסירה")
    add_line("שם המאשר במקום", "____________________")
    add_line("שעת מסירה", "__________")
    add_line("השליח הודיע לבעלי הקייטרינג", "כן / לא")

    def _delivery_footer(canvas, _doc):
        canvas.saveState()
        canvas.setFont("HebrewRegular", 8)
        canvas.setFillColor(HexColor("#64748b"))
        canvas.drawCentredString(A4[0] / 2, 0.65 * cm, f"{canvas.getPageNumber()}")
        canvas.restoreState()

    doc.build(elements, onFirstPage=_delivery_footer, onLaterPages=_delivery_footer)
    buffer.seek(0)
    return buffer
