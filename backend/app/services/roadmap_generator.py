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
        self.client = openai.OpenAI(api_key=api_key)
        self.model = get_model_name("roadmap_generation", override_model=override_model)

        # Get compaction strategy from env var
        self.strategy: CompactionStrategy = os.getenv(
            "ROADMAP_COMPACTION_STRATEGY",
            "hierarchical"  # Default to balanced approach
        ).lower()

        # Validate strategy
        if self.strategy not in ["full", "progressive", "hierarchical"]:
            print(f"[WARNING] Invalid ROADMAP_COMPACTION_STRATEGY '{self.strategy}', defaulting to 'hierarchical'")
            self.strategy = "hierarchical"

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
        # Ensure required fields exist
        if "summary" not in roadmap:
            roadmap["summary"] = "Your therapeutic journey is in progress."

        if "achievements" not in roadmap or not isinstance(roadmap["achievements"], list):
            roadmap["achievements"] = []

        if "currentFocus" not in roadmap or not isinstance(roadmap["currentFocus"], list):
            roadmap["currentFocus"] = []

        if "sections" not in roadmap or not isinstance(roadmap["sections"], list):
            roadmap["sections"] = []

        # Validate achievements count (should be 5)
        if len(roadmap["achievements"]) < 5:
            print(f"[WARNING] RoadmapGenerator: Expected 5 achievements, got {len(roadmap['achievements'])}")
            # Pad with placeholder if needed
            while len(roadmap["achievements"]) < 5:
                roadmap["achievements"].append("Continued engagement in therapeutic process")
        elif len(roadmap["achievements"]) > 5:
            roadmap["achievements"] = roadmap["achievements"][:5]

        # Validate currentFocus count (should be 3)
        if len(roadmap["currentFocus"]) < 3:
            print(f"[WARNING] RoadmapGenerator: Expected 3 focus areas, got {len(roadmap['currentFocus'])}")
            while len(roadmap["currentFocus"]) < 3:
                roadmap["currentFocus"].append("Ongoing skill development and practice")
        elif len(roadmap["currentFocus"]) > 3:
            roadmap["currentFocus"] = roadmap["currentFocus"][:3]

        # Validate sections (should be 5 with correct titles)
        expected_sections = [
            "Clinical Progress",
            "Therapeutic Strategies",
            "Identified Patterns",
            "Current Treatment Focus",
            "Long-term Goals"
        ]

        if len(roadmap["sections"]) != 5:
            print(f"[WARNING] RoadmapGenerator: Expected 5 sections, got {len(roadmap['sections'])}")

        # Ensure all sections have title and content
        for section in roadmap["sections"]:
            if "title" not in section:
                section["title"] = "Section"
            if "content" not in section:
                section["content"] = "Progress is being made in this area."

        return roadmap

    # Strategy-specific methods will be added in Phase 2
    def _build_prompt_for_strategy(self, *args, **kwargs) -> str:
        """Build prompt based on selected compaction strategy (implemented in Phase 2)"""
        raise NotImplementedError("Compaction strategies implemented in Phase 2")
