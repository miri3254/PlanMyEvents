"""Lookup values used by frontend dropdowns and settings."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.enums import (
    EventStatus,
    KosherType,
    ProductCategory,
    ToolCategory,
    ToolSubCategory,
    UnitType,
)
from app.db.session import get_db
from app.models.lookup import LOOKUP_CATEGORIES, LookupData
from app.models.menu import MenuTemplate

router = APIRouter(prefix="/lookup", tags=["lookup"])

EVENT_CATEGORY_DEFAULTS = [
    "בר מצווה",
    "אירוסים",
    "שבע ברכות",
    "אירוע מתוק",
    "שבת",
    "מגשי אירוח",
]

# Yield containers seen in the caterer's recipes (2026-11-24). Placeholder list until the
# caterer confirms sizes; editable in settings (lookup "dish_yield_units").
DISH_YIELD_UNIT_DEFAULTS = [
    "גסטרונום",
    "מגש שחור זהב קטן",
    "מגש שחור זהב גדול",
    "מגש קטן",
    "מגש גדול",
    "תבנית גדולה חד פעמית",
    "קערה 2.5 ליטר",
    "קערת מגשי אירוח",
    "כלי רוטב למגשי אירוח",
    "ליטר",
    'ק"ג',
    "יחידות",
    "חצאים",
    "קוביות",
    "מלבנים קטנים",
    "כוסות קטנות",
    "כוסות שוט",
    "רולדות",
    "שקיות",
    "מנות",
]


class LookupValuePayload(BaseModel):
    value: str = Field(min_length=1, max_length=255)


def _default_values(db: Session) -> dict[str, list[str]]:
    templates = db.query(MenuTemplate).filter(MenuTemplate.is_deleted == False).all()
    return {
        "menu_types": [template.menu_type for template in templates],
        "event_categories": EVENT_CATEGORY_DEFAULTS,
        "kosher_types": [item.value for item in KosherType],
        "measurement_units": [item.value for item in UnitType],
        "product_categories": [item.value for item in ProductCategory],
        "inventory_statuses": ["במלאי", "מלאי נמוך", "אין במלאי"],
        "event_statuses": [item.value for item in EventStatus],
        "tool_categories": [item.value for item in ToolCategory],
        "tool_sub_categories": [item.value for item in ToolSubCategory],
        "dish_yield_units": DISH_YIELD_UNIT_DEFAULTS,
    }


def _category_rows(db: Session, category: str) -> list[LookupData]:
    return (
        db.query(LookupData)
        .filter(LookupData.category == category)
        .order_by(LookupData.display_order, LookupData.id)
        .all()
    )


def _validate_editable_category(category: str) -> None:
    # Menu types are managed through the menus screen, not as free lookup data.
    if category not in LOOKUP_CATEGORIES or category == "menu_types":
        raise HTTPException(status_code=400, detail="Lookup category is not editable")


def _materialize_defaults(db: Session, category: str) -> list[LookupData]:
    rows = _category_rows(db, category)
    if rows:
        return rows

    for index, value in enumerate(_default_values(db).get(category, [])):
        db.add(
            LookupData(
                category=category,
                value=value,
                display_order=index,
                is_default=1,
            )
        )
    db.flush()
    return _category_rows(db, category)


@router.get("")
def get_lookup_data(db: Session = Depends(get_db)):
    """Keep the existing response shape; persisted edits override defaults."""
    defaults = _default_values(db)
    result: dict[str, list[str]] = {}
    for category, values in defaults.items():
        rows = _category_rows(db, category)
        result[category] = [row.value for row in rows] if rows else values
    return result


@router.post("/{category}", status_code=201)
def add_lookup_value(
    category: str,
    payload: LookupValuePayload,
    db: Session = Depends(get_db),
):
    _validate_editable_category(category)
    value = payload.value.strip()
    if not value:
        raise HTTPException(status_code=422, detail="Lookup value cannot be empty")

    rows = _materialize_defaults(db, category)
    if any(row.value == value for row in rows):
        raise HTTPException(status_code=409, detail="Lookup value already exists")

    db.add(
        LookupData(
            category=category,
            value=value,
            display_order=len(rows),
            is_default=0,
        )
    )
    db.commit()
    return {"message": "Lookup value added", "success": True}


@router.put("/{category}/{index}")
def update_lookup_value(
    category: str,
    index: int,
    payload: LookupValuePayload,
    db: Session = Depends(get_db),
):
    _validate_editable_category(category)
    rows = _materialize_defaults(db, category)
    if index < 0 or index >= len(rows):
        raise HTTPException(status_code=404, detail="Lookup value not found")

    value = payload.value.strip()
    if not value:
        raise HTTPException(status_code=422, detail="Lookup value cannot be empty")
    if any(row.value == value and position != index for position, row in enumerate(rows)):
        raise HTTPException(status_code=409, detail="Lookup value already exists")

    rows[index].value = value
    db.commit()
    return {"message": "Lookup value updated", "success": True}


@router.delete("/{category}/{index}")
def delete_lookup_value(category: str, index: int, db: Session = Depends(get_db)):
    _validate_editable_category(category)
    rows = _materialize_defaults(db, category)
    if index < 0 or index >= len(rows):
        raise HTTPException(status_code=404, detail="Lookup value not found")

    db.delete(rows[index])
    db.flush()
    for position, row in enumerate(_category_rows(db, category)):
        row.display_order = position
    db.commit()
    return {"message": "Lookup value deleted", "success": True}
