"""Export orchestration service - coordinates data gathering and export generation"""
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from uuid import UUID
import json
from collections import Counter

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import joinedload

from app.models.db_models import User, TherapySession, TherapistPatient
from app.models.export_models import ExportJob, ExportTemplate
from app.services.pdf_generator import PDFGeneratorService
from app.services.docx_generator import DOCXGeneratorService

logger = logging.getLogger(__name__)


class ExportService:
    """Service for coordinating export generation"""

    def __init__(
        self,
        pdf_generator: PDFGeneratorService,
        docx_generator: DOCXGeneratorService
    ):
        self.pdf_generator = pdf_generator
        self.docx_generator = docx_generator
        self.export_dir = Path("exports/output")
        self.export_dir.mkdir(parents=True, exist_ok=True)

    async def gather_session_notes_data(
        self,
        session_ids: List[UUID],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Gather data for session notes export.

        Args:
            session_ids: List of session UUIDs to export
            db: Database session

        Returns:
            Context dict with sessions, therapist, patient data

        Raises:
            ValueError: If no sessions found
        """
        # Query sessions with relationships using joinedload to avoid N+1 queries
        query = (
            select(TherapySession)
            .where(TherapySession.id.in_(session_ids))
            .options(joinedload(TherapySession.patient))
            .options(joinedload(TherapySession.therapist))
        )
        result = await db.execute(query)
        sessions = result.scalars().unique().all()

        if not sessions:
            raise ValueError("No sessions found")

        # Extract therapist and patients
        therapist = sessions[0].therapist
        patients = {s.patient_id: s.patient for s in sessions if s.patient}

        return {
            "sessions": [self._serialize_session(s) for s in sessions],
            "therapist": self._serialize_user(therapist),
            "patients": {str(pid): self._serialize_user(p) for pid, p in patients.items()},
            "session_count": len(sessions)
        }

    async def gather_progress_report_data(
        self,
        patient_id: UUID,
        start_date: datetime,
        end_date: datetime,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Gather data for progress report export.

        Args:
            patient_id: Patient UUID
            start_date: Report start date
            end_date: Report end date
            db: Database session

        Returns:
            Context dict with patient, therapist, sessions, goals, metrics

        Raises:
            ValueError: If patient not found
        """
        # Query patient
        patient_result = await db.execute(
            select(User).where(User.id == patient_id)
        )
        patient = patient_result.scalar_one_or_none()

        if not patient:
            raise ValueError(f"Patient {patient_id} not found")

        # Query therapist relationship
        therapist_rel = await db.execute(
            select(TherapistPatient)
            .where(
                and_(
                    TherapistPatient.patient_id == patient_id,
                    TherapistPatient.is_active == True,
                    TherapistPatient.relationship_type == 'primary'
                )
            )
            .options(joinedload(TherapistPatient.therapist))
        )
        relationship = therapist_rel.scalar_one_or_none()
        therapist = relationship.therapist if relationship else None

        # Query sessions in date range
        sessions_query = (
            select(TherapySession)
            .where(
                and_(
                    TherapySession.patient_id == patient_id,
                    TherapySession.session_date >= start_date,
                    TherapySession.session_date <= end_date,
                    TherapySession.status == 'processed'
                )
            )
            .order_by(TherapySession.session_date.asc())
        )
        sessions_result = await db.execute(sessions_query)
        sessions = sessions_result.scalars().all()

        # Extract goals from extracted_notes JSONB field
        goals = []
        for session in sessions:
            if session.extracted_notes:
                session_goals = session.extracted_notes.get('treatment_goals', [])
                # Add goals to list (simple implementation - could be enhanced with tracking)
                for goal in session_goals:
                    if isinstance(goal, dict):
                        goals.append(goal)
                    elif isinstance(goal, str):
                        goals.append({'description': goal, 'baseline': 'N/A', 'current': 'N/A', 'progress_percentage': 0})

        # Calculate metrics
        session_count = len(sessions)
        avg_duration = (
            sum(s.duration_seconds for s in sessions if s.duration_seconds) / session_count / 60
            if session_count > 0 else 0
        )

        # Extract key topics from extracted_notes
        all_topics = []
        for session in sessions:
            if session.extracted_notes:
                all_topics.extend(session.extracted_notes.get('key_topics', []))

        # Count topic frequency
        topic_counts = Counter(all_topics)
        key_topics = [topic for topic, count in topic_counts.most_common(10)]

        return {
            "patient": self._serialize_user(patient),
            "therapist": self._serialize_user(therapist) if therapist else None,
            "start_date": start_date,
            "end_date": end_date,
            "sessions": [self._serialize_session(s) for s in sessions],
            "session_count": session_count,
            "avg_duration_minutes": round(avg_duration, 1),
            "goals": goals,
            "key_topics": key_topics
        }

    async def gather_timeline_data(
        self,
        patient_id: UUID,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        event_types: Optional[List[str]],
        include_private: bool,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Gather data for timeline export.

        Args:
            patient_id: Patient UUID
            start_date: Optional start date filter
            end_date: Optional end date filter
            event_types: Optional event type filter
            include_private: Whether to include private events
            db: Database session

        Returns:
            Context dict with patient, therapist, timeline events, summary

        Raises:
            ValueError: If patient not found
        """
        from app.services.timeline import get_patient_timeline, get_timeline_summary

        # Query patient
        patient_result = await db.execute(
            select(User).where(User.id == patient_id)
        )
        patient = patient_result.scalar_one_or_none()

        if not patient:
            raise ValueError(f"Patient {patient_id} not found")

        # Query therapist relationship
        therapist_rel = await db.execute(
            select(TherapistPatient)
            .where(
                and_(
                    TherapistPatient.patient_id == patient_id,
                    TherapistPatient.is_active == True,
                    TherapistPatient.relationship_type == 'primary'
                )
            )
            .options(joinedload(TherapistPatient.therapist))
        )
        relationship = therapist_rel.scalar_one_or_none()
        therapist = relationship.therapist if relationship else None

        # Fetch timeline data using timeline service
        timeline_response = await get_patient_timeline(
            patient_id=patient_id,
            db=db,
            event_types=event_types,
            start_date=start_date,
            end_date=end_date,
            limit=10000  # Large limit for full export
        )

        # Apply privacy filter if needed
        events = timeline_response.events
        if not include_private:
            events = [e for e in events if not e.is_private]

        # Get timeline summary for additional context
        summary = await get_timeline_summary(patient_id=patient_id, db=db)

        # Serialize events to dict format
        events_serialized = [
            {
                "id": str(event.id),
                "event_type": event.event_type,
                "event_subtype": event.event_subtype,
                "event_date": event.event_date,
                "title": event.title,
                "description": event.description,
                "importance": event.importance,
                "metadata": event.metadata,
                "is_private": event.is_private
            }
            for event in events
        ]

        return {
            "patient": self._serialize_user(patient),
            "therapist": self._serialize_user(therapist) if therapist else None,
            "start_date": start_date,
            "end_date": end_date,
            "event_types_filter": event_types,
            "events": events_serialized,
            "total_events": len(events_serialized),
            "summary": {
                "total_sessions": summary.total_sessions,
                "first_session": summary.first_session,
                "last_session": summary.last_session,
                "milestones_achieved": summary.milestones_achieved,
                "events_by_type": summary.events_by_type
            }
        }

    async def generate_export(
        self,
        export_type: str,
        format: str,
        context: Dict[str, Any],
        template_id: Optional[UUID] = None,
        db: AsyncSession = None
    ) -> bytes:
        """
        Generate export file.

        Args:
            export_type: 'session_notes', 'progress_report', etc.
            format: 'pdf', 'docx', 'json', 'csv'
            context: Data context for rendering
            template_id: Optional custom template UUID
            db: Database session (unused for now, reserved for template queries)

        Returns:
            Export file as bytes

        Raises:
            ValueError: If format is unsupported
        """
        logger.info(
            f"Generating export",
            extra={"type": export_type, "format": format}
        )

        if format == 'pdf':
            # Route to PDF generator with appropriate template
            template_name = f"{export_type}.html"
            return await self.pdf_generator.generate_from_template(
                template_name,
                context
            )

        elif format == 'docx':
            # Route to DOCX generator based on export type
            if export_type == 'progress_report':
                return await self.docx_generator.generate_progress_report(
                    patient=context['patient'],
                    therapist=context['therapist'],
                    goals=context.get('goals', []),
                    sessions=context['sessions'],
                    date_range={
                        'start_date': context['start_date'],
                        'end_date': context['end_date']
                    },
                    include_sections=context.get('include_sections', {})
                )
            elif export_type == 'treatment_summary':
                return await self.docx_generator.generate_treatment_summary(
                    patient=context['patient'],
                    therapist=context['therapist'],
                    treatment_data=context,
                    include_sections=context.get('include_sections', {})
                )
            elif export_type == 'timeline':
                return await self.docx_generator.generate_timeline_export(
                    patient=context['patient'],
                    therapist=context['therapist'],
                    events=context['events'],
                    summary=context['summary'],
                    date_range={
                        'start_date': context.get('start_date'),
                        'end_date': context.get('end_date')
                    }
                )
            else:
                # Fallback for unsupported DOCX export types
                raise ValueError(f"Unsupported DOCX export type: {export_type}")

        elif format == 'json':
            # JSON export - serialize context to JSON
            return json.dumps(context, indent=2, default=str).encode('utf-8')

        elif format == 'csv':
            # CSV generation logic (placeholder for future implementation)
            raise ValueError("CSV export format not yet implemented")

        else:
            raise ValueError(f"Unsupported format: {format}")

    def _serialize_user(self, user: Optional[User]) -> Optional[Dict[str, Any]]:
        """
        Convert User ORM model to dict for templates.

        Args:
            user: User model instance or None

        Returns:
            Dictionary representation or None
        """
        if not user:
            return None

        return {
            "id": str(user.id),
            "full_name": user.full_name or f"{user.first_name} {user.last_name}".strip(),
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "role": user.role.value
        }

    def _serialize_session(self, session: TherapySession) -> Dict[str, Any]:
        """
        Convert TherapySession ORM model to dict for templates.

        Args:
            session: TherapySession model instance

        Returns:
            Dictionary representation
        """
        return {
            "id": str(session.id),
            "session_date": session.session_date,
            "duration_minutes": session.duration_seconds / 60 if session.duration_seconds else None,
            "transcript_text": session.transcript_text,
            "extracted_notes": session.extracted_notes,
            "therapist_summary": session.therapist_summary,
            "patient_summary": session.patient_summary,
            "status": session.status
        }


def get_export_service(
    pdf_generator: PDFGeneratorService,
    docx_generator: DOCXGeneratorService
) -> ExportService:
    """
    FastAPI dependency to provide export service.

    Args:
        pdf_generator: PDF generation service instance
        docx_generator: DOCX generation service instance

    Returns:
        ExportService instance
    """
    return ExportService(pdf_generator, docx_generator)
