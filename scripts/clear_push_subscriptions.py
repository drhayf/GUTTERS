#!/usr/bin/env python3
"""
Clear all push subscriptions for a user or all users.
Run this to force resubscription with the current VAPID keys.
"""

import asyncio
import sys
import os

# Change to src directory for proper imports
os.chdir(os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.getcwd())

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select
from app.models.push import PushSubscription
from app.core.config import settings


async def clear_user_subscriptions(db: AsyncSession, user_id: int) -> int:
    """Delete all push subscriptions for a specific user."""
    stmt = select(PushSubscription).where(PushSubscription.user_id == user_id)
    result = await db.execute(stmt)
    subs = result.scalars().all()

    count = len(subs)
    for sub in subs:
        await db.delete(sub)

    await db.commit()
    return count


async def clear_all_subscriptions(db: AsyncSession) -> int:
    """Delete all push subscriptions for all users."""
    stmt = select(PushSubscription)
    result = await db.execute(stmt)
    subs = result.scalars().all()

    count = len(subs)
    for sub in subs:
        await db.delete(sub)

    await db.commit()
    return count


async def main():
    """Main entry point."""
    # Parse arguments
    if len(sys.argv) < 2:
        print("Usage: python clear_push_subscriptions.py <user_id>|all")
        print("  <user_id> - Clear subscriptions for specific user")
        print("  all       - Clear ALL subscriptions for all users")
        return

    arg = sys.argv[1]

    # Build the database URL from settings
    # Check if POSTGRES_URL is set, otherwise build from components
    db_url = None

    # Try to use PostgreSQL settings from .env
    if settings.POSTGRES_SERVER:
        db_url = f"{settings.POSTGRES_ASYNC_PREFIX}{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
        print(f"[POSTGRES] Using PostgreSQL: {settings.POSTGRES_SERVER}")
    elif settings.SQLITE_URI:
        # Fallback to SQLite
        db_url = settings.SQLITE_ASYNC_PREFIX + os.path.abspath(settings.SQLITE_URI)
        print(f"[SQLITE] Using SQLite: {settings.SQLITE_URI}")

    if not db_url:
        print("[ERROR] No database configured!")
        return

    print(f"[DB] Connecting to: {db_url[:50]}...")

    engine = create_async_engine(db_url, echo=False)

    # Create async session factory
    async_session = async_sessionmaker(engine, class_=AsyncSession)

    async with async_session() as session:
        if arg == "all":
            count = await clear_all_subscriptions(session)
            print(f"[OK] Cleared {count} subscriptions for ALL users")
        else:
            try:
                user_id = int(arg)
                count = await clear_user_subscriptions(session, user_id)
                print(f"[OK] Cleared {count} subscriptions for user {user_id}")
            except ValueError:
                print(f"[ERROR] Invalid user ID: {arg}")
                print("Usage: python clear_push_subscriptions.py <user_id>|all")
                return

    await engine.dispose()
    print("[DONE]")


if __name__ == "__main__":
    asyncio.run(main())
