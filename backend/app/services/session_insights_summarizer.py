"""
Session Insights Summarizer

Extracts 3-5 key therapeutic insights from a session's deep_analysis JSONB.
Used for hierarchical context compaction in roadmap generation.

Model: GPT-5.2 (configurable)
Input: deep_analysis JSONB (~1.5K tokens)
Output: List of 3-5 insight strings (~150 tokens)
Cost: ~$0.0006 per session
"""

import json
import time
from typing import Optional, Tuple, Dict, List, Any
from uuid import UUID

from app.services.base_ai_generator import SyncAIGenerator
from app.config.model_config import track_generation_cost, GenerationCost


class SessionInsightsSummarizer(SyncAIGenerator):
    """
    Extract key therapeutic insights from session deep_analysis.

    Inherits from SyncAIGenerator for consistent initialization and cost tracking.
    """

    def __init__(self, api_key: Optional[str] = None, override_model: Optional[str] = None):
        """
        Initialize summarizer with OpenAI client.

        Args:
            api_key: OpenAI API key (uses env var if not provided)
            override_model: Override default model (for testing)
        """
        super().__init__(api_key=api_key, override_model=override_model)

    def get_task_name(self) -> str:
        """Return the task name for model selection and cost tracking."""
        return "session_insights"

    def build_messages(self, context: Dict[str, Any]) -> List[Dict[str, str]]:
        """Build messages for the API call. Required by base class but not used directly."""
        return [
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user", "content": context.get("prompt", "")}
        ]

    def generate_insights(
        self,
        session_id: UUID,
        deep_analysis: dict,
        confidence_score: float
    ) -> Tuple[list[str], Optional[GenerationCost]]:
        """
        Generate 3-5 key therapeutic insights from deep_analysis.

        Args:
            session_id: Session UUID
            deep_analysis: Complete deep_analysis JSONB dict
            confidence_score: Analysis confidence (0.0-1.0)

        Returns:
            Tuple of (List of 3-5 insight strings, GenerationCost info)

        Example output:
            ([
                "Patient identified work stress as primary anxiety trigger during guided reflection",
                "Successfully practiced 4-7-8 breathing technique independently for first time",
                "Breakthrough: Connected current avoidance patterns to childhood experiences"
            ], cost_info)
        """
        prompt = self._build_prompt(session_id, deep_analysis, confidence_score)

        # Call GPT-5.2
        start_time = time.time()
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )

        # Track cost and timing
        cost_info = track_generation_cost(
            response=response,
            task="session_insights",
            model=self.model,
            start_time=start_time,
            session_id=str(session_id)
        )

        # Parse response
        result = json.loads(response.choices[0].message.content)
        insights = result.get("insights", [])

        # Validate output
        if not isinstance(insights, list) or len(insights) < 3 or len(insights) > 5:
            print(f"[WARNING] SessionInsightsSummarizer: Expected 3-5 insights, got {len(insights)}")

        return insights, cost_info

    def _get_system_prompt(self) -> str:
        """System prompt defining task and output format"""
        return """You are a clinical insights extractor for therapy session analysis.

Your task: Extract 3-5 key therapeutic insights from a session's deep analysis.

Focus on the MOST SIGNIFICANT elements:
- Major progress or regression in symptoms/functioning
- New coping skills learned or existing skills practiced effectively
- Breakthrough moments, realizations, or cognitive shifts
- Important patterns, triggers, or behavioral dynamics identified
- Critical changes in therapeutic relationship or engagement

Output format:
{
  "insights": [
    "Insight 1 (1-2 sentences)",
    "Insight 2 (1-2 sentences)",
    "Insight 3 (1-2 sentences)",
    "Insight 4 (1-2 sentences, optional)",
    "Insight 5 (1-2 sentences, optional)"
  ]
}

Guidelines:
- Each insight: 1-2 sentences maximum (30-60 words)
- Be specific and concrete (reference techniques, emotions, situations)
- Prioritize actionable insights over general observations
- Maintain clinical accuracy and therapeutic tone
- Focus on what's NEW or CHANGED in this session
"""

    def _build_prompt(
        self,
        session_id: UUID,
        deep_analysis: dict,
        confidence_score: float
    ) -> str:
        """Build user prompt with deep_analysis data"""
        return f"""Session ID: {session_id}
Confidence Score: {confidence_score:.2f}

Deep Analysis Data:
{json.dumps(deep_analysis, indent=2)}

Extract 3-5 key therapeutic insights from this session's deep analysis.
Focus on the most significant progress, breakthroughs, skills, and patterns.

Return your response as a JSON object with an "insights" array.
"""
