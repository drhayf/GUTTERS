import logging
from datetime import UTC, datetime
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.app.core.events.bus import get_event_bus
from src.app.core.worker.client import get_arq_pool
from src.app.modules.features.quests.models import (
    Quest,
    QuestCategory,
    QuestDifficulty,
    QuestLog,
    QuestSource,
    QuestStatus,
    RecurrenceType,
)
from src.app.protocol import events

logger = logging.getLogger(__name__)

# Base XP rewards by difficulty
XP_MAP = {
    QuestDifficulty.EASY: 10,
    QuestDifficulty.MEDIUM: 25,
    QuestDifficulty.HARD: 50,
    QuestDifficulty.ELITE: 100,
}


class QuestManager:
    """
    Manages the lifecycle of Quests, XP rewards, and progression synchronization.
    """

    @staticmethod
    async def _get_redis():
        return await get_arq_pool()

    @staticmethod
    async def create_quest(
        db: AsyncSession,
        user_id: int,
        title: str,
        description: str = None,
        category: QuestCategory = QuestCategory.DAILY,
        difficulty: QuestDifficulty = QuestDifficulty.EASY,
        recurrence: RecurrenceType = RecurrenceType.ONCE,
        cron_expression: str = None,
        tags: List[str] = None,
        source: QuestSource = QuestSource.USER,
        insight_id: Optional[int] = None,
    ) -> Quest:
        """
        Creates a new Quest definition with associated XP reward.
        """
        tag_str = ",".join(tags) if tags else ""

        # Normalize recurrence - handle string input
        if isinstance(recurrence, str):
            recurrence_map = {
                "once": RecurrenceType.ONCE,
                "daily": RecurrenceType.DAILY,
                "weekly": RecurrenceType.WEEKLY,
                "monthly": RecurrenceType.MONTHLY,
                "custom": RecurrenceType.CUSTOM,
            }
            recurrence = recurrence_map.get(recurrence.lower(), RecurrenceType.ONCE)

        # Handle int difficulty (Rank 1-4)
        if isinstance(difficulty, int):
            difficulty_map = {
                1: QuestDifficulty.EASY,
                2: QuestDifficulty.MEDIUM,
                3: QuestDifficulty.HARD,
                4: QuestDifficulty.ELITE,
            }
            difficulty = difficulty_map.get(difficulty, QuestDifficulty.EASY)

        # Determine base XP
        base_xp = XP_MAP.get(difficulty, 10)

        quest = Quest(
            user_id=user_id,
            title=title,
            description=description,
            category=category,
            difficulty=difficulty,
            xp_reward=base_xp,
            insight_id=insight_id,
            recurrence=recurrence,
            cron_expression=cron_expression,
            tags=tag_str,
            is_active=True,
            source=source,
        )
        db.add(quest)
        await db.commit()
        await db.refresh(quest)

        # Schedule first occurrence
        # High Fidelity: Create the first log IMMEDIATELY so it appears in the UI even if the worker is slow/down.
        # The worker (trigger_quest_notification) is now idempotent and will skip creation if it sees this.
        await QuestManager.create_log(db=db, quest_id=quest.id, scheduled_for=datetime.now(UTC))

        await QuestManager._schedule_quest(db, quest)

        # Emit QUEST_CREATED event
        bus = get_event_bus()
        await bus.publish(
            events.QUEST_CREATED, {"quest_id": quest.id, "user_id": user_id, "title": title}, user_id=str(user_id)
        )

        return quest

    @staticmethod
    async def complete_quest(db: AsyncSession, quest_log_id: int, notes: str = None) -> QuestLog:
        """
        Marks a specific quest log as COMPLETED, calculates XP, and updates progression.
        """
        stmt = select(QuestLog).options(selectinload(QuestLog.quest)).join(Quest).where(QuestLog.id == quest_log_id)
        result = await db.execute(stmt)
        log = result.scalar_one_or_none()

        if not log:
            raise ValueError(f"QuestLog {quest_log_id} not found")

        if log.status == QuestStatus.COMPLETED:
            return log  # Already completed

        # 1. Update Log Status
        log.status = QuestStatus.COMPLETED
        log.completed_at = datetime.now(UTC)
        log.notes = notes

        # 2. XP Reward (Logic moved to EvolutionEngine)
        # Quests now emit a ProgressionPacket, and the EvolutionEngine handles the math

        # Calculate base multipliers (passed as context in packet)
        multiplier = 1.0
        if log.quest.insight_id:
            multiplier *= 1.5

        xp_base = log.quest.xp_reward
        xp_total = int(xp_base * multiplier)

        await db.commit()
        await db.refresh(log)

        # 3. Emit Events
        bus = get_event_bus()
        from src.app.protocol.packet import ProgressionPacket

        # Progression Packet (Centralized Math)
        packet = ProgressionPacket(
            source="quest_manager",
            event_type=events.PROGRESSION_EXPERIENCE_GAIN,
            payload={
                "quest_id": log.quest_id,
                "log_id": log.id,
                "title": log.quest.title,
                "category": log.quest.category,
                "insight_id": log.quest.insight_id,
            },
            user_id=str(log.quest.user_id),
            amount=xp_total,
            reason=f"Quest Completed: {log.quest.title}",
            category="SYNC" if log.quest.category == QuestCategory.DAILY else "INTELLECT",
        )
        await bus.publish_packet(packet)

        # Legacy Event for backward compatibility if needed (deprecated)
        await bus.publish(
            events.QUEST_COMPLETED,
            {"quest_id": log.quest_id, "xp_gained": xp_total, "log_id": log.id},
            user_id=str(log.quest.user_id),
        )

        logger.info(f"QuestManager: Quest {log.quest_id} completed. Emitted ProgressionPacket ({xp_total} XP)")

        return log

    @staticmethod
    async def update_quest(
        db: AsyncSession,
        quest_id: int,
        title: str = None,
        recurrence: RecurrenceType = None,
        cron_expression: str = None,
        is_active: bool = None,
    ) -> Quest:
        """
        Updates a quest. Handles rescheduling if recurrence changes.
        """
        stmt = select(Quest).where(Quest.id == quest_id)
        result = await db.execute(stmt)
        quest = result.scalar_one_or_none()

        if not quest:
            raise ValueError(f"Quest {quest_id} not found")

        # Normalize recurrence - handle string input
        if isinstance(recurrence, str):
            recurrence_map = {
                "once": RecurrenceType.ONCE,
                "daily": RecurrenceType.DAILY,
                "weekly": RecurrenceType.WEEKLY,
                "monthly": RecurrenceType.MONTHLY,
                "custom": RecurrenceType.CUSTOM,
            }
            recurrence = recurrence_map.get(recurrence.lower(), RecurrenceType.ONCE)

        # Track if scheduling needs update
        schedule_changed = False
        if recurrence is not None and recurrence != quest.recurrence:
            quest.recurrence = recurrence
            schedule_changed = True
        if cron_expression is not None and cron_expression != quest.cron_expression:
            quest.cron_expression = cron_expression
            schedule_changed = True

        if title:
            quest.title = title

        # If deactivating, cancel job
        if is_active is not None and is_active != quest.is_active:
            quest.is_active = is_active
            if not is_active:
                await QuestManager._cancel_job(quest.job_id)
                quest.job_id = None
            elif is_active:
                # Reactivating -> Schedule
                schedule_changed = True

        if schedule_changed and quest.is_active:
            # cancel old job
            await QuestManager._cancel_job(quest.job_id)
            # schedule new one
            await QuestManager._schedule_quest(db, quest)

        await db.commit()
        await db.refresh(quest)
        return quest

    @staticmethod
    async def delete_quest(db: AsyncSession, quest_id: int):
        """
        Deletes a quest and cancels its job.
        """
        stmt = select(Quest).where(Quest.id == quest_id)
        result = await db.execute(stmt)
        quest = result.scalar_one_or_none()

        if quest:
            await QuestManager._cancel_job(quest.job_id)
            await db.delete(quest)
            await db.commit()

    @staticmethod
    async def _cancel_job(job_id: str):
        if not job_id:
            return
        redis = await get_arq_pool()
        try:
            from arq.jobs import Job

            job = Job(job_id, redis)
            await job.abort(timeout=1)
        except Exception:
            pass  # Job might not exist
        # Do not close singleton pool

    @staticmethod
    async def _schedule_quest(db: AsyncSession, quest: Quest):
        """
        Internal method to schedule the ARQ job.
        """
        redis = await get_arq_pool()
        try:
            now = datetime.now(UTC)
            next_run = None

            if quest.recurrence == RecurrenceType.ONCE:
                next_run = now
            elif quest.recurrence == RecurrenceType.DAILY:
                next_run = now
            elif quest.recurrence == RecurrenceType.CUSTOM and quest.cron_expression:
                from croniter import croniter

                try:
                    iter = croniter(quest.cron_expression, now)
                    next_run = iter.get_next(datetime)
                except Exception:
                    pass

            if not next_run:
                next_run = now

            job_id = await redis.enqueue_job("trigger_quest_notification", quest.id, _defer_until=next_run)

            quest.job_id = job_id.job_id

        except Exception as e:
            logger.error(f"Failed to schedule quest {quest.id}: {e}")

    @staticmethod
    async def create_log(db: AsyncSession, quest_id: int, scheduled_for: datetime) -> QuestLog:
        """
        Creates a specific instance (Log) of a Quest to be completed.
        """
        log = QuestLog(quest_id=quest_id, status=QuestStatus.PENDING, scheduled_for=scheduled_for)
        db.add(log)
        await db.commit()
        await db.refresh(log)
        return log

    @staticmethod
    async def get_active_quests(db: AsyncSession, user_id: int) -> List[Quest]:
        """
        Retrieves all active quests for a user.
        """
        stmt = select(Quest).where(Quest.user_id == user_id, Quest.is_active.is_(True))
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_pending_logs(db: AsyncSession, user_id: int) -> List[QuestLog]:
        """
        Retrieves pending quest logs for a user.
        """
        # High Fidelity: Eager load the 'quest' relationship to prevent MissingGreenlet errors
        # when accessing log.quest in async contexts (API serialization).
        stmt = (
            select(QuestLog)
            .options(selectinload(QuestLog.quest))
            .join(Quest)
            .where(Quest.user_id == user_id, QuestLog.status == QuestStatus.PENDING)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def ensure_pending_logs_for_active_quests(db: AsyncSession, user_id: int):
        """
        Ensures all active quests have at least one PENDING log.
        This is for backward compatibility with quests created before immediate log creation logic.
        """
        # Get all active quests for user
        active_quests_stmt = select(Quest).where(Quest.user_id == user_id, Quest.is_active.is_(True))
        active_result = await db.execute(active_quests_stmt)
        active_quests = active_result.scalars().all()

        for quest in active_quests:
            # Check if quest has any PENDING log
            pending_stmt = select(QuestLog).where(QuestLog.quest_id == quest.id, QuestLog.status == QuestStatus.PENDING)
            pending_result = await db.execute(pending_stmt)
            pending_log = pending_result.scalar_one_or_none()

            # If no pending log exists, create one
            if not pending_log:
                await QuestManager.create_log(db=db, quest_id=quest.id, scheduled_for=datetime.now(UTC))
                logger.info(f"Created missing PENDING log for quest {quest.id} ('{quest.title}')")
