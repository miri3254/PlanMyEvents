"""
Unit Conversion Service — handles unit conversion logic.

Provides:
  - CRUD operations for unit conversions
  - Conversion calculation between compatible units
  - Base unit normalization (e.g., kg→gram, liter→ml)
"""

from collections import deque
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.unit_conversion import UnitConversion
from app.core.enums import UnitType, UnitCategory, UNIT_CATEGORY_MAP
from app.schemas.unit_conversion import (
    UnitConversionCreate, UnitConversionUpdate, UnitConversionResponse,
    ConversionResponse,
)
from app.utils.errors import AppException
from app.utils.app_logging import logger


# Base units for each category - all conversions go through these
BASE_UNITS = {
    UnitCategory.WEIGHT: UnitType.GRAM,
    UnitCategory.VOLUME: UnitType.ML,
    UnitCategory.COUNT: UnitType.UNIT,
}

# System conversions - fixed and cannot be changed
SYSTEM_CONVERSIONS = [
    # Weight conversions (to GRAM)
    (UnitType.KG, UnitType.GRAM, 1000.0, "1 קילוגרם = 1000 גרם"),
    (UnitType.GRAM, UnitType.KG, 0.001, "1 גרם = 0.001 קילוגרם"),
    (UnitType.MG, UnitType.GRAM, 0.001, "1 מיליגרם = 0.001 גרם"),
    (UnitType.GRAM, UnitType.MG, 1000.0, "1 גרם = 1000 מיליגרם"),
    (UnitType.KG, UnitType.MG, 1000000.0, "1 קילוגרם = 1,000,000 מיליגרם"),
    (UnitType.MG, UnitType.KG, 0.000001, "1 מיליגרם = 0.000001 קילוגרם"),
    
    # Volume conversions (to ML)
    (UnitType.LITER, UnitType.ML, 1000.0, "1 ליטר = 1000 מיליליטר"),
    (UnitType.ML, UnitType.LITER, 0.001, "1 מיליליטר = 0.001 ליטר"),
    (UnitType.CUP, UnitType.ML, 240.0, "1 כוס = 240 מיליליטר"),
    (UnitType.ML, UnitType.CUP, 1.0 / 240.0, "1 מיליליטר = 1/240 כוס"),
]

# Default user conversions - can be changed by user
DEFAULT_USER_CONVERSIONS = [
    # These defaults bridge weight and volume only as editable estimates.
    # Ingredients have different densities, so the caterer may refine them.
    (UnitType.CUP, UnitType.GRAM, 240.0, "1 כוס = 240 גרם (הערכה כללית, ניתנת לשינוי)"),
    (UnitType.GRAM, UnitType.CUP, 1.0 / 240.0, "1 גרם = 1/240 כוס (הערכה כללית, ניתנת לשינוי)"),
    (UnitType.TABLESPOON, UnitType.GRAM, 15.0, "1 כף = 15 גרם (ניתן לשינוי)"),
    (UnitType.GRAM, UnitType.TABLESPOON, 1.0 / 15.0, "1 גרם = 1/15 כף (ניתן לשינוי)"),
    (UnitType.TEASPOON, UnitType.GRAM, 5.0, "1 כפית = 5 גרם (ניתן לשינוי)"),
    (UnitType.GRAM, UnitType.TEASPOON, 1.0 / 5.0, "1 גרם = 1/5 כפית (ניתן לשינוי)"),
    (UnitType.PINCH, UnitType.GRAM, 0.5, "1 קורט = 0.5 גרם (ניתן לשינוי)"),
    (UnitType.GRAM, UnitType.PINCH, 2.0, "1 גרם = 2 קורט (ניתן לשינוי)"),
    (UnitType.TABLESPOON, UnitType.ML, 15.0, "1 כף = 15 מ\"ל (ניתן לשינוי)"),
    (UnitType.ML, UnitType.TABLESPOON, 1.0 / 15.0, "1 מ\"ל = 1/15 כף (ניתן לשינוי)"),
    (UnitType.TEASPOON, UnitType.ML, 5.0, "1 כפית = 5 מ\"ל (ניתן לשינוי)"),
    (UnitType.ML, UnitType.TEASPOON, 1.0 / 5.0, "1 מ\"ל = 1/5 כפית (ניתן לשינוי)"),
    (UnitType.PINCH, UnitType.ML, 0.5, "1 קורט = 0.5 מ\"ל (ניתן לשינוי)"),
    (UnitType.ML, UnitType.PINCH, 2.0, "1 מ\"ל = 2 קורט (ניתן לשינוי)"),
]


class UnitConversionService:
    def __init__(self, db: Session):
        self.db = db

    # ── CRUD Operations ───────────────────────────────────────────────

    def get_all(self) -> List[UnitConversion]:
        """Get all unit conversions."""
        return (
            self.db.query(UnitConversion)
            .filter(UnitConversion.is_deleted == False)
            .order_by(UnitConversion.is_system.desc(), UnitConversion.from_unit)
            .all()
        )

    def get_by_id(self, conversion_id: int) -> Optional[UnitConversion]:
        """Get a specific unit conversion."""
        return (
            self.db.query(UnitConversion)
            .filter(
                UnitConversion.id == conversion_id,
                UnitConversion.is_deleted == False
            )
            .first()
        )

    def get_conversion(self, from_unit: UnitType, to_unit: UnitType) -> Optional[UnitConversion]:
        """Get conversion between two specific units."""
        return (
            self.db.query(UnitConversion)
            .filter(
                UnitConversion.from_unit == from_unit,
                UnitConversion.to_unit == to_unit,
                UnitConversion.is_deleted == False
            )
            .first()
        )

    def create(self, data: UnitConversionCreate) -> UnitConversion:
        """Create a new user-defined unit conversion."""
        # Parse units
        from_unit = self._parse_unit(data.from_unit)
        to_unit = self._parse_unit(data.to_unit)
        
        if from_unit is None or to_unit is None:
            raise AppException(400, "יחידת מידה לא חוקית")
        
        # Check if conversion already exists
        existing = self.get_conversion(from_unit, to_unit)
        if existing:
            raise AppException(400, "המרה זו כבר קיימת")
        
        # Allow an explicit, editable weight/volume estimate, but never mix a
        # count unit with weight or volume.
        from_cat = UNIT_CATEGORY_MAP.get(from_unit)
        to_cat = UNIT_CATEGORY_MAP.get(to_unit)
        if from_cat != to_cat and {from_cat, to_cat} != {UnitCategory.WEIGHT, UnitCategory.VOLUME}:
            raise AppException(400, "ניתן להמיר בין יחידות מאותו סוג, או בין משקל לנפח כהערכה ניתנת לעריכה")
        
        conversion = UnitConversion(
            from_unit=from_unit,
            to_unit=to_unit,
            factor=data.factor,
            is_system=False,
            description=data.description,
        )
        self.db.add(conversion)
        self.db.commit()
        self.db.refresh(conversion)
        
        logger.info(f"Created unit conversion: {from_unit.value} → {to_unit.value} = {data.factor}")
        return conversion

    def update(self, conversion_id: int, data: UnitConversionUpdate) -> UnitConversion:
        """Update a unit conversion (only non-system conversions)."""
        conversion = self.get_by_id(conversion_id)
        if not conversion:
            raise AppException(404, "המרה לא נמצאה")
        
        if conversion.is_system:
            raise AppException(400, "לא ניתן לערוך המרות מערכתיות")
        
        if data.factor is not None:
            conversion.factor = data.factor
        if data.description is not None:
            conversion.description = data.description
        
        self.db.commit()
        self.db.refresh(conversion)
        
        logger.info(f"Updated unit conversion {conversion_id}")
        return conversion

    def delete(self, conversion_id: int) -> bool:
        """Soft-delete a unit conversion (only non-system conversions)."""
        conversion = self.get_by_id(conversion_id)
        if not conversion:
            raise AppException(404, "המרה לא נמצאה")
        
        if conversion.is_system:
            raise AppException(400, "לא ניתן למחוק המרות מערכתיות")
        
        conversion.is_deleted = True
        self.db.commit()
        
        logger.info(f"Deleted unit conversion {conversion_id}")
        return True

    # ── Conversion Logic ──────────────────────────────────────────────

    def convert(
        self,
        value: float,
        from_unit: UnitType | str,
        to_unit: UnitType | str,
    ) -> Tuple[float, List[str]]:
        """
        Convert a value from one unit to another.
        
        Returns:
            Tuple of (converted_value, conversion_path)
            
        Raises:
            AppException if conversion is not possible
        """
        # Parse units if strings
        parsed_from: Optional[UnitType] = None
        parsed_to: Optional[UnitType] = None
        
        if isinstance(from_unit, str):
            parsed_from = self._parse_unit(from_unit)
        else:
            parsed_from = from_unit
            
        if isinstance(to_unit, str):
            parsed_to = self._parse_unit(to_unit)
        else:
            parsed_to = to_unit
        
        if parsed_from is None or parsed_to is None:
            raise AppException(400, "יחידת מידה לא חוקית")
        
        # Same unit - no conversion needed
        if parsed_from == parsed_to:
            return value, [parsed_from.value]
        
        # Check same category
        from_cat = UNIT_CATEGORY_MAP.get(parsed_from)
        to_cat = UNIT_CATEGORY_MAP.get(parsed_to)
        
        if from_cat is None or to_cat is None:
            raise AppException(400, f"יחידת מידה לא מוגדרת בקטגוריה: {parsed_from.value} או {parsed_to.value}")
        
        if from_cat != to_cat:
            return self._convert_via_path(value, parsed_from, parsed_to)
        
        # Try direct conversion first
        direct = self.get_conversion(parsed_from, parsed_to)
        if direct:
            return value * float(direct.factor), [parsed_from.value, parsed_to.value]
        
        # Try through base unit
        base_unit = BASE_UNITS.get(from_cat)
        if base_unit:
            # from_unit → base → to_unit
            to_base = self.get_conversion(parsed_from, base_unit)
            from_base = self.get_conversion(base_unit, parsed_to)
            
            if to_base and from_base:
                base_value = value * float(to_base.factor)
                final_value = base_value * float(from_base.factor)
                return final_value, [parsed_from.value, base_unit.value, parsed_to.value]
            
            # If from_unit IS the base unit
            if parsed_from == base_unit and from_base:
                return value * float(from_base.factor), [parsed_from.value, parsed_to.value]
            
            # If to_unit IS the base unit
            if parsed_to == base_unit and to_base:
                return value * float(to_base.factor), [parsed_from.value, parsed_to.value]
        
        raise AppException(
            400,
            f"לא נמצאה דרך להמיר מ-{parsed_from.value} ל-{parsed_to.value}. יש להגדיר המרה בהגדרות."
        )

    def _convert_via_path(
        self,
        value: float,
        from_unit: UnitType,
        to_unit: UnitType,
    ) -> Tuple[float, List[str]]:
        """Resolve an explicit, editable cross-category conversion path."""
        adjacency: dict[UnitType, list[tuple[UnitType, float]]] = {}
        for conversion in self.get_all():
            adjacency.setdefault(conversion.from_unit, []).append(
                (conversion.to_unit, float(conversion.factor))
            )

        queue = deque([(from_unit, 1.0, [from_unit.value])])
        visited = {from_unit}
        while queue:
            current, factor, path = queue.popleft()
            for target, edge_factor in adjacency.get(current, []):
                if target in visited:
                    continue
                target_factor = factor * edge_factor
                target_path = [*path, target.value]
                if target == to_unit:
                    return value * target_factor, target_path
                visited.add(target)
                queue.append((target, target_factor, target_path))

        raise AppException(
            400,
            f"לא נמצאה דרך להמיר מ-{from_unit.value} ל-{to_unit.value}. יש להגדיר המרה בהגדרות."
        )

    def calculate_inventory_deduction(
        self,
        ingredient_quantity: float,
        ingredient_unit: UnitType | str,
        product_unit: UnitType | str,
        package_quantity: float,
    ) -> float:
        """
        Calculate how much to deduct from product stock.
        
        Args:
            ingredient_quantity: Amount needed in recipe
            ingredient_unit: Unit used in recipe (e.g., TABLESPOON)
            product_unit: Unit the product is stored in (e.g., KG)
            package_quantity: How much product is in one package
            
        Returns:
            Amount to deduct from quantity_in_stock (in product's unit)
        """
        # Parse units if strings
        parsed_ing: Optional[UnitType] = None
        parsed_prod: Optional[UnitType] = None
        
        if isinstance(ingredient_unit, str):
            parsed_ing = self._parse_unit(ingredient_unit)
        else:
            parsed_ing = ingredient_unit
            
        if isinstance(product_unit, str):
            parsed_prod = self._parse_unit(product_unit)
        else:
            parsed_prod = product_unit
        
        if parsed_ing is None or parsed_prod is None:
            logger.warning(f"Cannot convert units: {ingredient_unit} → {product_unit}")
            return 0.0
        
        # Same unit - simple calculation
        if parsed_ing == parsed_prod:
            return ingredient_quantity
        
        try:
            converted_value, _ = self.convert(ingredient_quantity, parsed_ing, parsed_prod)
            return converted_value
        except AppException as e:
            logger.warning(f"Conversion failed: {e.detail}")
            return 0.0

    # ── Initialization ────────────────────────────────────────────────

    def seed_system_conversions(self) -> int:
        """
        Seed system conversions if they don't exist.
        Called during app startup or migration.
        
        Returns:
            Number of conversions created
        """
        created = 0
        
        # System conversions
        for from_unit, to_unit, factor, desc in SYSTEM_CONVERSIONS:
            existing = self.get_conversion(from_unit, to_unit)
            if not existing:
                conv = UnitConversion(
                    from_unit=from_unit,
                    to_unit=to_unit,
                    factor=factor,
                    is_system=True,
                    description=desc,
                )
                self.db.add(conv)
                created += 1
        
        # Default user conversions
        for from_unit, to_unit, factor, desc in DEFAULT_USER_CONVERSIONS:
            existing = self.get_conversion(from_unit, to_unit)
            if not existing:
                conv = UnitConversion(
                    from_unit=from_unit,
                    to_unit=to_unit,
                    factor=factor,
                    is_system=False,
                    description=desc,
                )
                self.db.add(conv)
                created += 1
        
        if created > 0:
            self.db.commit()
            logger.info(f"Seeded {created} unit conversions")
        
        return created

    # ── Helpers ───────────────────────────────────────────────────────

    def _parse_unit(self, unit_str: str) -> Optional[UnitType]:
        """Parse a unit string to UnitType enum."""
        if isinstance(unit_str, UnitType):
            return unit_str
        
        for unit in UnitType:
            if unit.value == unit_str or unit.name == unit_str:
                return unit
        return None
