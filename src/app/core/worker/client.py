from arq import create_pool
from arq.connections import ArqRedis

from src.app.core.worker.settings import WorkerSettings

# Singleton pool instance
_arq_pool: ArqRedis | None = None


async def get_arq_pool() -> ArqRedis:
    """
    Get the singleton ARQ Redis pool instance.

    Returns:
        ArqRedis instance for enqueuing jobs.
    """
    global _arq_pool
    if _arq_pool is None:
        _arq_pool = await create_pool(WorkerSettings.redis_settings)
    return _arq_pool
