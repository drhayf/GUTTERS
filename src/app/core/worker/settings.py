import asyncio
from typing import cast

from arq.cli import watch_reload
from arq.connections import RedisSettings
from arq.cron import cron
from arq.typing import WorkerSettingsType
from arq.worker import check_health, run_worker

from ...core.config import settings
from ...core.logger import logging  # noqa: F401
from .functions import (
    daily_chronos_update_job,
    generate_hypotheses_job,
    observer_analysis_job,
    on_job_end,
    on_job_start,
    populate_embeddings_job,
    sample_background_task,
    shutdown,
    startup,
    synthesize_profile_job,
    update_lunar_tracking_job,
    update_solar_tracking_job,
    update_transit_tracking_job,
)

REDIS_QUEUE_HOST = settings.REDIS_QUEUE_HOST
REDIS_QUEUE_PORT = settings.REDIS_QUEUE_PORT
REDIS_PASSWORD = settings.REDIS_PASSWORD


class WorkerSettings:
    functions = [
        sample_background_task,
        synthesize_profile_job,
        update_solar_tracking_job,
        update_lunar_tracking_job,
        update_lunar_tracking_job,
        update_transit_tracking_job,
        observer_analysis_job,
        generate_hypotheses_job,
        populate_embeddings_job,
        daily_chronos_update_job,
    ]
    redis_settings = RedisSettings(
        host=REDIS_QUEUE_HOST,
        port=REDIS_QUEUE_PORT,
        password=REDIS_PASSWORD,
        ssl=settings.REDIS_QUEUE_SSL,
    )
    cron_jobs = [
        cron(
            update_solar_tracking_job,
            hour={0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23},
        ),
        cron(update_lunar_tracking_job, hour=0, minute=0),
        cron(update_transit_tracking_job, hour=0, minute=30),
        cron(observer_analysis_job, hour=1, minute=0),
        cron(generate_hypotheses_job, hour=2, minute=0),
        cron(populate_embeddings_job, hour=3, minute=0),
        cron(daily_chronos_update_job, hour=4, minute=0),  # After embeddings, detect period shifts
    ]
    on_startup = startup
    on_shutdown = shutdown
    on_job_start = on_job_start
    on_job_end = on_job_end
    handle_signals = False


def start_arq_service(check: bool = False, burst: int | None = None, watch: str | None = None):
    worker_settings_ = cast("WorkerSettingsType", WorkerSettings)

    if check:
        exit(check_health(worker_settings_))
    else:
        kwargs = {} if burst is None else {"burst": burst}
        if watch:
            asyncio.run(watch_reload(watch, worker_settings_))
        else:
            run_worker(worker_settings_, **kwargs)


if __name__ == "__main__":
    start_arq_service()
    # python -m src.app.core.worker.settings
