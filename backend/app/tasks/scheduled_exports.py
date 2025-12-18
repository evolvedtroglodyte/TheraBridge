"""
Scheduled report generation tasks

Provides automated processing of scheduled reports that are due for execution.
Runs on hourly schedule via APScheduler to check for reports that need to be generated.

Jobs:
    - process_scheduled_reports: Processes all scheduled reports due for execution

Design Principles:
    - Idempotent: Safe to run multiple times (skips already processed reports)
    - Efficient: Queries only reports due for execution (next_run_at <= now)
    - Fault-tolerant: Continues processing even if individual reports fail
    - Timezone-aware: All calculations in UTC
"""

import logging
from datetime import datetime, timedelta
from typing import Dict
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.export_models import ScheduledReport, ExportJob
from app.services.export_service import ExportService
from app.services.pdf_generator import get_pdf_generator
from app.services.docx_generator import get_docx_generator

logger = logging.getLogger(__name__)


async def process_scheduled_reports() -> Dict[str, int]:
    """
    Process scheduled reports that are due for execution.

    Runs hourly via APScheduler to check for reports that need to be generated.
    Creates ExportJob for each due report, processes the export, and updates
    the schedule for next run.

    Returns:
        Dict with metrics: {"reports_processed": N}

    Example:
        >>> result = await process_scheduled_reports()
        >>> print(f"Processed {result['reports_processed']} reports")

    Database Operations:
        1. Query ScheduledReport table for reports with next_run_at <= now
        2. For each report:
            a. Create ExportJob record
            b. Generate export file using ExportService
            c. Update job status to 'completed' or 'failed'
            d. Update report's last_run_at and next_run_at
        3. Commit updates for each report individually (fault-tolerant)

    Edge Cases:
        - No reports due: Returns {"reports_processed": 0}
        - Report processing fails: Logs error, continues to next report
        - Template or patient not found: Logs error, marks job as failed
        - Export generation fails: Marks job as failed with error message

    Error Handling:
        - Each report is processed in a try/except block
        - Failures don't stop processing of remaining reports
        - Errors logged with report_id for debugging
        - Failed jobs marked with error_message for user visibility
    """
    logger.info("Starting scheduled report processing")

    async with AsyncSessionLocal() as db:
        try:
            now = datetime.utcnow()

            # Find reports due for execution
            query = select(ScheduledReport).where(
                and_(
                    ScheduledReport.is_active == True,
                    ScheduledReport.next_run_at <= now
                )
            )
            result = await db.execute(query)
            reports = result.scalars().all()

            if not reports:
                logger.info("No scheduled reports due for execution")
                return {"reports_processed": 0}

            logger.info(f"Found {len(reports)} scheduled reports due for execution")

            processed_count = 0

            for report in reports:
                try:
                    logger.info(
                        f"Processing scheduled report {report.id}",
                        extra={
                            "report_id": str(report.id),
                            "schedule_type": report.schedule_type,
                            "export_type": report.template.export_type
                        }
                    )

                    # Create export job
                    job = ExportJob(
                        user_id=report.user_id,
                        patient_id=report.patient_id,
                        template_id=report.template_id,
                        export_type=report.template.export_type,
                        format=report.template.format,
                        status='pending',
                        parameters=report.parameters
                    )
                    db.add(job)
                    await db.commit()
                    await db.refresh(job)

                    # Mark job as processing
                    job.status = 'processing'
                    job.started_at = datetime.utcnow()
                    await db.commit()

                    # Process export (similar to background task)
                    try:
                        # Initialize export service
                        pdf_gen = get_pdf_generator()
                        docx_gen = get_docx_generator()
                        export_service = ExportService(pdf_gen, docx_gen)

                        # Gather data based on export type
                        context = None
                        if report.template.export_type == 'session_notes':
                            # Extract session_ids from parameters
                            session_ids = report.parameters.get('session_ids', [])
                            if session_ids:
                                context = await export_service.gather_session_notes_data(
                                    session_ids=[UUID(sid) for sid in session_ids],
                                    db=db
                                )
                        elif report.template.export_type == 'progress_report':
                            # Extract date range from parameters
                            start_date = datetime.fromisoformat(
                                report.parameters.get('start_date', (now - timedelta(days=30)).isoformat())
                            )
                            end_date = datetime.fromisoformat(
                                report.parameters.get('end_date', now.isoformat())
                            )
                            if report.patient_id:
                                context = await export_service.gather_progress_report_data(
                                    patient_id=report.patient_id,
                                    start_date=start_date,
                                    end_date=end_date,
                                    db=db
                                )

                        if context is None:
                            raise ValueError(
                                f"Unsupported export type '{report.template.export_type}' "
                                f"or missing required parameters"
                            )

                        # Merge template include_sections with report parameters
                        if report.template.include_sections:
                            context['include_sections'] = report.template.include_sections

                        # Generate export file
                        file_bytes = await export_service.generate_export(
                            export_type=report.template.export_type,
                            format=report.template.format,
                            context=context,
                            template_id=report.template_id,
                            db=db
                        )

                        # Save file to disk
                        file_extension = report.template.format
                        file_name = f"export_{job.id}.{file_extension}"
                        file_path = export_service.export_dir / file_name

                        with open(file_path, 'wb') as f:
                            f.write(file_bytes)

                        # Update job with success
                        job.status = 'completed'
                        job.file_path = str(file_path)
                        job.file_size_bytes = len(file_bytes)
                        job.completed_at = datetime.utcnow()

                        # Set expiration (default: 30 days)
                        job.expires_at = datetime.utcnow() + timedelta(days=30)

                        logger.info(
                            f"Export job {job.id} completed successfully",
                            extra={
                                "job_id": str(job.id),
                                "file_size": job.file_size_bytes
                            }
                        )

                    except Exception as e:
                        # Mark job as failed
                        job.status = 'failed'
                        job.error_message = str(e)
                        job.completed_at = datetime.utcnow()

                        logger.error(
                            f"Export job {job.id} failed",
                            extra={
                                "job_id": str(job.id),
                                "error": str(e)
                            },
                            exc_info=True
                        )

                    await db.commit()

                    # Update scheduled report
                    report.last_run_at = now
                    report.next_run_at = calculate_next_run(
                        report.schedule_type,
                        report.schedule_config
                    )
                    await db.commit()

                    processed_count += 1

                    logger.info(
                        f"Scheduled report {report.id} processed successfully",
                        extra={
                            "report_id": str(report.id),
                            "next_run_at": report.next_run_at.isoformat()
                        }
                    )

                except Exception as e:
                    logger.error(
                        f"Failed to process scheduled report {report.id}",
                        extra={"report_id": str(report.id)},
                        exc_info=True
                    )
                    # Continue to next report (fault-tolerant)
                    await db.rollback()

            logger.info(f"✅ Processed {processed_count} scheduled reports")
            return {"reports_processed": processed_count}

        except Exception as e:
            logger.error(
                f"❌ Scheduled report processing failed: {str(e)}",
                exc_info=True
            )
            await db.rollback()
            raise


def calculate_next_run(schedule_type: str, config: dict) -> datetime:
    """
    Calculate next run time based on schedule configuration.

    Args:
        schedule_type: 'daily', 'weekly', or 'monthly'
        config: Schedule configuration dict with parameters

    Returns:
        Datetime for next scheduled execution (UTC)

    Configuration Examples:
        Daily: {"hour": 8, "minute": 0}
            - Runs every day at 08:00 UTC

        Weekly: {"day_of_week": 0, "hour": 9, "minute": 0}
            - Runs every Monday at 09:00 UTC
            - day_of_week: 0=Monday, 6=Sunday

        Monthly: {"day_of_month": 1, "hour": 10, "minute": 0}
            - Runs on 1st of each month at 10:00 UTC
            - day_of_month: 1-28 (safe range for all months)

    Edge Cases:
        - Invalid schedule_type: Returns now + 1 day (fallback)
        - Missing config keys: Uses defaults (hour=0, minute=0)
        - day_of_month > 28: Clamped to 28 for safety
        - Next run in the past: Advances to next valid occurrence

    Algorithm:
        1. Parse schedule parameters from config
        2. Calculate next occurrence from current time
        3. If next occurrence is in the past, advance by interval
        4. Return UTC datetime for next run
    """
    now = datetime.utcnow()

    if schedule_type == 'daily':
        # Run at specific time daily
        hour = config.get('hour', 0)
        minute = config.get('minute', 0)

        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

        # If next_run is in the past, advance to tomorrow
        if next_run <= now:
            next_run += timedelta(days=1)

        return next_run

    elif schedule_type == 'weekly':
        # Run on specific day of week
        day_of_week = config.get('day_of_week', 0)  # 0=Monday, 6=Sunday
        hour = config.get('hour', 0)
        minute = config.get('minute', 0)

        # Calculate days until target day_of_week
        # now.weekday(): 0=Monday, 6=Sunday (matches our convention)
        current_day = now.weekday()
        days_ahead = (day_of_week - current_day) % 7

        # If target day is today, check if time has passed
        if days_ahead == 0:
            target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if target_time <= now:
                # Time has passed today, schedule for next week
                days_ahead = 7

        next_run = now + timedelta(days=days_ahead)
        next_run = next_run.replace(hour=hour, minute=minute, second=0, microsecond=0)

        return next_run

    elif schedule_type == 'monthly':
        # Run on specific day of month
        day_of_month = config.get('day_of_month', 1)
        hour = config.get('hour', 0)
        minute = config.get('minute', 0)

        # Clamp day_of_month to safe range (1-28 works for all months)
        day_of_month = max(1, min(28, day_of_month))

        # Try to create next_run in current month
        try:
            next_run = now.replace(
                day=day_of_month,
                hour=hour,
                minute=minute,
                second=0,
                microsecond=0
            )
        except ValueError:
            # If day doesn't exist in current month (shouldn't happen with clamp),
            # move to next month
            if now.month == 12:
                next_run = now.replace(
                    year=now.year + 1,
                    month=1,
                    day=day_of_month,
                    hour=hour,
                    minute=minute,
                    second=0,
                    microsecond=0
                )
            else:
                next_run = now.replace(
                    month=now.month + 1,
                    day=day_of_month,
                    hour=hour,
                    minute=minute,
                    second=0,
                    microsecond=0
                )

        # If next_run is in the past, advance to next month
        if next_run <= now:
            if next_run.month == 12:
                next_run = next_run.replace(year=next_run.year + 1, month=1)
            else:
                next_run = next_run.replace(month=next_run.month + 1)

        return next_run

    else:
        # Unsupported schedule type - fallback to daily
        logger.warning(
            f"Unsupported schedule_type '{schedule_type}', defaulting to +1 day"
        )
        return now + timedelta(days=1)


def register_export_jobs() -> None:
    """
    Register scheduled export tasks with APScheduler.

    Called during application startup (in app/main.py lifespan handler).
    Adds process_scheduled_reports job to run hourly and check for due reports.

    Jobs Registered:
        - scheduled_reports_processing: Runs every hour on the hour

    Configuration:
        - Trigger: CronTrigger(minute=0) - runs at :00 every hour
        - Job ID: "scheduled_reports_processing"
        - Misfire grace time: 600 seconds (10 minutes)
        - Coalesce: True (if multiple runs missed, only run once)

    Usage:
        # In app/main.py lifespan handler:
        from app.tasks.scheduled_exports import register_export_jobs

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            # Startup
            register_export_jobs()
            yield
            # Shutdown

    APScheduler Configuration:
        - Trigger: CronTrigger for time-based scheduling
        - Timezone: UTC (APScheduler default)
        - Misfire grace time: 600 seconds (10 minutes)
            - If server is down and job misses scheduled time,
              it will still run if caught within 10 minutes
        - Coalesce: True
            - If multiple runs are missed (e.g., server down for 3 hours),
              only run once when server comes back up (not 3 times)

    Example:
        >>> from app.scheduler import scheduler
        >>> register_export_jobs()
        >>> jobs = scheduler.get_jobs()
        >>> print([job.id for job in jobs])
        ['scheduled_reports_processing']

    Dependencies:
        Requires app.scheduler module to be imported and initialized.
        The scheduler must be started separately (scheduler.start()).
    """
    # Import scheduler here to avoid circular dependency
    try:
        from app.scheduler import scheduler
    except ImportError:
        logger.error(
            "❌ Failed to import scheduler. Ensure app.scheduler module exists. "
            "Scheduled export jobs will not be registered."
        )
        return

    try:
        from apscheduler.triggers.cron import CronTrigger
    except ImportError:
        logger.error(
            "❌ APScheduler not installed. Run: pip install apscheduler"
        )
        return

    logger.info("Registering scheduled export jobs with APScheduler")

    # Job: Scheduled report processing
    # Runs every hour on the hour to check for reports due
    scheduler.add_job(
        process_scheduled_reports,
        CronTrigger(minute=0, timezone='UTC'),  # Run every hour at :00
        id="scheduled_reports_processing",
        name="Process scheduled export reports",
        replace_existing=True,
        misfire_grace_time=600,  # 10 minute grace period for missed runs
        coalesce=True,  # If multiple runs missed, only run once
    )

    logger.info(
        "✅ Registered job: scheduled_reports_processing "
        "(schedule: hourly at :00 UTC)"
    )

    logger.info("✅ Scheduled export jobs registration complete (1 job registered)")
