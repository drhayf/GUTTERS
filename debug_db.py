import asyncio
import sys
import os

# Add src to sys.path
sys.path.append(os.path.join(os.getcwd(), "src"))

from app.core.db.database import async_engine, Base, DATABASE_URL
from app.models.user import User
from app.models.user_profile import UserProfile

async def main():
    print(f"DATABASE_URL: {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else DATABASE_URL}")
    print("Attempting to create tables...")
    
    # Try with default engine first
    try:
        print("\n--- Testing with default engine (from database.py) ---")
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("SUCCESS: Tables created with default engine")
    except Exception as e:
        print(f"FAILED: Default engine error: {e}")
        
    # Try with NullPool and explicit statement_cache_size=0
    from sqlalchemy.pool import NullPool
    from sqlalchemy.ext.asyncio import create_async_engine as create_engine_alt
    
    print("\n--- Testing with NullPool and statement_cache_size=0 ---")
    alt_engine = create_engine_alt(
        DATABASE_URL,
        poolclass=NullPool,
        connect_args={"statement_cache_size": 0}
    )
    try:
        async with alt_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("SUCCESS: Tables created with NullPool")
    except Exception as e:
        print(f"FAILED: NullPool error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
