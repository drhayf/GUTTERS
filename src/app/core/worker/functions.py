import asyncio
import logging
from typing import Any

import structlog
from arq.worker import Worker

try:
    import uvloop

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError:
    pass


# -------- background tasks --------
async def sample_background_task(ctx: Worker, name: str) -> str:
    await asyncio.sleep(5)
    return f"Task {name} is complete!"


async def synthesize_profile_job(ctx: Worker, user_id: int, model_id: str | None = None) -> dict:
    """
    Background job for profile synthesis.

    Args:
        ctx: ARQ worker context
        user_id: User ID to synthesize for
        model_id: Optional LLM model override

    Returns:
        Status dict with synthesis result
    """
    from src.app.core.db.database import async_session
    from src.app.modules.intelligence.synthesis import DEFAULT_MODEL, ProfileSynthesizer

    model = model_id or DEFAULT_MODEL

    async with async_session() as db:
        try:
            synthesizer = ProfileSynthesizer(model_id=model)
            synthesis = await synthesizer.synthesize_profile(user_id, db)

            logging.info(f"Synthesis complete for user {user_id} using {model}")

            return {
                "status": "complete",
                "user_id": user_id,
                "model": model,
                "modules_included": synthesis.modules_included,
            }
        except Exception as e:
            logging.error(f"Synthesis failed for user {user_id}: {e}")
            return {
                "status": "error",
                "user_id": user_id,
                "error": str(e),
            }


# -------- base functions --------
async def startup(ctx: Worker) -> None:
    logging.info("Worker Started")


async def shutdown(ctx: Worker) -> None:
    logging.info("Worker end")


async def on_job_start(ctx: dict[str, Any]) -> None:
    structlog.contextvars.bind_contextvars(job_id=ctx["job_id"])
    logging.info("Job Started")


async def on_job_end(ctx: dict[str, Any]) -> None:
    logging.info("Job Competed")
    structlog.contextvars.clear_contextvars()


# -------- tracking jobs --------
async def update_solar_tracking_job(ctx: Worker) -> None:
    """Background job: Update solar tracking (runs hourly)."""
    from src.app.modules.tracking.solar.tracker import SolarTracker
    from src.app.core.db.database import async_session
    from sqlalchemy import select
    from src.app.models.user import User
    import traceback

    tracker = SolarTracker()

    try:
        async with async_session() as db:
            result = await db.execute(select(User))
            users = result.scalars().all()

            for user in users:
                try:
                    await tracker.update(user.id)
                except Exception as e:
                    logging.error(f"Solar tracking failed for user {user.id}: {e}")
                    traceback.print_exc()
    except Exception as e:
        logging.error(f"Solar tracking job failed: {e}")


async def update_lunar_tracking_job(ctx: Worker) -> None:
    """Background job: Update lunar tracking (runs daily)."""
    from src.app.modules.tracking.lunar.tracker import LunarTracker
    from src.app.core.db.database import async_session
    from sqlalchemy import select
    from src.app.models.user import User
    import traceback

    tracker = LunarTracker()

    try:
        async with async_session() as db:
            result = await db.execute(select(User))
            users = result.scalars().all()

            for user in users:
                try:
                    await tracker.update(user.id)
                except Exception as e:
                    logging.error(f"Lunar tracking failed for user {user.id}: {e}")
                    traceback.print_exc()
    except Exception as e:
        logging.error(f"Lunar tracking job failed: {e}")


async def update_transit_tracking_job(ctx: Worker) -> None:
    """Background job: Update transit tracking (runs daily)."""
    from src.app.modules.tracking.transits.tracker import TransitTracker
    from src.app.core.db.database import async_session
    from sqlalchemy import select
    from src.app.models.user import User
    import traceback

    tracker = TransitTracker()

    try:
        async with async_session() as db:
            result = await db.execute(select(User))
            users = result.scalars().all()

            for user in users:
                try:
                    await tracker.update(user.id)
                except Exception as e:
                    logging.error(f"Transit tracking failed for user {user.id}: {e}")
                    traceback.print_exc()
    except Exception as e:
        logging.error(f"Transit tracking job failed: {e}")


async def observer_analysis_job(ctx: Worker) -> None:
    """
    Background job: Run Observer analysis for all users.

    Runs daily to detect new patterns.
    """
    from src.app.modules.intelligence.observer.observer import Observer
    from src.app.modules.intelligence.observer.storage import ObserverFindingStorage
    from src.app.core.db.database import async_session
    from sqlalchemy import select
    from src.app.models.user import User
    import traceback

    observer = Observer()
    storage = ObserverFindingStorage()

    try:
        async with async_session() as db:
            result = await db.execute(select(User))
            users = result.scalars().all()

            for user in users:
                try:
                    # Run all correlation analyses
                    solar_findings = await observer.detect_solar_correlations(user.id, db)
                    lunar_findings = await observer.detect_lunar_correlations(user.id, db)
                    transit_findings = await observer.detect_transit_correlations(user.id, db)
                    time_findings = await observer.detect_time_based_patterns(user.id, db)

                    # Store all findings
                    all_findings = solar_findings + lunar_findings + transit_findings + time_findings

                    for finding in all_findings:
                        await storage.store_finding(user.id, finding, db)

                    logging.info(f"[Observer] Analyzed user {user.id}: {len(all_findings)} findings")

                except Exception as e:
                    logging.error(f"[Observer] Error analyzing user {user.id}: {e}")
                    traceback.print_exc()
    except Exception as e:
        logging.error(f"[Observer] Analysis job failed: {e}")
        traceback.print_exc()


async def generate_hypotheses_job(ctx: Worker) -> None:
    """
    Background job: Generate theories from Observer patterns.

    Runs daily after Observer analysis (at 2am).
    """
    from src.app.modules.intelligence.hypothesis.generator import HypothesisGenerator
    from src.app.modules.intelligence.hypothesis.storage import HypothesisStorage
    from src.app.modules.intelligence.observer.storage import ObserverFindingStorage
    from src.app.modules.intelligence.synthesis.synthesizer import DEFAULT_MODEL
    from src.app.core.ai.llm_factory import get_llm
    from src.app.core.db.database import async_session
    from sqlalchemy import select
    from src.app.models.user import User
    import traceback

    llm = get_llm(DEFAULT_MODEL)
    generator = HypothesisGenerator(llm)
    storage = HypothesisStorage()
    observer_storage = ObserverFindingStorage()

    try:
        async with async_session() as db:
            result = await db.execute(select(User))
            users = result.scalars().all()

            for user in users:
                try:
                    # 1. Get Observer patterns
                    patterns = await observer_storage.get_findings(user.id, min_confidence=0.7)

                    if not patterns:
                        continue

                    # 2. Generate hypotheses
                    hypotheses = await generator.generate_from_patterns(user.id, patterns)

                    # 3. Store
                    for hypothesis in hypotheses:
                        await storage.store_hypothesis(hypothesis, db)

                    logging.info(f"[Hypothesis] Generated {len(hypotheses)} theories for user {user.id}")

                except Exception as e:
                    logging.error(f"[Hypothesis] Error for user {user.id}: {e}")
                    traceback.print_exc()
    except Exception as e:
        logging.error(f"[Hypothesis] Daily generation job failed: {e}")
        traceback.print_exc()


async def populate_embeddings_job(ctx: Worker) -> None:
    """
    Background job: Generate embeddings for all user content.

    Runs daily to embed:
    - New journal entries
    - New Observer findings
    - New hypotheses
    """
    from src.app.modules.intelligence.vector.embedding_service import EmbeddingService
    from src.app.models.embedding import Embedding
    from src.app.models.user_profile import UserProfile
    from src.app.models.user import User
    from src.app.core.db.database import local_session
    from src.app.core.config import settings
    from sqlalchemy import select
    import traceback

    service = EmbeddingService(settings.OPENROUTER_API_KEY.get_secret_value())

    try:
        async with local_session() as db:
            result = await db.execute(select(User))
            users = result.scalars().all()

            for user in users:
                try:
                    # Get user profile
                    profile_result = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
                    profile = profile_result.scalar_one_or_none()

                    if not profile:
                        continue

                    embeddings_created = 0

                    # 1. JOURNAL ENTRIES
                    journal_entries = profile.data.get("journal_entries", [])
                    for entry in journal_entries:
                        # Check if already embedded
                        entry_id = entry.get("id")
                        if not entry_id:
                            continue

                        exists_stmt = select(Embedding).where(
                            Embedding.user_id == user.id, Embedding.content_metadata["entry_id"].astext == str(entry_id)
                        )
                        exists_result = await db.execute(exists_stmt)
                        if exists_result.scalar_one_or_none():
                            continue

                        embedded = await service.embed_journal_entry(entry)
                        db.add(
                            Embedding(
                                user_id=user.id,
                                content=embedded["content"],
                                embedding=embedded["embedding"],
                                content_metadata=embedded["content_metadata"],
                            )
                        )
                        embeddings_created += 1

                    # 2. OBSERVER FINDINGS
                    observer_findings = profile.data.get("observer_findings", [])
                    for finding in observer_findings:
                        finding_id = finding.get("id")
                        if not finding_id:
                            continue

                        exists_stmt = select(Embedding).where(
                            Embedding.user_id == user.id,
                            Embedding.content_metadata["finding_id"].astext == str(finding_id),
                        )
                        exists_result = await db.execute(exists_stmt)
                        if exists_result.scalar_one_or_none():
                            continue

                        embedded = await service.embed_observer_finding(finding)
                        db.add(
                            Embedding(
                                user_id=user.id,
                                content=embedded["content"],
                                embedding=embedded["embedding"],
                                content_metadata=embedded["content_metadata"],
                            )
                        )
                        embeddings_created += 1

                    # 3. HYPOTHESES
                    hypotheses = profile.data.get("hypotheses", [])
                    for hypothesis in hypotheses:
                        hyp_id = hypothesis.get("id")
                        if not hyp_id:
                            continue

                        exists_stmt = select(Embedding).where(
                            Embedding.user_id == user.id,
                            Embedding.content_metadata["hypothesis_id"].astext == str(hyp_id),
                        )
                        exists_result = await db.execute(exists_stmt)
                        if exists_result.scalar_one_or_none():
                            continue

                        embedded = await service.embed_hypothesis(hypothesis)
                        db.add(
                            Embedding(
                                user_id=user.id,
                                content=embedded["content"],
                                embedding=embedded["embedding"],
                                content_metadata=embedded["content_metadata"],
                            )
                        )
                        embeddings_created += 1

                    if embeddings_created > 0:
                        await db.commit()
                        logging.info(f"[Embeddings] Created {embeddings_created} embeddings for user {user.id}")

                except Exception as e:
                    logging.error(f"[Embeddings] Error for user {user.id}: {e}")
                    await db.rollback()
                    traceback.print_exc()

    except Exception as e:
        logging.error(f"[Embeddings] Population job failed: {e}")
        traceback.print_exc()


# -------- chronos (cardology) jobs --------
async def daily_chronos_update_job(ctx: Worker) -> None:
    """
    Background job: Update Chronos state for all users.
    
    Runs daily to:
    - Refresh planetary period calculations
    - Detect period boundary crossings (52-day cycles)
    - Detect year boundary crossings (birthdays)
    - Emit MAGI_PERIOD_SHIFT and MAGI_YEAR_SHIFT events
    - Update Redis cache and UserProfile persistence
    
    Schedule: Daily at 4:00 AM UTC (after embeddings job)
    """
    from src.app.core.state.chronos import get_chronos_manager
    from src.app.core.db.database import async_session
    from sqlalchemy import select
    from src.app.models.user import User
    import traceback
    
    manager = get_chronos_manager()
    
    try:
        async with async_session() as db:
            result = await db.execute(select(User))
            users = result.scalars().all()
            
            updated_count = 0
            shift_count = 0
            
            for user in users:
                try:
                    # User must have birth_date for Cardology calculations
                    if not hasattr(user, 'birth_date') or not user.birth_date:
                        continue
                    
                    # Get current cached state for comparison
                    old_state = await manager.get_user_chronos(user.id)
                    
                    # Refresh state (this handles shift detection and events)
                    new_state = await manager.refresh_user_chronos(
                        user_id=user.id,
                        birth_date=user.birth_date
                    )
                    
                    updated_count += 1
                    
                    # Check if a shift occurred
                    if old_state:
                        old_period = old_state.get("period_number")
                        new_period = new_state.get("period_number")
                        if old_period != new_period:
                            shift_count += 1
                            logging.info(
                                f"[Chronos] Period shift for user {user.id}: "
                                f"Period {old_period} → {new_period}"
                            )
                    
                except Exception as e:
                    logging.error(f"[Chronos] Update failed for user {user.id}: {e}")
                    traceback.print_exc()
            
            logging.info(
                f"[Chronos] Daily update complete: "
                f"{updated_count} users updated, {shift_count} period shifts detected"
            )
            
    except Exception as e:
        logging.error(f"[Chronos] Daily update job failed: {e}")
        traceback.print_exc()
