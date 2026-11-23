"""
Unit Conversions router — CRUD + conversion calculation.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.services.unit_conversion_service import UnitConversionService
from app.schemas.unit_conversion import (
    UnitConversionCreate,
    UnitConversionUpdate,
    UnitConversionResponse,
    ConversionRequest,
    ConversionResponse,
)

router = APIRouter(prefix="/unit-conversions", tags=["unit-conversions"])


def _svc(db: Session = Depends(get_db)) -> UnitConversionService:
    return UnitConversionService(db)


@router.get("", response_model=dict)
def get_all_conversions(svc: UnitConversionService = Depends(_svc)):
    """Get all unit conversions (system and user-defined)."""
    conversions = svc.get_all()
    return {
        "items": [
            {
                "id": c.id,
                "fromUnit": c.from_unit.value if hasattr(c.from_unit, 'value') else c.from_unit,
                "toUnit": c.to_unit.value if hasattr(c.to_unit, 'value') else c.to_unit,
                "factor": c.factor,
                "isSystem": c.is_system,
                "description": c.description,
                "createdAt": c.created_at.isoformat() if c.created_at else None,
                "updatedAt": c.updated_at.isoformat() if c.updated_at else None,
            }
            for c in conversions
        ],
        "total": len(conversions),
    }


@router.get("/{conversion_id}")
def get_conversion(conversion_id: int, svc: UnitConversionService = Depends(_svc)):
    """Get a specific unit conversion."""
    c = svc.get_by_id(conversion_id)
    if not c:
        from app.utils.errors import AppException
        raise AppException(404, "המרה לא נמצאה")
    return {
        "id": c.id,
        "fromUnit": c.from_unit.value if hasattr(c.from_unit, 'value') else c.from_unit,
        "toUnit": c.to_unit.value if hasattr(c.to_unit, 'value') else c.to_unit,
        "factor": c.factor,
        "isSystem": c.is_system,
        "description": c.description,
        "createdAt": c.created_at.isoformat() if c.created_at else None,
        "updatedAt": c.updated_at.isoformat() if c.updated_at else None,
    }


@router.post("", status_code=201)
def create_conversion(data: UnitConversionCreate, svc: UnitConversionService = Depends(_svc)):
    """Create a new user-defined unit conversion."""
    c = svc.create(data)
    return {
        "id": c.id,
        "fromUnit": c.from_unit.value if hasattr(c.from_unit, 'value') else c.from_unit,
        "toUnit": c.to_unit.value if hasattr(c.to_unit, 'value') else c.to_unit,
        "factor": c.factor,
        "isSystem": c.is_system,
        "description": c.description,
        "createdAt": c.created_at.isoformat() if c.created_at else None,
        "updatedAt": c.updated_at.isoformat() if c.updated_at else None,
    }


@router.put("/{conversion_id}")
def update_conversion(
    conversion_id: int,
    data: UnitConversionUpdate,
    svc: UnitConversionService = Depends(_svc),
):
    """Update a user-defined unit conversion (system conversions cannot be modified)."""
    c = svc.update(conversion_id, data)
    return {
        "id": c.id,
        "fromUnit": c.from_unit.value if hasattr(c.from_unit, 'value') else c.from_unit,
        "toUnit": c.to_unit.value if hasattr(c.to_unit, 'value') else c.to_unit,
        "factor": c.factor,
        "isSystem": c.is_system,
        "description": c.description,
        "createdAt": c.created_at.isoformat() if c.created_at else None,
        "updatedAt": c.updated_at.isoformat() if c.updated_at else None,
    }


@router.delete("/{conversion_id}")
def delete_conversion(conversion_id: int, svc: UnitConversionService = Depends(_svc)):
    """Delete a user-defined unit conversion (system conversions cannot be deleted)."""
    svc.delete(conversion_id)
    return {"message": "המרה נמחקה בהצלחה"}


@router.post("/calculate")
def calculate_conversion(data: ConversionRequest, svc: UnitConversionService = Depends(_svc)):
    """Calculate a unit conversion."""
    converted_value, path = svc.convert(data.value, data.from_unit, data.to_unit)
    return {
        "originalValue": data.value,
        "originalUnit": data.from_unit,
        "convertedValue": round(converted_value, 6),
        "targetUnit": data.to_unit,
        "conversionPath": path,
    }


@router.post("/seed")
def seed_conversions(svc: UnitConversionService = Depends(_svc)):
    """Seed system conversions (admin endpoint for initialization)."""
    count = svc.seed_system_conversions()
    return {"message": f"נוספו {count} המרות", "count": count}
