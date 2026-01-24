import asyncio
import os
import sys

sys.path.append(os.path.join(os.getcwd(), "src"))

from app.core.db.database import local_session, Base
from app.models.user import User
from app.models.user_profile import UserProfile
from sqlalchemy import select

async def main():
    print(f"Metadata tables: {Base.metadata.tables.keys()}")
    async with local_session() as db:
        result = await db.execute(select(UserProfile))
        profiles = result.scalars().all()
        print(f"Found {len(profiles)} profiles.")
        for p in profiles:
            print(f"ID: {p.id}, UserID: {p.user_id}")

if __name__ == "__main__":
    asyncio.run(main())
