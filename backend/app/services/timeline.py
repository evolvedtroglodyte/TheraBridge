"""
Timeline Service for Session Timeline Feature

Provides business logic for timeline operations including:
- Fetching patient timeline with filtering and pagination
- Creating, retrieving, and deleting timeline events
- Cursor-based pagination for efficient timeline browsing
"""
from uuid import UUID
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from app.models.db_models import TimelineEvent, User, TherapySession
from app.models.analytics_models import SessionMetrics
from app.models.schemas import (
    TimelineEventCreate,
    TimelineEventResponse,
    SessionTimelineResponse,
    TimelineImportance,
    TimelineSummaryResponse,
    TimelineChartDataResponse
)
import logging

logger = logging.getLogger(__name__)


async def get_patient_timeline(
    patient_id: UUID,
    db: AsyncSession,
    event_types: Optional[List[str]] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    importance: Optional[TimelineImportance] = None,
    search: Optional[str] = None,
    limit: int = 20,
    cursor: Optional[UUID] = None
) -> SessionTimelineResponse:
    """
    Fetch patient timeline with filtering and cursor-based pagination.

    Retrieves timeline events for a specific patient with optional filtering
    by event types, date range, importance level, and text search. Uses
    cursor-based pagination for efficient browsing of large timelines.

    Args:
        patient_id: UUID of the patient whose timeline to fetch
        db: Async database session
        event_types: Optional list of event types to filter by (e.g., ['session', 'milestone'])
        start_date: Optional start date for date range filter (inclusive)
        end_date: Optional end date for date range filter (inclusive)
        importance: Optional importance level filter ('low', 'normal', 'high', 'milestone')
        search: Optional text search term (searches title and description)
        limit: Maximum number of events to return (default 20, max 100)
        cursor: Optional UUID cursor for pagination (returns events after this ID)

    Returns:
        SessionTimelineResponse: Pydantic model containing:
            - events: List of TimelineEventResponse objects
            - next_cursor: UUID of last event for pagination (None if no more)
            - has_more: Boolean indicating if more events are available
            - total_count: Total number of events matching the filters

    Pagination:
        - Uses cursor-based pagination with event ID
        - Events ordered by event_date DESC (newest first), then id DESC
        - Cursor represents the ID of the last event from previous page
        - If cursor provided, returns events with id < cursor
        - next_cursor is the id of the last event in current page

    Filtering:
        - event_types: Filters to specific event types (OR condition)
        - start_date/end_date: Filters to date range (inclusive)
        - importance: Filters to specific importance level
        - search: Case-insensitive search in title and description

    Example:
        >>> # Get first page of timeline
        >>> timeline = await get_patient_timeline(patient_uuid, db, limit=20)
        >>> # Get next page using cursor
        >>> next_page = await get_patient_timeline(
        ...     patient_uuid, db, limit=20, cursor=timeline.next_cursor
        ... )
        >>> # Filter by event types and date range
        >>> filtered = await get_patient_timeline(
        ...     patient_uuid, db,
        ...     event_types=['session', 'milestone'],
        ...     start_date=datetime(2024, 1, 1),
        ...     end_date=datetime(2024, 12, 31)
        ... )
    """
    logger.info(
        f"Fetching timeline for patient {patient_id}: "
        f"event_types={event_types}, date_range={start_date} to {end_date}, "
        f"importance={importance}, search={search}, limit={limit}, cursor={cursor}"
    )

    # Validate and cap limit
    if limit <= 0:
        limit = 20
    if limit > 100:
        logger.warning(f"Limit {limit} exceeds maximum, capping to 100")
        limit = 100

    # Build base query
    query = select(TimelineEvent).where(TimelineEvent.patient_id == patient_id)

    # Apply filters
    if event_types:
        query = query.where(TimelineEvent.event_type.in_(event_types))

    if start_date:
        query = query.where(TimelineEvent.event_date >= start_date)

    if end_date:
        query = query.where(TimelineEvent.event_date <= end_date)

    if importance:
        query = query.where(TimelineEvent.importance == importance.value)

    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            or_(
                TimelineEvent.title.ilike(search_pattern),
                TimelineEvent.description.ilike(search_pattern)
            )
        )

    # Apply cursor-based pagination
    if cursor:
        # Get the event_date of the cursor event to handle ties correctly
        cursor_query = select(TimelineEvent.event_date, TimelineEvent.id).where(
            TimelineEvent.id == cursor
        )
        cursor_result = await db.execute(cursor_query)
        cursor_row = cursor_result.first()

        if cursor_row:
            cursor_date, cursor_id = cursor_row
            # Filter events that come after the cursor (older events)
            # Use composite filter to handle events with same date
            query = query.where(
                or_(
                    TimelineEvent.event_date < cursor_date,
                    and_(
                        TimelineEvent.event_date == cursor_date,
                        TimelineEvent.id < cursor_id
                    )
                )
            )

    # Order by event_date DESC (newest first), then id DESC for stable ordering
    query = query.order_by(desc(TimelineEvent.event_date), desc(TimelineEvent.id))

    # Fetch limit + 1 to determine if there are more results
    query = query.limit(limit + 1)

    # Execute query
    result = await db.execute(query)
    events_raw = result.scalars().all()

    # Determine if there are more results
    has_more = len(events_raw) > limit
    events = events_raw[:limit]  # Trim to requested limit

    # Calculate next cursor
    next_cursor = events[-1].id if has_more and events else None

    # Calculate total count (for all matching filters, not just current page)
    count_query = select(func.count(TimelineEvent.id)).where(
        TimelineEvent.patient_id == patient_id
    )

    # Apply same filters to count query
    if event_types:
        count_query = count_query.where(TimelineEvent.event_type.in_(event_types))
    if start_date:
        count_query = count_query.where(TimelineEvent.event_date >= start_date)
    if end_date:
        count_query = count_query.where(TimelineEvent.event_date <= end_date)
    if importance:
        count_query = count_query.where(TimelineEvent.importance == importance.value)
    if search:
        search_pattern = f"%{search}%"
        count_query = count_query.where(
            or_(
                TimelineEvent.title.ilike(search_pattern),
                TimelineEvent.description.ilike(search_pattern)
            )
        )

    count_result = await db.execute(count_query)
    total_count = count_result.scalar() or 0

    # Convert to response schemas
    event_responses = [
        TimelineEventResponse.model_validate(event) for event in events
    ]

    logger.info(
        f"Timeline fetched for patient {patient_id}: "
        f"returned {len(event_responses)} events, has_more={has_more}, total_count={total_count}"
    )

    return SessionTimelineResponse(
        events=event_responses,
        next_cursor=next_cursor,
        has_more=has_more,
        total_count=total_count
    )


async def create_timeline_event(
    patient_id: UUID,
    event_data: TimelineEventCreate,
    therapist_id: Optional[UUID],
    db: AsyncSession
) -> TimelineEventResponse:
    """
    Create a new timeline event for a patient.

    Creates a timeline event record with the provided data. Validates that
    the patient exists before creating the event.

    Args:
        patient_id: UUID of the patient this event belongs to
        event_data: TimelineEventCreate schema with event details
        therapist_id: Optional UUID of the therapist creating the event
        db: Async database session

    Returns:
        TimelineEventResponse: Newly created event with id and created_at

    Raises:
        ValueError: If patient_id does not exist in the database

    Event Types:
        - session: Therapy session events
        - milestone: Treatment milestones (e.g., "100th session", "6 months progress")
        - clinical: Clinical events (diagnosis, treatment plan updates)
        - administrative: Administrative notes
        - goal: Goal-related events (created, achieved, modified)
        - assessment: Assessment or evaluation events
        - note: General clinical notes

    Importance Levels:
        - low: Routine events
        - normal: Standard events (default)
        - high: Important events
        - milestone: Significant milestones

    Example:
        >>> event_data = TimelineEventCreate(
        ...     event_type="milestone",
        ...     event_date=datetime.now(),
        ...     title="50th session completed",
        ...     description="Patient has shown consistent progress",
        ...     importance=TimelineImportance.milestone
        ... )
        >>> event = await create_timeline_event(
        ...     patient_uuid, event_data, therapist_uuid, db
        ... )
    """
    logger.info(
        f"Creating timeline event for patient {patient_id}: "
        f"type={event_data.event_type}, title={event_data.title}"
    )

    # Validate patient exists
    patient_query = select(User).where(
        and_(User.id == patient_id, User.role == 'patient')
    )
    patient_result = await db.execute(patient_query)
    patient = patient_result.scalar_one_or_none()

    if not patient:
        logger.error(f"Patient {patient_id} not found")
        raise ValueError(f"Patient with id {patient_id} does not exist")

    # Create timeline event
    timeline_event = TimelineEvent(
        patient_id=patient_id,
        therapist_id=therapist_id,
        event_type=event_data.event_type,
        event_subtype=event_data.event_subtype,
        event_date=event_data.event_date,
        title=event_data.title,
        description=event_data.description,
        metadata=event_data.metadata,
        related_entity_type=event_data.related_entity_type,
        related_entity_id=event_data.related_entity_id,
        importance=event_data.importance.value if event_data.importance else 'normal',
        is_private=event_data.is_private
    )

    db.add(timeline_event)
    await db.commit()
    await db.refresh(timeline_event)

    logger.info(
        f"Timeline event created: id={timeline_event.id}, patient={patient_id}, "
        f"type={timeline_event.event_type}, date={timeline_event.event_date}"
    )

    return TimelineEventResponse.model_validate(timeline_event)


async def get_timeline_event(
    event_id: UUID,
    db: AsyncSession
) -> Optional[TimelineEventResponse]:
    """
    Retrieve a single timeline event by ID.

    Fetches a timeline event by its unique identifier. Returns None if
    the event does not exist.

    Args:
        event_id: UUID of the timeline event to retrieve
        db: Async database session

    Returns:
        Optional[TimelineEventResponse]: Event data if found, None otherwise

    Example:
        >>> event = await get_timeline_event(event_uuid, db)
        >>> if event:
        ...     print(f"Event: {event.title} on {event.event_date}")
        ... else:
        ...     print("Event not found")
    """
    logger.info(f"Fetching timeline event {event_id}")

    query = select(TimelineEvent).where(TimelineEvent.id == event_id)
    result = await db.execute(query)
    event = result.scalar_one_or_none()

    if not event:
        logger.info(f"Timeline event {event_id} not found")
        return None

    logger.info(f"Timeline event {event_id} found: {event.title}")
    return TimelineEventResponse.model_validate(event)


async def delete_timeline_event(
    event_id: UUID,
    db: AsyncSession
) -> bool:
    """
    Delete a timeline event by ID.

    Removes a timeline event from the database. Returns True if the event
    was found and deleted, False if the event did not exist.

    Args:
        event_id: UUID of the timeline event to delete
        db: Async database session

    Returns:
        bool: True if event was deleted, False if event was not found

    Note:
        This is a hard delete - the event is permanently removed from the database.
        Consider implementing soft deletes (is_deleted flag) if event history
        needs to be preserved for audit purposes.

    Example:
        >>> deleted = await delete_timeline_event(event_uuid, db)
        >>> if deleted:
        ...     print("Event deleted successfully")
        ... else:
        ...     print("Event not found")
    """
    logger.info(f"Deleting timeline event {event_id}")

    # Query for the event
    query = select(TimelineEvent).where(TimelineEvent.id == event_id)
    result = await db.execute(query)
    event = result.scalar_one_or_none()

    if not event:
        logger.info(f"Timeline event {event_id} not found, cannot delete")
        return False

    # Delete the event
    await db.delete(event)
    await db.commit()

    logger.info(f"Timeline event {event_id} deleted successfully")
    return True


async def get_timeline_summary(
    patient_id: UUID,
    db: AsyncSession
) -> TimelineSummaryResponse:
    """
    Calculate summary statistics for a patient's timeline.

    Provides an overview of the patient's therapy journey including session counts,
    event distribution by type, milestones achieved, and recent highlights. This
    data powers the timeline summary dashboard widget.

    Args:
        patient_id: UUID of the patient to calculate summary for
        db: Async database session

    Returns:
        TimelineSummaryResponse: Pydantic model containing timeline statistics:
            - patient_id: Patient identifier
            - first_session: Date of first therapy session
            - last_session: Date of most recent therapy session
            - total_sessions: Total count of therapy sessions
            - total_events: Total count of timeline events
            - events_by_type: Dictionary mapping event types to counts
            - milestones_achieved: Count of milestone-importance events
            - recent_highlights: List of recent milestone events (last 3)

    Metrics Calculated:
        1. total_events: Count all timeline events for patient
        2. events_by_type: Group events by event_type and count each
        3. milestones_achieved: Count events where importance='milestone'
        4. Session stats: Query therapy_sessions for first, last, and total
        5. recent_highlights: Last 3 milestone events with title, date, description

    Event Type Grouping:
        Uses SQLAlchemy func.count() with group_by to efficiently count events
        by type in a single query rather than multiple individual queries.

    Recent Highlights Format:
        Each highlight is a dict with:
        - id: Event UUID (as string)
        - title: Event title
        - event_date: Event date (ISO format string)
        - description: Event description
        - event_type: Type of event

    Example:
        >>> summary = await get_timeline_summary(patient_uuid, db)
        >>> print(f"Total sessions: {summary.total_sessions}")
        >>> print(f"Milestones: {summary.milestones_achieved}")
        >>> print(f"Event breakdown: {summary.events_by_type}")
    """
    logger.info(f"Calculating timeline summary for patient {patient_id}")

    # 1. Calculate total_events
    total_events_query = select(func.count(TimelineEvent.id)).where(
        TimelineEvent.patient_id == patient_id
    )
    total_events_result = await db.execute(total_events_query)
    total_events = total_events_result.scalar() or 0

    # 2. Calculate events_by_type (grouped aggregation)
    events_by_type_query = select(
        TimelineEvent.event_type,
        func.count(TimelineEvent.id).label('count')
    ).where(
        TimelineEvent.patient_id == patient_id
    ).group_by(TimelineEvent.event_type)

    events_by_type_result = await db.execute(events_by_type_query)
    events_by_type_rows = events_by_type_result.all()

    # Convert to dictionary
    events_by_type: Dict[str, int] = {
        row.event_type: row.count for row in events_by_type_rows
    }

    # 3. Calculate milestones_achieved
    milestones_query = select(func.count(TimelineEvent.id)).where(
        and_(
            TimelineEvent.patient_id == patient_id,
            TimelineEvent.importance == 'milestone'
        )
    )
    milestones_result = await db.execute(milestones_query)
    milestones_achieved = milestones_result.scalar() or 0

    # 4. Query therapy_sessions for session stats
    sessions_query = select(
        func.min(TherapySession.session_date).label('first_session'),
        func.max(TherapySession.session_date).label('last_session'),
        func.count(TherapySession.id).label('total_sessions')
    ).where(
        and_(
            TherapySession.patient_id == patient_id,
            TherapySession.status != 'failed'
        )
    )
    sessions_result = await db.execute(sessions_query)
    sessions_row = sessions_result.first()

    first_session = sessions_row.first_session.date() if sessions_row and sessions_row.first_session else None
    last_session = sessions_row.last_session.date() if sessions_row and sessions_row.last_session else None
    total_sessions = sessions_row.total_sessions if sessions_row else 0

    # 5. Get recent highlights (last 3 milestone events)
    highlights_query = select(TimelineEvent).where(
        and_(
            TimelineEvent.patient_id == patient_id,
            TimelineEvent.importance == 'milestone'
        )
    ).order_by(desc(TimelineEvent.event_date)).limit(3)

    highlights_result = await db.execute(highlights_query)
    highlights_events = highlights_result.scalars().all()

    # Convert to dict format for response
    recent_highlights: List[Dict[str, Any]] = [
        {
            'id': str(event.id),
            'title': event.title,
            'event_date': event.event_date.isoformat(),
            'description': event.description or '',
            'event_type': event.event_type
        }
        for event in highlights_events
    ]

    logger.info(
        f"Timeline summary calculated for patient {patient_id}: "
        f"total_events={total_events}, total_sessions={total_sessions}, "
        f"milestones={milestones_achieved}, event_types={len(events_by_type)}"
    )

    return TimelineSummaryResponse(
        patient_id=patient_id,
        first_session=first_session,
        last_session=last_session,
        total_sessions=total_sessions,
        total_events=total_events,
        events_by_type=events_by_type,
        milestones_achieved=milestones_achieved,
        recent_highlights=recent_highlights
    )


async def get_timeline_chart_data(
    patient_id: UUID,
    db: AsyncSession
) -> TimelineChartDataResponse:
    """
    Get chart visualization data for patient timeline dashboard.

    Aggregates patient data into chart-friendly formats for frontend visualization.
    Provides mood trends over time, session frequency distribution, and milestone
    timeline for graphical display.

    Args:
        patient_id: UUID of the patient to generate chart data for
        db: Async database session

    Returns:
        TimelineChartDataResponse: Pydantic model containing chart data:
            - mood_trend: List of monthly mood averages
            - session_frequency: List of monthly session counts
            - milestones: List of milestone events with dates

    Chart Data Formats:

    1. mood_trend (monthly mood averages):
        [
            {'month': '2024-01', 'avg_mood': 3.5},
            {'month': '2024-02', 'avg_mood': 4.2},
            ...
        ]
        - Queries session_metrics table for mood_post scores
        - Groups by month using func.to_char(date, 'YYYY-MM')
        - Calculates average mood per month (1-10 scale)
        - Ordered chronologically (oldest to newest)

    2. session_frequency (monthly session counts):
        [
            {'month': '2024-01', 'count': 4},
            {'month': '2024-02', 'count': 5},
            ...
        ]
        - Queries therapy_sessions table
        - Groups by month using func.to_char(session_date, 'YYYY-MM')
        - Counts sessions per month (excludes failed sessions)
        - Ordered chronologically

    3. milestones (milestone events timeline):
        [
            {
                'date': '2024-01-15',
                'title': '10th session completed',
                'description': 'Making great progress',
                'event_type': 'milestone'
            },
            ...
        ]
        - Queries timeline_events where importance='milestone'
        - Includes date, title, description, event_type
        - Ordered by date (oldest to newest)
        - Limited to milestones only for visual clarity

    PostgreSQL Functions Used:
        - func.to_char(): Formats dates as 'YYYY-MM' for month grouping
        - func.avg(): Calculates average mood scores
        - func.count(): Counts sessions per month
        - func.date_trunc(): Could be used for month grouping alternative

    Edge Cases Handled:
        - No mood data: Returns empty mood_trend list
        - No sessions: Returns empty session_frequency list
        - No milestones: Returns empty milestones list
        - Missing mood scores: Excluded from average calculation

    Example:
        >>> chart_data = await get_timeline_chart_data(patient_uuid, db)
        >>> # mood_trend: [{'month': '2024-01', 'avg_mood': 3.8}, ...]
        >>> # session_frequency: [{'month': '2024-01', 'count': 4}, ...]
        >>> # milestones: [{'date': '2024-01-15', 'title': '...', ...}, ...]
    """
    logger.info(f"Generating timeline chart data for patient {patient_id}")

    # 1. Mood trend: Query session_metrics for monthly mood averages
    mood_query = select(
        func.to_char(SessionMetrics.session_date, 'YYYY-MM').label('month'),
        func.avg(SessionMetrics.mood_post).label('avg_mood')
    ).where(
        and_(
            SessionMetrics.patient_id == patient_id,
            SessionMetrics.mood_post.isnot(None)
        )
    ).group_by('month').order_by('month')

    mood_result = await db.execute(mood_query)
    mood_rows = mood_result.all()

    mood_trend: List[Dict[str, Any]] = [
        {
            'month': row.month,
            'avg_mood': round(float(row.avg_mood), 2) if row.avg_mood else 0.0
        }
        for row in mood_rows
    ]

    # 2. Session frequency: Query therapy_sessions for monthly counts
    session_freq_query = select(
        func.to_char(TherapySession.session_date, 'YYYY-MM').label('month'),
        func.count(TherapySession.id).label('count')
    ).where(
        and_(
            TherapySession.patient_id == patient_id,
            TherapySession.status != 'failed'
        )
    ).group_by('month').order_by('month')

    session_freq_result = await db.execute(session_freq_query)
    session_freq_rows = session_freq_result.all()

    session_frequency: List[Dict[str, Any]] = [
        {
            'month': row.month,
            'count': row.count
        }
        for row in session_freq_rows
    ]

    # 3. Milestones: Query timeline_events for milestone events
    milestones_query = select(TimelineEvent).where(
        and_(
            TimelineEvent.patient_id == patient_id,
            TimelineEvent.importance == 'milestone'
        )
    ).order_by(TimelineEvent.event_date)

    milestones_result = await db.execute(milestones_query)
    milestones_events = milestones_result.scalars().all()

    milestones: List[Dict[str, Any]] = [
        {
            'date': event.event_date.strftime('%Y-%m-%d'),
            'title': event.title,
            'description': event.description or '',
            'event_type': event.event_type
        }
        for event in milestones_events
    ]

    logger.info(
        f"Chart data generated for patient {patient_id}: "
        f"mood_data_points={len(mood_trend)}, "
        f"session_freq_points={len(session_frequency)}, "
        f"milestones={len(milestones)}"
    )

    return TimelineChartDataResponse(
        mood_trend=mood_trend,
        session_frequency=session_frequency,
        milestones=milestones
    )


async def auto_generate_session_event(
    session: TherapySession,
    db: AsyncSession
) -> TimelineEventResponse:
    """
    Automatically generate a timeline event when a therapy session completes.

    Creates a timeline event record for a completed session, extracting relevant
    data from the session record. This function is called automatically when a
    session's processing status changes to 'processed'.

    Args:
        session: TherapySession object that was just processed
        db: Async database session

    Returns:
        TimelineEventResponse: Newly created timeline event for the session

    Event Generation Logic:
        1. Extract session number from session count for this patient
        2. Create title: "Session #{number}" (e.g., "Session #15")
        3. Extract summary from session.patient_summary (first 200 chars)
        4. Build metadata dict with session details
        5. Call create_timeline_event() with event_type='session'

    Metadata Structure:
        {
            'session_id': str(session.id),
            'duration_seconds': session.duration_seconds,
            'topics': [...],  # Extracted from session.extracted_notes
            'mood': '...',    # Extracted from session.extracted_notes
        }

    Title Format:
        - "Session #1", "Session #2", etc.
        - Uses actual count of patient's sessions to determine number
        - Sequential numbering based on session_date order

    Description:
        - Extracted from patient_summary field (first 200 characters)
        - Truncated with "..." if longer than 200 chars
        - Defaults to "Session completed" if no summary available

    Related Entity Linking:
        - related_entity_type: 'session'
        - related_entity_id: session.id
        - Enables bidirectional navigation between timeline and sessions

    Importance Level:
        - Normal importance by default
        - Could be upgraded to 'milestone' for significant sessions (10th, 50th, 100th)
        - Frontend can filter/highlight milestone sessions

    Example:
        >>> session = await db.get(TherapySession, session_id)
        >>> event = await auto_generate_session_event(session, db)
        >>> # Creates: "Session #15" timeline event with summary and metadata
    """
    logger.info(f"Auto-generating timeline event for session {session.id}, patient {session.patient_id}")

    # 1. Calculate session number for this patient
    session_count_query = select(func.count(TherapySession.id)).where(
        and_(
            TherapySession.patient_id == session.patient_id,
            TherapySession.session_date <= session.session_date,
            TherapySession.status != 'failed'
        )
    )
    session_count_result = await db.execute(session_count_query)
    session_number = session_count_result.scalar() or 1

    # 2. Create title
    title = f"Session #{session_number}"

    # 3. Extract summary (first 200 chars from patient_summary)
    description = "Session completed"
    if session.patient_summary:
        summary_text = session.patient_summary[:200]
        description = summary_text + "..." if len(session.patient_summary) > 200 else summary_text

    # 4. Build metadata dict
    metadata: Dict[str, Any] = {
        'session_id': str(session.id),
        'duration_seconds': session.duration_seconds
    }

    # Extract additional metadata from extracted_notes if available
    if session.extracted_notes:
        # Add topics discussed
        key_topics = session.extracted_notes.get('key_topics', [])
        if key_topics:
            metadata['topics'] = key_topics

        # Add mood information
        session_mood = session.extracted_notes.get('session_mood')
        if session_mood:
            metadata['mood'] = session_mood

    # 5. Determine importance (milestone for every 10th session)
    importance = TimelineImportance.milestone if session_number % 10 == 0 else TimelineImportance.normal

    # 6. Create event data
    event_data = TimelineEventCreate(
        event_type='session',
        event_subtype=None,
        event_date=session.session_date,
        title=title,
        description=description,
        metadata=metadata,
        related_entity_type='session',
        related_entity_id=session.id,
        importance=importance,
        is_private=False
    )

    # 7. Call create_timeline_event to persist
    event = await create_timeline_event(
        patient_id=session.patient_id,
        event_data=event_data,
        therapist_id=session.therapist_id,
        db=db
    )

    logger.info(
        f"Timeline event auto-generated: id={event.id}, session_number={session_number}, "
        f"title='{title}', importance={importance.value}"
    )

    return event
