"""
Analysis Orchestrator Service

Manages multi-wave AI analysis pipeline with dependency resolution and race condition handling.

Wave 1 (Parallel):
  - Mood Analysis
  - Topic Extraction
  - Breakthrough Detection

Wave 2 (Sequential, requires Wave 1):
  - Deep Clinical Analysis (synthesizes Wave 1 + patient history)

Features:
- Automatic dependency management
- Retry logic with exponential backoff
- Processing status tracking
- Graceful error handling
"""

import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

from app.services.mood_analyzer import MoodAnalyzer
from app.services.topic_extractor import TopicExtractor
from app.services.breakthrough_detector import BreakthroughDetector
from app.services.deep_analyzer import DeepAnalyzer
from app.services.prose_generator import ProseGenerator
from app.services.action_items_summarizer import ActionItemsSummarizer, ActionItemsSummary
from app.database import get_db
from supabase import Client

logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    """Result from a single analysis wave"""
    wave: str
    status: str  # 'completed', 'failed'
    started_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str] = None
    retry_count: int = 0
    processing_duration_ms: Optional[int] = None


@dataclass
class PipelineStatus:
    """Overall analysis pipeline status"""
    session_id: str
    analysis_status: str
    mood_complete: bool
    topics_complete: bool
    breakthrough_complete: bool
    wave1_complete: bool
    deep_complete: bool
    wave1_completed_at: Optional[datetime]
    deep_analyzed_at: Optional[datetime]


class AnalysisOrchestrator:
    """
    Coordinates multi-wave AI analysis pipeline with proper dependency management.

    Ensures:
    1. Wave 1 analyses run in parallel (no dependencies)
    2. Wave 2 only starts after ALL Wave 1 completes
    3. Proper error handling and retry logic
    4. Status tracking in database
    """

    MAX_RETRIES = 3
    BACKOFF_MULTIPLIER = 2  # Exponential backoff: 2s, 4s, 8s
    TIMEOUT_SECONDS = 300  # 5 minutes max per wave

    def __init__(self, db: Optional[Client] = None):
        """
        Initialize the orchestrator.

        Args:
            db: Supabase client. If None, uses default from get_db()
        """
        self.db = db or next(get_db())
        self.mood_analyzer = MoodAnalyzer()
        self.topic_extractor = TopicExtractor()
        self.breakthrough_detector = BreakthroughDetector()
        self.deep_analyzer = DeepAnalyzer()
        self.action_items_summarizer = ActionItemsSummarizer()

    async def process_session_full_pipeline(
        self,
        session_id: str,
        force: bool = False
    ) -> PipelineStatus:
        """
        Run complete analysis pipeline: Wave 1 (parallel) → Wave 2 (deep analysis)

        Args:
            session_id: Session UUID
            force: Force re-analysis even if already completed

        Returns:
            PipelineStatus with final state

        Raises:
            Exception: If critical failure occurs after all retries
        """
        logger.info(f"🚀 Starting full analysis pipeline for session {session_id}")

        # Update status to wave1_running
        await self._update_session_status(session_id, "wave1_running")

        try:
            # WAVE 1: Run parallel analyses
            wave1_results = await self._run_wave1(session_id, force)

            # Check if all Wave 1 completed successfully
            if not all(r.status == 'completed' for r in wave1_results):
                failed_waves = [r.wave for r in wave1_results if r.status == 'failed']
                logger.error(f"❌ Wave 1 incomplete for session {session_id}. Failed: {failed_waves}")
                await self._update_session_status(session_id, "failed")
                raise Exception(f"Wave 1 failed for waves: {failed_waves}")

            # Mark Wave 1 as complete
            await self._mark_wave1_complete(session_id)
            logger.info(f"✅ Wave 1 complete for session {session_id}")

            # WAVE 2: Run deep analysis
            await self._update_session_status(session_id, "wave2_running")
            wave2_result = await self._run_wave2(session_id, force)

            if wave2_result.status == 'completed':
                await self._update_session_status(session_id, "complete")
                logger.info(f"✅ Full pipeline complete for session {session_id}")
            else:
                await self._update_session_status(session_id, "failed")
                logger.error(f"❌ Wave 2 failed for session {session_id}: {wave2_result.error_message}")
                raise Exception(f"Wave 2 failed: {wave2_result.error_message}")

            # Get final status
            return await self.get_pipeline_status(session_id)

        except Exception as e:
            logger.error(f"Pipeline failed for session {session_id}: {e}")
            await self._update_session_status(session_id, "failed")
            raise

    async def _run_wave1(
        self,
        session_id: str,
        force: bool = False
    ) -> List[AnalysisResult]:
        """
        Run Wave 1 analyses in parallel (mood, topics, breakthrough) + action summary (sequential)

        Args:
            session_id: Session UUID
            force: Force re-analysis

        Returns:
            List of AnalysisResult for each wave
        """
        logger.info(f"📊 Running Wave 1 (parallel) for session {session_id}")

        # Run mood, topics, breakthrough in parallel (unchanged)
        results = await asyncio.gather(
            self._run_with_retry(session_id, "mood", self._analyze_mood, force),
            self._run_with_retry(session_id, "topics", self._extract_topics, force),
            self._run_with_retry(session_id, "breakthrough", self._detect_breakthrough, force),
            return_exceptions=True  # Don't fail entire batch if one fails
        )

        # Convert exceptions to failed results
        processed_results = []
        wave_names = ["mood", "topics", "breakthrough"]

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(AnalysisResult(
                    wave=wave_names[i],
                    status="failed",
                    started_at=datetime.utcnow(),
                    completed_at=None,
                    error_message=str(result),
                    retry_count=self.MAX_RETRIES
                ))
            else:
                processed_results.append(result)

        # Check if core Wave 1 analyses succeeded
        logger.info(f"✅ Wave 1 core analyses complete for session {session_id}")

        # Run action items summarization SEQUENTIALLY (requires topic extraction to be complete)
        try:
            await self._run_with_retry(
                session_id,
                "action_summary",
                self._summarize_action_items,
                force
            )
        except Exception as e:
            # Don't fail Wave 1 if summarization fails (non-critical)
            logger.error(
                f"⚠️  Action items summarization failed for session {session_id}: {str(e)}. "
                f"Wave 1 will continue without summary."
            )

        logger.info(f"✅ Wave 1 complete (with summary) for session {session_id}")

        return processed_results

    async def _run_wave2(
        self,
        session_id: str,
        force: bool = False
    ) -> AnalysisResult:
        """
        Run Wave 2 (deep analysis) - requires Wave 1 to be complete

        Args:
            session_id: Session UUID
            force: Force re-analysis

        Returns:
            AnalysisResult for deep analysis wave
        """
        logger.info(f"🧠 Running Wave 2 (deep analysis) for session {session_id}")

        # Verify Wave 1 is complete
        if not await self._is_wave1_complete(session_id):
            raise Exception("Cannot run Wave 2: Wave 1 not complete")

        return await self._run_with_retry(session_id, "deep", self._analyze_deep, force)

    async def _run_with_retry(
        self,
        session_id: str,
        wave: str,
        analysis_func,
        force: bool = False
    ) -> AnalysisResult:
        """
        Run analysis with retry logic and exponential backoff

        Args:
            session_id: Session UUID
            wave: Wave name ('mood', 'topics', 'breakthrough', 'deep')
            analysis_func: Async function to run
            force: Force re-analysis

        Returns:
            AnalysisResult with status and timing
        """
        for attempt in range(self.MAX_RETRIES):
            started_at = datetime.utcnow()

            # Log start
            await self._log_analysis_start(session_id, wave, attempt)

            try:
                # Run analysis with timeout
                await asyncio.wait_for(
                    analysis_func(session_id, force),
                    timeout=self.TIMEOUT_SECONDS
                )

                # Success
                completed_at = datetime.utcnow()
                duration_ms = int((completed_at - started_at).total_seconds() * 1000)

                await self._log_analysis_complete(session_id, wave, duration_ms)

                return AnalysisResult(
                    wave=wave,
                    status="completed",
                    started_at=started_at,
                    completed_at=completed_at,
                    retry_count=attempt,
                    processing_duration_ms=duration_ms
                )

            except asyncio.TimeoutError as e:
                error_msg = f"Timeout after {self.TIMEOUT_SECONDS}s"
                logger.warning(f"⏱️ {wave} analysis timeout (attempt {attempt + 1}/{self.MAX_RETRIES}): {error_msg}")
                await self._log_analysis_failure(session_id, wave, error_msg, attempt)

                if attempt < self.MAX_RETRIES - 1:
                    await asyncio.sleep(self.BACKOFF_MULTIPLIER ** attempt)
                else:
                    return AnalysisResult(
                        wave=wave,
                        status="failed",
                        started_at=started_at,
                        completed_at=None,
                        error_message=error_msg,
                        retry_count=attempt + 1
                    )

            except Exception as e:
                error_msg = str(e)
                logger.warning(f"⚠️ {wave} analysis failed (attempt {attempt + 1}/{self.MAX_RETRIES}): {error_msg}")
                await self._log_analysis_failure(session_id, wave, error_msg, attempt)

                if attempt < self.MAX_RETRIES - 1:
                    await asyncio.sleep(self.BACKOFF_MULTIPLIER ** attempt)
                else:
                    return AnalysisResult(
                        wave=wave,
                        status="failed",
                        started_at=started_at,
                        completed_at=None,
                        error_message=error_msg,
                        retry_count=attempt + 1
                    )

    # =============================================================================
    # Individual Wave Functions
    # =============================================================================

    async def _analyze_mood(self, session_id: str, force: bool = False):
        """Run mood analysis for a session"""
        # Get session
        session = await self._get_session(session_id)

        # Skip if already analyzed and not forcing
        if session.get("mood_analyzed_at") and not force:
            logger.info(f"↩️ Mood already analyzed for session {session_id}, skipping")
            return

        # Run analysis
        analysis = self.mood_analyzer.analyze_session_mood(
            session_id=session_id,
            segments=session["transcript"],
            patient_speaker_id="SPEAKER_01"
        )

        # Update session
        self.db.table("therapy_sessions").update({
            "mood_score": analysis.mood_score,
            "mood_confidence": analysis.confidence,
            "mood_rationale": analysis.rationale,
            "mood_indicators": analysis.key_indicators,
            "emotional_tone": analysis.emotional_tone,
            "mood_analyzed_at": datetime.utcnow().isoformat(),
        }).eq("id", session_id).execute()

    async def _extract_topics(self, session_id: str, force: bool = False):
        """Run topic extraction for a session"""
        # Get session
        session = await self._get_session(session_id)

        # Skip if already extracted and not forcing
        if session.get("topics_extracted_at") and not force:
            logger.info(f"↩️ Topics already extracted for session {session_id}, skipping")
            return

        # Run extraction
        metadata = self.topic_extractor.extract_metadata(
            session_id=session_id,
            segments=session["transcript"]
        )

        # Update session
        self.db.table("therapy_sessions").update({
            "topics": metadata.topics,
            "action_items": metadata.action_items,
            "technique": metadata.technique,
            "summary": metadata.summary,
            "extraction_confidence": metadata.confidence,
            "raw_meta_summary": metadata.raw_meta_summary,
            "topics_extracted_at": datetime.utcnow().isoformat(),
        }).eq("id", session_id).execute()

    async def _detect_breakthrough(self, session_id: str, force: bool = False):
        """Run breakthrough detection for a session"""
        # Get session
        session = await self._get_session(session_id)

        # Skip if already analyzed and not forcing
        if session.get("breakthrough_analyzed_at") and not force:
            logger.info(f"↩️ Breakthrough already analyzed for session {session_id}, skipping")
            return

        # Run detection
        analysis = self.breakthrough_detector.analyze_session(
            transcript=session["transcript"],
            session_metadata={"session_id": session_id}
        )

        # Prepare breakthrough data
        primary_breakthrough = None
        breakthrough_label = None  # NEW

        if analysis.primary_breakthrough:
            bt = analysis.primary_breakthrough
            primary_breakthrough = {
                "type": bt.breakthrough_type,
                "description": bt.description,
                "label": bt.label,  # NEW: Include label in JSONB
                "evidence": bt.evidence,
                "confidence": float(bt.confidence_score),
                "timestamp_start": float(bt.timestamp_start),
                "timestamp_end": float(bt.timestamp_end),
            }
            breakthrough_label = bt.label  # NEW: Store as separate column for easy querying

        # Update session (now includes breakthrough_label column)
        self.db.table("therapy_sessions").update({
            "has_breakthrough": analysis.has_breakthrough,
            "breakthrough_data": primary_breakthrough,
            "breakthrough_label": breakthrough_label,  # NEW
            "breakthrough_analyzed_at": datetime.utcnow().isoformat(),
        }).eq("id", session_id).execute()

        # No longer storing in breakthrough_history table
        # (we're only keeping 1 breakthrough per session now)

    async def _summarize_action_items(self, session_id: str, force: bool = False):
        """
        Generate 45-character summary of action items (runs after topic extraction).

        This runs SEQUENTIALLY after topic extraction to ensure verbose action items
        are not modified by including summarization in the same LLM call.
        """
        session = await self._get_session(session_id)

        # Skip if already summarized
        if session.get("action_items_summary") and not force:
            logger.info(f"↩️  Action items already summarized for session {session_id}, skipping")
            return

        # Skip if no action items yet (topic extraction not complete)
        if not session.get("action_items") or len(session.get("action_items", [])) < 2:
            logger.warning(
                f"⚠️  Cannot summarize action items for session {session_id}: "
                f"Need 2 action items, found {len(session.get('action_items', []))}"
            )
            return

        logger.info(f"📝 Generating action items summary for session {session_id}...")

        # Run summarization
        summary_result = await self.action_items_summarizer.summarize_action_items(
            action_items=session["action_items"][:2],  # Use first 2 items
            session_id=session_id
        )

        # Update session with summary
        self.db.table("therapy_sessions").update({
            "action_items_summary": summary_result.summary,
            "updated_at": "now()",
        }).eq("id", session_id).execute()

        logger.info(
            f"✅ Action items summary stored for session {session_id}: "
            f"'{summary_result.summary}' ({summary_result.character_count} chars)"
        )

    async def _analyze_deep(self, session_id: str, force: bool = False):
        """Run deep clinical analysis for a session"""
        # Get session
        session = await self._get_session(session_id)

        # Skip if already analyzed and not forcing
        if session.get("deep_analyzed_at") and not force:
            logger.info(f"↩️ Deep analysis already completed for session {session_id}, skipping")
            return

        # Verify Wave 1 is complete
        if not await self._is_wave1_complete(session_id):
            raise Exception("Cannot run deep analysis: Wave 1 not complete")

        # Run deep analysis
        analysis = await self.deep_analyzer.analyze_session(
            session_id=session_id,
            session=session
        )

        # Update session
        self.db.table("therapy_sessions").update({
            "deep_analysis": analysis.to_dict(),
            "analysis_confidence": analysis.confidence_score,
            "deep_analyzed_at": datetime.utcnow().isoformat(),
        }).eq("id", session_id).execute()

        logger.info(f"✓ Wave 2 deep analysis complete for session {session_id}")

        # Auto-generate prose from deep analysis
        try:
            logger.info(f"📝 Auto-generating prose for session {session_id}")
            prose_generator = ProseGenerator()
            prose = await prose_generator.generate_prose(
                session_id=session_id,
                deep_analysis=analysis.to_dict(),
                confidence_score=analysis.confidence_score
            )

            # Update session with prose
            self.db.table("therapy_sessions").update({
                "prose_analysis": prose.prose_text,
                "prose_generated_at": prose.generated_at.isoformat()
            }).eq("id", session_id).execute()

            logger.info(f"✓ Prose auto-generated: {prose.word_count} words, {prose.paragraph_count} paragraphs")

        except Exception as e:
            # Don't fail entire Wave 2 if prose generation fails
            logger.error(f"Prose auto-generation failed for session {session_id}: {e}")
            logger.warning("Wave 2 deep analysis succeeded, but prose generation failed (non-critical)")

    # =============================================================================
    # Helper Functions
    # =============================================================================

    async def _get_session(self, session_id: str) -> Dict[str, Any]:
        """Get session from database"""
        response = self.db.table("therapy_sessions").select("*").eq("id", session_id).single().execute()
        if not response.data:
            raise Exception(f"Session not found: {session_id}")
        return response.data

    async def _is_wave1_complete(self, session_id: str) -> bool:
        """Check if all Wave 1 analyses are complete"""
        session = await self._get_session(session_id)
        return (
            session.get("mood_analyzed_at") is not None and
            session.get("topics_extracted_at") is not None and
            session.get("breakthrough_analyzed_at") is not None
        )

    async def _mark_wave1_complete(self, session_id: str):
        """Mark Wave 1 as complete"""
        self.db.table("therapy_sessions").update({
            "analysis_status": "wave1_complete",
            "wave1_completed_at": datetime.utcnow().isoformat(),
        }).eq("id", session_id).execute()

    async def _update_session_status(self, session_id: str, status: str):
        """Update analysis status in session"""
        self.db.table("therapy_sessions").update({
            "analysis_status": status,
        }).eq("id", session_id).execute()

    async def _log_analysis_start(self, session_id: str, wave: str, retry_count: int):
        """Log analysis start in processing log"""
        self.db.table("analysis_processing_log").insert({
            "session_id": session_id,
            "wave": wave,
            "status": "started",
            "retry_count": retry_count,
        }).execute()

    async def _log_analysis_complete(self, session_id: str, wave: str, duration_ms: int):
        """Log analysis completion in processing log"""
        # Update the most recent 'started' entry for this wave
        self.db.table("analysis_processing_log").update({
            "status": "completed",
            "completed_at": datetime.utcnow().isoformat(),
            "processing_duration_ms": duration_ms,
        }).eq("session_id", session_id).eq("wave", wave).eq("status", "started").execute()

    async def _log_analysis_failure(self, session_id: str, wave: str, error_message: str, retry_count: int):
        """Log analysis failure in processing log"""
        # Update the most recent 'started' entry for this wave
        self.db.table("analysis_processing_log").update({
            "status": "failed",
            "completed_at": datetime.utcnow().isoformat(),
            "error_message": error_message,
            "retry_count": retry_count,
        }).eq("session_id", session_id).eq("wave", wave).eq("status", "started").execute()

    async def get_pipeline_status(self, session_id: str) -> PipelineStatus:
        """Get current pipeline status for a session"""
        # Use database function
        response = self.db.rpc("get_analysis_pipeline_status", {"p_session_id": session_id}).execute()

        if not response.data or len(response.data) == 0:
            raise Exception(f"Session not found: {session_id}")

        data = response.data[0]

        return PipelineStatus(
            session_id=data["session_id"],
            analysis_status=data["analysis_status"],
            mood_complete=data["mood_complete"],
            topics_complete=data["topics_complete"],
            breakthrough_complete=data["breakthrough_complete"],
            wave1_complete=data["wave1_complete"],
            deep_complete=data["deep_complete"],
            wave1_completed_at=data.get("wave1_completed_at"),
            deep_analyzed_at=data.get("deep_analyzed_at"),
        )


# Convenience function for background tasks
async def analyze_session_full_pipeline(session_id: str, force: bool = False) -> PipelineStatus:
    """
    Convenience function to run full analysis pipeline

    Args:
        session_id: Session UUID
        force: Force re-analysis

    Returns:
        PipelineStatus with final state
    """
    orchestrator = AnalysisOrchestrator()
    return await orchestrator.process_session_full_pipeline(session_id, force)
