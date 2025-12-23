"""
Verification Script for GPT-5 Model Configuration

Tests that all AI services are using the correct GPT-5 models from config.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.mood_analyzer import MoodAnalyzer
from app.services.topic_extractor import TopicExtractor
from app.services.breakthrough_detector import BreakthroughDetector
from app.services.deep_analyzer import DeepAnalyzer
from app.config.model_config import TASK_MODEL_ASSIGNMENTS, get_model_name


def verify_service_models():
    """Verify all services use correct GPT-5 models from config"""

    print("\n" + "=" * 60)
    print("GPT-5 Model Configuration Verification")
    print("=" * 60 + "\n")

    results = []

    # Test 1: Mood Analyzer
    print("1. Mood Analyzer (MoodAnalyzer)")
    try:
        analyzer = MoodAnalyzer(api_key="test_key")
        expected = get_model_name("mood_analysis")
        actual = analyzer.model
        status = "✅ PASS" if actual == expected else "❌ FAIL"
        results.append(actual == expected)
        print(f"   Expected: {expected}")
        print(f"   Actual:   {actual}")
        print(f"   Status:   {status}\n")
    except Exception as e:
        print(f"   ❌ ERROR: {e}\n")
        results.append(False)

    # Test 2: Topic Extractor
    print("2. Topic Extractor (TopicExtractor)")
    try:
        extractor = TopicExtractor(api_key="test_key")
        expected = get_model_name("topic_extraction")
        actual = extractor.model
        status = "✅ PASS" if actual == expected else "❌ FAIL"
        results.append(actual == expected)
        print(f"   Expected: {expected}")
        print(f"   Actual:   {actual}")
        print(f"   Status:   {status}\n")
    except Exception as e:
        print(f"   ❌ ERROR: {e}\n")
        results.append(False)

    # Test 3: Breakthrough Detector
    print("3. Breakthrough Detector (BreakthroughDetector)")
    try:
        detector = BreakthroughDetector(api_key="test_key")
        expected = get_model_name("breakthrough_detection")
        actual = detector.model
        status = "✅ PASS" if actual == expected else "❌ FAIL"
        results.append(actual == expected)
        print(f"   Expected: {expected}")
        print(f"   Actual:   {actual}")
        print(f"   Status:   {status}\n")
    except Exception as e:
        print(f"   ❌ ERROR: {e}\n")
        results.append(False)

    # Test 4: Deep Analyzer
    print("4. Deep Analyzer (DeepAnalyzer)")
    try:
        # Note: DeepAnalyzer requires db parameter, but we can pass None for this test
        analyzer = DeepAnalyzer(api_key="test_key", db=None)
        expected = get_model_name("deep_analysis")
        actual = analyzer.model
        status = "✅ PASS" if actual == expected else "❌ FAIL"
        results.append(actual == expected)
        print(f"   Expected: {expected}")
        print(f"   Actual:   {actual}")
        print(f"   Status:   {status}\n")
    except Exception as e:
        print(f"   ❌ ERROR: {e}\n")
        results.append(False)

    # Test 5: Override functionality
    print("5. Override Model Test (MoodAnalyzer with override)")
    try:
        analyzer = MoodAnalyzer(api_key="test_key", override_model="gpt-5.2")
        expected = "gpt-5.2"
        actual = analyzer.model
        status = "✅ PASS" if actual == expected else "❌ FAIL"
        results.append(actual == expected)
        print(f"   Expected: {expected}")
        print(f"   Actual:   {actual}")
        print(f"   Status:   {status}\n")
    except Exception as e:
        print(f"   ❌ ERROR: {e}\n")
        results.append(False)

    # Summary
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("✅ ALL TESTS PASSED - GPT-5 configuration is correct!")
    else:
        print("❌ SOME TESTS FAILED - Please review configuration")

    print("=" * 60 + "\n")

    return passed == total


def print_model_summary():
    """Print the configured model assignments"""
    print("\n" + "=" * 60)
    print("Current Model Assignments")
    print("=" * 60 + "\n")

    for task, model in TASK_MODEL_ASSIGNMENTS.items():
        print(f"{task.replace('_', ' ').title():30} → {model}")

    print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    print_model_summary()
    success = verify_service_models()

    # Exit with appropriate code
    sys.exit(0 if success else 1)
