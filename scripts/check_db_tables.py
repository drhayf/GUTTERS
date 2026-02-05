import asyncio
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from src.app.core.db.database import async_engine
from sqlalchemy import inspect


async def check_schema():
    def get_tables(conn):
        inspector = inspect(conn)
        return inspector.get_table_names()

    async with async_engine.connect() as conn:
        tables = await conn.run_sync(get_tables)
        print("Existing Tables in Database:")
        for table in tables:
            print(f" - {table}")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(check_schema())
