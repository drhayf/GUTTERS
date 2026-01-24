import asyncio
import os
import sys

# Ensure src is in the path
sys.path.append(os.path.join(os.getcwd(), "src"))

from app.core.db.database import local_session
from app.models.user import User
from sqlalchemy import select

async def main():
    async with local_session() as db:
        result = await db.execute(select(User))
        users = result.scalars().all()
        for u in users:
            print(f"ID: {u.id}, Username: {u.username}, Email: {u.email}")

if __name__ == "__main__":
    asyncio.run(main())
