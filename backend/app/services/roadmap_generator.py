"""
Roadmap Generator

Generates dynamic "Your Journey" roadmap for patient dashboard.
Updates incrementally after each session's Wave 2 analysis completes.

Supports 3 compaction strategies:
1. Full Context: All previous sessions' raw data (expensive, maximum detail)
2. Progressive Summarization: Previous roadmap + current session (cheap, compact)
3. Hierarchical: Multi-tier summaries (balanced cost/detail)

Model: GPT-5.2 (configurable)
Input: Cumulative context (~10K-80K tokens depending on strategy)
Output: Roadmap JSON (~1K tokens)
Cost: ~$0.003-0.020 per generation (varies by strategy)
"""

import json
import os
from typing import Optional, Literal
from uuid import UUID
from datetime import datetime
import openai
from app.config.model_config import get_model_name


CompactionStrategy = Literal["full", "progressive", "hierarchical"]


class RoadmapGenerator:
    """Generate patient journey roadmaps with configurable compaction strategies"""

    def __init__(self, api_key: Optional[str] = None, override_model: Optional[str] = None):
        """
        Initialize roadmap generator with OpenAI client.

        Args:
            api_key: OpenAI API key (uses env var if not provided)
            override_model: Override default model (for testing)
        """
        # Only pass api_key if explicitly provided, otherwise let OpenAI use env var
        if api_key:
            self.client = openai.OpenAI(api_key=api_key)
        else:
            self.client = openai.OpenAI()  # Uses OPENAI_API_KEY env var
        self.model = get_model_name("roadmap_generation", override_model=override_model)

        # Get and validate compaction strategy from env var
        VALID_STRATEGIES = {"full", "progressive", "hierarchical"}
        raw_strategy = os.getenv("ROADMAP_COMPACTION_STRATEGY", "hierarchical").lower()

        if raw_strategy not in VALID_STRATEGIES:
            print(f"[WARNING] Invalid ROADMAP_COMPACTION_STRATEGY '{raw_strategy}', defaulting to 'hierarchical'")
            raw_strategy = "hierarchical"

        self.strategy: CompactionStrategy = raw_strategy

    def generate_roadmap(
        self,
        patient_id: UUID,
        current_session: dict,  # Current session wave1 + wave2 data
        context: dict,  # Compacted context (structure varies by strategy)
        sessions_analyzed: int,
        total_sessions: int
    ) -> dict:
        """
        Generate roadmap using configured compaction strategy.

        Args:
            patient_id: Patient UUID
            current_session: Current session data (wave1 + wave2)
            context: Previous context (structure depends on strategy)
            sessions_analyzed: Number of sessions analyzed (for counter display)
            total_sessions: Total sessions uploaded (for counter display)

        Returns:
            Roadmap dict matching NotesGoalsCard structure:
            {
                "summary": str,
                "achievements": [str, ...],  # 5 bullets
                "currentFocus": [str, ...],  # 3 bullets
                "sections": [
                    {"title": str, "content": str},  # 5 sections
                    ...
                ]
            }
        """
        start_time = datetime.now()

        # Build prompt based on strategy
        prompt = self._build_prompt_for_strategy(
            patient_id,
            current_session,
            context,
            sessions_analyzed,
            total_sessions
        )

        # Call GPT-5.2
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )

        # Parse and validate response
        roadmap_data = json.loads(response.choices[0].message.content)
        roadmap_data = self._validate_roadmap_structure(roadmap_data)

        # Calculate generation duration
        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        # Return roadmap with metadata
        return {
            "roadmap": roadmap_data,
            "metadata": {
                "compaction_strategy": self.strategy,
                "sessions_analyzed": sessions_analyzed,
                "total_sessions": total_sessions,
                "model_used": self.model,
                "generation_timestamp": datetime.now().isoformat(),
                "generation_duration_ms": duration_ms
            }
        }

    def _get_system_prompt(self) -> str:
        """System prompt defining roadmap generation task"""
        return """You are a therapeutic journey synthesizer for mental health care.

Your task: Generate a comprehensive "Your Journey" roadmap that summarizes a patient's therapeutic progress across multiple sessions.

The roadmap structure:
{
  "summary": "2-3 sentence overview of patient's journey (where they started, progress made, current state)",
  "achievements": [
    "Achievement 1 (1 sentence)",
    "Achievement 2 (1 sentence)",
    "Achievement 3 (1 sentence)",
    "Achievement 4 (1 sentence)",
    "Achievement 5 (1 sentence)"
  ],
  "currentFocus": [
    "Focus area 1 (1 sentence)",
    "Focus area 2 (1 sentence)",
    "Focus area 3 (1 sentence)"
  ],
  "sections": [
    {
      "title": "Clinical Progress",
      "content": "2-3 sentences describing symptom changes, functioning improvements, or clinical outcomes"
    },
    {
      "title": "Therapeutic Strategies",
      "content": "2-3 sentences about techniques used, interventions applied, and their effectiveness"
    },
    {
      "title": "Identified Patterns",
      "content": "2-3 sentences about recurring themes, triggers, behavioral patterns discovered"
    },
    {
      "title": "Current Treatment Focus",
      "content": "2-3 sentences about active goals, ongoing skill development, immediate priorities"
    },
    {
      "title": "Long-term Goals",
      "content": "2-3 sentences about overarching objectives, future milestones, sustained progress targets"
    }
  ]
}

Guidelines:
- Write for the PATIENT (supportive, encouraging, accessible language)
- Focus on GROWTH and PROGRESS (even if incremental)
- Be SPECIFIC (reference techniques, emotions, situations by name)
- Maintain CLINICAL ACCURACY (don't exaggerate or misrepresent)
- Show CONTINUITY (connect current session to previous journey)
- Each achievement: 1 sentence, concrete, measurable
- Current focus: Active, actionable, forward-looking
- Section content: 2-3 sentences, cohesive narrative

Tone: Warm, professional, empowering, hopeful but realistic
"""

    def _validate_roadmap_structure(self, roadmap: dict) -> dict:
        """Validate and fix roadmap structure"""
        # Ensure required fields with defaults
        roadmap.setdefault("summary", "Your therapeutic journey is in progress.")

        # Ensure list fields are actually lists
        list_fields = ["achievements", "currentFocus", "sections"]
        for field in list_fields:
            roadmap.setdefault(field, [])
            if not isinstance(roadmap[field], list):
                roadmap[field] = []

        # Normalize list lengths with padding/truncation
        roadmap["achievements"] = self._normalize_list(
            roadmap["achievements"], 5,
            "Continued engagement in therapeutic process",
            "achievements"
        )
        roadmap["currentFocus"] = self._normalize_list(
            roadmap["currentFocus"], 3,
            "Ongoing skill development and practice",
            "focus areas"
        )

        if len(roadmap["sections"]) != 5:
            print(f"[WARNING] RoadmapGenerator: Expected 5 sections, got {len(roadmap['sections'])}")

        # Ensure all sections have title and content
        for section in roadmap["sections"]:
            section.setdefault("title", "Section")
            section.setdefault("content", "Progress is being made in this area.")

        return roadmap

    def _normalize_list(self, items: list, expected_count: int, placeholder: str, field_name: str) -> list:
        """Normalize a list to expected count by padding or truncating"""
        if len(items) < expected_count:
            print(f"[WARNING] RoadmapGenerator: Expected {expected_count} {field_name}, got {len(items)}")
            items.extend([placeholder] * (expected_count - len(items)))
        return items[:expected_count]

    def _build_prompt_for_strategy(
        self,
        patient_id: UUID,
        current_session: dict,
        context: dict,
        sessions_analyzed: int,
        total_sessions: int
    ) -> str:
        """Build prompt based on selected compaction strategy"""
        prompt_builders = {
            "full": self._build_full_context_prompt,
            "progressive": self._build_progressive_prompt,
            "hierarchical": self._build_hierarchical_prompt,
        }

        builder = prompt_builders.get(self.strategy)
        if not builder:
            raise ValueError(f"Unknown compaction strategy: {self.strategy}")

        return builder(patient_id, current_session, context, sessions_analyzed, total_sessions)

    def _build_full_context_prompt(
        self,
        patient_id: UUID,
        current_session: dict,
        context: dict,
        sessions_analyzed: int,
        total_sessions: int
    ) -> str:
        """
        Strategy 1: Full Context (No Compaction)

        Passes ALL previous sessions' raw Wave 1 + Wave 2 data to LLM.

        Context structure:
        {
            "previous_context": {
                # Nested structure from Wave 2
                "previous_context": {...},
                "session_N_wave1": {...},
                "session_N_wave2": {...}
            },
            "current_session": {
                "wave1": {...},
                "wave2": {...}
            }
        }

        Token count: ~50K-80K by Session 10
        Cost: ~$0.014-0.020 per generation
        """
        prompt = f"""Patient ID: {patient_id}
Sessions Analyzed: {sessions_analyzed} out of {total_sessions} uploaded

COMPACTION STRATEGY: Full Context
You have access to ALL previous sessions' complete Wave 1 and Wave 2 analysis data.

CUMULATIVE CONTEXT (All Previous Sessions):
{json.dumps(context, indent=2)}

CURRENT SESSION DATA:
{json.dumps(current_session, indent=2)}

Generate a comprehensive "Your Journey" roadmap that synthesizes insights across all {sessions_analyzed} sessions.
The roadmap should reflect the patient's full therapeutic journey from Session 1 to Session {sessions_analyzed}.

Focus on:
- Overall trajectory (where they started → where they are now)
- Key milestones and breakthroughs across all sessions
- Cumulative skill development and progress
- Emerging patterns visible only across multiple sessions
- Current state in context of full journey

Return your response as a JSON object with the roadmap structure.
"""
        return prompt

    def _build_progressive_prompt(
        self,
        patient_id: UUID,
        current_session: dict,
        context: dict,
        sessions_analyzed: int,
        total_sessions: int
    ) -> str:
        """
        Strategy 2: Progressive Summarization

        Passes ONLY previous roadmap + current session data.
        Previous roadmap already contains synthesized insights from Sessions 1 to N-1.

        Context structure:
        {
            "previous_roadmap": {
                "summary": "...",
                "achievements": [...],
                "currentFocus": [...],
                "sections": [...]
            },  # Only exists if sessions_analyzed > 1
            "current_session": {
                "wave1": {...},
                "wave2": {...}
            }
        }

        Token count: ~7K-10K (constant)
        Cost: ~$0.0025 per generation
        """
        # Extract previous roadmap if it exists
        previous_roadmap = context.get("previous_roadmap")

        if previous_roadmap:
            # Session 2+: Build on previous roadmap
            prompt = f"""Patient ID: {patient_id}
Sessions Analyzed: {sessions_analyzed} out of {total_sessions} uploaded

COMPACTION STRATEGY: Progressive Summarization
You are updating an existing roadmap with insights from the latest session.

PREVIOUS ROADMAP (Sessions 1-{sessions_analyzed - 1}):
{json.dumps(previous_roadmap, indent=2)}

CURRENT SESSION DATA (Session {sessions_analyzed}):
{json.dumps(current_session, indent=2)}

Generate an UPDATED "Your Journey" roadmap that:
1. Builds on the previous roadmap's narrative
2. Integrates new insights from Session {sessions_analyzed}
3. Updates achievements (add new ones, keep most significant from before)
4. Updates current focus (shift based on latest session)
5. Updates all 5 sections to reflect cumulative + current progress

Important:
- Maintain narrative continuity (don't contradict previous roadmap)
- Show progression (how Session {sessions_analyzed} builds on earlier work)
- Keep the most important historical insights (don't lose key milestones)
- Emphasize recent progress (Session {sessions_analyzed} should be prominent)

Return your response as a JSON object with the roadmap structure.
"""
        else:
            # Session 1: No previous roadmap
            prompt = f"""Patient ID: {patient_id}
Sessions Analyzed: {sessions_analyzed} out of {total_sessions} uploaded

COMPACTION STRATEGY: Progressive Summarization
This is the FIRST roadmap generation for this patient.

CURRENT SESSION DATA (Session 1):
{json.dumps(current_session, indent=2)}

Generate the INITIAL "Your Journey" roadmap based on Session 1.
This roadmap will be progressively updated as more sessions are analyzed.

Focus on:
- Initial presentation and presenting concerns
- First steps taken in therapy
- Early insights and rapport building
- Foundation for future progress

Return your response as a JSON object with the roadmap structure.
"""

        return prompt

    def _build_hierarchical_prompt(
        self,
        patient_id: UUID,
        current_session: dict,
        context: dict,
        sessions_analyzed: int,
        total_sessions: int
    ) -> str:
        """
        Strategy 3: Hierarchical Summarization

        Uses multi-tier summaries that compact at different granularities:
        - Tier 1: Per-session insights (3-5 bullets) - Recent sessions
        - Tier 2: Every 5 sessions → compacted paragraph - Mid-range history
        - Tier 3: Every 10 sessions → journey arc narrative - Long-term trajectory

        Context structure:
        {
            "tier3_summary": "Sessions 1-10 arc narrative",  # Only if sessions_analyzed > 10
            "tier2_summaries": {
                "sessions_11_15": "Paragraph summary",
                "sessions_16_20": "Paragraph summary"
            },  # Only if sessions_analyzed > 10
            "tier1_summaries": {
                "session_N": ["insight 1", "insight 2", ...],  # Recent sessions
                "session_N+1": [...]
            },
            "previous_roadmap": {...},  # Previous roadmap
            "current_session": {
                "wave1": {...},
                "wave2": {...},
                "insights": [...]  # Generated by SessionInsightsSummarizer
            }
        }

        Token count: ~10K-12K
        Cost: ~$0.003-0.004 per generation
        """
        # Determine tier structure based on sessions_analyzed
        tier3_threshold = 10
        tier2_threshold = 5

        # Build tier context
        tier3_summary = context.get("tier3_summary")
        tier2_summaries = context.get("tier2_summaries", {})
        tier1_summaries = context.get("tier1_summaries", {})
        previous_roadmap = context.get("previous_roadmap")

        # Build prompt with appropriate tier context
        prompt = f"""Patient ID: {patient_id}
Sessions Analyzed: {sessions_analyzed} out of {total_sessions} uploaded

COMPACTION STRATEGY: Hierarchical Summarization
Multi-tier context provides both high-level trajectory and recent session details.
"""

        # Add Tier 3 if exists (Sessions 1-10+ arc)
        if tier3_summary:
            prompt += f"""
TIER 3 - LONG-TERM TRAJECTORY (Sessions 1-{tier3_threshold}):
{tier3_summary}

"""

        # Add Tier 2 summaries if exist (5-session chunks)
        if tier2_summaries:
            prompt += "TIER 2 - MID-RANGE HISTORY (5-session summaries):\n"
            for session_range, summary in tier2_summaries.items():
                prompt += f"\n{session_range}: {summary}\n"
            prompt += "\n"

        # Add Tier 1 summaries (recent sessions)
        if tier1_summaries:
            prompt += "TIER 1 - RECENT SESSIONS (detailed insights):\n"
            for session_key, insights in tier1_summaries.items():
                prompt += f"\n{session_key}:\n"
                for insight in insights:
                    prompt += f"  - {insight}\n"
            prompt += "\n"

        # Add previous roadmap
        if previous_roadmap:
            prompt += f"""PREVIOUS ROADMAP (Sessions 1-{sessions_analyzed - 1}):
{json.dumps(previous_roadmap, indent=2)}

"""

        # Add current session
        prompt += f"""CURRENT SESSION DATA (Session {sessions_analyzed}):
{json.dumps(current_session, indent=2)}

Generate an UPDATED "Your Journey" roadmap that synthesizes:
1. Long-term trajectory (Tier 3) - Overall journey arc
2. Mid-range patterns (Tier 2) - Themes across recent sessions
3. Recent progress (Tier 1) - Specific recent insights
4. Latest session (Current) - New developments

The roadmap should reflect BOTH the big picture AND recent details.
Show how Session {sessions_analyzed} fits into the larger journey narrative.

Return your response as a JSON object with the roadmap structure.
"""

        return prompt

    @staticmethod
    def compact_tier1_to_tier2(tier1_summaries: dict) -> str:
        """
        Compact Tier 1 insights (5 sessions worth) into Tier 2 paragraph summary.

        Called every 5 sessions to prevent Tier 1 from growing too large.

        Args:
            tier1_summaries: Dict of {session_id: [insights]} for 5 sessions

        Returns:
            Paragraph summary (2-3 sentences) synthesizing 5 sessions

        Example:
            Input: {
                "session_01": ["Anxiety trigger identified", "Breathing practiced"],
                "session_02": ["Breakthrough with avoidance", ...],
                ...
            }
            Output: "Patient made significant progress in Sessions 1-5, identifying work stress as primary anxiety trigger and practicing breathing techniques independently. Breakthrough moment occurred in Session 2 when connecting avoidance patterns to childhood experiences. By Session 5, patient demonstrated consistent skill application."
        """
        # This will be called by the orchestration script, not the generator itself
        # Placeholder for now - actual implementation in orchestration (Phase 5)
        pass

    @staticmethod
    def compact_tier2_to_tier3(tier2_summaries: list[str]) -> str:
        """
        Compact Tier 2 summaries (10 sessions worth) into Tier 3 journey arc.

        Called every 10 sessions to create high-level trajectory narrative.

        Args:
            tier2_summaries: List of 2 Tier 2 paragraph summaries (Sessions 1-5, 6-10)

        Returns:
            Journey arc narrative (3-4 sentences) synthesizing 10 sessions

        Example:
            Output: "Patient's journey began with acute anxiety symptoms and work-related stress (Sessions 1-5), progressing through skill acquisition and breakthrough insights about avoidance patterns. Mid-journey (Sessions 6-10) focused on applying learned techniques in real-world situations, with increasing confidence and reduced symptom severity. Overall trajectory shows steady improvement in emotional regulation and social functioning."
        """
        # Placeholder - implemented in orchestration script (Phase 5)
        pass
