#!/usr/bin/env python3
"""
Diagnostic script to check quest data in the database.
"""

import asyncio
import os
import sys

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from app.models.user import User
from app.modules.features.quests.models import Quest, QuestLog, QuestStatus

DATABASE_URL = os.getenv("DATABASE_URL")


async def main():
    if not DATABASE_URL:
        print("ERROR: DATABASE_URL not set")
        return

    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        print("=" * 80)
        print("QUEST DATABASE DIAGNOSTIC")
        print("=" * 80)

        # Check users
        result = await db.execute(select(User))
        users = result.scalars().all()
        print(f"\n1. Total Users: {len(users)}")
        for user in users[:5]:
            print(f"   - User ID {user.id}: {user.email}")

        # Check quests
        result = await db.execute(select(Quest))
        quests = result.scalars().all()
        print(f"\n2. Total Quests: {len(quests)}")

        for quest in quests[:10]:
            print(f"\n   Quest ID {quest.id}:")
            print(f"   - Title: {quest.title}")
            print(f"   - User ID: {quest.user_id}")
            print(f"   - is_active: {quest.is_active}")
            print(f"   - Source: {quest.source}")
            print(f"   - Created: {quest.created_at}")

            # Check logs for this quest
            result = await db.execute(select(QuestLog).where(QuestLog.quest_id == quest.id))
            logs = result.scalars().all()
            print(f"   - Logs: {len(logs)}")
            for log in logs[:3]:
                print(f"     * Log {log.id}: status={log.status}, scheduled={log.scheduled_for}")

        # Check quest logs directly
        result = await db.execute(select(QuestLog))
        all_logs = result.scalars().all()
        print(f"\n3. Total Quest Logs: {len(all_logs)}")

        # Group by status
        pending = [l for l in all_logs if l.status == QuestStatus.PENDING]
        completed = [l for l in all_logs if l.status == QuestStatus.COMPLETED]
        print(f"   - Pending: {len(pending)}")
        print(f"   - Completed: {len(completed)}")

        # Raw query to check for any data
        result = await db.execute(
            text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        )
        tables = result.scalars().all()
        print(f"\n4. Database Tables: {len(tables)}")
        for table in tables:
            if "quest" in table.lower():
                result = await db.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                print(f"   - {table}: {count} rows")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
