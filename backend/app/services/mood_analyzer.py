"""
Mood Analysis Service

Uses AI to analyze therapy session transcripts and extract patient mood scores.
Analyzes transcript content, sentiment, speaking patterns, and therapy-specific indicators
to produce a single 0.0-10.0 mood score (0.5 increments) where:
- 0.0 = Extremely distressed/negative
- 5.0 = Neutral/stable
- 10.0 = Very positive/content
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import openai
import os
import json
from app.config.model_config import get_model_name


@dataclass
class MoodAnalysis:
    """Represents mood analysis for a therapy session"""
    session_id: str
    mood_score: float  # 0.0 to 10.0 (0.5 increments)
    confidence: float  # 0.0 to 1.0
    rationale: str  # Explanation of the mood score
    key_indicators: List[str]  # Specific signals that influenced the score
    emotional_tone: str  # Overall emotional quality (e.g., "anxious", "hopeful", "flat")
    analyzed_at: datetime


class MoodAnalyzer:
    """
    AI-powered mood analysis for therapy sessions.

    Uses GPT-4o-mini to analyze patient mood by examining:
    - Emotional language and sentiment
    - Self-reported feelings and experiences
    - Energy level indicators (sleep, appetite, motivation)
    - Anxiety/depression symptom markers
    - Hopelessness vs. hopefulness expressions
    - Engagement level with therapist
    - Speaking patterns and verbal markers
    """

    def __init__(self, api_key: Optional[str] = None, override_model: Optional[str] = None):
        """
        Initialize the mood analyzer.

        Args:
            api_key: OpenAI API key. If None, uses OPENAI_API_KEY env var.
            override_model: Optional model override for testing (default: uses gpt-5-nano from config)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key required for mood analysis")

        openai.api_key = self.api_key
        self.model = get_model_name("mood_analysis", override_model=override_model)

    def analyze_session_mood(
        self,
        session_id: str,
        segments: List[Dict[str, Any]],
        patient_speaker_id: str = "SPEAKER_01"
    ) -> MoodAnalysis:
        """
        Analyze patient mood from therapy session transcript.

        Args:
            session_id: Unique identifier for the session
            segments: List of transcript segments with 'speaker', 'text', 'start', 'end'
            patient_speaker_id: Speaker ID for the patient (default: SPEAKER_01)

        Returns:
            MoodAnalysis with mood score, rationale, and indicators
        """
        # Extract patient dialogue only
        patient_segments = [
            seg for seg in segments
            if seg.get("speaker") == patient_speaker_id or seg.get("speaker_id") == patient_speaker_id
        ]

        if not patient_segments:
            raise ValueError(f"No segments found for patient speaker ID: {patient_speaker_id}")

        # Create analysis prompt
        prompt = self._create_analysis_prompt(patient_segments)

        # Call OpenAI API
        # NOTE: GPT-5 series does NOT support custom temperature - uses internal calibration
        try:
            response = openai.chat.completions.create(
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

            result = json.loads(response.choices[0].message.content)

            # Validate and round mood score to 0.5 increments
            mood_score = self._validate_mood_score(result.get("mood_score", 5.0))

            return MoodAnalysis(
                session_id=session_id,
                mood_score=mood_score,
                confidence=result.get("confidence", 0.8),
                rationale=result.get("rationale", ""),
                key_indicators=result.get("key_indicators", []),
                emotional_tone=result.get("emotional_tone", "neutral"),
                analyzed_at=datetime.utcnow()
            )

        except Exception as e:
            raise Exception(f"Mood analysis failed: {str(e)}")

    def _get_system_prompt(self) -> str:
        """System prompt defining the AI's role and instructions."""
        return """You are an expert clinical psychologist analyzing patient mood from therapy transcripts.

Your task is to assign a single mood score from 0.0 to 10.0 (in 0.5 increments) based on the patient's emotional state during the session.

**Mood Scale:**
- 0.0-2.0: Severe distress (suicidal ideation, crisis, overwhelming despair)
- 2.5-4.0: Significant distress (moderate-severe depression/anxiety symptoms)
- 4.5-5.5: Mild distress to neutral (some symptoms, manageable)
- 6.0-7.5: Positive baseline (stable, functional, minor concerns)
- 8.0-10.0: Very positive (hopeful, energized, thriving)

**What to analyze:**
1. **Emotional Language**: Words expressing feelings (sad, anxious, hopeful, excited)
2. **Self-Reported State**: Direct statements about how they feel
3. **Clinical Symptoms**: Sleep, appetite, energy, concentration, anhedonia
4. **Suicidal/Self-Harm Ideation**: Active vs passive vs none
5. **Hopelessness vs Hope**: Future orientation and outlook
6. **Functioning**: Work/school performance, relationships, self-care
7. **Engagement**: Energy in conversation, verbal fluency vs flatness
8. **Anxiety Markers**: Rumination, worry, panic symptoms, avoidance
9. **Depression Markers**: Low mood, loss of interest, fatigue, guilt
10. **Positive Indicators**: Moments of laughter, pride, connection, progress

**Output JSON format:**
{
  "mood_score": 4.5,
  "confidence": 0.85,
  "rationale": "Patient reports passive suicidal ideation, disrupted sleep (12 hrs/day), complete loss of interest in previously enjoyed activities (coding), and feelings of drowning. However, no active plan and reaching out for help shows some protective factors.",
  "key_indicators": [
    "Passive suicidal ideation present",
    "Severe sleep disruption (12 hours/day or insomnia)",
    "Complete anhedonia (can't open laptop)",
    "Recent relationship loss",
    "Reached out for help (positive factor)"
  ],
  "emotional_tone": "overwhelmed and despairing"
}

Be nuanced - consider both negative and positive signals. Don't default to middle scores."""

    def _create_analysis_prompt(self, patient_segments: List[Dict[str, Any]]) -> str:
        """Create the analysis prompt from patient transcript segments."""
        # Combine patient dialogue
        dialogue = "\n\n".join([
            f"[{self._format_timestamp(seg.get('start', 0))}] {seg.get('text', '')}"
            for seg in patient_segments
        ])

        return f"""Analyze this patient's mood from their therapy session dialogue.

**Patient Transcript:**

{dialogue}

**Instructions:**
1. Read the entire transcript carefully
2. Identify all mood-relevant signals (positive and negative)
3. Assign a mood score from 0.0 to 10.0 (0.5 increments only)
4. Provide clear rationale with specific evidence from transcript
5. List 3-5 key indicators that influenced your score

Return your analysis as JSON following the specified format."""

    def _format_timestamp(self, seconds: float) -> str:
        """Convert seconds to MM:SS format."""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"

    def _validate_mood_score(self, score: float) -> float:
        """
        Validate and round mood score to nearest 0.5 increment.

        Args:
            score: Raw mood score from AI

        Returns:
            Validated score between 0.0 and 10.0 in 0.5 increments
        """
        # Clamp to valid range
        score = max(0.0, min(10.0, score))

        # Round to nearest 0.5
        rounded = round(score * 2) / 2

        return rounded


# Convenience function for single-session analysis
def analyze_mood(
    session_id: str,
    segments: List[Dict[str, Any]],
    patient_speaker_id: str = "SPEAKER_01",
    api_key: Optional[str] = None
) -> MoodAnalysis:
    """
    Convenience function to analyze mood for a single session.

    Args:
        session_id: Unique session identifier
        segments: Transcript segments
        patient_speaker_id: Speaker ID for patient
        api_key: Optional OpenAI API key

    Returns:
        MoodAnalysis object
    """
    analyzer = MoodAnalyzer(api_key=api_key)
    return analyzer.analyze_session_mood(session_id, segments, patient_speaker_id)
