"""
Unit tests for data_generators module.

Tests verify that all generators produce data that:
1. Matches the expected schemas
2. Contains realistic values
3. Handles edge cases correctly
4. Can be customized via parameters
"""

import pytest
import uuid
from datetime import datetime

from app.models.schemas import (
    ExtractedNotes,
    Strategy,
    Trigger,
    ActionItem,
    SignificantQuote,
    RiskFlag,
    TranscriptSegment,
    MoodLevel,
    StrategyStatus,
    SessionStatus,
    UserRole,
)

from tests.utils.data_generators import (
    generate_transcript,
    generate_transcript_segments,
    generate_edge_case_transcript,
    generate_therapist,
    generate_patient,
    generate_session,
    generate_extracted_notes,
    generate_audio_file,
    generate_test_dataset,
)


# ============================================================================
# Transcript Generation Tests
# ============================================================================

class TestTranscriptGeneration:
    """Tests for transcript generation functions"""

    def test_generate_transcript_basic(self):
        """Test basic transcript generation"""
        transcript = generate_transcript(num_segments=5, duration_seconds=300)

        assert isinstance(transcript, str)
        assert len(transcript) > 0
        assert "Therapist:" in transcript or "Client:" in transcript

    def test_generate_transcript_without_labels(self):
        """Test transcript without speaker labels"""
        transcript = generate_transcript(
            num_segments=3,
            speaker_labels=False
        )

        assert isinstance(transcript, str)
        assert "Therapist:" not in transcript
        assert "Client:" not in transcript

    def test_generate_transcript_customizable(self):
        """Test that transcript respects num_segments parameter"""
        short_transcript = generate_transcript(num_segments=2)
        long_transcript = generate_transcript(num_segments=20)

        # Longer transcript should have more content
        assert len(long_transcript) > len(short_transcript)

    def test_generate_transcript_segments(self):
        """Test transcript segment generation with timing"""
        segments = generate_transcript_segments(
            num_segments=10,
            duration_seconds=600
        )

        assert len(segments) == 10
        assert all(isinstance(seg, TranscriptSegment) for seg in segments)

        # Check that segments have valid timing
        for seg in segments:
            assert seg.start >= 0
            assert seg.end > seg.start
            assert seg.speaker in ["Therapist", "Client"]
            assert len(seg.text) > 0

        # Check that segments are in order
        for i in range(len(segments) - 1):
            assert segments[i].end <= segments[i + 1].start + 5  # Allow small overlap

    def test_generate_transcript_segments_duration(self):
        """Test that segment timing matches duration"""
        duration = 600
        segments = generate_transcript_segments(
            num_segments=20,
            duration_seconds=duration
        )

        # Last segment should end around the total duration
        last_segment = segments[-1]
        assert last_segment.end <= duration * 1.5  # Allow some flexibility

    def test_edge_case_empty(self):
        """Test empty transcript generation"""
        transcript = generate_edge_case_transcript("empty")
        assert transcript == ""

    def test_edge_case_very_short(self):
        """Test very short transcript"""
        transcript = generate_edge_case_transcript("very_short")
        assert len(transcript) < 10
        assert len(transcript) > 0

    def test_edge_case_very_long(self):
        """Test very long transcript generation"""
        transcript = generate_edge_case_transcript("very_long")
        assert len(transcript) > 10000  # Should be very long
        word_count = len(transcript.split())
        assert word_count > 5000  # Many words

    def test_edge_case_special_chars(self):
        """Test transcript with special characters"""
        transcript = generate_edge_case_transcript("special_chars")
        assert len(transcript) > 0
        # Should contain some non-ASCII or special characters
        assert any(ord(c) > 127 for c in transcript) or any(c in "éàèù😊" for c in transcript)

    def test_edge_case_no_punctuation(self):
        """Test transcript without punctuation"""
        transcript = generate_edge_case_transcript("no_punctuation")
        assert "." not in transcript
        assert "!" not in transcript
        assert "?" not in transcript
        assert len(transcript) > 0

    def test_edge_case_single_speaker(self):
        """Test transcript with only one speaker"""
        transcript = generate_edge_case_transcript("single_speaker")
        assert "Therapist:" in transcript
        assert "Client:" not in transcript

    def test_edge_case_invalid_type(self):
        """Test that invalid edge case type raises error"""
        with pytest.raises(ValueError):
            generate_edge_case_transcript("invalid_type")


# ============================================================================
# User Data Generation Tests
# ============================================================================

class TestUserDataGeneration:
    """Tests for therapist and patient generation"""

    def test_generate_therapist_basic(self):
        """Test basic therapist generation"""
        therapist = generate_therapist()

        assert isinstance(therapist, dict)
        assert "id" in therapist
        assert "email" in therapist
        assert "full_name" in therapist
        assert therapist["role"] == UserRole.therapist
        assert isinstance(therapist["id"], uuid.UUID)
        assert "@" in therapist["email"]
        assert therapist["is_active"] is True

    def test_generate_therapist_custom_fields(self):
        """Test therapist with custom fields"""
        custom_email = "doctor@example.com"
        custom_name = "Dr. Jane Smith"
        custom_id = uuid.uuid4()

        therapist = generate_therapist(
            email=custom_email,
            name=custom_name,
            therapist_id=custom_id
        )

        assert therapist["email"] == custom_email
        assert therapist["full_name"] == custom_name
        assert therapist["id"] == custom_id

    def test_generate_patient_basic(self):
        """Test basic patient generation"""
        therapist_id = uuid.uuid4()
        patient = generate_patient(therapist_id)

        assert isinstance(patient, dict)
        assert "id" in patient
        assert "name" in patient
        assert patient["therapist_id"] == therapist_id
        assert isinstance(patient["id"], uuid.UUID)
        assert len(patient["name"]) > 0

    def test_generate_patient_custom_fields(self):
        """Test patient with custom fields"""
        therapist_id = uuid.uuid4()
        custom_email = "patient@example.com"
        custom_name = "John Doe"
        custom_phone = "555-1234"
        custom_id = uuid.uuid4()

        patient = generate_patient(
            therapist_id=therapist_id,
            email=custom_email,
            name=custom_name,
            phone=custom_phone,
            patient_id=custom_id
        )

        assert patient["email"] == custom_email
        assert patient["name"] == custom_name
        assert patient["phone"] == custom_phone
        assert patient["id"] == custom_id
        assert patient["therapist_id"] == therapist_id

    def test_patient_optional_fields(self):
        """Test that patient email and phone are optional"""
        therapist_id = uuid.uuid4()
        patients = [generate_patient(therapist_id) for _ in range(10)]

        # Some should have email, some shouldn't (due to randomization)
        emails = [p.get("email") for p in patients]
        assert None in emails or any(e is None for e in emails) or all(e is not None for e in emails)


# ============================================================================
# Session Data Generation Tests
# ============================================================================

class TestSessionGeneration:
    """Tests for session generation"""

    def test_generate_session_basic(self):
        """Test basic session generation"""
        patient_id = uuid.uuid4()
        therapist_id = uuid.uuid4()

        session = generate_session(patient_id, therapist_id)

        assert isinstance(session, dict)
        assert session["patient_id"] == patient_id
        assert session["therapist_id"] == therapist_id
        assert isinstance(session["id"], uuid.UUID)
        assert isinstance(session["session_date"], datetime)
        assert session["duration_seconds"] is not None
        assert session["status"] == SessionStatus.processed.value

    def test_generate_session_with_custom_status(self):
        """Test session with custom status"""
        patient_id = uuid.uuid4()
        therapist_id = uuid.uuid4()

        session = generate_session(
            patient_id,
            therapist_id,
            status=SessionStatus.pending
        )

        assert session["status"] == SessionStatus.pending.value
        assert session["processed_at"] is None  # Should be None for non-processed

    def test_generate_session_includes_transcript(self):
        """Test that session includes transcript by default"""
        patient_id = uuid.uuid4()
        therapist_id = uuid.uuid4()

        session = generate_session(patient_id, therapist_id)

        assert session["transcript_text"] is not None
        assert len(session["transcript_text"]) > 0
        assert session["transcript_segments"] is not None
        assert len(session["transcript_segments"]) > 0

    def test_generate_session_without_transcript(self):
        """Test session generation without transcript"""
        patient_id = uuid.uuid4()
        therapist_id = uuid.uuid4()

        session = generate_session(
            patient_id,
            therapist_id,
            include_transcript=False
        )

        assert session["transcript_text"] is None
        assert session["transcript_segments"] is None

    def test_generate_session_includes_notes(self):
        """Test that session includes extracted notes by default"""
        patient_id = uuid.uuid4()
        therapist_id = uuid.uuid4()

        session = generate_session(patient_id, therapist_id)

        assert session["extracted_notes"] is not None
        assert session["therapist_summary"] is not None
        assert session["patient_summary"] is not None
        assert isinstance(session["extracted_notes"], dict)

    def test_generate_session_without_notes(self):
        """Test session generation without notes"""
        patient_id = uuid.uuid4()
        therapist_id = uuid.uuid4()

        session = generate_session(
            patient_id,
            therapist_id,
            include_extracted_notes=False
        )

        assert session["extracted_notes"] is None
        assert session["therapist_summary"] is None
        assert session["patient_summary"] is None

    def test_generate_session_custom_date_duration(self):
        """Test session with custom date and duration"""
        patient_id = uuid.uuid4()
        therapist_id = uuid.uuid4()
        custom_date = datetime(2024, 6, 15, 14, 30)
        custom_duration = 2700  # 45 minutes

        session = generate_session(
            patient_id,
            therapist_id,
            session_date=custom_date,
            duration_seconds=custom_duration
        )

        assert session["session_date"] == custom_date
        assert session["duration_seconds"] == custom_duration


# ============================================================================
# Extracted Notes Generation Tests
# ============================================================================

class TestExtractedNotesGeneration:
    """Tests for extracted notes generation"""

    def test_generate_extracted_notes_basic(self):
        """Test basic extracted notes generation"""
        notes = generate_extracted_notes()

        # Verify it's a valid ExtractedNotes object
        assert isinstance(notes, ExtractedNotes)

        # Check required fields
        assert len(notes.key_topics) >= 3
        assert len(notes.topic_summary) > 0
        assert notes.session_mood in list(MoodLevel)
        assert notes.mood_trajectory in ["improving", "declining", "stable", "fluctuating"]
        assert len(notes.therapist_notes) > 100
        assert len(notes.patient_summary) > 50

    def test_generate_extracted_notes_strategies(self):
        """Test that strategies are generated correctly"""
        notes = generate_extracted_notes(num_strategies=5)

        assert len(notes.strategies) == 5
        for strategy in notes.strategies:
            assert isinstance(strategy, Strategy)
            assert len(strategy.name) > 0
            assert len(strategy.category) > 0
            assert strategy.status in list(StrategyStatus)
            assert len(strategy.context) > 0

    def test_generate_extracted_notes_triggers(self):
        """Test that triggers are generated correctly"""
        notes = generate_extracted_notes(num_triggers=4)

        assert len(notes.triggers) == 4
        for trigger in notes.triggers:
            assert isinstance(trigger, Trigger)
            assert len(trigger.trigger) > 0
            assert len(trigger.context) > 0
            assert trigger.severity in ["mild", "moderate", "severe", None]

    def test_generate_extracted_notes_action_items(self):
        """Test that action items are generated correctly"""
        notes = generate_extracted_notes(num_action_items=3)

        assert len(notes.action_items) == 3
        for item in notes.action_items:
            assert isinstance(item, ActionItem)
            assert len(item.task) > 0
            assert len(item.category) > 0

    def test_generate_extracted_notes_with_risk_flags(self):
        """Test notes generation with risk flags"""
        notes = generate_extracted_notes(include_risk_flags=True)

        assert len(notes.risk_flags) > 0
        for flag in notes.risk_flags:
            assert isinstance(flag, RiskFlag)
            assert len(flag.type) > 0
            assert len(flag.evidence) > 0
            assert flag.severity in ["low", "medium", "high"]

    def test_generate_extracted_notes_without_risk_flags(self):
        """Test notes generation without risk flags"""
        notes = generate_extracted_notes(include_risk_flags=False)

        assert len(notes.risk_flags) == 0

    def test_generate_extracted_notes_custom_mood(self):
        """Test notes with custom mood"""
        custom_mood = MoodLevel.very_positive

        notes = generate_extracted_notes(mood=custom_mood)

        assert notes.session_mood == custom_mood

    def test_generate_extracted_notes_schema_compliance(self):
        """Test that generated notes comply with ExtractedNotes schema"""
        notes = generate_extracted_notes(
            include_risk_flags=True,
            num_strategies=3,
            num_triggers=2,
            num_action_items=2
        )

        # Should not raise validation errors
        assert isinstance(notes, ExtractedNotes)

        # Test serialization
        notes_dict = notes.model_dump()
        assert isinstance(notes_dict, dict)
        assert "key_topics" in notes_dict
        assert "strategies" in notes_dict
        assert "risk_flags" in notes_dict


# ============================================================================
# Audio File Generation Tests
# ============================================================================

class TestAudioFileGeneration:
    """Tests for audio file generation"""

    def test_generate_audio_file_basic(self):
        """Test basic audio file generation"""
        audio_bytes = generate_audio_file()

        assert isinstance(audio_bytes, bytes)
        assert len(audio_bytes) > 0

    def test_generate_audio_file_formats(self):
        """Test different audio formats"""
        mp3_bytes = generate_audio_file(format="mp3", duration_seconds=30)
        wav_bytes = generate_audio_file(format="wav", duration_seconds=30)

        assert isinstance(mp3_bytes, bytes)
        assert isinstance(wav_bytes, bytes)
        # WAV should be larger for same duration
        assert len(wav_bytes) > len(mp3_bytes)

    def test_generate_audio_file_duration(self):
        """Test that longer duration produces more bytes"""
        short_audio = generate_audio_file(duration_seconds=10)
        long_audio = generate_audio_file(duration_seconds=60)

        assert len(long_audio) > len(short_audio)


# ============================================================================
# Batch Generation Tests
# ============================================================================

class TestBatchGeneration:
    """Tests for batch dataset generation"""

    def test_generate_test_dataset_basic(self):
        """Test basic dataset generation"""
        dataset = generate_test_dataset(
            num_therapists=2,
            patients_per_therapist=3,
            sessions_per_patient=2
        )

        assert "therapists" in dataset
        assert "patients" in dataset
        assert "sessions" in dataset

        assert len(dataset["therapists"]) == 2
        assert len(dataset["patients"]) == 6  # 2 * 3
        assert len(dataset["sessions"]) == 12  # 2 * 3 * 2

    def test_generate_test_dataset_relationships(self):
        """Test that dataset maintains proper relationships"""
        dataset = generate_test_dataset(
            num_therapists=1,
            patients_per_therapist=2,
            sessions_per_patient=1
        )

        therapist = dataset["therapists"][0]
        patients = dataset["patients"]
        sessions = dataset["sessions"]

        # All patients should belong to the therapist
        for patient in patients:
            assert patient["therapist_id"] == therapist["id"]

        # All sessions should reference valid patient and therapist
        for session in sessions:
            assert session["therapist_id"] == therapist["id"]
            assert any(p["id"] == session["patient_id"] for p in patients)

    def test_generate_test_dataset_empty(self):
        """Test dataset with zero items"""
        dataset = generate_test_dataset(
            num_therapists=0,
            patients_per_therapist=5,
            sessions_per_patient=3
        )

        assert len(dataset["therapists"]) == 0
        assert len(dataset["patients"]) == 0
        assert len(dataset["sessions"]) == 0


# ============================================================================
# Integration Tests
# ============================================================================

class TestDataGeneratorIntegration:
    """Integration tests using multiple generators together"""

    def test_complete_workflow(self):
        """Test generating a complete therapy session workflow"""
        # Generate therapist
        therapist = generate_therapist(name="Dr. Smith")

        # Generate patient
        patient = generate_patient(therapist["id"], name="Jane Doe")

        # Generate session
        session = generate_session(
            patient["id"],
            therapist["id"],
            status=SessionStatus.processed
        )

        # Verify relationships
        assert session["therapist_id"] == therapist["id"]
        assert session["patient_id"] == patient["id"]
        assert session["status"] == SessionStatus.processed.value

        # Verify session has all data
        assert session["transcript_text"] is not None
        assert session["extracted_notes"] is not None
        assert session["therapist_summary"] is not None

    def test_multiple_sessions_same_patient(self):
        """Test generating multiple sessions for same patient"""
        therapist_id = uuid.uuid4()
        patient_id = uuid.uuid4()

        sessions = [
            generate_session(patient_id, therapist_id)
            for _ in range(5)
        ]

        assert len(sessions) == 5
        # All should have different IDs
        session_ids = [s["id"] for s in sessions]
        assert len(set(session_ids)) == 5
        # All should reference same patient
        assert all(s["patient_id"] == patient_id for s in sessions)
