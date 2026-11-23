"""
Events router — all event CRUD + sub-resources (dishes, trays, lists).
"""

from datetime import datetime
from typing import Optional
from urllib.parse import quote
import math

from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.event_service import EventService
from app.services.event_calculation_service import EventCalculationService
from app.schemas.calculation import (
    EventCalculationSettingsUpdate,
    EventCalculationSummary,
    EventDishServingSelectionsRequest,
    EventManualToolRowsRequest,
)
from app.schemas.event import (
    EventCreate, EventUpdate, EventStatusUpdate, EventPriceUpdate,
    EventDishCreate, EventDishUpdate, EventDishBulkRequest,
    EventTrayCreate, EventTrayUpdate, MorningSplitUpdate,
    EventResponse, EventListResponse,
    DeliveryNoteTemplateResponse,
    ShoppingListResponse, EquipmentListResponse,
)
from app.schemas.common import SuccessResponse, BulkOperationResponse
from app.models.event import DeliveryNoteTemplate, Event, EventDish
from app.models.dish import Dish, ServingDish
from app.models.tool import Tool
from app.utils.pdf_generator import generate_delivery_sheet_pdf, generate_waiter_pdf, generate_shopping_pdf

router = APIRouter(prefix="/events", tags=["events"])


def _event_sequence_label(event: Event, db: Session) -> str | None:
    if not event.date:
        return None
    day_start = event.date.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = event.date.replace(hour=23, minute=59, second=59, microsecond=999999)
    same_day_count = (
        db.query(Event)
        .filter(Event.is_deleted == False)  # noqa: E712
        .filter(Event.date >= day_start, Event.date <= day_end)
        .count()
    )
    if same_day_count <= 1:
        return None
    return f"אירוע #{event.day_sequence_number or 1}"


def _svc(db: Session = Depends(get_db)) -> EventService:
    return EventService(db)


def _requirement_value(requirement, key: str, default=None):
    if isinstance(requirement, dict):
        return requirement.get(key, default)
    return getattr(requirement, key, default)


def _format_waiter_quantity(value) -> str:
    try:
        numeric = float(value or 0)
    except (TypeError, ValueError):
        return str(value or "")
    if numeric.is_integer():
        return str(int(numeric))
    return f"{numeric:.1f}".rstrip("0").rstrip(".")


def _append_drinks_to_waiter_data(event: Event, dishes_data: list[dict], db: Session) -> None:
    try:
        summary = EventCalculationService(db).summarize(event)
    except Exception:
        return

    drink_rows = [
        item for item in (summary.product_requirements or [])
        if _requirement_value(item, "source_type") == "drink"
    ]
    if not drink_rows:
        return

    for item in drink_rows:
        name = _requirement_value(item, "name", "")
        quantity = _format_waiter_quantity(_requirement_value(item, "quantity", ""))
        unit = _requirement_value(item, "unit", "")
        label = f"{name} - {quantity} {unit}".strip()
        dishes_data.append({
            "name": label,
            "category": "שתיה",
            "serving_dishes": [{"name": "בקבוקי שתיה", "quantity": 1}],
            "serving_description": "לוודא שהשתיה נמצאת באירוע ומסודרת במקום נגיש למלצרים.",
            "notes": "",
            "waiter_notes": "",
        })


# ── CRUD ──────────────────────────────────────────────────────────────

def _event_tool_set_items_for_pdf(event: Event, db: Session) -> list[dict]:
    settings = EventCalculationService(db).get_settings(event.id, create=False)
    if not settings or settings.event_tool_set_items is None:
        return []

    guest_count = event.guest_count or 1
    result: list[dict] = []
    for row in settings.event_tool_set_items:
        per_guest = float(row.get("quantity_per_guest") or 0)
        tool_id = row.get("tool_id")
        if per_guest <= 0 or not tool_id:
            continue

        tool = db.query(Tool).filter(Tool.id == tool_id).first()
        if not tool:
            continue

        result.append({
            "name": tool.name,
            "calculated_quantity": math.ceil(guest_count * per_guest),
        })
    return result


@router.get("", response_model=EventListResponse)
def get_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = None,
    menu_type: Optional[str] = None,
    search: Optional[str] = None,
    svc: EventService = Depends(_svc),
):
    items, total = svc.get_events(
        skip=skip, limit=limit, status=status,
        menu_type=menu_type, search=search,
    )
    return {"items": items, "total": total, "skip": skip, "limit": limit}


@router.get("/range", response_model=list[EventResponse])
def get_events_in_range(
    start: str = Query(...),
    end: str = Query(...),
    svc: EventService = Depends(_svc),
):
    s = datetime.fromisoformat(start)
    e = datetime.fromisoformat(end)
    return svc.get_events_in_range(s, e)


@router.get("/delivery-note-templates", response_model=list[DeliveryNoteTemplateResponse])
def get_delivery_note_templates(db: Session = Depends(get_db)):
    return (
        db.query(DeliveryNoteTemplate)
        .filter(DeliveryNoteTemplate.is_deleted == False)  # noqa: E712
        .order_by(DeliveryNoteTemplate.display_order, DeliveryNoteTemplate.id)
        .all()
    )


@router.get("/{event_id}", response_model=EventResponse)
def get_event(event_id: int, svc: EventService = Depends(_svc)):
    return svc.get_event(event_id)


@router.post("", status_code=201, response_model=EventResponse)
def create_event(data: EventCreate, svc: EventService = Depends(_svc)):
    return svc.create_event(data)


@router.put("/{event_id}", response_model=EventResponse)
def update_event(event_id: int, data: EventUpdate, svc: EventService = Depends(_svc)):
    return svc.update_event(event_id, data)


@router.delete("/{event_id}", response_model=SuccessResponse)
def delete_event(event_id: int, svc: EventService = Depends(_svc)):
    return svc.delete_event(event_id)


# ── Status ────────────────────────────────────────────────────────────

@router.patch("/{event_id}/status", response_model=EventResponse)
def change_status(event_id: int, data: EventStatusUpdate, svc: EventService = Depends(_svc)):
    return svc.change_status(event_id, data.status)


# ── Pricing ───────────────────────────────────────────────────────────

@router.patch("/{event_id}/price", response_model=EventResponse)
def update_price(event_id: int, data: EventPriceUpdate, svc: EventService = Depends(_svc)):
    """Update the final price and recalculate discount."""
    return svc.update_final_price(event_id, data.final_price)


# ── Dishes ────────────────────────────────────────────────────────────

@router.post("/{event_id}/dishes", response_model=EventResponse)
def add_dish(event_id: int, data: EventDishCreate, svc: EventService = Depends(_svc)):
    return svc.add_dish_to_event(event_id, data)


@router.put("/{event_id}/dishes/{dish_id}", response_model=EventResponse)
def update_dish(event_id: int, dish_id: int, data: EventDishUpdate, svc: EventService = Depends(_svc)):
    return svc.update_event_dish(event_id, dish_id, data)


@router.delete("/{event_id}/dishes/{dish_id}", response_model=SuccessResponse)
def remove_dish(event_id: int, dish_id: int, svc: EventService = Depends(_svc)):
    return svc.remove_dish_from_event(event_id, dish_id)


@router.post("/{event_id}/dishes/bulk", response_model=BulkOperationResponse)
def bulk_save_dishes(
    event_id: int,
    data: EventDishBulkRequest,
    svc: EventService = Depends(_svc),
):
    return svc.bulk_save_dishes(
        event_id,
        data.dishes,
        is_draft=data.is_draft,
        replace=data.replace,
    )


@router.post("/{event_id}/dishes/finalize", response_model=BulkOperationResponse)
def finalize_drafts(event_id: int, svc: EventService = Depends(_svc)):
    return svc.finalize_drafts(event_id)


# ── Trays ─────────────────────────────────────────────────────────────

@router.post("/{event_id}/trays", response_model=EventResponse)
def add_tray(event_id: int, data: EventTrayCreate, svc: EventService = Depends(_svc)):
    return svc.add_tray(event_id, data)


@router.put("/{event_id}/trays/{tray_id}", response_model=EventResponse)
def update_tray(event_id: int, tray_id: int, data: EventTrayUpdate, svc: EventService = Depends(_svc)):
    return svc.update_tray(event_id, tray_id, data)


@router.delete("/{event_id}/trays/{tray_id}", response_model=SuccessResponse)
def remove_tray(event_id: int, tray_id: int, svc: EventService = Depends(_svc)):
    return svc.remove_tray(event_id, tray_id)


# ── Morning split ────────────────────────────────────────────────────

@router.patch("/{event_id}/morning-split", response_model=EventResponse)
def toggle_morning_split(event_id: int, data: MorningSplitUpdate, svc: EventService = Depends(_svc)):
    return svc.toggle_morning_split(event_id, data.is_morning_split)


@router.post("/{event_id}/restore-stock", response_model=SuccessResponse)
def restore_stock(event_id: int, svc: EventService = Depends(_svc)):
    return svc.restore_stock(event_id)


# Event-wide calculations

def _calculation_event(event_id: int, db: Session) -> Event:
    event = db.query(Event).filter(Event.id == event_id, Event.is_deleted == False).first()  # noqa: E712
    if not event:
        raise HTTPException(status_code=404, detail="אירוע לא נמצא")
    return event


@router.get("/{event_id}/calculations/summary", response_model=EventCalculationSummary)
def get_calculation_summary(event_id: int, db: Session = Depends(get_db)):
    event = _calculation_event(event_id, db)
    return EventCalculationService(db).summarize(event)


@router.put("/{event_id}/calculations/settings", response_model=EventCalculationSummary)
def update_calculation_settings(
    event_id: int,
    data: EventCalculationSettingsUpdate,
    db: Session = Depends(get_db),
):
    event = _calculation_event(event_id, db)
    calculations = EventCalculationService(db)
    calculations.update_settings(event_id, data)
    EventService(db)._recalc_total(event)
    db.commit()
    db.refresh(event)
    return calculations.summarize(event, use_snapshot=False)


@router.get("/{event_id}/calculations/dish-serving-selections")
def get_dish_serving_selections(event_id: int, db: Session = Depends(get_db)):
    event = _calculation_event(event_id, db)
    service = EventCalculationService(db)
    result = []
    for kind in ("serving", "packaging"):
        selected = service._selection_map(event_id, kind)
        for ed in event.dishes:
            selected_id = selected.get(("dish", ed.id)) or selected.get(("dish_id", ed.dish_id))
            resolved = service._resolve_serving_set(event, ed.dish_id, selected_id) if kind == "serving" else service._resolve_set(ed.dish_id, kind, selected_id)
            if resolved:
                result.append({"dish_id": ed.dish_id, "set_type": kind, "set_id": resolved.id})
    return result


@router.put("/{event_id}/calculations/dish-serving-selections", response_model=EventCalculationSummary)
def update_dish_serving_selections(
    event_id: int,
    data: EventDishServingSelectionsRequest,
    db: Session = Depends(get_db),
):
    event = _calculation_event(event_id, db)
    calculations = EventCalculationService(db)
    calculations.replace_serving_selections(event_id, data.selections)
    db.commit()
    return calculations.summarize(event)


@router.put("/{event_id}/calculations/manual-tools", response_model=EventCalculationSummary)
def update_manual_tools(
    event_id: int,
    data: EventManualToolRowsRequest,
    db: Session = Depends(get_db),
):
    event = _calculation_event(event_id, db)
    calculations = EventCalculationService(db)
    calculations.replace_manual_tools(event_id, data.rows)
    db.commit()
    return calculations.summarize(event)


@router.post("/{event_id}/calculations/recalculate", response_model=EventCalculationSummary)
def recalculate_event(event_id: int, db: Session = Depends(get_db)):
    event = _calculation_event(event_id, db)
    return EventCalculationService(db).summarize(event)


# ── Lists ─────────────────────────────────────────────────────────────

@router.get("/{event_id}/shopping-list", response_model=ShoppingListResponse)
def get_shopping_list(event_id: int, svc: EventService = Depends(_svc)):
    return svc.get_shopping_list(event_id)


@router.get("/{event_id}/equipment-list", response_model=EquipmentListResponse)
def get_equipment_list(event_id: int, svc: EventService = Depends(_svc)):
    return svc.get_equipment_list(event_id)


@router.get("/{event_id}/delivery-sheet/pdf")
def get_delivery_sheet_pdf(event_id: int, svc: EventService = Depends(_svc), db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id, Event.is_deleted == False).first()  # noqa: E712
    if not event:
        raise HTTPException(status_code=404, detail="אירוע לא נמצא")

    event_data = svc.get_event(event_id)
    event_date_formatted = event.date.strftime("%d/%m/%Y") if event.date else ""
    event_sequence_label = _event_sequence_label(event, db)
    event_sequence_color = event.day_sequence_color if event_sequence_label else None

    try:
        pdf_buffer = generate_delivery_sheet_pdf(
            event_data=event_data,
            event_date=event_date_formatted,
            event_sequence_label=event_sequence_label,
            event_sequence_color=event_sequence_color,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=f"שגיאה בהגדרת פונט: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"שגיאה ביצירת PDF: {str(e)}")

    safe_event_name = event.name.replace(" ", "_").replace("/", "-")
    filename = f"delivery_sheet_{safe_event_name}_{event_date_formatted.replace('/', '-')}.pdf"
    encoded_filename = quote(filename, safe="")

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"inline; filename=\"document.pdf\"; filename*=UTF-8''{encoded_filename}",
            "Content-Type": "application/pdf",
        },
    )


# ── Waiter PDF ────────────────────────────────────────────────────────

@router.get("/{event_id}/waiter-pdf")
def get_waiter_pdf(event_id: int, db: Session = Depends(get_db)):
    """
    יצירת PDF להדפסה עבור מלצרים
    
    מחזיר קובץ PDF עם הוראות הגשה לכל המנות באירוע.
    הקובץ כולל: שם האירוע, תאריך, רשימת מנות עם כלי הגשה והערות מיוחדות.
    """
    # שליפת האירוע
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="אירוע לא נמצא")
    
    # עיצוב תאריך
    event_date_formatted = event.date.strftime("%d/%m/%Y") if event.date else ""
    
    # איסוף נתוני המנות
    dishes_data = []
    calculated_serving_tools = EventCalculationService(db).serving_tools_for_document(event)
    
    for event_dish in event.dishes:
        dish = db.query(Dish).filter(Dish.id == event_dish.dish_id).first()
        if not dish:
            continue
        
        # איסוף כלי הגשה
        serving_dishes = []
        for sd in dish.serving_dishes:
            serving_name = sd.name or ""
            # אם יש tool_id, ננסה לקבל פרטים נוספים
            if sd.tool_id:
                tool = db.query(Tool).filter(Tool.id == sd.tool_id).first()
                if tool and tool.name:
                    serving_name = tool.name
                    # הוספת צבע/גודל אם קיים
                    if tool.color:
                        serving_name += f" ({tool.color})"
            
            serving_dishes.append({
                "name": serving_name,
                "quantity": sd.quantity
            })
        
        if event_dish.id in calculated_serving_tools:
            serving_dishes = calculated_serving_tools[event_dish.id]
        # מציאת הקטגוריה מ-menu_mappings
        category_name = "אחר"
        if dish.menu_mappings:
            # קח את הקטגוריה הראשונה
            first_mapping = dish.menu_mappings[0]
            if first_mapping.category and first_mapping.category.name_hebrew:
                category_name = first_mapping.category.name_hebrew
        
        # בניית נתוני המנה
        dish_data = {
            "name": dish.name,
            "category": category_name,
            "serving_dishes": serving_dishes,
            "serving_description": dish.serving_description,
            "description": dish.description,
            "notes": event_dish.notes or dish.waiter_notes,
            "waiter_notes": dish.waiter_notes
        }
        
        dishes_data.append(dish_data)
    
    # בדיקה שיש מנות
    _append_drinks_to_waiter_data(event, dishes_data, db)

    if not dishes_data:
        raise HTTPException(status_code=400, detail="אין מנות באירוע זה")
    
    # בניית רשימת בעלי האירוע
    owners = []
    for owner in event.owners:
        owners.append({
            "name": owner.name,
            "phone": owner.phone or ""
        })
    
    # חישובים אוטומטיים
    guest_count = event.guest_count or 1
    waiter_count = math.ceil(guest_count / 50) * 2
    table_count = math.ceil(guest_count / 8)
    event_sequence_label = _event_sequence_label(event, db)
    event_sequence_color = event.day_sequence_color if event_sequence_label else None

    # יצירת ה-PDF
    try:
        pdf_buffer = generate_waiter_pdf(
            event_name=event.name,
            event_date=event_date_formatted,
            hebrew_date=event.hebrew_date,
            guest_count=guest_count,
            location=event.address,
            dishes_data=dishes_data,
            blank_path=None,
            hall_name=None,
            city=event.city,
            owners=owners,
            event_notes=event.notes,
            is_disposable=not event.is_real_dishes,
            simple_mode=True,
            waiter_count=waiter_count,
            table_count=table_count,
            event_sequence_label=event_sequence_label,
            event_sequence_color=event_sequence_color,
            event_tool_set_items=_event_tool_set_items_for_pdf(event, db),
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=500, 
            detail=f"שגיאה בהגדרת פונט: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"שגיאה ביצירת PDF: {str(e)}"
        )
    
    # שם הקובץ
    safe_event_name = event.name.replace(" ", "_").replace("/", "-")
    filename = f"waiter_instructions_{safe_event_name}_{event_date_formatted.replace('/', '-')}.pdf"
    encoded_filename = quote(filename, safe='')
    
    # החזרת הקובץ
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"inline; filename=\"document.pdf\"; filename*=UTF-8''{encoded_filename}",
            "Content-Type": "application/pdf"
        }
    )


# ── Catering Owner PDF ────────────────────────────────────────────────

@router.get("/{event_id}/catering-pdf")
def get_catering_pdf(event_id: int, db: Session = Depends(get_db)):
    """
    יצירת PDF לבעל הקייטרינג - ללא רקע צבעוני
    
    מחזיר קובץ PDF נקי לבעלי הקייטרינג עם הוראות הגשה לכל המנות באירוע.
    """
    # שליפת האירוע
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="אירוע לא נמצא")
    
    # עיצוב תאריך
    event_date_formatted = event.date.strftime("%d/%m/%Y") if event.date else ""
    
    # איסוף נתוני המנות
    dishes_data = []
    calculated_serving_tools = EventCalculationService(db).serving_tools_for_document(event)
    
    for event_dish in event.dishes:
        dish = db.query(Dish).filter(Dish.id == event_dish.dish_id).first()
        if not dish:
            continue
        
        # איסוף כלי הגשה
        serving_dishes = []
        for sd in dish.serving_dishes:
            serving_name = sd.name or ""
            if sd.tool_id:
                tool = db.query(Tool).filter(Tool.id == sd.tool_id).first()
                if tool and tool.name:
                    serving_name = tool.name
                    if tool.color:
                        serving_name += f" ({tool.color})"
            
            serving_dishes.append({
                "name": serving_name,
                "quantity": sd.quantity
            })
        
        if event_dish.id in calculated_serving_tools:
            serving_dishes = calculated_serving_tools[event_dish.id]
        # מציאת הקטגוריה מ-menu_mappings
        category_name = "אחר"
        if dish.menu_mappings:
            first_mapping = dish.menu_mappings[0]
            if first_mapping.category and first_mapping.category.name_hebrew:
                category_name = first_mapping.category.name_hebrew
        
        dish_data = {
            "name": dish.name,
            "category": category_name,
            "serving_dishes": serving_dishes,
            "serving_description": dish.serving_description,
            "description": dish.description,
            "notes": event_dish.notes or dish.waiter_notes,
            "waiter_notes": dish.waiter_notes
        }
        
        dishes_data.append(dish_data)
    
    _append_drinks_to_waiter_data(event, dishes_data, db)

    if not dishes_data:
        raise HTTPException(status_code=400, detail="אין מנות באירוע זה")
    
    # בניית רשימת בעלי האירוע
    owners = []
    for owner in event.owners:
        owners.append({
            "name": owner.name,
            "phone": owner.phone or ""
        })
    
    # חישובים אוטומטיים
    guest_count_val = event.guest_count or 1
    waiter_count = math.ceil(guest_count_val / 50) * 2
    table_count = math.ceil(guest_count_val / 8)
    event_sequence_label = _event_sequence_label(event, db)
    event_sequence_color = event.day_sequence_color if event_sequence_label else None

    # יצירת ה-PDF - מצב פשוט ללא רקע צבעוני
    try:
        pdf_buffer = generate_waiter_pdf(
            event_name=event.name,
            event_date=event_date_formatted,
            hebrew_date=event.hebrew_date,
            guest_count=guest_count_val,
            location=event.address,
            dishes_data=dishes_data,
            blank_path=None,
            hall_name=None,
            city=event.city,
            owners=owners,
            event_notes=event.notes,
            is_disposable=not event.is_real_dishes,
            simple_mode=True,  # מצב פשוט - ללא רקע צבעוני
            waiter_count=waiter_count,
            table_count=table_count,
            event_sequence_label=event_sequence_label,
            event_sequence_color=event_sequence_color,
            event_tool_set_items=_event_tool_set_items_for_pdf(event, db),
            document_title="סיכום אירוע",
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=500, 
            detail=f"שגיאה בהגדרת פונט: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"שגיאה ביצירת PDF: {str(e)}"
        )
    
    # שם הקובץ
    safe_event_name = event.name.replace(" ", "_").replace("/", "-")
    filename = f"catering_summary_{safe_event_name}_{event_date_formatted.replace('/', '-')}.pdf"
    encoded_filename = quote(filename, safe='')
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"inline; filename=\"document.pdf\"; filename*=UTF-8''{encoded_filename}",
            "Content-Type": "application/pdf"
        }
    )


# ── Shopping / Quantities PDF ─────────────────────────────────────────

@router.get("/{event_id}/shopping-pdf")
def get_shopping_pdf(event_id: int, svc: EventService = Depends(_svc), db: Session = Depends(get_db)):
    """
    יצירת PDF רשימת קניות לאירוע

    הקובץ כולל:
    - חישוב כמויות כוללות לכל מוצר
    - רשימת חומרי גלם מחולקת לפי קטגוריות
    - רשימת כלי הגשה הנדרשים
    ללא רקע צבעוני, גופן 14.
    """
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="אירוע לא נמצא")

    event_date_formatted = event.date.strftime("%d/%m/%Y") if event.date else ""

    # שליפת רשימת הקניות וכלי ההגשה
    shopping_data = svc.get_shopping_list(event_id)
    equipment_data = svc.get_equipment_list(event_id)

    shopping_items = shopping_data.get('items', [])
    equipment_items = equipment_data.get('items', [])
    event_sequence_label = _event_sequence_label(event, db)
    event_sequence_color = event.day_sequence_color if event_sequence_label else None

    try:
        pdf_buffer = generate_shopping_pdf(
            event_name=event.name,
            event_date=event_date_formatted,
            guest_count=event.guest_count or 1,
            shopping_items=shopping_items,
            equipment_items=equipment_items,
            event_sequence_label=event_sequence_label,
            event_sequence_color=event_sequence_color,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=f"שגיאה בהגדרת פונט: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"שגיאה ביצירת PDF: {str(e)}")

    safe_event_name = event.name.replace(" ", "_").replace("/", "-")
    filename = f"shopping_list_{safe_event_name}_{event_date_formatted.replace('/', '-')}.pdf"
    encoded_filename = quote(filename, safe='')

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"inline; filename=\"document.pdf\"; filename*=UTF-8''{encoded_filename}",
            "Content-Type": "application/pdf"
        }
    )
