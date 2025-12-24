"""
AI-Powered Speaker Labeling Service

Analyzes therapy session transcripts to:
1. Detect which speaker is therapist vs patient (SPEAKER_00 or SPEAKER_01)
2. Merge consecutive same-speaker segments
3. Format output with human-readable labels and MM:SS timestamps
4. Fetch therapist name from database for labeling
"""

from typing import List, Dict, Optional, Any
import openai
import json
import logging
import time
from app.config.model_config import get_model_name, track_generation_cost, GenerationCost

logger = logging.getLogger(__name__)

# ============================================
# Pydantic Models
# ============================================

from pydantic import BaseModel, Field

class SpeakerRoleDetection(BaseModel):
    """AI's determination of speaker roles"""
    therapist_speaker_id: str = Field(description="Which speaker ID is the therapist (SPEAKER_00 or SPEAKER_01)")
    patient_speaker_id: str = Field(description="Which speaker ID is the patient (SPEAKER_00 or SPEAKER_01)")
    confidence: float = Field(description="Confidence in role assignment (0.0-1.0)")
    reasoning: str = Field(description="Why the AI assigned these roles")

class LabeledSegment(BaseModel):
    """Labeled and formatted transcript segment"""
    speaker: str = Field(description="Speaker label (therapist name or 'You' for patient)")
    text: str = Field(description="Merged dialogue text")
    timestamp: str = Field(description="Start timestamp in MM:SS format")

class SpeakerLabelingResult(BaseModel):
    """Complete result from speaker labeling"""
    labeled_transcript: List[LabeledSegment]
    detection: SpeakerRoleDetection
    therapist_name: str
    patient_label: str = "You"
    cost_info: Optional[dict] = None  # Cost tracking (dict for Pydantic compatibility)

# ============================================
# Speaker Labeling Service
# ============================================

class SpeakerLabeler:
    """AI-powered speaker role detection and transcript labeling"""

    def __init__(self, openai_api_key: str, override_model: Optional[str] = None):
        self.client = openai.OpenAI(api_key=openai_api_key)
        self.model = get_model_name("speaker_labeling", override_model=override_model)

    def label_transcript(
        self,
        raw_segments: List[Dict[str, Any]],
        therapist_label: str = "Therapist",
        patient_label: str = "You"
    ) -> SpeakerLabelingResult:
        """
        Label transcript with speaker labels and format for patient-facing view.

        Args:
            raw_segments: Raw transcript with SPEAKER_00/SPEAKER_01 labels
            therapist_label: Label for therapist (default: "Therapist")
            patient_label: Label for patient (default: "You")

        Returns:
            SpeakerLabelingResult with labeled, merged, formatted transcript
        """
        try:
            # Step 1: Detect speaker roles using AI
            detection, cost_info = self._detect_speaker_roles(raw_segments)

            # Step 2: Merge consecutive same-speaker segments
            merged_segments = self._merge_consecutive_segments(raw_segments)

            # Step 3: Apply labels and format timestamps
            labeled_segments = self._apply_labels_and_format(
                merged_segments,
                detection,
                therapist_label,
                patient_label
            )

            return SpeakerLabelingResult(
                labeled_transcript=labeled_segments,
                detection=detection,
                therapist_name=therapist_label,
                patient_label=patient_label,
                cost_info=cost_info.to_dict() if cost_info else None
            )

        except Exception as e:
            logger.error(f"Speaker labeling failed: {e}")
            raise

    def _detect_speaker_roles(self, segments: List[Dict[str, Any]]) -> tuple[SpeakerRoleDetection, Optional[GenerationCost]]:
        """
        Use GPT to detect which speaker is therapist vs patient.

        Analyzes:
        - Opening statements (therapists typically introduce themselves)
        - Clinical language patterns
        - Question-asking patterns (therapists ask more assessment questions)
        - Speaking ratio (therapists typically 30-40%, patients 60-70%)
        - Conversational dynamics
        """
        system_prompt = self._get_detection_system_prompt()
        user_prompt = self._create_detection_user_prompt(segments)

        start_time = time.time()
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"}
        )

        # Track cost and timing
        cost_info = track_generation_cost(
            response=response,
            task="speaker_labeling",
            model=self.model,
            start_time=start_time
        )

        result = json.loads(response.choices[0].message.content)
        return SpeakerRoleDetection(**result), cost_info

    def _get_detection_system_prompt(self) -> str:
        """System prompt for speaker role detection"""
        return """You are an expert clinical psychologist analyzing therapy session transcripts.

Your task is to determine which speaker is the THERAPIST and which is the PATIENT.

## Detection Criteria:

1. **Opening Statements** (strongest signal):
   - Therapists typically introduce themselves ("I'm Dr. [Name]", "Welcome, I'm your therapist")
   - Therapists explain confidentiality and session structure
   - Therapists ask initial questions ("What brings you in today?")

2. **Clinical Language Patterns**:
   - Therapists use clinical terminology (e.g., "passive suicidal ideation", "cognitive restructuring")
   - Therapists validate emotions ("That sounds really difficult")
   - Therapists use reflective listening ("What I'm hearing is...")

3. **Question Patterns**:
   - Therapists ask more open-ended questions
   - Therapists use assessment questions (symptoms, history, functioning)
   - Patients ask fewer questions, mostly clarifying

4. **Speaking Ratio**:
   - Therapists typically speak 30-40% of session time
   - Patients typically speak 60-70% of session time
   - (Exception: Crisis sessions may have more therapist talking)

5. **Conversational Dynamics**:
   - Therapists guide session flow and topic transitions
   - Therapists provide psychoeducation
   - Patients share personal experiences and emotions

## Output Format:

Return a JSON object with:
- `therapist_speaker_id`: "SPEAKER_00" or "SPEAKER_01"
- `patient_speaker_id`: "SPEAKER_00" or "SPEAKER_01"
- `confidence`: float (0.0-1.0) based on clarity of signals
- `reasoning`: string explaining your determination

## Confidence Guidelines:

- 0.9-1.0: Clear introduction or multiple strong signals
- 0.7-0.89: Strong patterns but no explicit introduction
- 0.5-0.69: Moderate confidence, some conflicting signals
- Below 0.5: Unclear or ambiguous (flag for manual review)

Be thorough but concise in your reasoning."""

    def _create_detection_user_prompt(self, segments: List[Dict[str, Any]]) -> str:
        """Create user prompt with transcript excerpt for role detection"""
        # Use first 15-20 segments (usually enough to determine roles)
        excerpt_segments = segments[:20]

        # Calculate speaking statistics
        speaker_stats = self._calculate_speaker_stats(segments)

        # Format transcript excerpt
        transcript_text = "\n\n".join([
            f"[{seg['speaker']}] ({seg['start']:.1f}s - {seg['end']:.1f}s): {seg['text']}"
            for seg in excerpt_segments
        ])

        return f"""Analyze this therapy session transcript and determine speaker roles.

## Transcript Excerpt (First 20 segments):

{transcript_text}

## Speaking Statistics (Full Session):

{json.dumps(speaker_stats, indent=2)}

## Your Task:

Determine which speaker is the therapist and which is the patient. Provide your analysis in the specified JSON format."""

    def _calculate_speaker_stats(self, segments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate speaking time and segment counts for each speaker"""
        stats = {}

        for seg in segments:
            speaker_id = seg['speaker']
            duration = seg['end'] - seg['start']

            if speaker_id not in stats:
                stats[speaker_id] = {
                    'total_time_seconds': 0,
                    'segment_count': 0
                }

            stats[speaker_id]['total_time_seconds'] += duration
            stats[speaker_id]['segment_count'] += 1

        # Add percentages
        total_time = sum(s['total_time_seconds'] for s in stats.values())
        for speaker_id in stats:
            stats[speaker_id]['percentage'] = round(
                (stats[speaker_id]['total_time_seconds'] / total_time) * 100, 1
            )

        return stats

    def _merge_consecutive_segments(
        self,
        segments: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Merge consecutive segments from the same speaker.

        Returns list of merged segments with:
        - speaker: original speaker ID
        - text: combined text with spaces
        - start: timestamp of first segment
        - end: timestamp of last segment
        """
        if not segments:
            return []

        merged = []
        current_block = {
            'speaker': segments[0]['speaker'],
            'text': segments[0]['text'],
            'start': segments[0]['start'],
            'end': segments[0]['end']
        }

        for seg in segments[1:]:
            if seg['speaker'] == current_block['speaker']:
                # Same speaker - merge
                current_block['text'] += ' ' + seg['text']
                current_block['end'] = seg['end']
            else:
                # Different speaker - save current block and start new one
                merged.append(current_block)
                current_block = {
                    'speaker': seg['speaker'],
                    'text': seg['text'],
                    'start': seg['start'],
                    'end': seg['end']
                }

        # Don't forget the last block
        merged.append(current_block)

        return merged

    def _apply_labels_and_format(
        self,
        merged_segments: List[Dict[str, Any]],
        detection: SpeakerRoleDetection,
        therapist_label: str,
        patient_label: str
    ) -> List[LabeledSegment]:
        """
        Apply human-readable labels and format timestamps.

        Maps:
        - Therapist speaker ID → therapist_label (e.g., "Therapist")
        - Patient speaker ID → patient_label (e.g., "You")
        - Float timestamps → MM:SS format
        """
        labeled = []

        for seg in merged_segments:
            # Determine speaker label
            if seg['speaker'] == detection.therapist_speaker_id:
                speaker_label = therapist_label
            elif seg['speaker'] == detection.patient_speaker_id:
                speaker_label = patient_label
            else:
                # Fallback (shouldn't happen if detection is correct)
                speaker_label = seg['speaker']

            # Format timestamp
            formatted_timestamp = self._format_timestamp(seg['start'])

            labeled.append(LabeledSegment(
                speaker=speaker_label,
                text=seg['text'],
                timestamp=formatted_timestamp
            ))

        return labeled

    def _format_timestamp(self, seconds: float) -> str:
        """
        Convert float seconds to MM:SS format.

        Examples:
        - 0.0 → "00:00"
        - 28.4 → "00:28"
        - 83.7 → "01:24"
        - 3600.0 → "60:00"
        """
        total_seconds = int(seconds)
        minutes = total_seconds // 60
        secs = total_seconds % 60
        return f"{minutes:02d}:{secs:02d}"


# ============================================
# Convenience Functions
# ============================================

def label_session_transcript(
    session_id: str,
    raw_segments: List[Dict[str, Any]],
    openai_api_key: str,
    override_model: Optional[str] = None
) -> SpeakerLabelingResult:
    """
    Convenience function for labeling a session transcript.

    Args:
        session_id: Session UUID (for logging)
        raw_segments: Raw transcript segments with SPEAKER_00/SPEAKER_01
        openai_api_key: OpenAI API key
        override_model: Optional model override (default: uses task config)

    Returns:
        SpeakerLabelingResult with labeled transcript (Therapist/You labels)
    """
    labeler = SpeakerLabeler(openai_api_key, override_model=override_model)

    logger.info(f"Labeling transcript for session {session_id}")
    result = labeler.label_transcript(raw_segments)

    logger.info(
        f"Speaker labeling complete - Confidence: {result.detection.confidence:.2f}, "
        f"Therapist: {result.detection.therapist_speaker_id}, "
        f"Patient: {result.detection.patient_speaker_id}"
    )

    return result
