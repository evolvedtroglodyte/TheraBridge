"""
Session Bridge Generator

Generates patient-facing content for sharing therapy insights with support network.

Produces three categories of shareable content:
1. shareConcerns (4 items) - What I'm working through
2. shareProgress (4 items) - My recent wins and growth
3. setGoals (4 items) - What I'm focusing on next

Uses deep analysis and roadmap context to create personalized,
patient-friendly language suitable for sharing with family, friends, or support groups.

Example output:
{
    "shareConcerns": [
        "I've been feeling overwhelmed at work lately",
        "I'm working on managing my anxiety in social situations",
        "I've been processing some difficult memories from the past",
        "I'm learning to set better boundaries with family"
    ],
    "shareProgress": [
        "I've been practicing deep breathing when I feel stressed",
        "I spoke up about my needs in a relationship this week",
        "I recognized a negative thought pattern and challenged it",
        "I've been sleeping better since starting my wind-down routine"
    ],
    "setGoals": [
        "Practice grounding techniques 3 times this week",
        "Have one honest conversation about how I'm feeling",
        "Take 10 minutes daily for mindfulness",
        "Notice when I'm being self-critical and pause"
    ]
}
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import logging
import json

from app.services.base_ai_generator import SyncAIGenerator, GenerationResult
from app.config.model_config import GenerationCost
from app.utils.wave3_logger import create_session_bridge_logger, Wave3Event

logger = logging.getLogger(__name__)


@dataclass
class SessionBridgeData:
    """
    Generated session bridge content for patient sharing.

    Attributes:
        share_concerns: List of 4 items about current challenges
        share_progress: List of 4 items about recent wins/growth
        set_goals: List of 4 items about focus areas
        generation_context: Context data used for generation (for debugging)
        confidence_score: AI confidence in generation quality (0.0-1.0)
        generated_at: Timestamp of generation
        cost_info: Optional cost tracking data
    """
    share_concerns: List[str]
    share_progress: List[str]
    set_goals: List[str]
    generation_context: Optional[Dict[str, Any]] = None
    confidence_score: float = 0.8
    generated_at: datetime = field(default_factory=datetime.utcnow)
    cost_info: Optional[GenerationCost] = None

    def to_bridge_data(self) -> Dict[str, Any]:
        """
        Convert to JSONB format for session_bridge_versions.bridge_data column.

        Returns camelCase keys to match frontend expectations.
        """
        return {
            "shareConcerns": self.share_concerns,
            "shareProgress": self.share_progress,
            "setGoals": self.set_goals,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to full dictionary for debugging/logging."""
        result = {
            "shareConcerns": self.share_concerns,
            "shareProgress": self.share_progress,
            "setGoals": self.set_goals,
            "confidence_score": self.confidence_score,
            "generated_at": self.generated_at.isoformat(),
        }
        if self.generation_context:
            result["generation_context"] = self.generation_context
        if self.cost_info:
            result["cost_info"] = self.cost_info.to_dict()
        return result


class SessionBridgeGenerator(SyncAIGenerator):
    """
    AI-powered generator for patient-facing session bridge content.

    Uses deep analysis and roadmap data to create personalized, shareable
    content about the patient's therapy journey.
    """

    def get_task_name(self) -> str:
        return "session_bridge_generation"

    def build_messages(self, context: Dict[str, Any]) -> List[Dict[str, str]]:
        """Build messages for session bridge generation."""
        return [
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user", "content": self._create_user_prompt(context)}
        ]

    def _get_system_prompt(self) -> str:
        """System prompt for session bridge generation."""
        return """You are a compassionate therapy assistant helping patients share their mental health journey with their support network (family, friends, partner, support groups).

Your task is to generate shareable content that:
1. Uses first-person language ("I" statements)
2. Is honest but not overwhelming for the listener
3. Focuses on actionable insights and growth
4. Respects patient privacy while being authentic
5. Uses accessible, non-clinical language
6. Strikes a balance between vulnerability and hope

You will generate THREE categories of content:

**1. shareConcerns (4 items)** - "What I'm working through"
- Current challenges the patient is addressing in therapy
- Framed as active work, not complaints
- Shows self-awareness without being dramatic
- Examples: "I've been working on my anxiety around social situations"

**2. shareProgress (4 items)** - "My recent wins and growth"
- Concrete achievements and positive changes
- Small wins count! (showing up, trying new things)
- Demonstrates effort and progress
- Examples: "I practiced deep breathing when I felt anxious at work"

**3. setGoals (4 items)** - "What I'm focusing on next"
- Specific, achievable near-term goals
- Things the support network can encourage
- Practical and measurable when possible
- Examples: "I want to practice journaling 3 times this week"

**Important Guidelines:**
- Never reveal specific therapy session details or therapist interpretations
- Keep items 1-2 sentences max
- Avoid clinical jargon (say "feeling down" not "depressive episode")
- Frame challenges as growth opportunities, not problems
- If data is limited, generate thoughtful general items based on context
- Be warm and encouraging in tone

**Output Format:**
Return a JSON object with this exact structure:
{
    "shareConcerns": ["item 1", "item 2", "item 3", "item 4"],
    "shareProgress": ["item 1", "item 2", "item 3", "item 4"],
    "setGoals": ["item 1", "item 2", "item 3", "item 4"],
    "confidence_score": 0.85
}

The confidence_score (0.0-1.0) reflects how confident you are in the generation:
- 0.9+: Rich context, highly personalized content
- 0.7-0.8: Good context, solid personalization
- 0.5-0.6: Limited context, more generic content
- <0.5: Very limited context, mostly generic"""

    def _create_user_prompt(self, context: Dict[str, Any]) -> str:
        """Create user prompt from context data."""
        # Extract tier context
        tier1 = context.get("tier1_insights", {})
        tier2 = context.get("tier2_insights", {})
        tier3 = context.get("tier3_insights", {})

        # Current session info
        current = context.get("current_session", {})
        session_number = context.get("session_number", 1)

        # Roadmap data (if available)
        roadmap = context.get("roadmap_data", {})

        # Build prompt sections
        sections = []

        sections.append(f"""Generate session bridge content for this patient.

**Session Context:**
- This is session #{session_number}
- Mood score: {current.get('mood_score', 'N/A')}/10
- Main topics: {', '.join(current.get('topics', ['Unknown']))}
- Therapeutic technique: {current.get('technique', 'Unknown')}""")

        # Add tier 1 insights (most recent sessions)
        if tier1:
            sections.append("""
**Recent Session Insights (Last 1-3 sessions):**""")
            for session_id, insights in list(tier1.items())[:3]:
                wave1 = insights.get("wave1", {})
                wave2 = insights.get("wave2", {})

                # Extract key info
                mood = wave1.get("mood_score", "N/A")
                topics = ", ".join(wave1.get("topics", []))
                strengths = wave2.get("therapeutic_insights", {}).get("strengths", [])
                realizations = wave2.get("therapeutic_insights", {}).get("key_realizations", [])
                practices = wave2.get("recommendations", {}).get("practices", [])

                sections.append(f"""
- Mood: {mood}/10, Topics: {topics}
- Strengths observed: {', '.join(strengths[:2]) if strengths else 'N/A'}
- Key realizations: {', '.join(realizations[:2]) if realizations else 'N/A'}
- Recommended practices: {', '.join(practices[:2]) if practices else 'N/A'}""")

        # Add tier 2 insights (middle sessions)
        if tier2:
            sections.append("""
**Earlier Session Patterns (Sessions 4-7):**""")
            # Summarize tier 2
            all_strengths = []
            all_topics = []
            for session_id, insights in tier2.items():
                wave1 = insights.get("wave1", {})
                wave2 = insights.get("wave2", {})
                all_topics.extend(wave1.get("topics", []))
                all_strengths.extend(
                    wave2.get("therapeutic_insights", {}).get("strengths", [])
                )
            sections.append(f"""
- Recurring topics: {', '.join(set(all_topics)[:5])}
- Demonstrated strengths: {', '.join(set(all_strengths)[:4])}""")

        # Add tier 3 summary (oldest sessions)
        if tier3:
            sections.append("""
**Foundation Patterns (Early sessions):**""")
            summary = tier3.get("summary", "Limited historical context")
            sections.append(f"- {summary}")

        # Add roadmap context if available
        if roadmap:
            sections.append("""
**Current Roadmap Focus:**""")
            current_phase = roadmap.get("current_phase", {})
            if current_phase:
                sections.append(f"""
- Phase: {current_phase.get('name', 'Unknown')}
- Focus areas: {', '.join(current_phase.get('focus_areas', ['N/A'])[:3])}""")

        sections.append("""

**Instructions:**
Generate 4 items for each category based on this patient's journey.
Be specific to their situation when context allows.
Return valid JSON with shareConcerns, shareProgress, setGoals, and confidence_score.""")

        return "\n".join(sections)

    def generate_session_bridge(
        self,
        patient_id: str,
        session_id: str,
        session_number: int,
        context: Dict[str, Any],
        log_events: bool = True
    ) -> SessionBridgeData:
        """
        Generate session bridge content.

        Args:
            patient_id: Patient UUID
            session_id: Current session UUID
            session_number: Session number (1-N)
            context: Context with tier1_insights, tier2_insights, tier3_insights,
                     current_session, and optionally roadmap_data
            log_events: Whether to log Wave3 events (default: True)

        Returns:
            SessionBridgeData with generated content
        """
        wave3_logger = None
        if log_events:
            wave3_logger = create_session_bridge_logger(patient_id)
            wave3_logger.log_start(
                session_number=session_number,
                details={"session_id": session_id}
            )

        try:
            # Add session number to context for prompt
            context["session_number"] = session_number

            # Generate using base class template method
            result = self.generate(
                context=context,
                session_id=session_id,
                patient_id=patient_id,
                metadata={"session_number": session_number}
            )

            # Parse result into SessionBridgeData
            content = result.content
            bridge_data = SessionBridgeData(
                share_concerns=content.get("shareConcerns", [])[:4],
                share_progress=content.get("shareProgress", [])[:4],
                set_goals=content.get("setGoals", [])[:4],
                generation_context={
                    "tier1_count": len(context.get("tier1_insights", {})),
                    "tier2_count": len(context.get("tier2_insights", {})),
                    "has_tier3": bool(context.get("tier3_insights")),
                    "has_roadmap": bool(context.get("roadmap_data")),
                },
                confidence_score=content.get("confidence_score", 0.7),
                cost_info=result.cost_info
            )

            # Validate we have enough items
            bridge_data = self._ensure_minimum_items(bridge_data)

            if wave3_logger and result.cost_info:
                wave3_logger.log_event(
                    Wave3Event.BRIDGE_GENERATE,
                    session_id=session_id,
                    session_number=session_number,
                    duration_ms=result.cost_info.duration_ms,
                    cost=result.cost_info.cost,
                    details={"confidence": bridge_data.confidence_score}
                )

            logger.info(
                f"Generated session bridge for session {session_number} "
                f"(confidence: {bridge_data.confidence_score:.2f})"
            )

            return bridge_data

        except Exception as e:
            if wave3_logger:
                wave3_logger.log_failed(str(e), details={"session_id": session_id})
            logger.error(f"Failed to generate session bridge: {e}")
            raise

    def _ensure_minimum_items(self, data: SessionBridgeData) -> SessionBridgeData:
        """
        Ensure each category has exactly 4 items.

        Adds generic fallback items if needed.
        """
        fallback_concerns = [
            "I'm working on understanding my emotions better",
            "I'm learning to cope with stress in healthier ways",
            "I'm building self-awareness about my patterns",
            "I'm developing better communication skills"
        ]
        fallback_progress = [
            "I showed up for therapy this week",
            "I'm becoming more aware of my feelings",
            "I tried a new coping strategy",
            "I'm being more honest about how I feel"
        ]
        fallback_goals = [
            "Practice one self-care activity this week",
            "Notice when I'm feeling stressed and pause",
            "Share one thing about my week with someone I trust",
            "Try to be patient with myself when things are hard"
        ]

        # Pad each list to 4 items
        while len(data.share_concerns) < 4:
            idx = len(data.share_concerns)
            data.share_concerns.append(fallback_concerns[idx])
        while len(data.share_progress) < 4:
            idx = len(data.share_progress)
            data.share_progress.append(fallback_progress[idx])
        while len(data.set_goals) < 4:
            idx = len(data.set_goals)
            data.set_goals.append(fallback_goals[idx])

        return data


# =============================================================================
# Convenience function
# =============================================================================

def generate_session_bridge(
    patient_id: str,
    session_id: str,
    session_number: int,
    context: Dict[str, Any],
    api_key: Optional[str] = None,
    override_model: Optional[str] = None
) -> SessionBridgeData:
    """
    Convenience function to generate session bridge content.

    Args:
        patient_id: Patient UUID
        session_id: Current session UUID
        session_number: Session number (1-N)
        context: Context dictionary with tier insights
        api_key: Optional OpenAI API key
        override_model: Optional model override

    Returns:
        SessionBridgeData with generated content
    """
    generator = SessionBridgeGenerator(api_key=api_key, override_model=override_model)
    return generator.generate_session_bridge(
        patient_id=patient_id,
        session_id=session_id,
        session_number=session_number,
        context=context
    )
