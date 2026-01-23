import asyncio
import logging
from typing import Any

import structlog
import uvloop
from arq.worker import Worker

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


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
    from app.core.db.database import async_session
    from app.modules.intelligence.synthesis import DEFAULT_MODEL, ProfileSynthesizer
    
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

