import asyncio

from sqlalchemy import text

from src.app.core.db.database import local_session as async_session_factory


async def update_schema_source():
    async with async_session_factory() as session:
        try:
            print("Attempting to add source column to quests table...")
            # Check if column exists first to avoid error if re-running
            # Actually, standard SQL ADD COLUMN IF NOT EXISTS is cleanest
            await session.execute(text("ALTER TABLE quests ADD COLUMN IF NOT EXISTS source VARCHAR DEFAULT 'user';"))
            await session.commit()
            print("Success! Source column added.")
        except Exception as e:
            print(f"Error: {e}")
            await session.rollback()


if __name__ == "__main__":
    asyncio.run(update_schema_source())
