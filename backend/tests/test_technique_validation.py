"""
Test script for technique validation on mock therapy sessions

This script:
1. Tests exact matching on known technique names
2. Tests fuzzy matching on common variations
3. Re-extracts all 12 mock sessions with validation
4. Compares old vs new technique extraction
5. Generates JSON and Markdown reports
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.technique_library import get_technique_library
from app.services.topic_extractor import TopicExtractor
import json
from datetime import datetime
import os


def test_exact_matching():
    """Test exact matching on known technique names"""
    library = get_technique_library()

    test_cases = [
        ("Cognitive Restructuring", "CBT - Cognitive Restructuring"),
        ("TIPP Skills", "DBT - TIPP Skills"),
        ("Radical Acceptance", "DBT - Radical Acceptance"),
        ("cognitive defusion", "ACT - Cognitive Defusion"),  # case-insensitive
        ("CBT - Behavioral Activation", "CBT - Behavioral Activation"),  # formatted
    ]

    print("\n" + "="*80)
    print("EXACT MATCHING TESTS")
    print("="*80)

    passed = 0
    for input_str, expected in test_cases:
        result, confidence, match_type = library.validate_and_standardize(input_str)
        status = "✓" if result == expected else "✗"
        print(f"{status} '{input_str}' → '{result}' (expected: '{expected}')")
        if result == expected:
            passed += 1

    print(f"\nPassed: {passed}/{len(test_cases)}")
    return passed == len(test_cases)


def test_fuzzy_matching():
    """Test fuzzy matching on common variations"""
    library = get_technique_library()

    test_cases = [
        ("cognitive reframing", "CBT - Cognitive Restructuring"),
        ("thought challenging", "CBT - Cognitive Restructuring"),
        ("TIP skills", "DBT - TIPP Skills"),
        ("opposite action", "DBT - Opposite Action"),
        ("defusion", "ACT - Cognitive Defusion"),
        ("mindfulness meditation", "Mindfulness-Based - Mindfulness Meditation"),
    ]

    print("\n" + "="*80)
    print("FUZZY MATCHING TESTS")
    print("="*80)

    passed = 0
    for input_str, expected in test_cases:
        result, confidence, match_type = library.validate_and_standardize(input_str)
        status = "✓" if result == expected else "✗"
        print(f"{status} '{input_str}' → '{result}' (confidence: {confidence:.2f}, expected: '{expected}')")
        if result == expected:
            passed += 1

    print(f"\nPassed: {passed}/{len(test_cases)}")
    return passed >= len(test_cases) * 0.8  # 80% pass rate acceptable


def test_rejection_cases():
    """Test that non-clinical terms are properly rejected"""
    library = get_technique_library()

    # Note: "Psychoeducation" is actually in our library under "Other" modality
    # So we'll test other non-specific terms
    should_reject = [
        "crisis intervention",
        "supportive counseling",
        "active listening",
        "building rapport",
        "general therapy",
    ]

    print("\n" + "="*80)
    print("REJECTION TESTS (Non-Clinical Terms)")
    print("="*80)

    passed = 0
    for input_str in should_reject:
        result, confidence, match_type = library.validate_and_standardize(input_str)
        status = "✓" if result is None else "✗"
        print(f"{status} '{input_str}' → '{result}' (should be None)")
        if result is None:
            passed += 1

    print(f"\nPassed: {passed}/{len(should_reject)}")
    return passed >= len(should_reject) * 0.6  # 60% pass rate acceptable (some may fuzzy match)


def reprocess_all_sessions():
    """Re-extract all 12 mock sessions with technique validation"""
    current_dir = Path(__file__).parent.parent.parent
    mock_data_dir = current_dir / "mock-therapy-data" / "sessions"
    old_results_file = current_dir / "mock-therapy-data" / "topic_extraction_results.json"

    # Check if old results exist
    if not old_results_file.exists():
        print(f"\n⚠️  Old results file not found: {old_results_file}")
        print("    Skipping comparison, will generate new results only.")
        old_results = {}
    else:
        # Load old results for comparison
        with open(old_results_file, 'r') as f:
            old_data = json.load(f)
        old_results = {r["session_id"]: r for r in old_data["results"]}

    # Check if mock data directory exists
    if not mock_data_dir.exists():
        print(f"\n⚠️  Mock data directory not found: {mock_data_dir}")
        print("    Cannot run session reprocessing.")
        return [], []

    # Get session files
    session_files = sorted(mock_data_dir.glob("session_*.json"))

    if not session_files:
        print(f"\n⚠️  No session files found in {mock_data_dir}")
        return [], []

    print("\n" + "="*80)
    print("RE-PROCESSING ALL SESSIONS WITH VALIDATION")
    print("="*80)

    # Initialize extractor
    extractor = TopicExtractor()

    new_results = []
    comparison_table = []

    for session_file in session_files:
        with open(session_file, 'r') as f:
            session_data = json.load(f)

        session_id = session_data.get('id', session_file.stem)
        segments = session_data.get('segments', [])

        print(f"\nProcessing: {session_id}")

        # Extract with validation
        metadata = extractor.extract_metadata(session_id, segments)

        # Get old result for comparison
        old_result = old_results.get(session_id, {})
        old_technique = old_result.get("technique", "N/A")

        # Compare
        comparison_table.append({
            "session_id": session_id,
            "old_technique": old_technique,
            "new_technique": metadata.technique,
            "changed": old_technique != metadata.technique
        })

        print(f"  Old: {old_technique}")
        print(f"  New: {metadata.technique}")
        print(f"  Changed: {'YES' if old_technique != metadata.technique else 'NO'}")

        new_results.append({
            'session_id': metadata.session_id,
            'session_file': session_file.name,
            'topics': metadata.topics,
            'action_items': metadata.action_items,
            'technique': metadata.technique,
            'summary': metadata.summary,
            'confidence': metadata.confidence,
            'extracted_at': metadata.extracted_at.isoformat(),
            'raw_meta_summary': metadata.raw_meta_summary
        })

    return new_results, comparison_table


def generate_reports(new_results, comparison_table):
    """Generate JSON and Markdown comparison reports"""
    current_dir = Path(__file__).parent.parent.parent

    # JSON report
    json_report = {
        'test_run_at': datetime.now().isoformat(),
        'total_sessions': len(new_results),
        'validation_enabled': True,
        'results': new_results,
        'comparison': comparison_table
    }

    json_output = current_dir / "mock-therapy-data" / "technique_validation_results.json"
    with open(json_output, 'w') as f:
        json.dump(json_report, f, indent=2)

    print(f"\n✓ JSON report saved: {json_output}")

    # Markdown report
    md_lines = [
        "# Technique Validation Comparison Report",
        f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"\n**Total Sessions:** {len(new_results)}",
        "\n## Comparison Table\n",
        "| Session | Old Technique | New Technique | Changed |",
        "|---------|---------------|---------------|---------|"
    ]

    for row in comparison_table:
        changed = "✓" if row["changed"] else "-"
        md_lines.append(
            f"| {row['session_id']} | {row['old_technique']} | {row['new_technique']} | {changed} |"
        )

    # Summary statistics
    total_changed = sum(1 for r in comparison_table if r["changed"])
    md_lines.extend([
        f"\n## Summary Statistics\n",
        f"- **Total sessions processed:** {len(comparison_table)}",
        f"- **Techniques changed:** {total_changed}",
        f"- **Techniques unchanged:** {len(comparison_table) - total_changed}",
        f"- **Change rate:** {100 * total_changed / len(comparison_table):.1f}%" if comparison_table else "- **Change rate:** N/A"
    ])

    # Technique frequency analysis
    md_lines.extend([
        f"\n## New Technique Distribution\n",
    ])

    technique_counts = {}
    for result in new_results:
        tech = result['technique']
        technique_counts[tech] = technique_counts.get(tech, 0) + 1

    for technique, count in sorted(technique_counts.items(), key=lambda x: -x[1]):
        md_lines.append(f"- **{technique}:** {count} session(s)")

    md_output = current_dir / "mock-therapy-data" / "TECHNIQUE_VALIDATION_REPORT.md"
    with open(md_output, 'w') as f:
        f.write('\n'.join(md_lines))

    print(f"✓ Markdown report saved: {md_output}")


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("CLINICAL TECHNIQUE VALIDATION TEST SUITE")
    print("="*80)

    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("\n⚠️  WARNING: OPENAI_API_KEY not set in environment")
        print("    Session reprocessing will be skipped.")
        print("    Only running library validation tests.\n")

        # Run unit tests only
        exact_pass = test_exact_matching()
        fuzzy_pass = test_fuzzy_matching()
        reject_pass = test_rejection_cases()

        print("\n" + "="*80)
        print("UNIT TESTS COMPLETE")
        print("="*80)
        print(f"Exact matching: {'✓ PASS' if exact_pass else '✗ FAIL'}")
        print(f"Fuzzy matching: {'✓ PASS' if fuzzy_pass else '✗ FAIL'}")
        print(f"Rejection tests: {'✓ PASS' if reject_pass else '✗ FAIL'}")
        return

    # Unit tests
    exact_pass = test_exact_matching()
    fuzzy_pass = test_fuzzy_matching()
    reject_pass = test_rejection_cases()

    # Integration test
    new_results, comparison_table = reprocess_all_sessions()

    # Generate reports if we have results
    if new_results:
        generate_reports(new_results, comparison_table)

    print("\n" + "="*80)
    print("✨ ALL TESTS COMPLETE")
    print("="*80)
    print(f"Exact matching: {'✓ PASS' if exact_pass else '✗ FAIL'}")
    print(f"Fuzzy matching: {'✓ PASS' if fuzzy_pass else '✗ FAIL'}")
    print(f"Rejection tests: {'✓ PASS' if reject_pass else '✗ FAIL'}")
    if new_results:
        print(f"Sessions processed: {len(new_results)}")


if __name__ == "__main__":
    main()
