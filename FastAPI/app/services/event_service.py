"""
Event service — aggregate root for all event operations.

All dish/tray/list/status operations on an event go through here.
"""

import math
from datetime import datetime, time

from sqlalchemy.orm import Session

from app.repositories.event_repo import EventRepository
from app.repositories.dish_repo import DishRepository
from app.repositories.menu_repo import MenuRepository
from app.repositories.audit_repo import AuditRepository
from app.models.event import (
    DeliveryNoteTemplate,
    Event,
    EventBox,
    EventDeliveryNote,
    EventOwner,
    EventDish,
    EventTraySelection,
)
from app.models.dish import Dish, DishIngredient
from app.models.product import Product
from app.models.tool import Tool
from app.models.menu import MenuTemplate
from app.models.calculation import EventCalculationSnapshot
from app.core.enums import EventStatus, AuditAction
from app.core.constants import MIN_GUESTS, ALLOWED_STATUS_TRANSITIONS
from app.schemas.event import (
    EventCreate, EventUpdate, EventStatusUpdate,
    EventDishCreate, EventDishUpdate, EventTrayCreate, EventTrayUpdate,
    EventResponse, EventDishResponse, EventTrayResponse,
    EventOwnerResponse,
    ShoppingListItem, ShoppingListResponse,
    EquipmentListItem, EquipmentListResponse,
)
from app.utils.errors import AppException
from app.utils.app_logging import logger
from app.services.event_calculation_service import EventCalculationService


class EventService:
    DAY_SEQUENCE_COLORS = {
        1: "orange",
        2: "green",
        3: "purple",
        4: "sky",
        5: "red",
    }

    def __init__(self, db: Session):
        self.db = db
        self.repo = EventRepository(db)
        self.dish_repo = DishRepository(db)
        self.menu_repo = MenuRepository(db)
        self.audit = AuditRepository(db)
        self.calculations = EventCalculationService(db)
        # User decisions 2026-11-23: rule breaches are warnings, not blocks.
        self._op_warnings: dict[int, list[str]] = {}
        self._approved_changed: set[int] = set()
        self._template_cache: dict[str, object] = {}

    # ── helpers ───────────────────────────────────────────────────────

    def _get_or_404(self, event_id: int) -> Event:
        event = self.repo.get_with_relations(event_id)
        if not event:
            raise AppException(404, "אירוע לא נמצא")
        return event

    def _get_day_events(self, event_date: datetime) -> list[Event]:
        day_start = datetime.combine(event_date.date(), time.min)
        day_end = datetime.combine(event_date.date(), time.max)
        return (
            self.db.query(Event)
            .filter(Event.is_deleted == False)  # noqa: E712
            .filter(Event.date >= day_start, Event.date <= day_end)
            .all()
        )

    def _event_time_sort_key(self, event: Event) -> tuple[int, int]:
        raw_time = (event.event_time or "").strip()
        if raw_time:
            parts = raw_time.split(":")
            try:
                hour = int(parts[0])
                minute = int(parts[1]) if len(parts) > 1 else 0
                if 0 <= hour <= 23 and 0 <= minute <= 59:
                    return (hour * 60 + minute, event.id or 0)
            except (TypeError, ValueError):
                pass

        if event.date:
            minutes = event.date.hour * 60 + event.date.minute
            if minutes:
                return (minutes, event.id or 0)

        return (24 * 60, event.id or 0)

    def _recalculate_day_sequences(self, event_date: datetime | None) -> None:
        if not event_date:
            return

        events = sorted(self._get_day_events(event_date), key=self._event_time_sort_key)
        for sequence_number, day_event in enumerate(events, start=1):
            day_event.day_sequence_number = sequence_number
            day_event.day_sequence_color = self.DAY_SEQUENCE_COLORS.get(sequence_number)
        self.db.flush()

    def _replace_delivery_notes(self, event_id: int, template_ids: list[int] | None) -> None:
        if template_ids is None:
            return

        normalized_ids = list(dict.fromkeys([int(note_id) for note_id in template_ids if note_id]))
        if normalized_ids:
            found_ids = {
                row.id
                for row in self.db.query(DeliveryNoteTemplate)
                .filter(DeliveryNoteTemplate.id.in_(normalized_ids))
                .all()
            }
            missing = [note_id for note_id in normalized_ids if note_id not in found_ids]
            if missing:
                raise AppException(400, f"Delivery note templates not found: {missing}")

        self.db.query(EventDeliveryNote).filter(EventDeliveryNote.event_id == event_id).delete()
        for template_id in normalized_ids:
            self.db.add(EventDeliveryNote(event_id=event_id, template_id=template_id))

    def _replace_boxes(self, event_id: int, boxes_data) -> None:
        if boxes_data is None:
            return

        self.db.query(EventBox).filter(EventBox.event_id == event_id).delete()
        for box in boxes_data:
            payload = box.model_dump() if hasattr(box, "model_dump") else dict(box)
            box_type = (payload.get("box_type") or "").strip()
            if not box_type:
                continue
            self.db.add(
                EventBox(
                    event_id=event_id,
                    box_type=box_type,
                    quantity=payload.get("quantity") or 1,
                    notes=payload.get("notes"),
                )
            )

    def complete_past_approved_events(self) -> int:
        today_start = datetime.combine(datetime.now().date(), time.min)
        events = self.repo.get_approved_before(today_start)
        if not events:
            return 0

        for event in events:
            event.status = EventStatus.COMPLETED
            self._deduct_inventory(event)
            self.calculations.release_reservations(event.id)
            self.audit.log(
                "event",
                event.id,
                AuditAction.STATUS_CHANGED.value,
                {
                    "from": EventStatus.APPROVED.value,
                    "to": EventStatus.COMPLETED.value,
                    "automatic": True,
                },
            )

        self.db.commit()
        logger.info(f"Auto-completed {len(events)} past approved events")
        return len(events)

    def _lookup_by_ids(self, model, ids) -> dict:
        """Load rows for the given ids in one query (avoids per-row N+1 lookups)."""
        unique_ids = {i for i in ids if i}
        if not unique_ids:
            return {}
        return {row.id: row for row in self.db.query(model).filter(model.id.in_(unique_ids)).all()}

    def _response_warnings(self, event: Event) -> list[str]:
        warnings = list(self._op_warnings.pop(event.id, []))
        if self._is_status(event, EventStatus.DRAFT) or self._is_status(event, EventStatus.APPROVED):
            menu_type = str(event.menu_type)
            message = self._min_guests_warning(event.guest_count, menu_type, self._template_for(menu_type))
            if message:
                warnings.append(message)
        return warnings

    def _build_response(self, event: Event) -> dict:
        from app.models.menu import MenuCategory, MenuSubMeal

        dish_by_id = self._lookup_by_ids(
            Dish,
            [ed.dish_id for ed in event.dishes] + [t.dish_id for t in event.tray_selections],
        )
        category_by_id = self._lookup_by_ids(
            MenuCategory,
            [ed.category_id for ed in event.dishes] + [t.category_id for t in event.tray_selections],
        )
        sub_meal_by_id = self._lookup_by_ids(MenuSubMeal, [ed.sub_meal_id for ed in event.dishes])

        dishes = []
        for ed in event.dishes:
            dish = dish_by_id.get(ed.dish_id)
            cat = category_by_id.get(ed.category_id) if ed.category_id else None
            sm = sub_meal_by_id.get(ed.sub_meal_id) if ed.sub_meal_id else None
            dishes.append({
                "id": ed.id,
                "event_id": ed.event_id,
                "dish_id": ed.dish_id,
                "sub_meal_id": ed.sub_meal_id,
                "category_id": ed.category_id,
                "quantity": ed.quantity,
                "is_upgrade": ed.is_upgrade,
                "is_gift": ed.is_gift,
                "serving_mode": ed.serving_mode,
                "extra_charge": ed.extra_charge,
                "notes": ed.notes,
                "is_draft": ed.is_draft,
                "snapshot_base_price": ed.snapshot_base_price,
                "snapshot_client_price": ed.snapshot_client_price,
                "created_at": ed.created_at,
                "dish_name": dish.name if dish else None,
                "dish_kosher_type": dish.kosher_type.value if dish and hasattr(dish.kosher_type, "value") else None,
                "category_name_hebrew": cat.name_hebrew if cat else None,
                "sub_meal_name": sm.name if sm else None,
                "current_base_price": dish.base_price if dish else None,
            })

        owners = [
            {
                "id": o.id, "event_id": o.event_id, "name": o.name,
                "phone": o.phone, "email": o.email, "order": o.order,
                "created_at": o.created_at,
            }
            for o in event.owners
        ]

        trays = []
        for t in event.tray_selections:
            dish = dish_by_id.get(t.dish_id)
            cat = category_by_id.get(t.category_id) if t.category_id else None
            trays.append({
                "id": t.id, "event_id": t.event_id, "dish_id": t.dish_id,
                "category_id": t.category_id, "tray_count": t.tray_count,
                "price_per_tray": t.price_per_tray, "notes": t.notes,
                "created_at": t.created_at,
                "dish_name": dish.name if dish else None,
                "category_name_hebrew": cat.name_hebrew if cat else None,
            })

        delivery_notes = []
        for link in event.delivery_notes:
            if link.template:
                delivery_notes.append({
                    "id": link.id,
                    "event_id": link.event_id,
                    "template_id": link.template_id,
                    "note": link.template.note,
                })

        boxes = [
            {
                "id": box.id,
                "event_id": box.event_id,
                "box_type": box.box_type,
                "quantity": box.quantity,
                "notes": box.notes,
                "created_at": box.created_at,
            }
            for box in event.boxes
        ]
        total_boxes = sum((box.get("quantity") or 0) for box in boxes)
        calc_settings = self.calculations.get_settings(event.id, create=False)
        has_calc_snapshot = (
            self.db.query(EventCalculationSnapshot)
            .filter(EventCalculationSnapshot.event_id == event.id)
            .first()
            is not None
        )

        return {
            "id": event.id,
            "name": event.name,
            "event_category": getattr(event, "event_category", None),
            "menu_type": str(event.menu_type),
            "status": event.status.value if hasattr(event.status, "value") else str(event.status),
            "date": event.date,
            "event_time": event.event_time,
            "hebrew_date": event.hebrew_date,
            "day_sequence_number": getattr(event, "day_sequence_number", 1) or 1,
            "day_sequence_color": getattr(event, "day_sequence_color", None),
            "address": event.address,
            "city": event.city,
            "guest_count": event.guest_count,
            "is_real_dishes": getattr(event, 'is_real_dishes', False),
            "is_morning_split": event.is_morning_split,
            "split_extra_charge": event.split_extra_charge,
            "base_price_per_guest": event.base_price_per_guest,
            "real_dishes_extra_per_guest": getattr(event, 'real_dishes_extra_per_guest', 0.0) or 0.0,
            "calculated_price": getattr(event, 'calculated_price', 0.0) or 0.0,
            "final_price": getattr(event, 'final_price', None),
            "discount_percent": getattr(event, 'discount_percent', 0.0) or 0.0,
            "discount_amount": getattr(event, 'discount_amount', 0.0) or 0.0,
            "total_price": event.total_price,
            "notes": event.notes,
            "venue_name": getattr(event, "venue_name", None),
            "floor": getattr(event, "floor", None),
            "has_elevator": getattr(event, "has_elevator", False),
            "access_code": getattr(event, "access_code", None),
            "onsite_contact_name": getattr(event, "onsite_contact_name", None),
            "onsite_contact_phone": getattr(event, "onsite_contact_phone", None),
            "hall_owner_name": getattr(event, "hall_owner_name", None),
            "hall_owner_phone": getattr(event, "hall_owner_phone", None),
            "has_nearby_parking": getattr(event, "has_nearby_parking", False),
            "has_back_entrance": getattr(event, "has_back_entrance", False),
            "requires_carts": getattr(event, "requires_carts", False),
            "access_notes": getattr(event, "access_notes", None),
            "dishware_type": getattr(event, "dishware_type", None) or ("כלים אמיתיים" if getattr(event, "is_real_dishes", False) else "חד פעמי"),
            "delivery_contents_notes": getattr(event, "delivery_contents_notes", None),
            "last_minute_items": getattr(event, "last_minute_items", None),
            "equipment_dropoff_location": getattr(event, "equipment_dropoff_location", None),
            "check_refrigerator": getattr(event, "check_refrigerator", False),
            "check_freezer": getattr(event, "check_freezer", False),
            "check_hot_plate": getattr(event, "check_hot_plate", False),
            "connect_gas": getattr(event, "connect_gas", False),
            "put_in_refrigerator": getattr(event, "put_in_refrigerator", False),
            "put_in_freezer": getattr(event, "put_in_freezer", False),
            "put_on_hot_plate": getattr(event, "put_on_hot_plate", False),
            "count_boxes": getattr(event, "count_boxes", False),
            "check_drinks": getattr(event, "check_drinks", False),
            "check_rolls": getattr(event, "check_rolls", False),
            "delivery_special_notes": getattr(event, "delivery_special_notes", None),
            "selected_delivery_note_template_ids": [note["template_id"] for note in delivery_notes],
            "delivery_notes": delivery_notes,
            "boxes": boxes,
            "total_boxes": total_boxes,
            "created_at": event.created_at,
            "updated_at": event.updated_at,
            # חישובים אוטומטיים
            "waiter_count": self.calculations.waiter_count(event),
            "table_count": self.calculations.table_count(event),
            "dishes": dishes,
            "owners": owners,
            "tray_selections": trays,
            "calculation_settings": {
                "id": calc_settings.id,
                "event_id": calc_settings.event_id,
                "drinks_enabled": calc_settings.drinks_enabled,
                "drink_types": calc_settings.drink_types,
                "orange_flavored_mode": calc_settings.orange_flavored_mode,
                "rolls_enabled": calc_settings.rolls_enabled,
                "roll_splits": calc_settings.roll_splits,
                "table_shape": calc_settings.table_shape,
                "tablecloth_tool_id": calc_settings.tablecloth_tool_id,
                "use_rectangular_for_square": calc_settings.use_rectangular_for_square,
                "table_overrides": calc_settings.table_overrides,
                "event_tool_set_items": calc_settings.event_tool_set_items,
                "credit_card_enabled": calc_settings.credit_card_enabled,
                "credit_card_amount": calc_settings.credit_card_amount,
                "credit_card_installments": calc_settings.credit_card_installments,
                "credit_card_rate": calc_settings.credit_card_rate,
                "credit_card_vat_multiplier": calc_settings.credit_card_vat_multiplier,
            } if calc_settings else None,
            "has_calculation_snapshot": has_calc_snapshot,
            "warnings": self._response_warnings(event),
        }

    # ── CRUD ──────────────────────────────────────────────────────────

    def get_events(self, **kwargs) -> tuple[list[dict], int]:
        self.complete_past_approved_events()
        events, total = self.repo.get_list(**kwargs)
        return [self._build_response(e) for e in events], total

    def get_event(self, event_id: int) -> dict:
        self.complete_past_approved_events()
        event = self._get_or_404(event_id)
        return self._build_response(event)

    def get_events_in_range(self, start: datetime, end: datetime) -> list[dict]:
        self.complete_past_approved_events()
        events = self.repo.get_in_range(start, end)
        return [self._build_response(e) for e in events]

    def create_event(self, data: EventCreate) -> dict:
        # Validate min guests
        menu_type_val = data.menu_type
        template = self.menu_repo.get_template_by_type(menu_type_val)
        # Resolve base price from template
        base_price = template.base_price_per_guest if template else None
        real_dishes_extra = getattr(template, 'real_dishes_extra_per_guest', 0.0) if template else 0.0

        event_data = data.model_dump(exclude={"owners", "selected_delivery_note_template_ids", "boxes"})
        if not event_data.get("dishware_type"):
            event_data["dishware_type"] = "כלים אמיתיים" if event_data.get("is_real_dishes") else "חד פעמי"

        db_event = Event(**event_data)
        db_event.base_price_per_guest = base_price
        db_event.real_dishes_extra_per_guest = real_dishes_extra or 0.0
        db_event.calculated_price = 0.0
        db_event.final_price = None
        db_event.discount_percent = 0.0
        db_event.discount_amount = 0.0
        db_event.total_price = 0.0
        db_event.status = EventStatus.DRAFT

        self.repo.create(db_event)
        self.db.flush()
        self._recalculate_day_sequences(db_event.date)

        # Calculate initial price
        self._recalc_total(db_event)

        # Owners
        if data.owners:
            self.repo.replace_owners(db_event.id, data.owners)
        self._replace_delivery_notes(db_event.id, data.selected_delivery_note_template_ids)
        self._replace_boxes(db_event.id, data.boxes)

        self.db.commit()
        self.db.refresh(db_event)

        self.audit.log("event", db_event.id, AuditAction.CREATED.value)
        self.db.commit()

        logger.info(f"אירוע נוצר: {db_event.name} (ID={db_event.id})")
        return self._build_response(self.repo.get_with_relations(db_event.id))

    def update_event(self, event_id: int, data: EventUpdate) -> dict:
        event = self._get_or_404(event_id)
        update_data = data.model_dump(exclude_unset=True, exclude={"owners", "selected_delivery_note_template_ids", "boxes"})
        old_date = event.date

        logger.info(f"🔧 Update event {event_id}: {update_data}")
        logger.info(f"📋 Owners in request: {data.owners}")

        # The UI sends the whole form, so only real changes count.
        frozen_fields = ("guest_count", "is_real_dishes", "is_morning_split", "menu_type")
        changed_frozen = [
            f for f in frozen_fields
            if f in update_data and update_data[f] != (str(event.menu_type) if f == "menu_type" else getattr(event, f, None))
        ]
        if changed_frozen:
            self._ensure_editable(event)
        menu_changed = "menu_type" in changed_frozen
        old_guests = event.guest_count

        self.repo.update(event, update_data)

        if "guest_count" in changed_frozen:
            self._rescale_dish_units(event, old_guests)

        if menu_changed:
            self._replace_dishes_after_menu_change(event)
        if menu_changed and not self._is_status(event, EventStatus.APPROVED):
            # Approved events keep their approved prices (user decision Q046).
            template = self.menu_repo.get_template_by_type(str(event.menu_type))
            event.base_price_per_guest = template.base_price_per_guest if template else None
            event.real_dishes_extra_per_guest = (getattr(template, "real_dishes_extra_per_guest", 0.0) or 0.0) if template else 0.0

        sequence_dates = []
        if "date" in update_data and update_data["date"].date() != old_date.date():
            sequence_dates.append(old_date)
        if "date" in update_data or "event_time" in update_data:
            sequence_dates.append(event.date)

        if data.owners is not None:
            self.repo.replace_owners(event_id, data.owners)
        if data.selected_delivery_note_template_ids is not None:
            self._replace_delivery_notes(event_id, data.selected_delivery_note_template_ids)
        if data.boxes is not None:
            self._replace_boxes(event_id, data.boxes)

        # Recalculate price if relevant fields changed
        if menu_changed or any(field in update_data for field in ['guest_count', 'is_real_dishes', 'is_morning_split', 'final_price']):
            self._recalc_total(event)

        for sequence_date in sequence_dates:
            self._recalculate_day_sequences(sequence_date)

        self.audit.log("event", event_id, AuditAction.UPDATED.value)
        self.db.commit()
        return self._build_response(self.repo.get_with_relations(event_id))

    def update_final_price(self, event_id: int, final_price: float) -> dict:
        """Update only the final price of an event and recalculate discount."""
        event = self._get_or_404(event_id)
        
        event.final_price = final_price
        self._recalc_total(event)
        
        self.audit.log("event", event_id, AuditAction.UPDATED.value, {"final_price": final_price})
        self.db.commit()
        
        logger.info(f"מחיר סופי לאירוע {event_id} עודכן: {final_price}₪")
        return self._build_response(self.repo.get_with_relations(event_id))

    def change_status(self, event_id: int, new_status: str) -> dict:
        event = self._get_or_404(event_id)
        current = event.status.value if hasattr(event.status, "value") else str(event.status)

        allowed = ALLOWED_STATUS_TRANSITIONS.get(current, [])
        if new_status not in allowed:
            raise AppException(
                400,
                f"לא ניתן לשנות סטטוס מ-'{current}' ל-'{new_status}'. "
                f"מעברים מותרים: {', '.join(allowed) if allowed else 'אין'}",
            )

        event.status = new_status

        # Price snapshot on APPROVED. Approval also confirms the dish selection:
        # the UI never calls /dishes/finalize, so wizard dishes stay is_draft until here.
        if new_status == EventStatus.APPROVED.value:
            for ed in event.dishes:
                ed.is_draft = False
            self._snapshot_prices(event)
            self.calculations.snapshot_event(event)

        # APPROVED → DRAFT reopens the event for editing: drop the frozen calculation,
        # dish price snapshots and tool reservations; they are rebuilt on re-approval.
        if new_status == EventStatus.DRAFT.value and current == EventStatus.APPROVED.value:
            self._clear_approval_snapshot(event)
        
        # Inventory deduction on COMPLETED (only if was APPROVED)
        if new_status == EventStatus.COMPLETED.value and current == EventStatus.APPROVED.value:
            self._deduct_inventory(event)
            self.calculations.release_reservations(event.id)
        if new_status == EventStatus.CANCELLED.value:
            self.calculations.release_reservations(event.id)

        self.audit.log("event", event_id, AuditAction.STATUS_CHANGED.value, {"from": current, "to": new_status})
        self.db.commit()

        logger.info(f"סטטוס אירוע {event_id} שונה: {current} → {new_status}")
        return self._build_response(self.repo.get_with_relations(event_id))

    # User decision 2026-11-23: recipe (DishIngredient) and Dish.base_price describe ONE
    # dish unit that serves Dish.serving_size guests. EventDish.quantity = number of units
    # (wizard: ceil(guests / serving_size)). Never multiply it by guest_count again.
    @staticmethod
    def _dish_units(ed: EventDish) -> float:
        return ed.quantity or 0

    @staticmethod
    def _units_for_guests(dish: Dish | None, guests: int | None) -> int:
        serving = (dish.serving_size if dish else None) or 1
        return math.ceil(max(1, guests or 0) / serving)

    def _rescale_dish_units(self, event: Event, old_guests: int | None) -> None:
        """Guest count changed: every dish quantity follows it (user decision Q011)."""
        for ed in event.dishes:
            ed.quantity = self._units_for_guests(ed.dish, event.guest_count)

    @staticmethod
    def _min_guests_warning(guest_count: int, menu_type: str, template) -> str | None:
        # User decisions 2026-11-23: the menu's own min_guests wins (constants list only
        # when no MenuTemplate row); below the minimum is a warning, not a block (Q015).
        min_g = template.min_guests if template and template.min_guests else MIN_GUESTS.get(menu_type, 1)
        if (guest_count or 0) < min_g:
            return f"מתחת למינימום: לתפריט '{menu_type}' נדרשים {min_g} סועדים, הוזנו {guest_count}."
        return None

    def _template_for(self, menu_type: str):
        if menu_type not in self._template_cache:
            self._template_cache[menu_type] = self.menu_repo.get_template_by_type(menu_type)
        return self._template_cache[menu_type]

    @staticmethod
    def _is_status(event: Event, status: EventStatus) -> bool:
        value = event.status.value if hasattr(event.status, "value") else str(event.status)
        return value == status.value

    def _replace_dishes_after_menu_change(self, event: Event) -> None:
        """Q029: changing the menu removes dishes chosen from the previous menu (UI warns first)."""
        removed = len(event.dishes)
        if removed:
            self.db.query(EventDish).filter(EventDish.event_id == event.id).delete()
            self.db.flush()
            self.db.expire(event, ["dishes"])
            self._op_warnings.setdefault(event.id, []).append(f"התפריט הוחלף: הוסרו {removed} מנות מהתפריט הקודם.")

    def _clear_approval_snapshot(self, event: Event) -> None:
        self.db.query(EventCalculationSnapshot).filter(EventCalculationSnapshot.event_id == event.id).delete()
        for ed in event.dishes:
            ed.snapshot_base_price = None
            ed.snapshot_client_price = None
            # Back to draft so the wizard's replace (draft_only) can drop de-selected dishes.
            ed.is_draft = True
        self.calculations.release_reservations(event.id)

    def _ensure_editable(self, event: Event) -> None:
        """Q045: approved events may be edited with a warning; quantities and reservations
        are recalculated, approved prices stay. Completed events are closed (stock deducted)."""
        if self._is_status(event, EventStatus.COMPLETED):
            raise AppException(400, "לא ניתן לשנות אירוע שהסתיים (המלאי כבר הורד).")
        if self._is_status(event, EventStatus.APPROVED) and event.id not in self._approved_changed:
            self._approved_changed.add(event.id)
            self._op_warnings.setdefault(event.id, []).append(
                "האירוע מאושר: הכמויות והשריונים עודכנו, המחירים נשארו כפי שאושרו."
            )

    def _refresh_approved_snapshot(self, event: Event) -> None:
        """Re-freeze quantities/reservations after an approved event changed; keep prices."""
        self.db.flush()
        self.db.expire(event, ["dishes", "tray_selections"])
        for ed in event.dishes:
            if ed.snapshot_base_price is None and ed.dish:  # dish added after approval
                ed.snapshot_base_price = ed.dish.base_price
                ed.snapshot_client_price = ed.dish.client_price
        self.calculations.snapshot_event(event)

    def _snapshot_prices(self, event: Event):
        """Freeze dish/tray prices at finalization time."""
        for ed in event.dishes:
            dish = self.db.query(Dish).filter(Dish.id == ed.dish_id).first()
            if dish:
                ed.snapshot_base_price = dish.base_price
                ed.snapshot_client_price = dish.client_price
        for ts in event.tray_selections:
            from app.models.menu import MenuCategory
            cat = self.db.query(MenuCategory).filter(MenuCategory.id == ts.category_id).first()
            if cat and cat.tray_price:
                ts.price_per_tray = cat.tray_price
        self.db.flush()

    def _deduct_inventory(self, event: Event):
        """
        Deduct ingredients from product inventory when event is completed.
        Uses unit conversion service to handle different units.
        """
        from app.services.unit_conversion_service import UnitConversionService
        conversion_svc = UnitConversionService(self.db)
        
        # Aggregate all ingredients needed
        deductions: dict[int, float] = {}  # product_id → amount to deduct (in product's unit)
        replaced_product_ids = self.calculations.replaced_product_ids(event)
        
        for ed in event.dishes:
            dish = self.db.query(Dish).filter(Dish.id == ed.dish_id).first()
            if not dish:
                continue
            
            multiplier = self._dish_units(ed)
            
            for ing in dish.ingredients:
                if not ing.product_id:
                    continue
                # A calculation rule replaced this ingredient (e.g. with a prepared product);
                # its quantity already comes from calc product_requirements below.
                if ing.product_id in replaced_product_ids:
                    continue

                product = self.db.query(Product).filter(Product.id == ing.product_id).first()
                if not product:
                    continue
                
                # Calculate required quantity
                required_quantity = ing.quantity * multiplier
                
                # Convert to product's unit if needed
                try:
                    deduction = conversion_svc.calculate_inventory_deduction(
                        ingredient_quantity=required_quantity,
                        ingredient_unit=ing.unit,
                        product_unit=product.unit,
                        package_quantity=product.package_quantity or 1,
                    )
                    
                    if ing.product_id not in deductions:
                        deductions[ing.product_id] = 0.0
                    deductions[ing.product_id] += deduction
                    
                except Exception as e:
                    logger.warning(f"Failed to calculate inventory deduction for product {ing.product_id}: {e}")
                    continue

        calc_summary = self.calculations.summarize(event)
        for req in calc_summary.product_requirements:
            if req.product_id:
                deductions[req.product_id] = deductions.get(req.product_id, 0.0) + req.quantity
        
        # Apply deductions
        for product_id, amount in deductions.items():
            product = self.db.query(Product).filter(Product.id == product_id).first()
            if product:
                old_stock = product.quantity_in_stock
                # Q055: stock may go negative (shows what is missing); warn, don't floor at 0.
                product.quantity_in_stock = (product.quantity_in_stock or 0) - amount
                if product.quantity_in_stock < 0:
                    logger.warning(f"Negative stock after event {event.id}: {product.name} = {product.quantity_in_stock}")
                logger.info(
                    f"Inventory deduction for event {event.id}: "
                    f"Product {product_id} ({product.name}): {old_stock} → {product.quantity_in_stock} "
                    f"(deducted {amount} {product.unit.value if hasattr(product.unit, 'value') else product.unit})"
                )
        
        self.db.flush()

    def delete_event(self, event_id: int) -> dict:
        event = self._get_or_404(event_id)
        event_date = event.date
        self.repo.soft_delete(event)
        self._recalculate_day_sequences(event_date)
        self.audit.log("event", event_id, AuditAction.DELETED.value)
        self.db.commit()
        return {"success": True, "message": "האירוע נמחק בהצלחה"}

    # ── dishes ────────────────────────────────────────────────────────

    def add_dish_to_event(self, event_id: int, data: EventDishCreate) -> dict:
        event = self._get_or_404(event_id)
        self._ensure_editable(event)
        dish = self.db.query(Dish).filter(Dish.id == data.dish_id).first()
        if not dish:
            raise AppException(404, "מנה לא נמצאה")

        ed = EventDish(
            event_id=event_id,
            dish_id=data.dish_id,
            sub_meal_id=data.sub_meal_id,
            category_id=data.category_id,
            quantity=data.quantity,
            is_upgrade=data.is_upgrade,
            is_gift=data.is_gift,
            serving_mode=data.serving_mode,
            extra_charge=data.extra_charge,
            notes=data.notes,
        )
        self.repo.add_dish(ed)
        self.db.flush()
        self.db.refresh(event)
        self._recalc_total(event)
        self.db.commit()
        return self.get_event(event_id)

    def update_event_dish(self, event_id: int, dish_id: int, data: EventDishUpdate, event_dish_id: int | None = None) -> dict:
        ed = (self.db.query(EventDish).filter_by(id=event_dish_id, event_id=event_id, dish_id=dish_id).first()
              if event_dish_id is not None else self.repo.get_event_dish(event_id, dish_id))
        if not ed:
            raise AppException(404, "המנה לא נמצאה באירוע")
        self._ensure_editable(self._get_or_404(event_id))
        for k, v in data.model_dump(exclude_unset=True).items():
            if hasattr(ed, k):
                setattr(ed, k, v)
        if 'serving_mode' in data.model_fields_set:
            from app.models.calculation import EventDishServingSelection
            self.db.query(EventDishServingSelection).filter(
                EventDishServingSelection.event_id == event_id,
                EventDishServingSelection.dish_id == dish_id,
                EventDishServingSelection.set_type == 'serving').delete()
        event = self._get_or_404(event_id)
        self._recalc_total(event)
        self.db.commit()
        return self.get_event(event_id)

    def remove_dish_from_event(self, event_id: int, dish_id: int) -> dict:
        ed = self.repo.get_event_dish(event_id, dish_id)
        if not ed:
            raise AppException(404, "המנה לא נמצאה באירוע")
        self._ensure_editable(self._get_or_404(event_id))
        self.repo.remove_dish(ed)
        event = self._get_or_404(event_id)
        self._recalc_total(event)
        self.db.commit()
        return {"success": True, "message": "המנה הוסרה מהאירוע"}

    def bulk_save_dishes(self, event_id: int, dishes_data: list[EventDishCreate], is_draft: bool = True, replace: bool = False) -> dict:
        event = self._get_or_404(event_id)
        self._ensure_editable(event)
        if replace:
            self.repo.bulk_delete_dishes(event_id, draft_only=is_draft)

        saved = []
        for dd in dishes_data:
            dish = self.db.query(Dish).filter(Dish.id == dd.dish_id).first()
            if not dish:
                continue
            existing = self.repo.get_event_dish(event_id, dd.dish_id)
            if existing:
                existing.quantity = dd.quantity
                existing.notes = dd.notes
                existing.is_draft = is_draft
                existing.sub_meal_id = dd.sub_meal_id
                existing.category_id = dd.category_id
                existing.is_upgrade = dd.is_upgrade
                existing.is_gift = dd.is_gift
                existing.serving_mode = dd.serving_mode
                existing.extra_charge = dd.extra_charge
                saved.append(existing)
            else:
                ed = EventDish(
                    event_id=event_id, dish_id=dd.dish_id,
                    sub_meal_id=dd.sub_meal_id, category_id=dd.category_id,
                    quantity=dd.quantity, is_upgrade=dd.is_upgrade,
                    is_gift=dd.is_gift,
                    serving_mode=dd.serving_mode,
                    extra_charge=dd.extra_charge, notes=dd.notes,
                    is_draft=is_draft,
                )
                self.repo.add_dish(ed)
                saved.append(ed)

        self._recalc_total(event)
        self.db.commit()
        return {"success": True, "message": f"נשמרו {len(saved)} מנות", "count": len(saved)}

    def finalize_drafts(self, event_id: int) -> dict:
        event = self._get_or_404(event_id)
        drafts = self.repo.get_event_dishes(event_id, draft_only=True)
        for d in drafts:
            d.is_draft = False
        self._recalc_total(event)
        self.db.commit()
        return {"success": True, "message": f"אושרו {len(drafts)} מנות"}

    # ── trays ─────────────────────────────────────────────────────────

    def add_tray(self, event_id: int, data: EventTrayCreate) -> dict:
        event = self._get_or_404(event_id)
        self._ensure_editable(event)
        dish = self.db.query(Dish).filter(Dish.id == data.dish_id).first()
        if not dish:
            raise AppException(404, "מנה לא נמצאה")

        # Get tray price from category
        from app.models.menu import MenuCategory
        price = None
        if data.category_id:
            cat = self.db.query(MenuCategory).filter(MenuCategory.id == data.category_id).first()
            price = cat.tray_price if cat else None

        tray = EventTraySelection(
            event_id=event_id, dish_id=data.dish_id,
            category_id=data.category_id, tray_count=data.tray_count,
            price_per_tray=price, notes=data.notes,
        )
        self.repo.add_tray(tray)
        self._recalc_total(event)
        self.db.commit()
        return self.get_event(event_id)

    def update_tray(self, event_id: int, tray_id: int, data: EventTrayUpdate) -> dict:
        tray = self.repo.get_tray(tray_id)
        if not tray or tray.event_id != event_id:
            raise AppException(404, "מגש לא נמצא באירוע")
        self._ensure_editable(self._get_or_404(event_id))
        for k, v in data.model_dump(exclude_unset=True).items():
            if hasattr(tray, k):
                setattr(tray, k, v)
        event = self._get_or_404(event_id)
        self._recalc_total(event)
        self.db.commit()
        return self.get_event(event_id)

    def remove_tray(self, event_id: int, tray_id: int) -> dict:
        tray = self.repo.get_tray(tray_id)
        if not tray or tray.event_id != event_id:
            raise AppException(404, "מגש לא נמצא באירוע")
        self._ensure_editable(self._get_or_404(event_id))
        self.repo.remove_tray(tray)
        event = self._get_or_404(event_id)
        self._recalc_total(event)
        self.db.commit()
        return {"success": True, "message": "המגש הוסר"}

    # ── morning split ────────────────────────────────────────────────

    def restore_stock(self, event_id: int) -> dict:
        """Restore inventory previously deducted for a completed event."""
        from app.services.unit_conversion_service import UnitConversionService

        event = self._get_or_404(event_id)
        conversion_svc = UnitConversionService(self.db)
        restorations: dict[int, float] = {}
        replaced_product_ids = self.calculations.replaced_product_ids(event)

        for ed in event.dishes:
            dish = self.db.query(Dish).filter(Dish.id == ed.dish_id).first()
            if not dish:
                continue

            multiplier = self._dish_units(ed)
            for ing in dish.ingredients:
                if not ing.product_id:
                    continue
                if ing.product_id in replaced_product_ids:
                    continue

                product = self.db.query(Product).filter(Product.id == ing.product_id).first()
                if not product:
                    continue

                try:
                    amount = conversion_svc.calculate_inventory_deduction(
                        ingredient_quantity=ing.quantity * multiplier,
                        ingredient_unit=ing.unit,
                        product_unit=product.unit,
                        package_quantity=product.package_quantity or 1,
                    )
                except Exception as e:
                    logger.warning(f"Failed to calculate inventory restoration for product {ing.product_id}: {e}")
                    continue

                restorations[ing.product_id] = restorations.get(ing.product_id, 0.0) + amount

        calc_summary = self.calculations.summarize(event)
        for req in calc_summary.product_requirements:
            if req.product_id:
                restorations[req.product_id] = restorations.get(req.product_id, 0.0) + req.quantity

        for product_id, amount in restorations.items():
            product = self.db.query(Product).filter(Product.id == product_id).first()
            if product:
                product.quantity_in_stock = (product.quantity_in_stock or 0.0) + amount

        self.audit.log("event", event_id, AuditAction.UPDATED.value, {"restored_stock": restorations})
        self.db.commit()
        return {"success": True, "message": "Stock restored successfully"}

    def toggle_morning_split(self, event_id: int, split: bool) -> dict:
        event = self._get_or_404(event_id)
        if bool(event.is_morning_split) != bool(split):
            self._ensure_editable(event)
        event.is_morning_split = split
        if split:
            # Find split charge from Shabbat morning sub-meal
            from app.models.menu import MenuSubMeal
            sm = (
                self.db.query(MenuSubMeal)
                .filter(MenuSubMeal.is_splittable == True)  # noqa: E712
                .first()
            )
            event.split_extra_charge = sm.split_extra_charge if sm else 0
        else:
            event.split_extra_charge = None

        self._recalc_total(event)
        self.db.commit()
        return self.get_event(event_id)

    # ── price calculation ─────────────────────────────────────────────

    def _recalc_total(self, event: Event):
        """Recalculate all pricing fields for an event."""
        total = 0.0

        # Base price per guest
        if event.base_price_per_guest:
            total += event.base_price_per_guest * event.guest_count

        # Upgrade charges from dishes (e.g., salmon, steak)
        for ed in event.dishes:
            if not ed.is_gift and ed.is_upgrade and ed.extra_charge:
                total += ed.extra_charge * event.guest_count

        # Real dishes extra charge (תוספת כלים אמיתיים)
        is_real_dishes = getattr(event, 'is_real_dishes', False)
        real_dishes_extra = getattr(event, 'real_dishes_extra_per_guest', 0.0) or 0.0
        if is_real_dishes and real_dishes_extra:
            total += real_dishes_extra * event.guest_count

        # Tray costs
        for ts in event.tray_selections:
            if ts.price_per_tray:
                total += ts.price_per_tray * ts.tray_count

        # Morning split charge
        if event.is_morning_split and event.split_extra_charge:
            total += event.split_extra_charge * event.guest_count

        # Credit-card clearing is a client charge. It is calculated once on the
        # explicit credit amount, or on the event base total when "all price" is selected.
        calculation_settings = self.calculations.get_settings(event.id, create=False)
        if calculation_settings and calculation_settings.credit_card_enabled:
            credit_base = calculation_settings.credit_card_amount
            if credit_base is None:
                credit_base = total
            from app.services.workbook_rules import clearing_fee
            total += clearing_fee(credit_base, calculation_settings)

        # Update calculated price
        event.calculated_price = total
        event.total_price = total  # legacy field

        # Calculate discount if final_price is set
        final_price = getattr(event, 'final_price', None)
        if final_price is not None and total > 0:
            discount_amount = total - final_price
            discount_percent = (discount_amount / total) * 100 if total > 0 else 0.0
            event.discount_amount = max(0.0, discount_amount)  # No negative discount
            event.discount_percent = max(0.0, discount_percent)
        else:
            event.discount_amount = 0.0
            event.discount_percent = 0.0

        if event.id in self._approved_changed:
            self._refresh_approved_snapshot(event)

    # ── shopping list ─────────────────────────────────────────────────

    def get_shopping_list(self, event_id: int) -> dict:
        """
        חישוב רשימת קניות לאירוע.

        1. סוכם את כל הכמויות הנדרשות לפי מוצר
        2. ממיר ליחידות של המוצר (למשל כפיות → ליטר)
        3. מחסיר מהמלאי הקיים
        4. מחשב כמה חבילות צריך לקנות
        """
        from app.services.unit_conversion_service import UnitConversionService
        from app.utils.app_logging import logger

        event = self._get_or_404(event_id)
        conv_svc = UnitConversionService(self.db)

        # שלב 1: אגירת כמויות גולמיות לפי מוצר
        # key = product_id or name
        # value = { product, raw_quantities: [(ing_qty * multiplier, ing_unit)], ... }
        raw_items: dict[str, dict] = {}
        replaced_product_ids = self.calculations.replaced_product_ids(event)

        for ed in event.dishes:
            dish = self.db.query(Dish).filter(Dish.id == ed.dish_id).first()
            if not dish:
                continue
            multiplier = self._dish_units(ed)
            for ing in dish.ingredients:
                if ing.product_id and ing.product_id in replaced_product_ids:
                    continue
                key = ing.name or f"product_{ing.product_id}"
                if key not in raw_items:
                    prod = None
                    if ing.product_id:
                        prod = self.db.query(Product).filter(Product.id == ing.product_id).first()
                    raw_items[key] = {
                        "product_id": ing.product_id,
                        "name": ing.name or key,
                        "product": prod,
                        "quantities": [],  # [(total_qty, unit_enum)]
                    }
                ing_unit = ing.unit if hasattr(ing.unit, "value") else ing.unit
                raw_items[key]["quantities"].append(
                    (ing.quantity * multiplier, ing_unit)
                )

        # שלב 2: לכל מוצר — המרה ליחידת המוצר, חישוב מלאי וחבילות
        items: list[ShoppingListItem] = []
        total_price = 0.0

        for key, data in raw_items.items():
            prod = data["product"]
            product_id = data["product_id"]
            name = data["name"]

            # יחידת היעד = יחידת המוצר (אם קיים), אחרת יחידת המרכיב
            if prod:
                target_unit = prod.unit  # UnitType enum
                target_unit_str = target_unit.value if hasattr(target_unit, "value") else str(target_unit)
                cat = prod.category.value if hasattr(prod.category, "value") else str(prod.category)
                pkg_qty = prod.package_quantity if prod.package_quantity and prod.package_quantity > 0 else None
                stock = prod.quantity_in_stock or 0.0
                price_per_unit = prod.price_per_unit or 0.0
            else:
                # אין מוצר מקושר — נשתמש ביחידת המרכיב הראשון
                first_unit = data["quantities"][0][1]
                target_unit = first_unit
                target_unit_str = first_unit.value if hasattr(first_unit, "value") else str(first_unit)
                cat = None
                pkg_qty = None
                stock = 0.0
                price_per_unit = 0.0

            # סיכום הכמויות — המרה ליחידת היעד
            total_qty = 0.0
            for qty, unit in data["quantities"]:
                if unit == target_unit:
                    total_qty += qty
                else:
                    try:
                        converted, _ = conv_svc.convert(qty, unit, target_unit)
                        total_qty += converted
                    except Exception as e:
                        # אם ההמרה נכשלת, נוסיף את הכמות כמות שהיא
                        logger.warning(
                            f"Shopping list: failed to convert {qty} {unit} → {target_unit} for '{name}': {e}"
                        )
                        total_qty += qty

            # חישוב כמות לקניה (חיסור מלאי)
            need_to_buy = max(0.0, total_qty - stock)

            # חישוב חבילות לקניה
            if pkg_qty and pkg_qty > 0 and need_to_buy > 0:
                packages = math.ceil(need_to_buy / pkg_qty)
            elif need_to_buy > 0:
                packages = math.ceil(need_to_buy)  # אם אין גודל אריזה
            else:
                packages = 0

            # מחיר משוער — מבוסס על כמות לקניה
            est_price = price_per_unit * need_to_buy
            total_price += est_price

            items.append(ShoppingListItem(
                product_id=product_id,
                name=name,
                quantity=round(total_qty, 4),
                unit=target_unit_str,
                category=cat,
                estimated_price=round(est_price, 2),
                package_quantity=pkg_qty,
                quantity_in_stock=round(stock, 4),
                need_to_buy_quantity=round(need_to_buy, 4),
                packages_to_buy=packages,
            ))

        calc_summary = self.calculations.summarize(event)
        for req in calc_summary.product_requirements:
            items.append(ShoppingListItem(
                product_id=req.product_id,
                name=req.name,
                quantity=req.quantity,
                unit=req.unit,
                category=req.category,
                estimated_price=req.estimated_price,
                package_quantity=req.package_quantity,
                quantity_in_stock=req.available_in_stock,
                need_to_buy_quantity=req.need_to_buy_quantity,
                packages_to_buy=req.packages_to_buy,
                source_type=req.source_type,
                formula_label=req.formula_label,
                raw_quantity=req.raw_quantity,
            ))
            total_price += req.estimated_price

        items = self._merge_shopping_items(items)

        return ShoppingListResponse(
            event_id=event_id,
            event_name=event.name,
            items=items,
            total_estimated_price=round(total_price, 2),
        ).model_dump()

    # ── serving dishes list ───────────────────────────────────────────

    def _merge_shopping_items(self, items: list[ShoppingListItem]) -> list[ShoppingListItem]:
        """Merge regular ingredients and calculated requirements for the same product."""
        merged: dict[tuple, ShoppingListItem] = {}
        for item in items:
            key = (item.product_id or 0, item.name.strip().lower(), item.unit)
            if key not in merged:
                merged[key] = item.model_copy(deep=True)
                continue
            current = merged[key]
            current.quantity = round(current.quantity + item.quantity, 4)
            current.raw_quantity = round(
                (current.raw_quantity if current.raw_quantity is not None else current.quantity - item.quantity)
                + (item.raw_quantity if item.raw_quantity is not None else item.quantity),
                4,
            )
            current.need_to_buy_quantity = max(0, round(current.quantity - current.quantity_in_stock, 4))
            if current.package_quantity and current.package_quantity > 0:
                current.packages_to_buy = math.ceil(current.need_to_buy_quantity / current.package_quantity)
            elif current.need_to_buy_quantity > 0:
                current.packages_to_buy = math.ceil(current.need_to_buy_quantity)
            current.estimated_price = round(current.estimated_price + item.estimated_price, 2)
            sources = [part for part in [current.source_type, item.source_type] if part]
            current.source_type = ",".join(dict.fromkeys(sources)) or "dish_ingredient"
            formulas = [part for part in [current.formula_label, item.formula_label] if part]
            current.formula_label = " + ".join(dict.fromkeys(formulas)) or None
        return list(merged.values())

    def get_equipment_list(self, event_id: int) -> dict:
        """Get calculated serving, packaging, tablecloth and manual tool requirements."""
        event = self._get_or_404(event_id)
        summary = self.calculations.summarize(event)
        items = [
            EquipmentListItem(
                tool_id=req.tool_id,
                name=req.name,
                quantity=req.quantity,
                category=req.category or "כלי הגשה",
                available_in_stock=req.available_in_stock,
                need_to_buy=req.need_to_buy_quantity,
                source_type=req.source_type,
                formula_label=req.formula_label,
                raw_quantity=req.raw_quantity,
                is_reusable=req.is_reusable,
                reserved_quantity=req.reserved_quantity,
                available_after_reservations=req.available_after_reservations,
                shortage=req.shortage,
            )
            for req in summary.tool_requirements
        ]
        return EquipmentListResponse(
            event_id=event_id,
            event_name=event.name,
            items=items,
        ).model_dump()

