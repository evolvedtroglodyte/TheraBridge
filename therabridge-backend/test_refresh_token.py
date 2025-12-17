"""
Validation script for refresh token generation (Subtask 1.2.4).

Tests:
1. create_refresh_token returns 43-character string
2. Each call produces unique token (test 100 times)
3. hash_refresh_token uses get_password_hash (produces bcrypt hash)
4. Hashed token is 60 characters (bcrypt output)
"""

import sys
sys.path.insert(0, '.')

from app.auth.utils import create_refresh_token, hash_refresh_token, verify_password


def test_token_length():
    """Verify tokens are exactly 43 characters."""
    print("✓ Test 1: Token length verification")
    for i in range(10):
        token = create_refresh_token()
        assert len(token) == 43, f"Expected 43 chars, got {len(token)}"
    print("  ✓ All tokens are 43 characters")


def test_token_uniqueness():
    """Verify each call produces a unique token."""
    print("\n✓ Test 2: Token uniqueness (100 samples)")
    tokens = set()
    for i in range(100):
        token = create_refresh_token()
        assert token not in tokens, f"Duplicate token found at iteration {i}"
        tokens.add(token)
    print(f"  ✓ All 100 tokens are unique")


def test_hash_length():
    """Verify hashed tokens are 60 characters (bcrypt)."""
    print("\n✓ Test 3: Hash length verification")
    for i in range(10):
        token = create_refresh_token()
        hashed = hash_refresh_token(token)
        assert len(hashed) == 60, f"Expected 60 chars, got {len(hashed)}"
    print("  ✓ All hashed tokens are 60 characters")


def test_hash_verification():
    """Verify hashed tokens can be verified with verify_password."""
    print("\n✓ Test 4: Hash verification using bcrypt")
    for i in range(10):
        token = create_refresh_token()
        hashed = hash_refresh_token(token)
        # Should verify successfully with original token
        assert verify_password(token, hashed), "Token verification failed"
        # Should NOT verify with different token
        wrong_token = create_refresh_token()
        assert not verify_password(wrong_token, hashed), "Wrong token verified!"
    print("  ✓ Hash verification works correctly")


def test_hash_uniqueness():
    """Verify same token produces different hashes (bcrypt salt)."""
    print("\n✓ Test 5: Hash uniqueness (bcrypt random salt)")
    token = create_refresh_token()
    hashes = set()
    for i in range(5):
        hashed = hash_refresh_token(token)
        hashes.add(hashed)
    assert len(hashes) == 5, "Bcrypt should produce different hashes each time"
    print("  ✓ Same token produces different hashes (bcrypt salt working)")


if __name__ == "__main__":
    print("=" * 60)
    print("SUBTASK 1.2.4: Refresh Token Generation - Validation Tests")
    print("=" * 60)

    try:
        test_token_length()
        test_token_uniqueness()
        test_hash_length()
        test_hash_verification()
        test_hash_uniqueness()

        print("\n" + "=" * 60)
        print("✅ ALL VALIDATION TESTS PASSED")
        print("=" * 60)
        print("\nSummary:")
        print("  ✓ create_refresh_token() returns 43-character strings")
        print("  ✓ Each call produces unique tokens (100/100 unique)")
        print("  ✓ hash_refresh_token() uses bcrypt (60-char output)")
        print("  ✓ Hashed tokens can be verified with verify_password()")
        print("  ✓ Bcrypt random salt ensures hash uniqueness")

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
