"""
Create Oracle Reading table in database.
"""
import asyncio

from src.app.core.db.database import Base, async_engine


async def create_tables():
    """Create all tables including oracle_readings."""
    async with async_engine.begin() as conn:
        # Create only oracle_readings table
        await conn.run_sync(Base.metadata.create_all)

    print("✅ Oracle reading table created successfully!")


if __name__ == "__main__":
    asyncio.run(create_tables())
