"""
Analytics Aggregation Background Tasks

Provides scheduled job functions for daily/weekly analytics data aggregation.
These jobs run automatically via APScheduler to pre-compute metrics for the
analytics dashboard.

Jobs:
    - aggregate_daily_stats: Daily aggregation of session metrics per therapist
    - snapshot_patient_progress: Weekly snapshots of patient goal completion

Design Principles:
    - Idempotent: Safe to run multiple times (uses upsert pattern)
    - Efficient: Uses database-level aggregation (GROUP BY, COUNT, AVG)
    - Fault-tolerant: Comprehensive error logging and recovery
    - Timezone-aware: All calculations in UTC
"""

import logging
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy import select, func, and_, distinct
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.db_models import TherapySession, User
from app.models.analytics_models import DailyStats, PatientProgress
from app.config import settings

logger = logging.getLogger(__name__)


async def aggregate_daily_stats() -> Dict[str, int]:
    """
    Aggregate yesterday's session data into daily_stats table.

    Runs daily at configured hour (default: midnight UTC).
    Computes per-therapist statistics for the previous day and stores
    them in the daily_stats table using PostgreSQL upsert pattern
    for idempotency.

    Metrics Aggregated:
        - total_sessions: Count of therapy sessions completed
        - total_patients_seen: Count of distinct patients seen
        - avg_session_duration: Average session duration in minutes

    Returns:
        Dict with counts: {"therapists_processed": N, "total_sessions": N}

    Example:
        >>> result = await aggregate_daily_stats()
        >>> print(f"Processed {result['therapists_processed']} therapists")

    Database Operations:
        1. Calculate yesterday's date range (00:00:00 to 23:59:59 UTC)
        2. Query therapy_sessions grouped by therapist_id
        3. Use INSERT ... ON CONFLICT for upsert (safe for reruns)
        4. Log results and errors

    Edge Cases:
        - No sessions yesterday: Skips aggregation, logs info
        - Therapist with 0 sessions: Not inserted (only active therapists)
        - Null duration_seconds: Excluded from avg calculation
        - Failed sessions: Excluded (status != 'failed')

    PostgreSQL Upsert:
        Uses ON CONFLICT DO UPDATE to handle duplicate (therapist_id, stat_date)
        combinations. This ensures the job is idempotent and can safely rerun.
    """
    logger.info("Starting daily stats aggregation job")

    therapists_processed = 0
    total_sessions = 0

    async with AsyncSessionLocal() as db:
        try:
            # Calculate yesterday's date range
            today = datetime.utcnow().date()
            yesterday = today - timedelta(days=1)

            # Date boundaries for query
            start_of_yesterday = datetime.combine(yesterday, datetime.min.time())
            end_of_yesterday = datetime.combine(yesterday, datetime.max.time())

            logger.info(
                f"Aggregating stats for {yesterday} "
                f"(range: {start_of_yesterday} to {end_of_yesterday})"
            )

            # Query: Aggregate session metrics grouped by therapist_id
            # Filters:
            #   - session_date within yesterday
            #   - status != 'failed' (only successful sessions)
            #   - therapist_id is not null
            stats_query = select(
                TherapySession.therapist_id,
                func.count(TherapySession.id).label('total_sessions'),
                func.count(distinct(TherapySession.patient_id)).label('total_patients_seen'),
                func.avg(TherapySession.duration_seconds / 60.0).label('avg_duration_minutes')
            ).where(
                and_(
                    TherapySession.session_date >= start_of_yesterday,
                    TherapySession.session_date <= end_of_yesterday,
                    TherapySession.status != 'failed',
                    TherapySession.therapist_id.isnot(None)
                )
            ).group_by(TherapySession.therapist_id)

            result = await db.execute(stats_query)
            rows = result.fetchall()

            if not rows:
                logger.info(
                    f"No sessions found for {yesterday}. "
                    "Skipping aggregation (no data to insert)."
                )
                return {
                    "therapists_processed": 0,
                    "total_sessions": 0,
                    "stat_date": str(yesterday)
                }

            # Insert aggregated stats using upsert pattern
            for row in rows:
                therapist_id = row.therapist_id
                sessions_count = row.total_sessions
                patients_count = row.total_patients_seen
                avg_duration = round(float(row.avg_duration_minutes), 2) if row.avg_duration_minutes else None

                # PostgreSQL upsert: INSERT ... ON CONFLICT DO UPDATE
                # This ensures idempotency - safe to run multiple times
                stmt = pg_insert(DailyStats).values(
                    therapist_id=therapist_id,
                    stat_date=yesterday,
                    total_sessions=sessions_count,
                    total_patients_seen=patients_count,
                    avg_session_duration=avg_duration,
                    created_at=datetime.utcnow()
                )

                # On conflict (duplicate therapist_id + stat_date), update values
                stmt = stmt.on_conflict_do_update(
                    index_elements=['therapist_id', 'stat_date'],
                    set_={
                        'total_sessions': stmt.excluded.total_sessions,
                        'total_patients_seen': stmt.excluded.total_patients_seen,
                        'avg_session_duration': stmt.excluded.avg_session_duration,
                        # Note: created_at stays as original, no updated_at field
                    }
                )

                await db.execute(stmt)

                therapists_processed += 1
                total_sessions += sessions_count

                logger.debug(
                    f"Aggregated stats for therapist {therapist_id}: "
                    f"sessions={sessions_count}, patients={patients_count}, "
                    f"avg_duration={avg_duration} min"
                )

            # Commit all inserts/updates
            await db.commit()

            logger.info(
                f"✅ Daily stats aggregation complete: "
                f"processed {therapists_processed} therapists, "
                f"{total_sessions} total sessions for {yesterday}"
            )

            return {
                "therapists_processed": therapists_processed,
                "total_sessions": total_sessions,
                "stat_date": str(yesterday)
            }

        except Exception as e:
            logger.error(
                f"❌ Error during daily stats aggregation: {str(e)}",
                exc_info=True
            )
            await db.rollback()
            raise


async def snapshot_patient_progress() -> Dict[str, int]:
    """
    Create weekly progress snapshots for all active patients.

    Runs weekly on Sundays at 1:00 AM UTC.
    Calculates goal completion metrics from therapy session notes and
    stores snapshots in patient_progress table for trend analysis.

    Metrics Calculated:
        - goals_total: Total action items assigned (from extracted_notes JSONB)
        - goals_completed: Completed action items (from extracted_notes JSONB)
        - action_items_total: Same as goals_total (for schema compatibility)
        - action_items_completed: Same as goals_completed
        - overall_progress_score: Completion ratio (completed / total)

    Returns:
        Dict with counts: {"patients_processed": N, "total_goals": N}

    Example:
        >>> result = await snapshot_patient_progress()
        >>> print(f"Processed {result['patients_processed']} patients")

    Database Operations:
        1. Find all patients with at least one session
        2. For each patient, query all sessions
        3. Extract action_items from extracted_notes JSONB
        4. Count total and completed items
        5. Insert snapshot with current date

    Edge Cases:
        - Patients with no sessions: Skipped (not included)
        - Sessions with no extracted_notes: Skipped
        - Action items with no status: Counted as "not started"
        - No action items across all sessions: Creates snapshot with zeros

    JSONB Structure:
        extracted_notes: {
            "action_items": [
                {
                    "task": "Practice deep breathing",
                    "category": "homework",
                    "details": "...",
                    "status": "completed"  // Optional field
                },
                ...
            ]
        }

    Note on Status Tracking:
        Currently, the ExtractedNotes schema doesn't include a 'status' field
        on ActionItem objects. All items are counted as "not started" until
        we implement cross-session action item tracking.

        Future Enhancement: Match action items across sessions by task text
        similarity to detect completion mentioned in follow-up sessions.
    """
    logger.info("Starting weekly patient progress snapshot job")

    patients_processed = 0
    total_goals = 0

    async with AsyncSessionLocal() as db:
        try:
            # Use today's date for snapshot
            snapshot_date = datetime.utcnow().date()

            logger.info(f"Creating progress snapshots for date: {snapshot_date}")

            # Find all patients with at least one therapy session
            # Group by patient_id to get unique patients
            active_patients_query = select(
                distinct(TherapySession.patient_id)
            ).where(
                TherapySession.patient_id.isnot(None)
            )

            result = await db.execute(active_patients_query)
            patient_ids = [row[0] for row in result.fetchall()]

            logger.info(f"Found {len(patient_ids)} patients with session history")

            if not patient_ids:
                logger.info("No patients found. Skipping snapshot creation.")
                return {
                    "patients_processed": 0,
                    "total_goals": 0,
                    "snapshot_date": str(snapshot_date)
                }

            # Process each patient
            for patient_id in patient_ids:
                # Fetch all sessions for this patient
                sessions_query = select(TherapySession).where(
                    and_(
                        TherapySession.patient_id == patient_id,
                        TherapySession.extracted_notes.isnot(None)
                    )
                )

                sessions_result = await db.execute(sessions_query)
                sessions = sessions_result.scalars().all()

                if not sessions:
                    logger.debug(f"Patient {patient_id} has no sessions with extracted_notes")
                    continue

                # Calculate goal statistics from action_items in JSONB
                goals_total_count = 0
                goals_completed_count = 0

                for session in sessions:
                    if not session.extracted_notes:
                        continue

                    # Extract action_items array from JSONB
                    action_items = session.extracted_notes.get('action_items', [])

                    if not isinstance(action_items, list):
                        continue

                    for item in action_items:
                        if not isinstance(item, dict):
                            continue

                        goals_total_count += 1

                        # Check if action item has status field
                        # Note: Current schema doesn't include status, but we check
                        # for future compatibility
                        status = item.get('status', 'not_started')

                        if status == 'completed':
                            goals_completed_count += 1

                # Calculate overall progress score (0.00 to 1.00)
                if goals_total_count > 0:
                    progress_score = round(goals_completed_count / goals_total_count, 2)
                else:
                    progress_score = 0.0

                # Insert progress snapshot
                # Note: We don't use upsert here because each snapshot is unique by date
                # Multiple runs on same day would create duplicate entries, which is acceptable
                # for historical tracking. Could add upsert if needed.
                snapshot = PatientProgress(
                    patient_id=patient_id,
                    snapshot_date=snapshot_date,
                    goals_total=goals_total_count,
                    goals_completed=goals_completed_count,
                    action_items_total=goals_total_count,  # Same as goals for now
                    action_items_completed=goals_completed_count,
                    overall_progress_score=progress_score,
                    created_at=datetime.utcnow()
                )

                db.add(snapshot)

                patients_processed += 1
                total_goals += goals_total_count

                logger.debug(
                    f"Created snapshot for patient {patient_id}: "
                    f"total={goals_total_count}, completed={goals_completed_count}, "
                    f"score={progress_score}"
                )

            # Commit all snapshots
            await db.commit()

            logger.info(
                f"✅ Patient progress snapshot complete: "
                f"processed {patients_processed} patients, "
                f"{total_goals} total goals tracked for {snapshot_date}"
            )

            return {
                "patients_processed": patients_processed,
                "total_goals": total_goals,
                "snapshot_date": str(snapshot_date)
            }

        except Exception as e:
            logger.error(
                f"❌ Error during patient progress snapshot: {str(e)}",
                exc_info=True
            )
            await db.rollback()
            raise


def register_analytics_jobs(scheduler) -> None:
    """
    Register all analytics background jobs with APScheduler.

    Called during application startup (in app/main.py lifespan handler).
    Adds scheduled jobs with CronTrigger schedules to the provided scheduler
    instance.

    Args:
        scheduler: AsyncIOScheduler instance to register jobs with

    Jobs Registered:
        1. daily_stats_aggregation: Runs daily at configured hour (default: 00:00 UTC)
        2. weekly_progress_snapshot: Runs weekly on Sundays at 01:00 UTC

    Configuration:
        - Daily aggregation hour: settings.DAILY_AGGREGATION_HOUR (default: 0)
        - Jobs use 'replace_existing=True' for safe restarts
        - Job IDs allow management via scheduler.get_job(id)

    Usage:
        # In app/main.py lifespan handler:
        from app.scheduler import scheduler
        from app.tasks.aggregation import register_analytics_jobs

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            # Startup
            register_analytics_jobs(scheduler)
            yield
            # Shutdown

    APScheduler Configuration:
        - Trigger: CronTrigger for time-based scheduling
        - Timezone: UTC (APScheduler default)
        - Misfire grace time: 3600 seconds (1 hour)
        - Coalesce: True (run once if multiple missed)

    Example:
        >>> from app.scheduler import scheduler
        >>> register_analytics_jobs(scheduler)
        >>> jobs = scheduler.get_jobs()
        >>> print([job.id for job in jobs])
        ['daily_stats_aggregation', 'weekly_progress_snapshot']
    """
    try:
        from apscheduler.triggers.cron import CronTrigger
    except ImportError:
        logger.error(
            "❌ APScheduler not installed. Run: pip install apscheduler"
        )
        return

    logger.info("Registering analytics background jobs with APScheduler")

    # Job 1: Daily stats aggregation
    # Runs every day at configured hour (default: midnight UTC)
    daily_hour = getattr(settings, 'DAILY_AGGREGATION_HOUR', 0)

    scheduler.add_job(
        aggregate_daily_stats,
        CronTrigger(hour=daily_hour, minute=0, timezone='UTC'),
        id="daily_stats_aggregation",
        name="Aggregate daily analytics for therapists",
        replace_existing=True,
        misfire_grace_time=3600,  # 1 hour grace period for missed runs
        coalesce=True,  # If multiple runs missed, only run once
    )

    logger.info(
        f"✅ Registered job: daily_stats_aggregation "
        f"(schedule: daily at {daily_hour:02d}:00 UTC)"
    )

    # Job 2: Weekly patient progress snapshots
    # Runs every Sunday at 01:00 UTC
    scheduler.add_job(
        snapshot_patient_progress,
        CronTrigger(day_of_week='sun', hour=1, minute=0, timezone='UTC'),
        id="weekly_progress_snapshot",
        name="Weekly patient progress snapshot",
        replace_existing=True,
        misfire_grace_time=3600,  # 1 hour grace period
        coalesce=True,
    )

    logger.info(
        "✅ Registered job: weekly_progress_snapshot "
        "(schedule: Sundays at 01:00 UTC)"
    )

    logger.info("✅ Analytics background jobs registration complete (2 jobs registered)")
