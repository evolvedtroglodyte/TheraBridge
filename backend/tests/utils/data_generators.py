"""
Test data generators for creating realistic therapy session data.

This module provides utilities for generating:
- Realistic therapy transcripts with configurable parameters
- User data (therapists and patients)
- Session metadata
- Extracted notes matching the ExtractedNotes schema
- Mock audio file data
- Edge case data for testing boundary conditions

All generators use the faker library for realistic data and support
customization through parameters.
"""

import random
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from faker import Faker

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

# Initialize faker for realistic data generation
fake = Faker()
Faker.seed(0)  # Seed for reproducibility in tests


# ============================================================================
# Transcript Generation
# ============================================================================

def generate_transcript(
    num_segments: int = 10,
    duration_seconds: int = 600,
    include_timestamps: bool = True,
    speaker_labels: bool = True,
) -> str:
    """
    Generate a realistic therapy session transcript.

    Args:
        num_segments: Number of dialog exchanges (back-and-forth)
        duration_seconds: Total duration of session in seconds
        include_timestamps: Whether to include timestamp markers
        speaker_labels: Whether to label speakers as "Therapist" and "Client"

    Returns:
        String containing the generated transcript

    Example:
        >>> transcript = generate_transcript(num_segments=5, duration_seconds=300)
        >>> print(transcript)
        Therapist: How have you been feeling this week?
        Client: It's been challenging...
    """
    # Therapy conversation templates
    therapist_openers = [
        "How have you been feeling this week?",
        "What's been on your mind since our last session?",
        "I'd like to check in about how you're doing.",
        "Tell me about your week.",
        "What would you like to focus on today?",
    ]

    therapist_follow_ups = [
        "Can you tell me more about that?",
        "How did that make you feel?",
        "What was going through your mind at that time?",
        "That sounds challenging. How are you coping with it?",
        "What do you think might help with this?",
        "Have you noticed any patterns with this?",
        "Let's explore that a bit more.",
        "How does that connect to what we discussed before?",
    ]

    therapist_interventions = [
        "Let's try a grounding technique. Can you name five things you can see right now?",
        "I'd like to introduce a cognitive restructuring exercise.",
        "Have you tried the breathing technique we discussed?",
        "What evidence do you have for that thought?",
        "What would you tell a friend in this situation?",
        "Let's identify what's within your control here.",
        "How might you reframe that thought?",
    ]

    client_responses = [
        "It's been really difficult. I've been feeling overwhelmed with work.",
        "I had a panic attack on Tuesday. It came out of nowhere.",
        "I tried the breathing exercises, and they helped a little.",
        "I keep worrying about what people think of me.",
        "My sleep has been terrible. I wake up at 3am every night.",
        "I had a good day yesterday, but then today was harder again.",
        "I feel like I'm not making any progress.",
        "My partner and I had an argument, and I can't stop thinking about it.",
        "I'm starting to notice those patterns you mentioned.",
        "That makes sense. I never thought about it that way.",
    ]

    segments = []
    time_per_segment = duration_seconds / (num_segments * 2)  # 2 speakers per segment
    current_time = 0.0

    for i in range(num_segments):
        # Therapist speaks
        if i == 0:
            therapist_text = random.choice(therapist_openers)
        elif i % 3 == 0:
            therapist_text = random.choice(therapist_interventions)
        else:
            therapist_text = random.choice(therapist_follow_ups)

        if speaker_labels:
            segments.append(f"Therapist: {therapist_text}")
        else:
            segments.append(therapist_text)

        if include_timestamps:
            current_time += time_per_segment

        # Client responds
        client_text = random.choice(client_responses)
        if speaker_labels:
            segments.append(f"Client: {client_text}")
        else:
            segments.append(client_text)

        if include_timestamps:
            current_time += time_per_segment

    return "\n\n".join(segments)


def generate_transcript_segments(
    num_segments: int = 20,
    duration_seconds: int = 600,
) -> List[TranscriptSegment]:
    """
    Generate transcript segments with timing and speaker information.

    Args:
        num_segments: Number of speaking segments
        duration_seconds: Total duration in seconds

    Returns:
        List of TranscriptSegment objects

    Example:
        >>> segments = generate_transcript_segments(num_segments=10, duration_seconds=300)
        >>> print(segments[0].speaker, segments[0].text[:50])
        Therapist How have you been feeling this week?
    """
    segments = []
    time_per_segment = duration_seconds / num_segments
    current_time = 0.0

    therapist_lines = [
        "How have you been feeling this week?",
        "Can you tell me more about that?",
        "What was going through your mind?",
        "How did that make you feel?",
        "Let's try a breathing exercise.",
        "What patterns have you noticed?",
    ]

    client_lines = [
        "It's been a difficult week with work stress.",
        "I've been feeling anxious about the upcoming presentation.",
        "I tried the techniques we discussed, and they helped.",
        "I'm still struggling with negative thoughts.",
        "My sleep has improved a bit.",
        "I had a panic attack on Wednesday.",
    ]

    for i in range(num_segments):
        is_therapist = i % 2 == 0
        speaker = "Therapist" if is_therapist else "Client"
        text = random.choice(therapist_lines if is_therapist else client_lines)

        start_time = current_time
        segment_duration = random.uniform(time_per_segment * 0.5, time_per_segment * 1.5)
        end_time = start_time + segment_duration

        segments.append(
            TranscriptSegment(
                start=round(start_time, 2),
                end=round(end_time, 2),
                text=text,
                speaker=speaker,
            )
        )

        current_time = end_time

    return segments


def generate_edge_case_transcript(case_type: str = "empty") -> str:
    """
    Generate edge case transcripts for testing boundary conditions.

    Args:
        case_type: Type of edge case
            - "empty": Empty string
            - "very_short": Single word
            - "very_long": Extremely long transcript (10000+ words)
            - "special_chars": Contains special characters and unicode
            - "no_punctuation": No punctuation marks
            - "single_speaker": Only one speaker throughout

    Returns:
        Edge case transcript string

    Example:
        >>> empty = generate_edge_case_transcript("empty")
        >>> assert empty == ""
        >>> special = generate_edge_case_transcript("special_chars")
        >>> assert "émotions" in special or "😊" in special
    """
    if case_type == "empty":
        return ""

    elif case_type == "very_short":
        return "Hello"

    elif case_type == "very_long":
        # Generate a very long transcript (10000+ words)
        segments = []
        for _ in range(500):  # 500 exchanges = ~10000+ words
            segments.append(f"Therapist: {fake.sentence(nb_words=20)}")
            segments.append(f"Client: {fake.sentence(nb_words=20)}")
        return "\n\n".join(segments)

    elif case_type == "special_chars":
        return """Therapist: How are you feeling about the situation with your mère?

Client: It's compliqué... I feel like 😊 sometimes but 😢 other times. The émotions are très intense!

Therapist: Those mixed feelings are valid. Let's explore: what triggers the positive moments vs. the difficult ones?

Client: Well, when we talk about "normal" things—like cooking or the weather—c'est bon. But topics like my career? ¡Ay no! She says things like "Why can't you be more like [sibling]?" & it hurts.

Therapist: That comparison must be painful. How do you typically respond when she says that?

Client: I usually just say "Okay, mom" → then leave. Sometimes I want to scream but I don't... (sigh)"""

    elif case_type == "no_punctuation":
        return """Therapist how have you been this week

Client its been really hard I dont know what to do anymore everything feels overwhelming

Therapist I hear that youre struggling What specifically has been most difficult

Client work mostly my boss keeps adding more tasks and I cant keep up Im not sleeping well either

Therapist sleep problems often make everything feel harder Have you tried any of the relaxation techniques we discussed

Client I tried once but I gave up I dont think anything will help"""

    elif case_type == "single_speaker":
        segments = []
        for _ in range(10):
            segments.append(f"Therapist: {fake.sentence(nb_words=15)}")
        return "\n\n".join(segments)

    else:
        raise ValueError(f"Unknown edge case type: {case_type}")


# ============================================================================
# User Data Generation
# ============================================================================

def generate_therapist(
    email: Optional[str] = None,
    name: Optional[str] = None,
    therapist_id: Optional[uuid.UUID] = None,
) -> Dict[str, Any]:
    """
    Generate therapist user data.

    Args:
        email: Optional email (generates random if not provided)
        name: Optional full name (generates random if not provided)
        therapist_id: Optional UUID (generates random if not provided)

    Returns:
        Dictionary with therapist data matching User model

    Example:
        >>> therapist = generate_therapist()
        >>> assert therapist["role"] == UserRole.therapist
        >>> assert "@" in therapist["email"]
    """
    return {
        "id": therapist_id or uuid.uuid4(),
        "email": email or fake.email(),
        "full_name": name or fake.name(),
        "name": name or fake.name(),
        "role": UserRole.therapist,
        "is_active": True,
        "hashed_password": "$2b$12$KIXvBT7H1ImUQdqDKwJDxORvNHY3qRGlzQHpXzJ6L4EqJxGGKRpOy",  # "password123"
        "created_at": datetime.utcnow() - timedelta(days=random.randint(30, 365)),
        "updated_at": datetime.utcnow(),
    }


def generate_patient(
    therapist_id: uuid.UUID,
    email: Optional[str] = None,
    name: Optional[str] = None,
    patient_id: Optional[uuid.UUID] = None,
    phone: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate patient data.

    Args:
        therapist_id: UUID of the patient's therapist (required)
        email: Optional email
        name: Optional full name
        patient_id: Optional UUID
        phone: Optional phone number

    Returns:
        Dictionary with patient data matching Patient model

    Example:
        >>> therapist_id = uuid.uuid4()
        >>> patient = generate_patient(therapist_id)
        >>> assert patient["therapist_id"] == therapist_id
        >>> assert patient["name"] is not None
    """
    return {
        "id": patient_id or uuid.uuid4(),
        "name": name or fake.name(),
        "email": email or (fake.email() if random.choice([True, False]) else None),
        "phone": phone or (fake.phone_number() if random.choice([True, False]) else None),
        "therapist_id": therapist_id,
        "created_at": datetime.utcnow() - timedelta(days=random.randint(7, 180)),
        "updated_at": datetime.utcnow(),
    }


# ============================================================================
# Session Data Generation
# ============================================================================

def generate_session(
    patient_id: uuid.UUID,
    therapist_id: uuid.UUID,
    session_id: Optional[uuid.UUID] = None,
    status: SessionStatus = SessionStatus.processed,
    session_date: Optional[datetime] = None,
    duration_seconds: Optional[int] = None,
    include_transcript: bool = True,
    include_extracted_notes: bool = True,
) -> Dict[str, Any]:
    """
    Generate session metadata with optional transcript and notes.

    Args:
        patient_id: UUID of the patient
        therapist_id: UUID of the therapist
        session_id: Optional session UUID
        status: Session status (default: processed)
        session_date: Optional session date (defaults to recent past)
        duration_seconds: Optional duration (defaults to 30-60 min)
        include_transcript: Whether to generate transcript data
        include_extracted_notes: Whether to generate extracted notes

    Returns:
        Dictionary with session data matching Session model

    Example:
        >>> patient_id = uuid.uuid4()
        >>> therapist_id = uuid.uuid4()
        >>> session = generate_session(patient_id, therapist_id)
        >>> assert session["status"] == "processed"
        >>> assert session["transcript_text"] is not None
    """
    if session_date is None:
        # Random date in the past 30 days
        days_ago = random.randint(0, 30)
        session_date = datetime.utcnow() - timedelta(days=days_ago)

    if duration_seconds is None:
        # Random duration between 30-60 minutes
        duration_seconds = random.randint(1800, 3600)

    session_data = {
        "id": session_id or uuid.uuid4(),
        "patient_id": patient_id,
        "therapist_id": therapist_id,
        "session_date": session_date,
        "duration_seconds": duration_seconds,
        "status": status.value if isinstance(status, SessionStatus) else status,
        "created_at": session_date,
        "updated_at": datetime.utcnow(),
        "processed_at": datetime.utcnow() if status == SessionStatus.processed else None,
        "audio_filename": f"session_{uuid.uuid4()}.mp3",
        "audio_url": None,
        "error_message": None,
    }

    if include_transcript:
        transcript = generate_transcript(
            num_segments=random.randint(15, 30),
            duration_seconds=duration_seconds,
        )
        segments = generate_transcript_segments(
            num_segments=random.randint(20, 40),
            duration_seconds=duration_seconds,
        )
        session_data["transcript_text"] = transcript
        session_data["transcript_segments"] = [seg.model_dump() for seg in segments]
    else:
        session_data["transcript_text"] = None
        session_data["transcript_segments"] = None

    if include_extracted_notes:
        notes = generate_extracted_notes()
        session_data["extracted_notes"] = notes.model_dump()
        session_data["therapist_summary"] = notes.therapist_notes
        session_data["patient_summary"] = notes.patient_summary
        session_data["risk_flags"] = [flag.model_dump() for flag in notes.risk_flags]
    else:
        session_data["extracted_notes"] = None
        session_data["therapist_summary"] = None
        session_data["patient_summary"] = None
        session_data["risk_flags"] = None

    return session_data


# ============================================================================
# Extracted Notes Generation
# ============================================================================

def generate_extracted_notes(
    include_risk_flags: bool = False,
    mood: Optional[MoodLevel] = None,
    num_strategies: int = 3,
    num_triggers: int = 2,
    num_action_items: int = 2,
) -> ExtractedNotes:
    """
    Generate AI-extracted notes matching the ExtractedNotes schema.

    Args:
        include_risk_flags: Whether to include risk flags (default: False)
        mood: Optional mood level (randomly chosen if None)
        num_strategies: Number of strategies to generate (default: 3)
        num_triggers: Number of triggers to generate (default: 2)
        num_action_items: Number of action items (default: 2)

    Returns:
        ExtractedNotes object with realistic data

    Example:
        >>> notes = generate_extracted_notes(include_risk_flags=True)
        >>> assert len(notes.key_topics) >= 3
        >>> assert notes.session_mood in list(MoodLevel)
        >>> assert len(notes.therapist_notes) > 100
    """
    # Key topics
    topic_pool = [
        "Work-related stress and burnout",
        "Relationship challenges with partner",
        "Family dynamics and boundaries",
        "Sleep difficulties and insomnia",
        "Anxiety and panic symptoms",
        "Depression and low mood",
        "Self-esteem and self-criticism",
        "Grief and loss",
        "Trauma processing",
        "Coping skills development",
        "Cognitive distortions",
        "Mindfulness and grounding",
    ]
    key_topics = random.sample(topic_pool, k=random.randint(3, 6))

    # Strategies
    strategy_examples = [
        ("Box breathing", "Breathing technique", "Patient tried this week with some success"),
        ("Progressive muscle relaxation", "Relaxation technique", "Introduced as homework for anxiety management"),
        ("Cognitive restructuring", "Cognitive", "Working on identifying and challenging negative thoughts"),
        ("Thought records", "Cognitive", "Assigned to track and evaluate anxious thoughts"),
        ("Behavioral activation", "Behavioral", "Scheduling enjoyable activities despite low mood"),
        ("Grounding techniques", "Grounding", "5-4-3-2-1 method for managing anxiety"),
        ("Sleep hygiene", "Behavioral", "Discussed specific bedtime routine improvements"),
        ("Assertiveness training", "Communication", "Practicing 'I statements' in relationships"),
    ]
    strategies = []
    for _ in range(num_strategies):
        name, category, context = random.choice(strategy_examples)
        strategies.append(
            Strategy(
                name=name,
                category=category,
                status=random.choice(list(StrategyStatus)),
                context=context,
            )
        )

    # Triggers
    trigger_examples = [
        ("Work presentations", "Public speaking triggers anxiety and physical symptoms", "moderate"),
        ("Conflict with family", "Arguments with mother about boundaries", "mild"),
        ("Social gatherings", "Large groups cause overwhelm and panic", "moderate"),
        ("Financial stress", "Unexpected expenses trigger worry and rumination", "moderate"),
        ("Sleep deprivation", "Poor sleep worsens anxiety and mood", "severe"),
        ("Performance evaluations", "Fear of judgment and criticism at work", "mild"),
    ]
    triggers = []
    for _ in range(num_triggers):
        trigger, context, severity = random.choice(trigger_examples)
        triggers.append(
            Trigger(
                trigger=trigger,
                context=context,
                severity=severity,
            )
        )

    # Action items
    action_item_examples = [
        ("Practice box breathing twice daily", "behavioral", "Morning and evening routine"),
        ("Complete thought record when anxious", "cognitive", "Track thoughts, feelings, and evidence"),
        ("Schedule one enjoyable activity", "behavioral", "Something small but meaningful"),
        ("Set boundary with family member", "behavioral", "Use assertive communication script"),
        ("Try sleep hygiene improvements", "behavioral", "No screens 1 hour before bed"),
        ("Identify cognitive distortions", "cognitive", "Notice patterns in negative thinking"),
    ]
    action_items = []
    for _ in range(num_action_items):
        task, category, details = random.choice(action_item_examples)
        action_items.append(
            ActionItem(
                task=task,
                category=category,
                details=details,
            )
        )

    # Emotional themes
    emotional_themes = random.sample(
        [
            "Anxiety and worry",
            "Overwhelm",
            "Self-doubt",
            "Frustration",
            "Hope",
            "Determination",
            "Sadness",
            "Relief",
            "Guilt",
            "Anger",
        ],
        k=random.randint(2, 4),
    )

    # Significant quotes (optional)
    quote_examples = [
        ("I feel like I'm drowning in responsibilities", "Expresses feeling of overwhelm", 245.5),
        ("I never thought about it that way before", "Cognitive shift moment", 892.3),
        ("I'm scared I'll never feel better", "Core fear about recovery", 445.2),
        ("That technique actually helped when I tried it", "Positive reinforcement of skills", 1205.8),
    ]
    significant_quotes = []
    if random.choice([True, False]):
        quote, context, timestamp = random.choice(quote_examples)
        significant_quotes.append(
            SignificantQuote(
                quote=quote,
                context=context,
                timestamp_start=timestamp,
            )
        )

    # Mood
    if mood is None:
        mood = random.choice(list(MoodLevel))

    mood_trajectory = random.choice(["improving", "declining", "stable", "fluctuating"])

    # Follow-up topics
    follow_up_topics = random.sample(
        [
            "Review effectiveness of new coping strategies",
            "Explore family boundary-setting progress",
            "Check in on sleep quality changes",
            "Process upcoming stressful event",
            "Continue cognitive restructuring work",
        ],
        k=random.randint(1, 3),
    )

    # Unresolved concerns
    unresolved_concerns = []
    if random.choice([True, False]):
        unresolved_concerns = random.sample(
            [
                "Ongoing conflict with partner not yet addressed",
                "Work stress continues to impact daily functioning",
                "Underlying trauma needs more processing",
                "Medication concerns to discuss with psychiatrist",
            ],
            k=random.randint(1, 2),
        )

    # Risk flags
    risk_flags = []
    if include_risk_flags:
        risk_examples = [
            ("self_harm", "Patient mentioned thoughts of self-harm during difficult moments", "medium"),
            ("suicidal_ideation", "Passive suicidal thoughts reported - no plan or intent", "high"),
            ("crisis", "Patient in acute distress, needs increased monitoring", "high"),
        ]
        risk_type, evidence, severity = random.choice(risk_examples)
        risk_flags.append(
            RiskFlag(
                type=risk_type,
                evidence=evidence,
                severity=severity,
            )
        )

    # Summaries
    therapist_notes = f"""Patient presented with {key_topics[0].lower()} as primary concern. Clinical presentation shows {emotional_themes[0].lower()} with {mood.value.replace('_', ' ')} mood. Discussed {strategies[0].name.lower()} as intervention strategy. Patient demonstrated {random.choice(['good', 'moderate', 'limited'])} insight into patterns and {random.choice(['high', 'moderate', 'low'])} motivation for change. Assigned {action_items[0].task.lower()} as homework. Overall session was productive with {random.choice(['good', 'adequate', 'limited'])} engagement. Plan to continue current treatment approach and monitor progress. {'Risk assessment conducted - see flags for details.' if risk_flags else 'No immediate risk concerns identified.'}"""

    patient_summary = f"""We talked about {key_topics[0].lower()} and how it's been affecting you. You mentioned feeling {emotional_themes[0].lower()}, which is completely understandable given what you're dealing with. We worked on {strategies[0].name.lower()} as a tool you can use, and you seemed {random.choice(['hopeful', 'open', 'interested'])} about trying it. For this week, focus on {action_items[0].task.lower()}. Remember, small steps count as progress. You're doing good work showing up and being willing to try new approaches."""

    return ExtractedNotes(
        key_topics=key_topics,
        topic_summary=f"Session focused on {', '.join(key_topics[:2]).lower()}, with emphasis on developing coping strategies.",
        strategies=strategies,
        emotional_themes=emotional_themes,
        triggers=triggers,
        action_items=action_items,
        significant_quotes=significant_quotes,
        session_mood=mood,
        mood_trajectory=mood_trajectory,
        follow_up_topics=follow_up_topics,
        unresolved_concerns=unresolved_concerns,
        risk_flags=risk_flags,
        therapist_notes=therapist_notes,
        patient_summary=patient_summary,
    )


# ============================================================================
# Audio File Generation
# ============================================================================

def generate_audio_file(
    format: str = "mp3",
    duration_seconds: int = 60,
    sample_rate: int = 16000,
) -> bytes:
    """
    Generate mock audio file bytes for testing.

    NOTE: This generates random bytes, not actual audio data.
    For real audio testing, use actual audio files.

    Args:
        format: Audio format (mp3, wav, m4a, etc.)
        duration_seconds: Duration of audio in seconds
        sample_rate: Sample rate in Hz

    Returns:
        Random bytes representing mock audio data

    Example:
        >>> audio_bytes = generate_audio_file(format="mp3", duration_seconds=30)
        >>> assert len(audio_bytes) > 1000
        >>> assert isinstance(audio_bytes, bytes)
    """
    # Estimate file size based on format and duration
    if format.lower() == "wav":
        # WAV: ~sample_rate * duration * 2 bytes (16-bit audio)
        estimated_size = sample_rate * duration_seconds * 2
    elif format.lower() in ["mp3", "m4a", "aac"]:
        # Compressed: ~128kbps = 16KB/second
        estimated_size = duration_seconds * 16 * 1024
    else:
        # Default estimation
        estimated_size = duration_seconds * 16 * 1024

    # Generate random bytes
    # In real tests, use actual audio files instead
    return random.randbytes(estimated_size)


# ============================================================================
# Batch Generation Utilities
# ============================================================================

def generate_test_dataset(
    num_therapists: int = 2,
    patients_per_therapist: int = 5,
    sessions_per_patient: int = 3,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Generate a complete test dataset with therapists, patients, and sessions.

    Args:
        num_therapists: Number of therapists to generate
        patients_per_therapist: Number of patients per therapist
        sessions_per_patient: Number of sessions per patient

    Returns:
        Dictionary with "therapists", "patients", and "sessions" lists

    Example:
        >>> dataset = generate_test_dataset(num_therapists=1, patients_per_therapist=2, sessions_per_patient=1)
        >>> assert len(dataset["therapists"]) == 1
        >>> assert len(dataset["patients"]) == 2
        >>> assert len(dataset["sessions"]) == 2
    """
    therapists = []
    patients = []
    sessions = []

    for _ in range(num_therapists):
        therapist = generate_therapist()
        therapists.append(therapist)

        for _ in range(patients_per_therapist):
            patient = generate_patient(therapist["id"])
            patients.append(patient)

            for _ in range(sessions_per_patient):
                session = generate_session(
                    patient_id=patient["id"],
                    therapist_id=therapist["id"],
                )
                sessions.append(session)

    return {
        "therapists": therapists,
        "patients": patients,
        "sessions": sessions,
    }
