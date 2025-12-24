"""
Topic Extraction Service

Uses AI to analyze therapy session transcripts and extract structured metadata including:
- 1-2 main topics discussed
- 2 action items/homework
- 1 therapeutic technique used
- 2-sentence summary

This service creates a "meta summary" that can be further processed to extract
individual components, optimizing AI usage and consistency.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from openai import AsyncOpenAI
import os
import json
import time
from app.services.technique_library import get_technique_library, TechniqueLibrary
from app.config.model_config import get_model_name, track_generation_cost, GenerationCost
from app.config import settings


@dataclass
class SessionMetadata:
    """Represents extracted metadata from a therapy session"""
    session_id: str
    topics: List[str]  # 1-2 main topics
    action_items: List[str]  # 2 action items
    technique: str  # 1 therapeutic technique
    summary: str  # 2-sentence summary
    raw_meta_summary: str  # Full AI response for reference
    confidence: float  # 0.0 to 1.0
    extracted_at: datetime
    cost_info: Optional[GenerationCost] = None  # Cost tracking for this generation


class TopicExtractor:
    """
    AI-powered topic and metadata extraction for therapy sessions.

    Uses GPT-4o-mini to analyze full conversation and extract:
    - Main topics discussed
    - Action items/homework assigned
    - Therapeutic techniques employed
    - Concise session summary

    The AI naturally concludes topics from context without hardcoded outputs.
    """

    def __init__(self, api_key: Optional[str] = None, override_model: Optional[str] = None):
        """
        Initialize the topic extractor with async OpenAI client and technique library.

        Args:
            api_key: OpenAI API key. If None, uses OPENAI_API_KEY env var.
            override_model: Optional model override for testing (default: uses gpt-5-mini from config)
        """
        self.api_key = api_key or settings.openai_api_key
        if not self.api_key:
            raise ValueError("OpenAI API key required for topic extraction")

        self.client = AsyncOpenAI(api_key=self.api_key)
        self.model = get_model_name("topic_extraction", override_model=override_model)

        # Load technique library for validation
        self.technique_library: TechniqueLibrary = get_technique_library()

    async def extract_metadata(
        self,
        session_id: str,
        segments: List[Dict[str, Any]],
        speaker_roles: Optional[Dict[str, str]] = None
    ) -> SessionMetadata:
        """
        Extract topics, action items, technique, and summary from therapy session.

        Args:
            session_id: Unique identifier for the session
            segments: List of transcript segments with 'speaker', 'text', 'start', 'end'
            speaker_roles: Optional mapping of speaker IDs to roles (Therapist/Client)
                          If None, will use SPEAKER_00 as Therapist, SPEAKER_01 as Client

        Returns:
            SessionMetadata with extracted topics, action items, technique, and summary
        """
        # Format conversation with role labels
        conversation = self._format_conversation(segments, speaker_roles)

        if not conversation.strip():
            raise ValueError("No conversation content found in segments")

        # Create analysis prompt
        prompt = self._create_extraction_prompt(conversation)

        # Call OpenAI API
        # NOTE: GPT-5 series does NOT support custom temperature - uses internal calibration
        try:
            start_time = time.time()
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"}
            )

            # Track cost and timing
            cost_info = track_generation_cost(
                response=response,
                task="topic_extraction",
                model=self.model,
                start_time=start_time,
                session_id=session_id
            )

            result = json.loads(response.choices[0].message.content)

            # Validate and extract fields
            topics = result.get("topics", [])[:2]  # Max 2 topics
            action_items = result.get("action_items", [])[:2]  # Max 2 action items
            raw_technique = result.get("technique", "Not specified")
            raw_summary = result.get("summary", "")
            summary = self._truncate_summary(raw_summary, max_length=150)
            confidence = result.get("confidence", 0.8)

            # Log truncation for monitoring
            if len(raw_summary) > 150:
                print(f"⚠️  Summary truncated for {session_id}: {len(raw_summary)} → {len(summary)} chars")

            # ===== NEW: Validate and standardize technique =====
            standardized_technique, technique_confidence, match_type = \
                self.technique_library.validate_and_standardize(raw_technique)

            # Log validation results for debugging
            print(f"Technique validation for {session_id}:")
            print(f"  Raw: '{raw_technique}'")
            print(f"  Standardized: '{standardized_technique}'")
            print(f"  Confidence: {technique_confidence:.2f}")
            print(f"  Match type: {match_type}")

            # Use standardized technique or fallback
            final_technique = standardized_technique or "Not specified"
            # ===================================================

            # Ensure we have at least 1 topic
            if not topics:
                topics = ["General therapy session"]

            # Ensure we have at least 1 action item
            if not action_items:
                action_items = ["Continue practicing discussed techniques"]

            return SessionMetadata(
                session_id=session_id,
                topics=topics,
                action_items=action_items,
                technique=final_technique,  # Now standardized!
                summary=summary,
                raw_meta_summary=response.choices[0].message.content,
                confidence=confidence,
                extracted_at=datetime.utcnow(),
                cost_info=cost_info
            )

        except Exception as e:
            raise Exception(f"Topic extraction failed: {str(e)}")

    def _get_system_prompt(self) -> str:
        """System prompt defining the AI's role and instructions with technique library."""
        # Build technique reference list organized by modality
        techniques_by_modality = {}
        for modality in ["CBT", "DBT", "ACT", "Mindfulness-Based", "Motivational Interviewing", "EMDR", "Psychodynamic", "Solution-Focused", "Other"]:
            techniques = self.technique_library.get_techniques_by_modality(modality)
            if techniques:
                techniques_by_modality[modality] = [t.name for t in techniques]

        # Build technique list for prompt
        technique_list = []
        for modality, techniques in techniques_by_modality.items():
            technique_list.append(f"\n**{modality}:**")
            for tech in techniques:
                technique_list.append(f"  - {tech}")

        technique_reference = "\n".join(technique_list)

        return f"""You are an expert clinical psychologist analyzing therapy session transcripts.

Your task is to extract key metadata from the session to help both the therapist and client track progress and remember important details.

**What to extract:**

1. **Topics (1-2)**: The main themes or issues discussed in the session. Be specific and clinical.
   - Good: "Relationship anxiety and fear of abandonment", "ADHD medication adjustment"
   - Bad: "Mental health", "Feelings" (too vague)

2. **Action Items (2)**: Concrete homework, tasks, or commitments made during the session.
   - Good: "Practice TIPP skills when feeling overwhelmed", "Schedule psychiatrist appointment for medication evaluation"
   - Bad: "Feel better", "Think about things" (not actionable)

3. **Technique (1)**: The primary therapeutic technique or intervention used. **CRITICAL: You must extract a technique that matches the reference library below.**

   **VALID CLINICAL TECHNIQUES (choose from this list):**
   {technique_reference}

   **Format:** Return ONLY the technique name exactly as shown in the list above (e.g., "Cognitive Restructuring", "TIPP Skills", "Cognitive Defusion")

   **Rules:**
   - DO NOT make up technique names
   - DO NOT return non-clinical interventions like general "psychoeducation", "crisis intervention", or "supportive counseling"
   - If multiple techniques used, pick the most prominent one
   - If unsure or no specific technique used, return "Not specified"

4. **Summary (maximum 150 characters)**: Ultra-brief clinical summary capturing the session's essence.
   - CRITICAL: Maximum 150 characters total (including spaces and punctuation)
   - Write in direct, active voice without meta-commentary
   - Avoid phrases like "The session focused on", "The session addressed", "We discussed"
   - Start immediately with the content (e.g., "Patient experiencing anxiety..." not "The session focused on anxiety...")
   - Be extremely concise - every word must count
   - Examples of good summaries:
     * "Patient reported improved sleep. Practiced progressive muscle relaxation." (76 chars)
     * "Discussed grief triggers. Assigned emotion regulation worksheets." (67 chars)
     * "Severe anxiety about job interview. Taught box breathing technique." (69 chars)

**Guidelines:**
- Base conclusions on the actual conversation, not assumptions
- Use clinical language when appropriate
- Be specific and actionable
- Topics should reflect what was actually discussed, not what should have been
- Action items must be concrete tasks mentioned in the session

**Output JSON format:**
{{
  "topics": ["topic 1", "topic 2"],
  "action_items": ["action item 1", "action item 2"],
  "technique": "Exact technique name from list above",
  "summary": "Ultra-brief summary under 150 characters.",
  "confidence": 0.85
}}

Confidence score (0.0-1.0) reflects how clearly these elements were present in the session.
High confidence (0.8+): Topics, action items, and techniques are explicitly discussed
Medium confidence (0.5-0.7): Elements are implied or mentioned briefly
Low confidence (<0.5): Had to infer or make educated guesses"""

    def _create_extraction_prompt(self, conversation: str) -> str:
        """Create the analysis prompt from formatted conversation."""
        return f"""Analyze this therapy session transcript and extract the key metadata.

**Session Transcript:**

{conversation}

**Instructions:**
1. Read the entire conversation carefully
2. Identify 1-2 main topics discussed (be specific)
3. Extract 2 concrete action items or homework assignments
4. Identify the primary therapeutic technique used
5. Write an ultra-brief clinical summary (maximum 150 characters)
6. Rate your confidence in the extraction

Return your analysis as JSON following the specified format."""

    def _format_conversation(
        self,
        segments: List[Dict[str, Any]],
        speaker_roles: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Format transcript segments into readable conversation with role labels.

        Args:
            segments: Transcript segments
            speaker_roles: Optional mapping of speaker IDs to roles

        Returns:
            Formatted conversation string
        """
        # Default role mapping if not provided
        if speaker_roles is None:
            speaker_roles = {
                "SPEAKER_00": "Therapist",
                "SPEAKER_01": "Client"
            }

        formatted = []
        for segment in segments:
            speaker_id = segment.get("speaker") or segment.get("speaker_id", "UNKNOWN")
            text = segment.get("text", "").strip()
            start = segment.get("start", 0)

            if not text:
                continue

            # Get role label
            role = speaker_roles.get(speaker_id, speaker_id)

            # Format timestamp as MM:SS
            minutes = int(start // 60)
            seconds = int(start % 60)
            timestamp = f"{minutes:02d}:{seconds:02d}"

            formatted.append(f"[{timestamp}] {role}: {text}")

        return "\n".join(formatted)

    def _truncate_summary(self, summary: str, max_length: int = 150) -> str:
        """
        Truncate summary to maximum length with intelligent word boundary handling.

        Args:
            summary: Raw summary from AI (may exceed max_length)
            max_length: Maximum allowed characters (default: 150)

        Returns:
            Truncated summary ≤ max_length characters

        Examples:
            >>> _truncate_summary("Patient experiencing severe anxiety and discussed coping strategies for upcoming work presentation next week.", 150)
            "Patient experiencing severe anxiety and discussed coping strategies for upcoming work presentation next week."  # 113 chars - unchanged

            >>> _truncate_summary("Patient experiencing severe anxiety and discussed coping strategies. Therapist recommended deep breathing exercises and scheduled follow-up.", 150)
            "Patient experiencing severe anxiety and discussed coping strategies. Therapist recommended deep breathing exercises and scheduled..."  # 147 chars
        """
        # Already within limit - return as-is
        if len(summary) <= max_length:
            return summary

        # Truncate at max_length - 3 (reserve space for "...")
        truncated = summary[:max_length - 3]

        # Find last complete word (avoid cutting mid-word)
        last_space = truncated.rfind(' ')

        if last_space > 0:
            # Cut at word boundary
            truncated = truncated[:last_space]

        # Add ellipsis
        return truncated + "..."


# Convenience function for single-session extraction
def extract_session_metadata(
    session_id: str,
    segments: List[Dict[str, Any]],
    speaker_roles: Optional[Dict[str, str]] = None,
    api_key: Optional[str] = None
) -> SessionMetadata:
    """
    Convenience function to extract metadata for a single session.

    Args:
        session_id: Unique session identifier
        segments: Transcript segments
        speaker_roles: Optional speaker role mapping
        api_key: Optional OpenAI API key

    Returns:
        SessionMetadata object
    """
    extractor = TopicExtractor(api_key=api_key)
    return extractor.extract_metadata(session_id, segments, speaker_roles)
