# src/app/core/startup/tracking.py
"""
Tracking module initialization on application startup.

Ensures tracking data is available immediately when users first access the app.
"""

import asyncio

import structlog
from sqlalchemy import select

from ...models.user import User
from ...modules.tracking.lunar.tracker import LunarTracker
from ...modules.tracking.solar.tracker import SolarTracker
from ..db.database import local_session

logger = structlog.get_logger(__name__)


async def initialize_tracking_data() -> None:
    """
    Initialize tracking data for all users on app startup.

    Runs in background to avoid blocking app initialization.
    Updates solar and lunar tracking for all users to ensure
    fresh data is available on first page load.
    """
    try:
        logger.info("Starting tracking data initialization...")

        solar_tracker = SolarTracker()
        lunar_tracker = LunarTracker()

        # Get all active users
        async with local_session() as db:
            result = await db.execute(select(User.id))
            user_ids = [row[0] for row in result.fetchall()]

        if not user_ids:
            logger.info("No users found, skipping tracking initialization")
            return

        logger.info(f"Initializing tracking for {len(user_ids)} users")

        # Update tracking for each user (run concurrently for efficiency)
        update_tasks = []
        for user_id in user_ids:
            update_tasks.append(_update_user_tracking(user_id, solar_tracker, lunar_tracker))

        # Run all updates concurrently with a reasonable limit
        # Process in batches of 10 to avoid overwhelming the system
        batch_size = 10
        for i in range(0, len(update_tasks), batch_size):
            batch = update_tasks[i : i + batch_size]
            await asyncio.gather(*batch, return_exceptions=True)

        logger.info("✅ Tracking data initialization complete")

    except Exception as e:
        logger.error(f"Error initializing tracking data: {e}", exc_info=True)


async def _update_user_tracking(
    user_id: int, solar_tracker: SolarTracker, lunar_tracker: LunarTracker
) -> None:
    """Update tracking data for a single user."""
    try:
        # Update solar and lunar tracking
        await solar_tracker.update(user_id)
        await lunar_tracker.update(user_id)
        logger.debug(f"Updated tracking for user {user_id}")
    except Exception as e:
        logger.warning(f"Failed to update tracking for user {user_id}: {e}")

