# Test Data Generators - Quick Reference

## Installation
```bash
pip install faker>=20.0.0
```

## Import
```python
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
```

## Quick Examples

### Transcripts
```python
# Basic transcript
transcript = generate_transcript(num_segments=20, duration_seconds=3600)

# With timing
segments = generate_transcript_segments(num_segments=30, duration_seconds=1800)

# Edge cases
empty = generate_edge_case_transcript("empty")
long = generate_edge_case_transcript("very_long")
special = generate_edge_case_transcript("special_chars")
```

### Users
```python
# Therapist
therapist = generate_therapist(name="Dr. Smith", email="smith@clinic.com")

# Patient
patient = generate_patient(therapist_id=therapist["id"], name="Jane Doe")
```

### Sessions
```python
# Full session with transcript and notes
session = generate_session(patient_id, therapist_id)

# Pending session (no transcript/notes)
session = generate_session(
    patient_id, therapist_id,
    status=SessionStatus.pending,
    include_transcript=False,
    include_extracted_notes=False
)
```

### Extracted Notes
```python
# Basic notes
notes = generate_extracted_notes()

# High-risk session
notes = generate_extracted_notes(
    include_risk_flags=True,
    mood=MoodLevel.very_low
)

# Many strategies
notes = generate_extracted_notes(num_strategies=5)
```

### Batch Generation
```python
# Complete dataset
dataset = generate_test_dataset(
    num_therapists=2,
    patients_per_therapist=5,
    sessions_per_patient=3
)

therapists = dataset["therapists"]
patients = dataset["patients"]
sessions = dataset["sessions"]
```

## Common Patterns

### Test Session Creation
```python
therapist = generate_therapist()
patient = generate_patient(therapist["id"])
session = generate_session(patient["id"], therapist["id"])
```

### Test with Edge Cases
```python
@pytest.mark.parametrize("case_type", [
    "empty", "very_short", "very_long", "special_chars"
])
def test_edge_cases(case_type):
    transcript = generate_edge_case_transcript(case_type)
    result = process_transcript(transcript)
```

### Populate Test Database
```python
dataset = generate_test_dataset(num_therapists=3, patients_per_therapist=5)
for therapist in dataset["therapists"]:
    db.add(User(**therapist))
for patient in dataset["patients"]:
    db.add(Patient(**patient))
for session in dataset["sessions"]:
    db.add(Session(**session))
await db.commit()
```

## Edge Case Types
- `"empty"` - Empty string
- `"very_short"` - Single word
- `"very_long"` - 10000+ words
- `"special_chars"` - Unicode/emoji
- `"no_punctuation"` - No punctuation
- `"single_speaker"` - Only therapist

## Run Tests
```bash
pytest tests/test_data_generators.py -v
```

## Run Examples
```bash
python -m tests.utils.example_usage
```

## Documentation
- Full docs: `tests/utils/README.md`
- Summary: `tests/utils/GENERATOR_SUMMARY.md`
- Examples: `tests/utils/example_usage.py`
