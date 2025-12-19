"""
Note template rendering service for applying templates to AI-extracted clinical notes.

This service handles the application of clinical note templates (SOAP, DAP, BIRP, etc.)
to extracted session data. It works alongside note_extraction.py to format AI-generated
notes according to therapist-specific or practice-specific templates.

Key Responsibilities:
- Apply templates to extracted notes (format existing data)
- Re-generate notes using custom templates (new GPT-4o call with template-specific prompts)
- Validate template structures
- Provide default templates for common formats

Related Services:
- note_extraction.py: Extracts raw clinical data from transcripts
- template_service.py: CRUD operations for managing template entities
- template_autofill.py: Auto-fills template fields from extracted notes
"""
import json
import logging
from typing import Dict, Any, Optional, List
from uuid import UUID
from jinja2 import Template, Environment, BaseLoader, TemplateError

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from app.models.db_models import NoteTemplate
from app.models.schemas import (
    ExtractedNotes,
    TemplateType,
    TemplateStructure
)
from app.services.note_extraction import NoteExtractionService

# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# Default Template Definitions
# ============================================================================

DEFAULT_TEMPLATES = {
    "soap": {
        "name": "SOAP Format",
        "description": "Subjective, Objective, Assessment, Plan - Standard clinical documentation format",
        "template_type": "soap",
        "sections": [
            {
                "id": "subjective",
                "name": "Subjective",
                "prompt": "What the client reported: their concerns, feelings, and subjective experiences. Include significant quotes and chief complaints.",
                "ai_mapping": ["key_topics", "topic_summary", "significant_quotes", "emotional_themes"]
            },
            {
                "id": "objective",
                "name": "Objective",
                "prompt": "Observable behaviors, clinical observations, and measurable data. Include mood, affect, presentation, and any objective measurements.",
                "ai_mapping": ["session_mood", "mood_trajectory", "triggers"]
            },
            {
                "id": "assessment",
                "name": "Assessment",
                "prompt": "Clinical assessment, diagnosis, and professional interpretation of the session. Include progress evaluation and risk assessment.",
                "ai_mapping": ["therapist_notes", "risk_flags", "unresolved_concerns"]
            },
            {
                "id": "plan",
                "name": "Plan",
                "prompt": "Treatment plan, homework assignments, next steps, and follow-up topics. Include strategies discussed and action items.",
                "ai_mapping": ["action_items", "strategies", "follow_up_topics"]
            }
        ]
    },
    "dap": {
        "name": "DAP Format",
        "description": "Data, Assessment, Plan - Concise clinical documentation format",
        "template_type": "dap",
        "sections": [
            {
                "id": "data",
                "name": "Data",
                "prompt": "Factual information from the session: what was discussed, observed behaviors, client statements, and measurable data.",
                "ai_mapping": ["key_topics", "topic_summary", "significant_quotes", "session_mood", "emotional_themes"]
            },
            {
                "id": "assessment",
                "name": "Assessment",
                "prompt": "Clinical assessment and professional interpretation. Include progress evaluation, diagnostic impressions, and risk assessment.",
                "ai_mapping": ["therapist_notes", "risk_flags", "triggers", "mood_trajectory"]
            },
            {
                "id": "plan",
                "name": "Plan",
                "prompt": "Treatment plan, interventions, homework, and next steps. Include strategies discussed and follow-up topics.",
                "ai_mapping": ["action_items", "strategies", "follow_up_topics", "unresolved_concerns"]
            }
        ]
    },
    "birp": {
        "name": "BIRP Format",
        "description": "Behavior, Intervention, Response, Plan - Intervention-focused documentation",
        "template_type": "birp",
        "sections": [
            {
                "id": "behavior",
                "name": "Behavior",
                "prompt": "Observable behaviors, presenting concerns, and client's subjective experience during the session.",
                "ai_mapping": ["key_topics", "topic_summary", "emotional_themes", "session_mood", "triggers"]
            },
            {
                "id": "intervention",
                "name": "Intervention",
                "prompt": "Therapeutic interventions, techniques used, and strategies discussed during the session.",
                "ai_mapping": ["strategies", "therapist_notes"]
            },
            {
                "id": "response",
                "name": "Response",
                "prompt": "Client's response to interventions, including mood changes, insights gained, and engagement level.",
                "ai_mapping": ["mood_trajectory", "significant_quotes", "unresolved_concerns"]
            },
            {
                "id": "plan",
                "name": "Plan",
                "prompt": "Treatment plan, homework assignments, follow-up topics, and next session goals.",
                "ai_mapping": ["action_items", "follow_up_topics", "risk_flags"]
            }
        ]
    },
    "progress": {
        "name": "Progress Note",
        "description": "General progress note format for ongoing therapy sessions",
        "template_type": "progress",
        "sections": [
            {
                "id": "summary",
                "name": "Session Summary",
                "prompt": "Brief overview of the session, including topics discussed and overall mood.",
                "ai_mapping": ["topic_summary", "key_topics", "session_mood"]
            },
            {
                "id": "clinical_observations",
                "name": "Clinical Observations",
                "prompt": "Observations about client's presentation, affect, engagement, and any notable changes since last session.",
                "ai_mapping": ["emotional_themes", "mood_trajectory", "triggers", "therapist_notes"]
            },
            {
                "id": "interventions",
                "name": "Interventions & Techniques",
                "prompt": "Therapeutic techniques used and strategies discussed during the session.",
                "ai_mapping": ["strategies"]
            },
            {
                "id": "progress",
                "name": "Progress & Insights",
                "prompt": "Client progress toward goals, insights gained, and significant breakthroughs or quotes.",
                "ai_mapping": ["significant_quotes", "mood_trajectory"]
            },
            {
                "id": "homework_plan",
                "name": "Homework & Next Steps",
                "prompt": "Action items, homework assignments, and topics to address in future sessions.",
                "ai_mapping": ["action_items", "follow_up_topics", "unresolved_concerns"]
            },
            {
                "id": "risk_assessment",
                "name": "Risk Assessment",
                "prompt": "Any safety concerns, risk flags, or crisis-related content discussed.",
                "ai_mapping": ["risk_flags"]
            }
        ]
    }
}


class NoteTemplateService:
    """
    Service for rendering clinical note templates and applying them to extracted notes.

    This service bridges the gap between AI-extracted data (from NoteExtractionService)
    and formatted clinical notes (based on therapist templates). It supports multiple
    template types (SOAP, DAP, BIRP, etc.) and handles both:
    1. Formatting existing extracted notes using a template
    2. Re-generating notes with a new template (requires new GPT-4o API call)
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize the note template service.

        Args:
            db: Async database session for template lookups
        """
        self.db = db
        self.jinja_env = Environment(loader=BaseLoader())

    async def apply_template(
        self,
        template_id: UUID,
        extracted_notes: ExtractedNotes
    ) -> Dict[str, Any]:
        """
        Apply a template to already-extracted notes, formatting them according to template sections.

        This method takes existing ExtractedNotes and re-formats them into a structured
        note following the template's section definitions. It does NOT call GPT-4o again;
        it simply reorganizes existing data.

        Args:
            template_id: UUID of the template to apply
            extracted_notes: Already-extracted notes from NoteExtractionService

        Returns:
            Dict with formatted note content:
            {
                "template_id": UUID,
                "template_name": str,
                "template_type": str,
                "sections": {
                    "section_id": {
                        "name": str,
                        "content": str
                    },
                    ...
                }
            }

        Raises:
            HTTPException: 404 if template not found
            HTTPException: 500 if template application fails
        """
        logger.info(
            "Applying template to extracted notes",
            extra={
                "template_id": str(template_id),
                "extracted_notes_keys": list(extracted_notes.model_dump().keys())
            }
        )

        try:
            # Load template from database
            template = await self._get_template(template_id)

            # Get template structure
            structure = template.structure

            # Format notes according to template sections
            formatted_sections = {}

            for section in structure.get("sections", []):
                section_id = section.get("id")
                section_name = section.get("name")
                ai_mapping = section.get("ai_mapping", [])

                # Extract relevant data from ExtractedNotes based on ai_mapping
                section_content = self._build_section_content(
                    extracted_notes=extracted_notes,
                    ai_mapping=ai_mapping,
                    section_name=section_name
                )

                formatted_sections[section_id] = {
                    "name": section_name,
                    "content": section_content
                }

            result = {
                "template_id": str(template_id),
                "template_name": template.name,
                "template_type": template.template_type,
                "sections": formatted_sections
            }

            logger.info(
                "Template applied successfully",
                extra={
                    "template_id": str(template_id),
                    "sections_count": len(formatted_sections)
                }
            )

            return result

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "Error applying template",
                extra={
                    "template_id": str(template_id),
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            raise HTTPException(
                status_code=500,
                detail=f"Failed to apply template: {str(e)}"
            ) from e

    async def generate_from_template(
        self,
        template_id: UUID,
        transcript: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Re-generate notes from transcript using a specific template.

        This method makes a NEW call to GPT-4o with a custom prompt based on the
        template's section definitions. Use this when a therapist wants to regenerate
        notes with a different template format than the original extraction.

        Args:
            template_id: UUID of the template to use for generation
            transcript: Full therapy session transcript
            session_id: Optional session identifier for logging

        Returns:
            Dict with generated note content (same structure as apply_template):
            {
                "template_id": UUID,
                "template_name": str,
                "template_type": str,
                "sections": {
                    "section_id": {
                        "name": str,
                        "content": str
                    },
                    ...
                }
            }

        Raises:
            HTTPException: 404 if template not found
            HTTPException: 500 if generation fails (GPT-4o error, etc.)
        """
        logger.info(
            "Generating notes from template",
            extra={
                "template_id": str(template_id),
                "transcript_length": len(transcript),
                "session_id": session_id
            }
        )

        try:
            # Load template from database
            template = await self._get_template(template_id)

            # Build custom GPT-4o prompt using template sections
            custom_prompt = self._build_custom_prompt(
                template=template,
                transcript=transcript
            )

            # Call OpenAI API with custom prompt
            extraction_service = NoteExtractionService()

            # Use the custom prompt to extract notes in template format
            response = await extraction_service.client.chat.completions.create(
                model=extraction_service.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a clinical psychology expert who generates structured clinical notes from therapy transcripts. Always return valid JSON."
                    },
                    {
                        "role": "user",
                        "content": custom_prompt
                    }
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            # Parse response
            response_text = response.choices[0].message.content

            # Handle potential markdown code blocks
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]

            generated_data = json.loads(response_text)

            # Format result
            result = {
                "template_id": str(template_id),
                "template_name": template.name,
                "template_type": template.template_type,
                "sections": generated_data.get("sections", {})
            }

            logger.info(
                "Notes generated from template successfully",
                extra={
                    "template_id": str(template_id),
                    "sections_count": len(result.get("sections", {})),
                    "session_id": session_id
                }
            )

            return result

        except HTTPException:
            raise
        except json.JSONDecodeError as e:
            logger.error(
                "JSON parsing failed for GPT-4o response",
                extra={
                    "template_id": str(template_id),
                    "error": str(e),
                    "session_id": session_id
                }
            )
            raise HTTPException(
                status_code=500,
                detail=f"Failed to parse AI response: {str(e)}"
            ) from e
        except Exception as e:
            logger.error(
                "Error generating notes from template",
                extra={
                    "template_id": str(template_id),
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "session_id": session_id
                }
            )
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate notes from template: {str(e)}"
            ) from e

    def get_default_template(self, template_type: TemplateType) -> Dict[str, Any]:
        """
        Get default template structure for a given template type.

        Returns the built-in default template definition (not from database).
        Useful for providing template examples to users or initializing new templates.

        Args:
            template_type: Type of template (soap, dap, birp, progress, custom)

        Returns:
            Dict containing default template structure:
            {
                "name": str,
                "description": str,
                "template_type": str,
                "sections": [...]
            }

        Raises:
            ValueError: If template_type is not recognized or custom (custom has no default)
        """
        logger.info(
            "Getting default template",
            extra={"template_type": template_type.value}
        )

        if template_type == TemplateType.custom:
            raise ValueError(
                "No default template for 'custom' type. "
                "Custom templates must be defined by the user."
            )

        template_key = template_type.value

        if template_key not in DEFAULT_TEMPLATES:
            logger.warning(
                "Unknown template type requested",
                extra={"template_type": template_type.value}
            )
            raise ValueError(f"Unknown template type: {template_type.value}")

        default = DEFAULT_TEMPLATES[template_key].copy()

        logger.info(
            "Default template retrieved",
            extra={
                "template_type": template_type.value,
                "sections_count": len(default.get("sections", []))
            }
        )

        return default

    def validate_template(self, template_content: Dict[str, Any]) -> bool:
        """
        Validate template JSON structure.

        Ensures the template content has the required structure:
        - Must have 'sections' array
        - Each section must have: id, name, prompt
        - Section IDs must be unique
        - ai_mapping (if present) must be a list

        Args:
            template_content: Template structure to validate (JSON/dict)

        Returns:
            True if valid

        Raises:
            ValueError: If template structure is invalid (with specific error message)
        """
        logger.debug("Validating template content")

        # Check for sections array
        if "sections" not in template_content:
            raise ValueError("Template must have 'sections' array")

        sections = template_content["sections"]

        if not isinstance(sections, list):
            raise ValueError("'sections' must be an array")

        if len(sections) == 0:
            raise ValueError("Template must have at least one section")

        # Validate each section
        section_ids = []

        for i, section in enumerate(sections):
            if not isinstance(section, dict):
                raise ValueError(f"Section {i} must be an object")

            # Required fields
            required_fields = ["id", "name", "prompt"]
            for field in required_fields:
                if field not in section:
                    raise ValueError(f"Section {i} missing required field: '{field}'")

                if not isinstance(section[field], str) or not section[field].strip():
                    raise ValueError(f"Section {i} field '{field}' must be a non-empty string")

            # Check for duplicate section IDs
            section_id = section["id"]
            if section_id in section_ids:
                raise ValueError(f"Duplicate section ID: '{section_id}'")
            section_ids.append(section_id)

            # Validate ai_mapping if present
            if "ai_mapping" in section:
                if not isinstance(section["ai_mapping"], list):
                    raise ValueError(f"Section '{section_id}' ai_mapping must be an array")

        logger.debug(
            "Template validated successfully",
            extra={"sections_count": len(sections)}
        )

        return True

    # ============================================================================
    # Private Helper Methods
    # ============================================================================

    async def _get_template(self, template_id: UUID) -> NoteTemplate:
        """
        Fetch template from database by ID.

        Args:
            template_id: UUID of template to fetch

        Returns:
            NoteTemplate database model

        Raises:
            HTTPException: 404 if template not found
        """
        result = await self.db.execute(
            select(NoteTemplate).where(NoteTemplate.id == template_id)
        )
        template = result.scalar_one_or_none()

        if not template:
            logger.warning(
                "Template not found",
                extra={"template_id": str(template_id)}
            )
            raise HTTPException(
                status_code=404,
                detail=f"Template {template_id} not found"
            )

        return template

    def _build_section_content(
        self,
        extracted_notes: ExtractedNotes,
        ai_mapping: List[str],
        section_name: str
    ) -> str:
        """
        Build formatted content for a template section from extracted notes.

        Args:
            extracted_notes: AI-extracted notes data
            ai_mapping: List of ExtractedNotes field names to include in this section
            section_name: Name of the section (for logging)

        Returns:
            Formatted string content for the section
        """
        content_parts = []
        notes_dict = extracted_notes.model_dump()

        for field_name in ai_mapping:
            if field_name not in notes_dict:
                continue

            value = notes_dict[field_name]

            # Format based on field type
            if field_name == "key_topics" and value:
                content_parts.append("**Key Topics:**\n" + "\n".join(f"- {topic}" for topic in value))

            elif field_name == "topic_summary" and value:
                content_parts.append(f"**Summary:** {value}")

            elif field_name == "significant_quotes" and value:
                quotes_text = "\n".join(
                    f'- "{quote.get("quote", "")}" ({quote.get("context", "")})'
                    for quote in value
                )
                content_parts.append(f"**Significant Quotes:**\n{quotes_text}")

            elif field_name == "emotional_themes" and value:
                content_parts.append("**Emotional Themes:** " + ", ".join(value))

            elif field_name == "session_mood" and value:
                content_parts.append(f"**Session Mood:** {value}")

            elif field_name == "mood_trajectory" and value:
                content_parts.append(f"**Mood Trajectory:** {value}")

            elif field_name == "triggers" and value:
                triggers_text = "\n".join(
                    f'- {trigger.get("trigger", "")} ({trigger.get("severity", "")}) - {trigger.get("context", "")}'
                    for trigger in value
                )
                content_parts.append(f"**Triggers Identified:**\n{triggers_text}")

            elif field_name == "therapist_notes" and value:
                content_parts.append(f"**Clinical Notes:** {value}")

            elif field_name == "risk_flags" and value:
                risks_text = "\n".join(
                    f'- {risk.get("type", "")}: {risk.get("evidence", "")} (Severity: {risk.get("severity", "")})'
                    for risk in value
                )
                content_parts.append(f"**Risk Flags:**\n{risks_text}")

            elif field_name == "action_items" and value:
                items_text = "\n".join(
                    f'- {item.get("task", "")} ({item.get("category", "")})'
                    for item in value
                )
                content_parts.append(f"**Action Items:**\n{items_text}")

            elif field_name == "strategies" and value:
                strategies_text = "\n".join(
                    f'- {strategy.get("name", "")} ({strategy.get("category", "")}) - {strategy.get("status", "")}: {strategy.get("context", "")}'
                    for strategy in value
                )
                content_parts.append(f"**Strategies:**\n{strategies_text}")

            elif field_name == "follow_up_topics" and value:
                content_parts.append("**Follow-up Topics:**\n" + "\n".join(f"- {topic}" for topic in value))

            elif field_name == "unresolved_concerns" and value:
                content_parts.append("**Unresolved Concerns:**\n" + "\n".join(f"- {concern}" for concern in value))

        # Join all content parts
        section_content = "\n\n".join(content_parts) if content_parts else "No relevant data extracted for this section."

        return section_content

    def _build_custom_prompt(
        self,
        template: NoteTemplate,
        transcript: str
    ) -> str:
        """
        Build custom GPT-4o prompt based on template sections.

        Args:
            template: Template database model with structure
            transcript: Therapy session transcript

        Returns:
            Formatted prompt string for GPT-4o
        """
        structure = template.structure
        sections = structure.get("sections", [])

        # Build section instructions
        section_instructions = []
        for section in sections:
            section_id = section.get("id")
            section_name = section.get("name")
            section_prompt = section.get("prompt")

            section_instructions.append(
                f'**{section_name}** (id: "{section_id}"):\n{section_prompt}'
            )

        sections_text = "\n\n".join(section_instructions)

        # Build full prompt
        prompt = f"""You are a clinical psychology expert generating structured clinical notes from a therapy session transcript.

Generate notes following this template structure:

{sections_text}

Return your response as valid JSON in this exact format:
{{
  "sections": {{
    "section_id_1": {{
      "name": "Section Name",
      "content": "Generated content for this section..."
    }},
    "section_id_2": {{
      "name": "Section Name",
      "content": "Generated content for this section..."
    }},
    ...
  }}
}}

IMPORTANT:
- Only extract information that is actually present in the transcript
- Do not infer or assume information not explicitly stated
- Use markdown formatting (bold, bullets, etc.) to organize content
- Be thorough but concise
- Use exact quotes when appropriate

TRANSCRIPT:
{transcript}
"""

        return prompt


# ============================================================================
# Dependency Injection
# ============================================================================

def get_note_template_service(db: AsyncSession) -> NoteTemplateService:
    """
    FastAPI dependency to provide the note template service.

    Args:
        db: Async database session (injected by FastAPI)

    Returns:
        NoteTemplateService: New instance with database session

    Usage:
        In FastAPI routes:
        ```python
        from fastapi import Depends
        from sqlalchemy.ext.asyncio import AsyncSession
        from app.database import get_db

        @router.post("/sessions/{id}/regenerate-notes")
        async def regenerate_notes(
            id: UUID,
            template_id: UUID,
            db: AsyncSession = Depends(get_db),
            service: NoteTemplateService = Depends(get_note_template_service)
        ):
            # Use service...
        ```
    """
    return NoteTemplateService(db=db)
