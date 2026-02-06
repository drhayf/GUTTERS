import asyncio

from sqlalchemy import select
from sqlalchemy.orm import configure_mappers

from src.app.core.db.database import local_session
from src.app.models.user import User


async def cleanup_users(keep_username: str):
    configure_mappers()
    async with local_session() as db:
        async with db.begin():
            # Count users to be deleted
            result = await db.execute(select(User).where(User.username != keep_username))
            users_to_delete = result.scalars().all()
            count = len(users_to_delete)

            if count == 0:
                print(f"No other users found except '{keep_username}'.")
                return

            print(f"Deleting {count} test users...")

            # Delete everyone else
            # Note: cascades (profile, embeddings, chat_sessions) are handled by SQLAlchemy if loaded,
            # but for a raw delete we rely on DB constraints or manual cleanup if cascade isn't set at DB level.
            # User model has cascade="all, delete-orphan", so SQLAlchemy will handle it if we delete objects.

            for user in users_to_delete:
                await db.delete(user)

            print(f"Successfully purged {count} test accounts.")


if __name__ == "__main__":
    asyncio.run(cleanup_users("drof"))
