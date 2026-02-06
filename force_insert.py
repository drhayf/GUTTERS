import asyncio
import os
import sys

sys.path.append(os.path.join(os.getcwd(), "src"))

from sqlalchemy import text

from app.core.db.database import local_session


async def main():
    async with local_session() as db:
        await db.execute(text("INSERT INTO user_profile (user_id, data, created_at) VALUES (4, '{}', now())"))
        await db.commit()
        print("Inserted manually!")

if __name__ == "__main__":
    asyncio.run(main())
