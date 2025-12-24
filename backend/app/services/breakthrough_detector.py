"""
Breakthrough Detection Service

Uses AI to analyze therapy session transcripts and identify therapeutic breakthroughs.
This service looks for genuine moments of insight, emotional shifts, and meaningful progress
without relying on hardcoded keywords or patterns.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import json
import time

from app.services.base_ai_generator import AsyncAIGenerator
from app.config.model_config import track_generation_cost, GenerationCost


@dataclass
class BreakthroughCandidate:
    """Represents a potential breakthrough moment in therapy"""
    timestamp_start: float
    timestamp_end: float
    speaker_sequence: List[Dict[str, str]]  # [{speaker, text}]
    breakthrough_type: str  # Now always "Positive Discovery"
    confidence_score: float  # 0.0 to 1.0
    description: str  # Full description
    label: str  # NEW: 2-3 word concise label for UI
    evidence: str  # What made the AI identify this as a breakthrough


@dataclass
class SessionBreakthroughAnalysis:
    """Complete breakthrough analysis for a therapy session"""
    session_id: str
    has_breakthrough: bool
    breakthrough_candidates: List[BreakthroughCandidate]
    primary_breakthrough: Optional[BreakthroughCandidate]
    session_summary: str
    emotional_trajectory: str  # e.g., "resistant → reflective → insight → relief"
    cost_info: Optional[GenerationCost] = None  # Cost tracking for this generation


class BreakthroughDetector(AsyncAIGenerator):
    """
    AI-powered breakthrough detection for therapy sessions.

    Inherits from AsyncAIGenerator for consistent initialization and cost tracking.

    Uses GPT-5 to identify genuine therapeutic breakthroughs by analyzing:
    - Emotional shifts and affect changes
    - Cognitive insights and reframing moments
    - Behavioral commitments and action planning
    - Resistance-to-acceptance patterns
    - Therapist-client interaction dynamics
    """

    def __init__(self, api_key: Optional[str] = None, override_model: Optional[str] = None):
        """
        Initialize with async OpenAI client and model selection.

        Args:
            api_key: OpenAI API key. If None, uses OPENAI_API_KEY env var.
            override_model: Optional model override for testing (default: uses gpt-5 from config)
        """
        super().__init__(api_key=api_key, override_model=override_model)

    def get_task_name(self) -> str:
        """Return the task name for model selection and cost tracking."""
        return "breakthrough_detection"

    def build_messages(self, context: Dict[str, Any]) -> List[Dict[str, str]]:
        """Build messages for the API call. Required by base class but not used directly."""
        return [
            {"role": "system", "content": self._create_breakthrough_detection_prompt()},
            {"role": "user", "content": context.get("prompt", "")}
        ]

    async def analyze_session(
        self,
        transcript: List[Dict[str, Any]],
        session_metadata: Optional[Dict[str, Any]] = None
    ) -> SessionBreakthroughAnalysis:
        """
        Analyze a therapy session transcript to identify A breakthrough (0 or 1).

        Args:
            transcript: List of segments with {start, end, text, speaker}
            session_metadata: Optional context (patient history, session number, etc.)

        Returns:
            SessionBreakthroughAnalysis with 0 or 1 breakthrough
        """
        # Extract conversational segments (group by speaker turns)
        conversation = self._extract_conversation_turns(transcript)

        # Use AI to identify potential breakthrough moment
        breakthrough_candidates, cost_info = await self._identify_breakthrough_candidates(
            conversation,
            session_metadata
        )

        # Primary breakthrough is the only breakthrough (or None)
        primary_breakthrough = breakthrough_candidates[0] if breakthrough_candidates else None

        # Generate session-level analysis
        session_summary, emotional_trajectory = self._generate_session_analysis(
            conversation,
            breakthrough_candidates
        )

        return SessionBreakthroughAnalysis(
            session_id=session_metadata.get("session_id", "unknown") if session_metadata else "unknown",
            has_breakthrough=len(breakthrough_candidates) > 0,
            breakthrough_candidates=breakthrough_candidates,  # List of 0 or 1
            primary_breakthrough=primary_breakthrough,
            session_summary=session_summary,
            emotional_trajectory=emotional_trajectory,
            cost_info=cost_info
        )

    def _extract_conversation_turns(
        self,
        transcript: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Convert raw transcript into speaker turns for better context.
        Groups consecutive segments by the same speaker.
        """
        conversation_turns = []
        current_turn = None

        for segment in transcript:
            speaker = segment.get("speaker", "UNKNOWN")
            text = segment.get("text", "").strip()
            start = segment.get("start", 0.0)
            end = segment.get("end", 0.0)

            if not text:
                continue

            # Start new turn or continue existing
            if current_turn is None or current_turn["speaker"] != speaker:
                if current_turn:
                    conversation_turns.append(current_turn)
                current_turn = {
                    "speaker": speaker,
                    "text": text,
                    "start": start,
                    "end": end
                }
            else:
                # Same speaker, extend turn
                current_turn["text"] += " " + text
                current_turn["end"] = end

        # Add final turn
        if current_turn:
            conversation_turns.append(current_turn)

        return conversation_turns

    async def _identify_breakthrough_candidates(
        self,
        conversation: List[Dict[str, Any]],
        session_metadata: Optional[Dict[str, Any]] = None
    ) -> List[BreakthroughCandidate]:
        """
        Use AI to identify A breakthrough moment in the conversation.
        Returns a list with 0 or 1 element (keeping list for backwards compatibility).
        """
        # Prepare conversation text for AI analysis
        conversation_text = self._format_conversation_for_ai(conversation)

        # Create AI prompt for breakthrough detection
        system_prompt = self._create_breakthrough_detection_prompt()

        # Call OpenAI API
        # NOTE: GPT-5 series does NOT support custom temperature - uses internal calibration
        try:
            start_time = time.time()
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Analyze this therapy session transcript:\n\n{conversation_text}"}
                ],
                response_format={"type": "json_object"}
            )

            # Track cost and timing
            session_id = session_metadata.get("session_id") if session_metadata else None
            cost_info = track_generation_cost(
                response=response,
                task="breakthrough_detection",
                model=self.model,
                start_time=start_time,
                session_id=session_id
            )

            # Parse AI response
            ai_analysis = json.loads(response.choices[0].message.content)

            # Convert AI finding to BreakthroughCandidate object
            candidate = self._parse_breakthrough_finding(ai_analysis, conversation)

            # Return list with 0 or 1 element, and include cost_info in metadata
            return [candidate] if candidate else [], cost_info

        except Exception as e:
            print(f"Error during breakthrough detection: {e}")
            return [], None

    def _create_breakthrough_detection_prompt(self) -> str:
        """
        Create ultra-strict system prompt for positive discoveries only.
        """
        return """You are an expert clinical psychologist analyzing therapy session transcripts to identify MAJOR THERAPEUTIC BREAKTHROUGHS.

**CRITICAL: A breakthrough is ONLY a POSITIVE SELF-DISCOVERY where the patient learns something fundamentally NEW about themselves that opens possibilities for healing and growth.**

## What IS a Breakthrough (Positive Discoveries Only):

1. **Root Cause Discovery** - Patient identifies the underlying cause of their struggles
   - Example: "I realize my ADHD is causing my depression, not laziness"
   - Example: "My relationship anxiety comes from childhood abandonment fears"

2. **Pattern Recognition** - Patient connects past experiences to current behavior
   - Example: "My anxious attachment style mirrors how my parents loved me conditionally"
   - Example: "I self-sabotage relationships because I fear being known"

3. **Identity Insight** - Patient discovers a fundamental truth about who they are
   - Example: "I'm not broken, I'm neurodivergent"
   - Example: "My perfectionism is a trauma response, not a personality trait"

4. **Reframe Revelation** - Patient shifts from self-blame to self-understanding
   - Example: "My forgetfulness is ADHD, not personal failure"
   - Example: "My sensitivity is a strength, not a weakness"

**Requirements for a TRUE Breakthrough:**
- Must be a NEW realization (not something they already knew)
- Must be POSITIVE (opens doors, reduces shame, creates hope)
- Must be about SELF (not about others or external circumstances)
- Must be TRANSFORMATIVE (changes how they see themselves or their struggles)
- Must inspire relief, hope, or self-compassion (not just awareness)

## What is NOT a Breakthrough:

❌ **Emotional Releases** - Crying, expressing feelings, vulnerability
   - "Patient shares suicidal ideation" → This is crisis intervention, not discovery
   - "Patient cries about loneliness" → This is catharsis, not insight

❌ **Routine CBT Work** - Identifying triggers, challenging distortions
   - "Patient identifies Instagram as trigger" → This is basic CBT, not breakthrough
   - "Patient challenges negative thought" → This is skill practice, not discovery

❌ **Skill Application** - Using DBT skills, setting boundaries
   - "Patient practices DEAR MAN" → This is skill building, not insight
   - "Patient uses grounding technique" → This is coping, not discovery

❌ **Progress Updates** - Feeling better, making improvements
   - "Patient reports better sleep" → This is progress, not breakthrough
   - "Patient expresses hope" → This is mood improvement, not discovery

❌ **Values Clarification / Self-Agency** - Deciding what matters, making choices, recognizing agency
   - "Patient decides to come out" → This is courage, not discovery
   - "Patient values authenticity" → This is decision-making, not insight
   - "Patient realizes they're choosing themselves" → This is empowerment/progress, not new self-knowledge
   - "Patient recognizes they have agency/control" → This is progress, not discovery
   - "Patient realizes they can trust themselves" → This is growth/confidence, not breakthrough

❌ **Negative Insights** - Recognizing problems without solutions
   - "Patient realizes they're unlovable" → This is negative, not transformative
   - "Patient sees they're stuck" → This is awareness without hope

❌ **External Realizations** - Learning about others or circumstances, not self
   - "Patient understands parents' perspective" → This is empathy, not self-discovery
   - "Patient recognizes relationship incompatibility" → This is about the relationship, not self
   - "Patient reframes breakup as incompatibility not personal deficiency" → This is cognitive reframing about external event, not self-discovery
   - "Patient realizes medication is working" → This is treatment response, not self-discovery

## Analysis Instructions:

1. Read the ENTIRE transcript carefully
2. Look for moments where patient says "Oh!", "Wait...", "I never realized...", "That makes sense now..."
3. Identify if this is a POSITIVE SELF-DISCOVERY (new understanding about themselves)
4. Verify it meets ALL requirements above
5. Ask: "Did the patient learn something fundamentally NEW about WHO THEY ARE (not about circumstances, treatment, or decisions)?"
6. If you're unsure, it's NOT a breakthrough - be strict!
7. Remember: Progress, growth, empowerment, and positive changes are WONDERFUL but are NOT breakthroughs unless they reveal something new about the patient's core identity, patterns, or psychological makeup

## Output Format:

If a breakthrough IS found:
```json
{
  "has_breakthrough": true,
  "breakthrough": {
    "description": "<Full description of the breakthrough moment>",
    "label": "<2-3 word concise label>",
    "confidence": <0.0-1.0>,
    "evidence": "<Specific quotes/behavior demonstrating the breakthrough>",
    "timestamp_start": <seconds>,
    "timestamp_end": <seconds>
  }
}
```

If NO breakthrough found:
```json
{
  "has_breakthrough": false,
  "breakthrough": null
}
```

**Label Guidelines:**
- 2-3 words maximum
- Captures the essence of the discovery
- Natural, non-robotic phrasing
- Examples: "ADHD Discovery", "Attachment Pattern", "Trauma Response Recognition"

**Confidence Scoring:**
- 1.0: Clear, transformative positive discovery with strong evidence
- 0.9: Very strong breakthrough with minor ambiguity
- 0.8: Solid breakthrough but less transformative
- <0.8: Probably not a genuine breakthrough - be strict!

**BE EXTREMELY SELECTIVE. Most sessions will NOT have a breakthrough. That's normal and expected.**"""

    def _format_conversation_for_ai(self, conversation: List[Dict[str, Any]]) -> str:
        """Format conversation turns into readable text for AI"""
        formatted = []
        for turn in conversation:
            speaker = turn["speaker"]
            text = turn["text"]
            start = turn["start"]

            # Format timestamp as MM:SS
            minutes = int(start // 60)
            seconds = int(start % 60)
            timestamp = f"{minutes:02d}:{seconds:02d}"

            formatted.append(f"[{timestamp}] {speaker}: {text}")

        return "\n".join(formatted)

    def _parse_breakthrough_finding(
        self,
        finding: Dict[str, Any],
        conversation: List[Dict[str, Any]]
    ) -> Optional[BreakthroughCandidate]:
        """
        Convert AI finding to BreakthroughCandidate object.
        Handles new JSON structure with label field.
        """
        try:
            # Check if breakthrough was found
            if not finding.get("breakthrough"):
                return None

            bt_data = finding["breakthrough"]

            # Extract speaker sequence from conversation based on timestamp
            start_time = bt_data.get("timestamp_start", 0)
            end_time = bt_data.get("timestamp_end", 0)

            relevant_turns = [
                {"speaker": turn["speaker"], "text": turn["text"]}
                for turn in conversation
                if turn["start"] >= start_time - 10 and turn["end"] <= end_time + 10
            ]

            return BreakthroughCandidate(
                timestamp_start=start_time,
                timestamp_end=end_time,
                speaker_sequence=relevant_turns,
                breakthrough_type="Positive Discovery",  # Single type now
                confidence_score=bt_data.get("confidence", 0.0),
                description=bt_data.get("description", ""),
                label=bt_data.get("label", ""),  # NEW: Add label field
                evidence=bt_data.get("evidence", "")
            )
        except Exception as e:
            print(f"Error parsing breakthrough finding: {e}")
            return None

    def _generate_session_analysis(
        self,
        conversation: List[Dict[str, Any]],
        breakthroughs: List[BreakthroughCandidate]
    ) -> tuple[str, str]:
        """
        Generate overall session summary and emotional trajectory.
        Uses the AI's analysis from breakthrough detection.
        """
        # These would be extracted from the AI response in _identify_breakthrough_candidates
        # For now, return defaults - in production, parse from AI response

        if breakthroughs:
            summary = f"Session showed {len(breakthroughs)} significant breakthrough moment(s). "
            summary += f"Primary insight: {breakthroughs[0].description}"
        else:
            summary = "Session focused on exploration and rapport-building without major breakthroughs."

        # Emotional trajectory would be extracted from AI analysis
        trajectory = "exploratory → engaged → reflective"

        return summary, trajectory

    def export_breakthrough_report(
        self,
        analysis: SessionBreakthroughAnalysis,
        output_path: str
    ) -> None:
        """Export breakthrough analysis to JSON file"""
        report = {
            "session_id": analysis.session_id,
            "has_breakthrough": analysis.has_breakthrough,
            "breakthrough_count": len(analysis.breakthrough_candidates),
            "primary_breakthrough": {
                "type": analysis.primary_breakthrough.breakthrough_type,
                "description": analysis.primary_breakthrough.description,
                "evidence": analysis.primary_breakthrough.evidence,
                "confidence": analysis.primary_breakthrough.confidence_score,
                "timestamp": f"{int(analysis.primary_breakthrough.timestamp_start // 60):02d}:{int(analysis.primary_breakthrough.timestamp_start % 60):02d}"
            } if analysis.primary_breakthrough else None,
            "all_breakthroughs": [
                {
                    "type": bt.breakthrough_type,
                    "description": bt.description,
                    "evidence": bt.evidence,
                    "confidence": bt.confidence_score,
                    "timestamp": f"{int(bt.timestamp_start // 60):02d}:{int(bt.timestamp_start % 60):02d}"
                }
                for bt in analysis.breakthrough_candidates
            ],
            "session_summary": analysis.session_summary,
            "emotional_trajectory": analysis.emotional_trajectory
        }

        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
