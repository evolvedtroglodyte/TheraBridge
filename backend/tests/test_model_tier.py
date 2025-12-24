"""
Test suite for MODEL_TIER system in model_config.py

Tests tier switching, model resolution, and cost calculations.
Run with: python -m pytest backend/tests/test_model_tier.py -v
Or directly: python backend/tests/test_model_tier.py
"""

import os
import sys

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.config.model_config import (
    ModelTier,
    TIER_ASSIGNMENTS,
    TASK_MODEL_ASSIGNMENTS,
    get_current_tier,
    set_tier,
    reset_tier_cache,
    get_model_name,
    get_model_config,
    calculate_cost,
    estimate_task_cost,
)


def test_model_tier_enum():
    """Test ModelTier enum values."""
    assert ModelTier.PRECISION.value == "precision"
    assert ModelTier.BALANCED.value == "balanced"
    assert ModelTier.RAPID.value == "rapid"
    print("✓ ModelTier enum values correct")


def test_tier_assignments_structure():
    """Verify all tiers have assignments for all tasks."""
    all_tasks = set(TASK_MODEL_ASSIGNMENTS.keys())

    for tier in ModelTier:
        assert tier in TIER_ASSIGNMENTS, f"Missing tier: {tier}"
        tier_tasks = set(TIER_ASSIGNMENTS[tier].keys())
        missing = all_tasks - tier_tasks
        assert not missing, f"Tier {tier} missing tasks: {missing}"

    print(f"✓ All {len(all_tasks)} tasks have assignments in all 3 tiers")


def test_precision_tier_matches_defaults():
    """PRECISION tier should use same models as TASK_MODEL_ASSIGNMENTS."""
    for task, model in TASK_MODEL_ASSIGNMENTS.items():
        precision_model = TIER_ASSIGNMENTS[ModelTier.PRECISION][task]
        assert precision_model == model, (
            f"Task {task}: PRECISION tier ({precision_model}) != default ({model})"
        )
    print("✓ PRECISION tier matches default model assignments")


def test_balanced_tier_downgrades():
    """BALANCED tier should downgrade expensive models."""
    # Tasks that should be downgraded
    downgraded = [
        ("deep_analysis", "gpt-5"),      # From gpt-5.2
        ("prose_generation", "gpt-5"),   # From gpt-5.2
        ("session_insights", "gpt-5"),   # From gpt-5.2
        ("roadmap_generation", "gpt-5"), # From gpt-5.2
        ("breakthrough_detection", "gpt-5-mini"),  # From gpt-5
    ]

    for task, expected_model in downgraded:
        actual = TIER_ASSIGNMENTS[ModelTier.BALANCED][task]
        assert actual == expected_model, (
            f"Task {task}: expected {expected_model}, got {actual}"
        )
    print("✓ BALANCED tier correctly downgrades expensive models")


def test_rapid_tier_uses_mini():
    """RAPID tier should use gpt-5-mini for complex tasks."""
    complex_tasks = [
        "deep_analysis",
        "prose_generation",
        "session_insights",
        "roadmap_generation",
        "breakthrough_detection",
        "session_bridge_generation",
    ]

    for task in complex_tasks:
        actual = TIER_ASSIGNMENTS[ModelTier.RAPID][task]
        assert actual == "gpt-5-mini", f"Task {task}: expected gpt-5-mini, got {actual}"
    print("✓ RAPID tier uses gpt-5-mini for complex tasks")


def test_set_tier_and_get_current():
    """Test programmatic tier switching."""
    # Save original state
    original_tier = get_current_tier()

    try:
        # Test setting each tier
        for tier in ModelTier:
            set_tier(tier)
            assert get_current_tier() == tier, f"Failed to set tier to {tier}"

        print("✓ set_tier() and get_current_tier() work correctly")
    finally:
        # Restore original
        set_tier(original_tier)


def test_get_model_name_respects_tier():
    """Test that get_model_name() returns tier-appropriate model."""
    original_tier = get_current_tier()

    try:
        # Test PRECISION tier
        set_tier(ModelTier.PRECISION)
        assert get_model_name("deep_analysis") == "gpt-5.2"

        # Test BALANCED tier
        set_tier(ModelTier.BALANCED)
        assert get_model_name("deep_analysis") == "gpt-5"

        # Test RAPID tier
        set_tier(ModelTier.RAPID)
        assert get_model_name("deep_analysis") == "gpt-5-mini"

        print("✓ get_model_name() respects current tier")
    finally:
        set_tier(original_tier)


def test_override_model_bypasses_tier():
    """Test that override_model parameter bypasses tier logic."""
    original_tier = get_current_tier()

    try:
        set_tier(ModelTier.RAPID)  # Would normally use gpt-5-mini

        # Override should bypass tier
        model = get_model_name("deep_analysis", override_model="gpt-5.2-pro")
        assert model == "gpt-5.2-pro"

        print("✓ override_model parameter bypasses tier logic")
    finally:
        set_tier(original_tier)


def test_cost_calculation():
    """Test cost calculation with known values."""
    # gpt-5.2: $1.75/1M input, $14.00/1M output
    cost = calculate_cost("gpt-5.2", input_tokens=5000, output_tokens=800)

    expected = (5000 / 1_000_000 * 1.75) + (800 / 1_000_000 * 14.00)
    assert abs(cost - expected) < 0.0001, f"Cost {cost} != expected {expected}"

    print(f"✓ Cost calculation correct: ${cost:.6f}")


def test_cost_savings_by_tier():
    """Calculate actual cost savings for each tier."""
    original_tier = get_current_tier()

    try:
        # Calculate total cost for all tasks at each tier
        tasks = list(TASK_MODEL_ASSIGNMENTS.keys())
        tier_costs = {}

        for tier in ModelTier:
            set_tier(tier)
            total = sum(estimate_task_cost(task) for task in tasks)
            tier_costs[tier] = total

        precision_cost = tier_costs[ModelTier.PRECISION]
        balanced_savings = (1 - tier_costs[ModelTier.BALANCED] / precision_cost) * 100
        rapid_savings = (1 - tier_costs[ModelTier.RAPID] / precision_cost) * 100

        print(f"\n  Cost Analysis:")
        print(f"  PRECISION: ${precision_cost:.4f}/session (baseline)")
        print(f"  BALANCED:  ${tier_costs[ModelTier.BALANCED]:.4f}/session ({balanced_savings:.1f}% savings)")
        print(f"  RAPID:     ${tier_costs[ModelTier.RAPID]:.4f}/session ({rapid_savings:.1f}% savings)")

        # Verify expected savings ranges
        # BALANCED: ~30-40% savings (downgrades gpt-5.2 to gpt-5)
        # RAPID: ~80-90% savings (uses gpt-5-mini for complex tasks)
        assert 25 <= balanced_savings <= 50, f"BALANCED savings {balanced_savings:.1f}% outside expected range"
        assert 75 <= rapid_savings <= 95, f"RAPID savings {rapid_savings:.1f}% outside expected range"

        print("\n✓ Cost savings verified within expected ranges")
    finally:
        set_tier(original_tier)


def test_reset_tier_cache():
    """Test that reset_tier_cache() forces re-read from environment."""
    original_tier = get_current_tier()

    try:
        # Set tier programmatically
        set_tier(ModelTier.RAPID)
        assert get_current_tier() == ModelTier.RAPID

        # Reset cache - should re-read from env (defaults to precision)
        reset_tier_cache()

        # If MODEL_TIER env var is not set, should default to precision
        if "MODEL_TIER" not in os.environ:
            assert get_current_tier() == ModelTier.PRECISION
            print("✓ reset_tier_cache() forces re-read from environment")
        else:
            print(f"✓ reset_tier_cache() works (MODEL_TIER env={os.environ.get('MODEL_TIER')})")
    finally:
        set_tier(original_tier)


def test_env_var_tier_selection():
    """Test MODEL_TIER environment variable handling."""
    original_env = os.environ.get("MODEL_TIER")

    try:
        # Test each tier via env var
        for tier in ModelTier:
            os.environ["MODEL_TIER"] = tier.value
            reset_tier_cache()
            assert get_current_tier() == tier

        # Test invalid value falls back to precision
        os.environ["MODEL_TIER"] = "invalid_tier"
        reset_tier_cache()
        assert get_current_tier() == ModelTier.PRECISION

        print("✓ MODEL_TIER environment variable handling correct")
    finally:
        # Restore original
        if original_env is None:
            os.environ.pop("MODEL_TIER", None)
        else:
            os.environ["MODEL_TIER"] = original_env
        reset_tier_cache()


def test_session_bridge_task_exists():
    """Verify session_bridge_generation task is configured."""
    assert "session_bridge_generation" in TASK_MODEL_ASSIGNMENTS

    for tier in ModelTier:
        assert "session_bridge_generation" in TIER_ASSIGNMENTS[tier]

    print("✓ session_bridge_generation task configured in all tiers")


def run_all_tests():
    """Run all tests and print summary."""
    print("\n" + "=" * 60)
    print("MODEL_TIER System Tests")
    print("=" * 60 + "\n")

    tests = [
        test_model_tier_enum,
        test_tier_assignments_structure,
        test_precision_tier_matches_defaults,
        test_balanced_tier_downgrades,
        test_rapid_tier_uses_mini,
        test_set_tier_and_get_current,
        test_get_model_name_respects_tier,
        test_override_model_bypasses_tier,
        test_cost_calculation,
        test_reset_tier_cache,
        test_env_var_tier_selection,
        test_session_bridge_task_exists,
        test_cost_savings_by_tier,  # Run last as it prints more info
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
