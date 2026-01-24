
import asyncio
from sqlalchemy import text
from src.app.core.db.database import async_engine

async def check_pgvector():
    try:
        async with async_engine.connect() as conn:
            result = await conn.execute(text("SELECT extname FROM pg_extension WHERE extname = 'vector';"))
            extension = result.scalar()
            if extension:
                print("pgvector extension is already installed.")
            else:
                print("pgvector extension is NOT installed. Attempting to check if it can be installed...")
                # Try to see if it's available
                result = await conn.execute(text("SELECT name FROM pg_available_extensions WHERE name = 'vector';"))
                available = result.scalar()
                if available:
                    print("pgvector extension is available for installation.")
                else:
                    print("pgvector extension is NOT available in this PostgreSQL instance.")
    except Exception as e:
        print(f"Error checking pgvector: {e}")

if __name__ == "__main__":
    asyncio.run(check_pgvector())
