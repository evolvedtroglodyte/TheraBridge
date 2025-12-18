"""
Background job scheduler for analytics aggregation.

This module manages scheduled tasks using APScheduler's AsyncIOScheduler.
Jobs are registered by the background tasks module and run at configured intervals.

Scheduler lifecycle:
    - start_scheduler(): Called on API startup
    - shutdown_scheduler(): Called on API shutdown
    - Jobs are registered separately by background task modules

Configuration:
    ENABLE_ANALYTICS_SCHEDULER: Enable/disable scheduler (default: True)
    DAILY_AGGREGATION_HOUR: Hour (0-23 UTC) to run daily jobs (default: 0)
"""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.config import settings

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = AsyncIOScheduler()


def start_scheduler():
    """
    Start the APScheduler for background analytics jobs.

    This function is called during application startup. It checks the
    ENABLE_ANALYTICS_SCHEDULER setting and starts the scheduler if enabled.

    Jobs must be registered separately before calling this function.
    """
    if not settings.ENABLE_ANALYTICS_SCHEDULER:
        logger.info("Analytics scheduler disabled via config (ENABLE_ANALYTICS_SCHEDULER=False)")
        return

    from app.tasks import register_analytics_jobs, register_export_jobs

    register_analytics_jobs()
    register_export_jobs()
    scheduler.start()
    logger.info("✅ Analytics scheduler started")


def shutdown_scheduler():
    """
    Shutdown the scheduler gracefully.

    This function is called during application shutdown. It waits for
    all running jobs to complete before shutting down.

    The wait=True parameter ensures graceful shutdown by blocking until
    all currently executing jobs finish.
    """
    if scheduler.running:
        scheduler.shutdown(wait=True)
        logger.info("Analytics scheduler shut down")
