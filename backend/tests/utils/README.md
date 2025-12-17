# Test Data Generators

Comprehensive utilities for generating realistic test data for the TherapyBridge backend.

## Overview

The `data_generators.py` module provides functions to generate:
- **Therapy transcripts** with realistic dialog and customizable parameters
- **User data** (therapists and patients) with valid relationships
- **Session metadata** including transcripts and extracted notes
- **Extracted notes** matching the ExtractedNotes schema
- **Edge case data** for boundary testing
- **Complete test datasets** with hierarchical relationships

## Quick Start

```python
from tests.utils.data_generators import (
    generate_therapist,
    generate_patient,
    generate_session,
    generate_extracted_notes,
    generate_transcript,
)

# Generate a therapist
therapist = generate_therapist(name="Dr. Sarah Johnson")

# Generate a patient for that therapist
patient = generate_patient(
    therapist_id=therapist["id"],
    name="John Smith"
)

# Generate a complete session
session = generate_session(
    patient_id=patient["id"],
    therapist_id=therapist["id"]
)

# Session includes transcript, extracted notes, and all metadata
print(session["transcript_text"])
print(session["extracted_notes"]["key_topics"])
print(session["therapist_summary"])
```

## Generator Functions

### Transcript Generation

#### `generate_transcript()`
Generate realistic therapy dialog.

```python
# Basic usage
transcript = generate_transcript(
    num_segments=20,          # Number of back-and-forth exchanges
    duration_seconds=3600,    # Total duration (1 hour)
    include_timestamps=True,
    speaker_labels=True       # Include "Therapist:" and "Client:" labels
)

# Without speaker labels (raw text)
transcript = generate_transcript(speaker_labels=False)
```

#### `generate_transcript_segments()`
Generate transcript with timing information.

```python
segments = generate_transcript_segments(
    num_segments=30,
    duration_seconds=1800  # 30 minutes
)

# Each segment has start, end, text, and speaker
for seg in segments:
    print(f"[{seg.start:.2f}s - {seg.end:.2f}s] {seg.speaker}: {seg.text}")
```

#### `generate_edge_case_transcript()`
Generate edge case transcripts for testing boundaries.

```python
# Empty transcript
empty = generate_edge_case_transcript("empty")

# Very short (single word)
short = generate_edge_case_transcript("very_short")

# Very long (10000+ words)
long = generate_edge_case_transcript("very_long")

# Special characters and unicode
special = generate_edge_case_transcript("special_chars")

# No punctuation
no_punct = generate_edge_case_transcript("no_punctuation")

# Single speaker only
single = generate_edge_case_transcript("single_speaker")
```

### User Data Generation

#### `generate_therapist()`
Generate therapist user data.

```python
# Random therapist
therapist = generate_therapist()

# Custom therapist
therapist = generate_therapist(
    email="doctor@clinic.com",
    name="Dr. Emily Rodriguez",
    therapist_id=uuid.uuid4()  # Optional custom UUID
)

# Fields: id, email, full_name, role, hashed_password, created_at, etc.
```

#### `generate_patient()`
Generate patient data with therapist relationship.

```python
therapist_id = uuid.uuid4()

# Random patient
patient = generate_patient(therapist_id)

# Custom patient
patient = generate_patient(
    therapist_id=therapist_id,
    email="patient@example.com",
    name="Michael Chen",
    phone="555-0123",
    patient_id=uuid.uuid4()
)

# Email and phone are randomly included/excluded if not specified
```

### Session Data Generation

#### `generate_session()`
Generate complete session with all metadata.

```python
patient_id = uuid.uuid4()
therapist_id = uuid.uuid4()

# Full session (default includes transcript and notes)
session = generate_session(patient_id, therapist_id)

# Custom session
session = generate_session(
    patient_id=patient_id,
    therapist_id=therapist_id,
    session_id=uuid.uuid4(),
    status=SessionStatus.processed,
    session_date=datetime(2024, 6, 15, 10, 0),
    duration_seconds=3600,
    include_transcript=True,
    include_extracted_notes=True
)

# Session without transcript (e.g., for testing pending status)
pending_session = generate_session(
    patient_id,
    therapist_id,
    status=SessionStatus.pending,
    include_transcript=False,
    include_extracted_notes=False
)
```

### Extracted Notes Generation

#### `generate_extracted_notes()`
Generate AI-extracted notes matching the schema.

```python
# Basic notes
notes = generate_extracted_notes()

# Custom notes with risk flags
notes = generate_extracted_notes(
    include_risk_flags=True,
    mood=MoodLevel.low,
    num_strategies=5,
    num_triggers=3,
    num_action_items=4
)

# Notes object includes:
# - key_topics (list)
# - strategies (list of Strategy objects)
# - triggers (list of Trigger objects)
# - action_items (list of ActionItem objects)
# - session_mood (MoodLevel enum)
# - mood_trajectory (string)
# - risk_flags (list of RiskFlag objects)
# - therapist_notes (string)
# - patient_summary (string)
# - emotional_themes, significant_quotes, etc.

# Convert to dict for JSON storage
notes_dict = notes.model_dump()
```

### Audio File Generation

#### `generate_audio_file()`
Generate mock audio file bytes.

**NOTE:** This generates random bytes, not actual audio. Use real audio files for audio processing tests.

```python
# MP3 file (compressed)
mp3_bytes = generate_audio_file(
    format="mp3",
    duration_seconds=1800,  # 30 minutes
)

# WAV file (uncompressed, larger)
wav_bytes = generate_audio_file(
    format="wav",
    duration_seconds=1800,
    sample_rate=16000
)

# Use in file upload tests
from io import BytesIO
audio_file = BytesIO(mp3_bytes)
```

### Batch Generation

#### `generate_test_dataset()`
Generate a complete hierarchical dataset.

```python
# Generate 2 therapists, each with 5 patients, each with 3 sessions
dataset = generate_test_dataset(
    num_therapists=2,
    patients_per_therapist=5,
    sessions_per_patient=3
)

# Returns:
# {
#   "therapists": [therapist1, therapist2],
#   "patients": [patient1, patient2, ...],  # 10 patients
#   "sessions": [session1, session2, ...]   # 30 sessions
# }

# All relationships are properly maintained
therapists = dataset["therapists"]
patients = dataset["patients"]
sessions = dataset["sessions"]
```

## Usage Examples

### Example 1: Testing Session Creation

```python
import pytest
from tests.utils.data_generators import generate_therapist, generate_patient, generate_session

@pytest.mark.asyncio
async def test_create_session(db: AsyncSession):
    # Generate test data
    therapist = generate_therapist()
    patient = generate_patient(therapist["id"])

    # Create DB records (simplified)
    # ... insert therapist and patient into DB ...

    # Generate session data
    session_data = generate_session(
        patient_id=patient["id"],
        therapist_id=therapist["id"],
        status=SessionStatus.pending,
        include_transcript=False,
        include_extracted_notes=False
    )

    # Test session creation endpoint
    response = await client.post("/sessions", json=session_data)
    assert response.status_code == 201
```

### Example 2: Testing Note Extraction

```python
from tests.utils.data_generators import generate_transcript, generate_extracted_notes

@pytest.mark.asyncio
async def test_note_extraction_service():
    # Generate realistic transcript
    transcript = generate_transcript(num_segments=25, duration_seconds=3000)

    # Test extraction service
    extracted = await extraction_service.extract_notes(transcript)

    # Verify structure matches expected schema
    expected = generate_extracted_notes()
    assert "key_topics" in extracted
    assert "strategies" in extracted
    assert len(extracted["therapist_notes"]) > 100
```

### Example 3: Testing Edge Cases

```python
from tests.utils.data_generators import generate_edge_case_transcript

@pytest.mark.parametrize("case_type", [
    "empty",
    "very_short",
    "very_long",
    "special_chars",
    "no_punctuation",
    "single_speaker"
])
def test_transcript_edge_cases(case_type):
    transcript = generate_edge_case_transcript(case_type)

    # Test that system handles edge case gracefully
    result = process_transcript(transcript)
    assert result is not None or result == expected_error
```

### Example 4: Populating Test Database

```python
from tests.utils.data_generators import generate_test_dataset

@pytest.fixture
async def populated_db(db: AsyncSession):
    """Fixture that provides a database with test data"""

    # Generate comprehensive dataset
    dataset = generate_test_dataset(
        num_therapists=3,
        patients_per_therapist=10,
        sessions_per_patient=5
    )

    # Insert into database
    for therapist in dataset["therapists"]:
        db.add(User(**therapist))

    for patient in dataset["patients"]:
        db.add(Patient(**patient))

    for session in dataset["sessions"]:
        db.add(Session(**session))

    await db.commit()

    return dataset
```

### Example 5: Testing with Custom Data

```python
def test_high_risk_session():
    # Generate notes with risk flags
    notes = generate_extracted_notes(
        include_risk_flags=True,
        mood=MoodLevel.very_low,
        num_strategies=2,
        num_triggers=4
    )

    # Verify risk assessment logic
    assert len(notes.risk_flags) > 0
    assert any(flag.severity == "high" for flag in notes.risk_flags)

    # Test alert system
    should_alert = check_risk_alerts(notes)
    assert should_alert is True
```

## Schema Compliance

All generators produce data that complies with the schemas defined in `app/models/schemas.py`:

- `generate_therapist()` → matches User model (role=therapist)
- `generate_patient()` → matches Patient model
- `generate_session()` → matches Session model
- `generate_extracted_notes()` → matches ExtractedNotes schema
- `generate_transcript_segments()` → matches TranscriptSegment schema

Run the test suite to verify schema compliance:

```bash
cd backend
source venv/bin/activate
pytest tests/test_data_generators.py -v
```

## Tips and Best Practices

### 1. Use Realistic Data
The generators use the `faker` library to create realistic names, emails, and text. This helps catch issues that wouldn't appear with simple test strings like "test1", "test2".

### 2. Customize When Needed
All generators support optional parameters. Use them to test specific scenarios:

```python
# Test long session
long_session = generate_session(
    patient_id, therapist_id,
    duration_seconds=7200  # 2 hours
)

# Test session with no notes
minimal_session = generate_session(
    patient_id, therapist_id,
    include_extracted_notes=False
)
```

### 3. Test Edge Cases
Always include edge case tests:

```python
@pytest.mark.parametrize("transcript", [
    generate_edge_case_transcript("empty"),
    generate_edge_case_transcript("very_long"),
    generate_edge_case_transcript("special_chars"),
])
def test_handles_edge_cases(transcript):
    # Your test logic
    pass
```

### 4. Maintain Relationships
When testing multi-entity operations, use the batch generator to maintain proper relationships:

```python
dataset = generate_test_dataset(num_therapists=1, patients_per_therapist=3, sessions_per_patient=2)

# All relationships are guaranteed to be valid
therapist = dataset["therapists"][0]
patients = dataset["patients"]  # All belong to therapist
sessions = dataset["sessions"]  # All reference valid patient+therapist
```

### 5. Seed for Reproducibility
The generators are seeded for reproducible tests:

```python
from faker import Faker
Faker.seed(12345)  # Use specific seed for reproducible test data
```

## Requirements

Add `faker` to your requirements.txt:

```bash
# Testing
faker>=20.0.0  # Realistic test data generation
```

Install:

```bash
pip install faker
```

## Running Tests

```bash
# Run all data generator tests
pytest tests/test_data_generators.py -v

# Run specific test class
pytest tests/test_data_generators.py::TestTranscriptGeneration -v

# Run with coverage
pytest tests/test_data_generators.py --cov=tests.utils.data_generators
```

## Contributing

When adding new generators:

1. Add the function to `data_generators.py`
2. Add comprehensive tests to `test_data_generators.py`
3. Add usage examples to this README
4. Ensure schema compliance (validate with Pydantic models)
5. Support customization through optional parameters
6. Use realistic data from `faker` library

## Support

For issues or questions about test data generators, see:
- Test suite: `tests/test_data_generators.py`
- Schema definitions: `app/models/schemas.py`
- Database models: `app/models/db_models.py`
