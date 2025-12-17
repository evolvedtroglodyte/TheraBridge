"""
Mock note extraction service for testing without calling OpenAI API
"""
import asyncio
from typing import Optional, List
from app.models.schemas import (
    ExtractedNotes, Strategy, Trigger, ActionItem,
    SignificantQuote, RiskFlag, MoodLevel, StrategyStatus,
    TranscriptSegment
)


class MockNoteExtractionService:
    """Mock extraction service that returns realistic test data"""

    def __init__(self, should_fail: bool = False):
        """
        Initialize mock service.

        Args:
            should_fail: If True, extraction will raise an exception
        """
        self.should_fail = should_fail

    async def extract_notes_from_transcript(
        self,
        transcript: str,
        segments: Optional[List[TranscriptSegment]] = None,
        timeout: Optional[float] = None
    ) -> ExtractedNotes:
        """
        Mock extraction that returns structured test data.

        Args:
            transcript: Transcript text (not actually processed)
            segments: Transcript segments (not actually used)
            timeout: Timeout value (ignored in mock)

        Returns:
            ExtractedNotes: Mock extracted notes

        Raises:
            Exception: If should_fail is True
        """
        # Simulate processing delay
        await asyncio.sleep(0.1)

        if self.should_fail:
            raise Exception("Note extraction failed: API error")

        # Return realistic mock data
        return ExtractedNotes(
            key_topics=[
                "Work-related anxiety",
                "Team meeting stress",
                "Coping strategies",
                "Box breathing technique"
            ],
            topic_summary=(
                "Client discussed feelings of anxiety related to work, "
                "particularly during team meetings where they feel judged. "
                "We explored breathing techniques as a coping strategy."
            ),
            strategies=[
                Strategy(
                    name="Box breathing",
                    category="Breathing technique",
                    status=StrategyStatus.practiced,
                    context="Practiced during session to manage meeting anxiety"
                )
            ],
            emotional_themes=["anxiety", "self-doubt", "stress"],
            triggers=[
                Trigger(
                    trigger="Team meetings",
                    context="Feels judged when presenting ideas",
                    severity="moderate"
                )
            ],
            action_items=[
                ActionItem(
                    task="Practice box breathing before next team meeting",
                    category="behavioral",
                    details="Use 4-4-4-4 pattern to calm nerves"
                )
            ],
            significant_quotes=[
                SignificantQuote(
                    quote="I feel like everyone is judging my ideas.",
                    context="Reveals core fear driving anxiety",
                    timestamp_start=10.5
                )
            ],
            session_mood=MoodLevel.low,
            mood_trajectory="stable",
            follow_up_topics=["Progress with breathing exercises", "Team dynamics"],
            unresolved_concerns=["Root cause of feeling judged"],
            risk_flags=[],
            therapist_notes=(
                "Client presents with work-related anxiety, primarily triggered by team meetings. "
                "Reports feeling judged when presenting ideas, leading to significant distress. "
                "Introduced box breathing as a grounding technique. Client was receptive but "
                "expressed skepticism about effectiveness. Will monitor progress and explore "
                "additional CBT techniques if needed. No immediate risk concerns identified."
            ),
            patient_summary=(
                "You shared that work has been stressful lately, especially during team meetings "
                "where you feel anxious about being judged. We practiced box breathing together "
                "as a way to help manage those feelings. Your homework is to try this technique "
                "before your next meeting. Remember, it's okay to feel nervous, and with practice, "
                "these strategies can really help."
            )
        )


class MockNoteExtractionServiceWithRisk:
    """Mock extraction service that returns data with risk flags"""

    async def extract_notes_from_transcript(
        self,
        transcript: str,
        segments: Optional[List[TranscriptSegment]] = None,
        timeout: Optional[float] = None
    ) -> ExtractedNotes:
        """
        Mock extraction that returns data with risk flags.

        Args:
            transcript: Transcript text (not actually processed)
            segments: Transcript segments (not actually used)
            timeout: Timeout value (ignored in mock)

        Returns:
            ExtractedNotes: Mock extracted notes with risk flags
        """
        await asyncio.sleep(0.1)

        return ExtractedNotes(
            key_topics=["Depression", "Suicidal thoughts", "Safety planning"],
            topic_summary="Client disclosed suicidal ideation. Safety assessment conducted.",
            strategies=[],
            emotional_themes=["hopelessness", "despair"],
            triggers=[],
            action_items=[
                ActionItem(
                    task="Call crisis hotline if feelings worsen",
                    category="safety",
                    details="National Suicide Prevention Lifeline: 988"
                )
            ],
            significant_quotes=[
                SignificantQuote(
                    quote="Sometimes I think everyone would be better off without me.",
                    context="Expressed suicidal ideation",
                    timestamp_start=120.0
                )
            ],
            session_mood=MoodLevel.very_low,
            mood_trajectory="declining",
            follow_up_topics=["Safety check-in", "Crisis resources"],
            unresolved_concerns=["Ongoing suicidal thoughts"],
            risk_flags=[
                RiskFlag(
                    type="suicidal_ideation",
                    evidence="Client stated 'everyone would be better off without me'",
                    severity="high"
                )
            ],
            therapist_notes=(
                "URGENT: Client disclosed suicidal ideation during session. Safety assessment "
                "completed. Client denies immediate plan or intent but reports passive thoughts. "
                "Provided crisis resources and established safety plan. Recommend follow-up "
                "within 48 hours. Client agreed to call crisis line if feelings escalate."
            ),
            patient_summary=(
                "Thank you for sharing your difficult feelings with me today. I want you to know "
                "that what you're experiencing is serious, and I'm here to support you. Please "
                "remember the safety plan we discussed and don't hesitate to reach out for help."
            )
        )


def get_mock_extraction_service(should_fail: bool = False):
    """
    Factory function for mock extraction service.

    Args:
        should_fail: If True, service will fail on extraction

    Returns:
        MockNoteExtractionService instance
    """
    return MockNoteExtractionService(should_fail=should_fail)
