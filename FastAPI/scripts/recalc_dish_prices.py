import logging
import pathlib
import sys
from typing import Dict, Optional

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from app.core.database import SessionLocal
from app.models.dish import Dish, DishIngredient, ServingDish
from app.models.product import Product
from app.models.tool import Tool
from app.models.unit_conversion import UnitConversion
from app.core.enums import UnitType

logging.basicConfig(level=logging.INFO, format="%(message)s")


def get_conversion_factor(from_unit: str, to_unit: str, conversions: Dict[tuple, float]) -> Optional[float]:
    """Get conversion factor between units using cached conversions."""
    if from_unit == to_unit:
        return 1.0
    
    # Direct conversion
    if (from_unit, to_unit) in conversions:
        return conversions[(from_unit, to_unit)]
    
    # Through base unit (gram)
    if (from_unit, 'גרם') in conversions and ('גרם', to_unit) in conversions:
        return conversions[(from_unit, 'גרם')] * conversions[('גרם', to_unit)]
    
    # Through kg
    if (from_unit, 'ק"ג') in conversions and ('ק"ג', to_unit) in conversions:
        return conversions[(from_unit, 'ק"ג')] * conversions[('ק"ג', to_unit)]
    
    # Complex: from_unit -> gram -> kg -> to_unit
    if (from_unit, 'גרם') in conversions and ('גרם', 'ק"ג') in conversions:
        if to_unit == 'ק"ג':
            return conversions[(from_unit, 'גרם')] * conversions[('גרם', 'ק"ג')]
    
    return None


def calculate_dish_price(
    ingredients, 
    serving_dishes, 
    product_data: Dict[int, tuple],  # {product_id: (price_per_unit, estimated_price, package_qty, unit)}
    tool_prices: Dict[int, float],
    conversions: Dict[tuple, float]
) -> float:
    """Calculate dish price with unit conversion."""
    total = 0.0
    for ing in ingredients:
        product_info = product_data.get(ing.product_id)
        if not product_info:
            continue
        
        price_per_unit, estimated_price, package_qty, product_unit = product_info
        
        # Use estimated_price / package_qty as base
        effective_price = estimated_price or price_per_unit or 0
        if effective_price == 0:
            continue
            
        package_qty = package_qty or 1
        price_per_product_unit = effective_price / package_qty
        
        # Get ingredient unit
        ing_unit = ing.unit.value if hasattr(ing.unit, 'value') else ing.unit
        prod_unit = product_unit.value if hasattr(product_unit, 'value') else product_unit
        
        # Convert ingredient quantity to product unit
        conversion_factor = get_conversion_factor(ing_unit, prod_unit, conversions)
        
        if conversion_factor is not None:
            converted_qty = (ing.quantity or 0) * conversion_factor
            total += price_per_product_unit * converted_qty
        else:
            # Fallback: no conversion, use direct multiplication
            total += price_per_product_unit * (ing.quantity or 0)
    
    for sd in serving_dishes:
        price = tool_prices.get(sd.tool_id, 0) or 0
        total += price * (sd.quantity or 0)
    
    return round(total, 2)


def main():
    session = SessionLocal()
    try:
        # Load unit conversions as dict {(from_unit, to_unit): factor}
        conversions_raw = session.query(UnitConversion).filter(UnitConversion.is_deleted == False).all()
        conversions = {}
        for c in conversions_raw:
            from_u = c.from_unit.value if hasattr(c.from_unit, 'value') else c.from_unit
            to_u = c.to_unit.value if hasattr(c.to_unit, 'value') else c.to_unit
            conversions[(from_u, to_u)] = float(c.factor)
        
        # Load products with full info
        products_raw = session.query(
            Product.id, 
            Product.price_per_unit, 
            Product.estimated_price, 
            Product.package_quantity,
            Product.unit
        ).all()
        product_data = {
            p.id: (p.price_per_unit, p.estimated_price, p.package_quantity, p.unit) 
            for p in products_raw
        }
        
        tools = dict(session.query(Tool.id, Tool.price_per_unit).all())

        updated = 0
        unchanged = 0

        dishes = session.query(Dish).all()
        for dish in dishes:
            ingredients = session.query(DishIngredient).filter(DishIngredient.dish_id == dish.id).all()
            serving_dishes = session.query(ServingDish).filter(ServingDish.dish_id == dish.id).all()

            new_price = calculate_dish_price(ingredients, serving_dishes, product_data, tools, conversions)
            if abs((dish.base_price or 0) - new_price) > 0.01:
                dish.base_price = new_price
                updated += 1
                logging.info(f"Updated dish '{dish.name}': {dish.base_price} -> {new_price}")
            else:
                unchanged += 1

        session.commit()
        logging.info(f"Updated {updated} dishes; {unchanged} unchanged.")
    finally:
        session.close()


if __name__ == "__main__":
    main()
