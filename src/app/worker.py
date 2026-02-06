import logging

from arq import run_worker

from src.app.core.db.database import init_db
from src.app.core.scheduler import WorkerSettings

# Ensure logging is configured
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def startup(ctx):
    logger.info("Initializing Worker...")
    await init_db()
    # Any other startup logic (e.g., Redis connections which ARQ handles mostly)


async def shutdown(ctx):
    logger.info("Shutting down Worker...")


# Update settings with specific startup/shutdown if needed,
# though WorkerSettings might already have them.
# We override here to ensure explicit DB init if not in core settings.
WorkerSettings.on_startup = startup
WorkerSettings.on_shutdown = shutdown

if __name__ == "__main__":
    run_worker(WorkerSettings)
