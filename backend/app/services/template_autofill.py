"""
Template auto-fill service for mapping AI-extracted notes to template formats.

This service intelligently maps ExtractedNotes data to various clinical note
template formats (SOAP, DAP, BIRP, Progress Notes), calculates confidence
scores, and identifies missing fields requiring manual review.
"""
import logging
from typing import Dict, List, Any, Optional
from app.models.schemas import (
    ExtractedNotes,
    TemplateType,
    Strategy,
    Trigger,
    ActionItem,
    RiskFlag,
    SignificantQuote
)

logger = logging.getLogger(__name__)


class TemplateAutoFillService:
    """
    Service for auto-filling clinical note templates from AI-extracted session data.

    Maps ExtractedNotes to different template formats with confidence scoring
    and missing field detection to help therapists efficiently document sessions
    while ensuring data quality.
    """

    def __init__(self):
        """Initialize the template auto-fill service."""
        # Define standard template structures and required fields
        self.template_required_fields = {
            TemplateType.soap: {
                'subjective': ['chief_complaint', 'mood'],
                'objective': ['presentation'],
                'assessment': ['clinical_impression'],
                'plan': ['interventions']
            },
            TemplateType.dap: {
                'data': ['observations'],
                'assessment': ['clinical_impression'],
                'plan': ['interventions']
            },
            TemplateType.birp: {
                'behavior': ['presentation'],
                'intervention': ['techniques'],
                'response': ['patient_response'],
                'plan': ['next_steps']
            },
            TemplateType.progress: {
                'session_summary': ['overview'],
                'clinical_presentation': ['mood_affect'],
                'progress': ['changes'],
                'interventions': ['techniques'],
                'plan': ['next_steps']
            }
        }

    async def fill_template(
        self,
        notes: ExtractedNotes,
        template_type: TemplateType
    ) -> Dict[str, Any]:
        """
        Main entry point for auto-filling a template from extracted notes.

        Routes to the appropriate mapping function based on template type,
        calculates confidence scores, and identifies missing fields.

        Args:
            notes: AI-extracted session notes containing all clinical data
            template_type: Type of template to fill (soap, dap, birp, progress)

        Returns:
            Dict containing:
                - sections: Filled template sections with mapped data
                - confidence_scores: Per-section confidence (0.0-1.0)
                - missing_fields: Sections with weak/missing data
                - metadata: Processing information

        Raises:
            ValueError: If template_type is not supported

        Example:
            >>> service = TemplateAutoFillService()
            >>> result = await service.fill_template(notes, TemplateType.soap)
            >>> print(result['sections']['subjective']['chief_complaint'])
            >>> print(result['confidence_scores']['subjective'])
        """
        logger.info(f"Starting auto-fill for template type: {template_type.value}")

        # Map to appropriate template format
        mapping_functions = {
            TemplateType.soap: self._map_to_soap,
            TemplateType.dap: self._map_to_dap,
            TemplateType.birp: self._map_to_birp,
            TemplateType.progress: self._map_to_progress_note
        }

        if template_type not in mapping_functions:
            raise ValueError(
                f"Unsupported template type: {template_type}. "
                f"Supported types: {list(mapping_functions.keys())}"
            )

        # Execute mapping
        mapping_func = mapping_functions[template_type]
        sections = mapping_func(notes)

        # Calculate confidence scores per section
        confidence_scores = {}
        for section_name, section_data in sections.items():
            # Get all field values for this section
            field_values = list(section_data.values()) if isinstance(section_data, dict) else [section_data]
            confidence_scores[section_name] = self._calculate_section_confidence(field_values)

        # Identify missing or weak fields
        missing_fields = self.identify_missing_fields(notes, template_type, sections)

        # Build metadata
        metadata = {
            'template_type': template_type.value,
            'extraction_source': 'ai_extraction',
            'mapped_fields_count': sum(len(s) if isinstance(s, dict) else 1 for s in sections.values()),
            'overall_confidence': round(
                sum(confidence_scores.values()) / len(confidence_scores), 2
            ) if confidence_scores else 0.0
        }

        logger.info(
            f"Auto-fill completed for {template_type.value}",
            extra={
                'sections_count': len(sections),
                'overall_confidence': metadata['overall_confidence'],
                'missing_fields_count': sum(len(fields) for fields in missing_fields.values())
            }
        )

        return {
            'sections': sections,
            'confidence_scores': confidence_scores,
            'missing_fields': missing_fields,
            'metadata': metadata
        }

    def _map_to_soap(self, notes: ExtractedNotes) -> Dict[str, Dict[str, str]]:
        """
        Map extracted notes to SOAP (Subjective, Objective, Assessment, Plan) format.

        SOAP Mapping Strategy:
        - Subjective: Patient's self-reported experiences and concerns
        - Objective: Observable behaviors and clinical observations
        - Assessment: Clinical interpretation and risk evaluation
        - Plan: Treatment strategies and next steps

        Args:
            notes: AI-extracted session notes

        Returns:
            Dict with four sections: subjective, objective, assessment, plan
        """
        # Subjective: What the patient reports
        subjective = {
            'chief_complaint': notes.topic_summary,
            'mood': notes.session_mood.value,
            'presenting_issues': self._format_list(notes.key_topics),
            'patient_concerns': self._format_list(notes.unresolved_concerns),
            'significant_statements': self._format_quotes(notes.significant_quotes)
        }

        # Objective: What the therapist observes
        objective = {
            'presentation': f"Patient presented with {notes.session_mood.value} mood. "
                          f"Emotional themes observed: {', '.join(notes.emotional_themes)}.",
            'mood_affect': notes.session_mood.value,
            'emotional_presentation': self._format_list(notes.emotional_themes),
            'mood_trajectory': notes.mood_trajectory,
            'triggers_identified': self._format_triggers(notes.triggers)
        }

        # Assessment: Clinical interpretation
        reviewed_strategies = [s for s in notes.strategies if s.status.value == 'reviewed']
        assessment = {
            'clinical_impression': notes.therapist_notes,
            'strategies_reviewed': self._format_strategies(reviewed_strategies),
            'unresolved_concerns': self._format_list(notes.unresolved_concerns),
            'risk_assessment': self._format_risk_flags(notes.risk_flags)
        }

        # Plan: Next steps and interventions
        assigned_strategies = [s for s in notes.strategies if s.status.value == 'assigned']
        plan = {
            'interventions': self._format_strategies(notes.strategies),
            'homework': self._format_action_items(notes.action_items),
            'strategies_assigned': self._format_strategies(assigned_strategies),
            'follow_up_topics': self._format_list(notes.follow_up_topics),
            'next_session_focus': self._format_list(notes.follow_up_topics[:3]) if notes.follow_up_topics else "Continue current treatment plan"
        }

        return {
            'subjective': subjective,
            'objective': objective,
            'assessment': assessment,
            'plan': plan
        }

    def _map_to_dap(self, notes: ExtractedNotes) -> Dict[str, Dict[str, str]]:
        """
        Map extracted notes to DAP (Data, Assessment, Plan) format.

        DAP Mapping Strategy:
        - Data: Combines subjective reports and objective observations
        - Assessment: Clinical interpretation with interventions used
        - Plan: Homework and next session focus

        Args:
            notes: AI-extracted session notes

        Returns:
            Dict with three sections: data, assessment, plan
        """
        # Data: Subjective + Objective combined
        data = {
            'observations': f"{notes.topic_summary} "
                          f"Patient presented with {notes.session_mood.value} mood. "
                          f"Mood trajectory: {notes.mood_trajectory}.",
            'topics_discussed': self._format_list(notes.key_topics),
            'emotional_presentation': self._format_list(notes.emotional_themes),
            'triggers': self._format_triggers(notes.triggers),
            'patient_statements': self._format_quotes(notes.significant_quotes)
        }

        # Assessment: Clinical interpretation + interventions
        assessment = {
            'clinical_impression': notes.therapist_notes,
            'interventions_used': self._format_strategies(notes.strategies),
            'patient_engagement': self._get_engagement_summary(notes),
            'risk_assessment': self._format_risk_flags(notes.risk_flags),
            'progress_notes': f"Mood trajectory: {notes.mood_trajectory}. "
                            f"Session mood: {notes.session_mood.value}."
        }

        # Plan: Forward-looking actions
        plan = {
            'homework': self._format_action_items(notes.action_items),
            'next_session_focus': self._format_list(notes.follow_up_topics[:3]) if notes.follow_up_topics else "Continue current treatment approach",
            'strategies_to_practice': self._format_strategies(
                [s for s in notes.strategies if s.status.value in ['assigned', 'practiced']]
            ),
            'follow_up_items': self._format_list(notes.unresolved_concerns)
        }

        return {
            'data': data,
            'assessment': assessment,
            'plan': plan
        }

    def _map_to_birp(self, notes: ExtractedNotes) -> Dict[str, Dict[str, str]]:
        """
        Map extracted notes to BIRP (Behavior, Intervention, Response, Plan) format.

        BIRP Mapping Strategy:
        - Behavior: Emotional presentation and triggers
        - Intervention: Strategies and techniques applied
        - Response: Patient's engagement and mood changes
        - Plan: Action items and follow-up

        Args:
            notes: AI-extracted session notes

        Returns:
            Dict with four sections: behavior, intervention, response, plan
        """
        # Behavior: What was observed
        behavior = {
            'presentation': f"Patient presented with {notes.session_mood.value} mood. "
                          f"Discussed: {notes.topic_summary}",
            'emotional_state': self._format_list(notes.emotional_themes),
            'triggers_exhibited': self._format_triggers(notes.triggers),
            'reported_concerns': self._format_list(notes.key_topics)
        }

        # Intervention: What the therapist did
        intervention = {
            'techniques': self._format_strategies(notes.strategies),
            'therapeutic_approach': self._get_therapeutic_approach(notes.strategies),
            'interventions_applied': self._format_strategies(
                [s for s in notes.strategies if s.status.value in ['practiced', 'introduced']]
            )
        }

        # Response: How patient responded
        response = {
            'patient_response': self._get_engagement_summary(notes),
            'mood_trajectory': notes.mood_trajectory,
            'engagement_level': self._assess_engagement_level(notes),
            'insights_gained': self._format_quotes(notes.significant_quotes)
        }

        # Plan: Next steps
        plan = {
            'next_steps': self._format_action_items(notes.action_items),
            'homework': self._format_strategies(
                [s for s in notes.strategies if s.status.value == 'assigned']
            ),
            'follow_up_topics': self._format_list(notes.follow_up_topics),
            'risk_management': self._format_risk_flags(notes.risk_flags) if notes.risk_flags else "No current risk concerns identified"
        }

        return {
            'behavior': behavior,
            'intervention': intervention,
            'response': response,
            'plan': plan
        }

    def _map_to_progress_note(self, notes: ExtractedNotes) -> Dict[str, Dict[str, str]]:
        """
        Map extracted notes to Progress Note format (general narrative style).

        Progress Note Mapping Strategy:
        - Session Summary: Overall narrative of session
        - Clinical Presentation: Mood, affect, and emotional state
        - Progress: Changes and trajectory
        - Interventions: Techniques and strategies used
        - Risk Assessment: Safety concerns
        - Plan: Next steps and homework

        Args:
            notes: AI-extracted session notes

        Returns:
            Dict with six sections covering comprehensive session documentation
        """
        # Session Summary: Narrative overview
        session_summary = {
            'overview': notes.topic_summary,
            'session_date': "See session metadata",
            'duration': "See session metadata",
            'topics_covered': self._format_list(notes.key_topics)
        }

        # Clinical Presentation
        clinical_presentation = {
            'mood_affect': f"{notes.session_mood.value} mood with {notes.mood_trajectory} trajectory",
            'emotional_themes': self._format_list(notes.emotional_themes),
            'presentation_summary': f"Patient presented with {notes.session_mood.value} mood. "
                                  f"Primary emotional themes included {', '.join(notes.emotional_themes[:3])}.",
            'behavioral_observations': self._format_triggers(notes.triggers)
        }

        # Progress: Changes and development
        progress = {
            'changes': f"Mood trajectory: {notes.mood_trajectory}",
            'treatment_response': self._get_engagement_summary(notes),
            'strategies_effectiveness': self._format_strategies(
                [s for s in notes.strategies if s.status.value == 'reviewed']
            ),
            'patient_insights': self._format_quotes(notes.significant_quotes)
        }

        # Interventions: What was done
        interventions = {
            'techniques': self._format_strategies(notes.strategies),
            'therapeutic_approach': self._get_therapeutic_approach(notes.strategies),
            'interventions_used': self._format_strategies(
                [s for s in notes.strategies if s.status.value in ['practiced', 'introduced']]
            )
        }

        # Risk Assessment
        risk_assessment = {
            'risk_flags': self._format_risk_flags(notes.risk_flags) if notes.risk_flags else "No current risk concerns identified",
            'safety_plan': "See risk flags for details" if notes.risk_flags else "Not applicable"
        }

        # Plan: Forward looking
        plan = {
            'next_steps': self._format_action_items(notes.action_items),
            'homework': self._format_strategies(
                [s for s in notes.strategies if s.status.value == 'assigned']
            ),
            'follow_up_topics': self._format_list(notes.follow_up_topics),
            'unresolved_concerns': self._format_list(notes.unresolved_concerns),
            'next_session_plan': self._format_list(notes.follow_up_topics[:3]) if notes.follow_up_topics else "Continue treatment as planned"
        }

        return {
            'session_summary': session_summary,
            'clinical_presentation': clinical_presentation,
            'progress': progress,
            'interventions': interventions,
            'risk_assessment': risk_assessment,
            'plan': plan
        }

    def calculate_confidence(
        self,
        notes: ExtractedNotes,
        field_names: List[str]
    ) -> float:
        """
        Calculate confidence score for a set of fields.

        Confidence Scoring Algorithm:
        - Empty field: 0.0
        - Short text (< 20 chars): 0.5
        - Moderate text (< 100 chars): 0.8
        - Comprehensive text (> 100 chars): 1.0
        - Empty list: 0.3 (field exists but no data)
        - Short list (< 3 items): 0.7
        - Good list (3+ items): 1.0

        Args:
            notes: AI-extracted session notes
            field_names: List of field names to check (e.g., ['key_topics', 'session_mood'])

        Returns:
            float: Average confidence score between 0.0 and 1.0

        Example:
            >>> confidence = service.calculate_confidence(
            ...     notes,
            ...     ['key_topics', 'topic_summary', 'strategies']
            ... )
            >>> print(f"Confidence: {confidence:.2f}")
        """
        if not field_names:
            return 0.0

        scores = []

        for field_name in field_names:
            # Get field value from notes
            field_value = getattr(notes, field_name, None)

            if field_value is None:
                scores.append(0.0)
            elif isinstance(field_value, str):
                # String fields: score by length and content
                if not field_value or len(field_value.strip()) == 0:
                    scores.append(0.0)
                elif len(field_value) < 20:
                    scores.append(0.5)
                elif len(field_value) < 100:
                    scores.append(0.8)
                else:
                    scores.append(1.0)
            elif isinstance(field_value, list):
                # List fields: score by item count
                if len(field_value) == 0:
                    scores.append(0.3)  # Field exists but empty
                elif len(field_value) < 3:
                    scores.append(0.7)
                else:
                    scores.append(1.0)
            elif isinstance(field_value, (int, float, bool)):
                # Numeric/boolean fields: presence = good
                scores.append(1.0)
            else:
                # Enum or other types: presence = good
                scores.append(1.0)

        return round(sum(scores) / len(scores), 2) if scores else 0.0

    def _calculate_section_confidence(self, field_values: List[Any]) -> float:
        """
        Calculate confidence for a section based on its field values.

        Args:
            field_values: List of field values in the section

        Returns:
            float: Confidence score between 0.0 and 1.0
        """
        if not field_values:
            return 0.0

        scores = []

        for value in field_values:
            if value is None or (isinstance(value, str) and not value.strip()):
                scores.append(0.0)
            elif isinstance(value, str):
                if len(value) < 20:
                    scores.append(0.5)
                elif len(value) < 100:
                    scores.append(0.8)
                else:
                    scores.append(1.0)
            else:
                scores.append(1.0)

        return round(sum(scores) / len(scores), 2) if scores else 0.0

    def identify_missing_fields(
        self,
        notes: ExtractedNotes,
        template_type: TemplateType,
        filled_sections: Optional[Dict[str, Any]] = None
    ) -> Dict[str, List[str]]:
        """
        Identify fields with missing or low-confidence data that need manual review.

        Checks each required field for the template type and flags those that
        are empty, very short, or have low confidence based on the data source.

        Args:
            notes: AI-extracted session notes
            template_type: Type of template being filled
            filled_sections: Optional pre-filled sections to analyze

        Returns:
            Dict mapping section names to lists of missing field names

        Example:
            >>> missing = service.identify_missing_fields(notes, TemplateType.soap)
            >>> if missing:
            ...     print(f"Sections needing review: {list(missing.keys())}")
        """
        missing = {}

        # Get required fields for this template type
        template_requirements = self.template_required_fields.get(template_type, {})

        if filled_sections:
            # Analyze provided sections
            for section_name, required_fields in template_requirements.items():
                section_data = filled_sections.get(section_name, {})
                section_missing = []

                for field_name in required_fields:
                    field_value = section_data.get(field_name, '')

                    # Check if field is missing or weak
                    if not field_value or (isinstance(field_value, str) and len(field_value.strip()) < 10):
                        section_missing.append(field_name)

                if section_missing:
                    missing[section_name] = section_missing
        else:
            # Analyze based on source ExtractedNotes
            # This is a fallback when sections aren't provided
            source_field_mapping = {
                'chief_complaint': 'topic_summary',
                'mood': 'session_mood',
                'presentation': 'emotional_themes',
                'clinical_impression': 'therapist_notes',
                'interventions': 'strategies',
                'observations': 'key_topics',
                'techniques': 'strategies',
                'next_steps': 'action_items',
                'overview': 'topic_summary'
            }

            for section_name, required_fields in template_requirements.items():
                section_missing = []

                for field_name in required_fields:
                    # Map to source field
                    source_field = source_field_mapping.get(field_name)
                    if source_field:
                        source_value = getattr(notes, source_field, None)

                        # Check if weak
                        if source_value is None:
                            section_missing.append(field_name)
                        elif isinstance(source_value, str) and len(source_value.strip()) < 10:
                            section_missing.append(field_name)
                        elif isinstance(source_value, list) and len(source_value) == 0:
                            section_missing.append(field_name)

                if section_missing:
                    missing[section_name] = section_missing

        return missing

    # ========================================================================
    # Helper Methods for Formatting
    # ========================================================================

    def _format_list(self, items: List[str]) -> str:
        """Format a list of strings as a bulleted list or sentence."""
        if not items:
            return "None documented"
        if len(items) == 1:
            return items[0]
        return "• " + "\n• ".join(items)

    def _format_strategies(self, strategies: List[Strategy]) -> str:
        """Format strategies with their context and status."""
        if not strategies:
            return "None documented"

        formatted = []
        for strategy in strategies:
            formatted.append(
                f"• {strategy.name} ({strategy.category}, {strategy.status.value}): {strategy.context}"
            )
        return "\n".join(formatted)

    def _format_triggers(self, triggers: List[Trigger]) -> str:
        """Format triggers with severity and context."""
        if not triggers:
            return "No specific triggers identified"

        formatted = []
        for trigger in triggers:
            severity_str = f" [{trigger.severity}]" if trigger.severity else ""
            formatted.append(f"• {trigger.trigger}{severity_str}: {trigger.context}")
        return "\n".join(formatted)

    def _format_action_items(self, items: List[ActionItem]) -> str:
        """Format action items with category and details."""
        if not items:
            return "No homework assigned"

        formatted = []
        for item in items:
            details_str = f" - {item.details}" if item.details else ""
            formatted.append(f"• [{item.category}] {item.task}{details_str}")
        return "\n".join(formatted)

    def _format_quotes(self, quotes: List[SignificantQuote]) -> str:
        """Format significant quotes with context."""
        if not quotes:
            return "No significant quotes documented"

        formatted = []
        for quote in quotes[:5]:  # Limit to top 5
            formatted.append(f'• "{quote.quote}" - {quote.context}')
        return "\n".join(formatted)

    def _format_risk_flags(self, flags: List[RiskFlag]) -> str:
        """Format risk flags with severity and evidence."""
        if not flags:
            return "No risk flags identified"

        formatted = []
        for flag in flags:
            formatted.append(
                f"⚠️ {flag.type.upper()} [{flag.severity}]: {flag.evidence}"
            )
        return "\n".join(formatted)

    def _get_therapeutic_approach(self, strategies: List[Strategy]) -> str:
        """Summarize therapeutic approaches used based on strategy categories."""
        if not strategies:
            return "Supportive therapy"

        categories = [s.category for s in strategies]
        category_counts = {}
        for cat in categories:
            category_counts[cat] = category_counts.get(cat, 0) + 1

        # Get top 3 categories
        top_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        approach_list = [cat for cat, _ in top_categories]

        return ", ".join(approach_list) if approach_list else "Supportive therapy"

    def _get_engagement_summary(self, notes: ExtractedNotes) -> str:
        """Generate patient engagement summary based on mood trajectory and quotes."""
        engagement_indicators = []

        # Check mood trajectory
        if notes.mood_trajectory == "improving":
            engagement_indicators.append("Patient showed improvement during session")
        elif notes.mood_trajectory == "stable":
            engagement_indicators.append("Patient maintained stable mood throughout")
        elif notes.mood_trajectory == "declining":
            engagement_indicators.append("Patient experienced declining mood during session")
        else:
            engagement_indicators.append("Patient's mood fluctuated during session")

        # Check for insights (quotes indicate engagement)
        if len(notes.significant_quotes) > 0:
            engagement_indicators.append(f"demonstrated insight through {len(notes.significant_quotes)} significant reflections")

        # Check for action items (indicates willingness)
        if len(notes.action_items) > 0:
            engagement_indicators.append(f"receptive to {len(notes.action_items)} homework assignments")

        return "; ".join(engagement_indicators) if engagement_indicators else "Patient engaged in session"

    def _assess_engagement_level(self, notes: ExtractedNotes) -> str:
        """Assess overall engagement level based on multiple factors."""
        score = 0

        # Positive indicators
        if notes.mood_trajectory == "improving":
            score += 2
        if len(notes.significant_quotes) >= 2:
            score += 2
        if len(notes.action_items) >= 1:
            score += 1
        if len(notes.strategies) >= 2:
            score += 1

        # Negative indicators
        if notes.mood_trajectory == "declining":
            score -= 1
        if len(notes.unresolved_concerns) > 3:
            score -= 1

        # Map score to engagement level
        if score >= 4:
            return "High engagement - patient actively participated and demonstrated insight"
        elif score >= 2:
            return "Good engagement - patient participated appropriately in session"
        elif score >= 0:
            return "Moderate engagement - patient present but reserved"
        else:
            return "Limited engagement - patient struggled to engage fully"


def get_autofill_service() -> TemplateAutoFillService:
    """
    FastAPI dependency to provide the template auto-fill service.

    Creates a new TemplateAutoFillService instance for each request.
    This service is stateless and lightweight, so creating new instances is efficient.

    Returns:
        TemplateAutoFillService: New instance ready for template mapping

    Usage:
        In FastAPI routes: service = Depends(get_autofill_service)
    """
    return TemplateAutoFillService()
