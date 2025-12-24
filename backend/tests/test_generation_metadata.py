"""
Test suite for generation_metadata utilities.

Tests polymorphic FK validation and utility functions.
Run with: python -m pytest backend/tests/test_generation_metadata.py -v
Or directly: python backend/tests/test_generation_metadata.py
"""

import os
import sys
from uuid import UUID, uuid4

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.utils.generation_metadata import (
    validate_exactly_one_fk,
)


def test_validate_exactly_one_fk_with_your_journey():
    """Test that providing only your_journey_version_id passes validation."""
    # Should not raise
    validate_exactly_one_fk(
        your_journey_version_id=uuid4(),
        session_bridge_version_id=None
    )
    print("✓ Validation passes with only your_journey_version_id")


def test_validate_exactly_one_fk_with_session_bridge():
    """Test that providing only session_bridge_version_id passes validation."""
    # Should not raise
    validate_exactly_one_fk(
        your_journey_version_id=None,
        session_bridge_version_id=uuid4()
    )
    print("✓ Validation passes with only session_bridge_version_id")


def test_validate_exactly_one_fk_with_neither():
    """Test that providing neither FK raises ValueError."""
    try:
        validate_exactly_one_fk(
            your_journey_version_id=None,
            session_bridge_version_id=None
        )
        raise AssertionError("Should have raised ValueError")
    except ValueError as e:
        assert "Must provide exactly one version_id" in str(e)
        print("✓ Validation raises error when neither FK provided")


def test_validate_exactly_one_fk_with_both():
    """Test that providing both FKs raises ValueError."""
    try:
        validate_exactly_one_fk(
            your_journey_version_id=uuid4(),
            session_bridge_version_id=uuid4()
        )
        raise AssertionError("Should have raised ValueError")
    except ValueError as e:
        assert "Cannot set both" in str(e)
        print("✓ Validation raises error when both FKs provided")


def run_all_tests():
    """Run all tests and print summary."""
    print("\n" + "=" * 60)
    print("generation_metadata Utilities Tests")
    print("=" * 60 + "\n")

    tests = [
        test_validate_exactly_one_fk_with_your_journey,
        test_validate_exactly_one_fk_with_session_bridge,
        test_validate_exactly_one_fk_with_neither,
        test_validate_exactly_one_fk_with_both,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__}: ERROR - {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60 + "\n")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
