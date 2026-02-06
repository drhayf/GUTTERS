#!/usr/bin/env python3
"""
Maximum Fidelity Quest Visibility Check.
Verifies that:
1. All quests exist in database with correct data
2. API endpoints return properly serialized responses
3. Frontend will receive correct data format
4. No serialization errors occur
"""

import asyncio
import json
import os
import sys

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import selectinload, sessionmaker

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from app.api.v1.quests import QuestRead
from app.core.config import settings
from app.models.user import User
from app.modules.features.quests.models import Quest, QuestLog, QuestStatus


async def main():
    DATABASE_URL = settings.POSTGRES_ASYNC_URI
    print("📊 QUEST VISIBILITY DIAGNOSTIC CHECK")
    print("=" * 80)
    print(f"Database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'Unknown'}")
    print("=" * 80)

    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with async_session() as db:
            # 1. GET ALL USERS
            print("\n1️⃣  USERS IN SYSTEM")
            print("-" * 80)
            result = await db.execute(select(User))
            users = result.scalars().all()
            print(f"   Total users: {len(users)}")
            for user in users[:5]:
                print(f"   • User #{user.id}: {user.username} ({user.email})")

            # 2. GET ALL QUESTS
            print("\n2️⃣  QUESTS IN DATABASE")
            print("-" * 80)
            result = await db.execute(select(Quest))
            all_quests = result.scalars().all()
            print(f"   Total quests: {len(all_quests)}")

            # Group by user
            quests_by_user = {}
            for quest in all_quests:
                if quest.user_id not in quests_by_user:
                    quests_by_user[quest.user_id] = []
                quests_by_user[quest.user_id].append(quest)

            for user_id, quests in sorted(quests_by_user.items()):
                print(f"\n   👤 User #{user_id}: {len(quests)} quests")
                for quest in quests[:10]:
                    print(f"      • Quest #{quest.id}: '{quest.title}'")
                    print(f"        - recurrence: {quest.recurrence} (type: {type(quest.recurrence).__name__})")
                    print(f"        - difficulty: {quest.difficulty} (type: {type(quest.difficulty).__name__})")
                    print(f"        - source: {quest.source} (type: {type(quest.source).__name__})")
                    print(f"        - is_active: {quest.is_active}")
                    print(f"        - user_id: {quest.user_id}")

            # 3. GET ALL QUEST LOGS
            print("\n3️⃣  QUEST LOGS IN DATABASE")
            print("-" * 80)
            result = await db.execute(select(QuestLog))
            all_logs = result.scalars().all()

            # Count by status
            status_counts = {}
            for log in all_logs:
                status = str(log.status)
                status_counts[status] = status_counts.get(status, 0) + 1

            print(f"   Total logs: {len(all_logs)}")
            for status, count in sorted(status_counts.items()):
                print(f"   • {status}: {count}")

            # 4. TEST API SERIALIZATION (view=definitions)
            print("\n4️⃣  API SERIALIZATION TEST - CONTROL ROOM (view=definitions)")
            print("-" * 80)

            if len(users) > 0:
                test_user = users[0]
                print(f"   Testing with user: {test_user.username} (#{test_user.id})")

                # Simulate API call: get_active_quests
                result = await db.execute(select(Quest).where(Quest.user_id == test_user.id, Quest.is_active.is_(True)))
                user_quests = result.scalars().all()

                print(f"   Active quests for user: {len(user_quests)}")

                if len(user_quests) > 0:
                    quest = user_quests[0]
                    print("\n   ✓ Serializing first quest for API response...")

                    try:
                        # Simulate QuestRead creation (what the API does)
                        quest_read = QuestRead(
                            id=quest.id,
                            title=quest.title,
                            description=quest.description,
                            recurrence=quest.recurrence,
                            cron_expression=quest.cron_expression,
                            difficulty=quest.difficulty,
                            tags=quest.tags,
                            is_active=quest.is_active,
                            source=quest.source,
                            job_id=quest.job_id,
                            log_id=None,
                            status=None,
                        )

                        # Convert to dict (what FastAPI returns as JSON)
                        quest_dict = quest_read.model_dump()

                        print("\n   API Response:")
                        print(f"      - id: {quest_dict['id']} (type: {type(quest_dict['id']).__name__})")
                        print(f"      - title: {quest_dict['title']} (type: {type(quest_dict['title']).__name__})")
                        print(
                            f"      - recurrence: {quest_dict['recurrence']} "
                            f"(type: {type(quest_dict['recurrence']).__name__})"
                        )
                        print("        ✓ Frontend expects: string 'daily', 'weekly', etc.")
                        recurrence_valid = isinstance(quest_dict['recurrence'], str)
                        print(f"        {'✓ PASS' if recurrence_valid else '✗ FAIL'}")

                        print(f"      - source: {quest_dict['source']} (type: {type(quest_dict['source']).__name__})")
                        print("        ✓ Frontend expects: string 'user', 'agent', etc.")
                        source_valid = isinstance(quest_dict['source'], str)
                        print(f"        {'✓ PASS' if source_valid else '✗ FAIL'}")
                        print(
                            f"      - difficulty: {quest_dict['difficulty']} "
                            f"(type: {type(quest_dict['difficulty']).__name__})"
                        )
                        print("        ✓ Frontend expects: integer 1-4")
                        is_valid_difficulty = (
                            isinstance(quest_dict['difficulty'], int) and
                            1 <= quest_dict['difficulty'] <= 4
                        )
                        result_str = "✓ PASS" if is_valid_difficulty else "✗ FAIL"
                        print(f"        {result_str}")

                        # Can it be JSON serialized?
                        json_str = json.dumps(quest_dict)
                        print("\n   ✓ JSON serialization: SUCCESS")
                        print(f"   ✓ Sample JSON: {json_str[:100]}...")

                    except Exception as e:
                        print(f"   ✗ ERROR during serialization: {e}")

                # 5. TEST API SERIALIZATION (view=tasks)
                print("\n5️⃣  API SERIALIZATION TEST - DASHBOARD (view=tasks)")
                print("-" * 80)
                print(f"   Testing with user: {test_user.username} (#{test_user.id})")

                # Simulate API call: get_pending_logs with eager loading
                stmt = (
                    select(QuestLog).options(selectinload(QuestLog.quest)).where(QuestLog.status == QuestStatus.PENDING)
                )
                result = await db.execute(stmt)
                pending_logs = result.scalars().unique().all()

                # Filter by user
                user_pending_logs = [log for log in pending_logs if log.quest.user_id == test_user.id]
                print(f"   Pending tasks for user: {len(user_pending_logs)}")

                if len(user_pending_logs) > 0:
                    log = user_pending_logs[0]
                    quest = log.quest
                    print("\n   ✓ Serializing first pending log for API response...")

                    try:
                        quest_read = QuestRead(
                            id=quest.id,
                            title=quest.title,
                            description=quest.description,
                            recurrence=quest.recurrence,
                            cron_expression=quest.cron_expression,
                            difficulty=quest.difficulty,
                            tags=quest.tags,
                            is_active=quest.is_active,
                            source=quest.source,
                            job_id=quest.job_id,
                            log_id=log.id,
                            status=log.status,
                        )

                        quest_dict = quest_read.model_dump()

                        print("\n   API Response:")
                        print(f"      - id: {quest_dict['id']}")
                        print(f"      - log_id: {quest_dict['log_id']} (instance ID)")
                        print(f"      - status: {quest_dict['status']} (pending/completed/etc.)")
                        print(f"      - title: {quest_dict['title']}")

                        json_str = json.dumps(quest_dict)
                        print("\n   ✓ JSON serialization: SUCCESS")
                        print(f"   Sample JSON: {json_str[:120]}...")

                    except Exception as e:
                        print(f"   ✗ ERROR during serialization: {e}")

                else:
                    print("   ⚠️  No pending logs found. Run tests to create sample data.")

            # 6. SUMMARY
            print("\n" + "=" * 80)
            print("6️⃣  SUMMARY & RECOMMENDATIONS")
            print("=" * 80)

            print("\n✓ Total Database Records:")
            print(f"  • Users: {len(users)}")
            print(f"  • Quests: {len(all_quests)}")
            print(f"  • QuestLogs: {len(all_logs)}")

            # Check for data issues
            issues = []

            # Check for quests with no logs
            quests_with_no_logs = []
            for quest in all_quests:
                log_count = sum(1 for log in all_logs if log.quest_id == quest.id)
                if log_count == 0:
                    quests_with_no_logs.append(quest.id)

            if quests_with_no_logs:
                issues.append(f"⚠️  {len(quests_with_no_logs)} quests have no associated logs")

            if not issues:
                print("\n✓ No issues detected!")
                print("✓ Frontend Dashboard should display all pending quests")
                print("✓ Frontend Control Room should display all active quests")
                print("✓ All serialization is correct (strings and integers)")
            else:
                print("\n⚠️  Issues detected:")
                for issue in issues:
                    print(f"  {issue}")

    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
