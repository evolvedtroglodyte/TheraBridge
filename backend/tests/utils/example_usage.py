"""
Example usage of data generators.

This file demonstrates practical use cases for the data generator functions.
You can run this file directly to see example output.

Run with:
    cd backend
    source venv/bin/activate
    python -m tests.utils.example_usage
"""

import json
import uuid
from datetime import datetime

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

from app.models.schemas import MoodLevel, SessionStatus


def example_1_basic_transcript():
    """Example 1: Generate a basic therapy transcript"""
    print("=" * 80)
    print("EXAMPLE 1: Basic Therapy Transcript")
    print("=" * 80)

    transcript = generate_transcript(
        num_segments=5,
        duration_seconds=600,
        speaker_labels=True
    )

    print(transcript)
    print("\n" + "=" * 80 + "\n")


def example_2_transcript_segments():
    """Example 2: Generate transcript with timing information"""
    print("=" * 80)
    print("EXAMPLE 2: Transcript Segments with Timing")
    print("=" * 80)

    segments = generate_transcript_segments(
        num_segments=10,
        duration_seconds=600
    )

    for i, seg in enumerate(segments[:5], 1):  # Show first 5
        print(f"\nSegment {i}:")
        print(f"  Time: {seg.start:.2f}s - {seg.end:.2f}s")
        print(f"  Speaker: {seg.speaker}")
        print(f"  Text: {seg.text}")

    print(f"\n... and {len(segments) - 5} more segments")
    print("\n" + "=" * 80 + "\n")


def example_3_edge_cases():
    """Example 3: Generate edge case transcripts"""
    print("=" * 80)
    print("EXAMPLE 3: Edge Case Transcripts")
    print("=" * 80)

    cases = {
        "Empty": generate_edge_case_transcript("empty"),
        "Very Short": generate_edge_case_transcript("very_short"),
        "Special Characters": generate_edge_case_transcript("special_chars")[:500],  # First 500 chars
        "No Punctuation": generate_edge_case_transcript("no_punctuation")[:300],
        "Single Speaker": generate_edge_case_transcript("single_speaker")[:400],
    }

    for case_name, transcript in cases.items():
        print(f"\n{case_name}:")
        print(f"  Length: {len(transcript)} characters")
        if len(transcript) > 0:
            preview = transcript[:200] + "..." if len(transcript) > 200 else transcript
            print(f"  Preview: {preview}")
        else:
            print(f"  Preview: (empty)")

    # Very long is too big to print
    very_long = generate_edge_case_transcript("very_long")
    print(f"\nVery Long:")
    print(f"  Length: {len(very_long)} characters")
    print(f"  Word count: ~{len(very_long.split())} words")

    print("\n" + "=" * 80 + "\n")


def example_4_user_data():
    """Example 4: Generate therapist and patient data"""
    print("=" * 80)
    print("EXAMPLE 4: User Data Generation")
    print("=" * 80)

    # Generate therapist
    therapist = generate_therapist(
        name="Dr. Sarah Johnson",
        email="sjohnson@clinic.com"
    )

    print("\nTherapist:")
    print(f"  ID: {therapist['id']}")
    print(f"  Name: {therapist['full_name']}")
    print(f"  Email: {therapist['email']}")
    print(f"  Role: {therapist['role']}")
    print(f"  Created: {therapist['created_at']}")

    # Generate patients
    print("\nPatients:")
    for i in range(3):
        patient = generate_patient(therapist['id'])
        print(f"\n  Patient {i+1}:")
        print(f"    ID: {patient['id']}")
        print(f"    Name: {patient['name']}")
        print(f"    Email: {patient['email']}")
        print(f"    Phone: {patient['phone']}")
        print(f"    Therapist: {patient['therapist_id']}")

    print("\n" + "=" * 80 + "\n")


def example_5_session_data():
    """Example 5: Generate complete session data"""
    print("=" * 80)
    print("EXAMPLE 5: Complete Session Data")
    print("=" * 80)

    patient_id = uuid.uuid4()
    therapist_id = uuid.uuid4()

    session = generate_session(
        patient_id=patient_id,
        therapist_id=therapist_id,
        status=SessionStatus.processed,
        duration_seconds=3600
    )

    print("\nSession Metadata:")
    print(f"  ID: {session['id']}")
    print(f"  Patient: {session['patient_id']}")
    print(f"  Therapist: {session['therapist_id']}")
    print(f"  Date: {session['session_date']}")
    print(f"  Duration: {session['duration_seconds']}s ({session['duration_seconds']//60} minutes)")
    print(f"  Status: {session['status']}")
    print(f"  Audio File: {session['audio_filename']}")

    print("\nTranscript Preview:")
    transcript_preview = session['transcript_text'][:300]
    print(f"  {transcript_preview}...")

    print("\nExtracted Notes Preview:")
    notes = session['extracted_notes']
    print(f"  Key Topics: {notes['key_topics'][:2]}")
    print(f"  Session Mood: {notes['session_mood']}")
    print(f"  Strategies: {len(notes['strategies'])} strategies")
    print(f"  Action Items: {len(notes['action_items'])} items")

    print("\nTherapist Summary:")
    print(f"  {session['therapist_summary'][:200]}...")

    print("\n" + "=" * 80 + "\n")


def example_6_extracted_notes():
    """Example 6: Generate detailed extracted notes"""
    print("=" * 80)
    print("EXAMPLE 6: Extracted Notes Details")
    print("=" * 80)

    notes = generate_extracted_notes(
        include_risk_flags=True,
        mood=MoodLevel.low,
        num_strategies=3,
        num_triggers=2,
        num_action_items=2
    )

    print("\nKey Topics:")
    for topic in notes.key_topics:
        print(f"  - {topic}")

    print(f"\nTopic Summary:")
    print(f"  {notes.topic_summary}")

    print("\nStrategies:")
    for strategy in notes.strategies:
        print(f"\n  • {strategy.name} ({strategy.category})")
        print(f"    Status: {strategy.status.value}")
        print(f"    Context: {strategy.context}")

    print("\nTriggers:")
    for trigger in notes.triggers:
        print(f"\n  • {trigger.trigger}")
        print(f"    Severity: {trigger.severity}")
        print(f"    Context: {trigger.context}")

    print("\nAction Items:")
    for item in notes.action_items:
        print(f"\n  • {item.task}")
        print(f"    Category: {item.category}")
        print(f"    Details: {item.details}")

    print("\nEmotional Themes:")
    for theme in notes.emotional_themes:
        print(f"  - {theme}")

    print(f"\nMood Assessment:")
    print(f"  Current Mood: {notes.session_mood.value}")
    print(f"  Trajectory: {notes.mood_trajectory}")

    if notes.risk_flags:
        print("\nRisk Flags:")
        for flag in notes.risk_flags:
            print(f"\n  ⚠️  {flag.type} (Severity: {flag.severity})")
            print(f"      Evidence: {flag.evidence}")

    print("\nTherapist Notes:")
    print(f"  {notes.therapist_notes}")

    print("\nPatient Summary:")
    print(f"  {notes.patient_summary}")

    print("\n" + "=" * 80 + "\n")


def example_7_test_dataset():
    """Example 7: Generate complete test dataset"""
    print("=" * 80)
    print("EXAMPLE 7: Complete Test Dataset")
    print("=" * 80)

    dataset = generate_test_dataset(
        num_therapists=2,
        patients_per_therapist=3,
        sessions_per_patient=2
    )

    print(f"\nDataset Summary:")
    print(f"  Therapists: {len(dataset['therapists'])}")
    print(f"  Patients: {len(dataset['patients'])}")
    print(f"  Sessions: {len(dataset['sessions'])}")

    print("\nTherapists:")
    for therapist in dataset['therapists']:
        print(f"  - {therapist['full_name']} ({therapist['email']})")

        # Show patients for this therapist
        therapist_patients = [
            p for p in dataset['patients']
            if p['therapist_id'] == therapist['id']
        ]
        print(f"    Patients: {len(therapist_patients)}")
        for patient in therapist_patients:
            print(f"      • {patient['name']}")

            # Show sessions for this patient
            patient_sessions = [
                s for s in dataset['sessions']
                if s['patient_id'] == patient['id']
            ]
            print(f"        Sessions: {len(patient_sessions)}")
            for session in patient_sessions:
                print(f"          - {session['session_date'].strftime('%Y-%m-%d')} "
                      f"({session['duration_seconds']//60}min, {session['status']})")

    print("\n" + "=" * 80 + "\n")


def example_8_audio_files():
    """Example 8: Generate mock audio files"""
    print("=" * 80)
    print("EXAMPLE 8: Mock Audio File Generation")
    print("=" * 80)

    formats = ["mp3", "wav", "m4a"]
    durations = [30, 300, 1800]  # 30s, 5min, 30min

    print("\nAudio File Sizes:\n")
    print(f"{'Format':<10} {'Duration':<12} {'Size (KB)':<12} {'Size (MB)':<12}")
    print("-" * 50)

    for format in formats:
        for duration in durations:
            audio_bytes = generate_audio_file(
                format=format,
                duration_seconds=duration
            )
            size_kb = len(audio_bytes) / 1024
            size_mb = size_kb / 1024

            duration_str = f"{duration}s"
            if duration >= 60:
                duration_str = f"{duration//60}min"

            print(f"{format:<10} {duration_str:<12} {size_kb:<12.1f} {size_mb:<12.2f}")

    print("\nNote: These are random bytes, not actual audio data.")
    print("Use real audio files for audio processing tests.")

    print("\n" + "=" * 80 + "\n")


def example_9_json_export():
    """Example 9: Export data as JSON"""
    print("=" * 80)
    print("EXAMPLE 9: JSON Export")
    print("=" * 80)

    # Generate data
    therapist = generate_therapist(name="Dr. Michael Chen")
    patient = generate_patient(therapist['id'], name="Jane Smith")
    session = generate_session(patient['id'], therapist['id'])

    # Convert to JSON-serializable format
    def make_serializable(obj):
        """Convert UUID and datetime objects to strings"""
        if isinstance(obj, uuid.UUID):
            return str(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {k: make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [make_serializable(item) for item in obj]
        return obj

    # Export as JSON
    export_data = {
        "therapist": make_serializable(therapist),
        "patient": make_serializable(patient),
        "session": make_serializable(session),
    }

    json_output = json.dumps(export_data, indent=2)

    print("\nJSON Export (first 1000 characters):")
    print(json_output[:1000] + "...")

    print(f"\nTotal JSON size: {len(json_output)} characters")
    print("Full JSON can be saved to a file for test fixtures")

    print("\n" + "=" * 80 + "\n")


def example_10_custom_scenarios():
    """Example 10: Custom testing scenarios"""
    print("=" * 80)
    print("EXAMPLE 10: Custom Testing Scenarios")
    print("=" * 80)

    # Scenario 1: High-risk session
    print("\nScenario 1: High-Risk Session")
    print("-" * 40)
    high_risk_notes = generate_extracted_notes(
        include_risk_flags=True,
        mood=MoodLevel.very_low,
        num_triggers=4
    )
    print(f"Mood: {high_risk_notes.session_mood.value}")
    print(f"Risk Flags: {len(high_risk_notes.risk_flags)}")
    if high_risk_notes.risk_flags:
        for flag in high_risk_notes.risk_flags:
            print(f"  - {flag.type}: {flag.severity} severity")

    # Scenario 2: Progress session (improving)
    print("\nScenario 2: Progress Session")
    print("-" * 40)
    progress_notes = generate_extracted_notes(
        include_risk_flags=False,
        mood=MoodLevel.positive,
        num_strategies=5
    )
    print(f"Mood: {progress_notes.session_mood.value}")
    print(f"Strategies: {len(progress_notes.strategies)}")
    print(f"Trajectory: {progress_notes.mood_trajectory}")

    # Scenario 3: Initial assessment (many triggers identified)
    print("\nScenario 3: Initial Assessment")
    print("-" * 40)
    assessment_notes = generate_extracted_notes(
        mood=MoodLevel.low,
        num_triggers=5,
        num_action_items=3
    )
    print(f"Triggers Identified: {len(assessment_notes.triggers)}")
    print(f"Action Items: {len(assessment_notes.action_items)}")

    # Scenario 4: Minimal session (short check-in)
    print("\nScenario 4: Brief Check-in Session")
    print("-" * 40)
    brief_session = generate_session(
        patient_id=uuid.uuid4(),
        therapist_id=uuid.uuid4(),
        duration_seconds=900  # 15 minutes
    )
    print(f"Duration: {brief_session['duration_seconds']//60} minutes")
    print(f"Transcript length: {len(brief_session['transcript_text'])} characters")

    # Scenario 5: Long intensive session
    print("\nScenario 5: Long Intensive Session")
    print("-" * 40)
    intensive_session = generate_session(
        patient_id=uuid.uuid4(),
        therapist_id=uuid.uuid4(),
        duration_seconds=7200  # 2 hours
    )
    print(f"Duration: {intensive_session['duration_seconds']//60} minutes")
    print(f"Transcript length: {len(intensive_session['transcript_text'])} characters")
    print(f"Transcript segments: {len(intensive_session['transcript_segments'])}")

    print("\n" + "=" * 80 + "\n")


def main():
    """Run all examples"""
    print("\n")
    print("=" * 80)
    print("DATA GENERATOR USAGE EXAMPLES")
    print("=" * 80)
    print("\n")

    examples = [
        example_1_basic_transcript,
        example_2_transcript_segments,
        example_3_edge_cases,
        example_4_user_data,
        example_5_session_data,
        example_6_extracted_notes,
        example_7_test_dataset,
        example_8_audio_files,
        example_9_json_export,
        example_10_custom_scenarios,
    ]

    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"\nERROR in {example.__name__}: {e}")
            import traceback
            traceback.print_exc()
            print("\n" + "=" * 80 + "\n")

    print("=" * 80)
    print("ALL EXAMPLES COMPLETED")
    print("=" * 80)
    print("\n")


if __name__ == "__main__":
    main()
