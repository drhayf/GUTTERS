import asyncio
from sqlalchemy import text
from src.app.core.db.database import local_session as async_session_factory


async def update_schema():
    async with async_session_factory() as session:
        try:
            print("Attempting to add job_id column to quests table...")
            await session.execute(text("ALTER TABLE quests ADD COLUMN job_id VARCHAR;"))
            await session.commit()
            print("Success! Column added.")
        except Exception as e:
            print(f"Error (ignoring if column exists): {e}")
            await session.rollback()


if __name__ == "__main__":
    asyncio.run(update_schema())
