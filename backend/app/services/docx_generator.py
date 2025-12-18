"""DOCX generation service using python-docx"""
import logging
from io import BytesIO
from typing import Dict, Any, List, Optional
from datetime import datetime

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

logger = logging.getLogger(__name__)


class DOCXGeneratorService:
    """Service for generating DOCX documents"""

    def __init__(self):
        """Initialize DOCX generator"""
        pass

    async def generate_progress_report(
        self,
        patient: Dict[str, Any],
        therapist: Dict[str, Any],
        goals: List[Dict[str, Any]],
        sessions: List[Dict[str, Any]],
        date_range: Dict[str, datetime],
        include_sections: Dict[str, bool]
    ) -> bytes:
        """
        Generate progress report DOCX.

        Args:
            patient: Patient data
            therapist: Therapist data
            goals: Treatment goals with progress
            sessions: Session summaries
            date_range: {start_date, end_date}
            include_sections: Which sections to include

        Returns:
            DOCX file as bytes
        """
        try:
            logger.info("Starting DOCX progress report generation")

            doc = Document()

            # Add confidentiality notice
            heading = doc.add_paragraph("CONFIDENTIAL - PROTECTED HEALTH INFORMATION")
            heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
            heading.runs[0].font.color.rgb = RGBColor(211, 47, 47)
            heading.runs[0].font.bold = True

            # Add title
            title = doc.add_heading('Progress Report', 0)

            # Add header information
            doc.add_paragraph(f"Patient: {patient['full_name']}")
            doc.add_paragraph(
                f"Period: {date_range['start_date'].strftime('%B %d, %Y')} - "
                f"{date_range['end_date'].strftime('%B %d, %Y')}"
            )
            doc.add_paragraph(f"Prepared by: {therapist['full_name']}")
            doc.add_paragraph("")  # Blank line

            # Patient information section
            if include_sections.get('patient_info', True):
                doc.add_heading('Patient Information', 1)
                doc.add_paragraph(f"Name: {patient['full_name']}")
                doc.add_paragraph(f"Email: {patient.get('email', 'N/A')}")
                doc.add_paragraph("")

            # Treatment goals section
            if include_sections.get('treatment_goals', True) and goals:
                doc.add_heading('Treatment Goals & Progress', 1)

                # Create table
                table = doc.add_table(rows=1, cols=4)
                table.style = 'Light Grid Accent 1'

                # Header row
                hdr_cells = table.rows[0].cells
                hdr_cells[0].text = 'Goal'
                hdr_cells[1].text = 'Baseline'
                hdr_cells[2].text = 'Current'
                hdr_cells[3].text = 'Progress'

                # Data rows
                for goal in goals:
                    row_cells = table.add_row().cells
                    row_cells[0].text = goal['description']
                    row_cells[1].text = str(goal.get('baseline', 'N/A'))
                    row_cells[2].text = str(goal.get('current', 'N/A'))
                    row_cells[3].text = f"{goal.get('progress_percentage', 0)}%"

                doc.add_paragraph("")

            # Session summary section
            if include_sections.get('session_summary', True):
                doc.add_heading('Session Summary', 1)
                doc.add_paragraph(f"Total Sessions: {len(sessions)}")

                if sessions:
                    avg_duration = sum(s.get('duration_minutes', 0) for s in sessions) / len(sessions)
                    doc.add_paragraph(f"Average Duration: {avg_duration:.1f} minutes")

                doc.add_paragraph("")

            # Save to bytes
            buffer = BytesIO()
            doc.save(buffer)
            buffer.seek(0)
            docx_bytes = buffer.read()

            logger.info(
                f"DOCX generated successfully",
                extra={"size_kb": len(docx_bytes) / 1024}
            )

            return docx_bytes

        except Exception as e:
            logger.error(f"DOCX generation failed: {e}", exc_info=True)
            raise ValueError(f"Failed to generate DOCX: {str(e)}")

    async def generate_treatment_summary(
        self,
        patient: Dict[str, Any],
        therapist: Dict[str, Any],
        treatment_data: Dict[str, Any],
        include_sections: Dict[str, bool]
    ) -> bytes:
        """Generate treatment summary DOCX"""
        # Similar structure to progress_report
        # ... implementation ...
        pass


def get_docx_generator() -> DOCXGeneratorService:
    """FastAPI dependency to provide DOCX generator service"""
    return DOCXGeneratorService()
