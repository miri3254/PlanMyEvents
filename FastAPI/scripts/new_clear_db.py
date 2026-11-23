import asyncio
import sys
from pathlib import Path
import os

# Add project root to the Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
# also add the parent of the project root
sys.path.insert(0, str(project_root.parent))

from app.core.database import engine, Base
from app.models.dish import Dish, DishIngredient, DishEquipment, ServingDish
from app.models.event import Event, EventDish, EventOwner
from app.models.product import Product
from app.models.tool import Tool
from app.models.lookup import LookupData
from app.models.menu import DishMenuMapping
from app.models.menu_template import MenuTemplate, MenuCategory

async def clear_db():
    """
    Completely wipe all data from the database.
    Tables are dropped in reverse dependency order to avoid foreign key errors.
    """
    print("=" * 70)
    print("DANGER: This is a DESTRUCTIVE operation that cannot be undone!")
    print("Starting complete data wipe...")

    async with engine.begin() as conn:
        # Drop tables in reverse order of dependencies
        await conn.run_sync(Base.metadata.drop_all, checkfirst=True, tables=[
            EventDish.__table__,
            EventOwner.__table__,
            DishIngredient.__table__,
            DishEquipment.__table__,
            DishMenuMapping.__table__,
        ])
        print("Dropped join tables...")

        await conn.run_sync(Base.metadata.drop_all, checkfirst=True, tables=[
            Dish.__table__,
            Event.__table__,
            Product.__table__,
            Tool.__table__,
            ServingDish.__table__,
            MenuCategory.__table__,
        ])
        print("Dropped primary data tables...")

        await conn.run_sync(Base.metadata.drop_all, checkfirst=True, tables=[
            MenuTemplate.__table__,
            LookupData.__table__,
        ])
        print("Dropped remaining tables...")

        print("All tables dropped successfully.")
        print("-" * 70)
        print("Recreating all tables from metadata...")
        await conn.run_sync(Base.metadata.create_all)
        print("All tables recreated successfully.")

    print("Database has been wiped and reset.")
    print("=" * 70)

async def main():
    # This is to address a known issue on Windows with asyncio
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    await clear_db()

if __name__ == "__main__":
    asyncio.run(main())
