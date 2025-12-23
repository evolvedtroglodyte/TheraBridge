"""
Deep Clinical Analysis Service

Uses AI to synthesize all Wave 1 analysis outputs + patient history to generate
comprehensive, patient-facing clinical insights.

Analyzes:
- Progress indicators (symptom reduction, skill development, goal progress)
- Therapeutic insights (key realizations, patterns, growth areas, strengths)
- Coping skill development (skills learned, proficiency, practice recommendations)
- Therapeutic relationship quality (engagement, openness, alliance strength)
- Actionable recommendations (practices, resources, reflection prompts)

Uses GPT-4o for complex reasoning and synthesis.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import openai
import os
import json
import logging

from app.database import get_db
from supabase import Client

logger = logging.getLogger(__name__)


@dataclass
class ProgressIndicator:
    """Progress indicator from the session"""
    symptom_reduction: Optional[Dict[str, Any]] = None
    skill_development: List[Dict[str, str]] = None
    goal_progress: List[Dict[str, str]] = None
    behavioral_changes: List[str] = None

    def __post_init__(self):
        if self.skill_development is None:
            self.skill_development = []
        if self.goal_progress is None:
            self.goal_progress = []
        if self.behavioral_changes is None:
            self.behavioral_changes = []


@dataclass
class TherapeuticInsights:
    """Key insights from the session"""
    key_realizations: List[str]
    patterns: List[str]
    growth_areas: List[str]
    strengths: List[str]


@dataclass
class CopingSkills:
    """Coping skills development"""
    learned: List[str]
    proficiency: Dict[str, str]  # skill -> 'beginner'/'developing'/'proficient'
    practice_recommendations: List[str]


@dataclass
class TherapeuticRelationship:
    """Therapeutic relationship quality"""
    engagement_level: str  # 'low', 'moderate', 'high'
    engagement_evidence: str
    openness: str  # 'guarded', 'somewhat_open', 'very_open'
    openness_evidence: str
    alliance_strength: str  # 'weak', 'developing', 'strong'
    alliance_evidence: str


@dataclass
class Recommendations:
    """Patient-facing recommendations"""
    practices: List[str]
    resources: List[str]
    reflection_prompts: List[str]


@dataclass
class DeepAnalysis:
    """Complete deep clinical analysis"""
    session_id: str
    progress_indicators: ProgressIndicator
    therapeutic_insights: TherapeuticInsights
    coping_skills: CopingSkills
    therapeutic_relationship: TherapeuticRelationship
    recommendations: Recommendations
    confidence_score: float  # 0.0 to 1.0
    analyzed_at: datetime

    def to_dict(self) -> dict:
        """Convert to dictionary for JSONB storage"""
        return {
            "progress_indicators": asdict(self.progress_indicators),
            "therapeutic_insights": asdict(self.therapeutic_insights),
            "coping_skills": asdict(self.coping_skills),
            "therapeutic_relationship": asdict(self.therapeutic_relationship),
            "recommendations": asdict(self.recommendations),
            "confidence_score": self.confidence_score,
            "analyzed_at": self.analyzed_at.isoformat()
        }


class DeepAnalyzer:
    """
    AI-powered deep clinical analysis for therapy sessions.

    Synthesizes:
    - Current session transcript
    - Wave 1 analysis outputs (mood, topics, breakthrough)
    - Patient history (previous sessions, mood trends, recurring themes)
    """

    def __init__(self, api_key: Optional[str] = None, db: Optional[Client] = None):
        """
        Initialize the deep analyzer.

        Args:
            api_key: OpenAI API key. If None, uses OPENAI_API_KEY env var.
            db: Supabase client. If None, uses default from get_db()
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key required for deep analysis")

        openai.api_key = self.api_key
        self.model = "gpt-4o"  # More complex reasoning needed
        self.db = db or next(get_db())

    async def analyze_session(
        self,
        session_id: str,
        session: Dict[str, Any]
    ) -> DeepAnalysis:
        """
        Perform deep clinical analysis on a therapy session.

        Args:
            session_id: Unique identifier for the session
            session: Session data with transcript and Wave 1 analysis results

        Returns:
            DeepAnalysis with comprehensive insights
        """
        logger.info(f"🧠 Starting deep analysis for session {session_id}")

        # Gather all context
        context = await self._build_analysis_context(session_id, session)

        # Create analysis prompt
        prompt = self._create_analysis_prompt(context)

        # Call OpenAI API
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
                temperature=0.3,  # Lower temperature for consistent analysis
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)

            # Parse and validate result
            analysis = self._parse_analysis_result(session_id, result)

            logger.info(f"✓ Deep analysis complete for session {session_id}")

            return analysis

        except Exception as e:
            logger.error(f"Deep analysis failed for session {session_id}: {e}")
            raise Exception(f"Deep analysis failed: {str(e)}")

    def _get_system_prompt(self) -> str:
        """System prompt defining the AI's role and instructions."""
        return """You are an expert clinical psychologist analyzing therapy sessions to provide
patient-facing insights. Your goal is to help the patient understand their progress, strengths,
and areas for growth in a compassionate, empowering way.

You have access to:
1. Full session transcript with speaker roles (Therapist/Client)
2. AI-extracted mood score, topics, action items, and therapeutic technique
3. Breakthrough moments detected during the session
4. Patient's therapy history (previous sessions, mood trends, recurring themes)

Your task is to generate a deep clinical analysis with the following dimensions:

**1. Progress Indicators** (clinical but accessible):
   - Symptom reduction or improvement (sleep, anxiety, depression, etc.)
   - Skill development (DBT, CBT, mindfulness, etc.)
   - Goal progress (if goals mentioned in history)
   - Behavioral changes (relationships, work/school, self-care)

**2. Therapeutic Insights** (patient empowerment):
   - Key realizations or "aha moments" from this session
   - Connections to previous sessions (patterns emerging)
   - Growth areas (framed positively, not deficits)
   - Strengths demonstrated (resilience, openness, effort, courage)

**3. Coping Skill Development**:
   - Skills learned or practiced (TIPP, grounding, opposite action, etc.)
   - Proficiency level: 'beginner' (just introduced), 'developing' (practicing with support), 'proficient' (using independently)
   - Practice recommendations (specific, actionable, encouraging)

**4. Therapeutic Relationship Quality**:
   - Engagement level: 'low' (disengaged, minimal participation), 'moderate' (some engagement), 'high' (active, collaborative)
   - Openness/vulnerability: 'guarded' (surface-level), 'somewhat_open' (some vulnerability), 'very_open' (deep sharing)
   - Alliance strength: 'weak' (disconnected), 'developing' (building trust), 'strong' (collaborative partnership)
   - Provide evidence from transcript for each rating

**5. Recommendations** (patient-friendly, actionable):
   - Practices: Specific homework or exercises to try before next session
   - Resources: Apps, books, videos, worksheets (if applicable to session content)
   - Reflection prompts: Journal prompts for deeper self-exploration

**Guidelines**:
- Use accessible language (avoid overly clinical jargon)
- Frame everything with compassion and hope
- Acknowledge both struggles and strengths equally
- Be specific with evidence from transcript
- Avoid making the patient feel judged or inadequate
- Celebrate small wins and efforts, not just outcomes
- If information is not available (e.g., no previous sessions), acknowledge this and focus on current session
- Use direct, active voice (not "The patient demonstrated..." but "You demonstrated...")

**Output Format**: Return a JSON object with this exact structure:

{
  "progress_indicators": {
    "symptom_reduction": {
      "detected": true/false,
      "description": "specific evidence from session",
      "confidence": 0.0-1.0
    },
    "skill_development": [
      {
        "skill": "specific skill name",
        "proficiency": "beginner/developing/proficient",
        "evidence": "specific quote or behavior from session"
      }
    ],
    "goal_progress": [
      {
        "goal": "specific goal",
        "status": "on_track/needs_attention/achieved",
        "evidence": "specific evidence"
      }
    ],
    "behavioral_changes": ["specific behavioral change observed"]
  },

  "therapeutic_insights": {
    "key_realizations": ["specific realization with context"],
    "patterns": ["pattern across sessions with evidence"],
    "growth_areas": ["growth area framed positively"],
    "strengths": ["specific strength demonstrated with evidence"]
  },

  "coping_skills": {
    "learned": ["skill name"],
    "proficiency": {
      "Skill_Name": "beginner/developing/proficient"
    },
    "practice_recommendations": ["specific practice instruction"]
  },

  "therapeutic_relationship": {
    "engagement_level": "low/moderate/high",
    "engagement_evidence": "specific evidence",
    "openness": "guarded/somewhat_open/very_open",
    "openness_evidence": "specific evidence",
    "alliance_strength": "weak/developing/strong",
    "alliance_evidence": "specific evidence"
  },

  "recommendations": {
    "practices": ["specific practice to try"],
    "resources": ["resource name and brief description"],
    "reflection_prompts": ["journal prompt question"]
  },

  "confidence_score": 0.0-1.0
}

**Confidence scoring:**
- 0.9-1.0: Rich session data, clear patterns, strong evidence
- 0.7-0.8: Good session data, some patterns visible
- 0.5-0.6: Limited data or first session
- <0.5: Insufficient data for meaningful analysis"""

    async def _build_analysis_context(
        self,
        session_id: str,
        session: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build comprehensive context for deep analysis.

        Args:
            session_id: Session UUID
            session: Current session data

        Returns:
            Dictionary with all necessary context
        """
        patient_id = session["patient_id"]

        # Get patient history (last 5 sessions)
        previous_sessions = await self._get_previous_sessions(patient_id, current_session_id=session_id, limit=5)

        # Get mood trend
        mood_trend = await self._get_mood_trend(patient_id, days=90)

        # Get recurring topics
        recurring_topics = await self._get_recurring_topics(patient_id)

        # Get technique history
        technique_history = await self._get_technique_history(patient_id)

        # Get breakthrough history
        breakthrough_history = await self._get_breakthrough_history(patient_id)

        # Detect speaker roles (Therapist/Client)
        speaker_roles = self._detect_speaker_roles(session.get("transcript", []))

        return {
            "current_session": {
                "session_id": session_id,
                "date": session.get("session_date"),
                "transcript": self._format_transcript(session.get("transcript", []), speaker_roles),
                "mood_score": session.get("mood_score"),
                "mood_indicators": session.get("mood_indicators", []),
                "emotional_tone": session.get("emotional_tone"),
                "topics": session.get("topics", []),
                "action_items": session.get("action_items", []),
                "technique": session.get("technique"),
                "summary": session.get("summary"),
                "breakthrough": session.get("breakthrough_data"),
            },
            "patient_history": {
                "previous_sessions": previous_sessions,
                "mood_trend": mood_trend,
                "recurring_topics": recurring_topics,
                "technique_history": technique_history,
                "breakthrough_history": breakthrough_history,
                "total_sessions": len(previous_sessions) + 1,  # Include current
            }
        }

    def _create_analysis_prompt(self, context: Dict[str, Any]) -> str:
        """Create the analysis prompt from context."""
        current = context["current_session"]
        history = context["patient_history"]

        # Format previous sessions summary
        prev_sessions_summary = "No previous sessions available."
        if history["previous_sessions"]:
            prev_sessions_summary = "\n".join([
                f"- Session {i+1} ({s.get('session_date', 'Unknown date')}): "
                f"Mood: {s.get('mood_score', 'N/A')}/10, "
                f"Topics: {', '.join(s.get('topics', []))}, "
                f"Technique: {s.get('technique', 'N/A')}"
                for i, s in enumerate(history["previous_sessions"])
            ])

        return f"""Analyze this therapy session and provide comprehensive patient-facing insights.

**CURRENT SESSION DATA:**

**Date:** {current.get('date', 'Unknown')}

**Mood Analysis:**
- Score: {current.get('mood_score', 'N/A')}/10.0
- Emotional Tone: {current.get('emotional_tone', 'N/A')}
- Key Indicators: {', '.join(current.get('mood_indicators', []))}

**Topics & Technique:**
- Main Topics: {', '.join(current.get('topics', []))}
- Therapeutic Technique: {current.get('technique', 'N/A')}
- Action Items: {', '.join(current.get('action_items', []))}
- Summary: {current.get('summary', 'N/A')}

**Breakthrough Detected:** {current.get('breakthrough') is not None}
{f"Breakthrough Type: {current['breakthrough']['type']}" if current.get('breakthrough') else ""}
{f"Breakthrough Description: {current['breakthrough']['description']}" if current.get('breakthrough') else ""}

**Session Transcript:**

{current.get('transcript', 'No transcript available.')}

---

**PATIENT HISTORY:**

**Total Sessions:** {history['total_sessions']}

**Previous Sessions:**
{prev_sessions_summary}

**Mood Trend:** {history.get('mood_trend', {}).get('trend', 'Unknown')}
- Recent Average: {history.get('mood_trend', {}).get('recent_avg', 'N/A')}
- Historical Average: {history.get('mood_trend', {}).get('historical_avg', 'N/A')}

**Recurring Topics:** {', '.join([t['topic'] for t in history.get('recurring_topics', [])[:5]])}

**Techniques Used Previously:** {', '.join([t['technique'] for t in history.get('technique_history', [])[:5]])}

**Breakthrough History:** {len(history.get('breakthrough_history', []))} breakthrough moments detected across all sessions

---

**INSTRUCTIONS:**

1. Read the entire current session transcript carefully
2. Analyze in context of patient history and trends
3. Extract progress indicators (symptom reduction, skill development, goals, behavioral changes)
4. Identify key insights (realizations, patterns, growth areas, strengths)
5. Assess coping skill development (learned, proficiency, recommendations)
6. Evaluate therapeutic relationship quality (engagement, openness, alliance)
7. Provide actionable recommendations (practices, resources, reflection prompts)
8. Assign confidence score based on data quality and clarity

Return your analysis as JSON following the specified format. Be compassionate, specific, and empowering."""

    def _parse_analysis_result(self, session_id: str, result: Dict[str, Any]) -> DeepAnalysis:
        """Parse and validate AI response into DeepAnalysis object."""
        # Extract progress indicators
        progress_data = result.get("progress_indicators", {})
        progress_indicators = ProgressIndicator(
            symptom_reduction=progress_data.get("symptom_reduction"),
            skill_development=progress_data.get("skill_development", []),
            goal_progress=progress_data.get("goal_progress", []),
            behavioral_changes=progress_data.get("behavioral_changes", [])
        )

        # Extract therapeutic insights
        insights_data = result.get("therapeutic_insights", {})
        therapeutic_insights = TherapeuticInsights(
            key_realizations=insights_data.get("key_realizations", []),
            patterns=insights_data.get("patterns", []),
            growth_areas=insights_data.get("growth_areas", []),
            strengths=insights_data.get("strengths", [])
        )

        # Extract coping skills
        skills_data = result.get("coping_skills", {})
        coping_skills = CopingSkills(
            learned=skills_data.get("learned", []),
            proficiency=skills_data.get("proficiency", {}),
            practice_recommendations=skills_data.get("practice_recommendations", [])
        )

        # Extract therapeutic relationship
        relationship_data = result.get("therapeutic_relationship", {})
        therapeutic_relationship = TherapeuticRelationship(
            engagement_level=relationship_data.get("engagement_level", "moderate"),
            engagement_evidence=relationship_data.get("engagement_evidence", ""),
            openness=relationship_data.get("openness", "somewhat_open"),
            openness_evidence=relationship_data.get("openness_evidence", ""),
            alliance_strength=relationship_data.get("alliance_strength", "developing"),
            alliance_evidence=relationship_data.get("alliance_evidence", "")
        )

        # Extract recommendations
        rec_data = result.get("recommendations", {})
        recommendations = Recommendations(
            practices=rec_data.get("practices", []),
            resources=rec_data.get("resources", []),
            reflection_prompts=rec_data.get("reflection_prompts", [])
        )

        # Confidence score
        confidence_score = result.get("confidence_score", 0.7)
        confidence_score = max(0.0, min(1.0, confidence_score))  # Clamp to [0, 1]

        return DeepAnalysis(
            session_id=session_id,
            progress_indicators=progress_indicators,
            therapeutic_insights=therapeutic_insights,
            coping_skills=coping_skills,
            therapeutic_relationship=therapeutic_relationship,
            recommendations=recommendations,
            confidence_score=confidence_score,
            analyzed_at=datetime.utcnow()
        )

    # =============================================================================
    # Helper Functions - Patient History
    # =============================================================================

    async def _get_previous_sessions(
        self,
        patient_id: str,
        current_session_id: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get previous sessions for the patient."""
        response = (
            self.db.table("therapy_sessions")
            .select("id, session_date, mood_score, topics, technique, summary")
            .eq("patient_id", patient_id)
            .neq("id", current_session_id)
            .order("session_date", desc=True)
            .limit(limit)
            .execute()
        )
        return response.data if response.data else []

    async def _get_mood_trend(self, patient_id: str, days: int = 90) -> Dict[str, Any]:
        """Get mood trend for the patient."""
        try:
            response = self.db.rpc("get_patient_mood_stats", {
                "p_patient_id": patient_id,
                "p_days": days
            }).execute()

            if response.data and len(response.data) > 0:
                return response.data[0]
            return {}
        except Exception as e:
            logger.warning(f"Failed to get mood trend: {e}")
            return {}

    async def _get_recurring_topics(self, patient_id: str) -> List[Dict[str, Any]]:
        """Get recurring topics for the patient."""
        try:
            response = (
                self.db.table("patient_topic_frequency")
                .select("*")
                .eq("patient_id", patient_id)
                .order("frequency", desc=True)
                .limit(10)
                .execute()
            )
            return response.data if response.data else []
        except Exception as e:
            logger.warning(f"Failed to get recurring topics: {e}")
            return []

    async def _get_technique_history(self, patient_id: str) -> List[Dict[str, Any]]:
        """Get technique usage history for the patient."""
        try:
            response = (
                self.db.table("patient_technique_history")
                .select("*")
                .eq("patient_id", patient_id)
                .order("usage_count", desc=True)
                .limit(10)
                .execute()
            )
            return response.data if response.data else []
        except Exception as e:
            logger.warning(f"Failed to get technique history: {e}")
            return []

    async def _get_breakthrough_history(self, patient_id: str) -> List[Dict[str, Any]]:
        """Get breakthrough history for the patient."""
        try:
            # Get all sessions for this patient
            sessions_response = (
                self.db.table("therapy_sessions")
                .select("id")
                .eq("patient_id", patient_id)
                .execute()
            )

            if not sessions_response.data:
                return []

            session_ids = [s["id"] for s in sessions_response.data]

            # Get breakthroughs for these sessions
            response = (
                self.db.table("breakthrough_history")
                .select("*")
                .in_("session_id", session_ids)
                .order("created_at", desc=True)
                .limit(10)
                .execute()
            )
            return response.data if response.data else []
        except Exception as e:
            logger.warning(f"Failed to get breakthrough history: {e}")
            return []

    def _detect_speaker_roles(self, segments: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Detect speaker roles (Therapist/Client) using heuristics.

        Returns:
            Mapping of speaker IDs to roles
        """
        if not segments:
            return {"SPEAKER_00": "Therapist", "SPEAKER_01": "Client"}

        # Count speaking time for each speaker
        speaker_times = {}
        for seg in segments:
            speaker = seg.get("speaker") or seg.get("speaker_id", "UNKNOWN")
            duration = seg.get("end", 0) - seg.get("start", 0)
            speaker_times[speaker] = speaker_times.get(speaker, 0) + duration

        # Heuristic: Therapist typically speaks 30-40%, client 60-70%
        speakers = list(speaker_times.keys())
        if len(speakers) >= 2:
            # Assume speaker with less total time is therapist
            sorted_speakers = sorted(speakers, key=lambda s: speaker_times[s])
            return {
                sorted_speakers[0]: "Therapist",
                sorted_speakers[1]: "Client"
            }

        # Default mapping
        return {"SPEAKER_00": "Therapist", "SPEAKER_01": "Client"}

    def _format_transcript(
        self,
        segments: List[Dict[str, Any]],
        speaker_roles: Dict[str, str]
    ) -> str:
        """Format transcript with role labels."""
        formatted = []
        for segment in segments:
            speaker_id = segment.get("speaker") or segment.get("speaker_id", "UNKNOWN")
            text = segment.get("text", "").strip()

            if not text:
                continue

            role = speaker_roles.get(speaker_id, speaker_id)
            formatted.append(f"{role}: {text}")

        return "\n".join(formatted)


# Convenience function
async def analyze_session_deep(
    session_id: str,
    session: Dict[str, Any],
    api_key: Optional[str] = None
) -> DeepAnalysis:
    """
    Convenience function to perform deep analysis on a session.

    Args:
        session_id: Session UUID
        session: Session data
        api_key: Optional OpenAI API key

    Returns:
        DeepAnalysis object
    """
    analyzer = DeepAnalyzer(api_key=api_key)
    return await analyzer.analyze_session(session_id, session)
