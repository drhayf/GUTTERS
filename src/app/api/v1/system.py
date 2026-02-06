"""
GUTTERS System Control API

Endpoints for system configuration, worker management, and global status.
Only accessible to superusers.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from src.app.api.dependencies import get_current_superuser
from src.app.core.llm.config import LLMConfig, LLMTier, ModelConfig
from src.app.core.worker.ingestion import worker

router = APIRouter(prefix="/system", tags=["system"])


class ModelUpdateSchema(BaseModel):
    tier: LLMTier
    model_id: str
    temperature: float = 0.7
    max_tokens: int = 4000
    cost_per_1k_input: float
    cost_per_1k_output: float


@router.get("/status", dependencies=[Depends(get_current_superuser)])
async def get_system_status() -> dict[str, Any]:
    """Get global system status including worker state and AI configs."""

    # Get current model configs
    models = {}
    for tier, config in LLMConfig.MODELS.items():
        models[tier.value] = {
            "model_id": config.model_id,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "cost_per_1k_input": config.cost_per_1k_input,
            "cost_per_1k_output": config.cost_per_1k_output,
        }

    return {
        "worker": {
            "is_running": worker.is_running,
            "interval_seconds": worker.interval_seconds,
        },
        "ai_config": {
            "models": models,
            "exchange_rate": LLMConfig.AUD_EXCHANGE_RATE,
        },
    }


@router.put("/config/ai", dependencies=[Depends(get_current_superuser)])
async def update_ai_config(update: ModelUpdateSchema) -> dict[str, Any]:
    """
    Update LLM configuration for a specific tier and persist to database.
    """
    from sqlalchemy import select

    from ...core.db.database import local_session
    from ...models.system_configuration import SystemConfiguration

    try:
        new_config = ModelConfig(
            model_id=update.model_id,
            temperature=update.temperature,
            max_tokens=update.max_tokens,
            cost_per_1k_input=update.cost_per_1k_input,
            cost_per_1k_output=update.cost_per_1k_output,
        )

        # Update in-memory
        LLMConfig.MODELS[update.tier] = new_config

        # Persist to database
        async with local_session() as db:
            result = await db.execute(
                select(SystemConfiguration).where(SystemConfiguration.module_name == "llm_config")
            )
            sys_config = result.scalar_one_or_none()

            if not sys_config:
                sys_config = SystemConfiguration(
                    module_name="llm_config", config={"models": {}, "exchange_rate": LLMConfig.AUD_EXCHANGE_RATE}
                )
                db.add(sys_config)

            # Ensure 'models' is in config
            if "models" not in sys_config.config:
                sys_config.config["models"] = {}

            # Update specific tier
            sys_config.config["models"][update.tier.value] = new_config.to_dict()

            # Use flag_modified if using JSONB to ensure update detection
            from sqlalchemy.orm.attributes import flag_modified

            flag_modified(sys_config, "config")

            await db.commit()

        # Optimization: Force reload from DB to ensure consistency across async context
        await LLMConfig.initialize_from_db()

        return {
            "message": f"Successfully updated {update.tier} model to {update.model_id} and persisted to database.",
            "config": {"model_id": new_config.model_id, "tier": update.tier.value},
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update AI config: {str(e)}"
        )


@router.post("/worker/{action}", dependencies=[Depends(get_current_superuser)])
async def control_worker(action: str) -> dict[str, Any]:
    """Control the background DataIngestionWorker."""

    if action == "start":
        if worker.is_running:
            return {"message": "Worker is already running"}
        await worker.start()
        return {"message": "Worker started successfully"}

    elif action == "stop":
        if not worker.is_running:
            return {"message": "Worker is already stopped"}
        await worker.stop()
        return {"message": "Worker stopped successfully"}

    elif action == "restart":
        await worker.stop()
        await worker.start()
        return {"message": "Worker restarted successfully"}

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid action: {action}. Must be start, stop, or restart.",
        )
