import asyncio
import sys
from pathlib import Path

# Add the current directory to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent))
print(sys.path)

from scripts.new_clear_db import clear_db

async def main():
    # This is to address a known issue on Windows with asyncio
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    await clear_db()

if __name__ == "__main__":
    asyncio.run(main())
