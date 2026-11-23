"""
Event repository — data access for Event aggregate.
"""

from typing import Optional, List
from datetime import datetime

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_

from app.repositories.base_repo import BaseRepository
from app.models.event import Event, EventOwner, EventDish, EventTraySelection, EventDeliveryNote


class EventRepository(BaseRepository[Event]):
    def __init__(self, db: Session):
        super().__init__(Event, db)

    # ── queries ───────────────────────────────────────────────────────

    def get_with_relations(self, event_id: int) -> Optional[Event]:
        return (
            self._active()
            .options(
                joinedload(Event.owners),
                joinedload(Event.dishes),
                joinedload(Event.tray_selections),
                joinedload(Event.delivery_notes).joinedload(EventDeliveryNote.template),
                joinedload(Event.boxes),
            )
            .filter(Event.id == event_id)
            .first()
        )

    def get_list(
        self,
        status: Optional[str] = None,
        menu_type: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[List[Event], int]:
        q = self._active()
        if status:
            q = q.filter(Event.status == status)
        if menu_type:
            q = q.filter(Event.menu_type == menu_type)
        if from_date:
            q = q.filter(Event.date >= from_date)
        if to_date:
            q = q.filter(Event.date <= to_date)
        if search:
            q = q.filter(Event.name.ilike(f"%{search}%"))

        total = q.count()
        events = q.order_by(Event.date.desc()).offset(skip).limit(limit).all()
        return events, total

    def get_in_range(self, start: datetime, end: datetime) -> List[Event]:
        return (
            self._active()
            .filter(and_(Event.date >= start, Event.date <= end))
            .order_by(Event.date)
            .all()
        )

    def get_approved_before(self, cutoff: datetime) -> List[Event]:
        return (
            self._active()
            .options(
                joinedload(Event.dishes),
                joinedload(Event.tray_selections),
            )
            .filter(Event.status == "מאושר", Event.date < cutoff)
            .all()
        )

    # ── owners ────────────────────────────────────────────────────────

    def replace_owners(self, event_id: int, owners_data: list) -> List[EventOwner]:
        self.db.query(EventOwner).filter(EventOwner.event_id == event_id).delete()
        new_owners = []
        for i, od in enumerate(owners_data):
            owner = EventOwner(
                event_id=event_id,
                name=od.name,
                phone=od.phone,
                email=od.email,
                order=od.order if od.order is not None else i,
            )
            self.db.add(owner)
            new_owners.append(owner)
        self.db.flush()
        return new_owners

    # ── dishes ────────────────────────────────────────────────────────

    def add_dish(self, event_dish: EventDish) -> EventDish:
        self.db.add(event_dish)
        self.db.flush()
        return event_dish

    def get_event_dish(self, event_id: int, dish_id: int) -> Optional[EventDish]:
        return (
            self.db.query(EventDish)
            .filter(EventDish.event_id == event_id, EventDish.dish_id == dish_id)
            .first()
        )

    def get_event_dishes(self, event_id: int, draft_only: bool = False) -> List[EventDish]:
        q = self.db.query(EventDish).filter(EventDish.event_id == event_id)
        if draft_only:
            q = q.filter(EventDish.is_draft == True)  # noqa: E712
        return q.all()

    def remove_dish(self, event_dish: EventDish) -> None:
        self.db.delete(event_dish)
        self.db.flush()

    def bulk_delete_dishes(self, event_id: int, draft_only: bool = False) -> int:
        q = self.db.query(EventDish).filter(EventDish.event_id == event_id)
        if draft_only:
            q = q.filter(EventDish.is_draft == True)  # noqa: E712
        count = q.delete()
        self.db.flush()
        return count

    # ── trays ─────────────────────────────────────────────────────────

    def add_tray(self, tray: EventTraySelection) -> EventTraySelection:
        self.db.add(tray)
        self.db.flush()
        return tray

    def get_tray(self, tray_id: int) -> Optional[EventTraySelection]:
        return self.db.query(EventTraySelection).filter(EventTraySelection.id == tray_id).first()

    def get_event_trays(self, event_id: int) -> List[EventTraySelection]:
        return (
            self.db.query(EventTraySelection)
            .filter(EventTraySelection.event_id == event_id)
            .all()
        )

    def remove_tray(self, tray: EventTraySelection) -> None:
        self.db.delete(tray)
        self.db.flush()
