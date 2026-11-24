"""
Events router — all event CRUD + sub-resources (dishes, trays, lists).
"""

from datetime import datetime
from typing import Optional
from urllib.parse import quote

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
from app.models.event import DeliveryNoteTemplate, Event
from app.utils.pdf_generator import generate_shopping_pdf
from app.services.event_documents_service import EventDocumentsService

router = APIRouter(prefix="/events", tags=["events"])

def _branded_pdf_response(event_id: int, db: Session, render, prefix: str) -> StreamingResponse:
    """Branded event documents (caterer instructions 2026-11); data comes from the calculation service."""
    event = db.query(Event).filter(Event.id == event_id, Event.is_deleted == False).first()  # noqa: E712
    if not event:
        raise HTTPException(status_code=404, detail="אירוע לא נמצא")
    try:
        buffer = render(EventDocumentsService(db), event)
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=f"שגיאה בהגדרת פונט: {str(e)}")
    date_part = event.date.strftime("%d-%m-%Y") if event.date else ""
    filename = f"{prefix}_{event.name.replace(' ', '_').replace('/', '-')}_{date_part}.pdf"
    return StreamingResponse(buffer, media_type="application/pdf", headers={
        "Content-Disposition": f"inline; filename=\"document.pdf\"; filename*=UTF-8''{quote(filename, safe='')}",
        "Content-Type": "application/pdf",
    })


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


# ── CRUD ──────────────────────────────────────────────────────────────

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
def update_dish(event_id: int, dish_id: int, data: EventDishUpdate, event_dish_id: int | None = None, svc: EventService = Depends(_svc)):
    return svc.update_event_dish(event_id, dish_id, data, event_dish_id)


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
            resolved = service._resolve_serving_set(event, ed.dish_id, selected_id, ed) if kind == "serving" else service._resolve_set(ed.dish_id, kind, selected_id)
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


@router.get("/{event_id}/calculations/manual-tools")
def get_manual_tools(event_id: int, db: Session = Depends(get_db)):
    from app.models.calculation import EventManualToolRow
    _calculation_event(event_id, db)
    return [dict(tool_id=r.tool_id, name=r.name, quantity=r.quantity, is_reusable=r.is_reusable, notes=r.notes)
            for r in db.query(EventManualToolRow).filter_by(event_id=event_id).all()]


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
def get_delivery_sheet_pdf(event_id: int, db: Session = Depends(get_db)):
    """דף מוביל הלוך: פרטים, בדיקה לפני יציאה ובהגעה, חמשת שלבי ההובלה, אישור מסירה."""
    return _branded_pdf_response(event_id, db, lambda svc, e: svc.delivery_sheet_pdf(e), "delivery_out")


@router.get("/{event_id}/return-sheet/pdf")
def get_return_sheet_pdf(event_id: int, db: Session = Depends(get_db)):
    """דף מוביל חזור: מה אמור לחזור לקייטרינג + הוראות החזרה."""
    return _branded_pdf_response(event_id, db, lambda svc, e: svc.return_sheet_pdf(e), "delivery_return")

@router.get("/{event_id}/waiter-pdf")
def get_waiter_pdf(event_id: int, db: Session = Depends(get_db)):
    """הוראות הגשה ועריכה למלצר: אולם, צדדים, עריכה, מנות עם כלים/סכו"ם/תוספות, מוצרים נלווים."""
    return _branded_pdf_response(event_id, db, lambda svc, e: svc.serving_instructions_pdf(e), "serving_instructions")

@router.get("/{event_id}/catering-pdf")
def get_catering_pdf(event_id: int, db: Session = Depends(get_db)):
    """רשימת אריזה (מחליפה את "סיכום אירוע"): אוכל, נלווים, מפות, כלים, ספייר, כלי מלצר, תוספות."""
    return _branded_pdf_response(event_id, db, lambda svc, e: svc.packing_list_pdf(e), "packing_list")

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
