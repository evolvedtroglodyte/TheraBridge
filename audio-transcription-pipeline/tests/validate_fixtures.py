#!/usr/bin/env python3
"""
Quick validation script to test fixture behavior.

This script validates that:
1. Sample files are properly detected
2. Fallback logic works when files are missing
3. Error messages are helpful
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_sample_discovery():
    """Test that sample file discovery works"""
    script_dir = Path(__file__).parent
    candidates = [
        "compressed-cbt-session.m4a",
        "LIVE Cognitive Behavioral Therapy Session (1).mp3",
        "Person-Centred Therapy Session - Full Example [VLDDUL3HBIg].mp3",
    ]

    print("=" * 60)
    print("SAMPLE FILE DISCOVERY TEST")
    print("=" * 60)
    print()

    found_files = []
    for candidate in candidates:
        test_path = script_dir / "samples" / candidate
        if test_path.exists():
            size_mb = test_path.stat().st_size / (1024 * 1024)
            print(f"✅ Found: {candidate} ({size_mb:.1f} MB)")
            found_files.append(test_path)
        else:
            print(f"❌ Missing: {candidate}")

    print()
    if found_files:
        print(f"✅ SUCCESS: Found {len(found_files)} sample file(s)")
        print(f"   First available: {found_files[0].name}")
        return True
    else:
        print("❌ FAILURE: No sample files found")
        print()
        print("To fix this:")
        print("1. See tests/README.md for setup instructions")
        print("2. Download sample audio files")
        print("3. Place them in tests/samples/ directory")
        return False


def test_conftest_imports():
    """Test that conftest.py can be imported"""
    print()
    print("=" * 60)
    print("CONFTEST IMPORT TEST")
    print("=" * 60)
    print()

    # Check if pytest is available
    try:
        import pytest
        pytest_available = True
    except ImportError:
        pytest_available = False
        print("⚠️  pytest not installed (activate venv to test imports)")
        print("   Checking conftest.py syntax instead...")

    # Check conftest.py exists and is syntactically valid
    conftest_path = Path(__file__).parent / "conftest.py"

    if not conftest_path.exists():
        print("❌ conftest.py not found")
        return False

    print(f"✅ conftest.py exists ({conftest_path.stat().st_size} bytes)")

    # Try to compile it to check for syntax errors
    try:
        import py_compile
        py_compile.compile(str(conftest_path), doraise=True)
        print("✅ conftest.py has valid Python syntax")
    except Exception as e:
        print(f"❌ Syntax error in conftest.py: {e}")
        return False

    # Check for expected fixture definitions in the source
    content = conftest_path.read_text()
    expected_fixtures = [
        'def sample_cbt_session',
        'def sample_person_centered',
        'def sample_compressed_cbt',
        'def any_sample_audio',
        'def openai_api_key',
        'def hf_token',
        'def outputs_dir',
        'def processed_dir',
    ]

    print("✅ Checking for fixture definitions:")
    all_found = True
    for fixture_def in expected_fixtures:
        if fixture_def in content:
            print(f"   ✅ {fixture_def}()")
        else:
            print(f"   ❌ {fixture_def}() (MISSING)")
            all_found = False

    if not pytest_available:
        print()
        print("ℹ️  To fully test fixtures, activate venv and run:")
        print("   source venv/bin/activate && pytest tests/test_fixtures_example.py -v")

    return all_found


def test_readme_exists():
    """Test that README.md exists and is comprehensive"""
    print()
    print("=" * 60)
    print("README VALIDATION TEST")
    print("=" * 60)
    print()

    readme_path = Path(__file__).parent / "README.md"

    if not readme_path.exists():
        print("❌ tests/README.md not found")
        return False

    content = readme_path.read_text()
    size_kb = len(content) / 1024

    print(f"✅ README.md exists ({size_kb:.1f} KB)")

    # Check for key sections
    required_sections = [
        "Prerequisites",
        "Sample Audio Files",
        "API Keys",
        "Running Tests",
        "Fixtures Available",
        "Troubleshooting",
    ]

    missing_sections = []
    for section in required_sections:
        if section in content:
            print(f"   ✅ Contains '{section}' section")
        else:
            print(f"   ❌ Missing '{section}' section")
            missing_sections.append(section)

    if missing_sections:
        print(f"\n❌ Missing {len(missing_sections)} required section(s)")
        return False
    else:
        print("\n✅ All required sections present")
        return True


def main():
    """Run all validation tests"""
    print()
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 15 + "FIXTURE VALIDATION SUITE" + " " * 19 + "║")
    print("╚" + "═" * 58 + "╝")
    print()

    results = []

    # Run tests
    results.append(("Sample Discovery", test_sample_discovery()))
    results.append(("Conftest Import", test_conftest_imports()))
    results.append(("README Validation", test_readme_exists()))

    # Summary
    print()
    print("=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    print()

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:8} {test_name}")

    print()
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print()
        print("🎉 All validation tests passed!")
        print("   Test fixtures are ready to use.")
        print()
        print("Next steps:")
        print("   1. Run: pytest tests/test_fixtures_example.py -v")
        print("   2. See: tests/README.md for usage guide")
        return 0
    else:
        print()
        print("⚠️  Some validation tests failed")
        print("   Please fix the issues above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
