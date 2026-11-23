"""
Dishes router — CRUD for dish catalog + sub-entities.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.dish_service import DishService
from app.schemas.dish import (
    DishCreate, DishUpdate, DishActiveUpdate, DishListResponse, DishResponse,
    DishIngredientCreate, DishIngredientUpdate,
    ServingDishCreate, ServingDishUpdate,
)
from app.schemas.common import SuccessResponse
from app.schemas.calculation import (
    DishCalculationRuleCreate,
    DishCalculationRuleResponse,
    DishServingSetCreate,
    DishServingSetResponse,
)
from app.models.dish import Dish
from app.models.calculation import DishCalculationRule, DishServingSet, DishServingSetItem

router = APIRouter(prefix="/dishes", tags=["dishes"])


def _svc(db: Session = Depends(get_db)) -> DishService:
    return DishService(db)


@router.get('/calculation-presets')
def calculation_presets():
    from app.services.workbook_rules import PRESETS
    return list(PRESETS.values())


def _validate_workbook_rule(data):
    if data.rule_type != 'workbook':
        return
    from app.services.workbook_rules import PRESETS, calculate_preset
    params = data.params or {}
    if params.get('formula_key') not in PRESETS:
        raise HTTPException(422, 'יש לבחור נוסחה מתוך האקסל')
    try:
        calculate_preset(params['formula_key'], 1, 'regular', params)
    except (ValueError, TypeError, ZeroDivisionError):
        raise HTTPException(422, 'ערכי הנוסחה אינם תקינים')


# ── CRUD ──────────────────────────────────────────────────────────────

@router.get("", response_model=DishListResponse)
def get_dishes(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    search: Optional[str] = None,
    kosher_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    svc: DishService = Depends(_svc),
):
    items, total = svc.get_dishes(skip=skip, limit=limit, search=search, kosher_type=kosher_type, is_active=is_active)
    return {"items": items, "total": total, "skip": skip, "limit": limit}


@router.get("/{dish_id}", response_model=DishResponse)
def get_dish(dish_id: int, svc: DishService = Depends(_svc)):
    return svc.get_dish(dish_id)


@router.post("", status_code=201, response_model=DishResponse)
def create_dish(data: DishCreate, svc: DishService = Depends(_svc)):
    return svc.create_dish(data)


@router.put("/{dish_id}", response_model=DishResponse)
def update_dish(dish_id: int, data: DishUpdate, svc: DishService = Depends(_svc)):
    return svc.update_dish(dish_id, data)


@router.delete("/{dish_id}", response_model=SuccessResponse)
def delete_dish(dish_id: int, svc: DishService = Depends(_svc)):
    return svc.delete_dish(dish_id)


@router.patch("/{dish_id}/active", response_model=DishResponse)
def update_dish_active(dish_id: int, data: DishActiveUpdate, svc: DishService = Depends(_svc)):
    return svc.update_dish(dish_id, DishUpdate(is_active=data.is_active))


# ── INGREDIENTS ───────────────────────────────────────────────────────

@router.post("/{dish_id}/ingredients", response_model=DishResponse)
def add_ingredient(dish_id: int, data: DishIngredientCreate, svc: DishService = Depends(_svc)):
    return svc.add_ingredient(dish_id, data)


@router.put("/{dish_id}/ingredients/{ingredient_id}", response_model=DishResponse)
def update_ingredient(dish_id: int, ingredient_id: int, data: DishIngredientUpdate, svc: DishService = Depends(_svc)):
    return svc.update_ingredient(dish_id, ingredient_id, data)


@router.delete("/{dish_id}/ingredients/{ingredient_id}", response_model=SuccessResponse)
def remove_ingredient(dish_id: int, ingredient_id: int, svc: DishService = Depends(_svc)):
    return svc.remove_ingredient(dish_id, ingredient_id)


# ── SERVING DISHES ────────────────────────────────────────────────────

@router.post("/{dish_id}/serving-dishes", response_model=DishResponse)
def add_serving_dish(dish_id: int, data: ServingDishCreate, svc: DishService = Depends(_svc)):
    return svc.add_serving_dish(dish_id, data)


@router.put("/{dish_id}/serving-dishes/{serving_id}", response_model=DishResponse)
def update_serving_dish(dish_id: int, serving_id: int, data: ServingDishUpdate, svc: DishService = Depends(_svc)):
    return svc.update_serving_dish(dish_id, serving_id, data)


@router.delete("/{dish_id}/serving-dishes/{serving_id}", response_model=SuccessResponse)
def remove_serving_dish(dish_id: int, serving_id: int, svc: DishService = Depends(_svc)):
    return svc.remove_serving_dish(dish_id, serving_id)


# Backward-compatible aliases used by the Angular service.
@router.post("/{dish_id}/equipment", response_model=DishResponse)
def add_equipment(dish_id: int, data: ServingDishCreate, svc: DishService = Depends(_svc)):
    return svc.add_serving_dish(dish_id, data)


@router.put("/{dish_id}/equipment/{equipment_id}", response_model=DishResponse)
def update_equipment(
    dish_id: int,
    equipment_id: int,
    data: ServingDishUpdate,
    svc: DishService = Depends(_svc),
):
    return svc.update_serving_dish(dish_id, equipment_id, data)


@router.delete("/{dish_id}/equipment/{equipment_id}", response_model=SuccessResponse)
def remove_equipment(dish_id: int, equipment_id: int, svc: DishService = Depends(_svc)):
    return svc.remove_serving_dish(dish_id, equipment_id)


# Serving/packaging alternatives and special calculation rules

def _dish_or_404(dish_id: int, db: Session) -> Dish:
    dish = db.query(Dish).filter(Dish.id == dish_id, Dish.is_deleted == False).first()  # noqa: E712
    if not dish:
        raise HTTPException(status_code=404, detail="מנה לא נמצאה")
    return dish


@router.get("/{dish_id}/serving-sets", response_model=list[DishServingSetResponse])
def get_serving_sets(dish_id: int, db: Session = Depends(get_db)):
    _dish_or_404(dish_id, db)
    return db.query(DishServingSet).filter(DishServingSet.dish_id == dish_id).all()


@router.post("/{dish_id}/serving-sets", status_code=201, response_model=DishServingSetResponse)
def create_serving_set(dish_id: int, data: DishServingSetCreate, db: Session = Depends(get_db)):
    _dish_or_404(dish_id, db)
    if data.serving_mode and db.query(DishServingSet).filter(
        DishServingSet.dish_id == dish_id, DishServingSet.set_type == data.set_type,
        DishServingSet.dishware_type == data.dishware_type,
        DishServingSet.serving_mode == data.serving_mode, 
    ).first():
        raise HTTPException(422, "כבר קיימת אפשרות לסוג הכלים ולצורת ההגשה האלה; יש לערוך אותה")
    if data.serving_mode:
        if data.dishware_type not in ("disposable", "real"):
            raise HTTPException(422, "יש לבחור חד פעמי או אמיתי")
        if not data.items or any(not item.tool_id for item in data.items):
            raise HTTPException(422, "יש לקשר לפחות כלי אחד מהמלאי")
    from app.models.tool import Tool
    for item in data.items:
        if item.tool_id and not db.query(Tool).filter(Tool.id == item.tool_id, Tool.is_deleted == False).first():
            raise HTTPException(422, "כלי מקושר אינו קיים במלאי")
    if data.is_default:
        db.query(DishServingSet).filter(
            DishServingSet.dish_id == dish_id,
            DishServingSet.set_type == data.set_type,
            DishServingSet.dishware_type == data.dishware_type,
        ).update({"is_default": False})
    serving_set = DishServingSet(
        dish_id=dish_id,
        name=data.name,
        set_type=data.set_type,
        is_default=data.is_default,
        dishware_type=data.dishware_type,
        serving_mode=data.serving_mode,
        notes=data.notes,
    )
    serving_set.items = [DishServingSetItem(**item.model_dump()) for item in data.items]
    db.add(serving_set)
    db.commit()
    db.refresh(serving_set)
    return serving_set


@router.put("/{dish_id}/serving-sets/{set_id}", response_model=DishServingSetResponse)
def update_serving_set(dish_id: int, set_id: int, data: DishServingSetCreate, db: Session = Depends(get_db)):
    _dish_or_404(dish_id, db)
    serving_set = db.query(DishServingSet).filter(
        DishServingSet.id == set_id, DishServingSet.dish_id == dish_id
    ).first()
    if not serving_set:
        raise HTTPException(status_code=404, detail="סט כלי הגשה לא נמצא")
    if data.serving_mode and db.query(DishServingSet).filter(
        DishServingSet.dish_id == dish_id, DishServingSet.set_type == data.set_type,
        DishServingSet.dishware_type == data.dishware_type,
        DishServingSet.serving_mode == data.serving_mode, DishServingSet.id != set_id,
    ).first():
        raise HTTPException(422, "כבר קיימת אפשרות לסוג הכלים ולצורת ההגשה האלה; יש לערוך אותה")
    if data.serving_mode:
        if data.dishware_type not in ("disposable", "real"):
            raise HTTPException(422, "יש לבחור חד פעמי או אמיתי")
        if not data.items or any(not item.tool_id for item in data.items):
            raise HTTPException(422, "יש לקשר לפחות כלי אחד מהמלאי")
    from app.models.tool import Tool
    for item in data.items:
        if item.tool_id and not db.query(Tool).filter(Tool.id == item.tool_id, Tool.is_deleted == False).first():
            raise HTTPException(422, "כלי מקושר אינו קיים במלאי")
    if data.is_default:
        db.query(DishServingSet).filter(
            DishServingSet.dish_id == dish_id,
            DishServingSet.set_type == data.set_type,
            DishServingSet.dishware_type == data.dishware_type,
            DishServingSet.id != set_id,
        ).update({"is_default": False})
    for field in ["name", "set_type", "is_default", "dishware_type", "serving_mode", "notes"]:
        setattr(serving_set, field, getattr(data, field))
    serving_set.items.clear()
    serving_set.items.extend(DishServingSetItem(**item.model_dump()) for item in data.items)
    db.commit()
    db.refresh(serving_set)
    return serving_set


@router.delete("/{dish_id}/serving-sets/{set_id}", response_model=SuccessResponse)
def delete_serving_set(dish_id: int, set_id: int, db: Session = Depends(get_db)):
    serving_set = db.query(DishServingSet).filter(
        DishServingSet.id == set_id, DishServingSet.dish_id == dish_id
    ).first()
    if not serving_set:
        raise HTTPException(status_code=404, detail="סט כלי הגשה לא נמצא")
    db.delete(serving_set)
    db.commit()
    return {"success": True, "message": "סט כלי ההגשה נמחק"}


@router.get("/{dish_id}/calculation-rules", response_model=list[DishCalculationRuleResponse])
def get_calculation_rules(dish_id: int, db: Session = Depends(get_db)):
    _dish_or_404(dish_id, db)
    return db.query(DishCalculationRule).filter(DishCalculationRule.dish_id == dish_id).all()


@router.post("/{dish_id}/calculation-rules", status_code=201, response_model=DishCalculationRuleResponse)
def create_calculation_rule(dish_id: int, data: DishCalculationRuleCreate, db: Session = Depends(get_db)):
    _dish_or_404(dish_id, db)
    _validate_workbook_rule(data)
    rule = DishCalculationRule(dish_id=dish_id, **data.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.put("/{dish_id}/calculation-rules/{rule_id}", response_model=DishCalculationRuleResponse)
def update_calculation_rule(
    dish_id: int, rule_id: int, data: DishCalculationRuleCreate, db: Session = Depends(get_db)
):
    rule = db.query(DishCalculationRule).filter(
        DishCalculationRule.id == rule_id, DishCalculationRule.dish_id == dish_id
    ).first()
    if not rule:
        raise HTTPException(status_code=404, detail="חוק חישוב לא נמצא")
    _validate_workbook_rule(data)
    for key, value in data.model_dump().items():
        setattr(rule, key, value)
    db.commit()
    db.refresh(rule)
    return rule


@router.delete("/{dish_id}/calculation-rules/{rule_id}", response_model=SuccessResponse)
def delete_calculation_rule(dish_id: int, rule_id: int, db: Session = Depends(get_db)):
    rule = db.query(DishCalculationRule).filter(
        DishCalculationRule.id == rule_id, DishCalculationRule.dish_id == dish_id
    ).first()
    if not rule:
        raise HTTPException(status_code=404, detail="חוק חישוב לא נמצא")
    db.delete(rule)
    db.commit()
    return {"success": True, "message": "חוק החישוב נמחק"}
