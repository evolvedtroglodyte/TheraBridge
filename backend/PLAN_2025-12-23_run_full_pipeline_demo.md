# Run Full AI Analysis Pipeline Demo - Implementation Plan

## Overview

Create a comprehensive test script that runs the complete AI analysis pipeline (Wave 1 + Wave 2) on the last 3 mock therapy sessions (Sessions 10, 11, 12) and automatically displays the results.

## Current State Analysis

**Existing Infrastructure:**
- ✅ Wave 1 algorithms complete: `mood_analyzer.py`, `topic_extractor.py`, `breakthrough_detector.py`
- ✅ Wave 2 algorithm complete: `deep_analyzer.py`
- ✅ Orchestrator with dependency management: `analysis_orchestrator.py`
- ✅ 12 mock therapy sessions in `/mock-therapy-data/sessions/`
- ✅ Database schema supports all analysis fields
- ✅ Existing test script pattern: `test_breakthrough_all_sessions.py`

**What's Missing:**
- No end-to-end test demonstrating the full orchestrated pipeline
- No automated output file opening for easy inspection
- No script that simulates the complete production flow with proper context

## Desired End State

A single test script that:
1. Runs the complete orchestrated pipeline on Sessions 10, 11, 12
2. Uses previous sessions as context for deep analysis (Session 10 uses 8-9, Session 11 uses 9-10, Session 12 uses 10-11)
3. Displays detailed terminal output showing all algorithm results
4. Saves comprehensive JSON results to a timestamped file
5. Automatically opens both the terminal output and JSON file for inspection

**Verification:**
- Run `python tests/test_full_pipeline_demo.py` and see both terminal output and JSON file open automatically
- Verify all 4 algorithms (mood, topics, breakthrough, deep) ran successfully
- Confirm deep analysis used proper session history context
- Check JSON structure includes all analysis dimensions

## What We're NOT Doing

- Not modifying existing production code (`analysis_orchestrator.py`, individual analyzers)
- Not creating new API endpoints
- Not running on real patient data (using mock sessions only)
- Not storing results in database (file-based output only for demo)
- Not implementing the orchestrator from scratch (reusing existing code)

## Implementation Approach

Create a self-contained demo script that:
1. Loads mock sessions from JSON files
2. Simulates a mini database with session history
3. Runs the orchestrator's full pipeline
4. Captures all outputs and formats them clearly
5. Auto-opens results using system commands

---

## Phase 1: Create Mock Database Context

### Overview
Build an in-memory context that simulates the database for deep analysis to access session history.

### Changes Required:

#### 1.1 Create Demo Script Scaffold

**File**: `backend/tests/test_full_pipeline_demo.py`
**Changes**: Create new test script with imports and utilities

```python
"""
Full Pipeline Demo - Run complete AI analysis on Sessions 10, 11, 12

Demonstrates:
- Wave 1: Mood analysis, topic extraction, breakthrough detection (parallel)
- Wave 2: Deep clinical analysis (uses previous sessions as context)

Outputs:
- Detailed terminal output
- Comprehensive JSON report (auto-opened)
"""

import os
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List
from dotenv import load_dotenv
import subprocess
import platform

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.mood_analyzer import MoodAnalyzer
from app.services.topic_extractor import TopicExtractor
from app.services.breakthrough_detector import BreakthroughDetector
from app.services.deep_analyzer import DeepAnalyzer


def load_session(session_number: int) -> Dict[str, Any]:
    """Load a session JSON file"""
    session_files = {
        1: "session_01_crisis_intake.json",
        2: "session_02_emotional_regulation.json",
        3: "session_03_adhd_discovery.json",
        4: "session_04_medication_start.json",
        5: "session_05_family_conflict.json",
        6: "session_06_spring_break_hope.json",
        7: "session_07_dating_anxiety.json",
        8: "session_08_relationship_boundaries.json",
        9: "session_09_coming_out_preparation.json",
        10: "session_10_coming_out_aftermath.json",
        11: "session_11_rebuilding.json",
        12: "session_12_thriving.json",
    }

    data_dir = Path(__file__).parent.parent.parent / "mock-therapy-data" / "sessions"
    filepath = data_dir / session_files[session_number]

    with open(filepath, 'r') as f:
        return json.load(f)


def open_file_automatically(filepath: str):
    """Open file using system default application"""
    system = platform.system()

    try:
        if system == "Darwin":  # macOS
            subprocess.run(["open", filepath], check=True)
        elif system == "Windows":
            os.startfile(filepath)
        elif system == "Linux":
            subprocess.run(["xdg-open", filepath], check=True)
        else:
            print(f"⚠️  Cannot auto-open on {system}. File saved to: {filepath}")
    except Exception as e:
        print(f"⚠️  Could not auto-open file: {e}")
        print(f"📄 File saved to: {filepath}")
```

#### 1.2 Create Mock Database Context Builder

**File**: `backend/tests/test_full_pipeline_demo.py`
**Changes**: Add function to build in-memory session database

```python
class MockSessionDatabase:
    """
    In-memory mock database for session history.
    Simulates the database queries that deep_analyzer.py makes.
    """

    def __init__(self):
        self.sessions = {}  # session_id -> session data
        self.patient_id = "patient_alex_chen_demo"

    def add_session(self, session_num: int, session_data: Dict[str, Any], wave1_results: Dict[str, Any]):
        """Add a session with its Wave 1 analysis results"""
        session_id = f"session_{session_num:02d}"

        # Simulate database schema
        self.sessions[session_id] = {
            "id": session_id,
            "patient_id": self.patient_id,
            "session_date": (datetime(2025, 1, 10) + timedelta(weeks=session_num-1)).isoformat(),
            "transcript": session_data.get("segments", []),

            # Wave 1 results
            "mood_score": wave1_results.get("mood_score"),
            "mood_confidence": wave1_results.get("mood_confidence"),
            "mood_rationale": wave1_results.get("mood_rationale"),
            "mood_indicators": wave1_results.get("mood_indicators", []),
            "emotional_tone": wave1_results.get("emotional_tone"),

            "topics": wave1_results.get("topics", []),
            "action_items": wave1_results.get("action_items", []),
            "technique": wave1_results.get("technique"),
            "summary": wave1_results.get("summary"),
            "extraction_confidence": wave1_results.get("extraction_confidence"),

            "has_breakthrough": wave1_results.get("has_breakthrough", False),
            "breakthrough_data": wave1_results.get("breakthrough_data"),

            # Timestamps
            "mood_analyzed_at": datetime.utcnow().isoformat(),
            "topics_extracted_at": datetime.utcnow().isoformat(),
            "breakthrough_analyzed_at": datetime.utcnow().isoformat(),
        }

    def get_session(self, session_id: str) -> Dict[str, Any]:
        """Get session by ID"""
        return self.sessions.get(session_id)

    def get_previous_sessions(self, current_session_num: int, limit: int = 2) -> List[Dict[str, Any]]:
        """Get previous sessions for context"""
        previous = []
        for i in range(max(1, current_session_num - limit), current_session_num):
            session_id = f"session_{i:02d}"
            if session_id in self.sessions:
                previous.append(self.sessions[session_id])
        return previous
```

### Success Criteria:

#### Automated Verification:
- [ ] Script imports all required services without errors
- [ ] Mock database can load and store session data
- [ ] File opening utility works on current OS

#### Manual Verification:
- [ ] Review mock database structure matches real schema
- [ ] Confirm session loading works for Sessions 1-12

**Implementation Note**: After completing this phase, verify the mock database correctly simulates the real database structure before proceeding to Phase 2.

---

## Phase 2: Implement Wave 1 Analysis

### Overview
Run all three Wave 1 algorithms (mood, topics, breakthrough) on each session and collect results.

### Changes Required:

#### 2.1 Wave 1 Analysis Runner

**File**: `backend/tests/test_full_pipeline_demo.py`
**Changes**: Add function to run Wave 1 analyses

```python
def run_wave1_analysis(session_num: int, session_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run Wave 1 analyses: mood, topics, breakthrough (parallel simulation)

    Args:
        session_num: Session number (1-12)
        session_data: Loaded session JSON

    Returns:
        Dictionary with all Wave 1 results
    """
    print(f"\n{'=' * 80}")
    print(f"WAVE 1 ANALYSIS - SESSION {session_num}")
    print(f"{'=' * 80}")

    session_id = f"session_{session_num:02d}"
    segments = session_data.get("segments", [])

    results = {
        "session_id": session_id,
        "session_num": session_num,
    }

    # 1. Mood Analysis
    print(f"\n📊 Running Mood Analysis...")
    try:
        mood_analyzer = MoodAnalyzer()
        mood_analysis = mood_analyzer.analyze_session_mood(
            session_id=session_id,
            segments=segments,
            patient_speaker_id="SPEAKER_01"
        )

        results["mood_score"] = mood_analysis.mood_score
        results["mood_confidence"] = mood_analysis.confidence
        results["mood_rationale"] = mood_analysis.rationale
        results["mood_indicators"] = mood_analysis.key_indicators
        results["emotional_tone"] = mood_analysis.emotional_tone

        print(f"   ✓ Mood Score: {mood_analysis.mood_score}/10.0")
        print(f"   ✓ Confidence: {mood_analysis.confidence:.2f}")
        print(f"   ✓ Emotional Tone: {mood_analysis.emotional_tone}")
        print(f"   ✓ Key Indicators: {', '.join(mood_analysis.key_indicators[:3])}")

    except Exception as e:
        print(f"   ❌ Mood Analysis Failed: {e}")
        results["mood_error"] = str(e)

    # 2. Topic Extraction
    print(f"\n📝 Running Topic Extraction...")
    try:
        topic_extractor = TopicExtractor()
        metadata = topic_extractor.extract_metadata(
            session_id=session_id,
            segments=segments
        )

        results["topics"] = metadata.topics
        results["action_items"] = metadata.action_items
        results["technique"] = metadata.technique
        results["summary"] = metadata.summary
        results["extraction_confidence"] = metadata.confidence

        print(f"   ✓ Topics: {', '.join(metadata.topics)}")
        print(f"   ✓ Technique: {metadata.technique}")
        print(f"   ✓ Action Items: {', '.join(metadata.action_items)}")
        print(f"   ✓ Summary: {metadata.summary[:100]}...")

    except Exception as e:
        print(f"   ❌ Topic Extraction Failed: {e}")
        results["topics_error"] = str(e)

    # 3. Breakthrough Detection
    print(f"\n⭐ Running Breakthrough Detection...")
    try:
        breakthrough_detector = BreakthroughDetector()
        bt_analysis = breakthrough_detector.analyze_session(
            transcript=segments,
            session_metadata={"session_id": session_id}
        )

        results["has_breakthrough"] = bt_analysis.has_breakthrough
        results["breakthrough_data"] = None

        if bt_analysis.primary_breakthrough:
            bt = bt_analysis.primary_breakthrough
            results["breakthrough_data"] = {
                "type": bt.breakthrough_type,
                "label": bt.label,
                "description": bt.description,
                "evidence": bt.evidence,
                "confidence": float(bt.confidence_score),
                "timestamp_start": float(bt.timestamp_start),
                "timestamp_end": float(bt.timestamp_end),
            }

            print(f"   ✓ Breakthrough Detected: {bt.label}")
            print(f"   ✓ Type: {bt.breakthrough_type}")
            print(f"   ✓ Confidence: {bt.confidence_score:.2f}")
            print(f"   ✓ Description: {bt.description[:100]}...")
        else:
            print(f"   ✓ No breakthrough detected (as expected for most sessions)")

    except Exception as e:
        print(f"   ❌ Breakthrough Detection Failed: {e}")
        results["breakthrough_error"] = str(e)

    print(f"\n{'=' * 80}")
    print(f"WAVE 1 COMPLETE - SESSION {session_num}")
    print(f"{'=' * 80}")

    return results
```

### Success Criteria:

#### Automated Verification:
- [ ] All three Wave 1 algorithms execute without errors
- [ ] Results dictionary contains all expected fields
- [ ] Terminal output displays all algorithm results

#### Manual Verification:
- [ ] Mood scores are in valid range (0.0-10.0)
- [ ] Topics and techniques are extracted correctly
- [ ] Breakthrough detection is appropriately selective

**Implementation Note**: Verify Wave 1 results are sensible before proceeding to Wave 2.

---

## Phase 3: Implement Wave 2 Deep Analysis

### Overview
Run deep clinical analysis using Wave 1 results + session history as context.

### Changes Required:

#### 3.1 Wave 2 Analysis Runner with Mock Database Integration

**File**: `backend/tests/test_full_pipeline_demo.py`
**Changes**: Add async function to run Wave 2 with proper context

```python
import asyncio


async def run_wave2_analysis(
    session_num: int,
    session_data: Dict[str, Any],
    wave1_results: Dict[str, Any],
    mock_db: MockSessionDatabase
) -> Dict[str, Any]:
    """
    Run Wave 2 deep analysis with session history context

    Args:
        session_num: Current session number
        session_data: Raw session JSON
        wave1_results: Wave 1 analysis results
        mock_db: Mock database with previous sessions

    Returns:
        Deep analysis results
    """
    print(f"\n{'=' * 80}")
    print(f"WAVE 2 ANALYSIS - SESSION {session_num}")
    print(f"{'=' * 80}")

    session_id = f"session_{session_num:02d}"

    # Get previous sessions for context
    previous_sessions = mock_db.get_previous_sessions(session_num, limit=2)

    print(f"\n🧠 Running Deep Clinical Analysis...")
    print(f"   Context: Using {len(previous_sessions)} previous session(s) as history")

    if previous_sessions:
        for i, prev in enumerate(previous_sessions, 1):
            print(f"      - Session {prev['id']}: Mood {prev.get('mood_score', 'N/A')}/10, Topics: {', '.join(prev.get('topics', []))}")

    try:
        # Note: DeepAnalyzer expects a database connection, but we'll need to mock it
        # For this demo, we'll create a simplified version that doesn't require DB

        # Build session context for deep analyzer
        session_context = {
            "session_id": session_id,
            "patient_id": mock_db.patient_id,
            "session_date": mock_db.sessions[session_id]["session_date"],
            "transcript": session_data.get("segments", []),

            # Wave 1 results
            "mood_score": wave1_results.get("mood_score"),
            "mood_indicators": wave1_results.get("mood_indicators", []),
            "emotional_tone": wave1_results.get("emotional_tone"),
            "topics": wave1_results.get("topics", []),
            "action_items": wave1_results.get("action_items", []),
            "technique": wave1_results.get("technique"),
            "summary": wave1_results.get("summary"),
            "breakthrough_data": wave1_results.get("breakthrough_data"),
        }

        # For demo purposes, we'll call the deep analyzer directly
        # In production, this would go through the orchestrator
        deep_analyzer = DeepAnalyzer()

        # Note: DeepAnalyzer.analyze_session is async and expects DB access
        # We need to mock the DB queries or create a simplified version

        # Simplified approach: Extract the key logic without DB dependency
        analysis = await run_deep_analysis_with_mock_db(
            deep_analyzer,
            session_id,
            session_context,
            previous_sessions
        )

        # Display results
        print(f"\n   ✓ Deep Analysis Complete")
        print(f"   ✓ Confidence: {analysis.confidence_score:.2f}")

        # Progress Indicators
        print(f"\n   📈 Progress Indicators:")
        if analysis.progress_indicators.symptom_reduction:
            print(f"      - Symptom Reduction: {analysis.progress_indicators.symptom_reduction.get('description', 'N/A')}")
        print(f"      - Skills Developed: {len(analysis.progress_indicators.skill_development)}")
        print(f"      - Goals Tracked: {len(analysis.progress_indicators.goal_progress)}")

        # Key Insights
        print(f"\n   💡 Therapeutic Insights:")
        for insight in analysis.therapeutic_insights.key_realizations[:2]:
            print(f"      - {insight}")

        # Coping Skills
        print(f"\n   🛠️  Coping Skills:")
        for skill in analysis.coping_skills.learned[:3]:
            proficiency = analysis.coping_skills.proficiency.get(skill, "N/A")
            print(f"      - {skill}: {proficiency}")

        # Therapeutic Relationship
        print(f"\n   🤝 Therapeutic Relationship:")
        print(f"      - Engagement: {analysis.therapeutic_relationship.engagement_level}")
        print(f"      - Openness: {analysis.therapeutic_relationship.openness}")
        print(f"      - Alliance: {analysis.therapeutic_relationship.alliance_strength}")

        # Recommendations
        print(f"\n   ✅ Recommendations:")
        for rec in analysis.recommendations.practices[:2]:
            print(f"      - {rec}")

        return {
            "session_id": session_id,
            "deep_analysis": analysis.to_dict(),
            "confidence_score": analysis.confidence_score,
        }

    except Exception as e:
        print(f"   ❌ Deep Analysis Failed: {e}")
        return {
            "session_id": session_id,
            "deep_error": str(e)
        }


async def run_deep_analysis_with_mock_db(
    deep_analyzer: DeepAnalyzer,
    session_id: str,
    session_context: Dict[str, Any],
    previous_sessions: List[Dict[str, Any]]
) -> Any:
    """
    Wrapper to run deep analysis with mocked database context.

    This function simulates what the orchestrator does but without requiring
    a real database connection.
    """
    # The DeepAnalyzer expects to query the database for history
    # For this demo, we'll manually inject the history into the context

    # Create a modified session dict that includes the history
    enriched_session = {
        **session_context,
        "_mock_previous_sessions": previous_sessions,
    }

    # Call the analyzer
    # Note: This may still fail if it tries to access DB directly
    # In that case, we'll need to further mock the DB methods

    try:
        return await deep_analyzer.analyze_session(session_id, enriched_session)
    except AttributeError:
        # If it fails due to DB access, we need to patch the DB methods
        # Create a mock DB client
        from unittest.mock import MagicMock, AsyncMock

        mock_db_client = MagicMock()

        # Mock the table queries to return our previous sessions
        def mock_table_query(*args, **kwargs):
            mock_response = MagicMock()
            mock_response.data = previous_sessions
            return mock_response

        mock_db_client.table.return_value.select.return_value.eq.return_value.neq.return_value.order.return_value.limit.return_value.execute = mock_table_query

        # Mock RPC calls
        mock_db_client.rpc.return_value.execute.return_value.data = []

        # Replace the DB in the analyzer
        deep_analyzer.db = mock_db_client

        # Try again
        return await deep_analyzer.analyze_session(session_id, enriched_session)
```

### Success Criteria:

#### Automated Verification:
- [ ] Deep analysis executes without errors
- [ ] Previous sessions are correctly loaded as context
- [ ] All analysis dimensions are populated

#### Manual Verification:
- [ ] Deep analysis shows awareness of patient history
- [ ] Insights reference patterns from previous sessions
- [ ] Recommendations are contextually appropriate

**Implementation Note**: Verify deep analysis quality before proceeding to output generation.

---

## Phase 4: Output Generation and Auto-Opening

### Overview
Generate comprehensive terminal output and JSON file, then automatically open the results.

### Changes Required:

#### 4.1 Main Execution Function

**File**: `backend/tests/test_full_pipeline_demo.py`
**Changes**: Add main function to orchestrate everything

```python
async def main():
    """
    Main execution: Run full pipeline on Sessions 10, 11, 12
    """
    print("=" * 80)
    print("FULL AI ANALYSIS PIPELINE DEMO")
    print("Sessions 10, 11, 12 (Coming Out Aftermath → Rebuilding → Thriving)")
    print("=" * 80)
    print()

    # Initialize mock database
    mock_db = MockSessionDatabase()

    # Store all results
    all_results = {
        "demo_info": {
            "timestamp": datetime.utcnow().isoformat(),
            "sessions_analyzed": [10, 11, 12],
            "pipeline_version": "Wave 1 + Wave 2 (Full Orchestration)",
        },
        "sessions": []
    }

    # Process Sessions 1-9 (to build context, but don't display)
    print("📚 Loading context sessions (1-9) for history...")
    for session_num in range(1, 10):
        session_data = load_session(session_num)

        # Run Wave 1 only (no output)
        wave1_results = run_wave1_analysis_silent(session_num, session_data)

        # Add to mock database
        mock_db.add_session(session_num, session_data, wave1_results)

        print(f"   ✓ Session {session_num} loaded")

    print(f"\n✅ Context built: 9 previous sessions loaded\n")

    # Process Sessions 10, 11, 12 (full analysis with output)
    target_sessions = [10, 11, 12]

    for session_num in target_sessions:
        print(f"\n{'#' * 80}")
        print(f"SESSION {session_num} - FULL PIPELINE")
        print(f"{'#' * 80}")

        # Load session
        session_data = load_session(session_num)
        print(f"\n📄 Loaded: {session_data.get('id', 'Unknown')}")
        print(f"   Segments: {len(session_data.get('segments', []))}")

        # Wave 1
        wave1_results = run_wave1_analysis(session_num, session_data)

        # Add to mock database
        mock_db.add_session(session_num, session_data, wave1_results)

        # Wave 2
        wave2_results = await run_wave2_analysis(
            session_num,
            session_data,
            wave1_results,
            mock_db
        )

        # Combine results
        session_result = {
            "session_num": session_num,
            "session_id": session_data.get("id"),
            "wave1": wave1_results,
            "wave2": wave2_results,
        }

        all_results["sessions"].append(session_result)

    # Save to JSON file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(__file__).parent.parent.parent / "mock-therapy-data"
    output_file = output_dir / f"full_pipeline_demo_{timestamp}.json"

    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)

    print(f"\n{'=' * 80}")
    print("DEMO COMPLETE")
    print(f"{'=' * 80}")
    print(f"\n✅ All sessions analyzed successfully")
    print(f"📄 Results saved to: {output_file}")
    print(f"\n🚀 Auto-opening results file...\n")

    # Auto-open the JSON file
    open_file_automatically(str(output_file))

    return all_results


def run_wave1_analysis_silent(session_num: int, session_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run Wave 1 analysis without terminal output (for context building)
    """
    session_id = f"session_{session_num:02d}"
    segments = session_data.get("segments", [])

    results = {"session_id": session_id, "session_num": session_num}

    try:
        mood_analyzer = MoodAnalyzer()
        mood_analysis = mood_analyzer.analyze_session_mood(
            session_id=session_id,
            segments=segments,
            patient_speaker_id="SPEAKER_01"
        )
        results.update({
            "mood_score": mood_analysis.mood_score,
            "mood_confidence": mood_analysis.confidence,
            "mood_rationale": mood_analysis.rationale,
            "mood_indicators": mood_analysis.key_indicators,
            "emotional_tone": mood_analysis.emotional_tone,
        })
    except Exception as e:
        results["mood_error"] = str(e)

    try:
        topic_extractor = TopicExtractor()
        metadata = topic_extractor.extract_metadata(session_id=session_id, segments=segments)
        results.update({
            "topics": metadata.topics,
            "action_items": metadata.action_items,
            "technique": metadata.technique,
            "summary": metadata.summary,
            "extraction_confidence": metadata.confidence,
        })
    except Exception as e:
        results["topics_error"] = str(e)

    try:
        breakthrough_detector = BreakthroughDetector()
        bt_analysis = breakthrough_detector.analyze_session(
            transcript=segments,
            session_metadata={"session_id": session_id}
        )
        results["has_breakthrough"] = bt_analysis.has_breakthrough
        results["breakthrough_data"] = None
        if bt_analysis.primary_breakthrough:
            bt = bt_analysis.primary_breakthrough
            results["breakthrough_data"] = {
                "type": bt.breakthrough_type,
                "label": bt.label,
                "description": bt.description,
                "evidence": bt.evidence,
                "confidence": float(bt.confidence_score),
                "timestamp_start": float(bt.timestamp_start),
                "timestamp_end": float(bt.timestamp_end),
            }
    except Exception as e:
        results["breakthrough_error"] = str(e)

    return results


if __name__ == "__main__":
    asyncio.run(main())
```

### Success Criteria:

#### Automated Verification:
- [ ] Script runs end-to-end: `python tests/test_full_pipeline_demo.py`
- [ ] JSON file is created with timestamp
- [ ] JSON file opens automatically in system default application
- [ ] No Python errors or exceptions

#### Manual Verification:
- [ ] Terminal output is clear and well-formatted
- [ ] JSON structure is complete and readable
- [ ] All 3 sessions show complete Wave 1 + Wave 2 results
- [ ] Deep analysis shows proper use of session history

**Implementation Note**: After successful execution, review JSON output to ensure all analysis dimensions are captured correctly.

---

## Testing Strategy

### Unit Tests:
- Mock database correctly simulates real schema
- Wave 1 analyses run independently
- Wave 2 uses session history properly
- File opening works on macOS (current platform)

### Integration Tests:
- End-to-end pipeline execution on Sessions 10-12
- Context building from Sessions 1-9
- JSON output structure validation
- Auto-open functionality verification

### Manual Testing Steps:
1. Run: `cd backend && python tests/test_full_pipeline_demo.py`
2. Verify terminal output shows all algorithm results clearly
3. Confirm JSON file opens automatically in default editor/viewer
4. Review JSON structure for completeness:
   - All Wave 1 fields (mood, topics, breakthrough)
   - All Wave 2 fields (progress, insights, skills, relationship, recommendations)
   - Proper session context usage
5. Check that deep analysis references previous sessions appropriately

## Performance Considerations

**Expected Runtime:**
- Wave 1 (3 analyses × 3 sessions): ~60-90 seconds total
- Wave 2 (1 analysis × 3 sessions with context): ~90-120 seconds total
- **Total: ~2.5-3.5 minutes**

**API Costs:**
- Mood analysis: GPT-4o-mini (~$0.01 × 3 = $0.03)
- Topic extraction: GPT-4o-mini (~$0.01 × 3 = $0.03)
- Breakthrough detection: GPT-4o (~$0.05 × 3 = $0.15)
- Deep analysis: GPT-4o (~$0.10 × 3 = $0.30)
- **Total: ~$0.51 per run**

## Migration Notes

N/A - This is a standalone demo script, not a migration.

## References

- Existing pipeline: `backend/app/services/analysis_orchestrator.py`
- Existing test pattern: `backend/tests/test_breakthrough_all_sessions.py`
- Mock sessions: `/mock-therapy-data/sessions/session_10_coming_out_aftermath.json` (and 11, 12)
- Deep analyzer: `backend/app/services/deep_analyzer.py:308` (context building)
- Mood analyzer: `backend/app/services/mood_analyzer.py:62` (analyze_session_mood)
- Topic extractor: `backend/app/services/topic_extractor.py:68` (extract_metadata)
- Breakthrough detector: `backend/app/services/breakthrough_detector.py:68` (analyze_session)
