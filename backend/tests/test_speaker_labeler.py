"""
Unit tests for speaker labeling service
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from app.services.speaker_labeler import (
    SpeakerLabeler,
    label_session_transcript,
    SpeakerRoleDetection,
    LabeledSegment
)

# Mock transcript data
MOCK_TRANSCRIPT = [
    {"start": 0.0, "end": 28.4, "speaker": "SPEAKER_00", "text": "Hi Alex, welcome. I'm Dr. Rodriguez."},
    {"start": 28.4, "end": 45.8, "speaker": "SPEAKER_01", "text": "Yeah, that makes sense. Um, I'm really nervous."},
    {"start": 45.8, "end": 60.2, "speaker": "SPEAKER_01", "text": "I've never done therapy before."},
    {"start": 60.2, "end": 72.3, "speaker": "SPEAKER_00", "text": "It's completely normal to feel nervous."},
]

class TestSpeakerLabeler:
    """Tests for SpeakerLabeler class"""

    @pytest.fixture
    def labeler(self, openai_api_key):
        return SpeakerLabeler(openai_api_key=openai_api_key)

    def test_merge_consecutive_segments(self, labeler):
        """Test merging consecutive same-speaker segments"""
        merged = labeler._merge_consecutive_segments(MOCK_TRANSCRIPT)

        assert len(merged) == 3  # 4 segments → 3 merged blocks
        assert merged[0]['speaker'] == 'SPEAKER_00'
        assert merged[1]['speaker'] == 'SPEAKER_01'
        assert merged[1]['text'] == "Yeah, that makes sense. Um, I'm really nervous. I've never done therapy before."
        assert merged[2]['speaker'] == 'SPEAKER_00'

    def test_format_timestamp(self, labeler):
        """Test timestamp conversion to MM:SS"""
        assert labeler._format_timestamp(0.0) == "00:00"
        assert labeler._format_timestamp(28.4) == "00:28"
        assert labeler._format_timestamp(83.7) == "01:23"
        assert labeler._format_timestamp(3600.0) == "60:00"

    def test_calculate_speaker_stats(self, labeler):
        """Test speaking time statistics"""
        stats = labeler._calculate_speaker_stats(MOCK_TRANSCRIPT)

        assert 'SPEAKER_00' in stats
        assert 'SPEAKER_01' in stats
        assert 'total_time_seconds' in stats['SPEAKER_00']
        assert 'segment_count' in stats['SPEAKER_00']
        assert 'percentage' in stats['SPEAKER_00']

        # Verify totals
        total_pct = stats['SPEAKER_00']['percentage'] + stats['SPEAKER_01']['percentage']
        assert abs(total_pct - 100.0) < 0.1  # Should sum to 100%

    @pytest.mark.integration
    def test_detect_speaker_roles(self, labeler):
        """Test AI speaker role detection (requires OpenAI API)"""
        detection = labeler._detect_speaker_roles(MOCK_TRANSCRIPT)

        assert isinstance(detection, SpeakerRoleDetection)
        assert detection.therapist_speaker_id in ['SPEAKER_00', 'SPEAKER_01']
        assert detection.patient_speaker_id in ['SPEAKER_00', 'SPEAKER_01']
        assert detection.therapist_speaker_id != detection.patient_speaker_id
        assert 0.0 <= detection.confidence <= 1.0
        assert len(detection.reasoning) > 0

        # Should detect SPEAKER_00 as therapist (introduces self as "Dr. Rodriguez")
        assert detection.therapist_speaker_id == 'SPEAKER_00'

    @pytest.mark.integration
    def test_full_labeling_pipeline(self, labeler):
        """Test complete labeling workflow"""
        result = labeler.label_transcript(
            raw_segments=MOCK_TRANSCRIPT,
            therapist_name="Dr. Sarah Rodriguez"
        )

        # Verify structure
        assert len(result.labeled_transcript) > 0
        assert result.therapist_name == "Dr. Sarah Rodriguez"
        assert result.patient_label == "You"
        assert result.detection.confidence > 0.5

        # Verify labels
        first_segment = result.labeled_transcript[0]
        assert isinstance(first_segment, LabeledSegment)
        assert first_segment.speaker == "Dr. Sarah Rodriguez"
        assert first_segment.timestamp == "00:00"

        # Verify merging happened
        assert len(result.labeled_transcript) < len(MOCK_TRANSCRIPT)
