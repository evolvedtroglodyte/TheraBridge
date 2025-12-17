"""
End-to-end integration tests for complete authentication flow.

Tests the full user journey:
- Signup → Login → Access Protected Resource → Refresh Token → Logout
"""
import pytest
from fastapi import status


@pytest.mark.integration
def test_complete_user_journey(client, db_session):
    """
    Test: Signup → Login → Access → Refresh → Logout

    This test validates the entire authentication lifecycle to ensure
    all components work together correctly.
    """

    # ==================== STEP 1: SIGNUP ====================
    signup_resp = client.post("/api/v1/signup", json={
        "email": "journey@example.com",
        "password": "Journey123!",
        "full_name": "Journey User",
        "role": "therapist"
    })
    assert signup_resp.status_code == status.HTTP_201_CREATED

    tokens = signup_resp.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert "expires_in" in tokens
    assert tokens["expires_in"] > 0

    original_access_token = tokens["access_token"]
    original_refresh_token = tokens["refresh_token"]

    # ==================== STEP 2: ACCESS PROTECTED ENDPOINT ====================
    me_resp = client.get(
        "/api/v1/me",
        headers={"Authorization": f"Bearer {original_access_token}"}
    )
    assert me_resp.status_code == status.HTTP_200_OK

    user_data = me_resp.json()
    assert user_data["email"] == "journey@example.com"
    assert user_data["full_name"] == "Journey User"
    assert user_data["role"] == "therapist"
    assert user_data["is_active"] is True
    assert "id" in user_data

    # ==================== STEP 3: REFRESH TOKEN (WITH ROTATION) ====================
    refresh_resp = client.post(
        "/api/v1/refresh",
        json={"refresh_token": original_refresh_token}
    )
    assert refresh_resp.status_code == status.HTTP_200_OK

    new_tokens = refresh_resp.json()
    assert "access_token" in new_tokens
    assert "refresh_token" in new_tokens

    # Verify new tokens are different (rotation security)
    assert new_tokens["access_token"] != original_access_token
    assert new_tokens["refresh_token"] != original_refresh_token

    new_access_token = new_tokens["access_token"]
    new_refresh_token = new_tokens["refresh_token"]

    # Verify new access token works
    me_resp_2 = client.get(
        "/api/v1/me",
        headers={"Authorization": f"Bearer {new_access_token}"}
    )
    assert me_resp_2.status_code == status.HTTP_200_OK
    assert me_resp_2.json()["email"] == "journey@example.com"

    # ==================== STEP 4: VERIFY OLD REFRESH TOKEN IS REVOKED ====================
    # After rotation, old refresh token should be invalid
    old_refresh_resp = client.post(
        "/api/v1/refresh",
        json={"refresh_token": original_refresh_token}
    )
    assert old_refresh_resp.status_code == status.HTTP_401_UNAUTHORIZED
    assert "revoked" in old_refresh_resp.json()["detail"].lower()

    # ==================== STEP 5: LOGOUT ====================
    logout_resp = client.post(
        "/api/v1/logout",
        json={"refresh_token": new_refresh_token},
        headers={"Authorization": f"Bearer {new_access_token}"}
    )
    assert logout_resp.status_code == status.HTTP_200_OK
    assert "logged out" in logout_resp.json()["message"].lower()

    # ==================== STEP 6: VERIFY REFRESH TOKEN IS REVOKED AFTER LOGOUT ====================
    post_logout_refresh = client.post(
        "/api/v1/refresh",
        json={"refresh_token": new_refresh_token}
    )
    assert post_logout_refresh.status_code == status.HTTP_401_UNAUTHORIZED
    assert "revoked" in post_logout_refresh.json()["detail"].lower()


@pytest.mark.integration
def test_signup_duplicate_email_rejected(client, db_session):
    """
    Test: Duplicate signup attempts should be rejected
    """
    # First signup
    first_signup = client.post("/api/v1/signup", json={
        "email": "duplicate@example.com",
        "password": "Password123!",
        "full_name": "First User",
        "role": "therapist"
    })
    assert first_signup.status_code == status.HTTP_201_CREATED

    # Second signup with same email should fail
    second_signup = client.post("/api/v1/signup", json={
        "email": "duplicate@example.com",
        "password": "DifferentPassword123!",
        "full_name": "Second User",
        "role": "patient"
    })
    assert second_signup.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "already registered" in second_signup.json()["detail"].lower()


@pytest.mark.integration
def test_login_after_signup(client, db_session):
    """
    Test: User can login after signup with correct credentials
    """
    # Signup
    signup_resp = client.post("/api/v1/signup", json={
        "email": "logintest@example.com",
        "password": "SecurePass123!",
        "full_name": "Login Test User",
        "role": "patient"
    })
    assert signup_resp.status_code == status.HTTP_201_CREATED
    signup_tokens = signup_resp.json()

    # Login with same credentials
    login_resp = client.post("/api/v1/login", json={
        "email": "logintest@example.com",
        "password": "SecurePass123!"
    })
    assert login_resp.status_code == status.HTTP_200_OK

    login_tokens = login_resp.json()
    assert "access_token" in login_tokens
    assert "refresh_token" in login_tokens

    # Tokens should be different from signup tokens
    assert login_tokens["access_token"] != signup_tokens["access_token"]
    assert login_tokens["refresh_token"] != signup_tokens["refresh_token"]

    # Both tokens should work
    me_resp = client.get(
        "/api/v1/me",
        headers={"Authorization": f"Bearer {login_tokens['access_token']}"}
    )
    assert me_resp.status_code == status.HTTP_200_OK
    assert me_resp.json()["email"] == "logintest@example.com"


@pytest.mark.integration
def test_invalid_credentials_rejected(client, db_session):
    """
    Test: Login with incorrect password should fail
    """
    # Signup
    client.post("/api/v1/signup", json={
        "email": "secure@example.com",
        "password": "CorrectPassword123!",
        "full_name": "Secure User",
        "role": "therapist"
    })

    # Try login with wrong password
    wrong_password_resp = client.post("/api/v1/login", json={
        "email": "secure@example.com",
        "password": "WrongPassword123!"
    })
    assert wrong_password_resp.status_code == status.HTTP_401_UNAUTHORIZED
    assert "incorrect" in wrong_password_resp.json()["detail"].lower()

    # Try login with non-existent email
    wrong_email_resp = client.post("/api/v1/login", json={
        "email": "nonexistent@example.com",
        "password": "SomePassword123!"
    })
    assert wrong_email_resp.status_code == status.HTTP_401_UNAUTHORIZED
    assert "incorrect" in wrong_email_resp.json()["detail"].lower()


@pytest.mark.integration
def test_multiple_refresh_cycles(client, db_session):
    """
    Test: Multiple token refresh cycles work correctly (token rotation chain)
    """
    # Signup
    signup_resp = client.post("/api/v1/signup", json={
        "email": "multirefresh@example.com",
        "password": "RefreshTest123!",
        "full_name": "Multi Refresh User",
        "role": "therapist"
    })
    assert signup_resp.status_code == status.HTTP_201_CREATED

    tokens = signup_resp.json()
    refresh_token = tokens["refresh_token"]

    # Perform 3 refresh cycles
    for cycle in range(1, 4):
        refresh_resp = client.post(
            "/api/v1/refresh",
            json={"refresh_token": refresh_token}
        )
        assert refresh_resp.status_code == status.HTTP_200_OK, f"Cycle {cycle} failed"

        new_tokens = refresh_resp.json()
        new_access_token = new_tokens["access_token"]
        new_refresh_token = new_tokens["refresh_token"]

        # Verify new access token works
        me_resp = client.get(
            "/api/v1/me",
            headers={"Authorization": f"Bearer {new_access_token}"}
        )
        assert me_resp.status_code == status.HTTP_200_OK, f"Cycle {cycle} access failed"

        # Update for next cycle
        refresh_token = new_refresh_token

    # Verify final token still works
    final_me_resp = client.get(
        "/api/v1/me",
        headers={"Authorization": f"Bearer {new_access_token}"}
    )
    assert final_me_resp.status_code == status.HTTP_200_OK
    assert final_me_resp.json()["email"] == "multirefresh@example.com"


@pytest.mark.integration
def test_access_without_token_denied(client, db_session):
    """
    Test: Protected endpoints require valid access token
    """
    # Try to access /me without token
    no_token_resp = client.get("/api/v1/me")
    assert no_token_resp.status_code == status.HTTP_401_UNAUTHORIZED

    # Try with invalid token
    invalid_token_resp = client.get(
        "/api/v1/me",
        headers={"Authorization": "Bearer invalid_token_xyz"}
    )
    assert invalid_token_resp.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.integration
def test_different_roles_can_signup(client, db_session):
    """
    Test: All user roles can successfully signup and authenticate
    """
    roles = ["therapist", "patient", "admin"]

    for role in roles:
        email = f"{role}@example.com"

        # Signup
        signup_resp = client.post("/api/v1/signup", json={
            "email": email,
            "password": f"{role.capitalize()}Pass123!",
            "full_name": f"Test {role.capitalize()}",
            "role": role
        })
        assert signup_resp.status_code == status.HTTP_201_CREATED, f"{role} signup failed"

        tokens = signup_resp.json()

        # Verify role is correct
        me_resp = client.get(
            "/api/v1/me",
            headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )
        assert me_resp.status_code == status.HTTP_200_OK, f"{role} access failed"
        assert me_resp.json()["role"] == role, f"{role} role mismatch"
