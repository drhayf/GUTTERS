import asyncio
import logging
from datetime import UTC, datetime

from sqlalchemy import select

from src.app.core.db.database import async_get_db
from src.app.core.events.bus import get_event_bus
from src.app.models.user import User
from src.app.modules.intelligence.hypothesis.generator import HypothesisGenerator
from src.app.modules.intelligence.hypothesis.storage import HypothesisStorage
from src.app.modules.intelligence.observer.observer import Observer
from src.app.modules.tracking.lunar.tracker import LunarTracker
from src.app.modules.tracking.solar.tracker import SolarTracker
from src.app.modules.tracking.transits.tracker import TransitTracker

logger = logging.getLogger(__name__)


class MockLLM:
    """Mock LLM for HypothesisGenerator dependency injection."""

    async def ainvoke(self, *args, **kwargs):
        return "Mock response"


class DataIngestionWorker:
    """
    Background worker that runs periodically to:
    1. Ingest cosmic data (Transits, Solar, Lunar)
    2. Update user tracking history
    3. Run Intelligence Layer (Observer analysis)
    4. Generate/Update Hypotheses
    """

    def __init__(self):
        self.is_running = False
        self.interval_seconds = 3600  # Run every hour

    async def start(self):
        """Start the background worker loop."""
        self.is_running = True
        logger.info("Starting Data Ingestion Worker...")
        bus = get_event_bus()
        try:
            await bus.publish("worker.status", {"message": "Data Ingestion Worker STARTED", "status": "UP"})
        except Exception:
            pass
        asyncio.create_task(self._run_loop())

    async def stop(self):
        """Stop the background worker."""
        logger.info("Stopping Data Ingestion Worker...")
        self.is_running = False
        bus = get_event_bus()
        try:
            await bus.publish("worker.status", {"message": "Data Ingestion Worker STOPPED", "status": "DOWN"})
        except Exception:
            pass

    async def _run_loop(self):
        """Main worker loop."""
        while self.is_running:
            try:
                await self._process_cycle()
            except Exception as e:
                logger.error(f"Error in Data Ingestion Worker: {e}", exc_info=True)

            # Wait for next cycle
            await asyncio.sleep(self.interval_seconds)

    async def _process_cycle(self):
        """
        Execute one complete intelligence cycle.
        """
        logger.info(f"Running intelligence cycle at {datetime.now(UTC)}")
        bus = get_event_bus()
        try:
            await bus.publish(
                "worker.cycle.start",
                {"message": "Intelligence cycle initiated", "timestamp": datetime.now(UTC).isoformat()},
            )
        except Exception:
            pass

        # 1. Initialize Trackers
        transit_tracker = TransitTracker()
        solar_tracker = SolarTracker()
        lunar_tracker = LunarTracker()

        # Observer & Intelligence components
        observer = Observer()

        # Generator requires LLM, but pattern generation is deterministic.
        # We pass a mock to satisfy __init__.
        hyp_generator = HypothesisGenerator(MockLLM())
        hyp_storage = HypothesisStorage()

        try:
            # 2. Iterate Users
            async for db in async_get_db():
                result = await db.execute(select(User))
                users = result.scalars().all()

                for user in users:
                    try:
                        user_id = user.id
                        logger.debug(f"Processing user {user_id}")

                        # --- A. Data Ingestion ---
                        # Fetch and store latest cosmic data for this user
                        await transit_tracker.update(user_id)
                        await solar_tracker.update(user_id)
                        await lunar_tracker.update(user_id)

                        # --- B. Observation (Pattern Detection) ---
                        # Detect patterns in the newly updated history
                        patterns = []
                        # Run sequentially to be safe
                        patterns.extend(await observer.detect_solar_correlations(user_id, db))
                        patterns.extend(await observer.detect_lunar_correlations(user_id, db))
                        patterns.extend(await observer.detect_time_based_patterns(user_id, db))
                        patterns.extend(await observer.detect_transit_correlations(user_id, db))

                        if patterns:
                            logger.info(f"Observer detected {len(patterns)} patterns for user {user_id}")

                            # --- C. Hypothesis Generation ---
                            hypotheses = await hyp_generator.generate_from_patterns(user_id, patterns)

                            if hypotheses:
                                logger.info(f"Generated {len(hypotheses)} hypotheses for user {user_id}")
                                try:
                                    await bus.publish(
                                        "intelligence.hypothesis.generated",
                                        {
                                            "message": f"Generated {len(hypotheses)} potential hypotheses",
                                            "user_id": user_id,
                                            "count": len(hypotheses),
                                        },
                                        user_id=str(user_id),
                                    )
                                except Exception:
                                    pass

                            # --- D. Hypothesis Storage (with de-duplication) ---
                            existing_hypotheses = await hyp_storage.get_hypotheses(user_id)
                            existing_claims = {h.claim for h in existing_hypotheses}

                            for h in hypotheses:
                                if h.claim not in existing_claims:
                                    logger.info(f"Generated NEW hypothesis: {h.claim}")
                                    await hyp_storage.store_hypothesis(h, db)
                                else:
                                    logger.debug(f"Skipping duplicate hypothesis: {h.claim}")

                    except Exception as ue:
                        logger.error(f"Failed to process user {user.id}: {ue}")

                # We only need one db session iteration
                # (Assuming standard asyncio session handling)
                break

        except Exception as e:
            logger.error(f"Error in intelligence cycle: {e}")
            try:
                await bus.publish("worker.error", {"message": f"Cycle error: {str(e)}"})
            except Exception:
                pass

        logger.info("Intelligence cycle complete")
        try:
            await bus.publish("worker.cycle.end", {"message": "Intelligence cycle complete"})
        except Exception:
            pass


worker = DataIngestionWorker()
