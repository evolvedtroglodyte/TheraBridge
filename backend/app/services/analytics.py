"""
Analytics Service for Therapist Dashboard

Provides calculation functions for analytics endpoints including:
- Practice overview metrics (total patients, sessions, completion rates)
- Patient progress tracking
- Session trends and frequency analysis
- Topic analysis and insights
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, distinct, case, cast, Integer, String
from uuid import UUID
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import HTTPException
import logging
import json

from app.models.schemas import (
    AnalyticsOverviewResponse,
    SessionTrendsResponse,
    SessionTrendDataPoint,
    TopicsResponse,
    TopicFrequency,
    PatientProgressResponse,
    SessionFrequency,
    MoodTrend,
    MoodTrendData,
    GoalStatus
)
from app.models.db_models import TherapySession, User, TherapistPatient

# Configure logger
logger = logging.getLogger(__name__)


def dialect_aware_date_trunc(period: str, column, db_session: AsyncSession):
    """
    Create a database-agnostic date truncation expression.

    PostgreSQL uses func.date_trunc(), SQLite uses func.strftime().
    This helper function returns the appropriate SQL expression based on the dialect.

    Args:
        period: Time period to truncate to ("week", "month", "quarter", "year")
        column: SQLAlchemy column to truncate (e.g., TherapySession.session_date)
        db_session: AsyncSession used to detect database dialect

    Returns:
        SQLAlchemy expression appropriate for the database dialect

    SQLite Format Strings:
        - week: '%Y-%W' (Year-WeekNumber)
        - month: '%Y-%m' (Year-Month)
        - quarter: Calculated using month division
        - year: '%Y' (Year)
    """
    # Detect dialect from session's bind
    dialect_name = db_session.bind.dialect.name

    if dialect_name == 'postgresql':
        # PostgreSQL: Use native date_trunc
        return func.date_trunc(period, column)

    elif dialect_name == 'sqlite':
        # SQLite: Use strftime with format strings
        if period == 'week':
            # ISO week format: YYYY-WW
            return func.strftime('%Y-%W', column)
        elif period == 'month':
            # Month format: YYYY-MM
            return func.strftime('%Y-%m', column)
        elif period == 'quarter':
            # Quarter calculation: YYYY-Q
            # Formula: (month - 1) / 3 + 1 = quarter number
            return func.strftime('%Y-', column) + cast(
                (cast(func.strftime('%m', column), Integer) - 1) / 3 + 1,
                Integer
            )
        elif period == 'year':
            # Year format: YYYY
            return func.strftime('%Y', column)
        else:
            # Default to month for unknown periods
            logger.warning(f"Unknown period '{period}' for SQLite, defaulting to month")
            return func.strftime('%Y-%m', column)

    else:
        # Fallback for other databases (MySQL, etc.) - use PostgreSQL syntax
        logger.warning(f"Unknown dialect '{dialect_name}', using PostgreSQL date_trunc syntax")
        return func.date_trunc(period, column)


async def calculate_overview_analytics(
    therapist_id: UUID,
    db: AsyncSession
) -> AnalyticsOverviewResponse:
    """
    Calculate overview analytics for a therapist's practice.

    Provides key metrics including total patients, active patients, recent session
    counts, upcoming sessions, and overall completion rate. This data powers the
    main dashboard overview section.

    Args:
        therapist_id: UUID of the therapist to calculate analytics for
        db: Async database session

    Returns:
        AnalyticsOverviewResponse: Pydantic model containing all overview metrics

    Metrics Calculated:
        - total_patients: Count of all active therapist-patient relationships
        - active_patients: Patients with at least one session in last 30 days
        - sessions_this_week: Sessions where session_date >= start of current week
        - sessions_this_month: Sessions where session_date >= start of current month
        - upcoming_sessions: Future sessions (status != 'failed')
        - completion_rate: Ratio of processed sessions to total sessions

    Date Ranges:
        - Week starts on Monday (ISO 8601 standard)
        - Month starts on day 1 of current month
        - Active patient window: last 30 days

    Edge Cases Handled:
        - No patients: returns zeros for all metrics
        - No sessions: completion_rate defaults to 0.0
        - Division by zero: handled with conditional logic

    Example:
        >>> async with AsyncSession(engine) as db:
        ...     overview = await calculate_overview_analytics(therapist_uuid, db)
        ...     print(f"Total patients: {overview.total_patients}")
    """
    logger.info(f"Calculating overview analytics for therapist {therapist_id}")

    # Calculate date boundaries
    now = datetime.utcnow()
    week_start = now - timedelta(days=now.weekday())  # Monday of current week
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    thirty_days_ago = now - timedelta(days=30)

    # 1. Calculate total_patients (active relationships)
    total_patients_query = select(func.count(TherapistPatient.id)).where(
        and_(
            TherapistPatient.therapist_id == therapist_id,
            TherapistPatient.is_active == True
        )
    )
    total_patients_result = await db.execute(total_patients_query)
    total_patients = total_patients_result.scalar() or 0

    # 2. Calculate active_patients (patients with sessions in last 30 days)
    # Use distinct patient_id count to avoid duplicate patients
    active_patients_query = select(func.count(distinct(TherapySession.patient_id))).where(
        and_(
            TherapySession.therapist_id == therapist_id,
            TherapySession.session_date >= thirty_days_ago,
            TherapySession.status != 'failed'
        )
    )
    active_patients_result = await db.execute(active_patients_query)
    active_patients = active_patients_result.scalar() or 0

    # 3. Calculate sessions_this_week
    sessions_this_week_query = select(func.count(TherapySession.id)).where(
        and_(
            TherapySession.therapist_id == therapist_id,
            TherapySession.session_date >= week_start,
            TherapySession.session_date <= now,
            TherapySession.status != 'failed'
        )
    )
    sessions_this_week_result = await db.execute(sessions_this_week_query)
    sessions_this_week = sessions_this_week_result.scalar() or 0

    # 4. Calculate sessions_this_month
    sessions_this_month_query = select(func.count(TherapySession.id)).where(
        and_(
            TherapySession.therapist_id == therapist_id,
            TherapySession.session_date >= month_start,
            TherapySession.session_date <= now,
            TherapySession.status != 'failed'
        )
    )
    sessions_this_month_result = await db.execute(sessions_this_month_query)
    sessions_this_month = sessions_this_month_result.scalar() or 0

    # 5. Calculate upcoming_sessions (future sessions, not failed)
    upcoming_sessions_query = select(func.count(TherapySession.id)).where(
        and_(
            TherapySession.therapist_id == therapist_id,
            TherapySession.session_date > now,
            TherapySession.status != 'failed'
        )
    )
    upcoming_sessions_result = await db.execute(upcoming_sessions_query)
    upcoming_sessions = upcoming_sessions_result.scalar() or 0

    # 6. Calculate completion_rate (processed sessions / total sessions)
    # Total sessions (excluding failed)
    total_sessions_query = select(func.count(TherapySession.id)).where(
        and_(
            TherapySession.therapist_id == therapist_id,
            TherapySession.status != 'failed'
        )
    )
    total_sessions_result = await db.execute(total_sessions_query)
    total_sessions = total_sessions_result.scalar() or 0

    # Processed sessions (status = 'processed')
    processed_sessions_query = select(func.count(TherapySession.id)).where(
        and_(
            TherapySession.therapist_id == therapist_id,
            TherapySession.status == 'processed'
        )
    )
    processed_sessions_result = await db.execute(processed_sessions_query)
    processed_sessions = processed_sessions_result.scalar() or 0

    # Calculate completion rate (avoid division by zero)
    completion_rate = (
        float(processed_sessions) / float(total_sessions)
        if total_sessions > 0
        else 0.0
    )

    logger.info(
        f"Overview analytics calculated for therapist {therapist_id}: "
        f"total_patients={total_patients}, active_patients={active_patients}, "
        f"sessions_this_week={sessions_this_week}, sessions_this_month={sessions_this_month}, "
        f"upcoming_sessions={upcoming_sessions}, completion_rate={completion_rate:.2f}"
    )

    # Return Pydantic response model
    return AnalyticsOverviewResponse(
        total_patients=total_patients,
        active_patients=active_patients,
        sessions_this_week=sessions_this_week,
        sessions_this_month=sessions_this_month,
        upcoming_sessions=upcoming_sessions,
        completion_rate=completion_rate
    )


async def calculate_session_trends(
    therapist_id: UUID,
    period: str,
    patient_id: Optional[UUID],
    db: AsyncSession
) -> SessionTrendsResponse:
    """
    Calculate session trends over time with configurable aggregation periods.

    Aggregates session data into time-based buckets (week, month, quarter, year)
    to show volume trends and unique patient counts. Supports filtering by specific
    patient for individual patient trend analysis.

    Args:
        therapist_id: UUID of the therapist to calculate trends for
        period: Aggregation period - one of: "week", "month", "quarter", "year"
        patient_id: Optional UUID to filter trends for a specific patient
        db: Async database session

    Returns:
        SessionTrendsResponse: Pydantic model containing period and trend data points

    Period Specifications:
        - "week": Last 12 weeks, grouped by ISO week, labeled "Week 42 2024"
        - "month": Last 12 months, grouped by month, labeled "Jan", "Feb", etc.
        - "quarter": Last 8 quarters, grouped by quarter, labeled "Q1 2024", "Q2 2024"
        - "year": Last 5 years, grouped by year, labeled "2024", "2023", etc.

    Data Points:
        Each data point contains:
        - label: Human-readable period label
        - sessions: Total number of therapy sessions in that period
        - unique_patients: Count of distinct patients seen in that period

    PostgreSQL Functions Used:
        - func.date_trunc(): Groups dates by time period
        - func.to_char(): Formats dates for labels
        - func.extract(): Extracts week/year components
        - func.count(): Aggregates session counts
        - func.count(func.distinct()): Counts unique patients

    Example:
        >>> # Get monthly trends for all patients
        >>> trends = await calculate_session_trends(
        ...     therapist_uuid, "month", None, db
        ... )
        >>> # Get weekly trends for specific patient
        >>> patient_trends = await calculate_session_trends(
        ...     therapist_uuid, "week", patient_uuid, db
        ... )

    Edge Cases:
        - No sessions in period: returns data point with 0 sessions, 0 patients
        - Invalid period: defaults to "month"
        - Patient filter applied: only counts that patient's sessions
    """
    logger.info(
        f"Calculating session trends for therapist {therapist_id}, "
        f"period={period}, patient_id={patient_id}"
    )

    # Map period to PostgreSQL date_trunc argument, limit, and label format
    period_config = {
        "week": {
            "trunc": "week",
            "limit": 12,
            "label_format": "week"
        },
        "month": {
            "trunc": "month",
            "limit": 12,
            "label_format": "month"
        },
        "quarter": {
            "trunc": "quarter",
            "limit": 8,
            "label_format": "quarter"
        },
        "year": {
            "trunc": "year",
            "limit": 5,
            "label_format": "year"
        }
    }

    # Default to month if invalid period provided
    if period not in period_config:
        logger.warning(f"Invalid period '{period}' provided, defaulting to 'month'")
        period = "month"

    config = period_config[period]
    trunc_arg = config["trunc"]
    limit = config["limit"]
    label_format = config["label_format"]

    # Detect database dialect for cross-database compatibility
    dialect_name = db.bind.dialect.name

    # Build base query with different label generation based on period
    if label_format == "week":
        # Week: "Week 42 2024"
        if dialect_name == 'postgresql':
            label_expr = func.concat(
                'Week ',
                func.extract('week', TherapySession.session_date),
                ' ',
                func.extract('year', TherapySession.session_date)
            ).label('label')
        else:  # sqlite
            # SQLite: Use strftime for week and year
            label_expr = (
                'Week ' +
                cast(func.strftime('%W', TherapySession.session_date), String) +
                ' ' +
                cast(func.strftime('%Y', TherapySession.session_date), String)
            ).label('label')
    elif label_format == "month":
        # Month: "Jan", "Feb", "Mar"
        if dialect_name == 'postgresql':
            label_expr = func.to_char(TherapySession.session_date, 'Mon').label('label')
        else:  # sqlite
            # SQLite: Use strftime with %m and map to month names
            label_expr = func.strftime('%m', TherapySession.session_date).label('label')
    elif label_format == "quarter":
        # Quarter: "Q1 2024", "Q2 2024"
        if dialect_name == 'postgresql':
            label_expr = func.concat(
                'Q',
                func.extract('quarter', TherapySession.session_date),
                ' ',
                func.extract('year', TherapySession.session_date)
            ).label('label')
        else:  # sqlite
            # SQLite: Calculate quarter from month
            label_expr = (
                'Q' +
                cast((cast(func.strftime('%m', TherapySession.session_date), Integer) - 1) / 3 + 1, String) +
                ' ' +
                cast(func.strftime('%Y', TherapySession.session_date), String)
            ).label('label')
    else:  # year
        # Year: "2024", "2023"
        if dialect_name == 'postgresql':
            label_expr = func.to_char(TherapySession.session_date, 'YYYY').label('label')
        else:  # sqlite
            label_expr = func.strftime('%Y', TherapySession.session_date).label('label')

    # Build query
    query = select(
        label_expr,
        func.count(TherapySession.id).label('sessions'),
        func.count(func.distinct(TherapySession.patient_id)).label('unique_patients')
    ).where(
        TherapySession.therapist_id == therapist_id
    )

    # Add optional patient filter
    if patient_id is not None:
        query = query.where(TherapySession.patient_id == patient_id)

    # Group by truncated date using dialect-aware function
    date_trunc_expr = dialect_aware_date_trunc(trunc_arg, TherapySession.session_date, db)
    query = query.group_by(
        date_trunc_expr
    ).order_by(
        date_trunc_expr.desc()
    ).limit(limit)

    # Execute query
    result = await db.execute(query)
    rows = result.fetchall()

    # Convert to data points
    data_points = [
        SessionTrendDataPoint(
            label=row[0],
            sessions=row[1],
            unique_patients=row[2]
        )
        for row in rows
    ]

    # Reverse to show oldest to newest (query ordered desc for LIMIT, now reverse)
    data_points.reverse()

    logger.info(
        f"Session trends calculated for therapist {therapist_id}: "
        f"period={period}, data_points={len(data_points)}"
    )

    return SessionTrendsResponse(
        period=period,
        data=data_points
    )

async def calculate_topic_frequencies(
    therapist_id: UUID,
    db: AsyncSession
) -> TopicsResponse:
    """
    Analyze frequently discussed topics across all therapist's sessions.

    Extracts topics from the extracted_notes JSONB column's 'key_topics' array,
    counts frequency of each unique topic, and returns the top 20 topics sorted
    by frequency with percentage calculations.

    Args:
        therapist_id: UUID of the therapist to calculate topic analytics for
        db: Async database session

    Returns:
        TopicsResponse: Pydantic model containing list of TopicFrequency objects

    JSONB Structure:
        extracted_notes = {
            "key_topics": ["anxiety", "work stress", "relationships"],
            "topic_summary": "...",
            ...
        }

    Algorithm:
        1. Extract all topics from JSONB arrays using jsonb_array_elements_text
        2. Normalize topics to lowercase for consistent counting
        3. Count frequency of each unique topic
        4. Calculate percentage (topic_count / total_topics)
        5. Sort by count descending and return top 20

    Edge Cases Handled:
        - Sessions with no extracted_notes (filtered out)
        - extracted_notes with no key_topics (filtered out)
        - Empty key_topics arrays (no rows returned)
        - Empty/whitespace-only topic strings (skipped)
        - No topics found across all sessions (returns empty list)

    Example:
        >>> async with AsyncSession(engine) as db:
        ...     topics = await calculate_topic_frequencies(therapist_uuid, db)
        ...     for topic in topics.topics[:5]:
        ...         print(f"{topic.name}: {topic.count} ({topic.percentage:.1%})")
        anxiety: 45 (35.0%)
        relationships: 38 (29.5%)
        work stress: 22 (17.1%)
        sleep issues: 15 (11.6%)
        family: 9 (7.0%)
    """
    logger.info(f"Calculating topic frequencies for therapist {therapist_id}")

    try:
        # Detect database dialect for cross-database compatibility
        dialect_name = db.bind.dialect.name

        if dialect_name == 'postgresql':
            # PostgreSQL - Use SQL-based aggregation with GROUP BY and COUNT
            # This optimizes the query by doing counting at the database level
            # instead of fetching all topics and counting in Python

            # Build optimized query with GROUP BY, COUNT, filtering, ordering, and limiting
            # Use CTE (Common Table Expression) to expand topics once, then filter and count
            from sqlalchemy import literal_column

            topic_expr = func.lower(
                func.jsonb_array_elements_text(
                    TherapySession.extracted_notes['key_topics']
                )
            )

            topic_query = (
                select(
                    topic_expr.label('topic'),
                    func.count().label('count')
                )
                .where(
                    and_(
                        TherapySession.therapist_id == therapist_id,
                        TherapySession.extracted_notes.isnot(None)
                    )
                )
                .group_by(topic_expr)
                .having(
                    and_(
                        topic_expr != '',
                        topic_expr.isnot(None),
                        func.length(func.trim(topic_expr)) > 0
                    )
                )
                .order_by(func.count().desc())
                .limit(50)
            )

            # Execute optimized query
            result = await db.execute(topic_query)
            topic_rows = result.fetchall()

            # Calculate total topics for percentages
            total_topics = sum(row.count for row in topic_rows)

            # Handle edge case: no topics found
            if total_topics == 0:
                logger.info(f"No topics found for therapist {therapist_id}")
                return TopicsResponse(topics=[])

            # Convert to TopicFrequency objects
            topic_frequencies = [
                TopicFrequency(
                    name=row.topic.strip(),
                    count=row.count,
                    percentage=round(row.count / total_topics, 4)
                )
                for row in topic_rows
                if row.topic and row.topic.strip()  # Skip empty/whitespace topics
            ]

            # Take top 20 (already ordered by count desc in SQL)
            top_topics = topic_frequencies[:20]

            logger.info(
                f"Topic frequency analysis complete for therapist {therapist_id}: "
                f"analyzed {total_topics} total topics, "
                f"found {len(topic_frequencies)} unique topics, "
                f"returning top {len(top_topics)} topics"
            )

            return TopicsResponse(topics=top_topics)

        else:  # sqlite
            # SQLite - Parse JSON in Python since SQLite lacks jsonb_array_elements_text
            # First fetch all sessions with extracted_notes
            sessions_query = (
                select(TherapySession.extracted_notes)
                .where(TherapySession.therapist_id == therapist_id)
                .where(TherapySession.extracted_notes.isnot(None))
            )
            result = await db.execute(sessions_query)
            all_notes = result.scalars().all()

            # Parse JSON and extract key_topics arrays
            all_topics = []
            for notes in all_notes:
                if notes and 'key_topics' in notes:
                    topics = notes['key_topics']
                    if isinstance(topics, list):
                        # Normalize to lowercase and filter empty
                        all_topics.extend([
                            topic.lower().strip()
                            for topic in topics
                            if isinstance(topic, str) and topic.strip()
                        ])
                    elif isinstance(topics, str):
                        # Handle case where it's stored as JSON string
                        try:
                            topics_list = json.loads(topics)
                            if isinstance(topics_list, list):
                                all_topics.extend([
                                    topic.lower().strip()
                                    for topic in topics_list
                                    if isinstance(topic, str) and topic.strip()
                                ])
                        except json.JSONDecodeError:
                            pass

            # Handle edge case: no topics found
            if not all_topics:
                logger.info(f"No topics found for therapist {therapist_id}")
                return TopicsResponse(topics=[])

            # Count frequencies using Python Counter for SQLite
            from collections import Counter
            topic_counts = Counter(all_topics)

            # Calculate total for percentage calculations
            total_topics = sum(topic_counts.values())

            # Convert to TopicFrequency objects with percentages
            topic_frequencies = [
                TopicFrequency(
                    name=topic,
                    count=count,
                    percentage=round(count / total_topics, 4)
                )
                for topic, count in topic_counts.most_common(50)  # Get top 50
            ]

            # Take top 20
            top_topics = topic_frequencies[:20]

            logger.info(
                f"Topic frequency analysis complete for therapist {therapist_id}: "
                f"analyzed {total_topics} total topics, "
                f"found {len(topic_counts)} unique topics, "
                f"returning top {len(top_topics)} topics"
            )

            return TopicsResponse(topics=top_topics)

    except Exception as e:
        logger.error(
            f"Error calculating topic frequencies for therapist {therapist_id}: {str(e)}",
            exc_info=True
        )
        # Return empty response on error rather than failing the endpoint
        return TopicsResponse(topics=[])


async def calculate_patient_progress(
    patient_id: UUID,
    therapist_id: UUID,
    db: AsyncSession
) -> PatientProgressResponse:
    """
    Calculate detailed progress metrics for a specific patient.

    Provides comprehensive progress tracking including session frequency, mood trends,
    and goal completion status. This data powers the patient progress detail view.

    Args:
        patient_id: UUID of the patient to calculate progress for
        therapist_id: UUID of the therapist requesting the data
        db: Async database session

    Returns:
        PatientProgressResponse: Pydantic model containing all progress metrics

    Raises:
        HTTPException: 403 if therapist doesn't have access to this patient

    Metrics Calculated:
        - total_sessions: Count of all sessions for the patient
        - first_session_date: Date of earliest session (YYYY-MM-DD format)
        - last_session_date: Date of most recent session (YYYY-MM-DD format)
        - session_frequency: Weekly average and trend (stable/increasing/decreasing)
        - mood_trend: Monthly mood averages and overall trend (improving/declining/stable)
        - goals: Action item counts by status (total/completed/in_progress/not_started)

    Authorization:
        - Verifies patient is assigned to therapist via therapist_patients table
        - Requires is_active=True relationship
        - Returns 403 Forbidden if access denied

    Edge Cases Handled:
        - No sessions: Returns N/A dates and zero metrics
        - Single session: Weekly average set to 1.0, trend "stable"
        - No mood data: Returns empty mood_trend with "stable" trend
        - No goals: Returns zero goal counts

    Data Sources:
        - Mood: extracted_notes->>'session_mood' (very_low/low/neutral/positive/very_positive)
        - Goals: treatment_goals table (queried by patient_id)

    Example:
        >>> async with AsyncSession(engine) as db:
        ...     progress = await calculate_patient_progress(patient_uuid, therapist_uuid, db)
        ...     print(f"Total sessions: {progress.total_sessions}")
        ...     print(f"Weekly average: {progress.session_frequency.weekly_average}")
    """
    logger.info(f"Calculating patient progress for patient {patient_id}, therapist {therapist_id}")

    # 1. Verify access: Check that patient is assigned to therapist
    access_query = select(TherapistPatient).where(
        and_(
            TherapistPatient.therapist_id == therapist_id,
            TherapistPatient.patient_id == patient_id,
            TherapistPatient.is_active == True
        )
    )
    access_result = await db.execute(access_query)
    relationship = access_result.scalar_one_or_none()

    if not relationship:
        logger.warning(
            f"Access denied: Patient {patient_id} not assigned to therapist {therapist_id}"
        )
        raise HTTPException(
            status_code=403,
            detail="Access denied: Patient is not assigned to this therapist"
        )

    # 2. Fetch all sessions for this patient, ordered by date
    sessions_query = select(TherapySession).where(
        TherapySession.patient_id == patient_id
    ).order_by(TherapySession.session_date)

    sessions_result = await db.execute(sessions_query)
    sessions = sessions_result.scalars().all()

    total_sessions = len(sessions)

    # Handle patients with no sessions
    if total_sessions == 0:
        logger.info(f"Patient {patient_id} has no sessions")
        return PatientProgressResponse(
            patient_id=patient_id,
            total_sessions=0,
            first_session_date="N/A",
            last_session_date="N/A",
            session_frequency=SessionFrequency(
                weekly_average=0.0,
                trend="stable"
            ),
            mood_trend=MoodTrend(
                data=[],
                trend="stable"
            ),
            goals=GoalStatus(
                total=0,
                completed=0,
                in_progress=0,
                not_started=0
            )
        )

    # 3. Basic session stats
    first_session_date = sessions[0].session_date.strftime("%Y-%m-%d")
    last_session_date = sessions[-1].session_date.strftime("%Y-%m-%d")

    # 4. Calculate session frequency
    session_frequency = await _calculate_session_frequency(sessions, db, patient_id)

    # 5. Calculate mood trend
    mood_trend = await _calculate_mood_trend(sessions, db, patient_id)

    # 6. Calculate goals from treatment_goals table
    goals = await _calculate_goals(patient_id, db)

    logger.info(
        f"Patient progress calculated for patient {patient_id}: "
        f"total_sessions={total_sessions}, weekly_avg={session_frequency.weekly_average}, "
        f"mood_trend={mood_trend.trend}, goals_total={goals.total}"
    )

    return PatientProgressResponse(
        patient_id=patient_id,
        total_sessions=total_sessions,
        first_session_date=first_session_date,
        last_session_date=last_session_date,
        session_frequency=session_frequency,
        mood_trend=mood_trend,
        goals=goals
    )


async def _calculate_session_frequency(
    sessions: List[TherapySession],
    db: AsyncSession,
    patient_id: UUID
) -> SessionFrequency:
    """
    Calculate weekly average and trend for session frequency.

    Args:
        sessions: List of all sessions for the patient (ordered by date)
        db: Async database session
        patient_id: UUID of the patient

    Returns:
        SessionFrequency: Weekly average and trend (stable/increasing/decreasing)

    Trend Calculation:
        - Compare last 30 days vs previous 30 days (30-60 days ago)
        - increasing: last month > previous month
        - decreasing: last month < previous month
        - stable: last month == previous month
    """
    if len(sessions) < 2:
        return SessionFrequency(
            weekly_average=0.0 if len(sessions) == 0 else 1.0,
            trend="stable"
        )

    first_date = sessions[0].session_date
    last_date = sessions[-1].session_date

    # Calculate weeks between first and last session
    days_diff = (last_date - first_date).days
    weeks_diff = max(days_diff / 7.0, 1.0)  # Minimum 1 week to avoid division by zero

    weekly_average = round(len(sessions) / weeks_diff, 2)

    # Determine trend: compare last month vs previous month
    now = datetime.utcnow()
    one_month_ago = now - timedelta(days=30)
    two_months_ago = now - timedelta(days=60)

    # Count sessions in last 30 days
    last_month_query = select(func.count(TherapySession.id)).where(
        and_(
            TherapySession.patient_id == patient_id,
            TherapySession.session_date >= one_month_ago,
            TherapySession.session_date <= now
        )
    )
    last_month_result = await db.execute(last_month_query)
    last_month_count = last_month_result.scalar() or 0

    # Count sessions in previous 30 days (30-60 days ago)
    previous_month_query = select(func.count(TherapySession.id)).where(
        and_(
            TherapySession.patient_id == patient_id,
            TherapySession.session_date >= two_months_ago,
            TherapySession.session_date < one_month_ago
        )
    )
    previous_month_result = await db.execute(previous_month_query)
    previous_month_count = previous_month_result.scalar() or 0

    # Determine trend
    if last_month_count > previous_month_count:
        trend = "increasing"
    elif last_month_count < previous_month_count:
        trend = "decreasing"
    else:
        trend = "stable"

    logger.debug(
        f"Session frequency for patient {patient_id}: weekly_avg={weekly_average}, "
        f"trend={trend} (last_month={last_month_count}, prev_month={previous_month_count})"
    )

    return SessionFrequency(
        weekly_average=weekly_average,
        trend=trend
    )


async def _calculate_mood_trend(
    sessions: List[TherapySession],
    db: AsyncSession,
    patient_id: UUID
) -> MoodTrend:
    """
    Calculate mood trend from extracted notes JSONB.

    Extracts session_mood from extracted_notes JSONB column and calculates
    monthly averages. Maps mood levels to numeric scores for aggregation.

    Args:
        sessions: List of all sessions for the patient
        db: Async database session
        patient_id: UUID of the patient

    Returns:
        MoodTrend: Monthly mood data points and overall trend

    Mood Score Mapping:
        - very_low: 1.0
        - low: 2.0
        - neutral: 3.0
        - positive: 4.0
        - very_positive: 5.0

    Trend Calculation:
        - Compare first half vs second half of monthly data
        - improving: second half avg > first half avg + 0.3
        - declining: second half avg < first half avg - 0.3
        - stable: otherwise

    JSONB Query:
        Uses extracted_notes->>'session_mood' to extract mood as text,
        then maps to numeric score using CASE statement.
    """
    # Detect database dialect for cross-database compatibility
    dialect_name = db.bind.dialect.name

    # Query sessions grouped by month with mood data
    # Extract session_mood from extracted_notes JSONB and convert to numeric score
    if dialect_name == 'postgresql':
        month_expr = func.to_char(TherapySession.session_date, 'YYYY-MM').label('month')
    else:  # sqlite
        month_expr = func.strftime('%Y-%m', TherapySession.session_date).label('month')

    mood_query = select(
        month_expr,
        func.avg(
            func.cast(
                func.case(
                    (TherapySession.extracted_notes['session_mood'].astext == 'very_low', 1),
                    (TherapySession.extracted_notes['session_mood'].astext == 'low', 2),
                    (TherapySession.extracted_notes['session_mood'].astext == 'neutral', 3),
                    (TherapySession.extracted_notes['session_mood'].astext == 'positive', 4),
                    (TherapySession.extracted_notes['session_mood'].astext == 'very_positive', 5),
                    else_=3  # Default to neutral if missing
                ),
                float
            )
        ).label('avg_mood')
    ).where(
        and_(
            TherapySession.patient_id == patient_id,
            TherapySession.extracted_notes.isnot(None)
        )
    ).group_by('month').order_by('month')

    mood_result = await db.execute(mood_query)
    mood_data_raw = mood_result.all()

    # Build MoodTrendData list
    # Note: Currently using same avg for pre and post since we don't track separate pre/post scores
    # In future, could extract from JSONB if pre/post mood scores are stored
    mood_data = [
        MoodTrendData(
            date=row.month,
            avg_pre=round(row.avg_mood, 2),
            avg_post=round(row.avg_mood, 2)
        )
        for row in mood_data_raw
    ]

    # Determine overall trend
    if len(mood_data) < 2:
        trend = "stable"
    else:
        # Compare first half vs second half of data
        midpoint = len(mood_data) // 2
        first_half_avg = sum(d.avg_post for d in mood_data[:midpoint]) / midpoint
        second_half_avg = sum(d.avg_post for d in mood_data[midpoint:]) / (len(mood_data) - midpoint)

        if second_half_avg > first_half_avg + 0.3:  # Threshold for "improving"
            trend = "improving"
        elif second_half_avg < first_half_avg - 0.3:  # Threshold for "declining"
            trend = "declining"
        else:
            trend = "stable"

    logger.debug(
        f"Mood trend for patient {patient_id}: {len(mood_data)} months, trend={trend}"
    )

    return MoodTrend(
        data=mood_data,
        trend=trend
    )


async def _calculate_goals(patient_id: UUID, db: AsyncSession) -> GoalStatus:
    """
    Calculate goal status from treatment_goals table.

    Queries the treatment_goals table for all goals assigned to a patient
    and counts them by status (assigned, in_progress, completed, abandoned).

    Args:
        patient_id: UUID of the patient to calculate goal status for
        db: Async database session

    Returns:
        GoalStatus: Counts of goals by status

    Status Mapping:
        - not_started: Goals with status 'assigned'
        - in_progress: Goals with status 'in_progress'
        - completed: Goals with status 'completed' or 'abandoned'

    Note: Previously extracted from action_items in therapy_sessions.extracted_notes JSONB.
    Now uses dedicated treatment_goals table for proper relational tracking.
    """
    from app.models.goal_models import TreatmentGoal

    # Query all goals for patient
    query = select(TreatmentGoal).where(
        TreatmentGoal.patient_id == patient_id
    )
    result = await db.execute(query)
    goals = result.scalars().all()

    # Count by status
    total = len(goals)
    completed = len([g for g in goals if g.status == 'completed'])
    in_progress = len([g for g in goals if g.status == 'in_progress'])
    not_started = len([g for g in goals if g.status == 'assigned'])

    logger.debug(
        f"Goal status calculated for patient {patient_id}: total={total}, "
        f"completed={completed}, in_progress={in_progress}, not_started={not_started}"
    )

    return GoalStatus(
        total=total,
        completed=completed,
        in_progress=in_progress,
        not_started=not_started
    )
