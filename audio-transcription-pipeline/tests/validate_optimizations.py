#!/usr/bin/env python3
"""
Quick validation script for GPU pipeline optimizations (no pytest required).

This script verifies the optimizations work correctly without needing pytest.
Useful for quick checks during development.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_silence_trimming_disabled_by_default():
    """Test that silence trimming is disabled by default"""
    print("Testing: Silence trimming disabled by default...")
    try:
        from pipeline_gpu import GPUTranscriptionPipeline
        pipeline = GPUTranscriptionPipeline(whisper_model="base")
        assert pipeline.enable_silence_trimming is False
        print("✓ PASS: Silence trimming is disabled by default")
        return True
    except ImportError:
        print("⊘ SKIP: GPU pipeline dependencies not installed")
        return None
    except AssertionError:
        print("✗ FAIL: Silence trimming should be disabled by default")
        return False
    except (ValueError, RuntimeError) as e:
        if "CUDA not available" in str(e) or "No NVIDIA GPU" in str(e):
            print("⊘ SKIP: CUDA not available (expected on non-GPU systems)")
            return None
        print(f"✗ ERROR: {e}")
        return False
    except Exception as e:
        print(f"✗ ERROR: {e}")
        return False


def test_silence_trimming_can_be_enabled():
    """Test that silence trimming can be explicitly enabled"""
    print("\nTesting: Silence trimming can be enabled...")
    try:
        from pipeline_gpu import GPUTranscriptionPipeline
        pipeline = GPUTranscriptionPipeline(
            whisper_model="base",
            enable_silence_trimming=True
        )
        assert pipeline.enable_silence_trimming is True
        print("✓ PASS: Silence trimming can be enabled when requested")
        return True
    except ImportError:
        print("⊘ SKIP: GPU pipeline dependencies not installed")
        return None
    except AssertionError:
        print("✗ FAIL: Silence trimming should be enabled when requested")
        return False
    except (ValueError, RuntimeError) as e:
        if "CUDA not available" in str(e) or "No NVIDIA GPU" in str(e):
            print("⊘ SKIP: CUDA not available (expected on non-GPU systems)")
            return None
        print(f"✗ ERROR: {e}")
        return False
    except Exception as e:
        print(f"✗ ERROR: {e}")
        return False


def test_cpu_fallback_flag_initialized():
    """Test that CPU fallback flag is initialized"""
    print("\nTesting: CPU fallback flag initialized...")
    try:
        from pipeline_gpu import GPUTranscriptionPipeline
        pipeline = GPUTranscriptionPipeline(whisper_model="base")
        assert hasattr(pipeline, 'used_cpu_fallback')
        assert pipeline.used_cpu_fallback is False
        print("✓ PASS: CPU fallback flag is properly initialized")
        return True
    except ImportError:
        print("⊘ SKIP: GPU pipeline dependencies not installed")
        return None
    except AssertionError as e:
        print(f"✗ FAIL: CPU fallback flag not properly initialized: {e}")
        return False
    except (ValueError, RuntimeError) as e:
        if "CUDA not available" in str(e) or "No NVIDIA GPU" in str(e):
            print("⊘ SKIP: CUDA not available (expected on non-GPU systems)")
            return None
        print(f"✗ ERROR: {e}")
        return False
    except Exception as e:
        print(f"✗ ERROR: {e}")
        return False


def test_performance_expectation_documented():
    """Test that performance expectations are documented"""
    print("\nTesting: Performance expectations documented...")
    try:
        from pipeline_gpu import GPUTranscriptionPipeline
        init_docstring = GPUTranscriptionPipeline.__init__.__doc__
        assert "enable_silence_trimming" in init_docstring
        assert "performance" in init_docstring.lower()
        print("✓ PASS: Performance expectations are documented")
        return True
    except ImportError:
        print("⊘ SKIP: GPU pipeline dependencies not installed")
        return None
    except AssertionError:
        print("✗ FAIL: Performance expectations not documented in docstring")
        return False
    except Exception as e:
        print(f"✗ ERROR: {e}")
        return False


def main():
    """Run all validation tests"""
    print("=" * 60)
    print("GPU Pipeline Optimization Validation")
    print("=" * 60)

    tests = [
        test_silence_trimming_disabled_by_default,
        test_silence_trimming_can_be_enabled,
        test_cpu_fallback_flag_initialized,
        test_performance_expectation_documented,
    ]

    results = []
    skipped_count = 0
    for test in tests:
        result = test()
        if result is None:
            skipped_count += 1
        else:
            results.append(result)

    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)

    passed = sum(1 for r in results if r is True)
    failed = sum(1 for r in results if r is False)
    total = len(results)

    print(f"Passed:  {passed}/{total}")
    print(f"Failed:  {failed}/{total}")
    print(f"Skipped: {skipped_count}/{len(tests)}")

    if failed == 0:
        if skipped_count > 0:
            print(f"\n✓ All runnable tests passed! ({skipped_count} tests skipped - CUDA not available)")
        else:
            print("\n✓ All tests passed!")
        return 0
    else:
        print(f"\n✗ {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
