import asyncio

from sqlalchemy import select
from sqlalchemy.orm import configure_mappers

from src.app.core.db.database import local_session
from src.app.models.user import User


async def check_users():
    configure_mappers()
    async with local_session() as db:
        result = await db.execute(select(User))
        users = result.scalars().all()
        print(f"Total Users: {len(users)}")
        for user in users:
            print(f"ID: {user.id}, Username: {user.username}, Is Superuser: {user.is_superuser}")


if __name__ == "__main__":
    asyncio.run(check_users())
