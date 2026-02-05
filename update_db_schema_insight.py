import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine
from src.app.core.db.database import Base, DATABASE_URL
from src.app.models.insight import ReflectionPrompt, JournalEntry

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_tables():
    """
    Create the reflection_prompts and journal_entries tables.
    """
    logger.info("Starting schema update for Insight Engine...")

    # Use the centralized DATABASE_URL
    database_url = DATABASE_URL
    logger.info(f"Connecting to database...")

    engine = create_async_engine(database_url, echo=True)

    async with engine.begin() as conn:
        logger.info("Creating tables (reflection_prompts, journal_entries) if not exist...")
        await conn.run_sync(Base.metadata.create_all)

        logger.info("Schema update completed successfully.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(create_tables())
