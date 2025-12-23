"""
Simple example demonstrating breakthrough detection on a sample therapy session.

This script shows how to use the BreakthroughDetector with a realistic
therapy conversation that contains a clear breakthrough moment.
"""

from app.services.breakthrough_detector import BreakthroughDetector


def main():
    print("=" * 80)
    print("BREAKTHROUGH DETECTION - SIMPLE EXAMPLE")
    print("=" * 80)

    # Create a realistic therapy session transcript
    # This session shows a patient having a cognitive insight about their
    # relationship patterns stemming from childhood experiences
    sample_session = [
        {
            "start": 0.0,
            "end": 5.2,
            "speaker": "Therapist",
            "text": "Last week you mentioned feeling anxious when your partner didn't text back right away. Has that happened again?"
        },
        {
            "start": 5.2,
            "end": 12.5,
            "speaker": "Patient",
            "text": "Yes, constantly. Like yesterday, he didn't respond for two hours and I spiraled. I checked my phone probably 50 times."
        },
        {
            "start": 12.5,
            "end": 18.0,
            "speaker": "Therapist",
            "text": "What went through your mind during those two hours when you were checking your phone?"
        },
        {
            "start": 18.0,
            "end": 28.3,
            "speaker": "Patient",
            "text": "I kept thinking he's losing interest, he's going to leave me, I did something wrong. It's like this panic that just takes over."
        },
        {
            "start": 28.3,
            "end": 34.5,
            "speaker": "Therapist",
            "text": "That sounds exhausting. When did you first remember feeling this kind of panic about someone leaving?"
        },
        {
            "start": 34.5,
            "end": 42.0,
            "speaker": "Patient",
            "text": "Hmm... I guess when I was a kid? My dad would leave for business trips and I never knew when he'd be back."
        },
        {
            "start": 42.0,
            "end": 48.5,
            "speaker": "Therapist",
            "text": "Tell me more about that. What was it like when he would leave?"
        },
        {
            "start": 48.5,
            "end": 62.0,
            "speaker": "Patient",
            "text": "My mom would say he'd be back in a few days, but sometimes it was weeks. I remember sitting by the window watching for his car. I felt so... abandoned, I guess."
        },
        {
            "start": 62.0,
            "end": 68.0,
            "speaker": "Therapist",
            "text": "And when you check your phone 50 times waiting for your partner to text back..."
        },
        {
            "start": 68.0,
            "end": 82.5,
            "speaker": "Patient",
            "text": "Oh my god. I'm that little kid watching out the window. I'm doing the exact same thing. It's not really about my boyfriend at all, is it? It's about my dad leaving."
        },
        {
            "start": 82.5,
            "end": 88.0,
            "speaker": "Therapist",
            "text": "That's a really profound connection you just made. How does it feel to recognize that?"
        },
        {
            "start": 88.0,
            "end": 98.5,
            "speaker": "Patient",
            "text": "It's... it's actually a relief? Like, I'm not crazy. This makes sense. My boyfriend isn't my dad. He's not abandoning me when he doesn't text back immediately."
        },
        {
            "start": 98.5,
            "end": 104.0,
            "speaker": "Therapist",
            "text": "This is a significant insight. How might this change how you respond next time?"
        },
        {
            "start": 104.0,
            "end": 115.0,
            "speaker": "Patient",
            "text": "Maybe I can remind myself - this is old fear, not current reality. He always texts back. He's not leaving. I can breathe through the anxiety."
        }
    ]

    # Initialize the breakthrough detector
    print("\n1. Initializing BreakthroughDetector...")
    detector = BreakthroughDetector()
    print("   ✓ Detector ready with GPT-4 integration")

    # Provide some context about the session
    session_metadata = {
        "session_id": "example_session",
        "patient_id": "demo_patient",
        "session_number": 8,
        "duration": 115.0
    }

    # Analyze the session
    print("\n2. Analyzing session for breakthroughs...")
    print("   (Processing with AI...)")

    analysis = detector.analyze_session(
        transcript=sample_session,
        session_metadata=session_metadata
    )

    # Display the results
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)

    print(f"\nBreakthrough Detected: {'Yes ✓' if analysis.has_breakthrough else 'No ✗'}")

    if analysis.has_breakthrough:
        print(f"Number of Breakthroughs: {len(analysis.breakthrough_candidates)}")

        # Show the primary breakthrough
        if analysis.primary_breakthrough:
            bt = analysis.primary_breakthrough

            print(f"\n{'─' * 80}")
            print("PRIMARY BREAKTHROUGH")
            print(f"{'─' * 80}")

            print(f"\n🎯 Type: {bt.breakthrough_type.replace('_', ' ').title()}")
            print(f"⭐ Confidence: {bt.confidence_score:.1%}")

            # Format timestamp
            start_min = int(bt.timestamp_start // 60)
            start_sec = int(bt.timestamp_start % 60)
            end_min = int(bt.timestamp_end // 60)
            end_sec = int(bt.timestamp_end % 60)
            print(f"⏱️  Timestamp: {start_min:02d}:{start_sec:02d} - {end_min:02d}:{end_sec:02d}")

            print(f"\n📝 Description:")
            print(f"   {bt.description}")

            print(f"\n🔍 Evidence (Why this is a breakthrough):")
            print(f"   {bt.evidence}")

            print(f"\n💬 Key Dialogue:")
            for i, turn in enumerate(bt.speaker_sequence[:5]):  # Show first 5 turns
                speaker = turn.get("speaker", "Unknown")
                text = turn.get("text", "")
                # Add visual separator
                prefix = "   ├─" if i < len(bt.speaker_sequence[:5]) - 1 else "   └─"
                print(f"{prefix} {speaker}: {text}")

        # Show session-level insights
        print(f"\n{'─' * 80}")
        print("SESSION ANALYSIS")
        print(f"{'─' * 80}")

        print(f"\n📊 Summary:")
        print(f"   {analysis.session_summary}")

        print(f"\n💭 Emotional Trajectory:")
        print(f"   {analysis.emotional_trajectory}")

        # Show all breakthroughs if multiple
        if len(analysis.breakthrough_candidates) > 1:
            print(f"\n{'─' * 80}")
            print(f"ALL BREAKTHROUGHS ({len(analysis.breakthrough_candidates)})")
            print(f"{'─' * 80}")

            for i, bt in enumerate(analysis.breakthrough_candidates, 1):
                print(f"\n{i}. {bt.breakthrough_type.replace('_', ' ').title()}")
                print(f"   Confidence: {bt.confidence_score:.1%}")
                print(f"   {bt.description}")

    else:
        print("\nNo significant breakthroughs detected in this session.")
        print("\nPossible reasons:")
        print("  • Early rapport-building phase")
        print("  • Maintenance/check-in session")
        print("  • Gradual progress without dramatic moments")

    # Export results
    print(f"\n{'=' * 80}")
    print("3. Exporting results...")

    output_file = "example_breakthrough_report.json"
    detector.export_breakthrough_report(analysis, output_file)
    print(f"   ✓ Results saved to: {output_file}")

    print(f"\n{'=' * 80}")
    print("EXAMPLE COMPLETE")
    print(f"{'=' * 80}")

    print("\n💡 Next steps:")
    print("   • Review the exported JSON file for full details")
    print("   • Try with your own therapy transcripts")
    print("   • Adjust confidence thresholds based on your needs")
    print("   • Integrate with your backend API endpoints")

    print("\n📚 For more information:")
    print("   • See: app/services/BREAKTHROUGH_DETECTION_README.md")
    print("   • Run tests: python tests/test_breakthrough_detection.py")


if __name__ == "__main__":
    main()
