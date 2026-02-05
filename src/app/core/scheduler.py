from datetime import datetime, timedelta, UTC
import logging
from typing import Optional

from arq.connections import RedisSettings
from croniter import croniter
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.config import settings
from src.app.core.db.database import local_session as async_session_factory
from src.app.core.events.bus import get_event_bus
from src.app.modules.features.quests.models import Quest, QuestLog, QuestStatus, RecurrenceType
from src.app.modules.infrastructure.push.service import notification_service
from src.app.models.push import PushSubscription
from src.app.modules.tracking.solar.tracker import SolarTracker
from src.app.modules.tracking.lunar.tracker import LunarTracker
from src.app.models.user import User
from src.app.models.progression import PlayerStats
from src.app.modules.features.quests.models import QuestCategory, QuestLog, QuestStatus
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

# Configure Redis settings for ARQ
redis_settings = RedisSettings(
    host=settings.REDIS_QUEUE_HOST,
    port=settings.REDIS_QUEUE_PORT,
    database=0,  # Default to 0 as it's not in settings
    password=settings.REDIS_PASSWORD or None,
)


async def get_db_session() -> AsyncSession:
    async with async_session_factory() as session:
        yield session


async def trigger_quest_notification(ctx, quest_id: int):
    """
    Job to trigger a quest notification and schedule the next occurrence.
    """
    logger.info(f"Executing quest job for Quest ID: {quest_id}")

    async with async_session_factory() as db:
        # 1. Fetch Quest & User (for Timezone)
        stmt = select(Quest).join(User).where(Quest.id == quest_id)
        result = await db.execute(stmt)
        quest = result.scalar_one_or_none()

        if not quest or not quest.is_active:
            logger.info(f"Quest {quest_id} not found or inactive. Stopping chain.")
            return

        # 2. Send Notification
        # Check active subscriptions first for better logging
        stmt_sub = select(func.count(PushSubscription.id)).where(PushSubscription.user_id == quest.user_id)
        sub_count = await db.scalar(stmt_sub)

        if sub_count == 0:
            logger.warning(f"Quest {quest_id}: No push subscriptions found for user {quest.user_id}. Skipping send.")
        else:
            result = await notification_service.send_to_user(
                db=db,
                user_id=quest.user_id,
                title=f"Quest Due: {quest.title}",
                body=quest.description or "Time to complete your quest!",
                url=f"/quests/{quest.id}",  # Deep link
            )
            logger.info(f"Quest {quest_id}: Notification Result: {result}")

        # 3. Create or Retrieve Quest Log (Pending)
        # Check for an existing pending log to ensure idempotency (if Manager created it synchronously)
        # We look for a pending log created recently or just any pending log for this quest?
        # A quest line should mainly have one active pending log at a time in this simple model.
        stmt_log = select(QuestLog).where(QuestLog.quest_id == quest_id, QuestLog.status == QuestStatus.PENDING)
        result_log = await db.execute(stmt_log)
        existing_log = result_log.scalars().first()

        if existing_log:
            logger.info(f"Pending log already exists for Quest {quest_id}. Skipping creation.")
            log = existing_log
        else:
            # Note: We use the *current* time as the scheduled time for this log
            log = QuestLog(quest_id=quest.id, status=QuestStatus.PENDING, scheduled_for=datetime.now(UTC))
            db.add(log)
            await db.commit()

        # 4. Calculate Next Occurrence (The Daisy Chain)
        # If ONCE, we are done.
        if quest.recurrence == RecurrenceType.ONCE:
            logger.info(f"Quest {quest_id} is ONCE. Chain complete.")
            quest.is_active = False  # Or keep active but no job? Usually ONCE implies done.
            quest.job_id = None
            await db.commit()
            return

        # Calculate next run
        # Use User's timezone or UTC
        user_tz = UTC
        if quest.user and quest.user.birth_timezone:  # Assuming user object has birth_timezone or similar
            # Note: user is joined but confirm if explicitly loaded. If yes:
            # Need to convert string tz to timezone object.
            try:
                from zoneinfo import ZoneInfo

                user_tz = ZoneInfo(quest.user.birth_timezone)
            except Exception:
                user_tz = UTC

        # Current time in that timezone
        now = datetime.now(user_tz)
        next_run = None

        if quest.recurrence == RecurrenceType.DAILY:
            next_run = now + timedelta(days=1)
        elif quest.recurrence == RecurrenceType.WEEKLY:
            next_run = now + timedelta(weeks=1)
        elif quest.recurrence == RecurrenceType.MONTHLY:
            # Simple approximation, better to use relativedelta
            next_run = now + timedelta(days=30)
        elif quest.recurrence == RecurrenceType.CUSTOM and quest.cron_expression:
            try:
                iter = croniter(quest.cron_expression, now)
                next_run = iter.get_next(datetime)
            except Exception as e:
                logger.error(f"Invalid cron for Quest {quest_id}: {e}")
                return

        if next_run:
            # Enqueue next job
            # We defer until that time.
            # Convert next_run to delay/timestamp for ARQ?
            # arq uses _defer_until (datetime)

            job_id = await ctx["redis"].enqueue_job("trigger_quest_notification", quest_id, _defer_until=next_run)

            # Update Quest with new job ID
            quest.job_id = job_id
            await db.commit()
            logger.info(f"Scheduled next run for Quest {quest_id} at {next_run} (Job: {job_id})")


async def cosmic_heartbeat(ctx):
    """
    Periodically fetches cosmic data and publishes COSMIC_UPDATE.
    This wakes up the Insight Engine.
    """
    logger.info("Executing Cosmic Heartbeat...")

    try:
        solar = SolarTracker()
        lunar = LunarTracker()

        # 1. Fetch current data
        solar_data = await solar.fetch_current_data()
        lunar_data = await lunar.fetch_current_data()

        # 2. Assemble event data
        # We merge solar and lunar into a single COSMIC_UPDATE event
        event_payload = {
            "kp_index": solar_data.data.get("kp_index", 0),
            "kp_status": solar_data.data.get("kp_status", "Quiet"),
            "solar_flares": solar_data.data.get("solar_flares", []),
            "moon_phase": lunar_data.data.get("phase_name", "Unknown"),
            "moon_illumination": lunar_data.data.get("illumination", 0),
            "moon_event": lunar_data.detect_significant_events(lunar_data, None),  # List of events
            "timestamp": datetime.now(UTC).isoformat(),
        }

        # 3. Publish to EventBus
        # This will trigger the InsightListener and generate reflection prompts
        bus = get_event_bus()
        await bus.publish("cosmic_update", event_payload)
        logger.info(f"Published COSMIC_UPDATE: Kp={event_payload['kp_index']}, Moon={event_payload['moon_phase']}")

    except Exception as e:
        logger.error(f"Error in Cosmic Heartbeat: {e}", exc_info=True)


async def daily_reset_job(ctx):
    """
    Analyzes previous day's performance for all users.
    Calculates WMA Sync Rate, updates streaks, and renews Daily Quests.
    Runs hourly but only executes reset logic if it's midnight for the user.
    """
    logger.info("Executing Daily Reset Check...")

    async with async_session_factory() as db:
        # 1. Fetch all active users
        stmt = select(User).where(User.is_deleted == False)
        result = await db.execute(stmt)
        users = result.scalars().all()

        for user in users:
            try:
                # 2. Determine User's local time
                user_tz_str = user.birth_timezone or "UTC"
                try:
                    user_tz = ZoneInfo(user_tz_str)
                except Exception:
                    user_tz = UTC

                now_local = datetime.now(user_tz)

                # 3. Check if reset is due (Midnight or later today, and last_reset was yesterday)
                stats_stmt = select(PlayerStats).where(PlayerStats.user_id == user.id)
                stats_result = await db.execute(stats_stmt)
                stats = stats_result.scalar_one_or_none()

                if not stats:
                    stats = PlayerStats(user_id=user.id)
                    db.add(stats)
                    await db.commit()
                    await db.refresh(stats)

                # last_reset_at is UTC in DB
                last_reset_local = stats.last_reset_at.astimezone(user_tz) if stats.last_reset_at else None

                # Logic: If now is >= midnight today, and was never reset OR was reset before today's 00:00
                if not last_reset_local or last_reset_local.date() < now_local.date():
                    # PERFORM RESET
                    logger.info(f"Resetting day for user {user.id} (TZ: {user_tz_str})")
                    await _perform_user_daily_reset(db, user, stats, user_tz)

            except Exception as e:
                logger.error(f"Failed to process daily reset for user {user.id}: {e}")

    logger.info("Daily Reset Check complete.")


async def _perform_user_daily_reset(db: AsyncSession, user: User, stats: PlayerStats, tz: ZoneInfo):
    """Internal logic to update WMA and renew quests."""
    # 1. Evaluate yesterday's quests
    # Yesterday in user's TZ: from [now - 24h] start of day to [now - 24h] end of day
    now_local = datetime.now(tz)
    yesterday_local = now_local - timedelta(days=1)

    start_of_yesterday = datetime.combine(yesterday_local.date(), datetime.min.time()).replace(tzinfo=tz)
    end_of_yesterday = datetime.combine(yesterday_local.date(), datetime.max.time()).replace(tzinfo=tz)

    # Query logs scheduled for yesterday
    log_stmt = (
        select(QuestLog)
        .join(Quest)
        .where(
            Quest.user_id == user.id,
            QuestLog.scheduled_for >= start_of_yesterday,
            QuestLog.scheduled_for <= end_of_yesterday,
        )
    )
    result = await db.execute(log_stmt)
    logs = result.scalars().all()

    total = len(logs)
    completed = len([l for l in logs if l.status == QuestStatus.COMPLETED])

    daily_sync = (
        completed / total if total > 0 else 1.0
    )  # Perfect sync if no quests? Or 0? User asked for 1.0-ish logic.

    # 2. Update WMA (7-day Weighted Moving Average)
    # new_wma = (daily_sync * 0.4) + (prev_avg * 0.6)
    stats.sync_rate = (daily_sync * 0.4) + (stats.sync_rate * 0.6)

    # Update History (JSONB)
    history = stats.sync_history.copy() if stats.sync_history else []
    history.append({"date": yesterday_local.date().isoformat(), "score": daily_sync})
    stats.sync_history = history[-7:]  # Keep last 7

    # 3. Streak Evaluation
    if completed > 0:
        stats.streak_count += 1
    else:
        stats.streak_count = 0  # Streak broken

    stats.last_reset_at = datetime.now(UTC)

    # 4. Renew DAILY category quests for TODAY
    daily_quests_stmt = select(Quest).where(
        Quest.user_id == user.id, Quest.category == QuestCategory.DAILY, Quest.is_active == True
    )
    q_result = await db.execute(daily_quests_stmt)
    dailies = q_result.scalars().all()

    for q in dailies:
        # Create new log for today
        log = QuestLog(
            quest_id=q.id,
            status=QuestStatus.PENDING,
            scheduled_for=datetime.now(UTC),  # Or today's start in TZ
        )
        db.add(log)

    await db.commit()
    await db.refresh(stats)


async def startup(ctx):
    """Initialize periodic jobs on worker startup."""
    logger.info("Scheduler worker starting up...")

    # Schedule the first Cosmic Heartbeat immediately
    await ctx["redis"].enqueue_job("cosmic_heartbeat")

    # In production, arq handles periodic jobs via cron, but for now
    # we can daisy-chain it if we don't use CronSettings.
    # Actually, let's use CronSettings for robustness.


async def shutdown(ctx):
    pass


from arq import cron


class WorkerSettings:
    functions = [trigger_quest_notification, cosmic_heartbeat, daily_reset_job]
    cron_jobs = [
        cron(cosmic_heartbeat, hour=None, minute=0, second=0),  # Run every hour on the hour
        cron(daily_reset_job, hour=None, minute=0, second=0),  # Check resets every hour
    ]
    redis_settings = redis_settings
    on_startup = startup
    on_shutdown = shutdown
    allow_abort_jobs = True
