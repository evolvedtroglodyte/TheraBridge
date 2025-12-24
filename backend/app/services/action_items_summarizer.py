"""
Action Items Summarizer Service
Condenses 2 verbose action items into a single 45-character phrase.
Uses GPT-5-nano for efficient, cost-effective summarization.
"""

import os
import logging
from typing import List
from openai import AsyncOpenAI
from datetime import datetime
from pydantic import BaseModel

from app.config.model_config import get_model_name

logger = logging.getLogger(__name__)


class ActionItemsSummary(BaseModel):
    """Dataclass for action items summary result"""
    summary: str
    character_count: int
    original_items: List[str]
    summarized_at: datetime


class ActionItemsSummarizer:
    """
    Summarizes two verbose action items into a single 45-character phrase.

    Uses GPT-5-nano for cost-effective summarization while maintaining
    the core meaning of both action items.
    """

    def __init__(self):
        """Initialize the summarizer with OpenAI client"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        self.client = AsyncOpenAI(api_key=api_key)

        # Use GPT-5-nano for efficient summarization
        self.model = get_model_name("action_summary", override_model=None)
        logger.info(f"Initialized ActionItemsSummarizer with model: {self.model}")

    async def summarize_action_items(
        self,
        action_items: List[str],
        session_id: str = None
    ) -> ActionItemsSummary:
        """
        Generate a 45-character max summary from 2 action items.

        Args:
            action_items: List of 2 action item strings
            session_id: Optional session ID for logging

        Returns:
            ActionItemsSummary with condensed phrase

        Raises:
            ValueError: If action_items doesn't have exactly 2 items
        """
        if len(action_items) != 2:
            raise ValueError(f"Expected 2 action items, got {len(action_items)}")

        log_prefix = f"Session {session_id}: " if session_id else ""
        logger.info(f"📝 {log_prefix}Generating action items summary...")

        # Construct prompt
        prompt = self._build_prompt(action_items)

        try:
            # Call OpenAI API
            # Note: gpt-5-nano works with NO parameters (like mood_analyzer)
            # Adding temperature or max_completion_tokens causes empty responses
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ]
            )

            # Extract summary
            summary = response.choices[0].message.content.strip()

            # Truncate if over 45 characters (safety check)
            if len(summary) > 45:
                logger.warning(f"📝 {log_prefix}Summary exceeded 45 chars ({len(summary)}), truncating")
                summary = summary[:42] + "..."

            char_count = len(summary)

            logger.info(
                f"✅ {log_prefix}Action items summary complete: "
                f"'{summary}' ({char_count} chars)"
            )

            return ActionItemsSummary(
                summary=summary,
                character_count=char_count,
                original_items=action_items,
                summarized_at=datetime.utcnow()
            )

        except Exception as e:
            logger.error(f"❌ {log_prefix}Action items summarization failed: {str(e)}")
            raise

    def _get_system_prompt(self) -> str:
        """System prompt for GPT-5-nano summarization"""
        return """You are an expert at condensing therapy action items into ultra-brief phrases.

Your task: Combine TWO action items into ONE phrase of MAXIMUM 45 characters.

Requirements:
- Capture the essence of BOTH action items
- Use action verbs (practice, schedule, talk, write, etc.)
- Be specific enough to be meaningful
- Maximum 45 characters (strict limit)
- No punctuation at the end
- Conversational, patient-friendly tone

Examples:
Input: ["Practice TIPP skills when feeling overwhelmed", "Schedule psychiatrist appointment"]
Output: "Practice TIPP & schedule psychiatrist"

Input: ["Write down 3 daily accomplishments before bed", "Reach out to one friend this week"]
Output: "Track wins & reach out to friend"

Input: ["Use wise mind skill during family conflict", "Complete CBT thought record worksheet"]
Output: "Use wise mind & complete worksheet"

Input: ["Apply radical acceptance when stuck on ex-partner thoughts", "Practice opposite action for urge to isolate"]
Output: "Accept & practice opposite action"

Return ONLY the summary phrase, nothing else."""

    def _build_prompt(self, action_items: List[str]) -> str:
        """Build the user prompt with the two action items"""
        return f"""Condense these TWO action items into ONE phrase (max 45 characters):

1. {action_items[0]}
2. {action_items[1]}

Return only the condensed phrase."""
