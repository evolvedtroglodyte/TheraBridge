"""
Integration tests for authentication endpoints.

Tests cover:
- User signup (account creation)
- User login (authentication)
- Token refresh (access token renewal)
- User logout (session revocation)
- Protected endpoint access (/me)
- Error cases (invalid credentials, inactive accounts, etc.)
"""
import pytest
from fastapi import status
from app.auth.models import AuthSession
from app.models.db_models import User
from app.models.schemas import UserRole

# API prefix for auth endpoints
AUTH_PREFIX = "/api/v1"


class TestSignup:
    """Test user registration endpoint"""

    def test_signup_success(self, client, test_db):
        """Test successful user registration"""
        response = client.post(
            f"{AUTH_PREFIX}/signup",
            json={
                "email": "newuser@example.com",
                "password": "NewPass123!",
                "first_name": "New",
                "last_name": "User",
                "role": "therapist"
            }
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        # Verify response structure
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data

        # Verify user was created in database
        user = test_db.query(User).filter(User.email == "newuser@example.com").first()
        assert user is not None
        assert user.full_name == "New User"
        assert user.role == UserRole.therapist
        assert user.is_active is True

        # Verify auth session was created
        auth_session = test_db.query(AuthSession).filter(AuthSession.user_id == user.id).first()
        assert auth_session is not None
        assert auth_session.is_revoked is False

    def test_signup_patient_role(self, client, test_db):
        """Test signup with patient role"""
        response = client.post(
            f"{AUTH_PREFIX}/signup",
            json={
                "email": "patient@example.com",
                "password": "PatientPass123!",
                "first_name": "Patient",
                "last_name": "User",
                "role": "patient"
            }
        )

        assert response.status_code == status.HTTP_201_CREATED
        user = test_db.query(User).filter(User.email == "patient@example.com").first()
        assert user.role == UserRole.patient

    def test_signup_duplicate_email(self, client, test_user):
        """Test signup fails with duplicate email"""
        response = client.post(
            f"{AUTH_PREFIX}/signup",
            json={
                "email": "test@example.com",  # Already exists from test_user fixture
                "password": "AnotherPass123!",
                "first_name": "Another",
                "last_name": "User",
                "role": "therapist"
            }
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "already registered" in response.json()["detail"].lower()

    def test_signup_invalid_email(self, client):
        """Test signup fails with invalid email format"""
        response = client.post(
            f"{AUTH_PREFIX}/signup",
            json={
                "email": "not-an-email",
                "password": "ValidPass123!",
                "first_name": "Test",
                "last_name": "User",
                "role": "therapist"
            }
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_signup_weak_password(self, client):
        """Test signup fails with password too short"""
        response = client.post(
            f"{AUTH_PREFIX}/signup",
            json={
                "email": "newuser@example.com",
                "password": "short",  # Less than 12 characters
                "first_name": "Test",
                "last_name": "User",
                "role": "therapist"
            }
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_signup_missing_fields(self, client):
        """Test signup fails with missing required fields"""
        response = client.post(
            f"{AUTH_PREFIX}/signup",
            json={
                "email": "newuser@example.com",
                # Missing password, full_name, role
            }
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestLogin:
    """Test user login endpoint"""

    def test_login_success(self, client, test_user):
        """Test successful login with valid credentials"""
        response = client.post(
            f"{AUTH_PREFIX}/login",
            json={
                "email": "test@example.com",
                "password": "TestPass123!"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify response structure
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data

    def test_login_wrong_password(self, client, test_user):
        """Test login fails with incorrect password"""
        response = client.post(
            f"{AUTH_PREFIX}/login",
            json={
                "email": "test@example.com",
                "password": "WrongPassword123!"
            }
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "incorrect" in response.json()["detail"].lower()

    def test_login_nonexistent_user(self, client):
        """Test login fails with non-existent email"""
        response = client.post(
            f"{AUTH_PREFIX}/login",
            json={
                "email": "nonexistent@example.com",
                "password": "SomePass123!"
            }
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "incorrect" in response.json()["detail"].lower()

    def test_login_inactive_account(self, client, inactive_user):
        """Test login fails for inactive account"""
        response = client.post(
            f"{AUTH_PREFIX}/login",
            json={
                "email": "inactive@example.com",
                "password": "InactivePass123!"
            }
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "inactive" in response.json()["detail"].lower()

    def test_login_creates_new_session(self, client, test_user, test_db):
        """Test that each login creates a new auth session"""
        # First login
        response1 = client.post(
            f"{AUTH_PREFIX}/login",
            json={
                "email": "test@example.com",
                "password": "TestPass123!"
            }
        )
        token1 = response1.json()["refresh_token"]

        # Second login
        response2 = client.post(
            f"{AUTH_PREFIX}/login",
            json={
                "email": "test@example.com",
                "password": "TestPass123!"
            }
        )
        token2 = response2.json()["refresh_token"]

        # Verify different tokens
        assert token1 != token2

        # Verify both sessions exist
        sessions = test_db.query(AuthSession).filter(
            AuthSession.user_id == test_user.id
        ).all()
        assert len(sessions) == 2


class TestTokenRefresh:
    """Test token refresh endpoint"""

    def test_refresh_success(self, client, test_user):
        """Test successful token refresh"""
        # Login to get tokens
        login_response = client.post(
            f"{AUTH_PREFIX}/login",
            json={
                "email": "test@example.com",
                "password": "TestPass123!"
            }
        )
        refresh_token = login_response.json()["refresh_token"]
        old_access_token = login_response.json()["access_token"]

        # Refresh tokens
        refresh_response = client.post(
            f"{AUTH_PREFIX}/refresh",
            json={"refresh_token": refresh_token}
        )

        assert refresh_response.status_code == status.HTTP_200_OK
        data = refresh_response.json()

        # Verify new access token is different
        assert data["access_token"] != old_access_token
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_refresh_invalid_token(self, client):
        """Test refresh fails with invalid token"""
        response = client.post(
            f"{AUTH_PREFIX}/refresh",
            json={"refresh_token": "invalid-token-12345"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "invalid" in response.json()["detail"].lower()

    def test_refresh_revoked_token(self, client, test_user, test_db):
        """Test refresh fails with revoked token"""
        # Login and get refresh token
        login_response = client.post(
            f"{AUTH_PREFIX}/login",
            json={
                "email": "test@example.com",
                "password": "TestPass123!"
            }
        )
        refresh_token = login_response.json()["refresh_token"]
        access_token = login_response.json()["access_token"]

        # Logout (revoke token)
        client.post(
            f"{AUTH_PREFIX}/logout",
            json={"refresh_token": refresh_token},
            headers={"Authorization": f"Bearer {access_token}"}
        )

        # Try to refresh with revoked token
        refresh_response = client.post(
            f"{AUTH_PREFIX}/refresh",
            json={"refresh_token": refresh_token}
        )

        assert refresh_response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "revoked" in refresh_response.json()["detail"].lower()


class TestLogout:
    """Test logout endpoint"""

    def test_logout_success(self, client, test_user, test_db):
        """Test successful logout"""
        # Login to get tokens
        login_response = client.post(
            f"{AUTH_PREFIX}/login",
            json={
                "email": "test@example.com",
                "password": "TestPass123!"
            }
        )
        refresh_token = login_response.json()["refresh_token"]
        access_token = login_response.json()["access_token"]

        # Logout
        logout_response = client.post(
            f"{AUTH_PREFIX}/logout",
            json={"refresh_token": refresh_token},
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert logout_response.status_code == status.HTTP_200_OK
        assert "logged out" in logout_response.json()["message"].lower()

        # Verify session was revoked
        from app.auth.utils import hash_refresh_token
        session = test_db.query(AuthSession).filter(
            AuthSession.refresh_token == hash_refresh_token(refresh_token)
        ).first()
        assert session.is_revoked is True

    def test_logout_without_auth(self, client):
        """Test logout fails without authentication"""
        response = client.post(
            f"{AUTH_PREFIX}/logout",
            json={"refresh_token": "some-token"}
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_logout_with_invalid_token(self, client, test_user):
        """Test logout with invalid refresh token (graceful failure)"""
        # Login to get access token
        login_response = client.post(
            f"{AUTH_PREFIX}/login",
            json={
                "email": "test@example.com",
                "password": "TestPass123!"
            }
        )
        access_token = login_response.json()["access_token"]

        # Logout with invalid refresh token (should still succeed)
        logout_response = client.post(
            f"{AUTH_PREFIX}/logout",
            json={"refresh_token": "invalid-token"},
            headers={"Authorization": f"Bearer {access_token}"}
        )

        # Logout is idempotent - succeeds even if token not found
        assert logout_response.status_code == status.HTTP_200_OK


class TestGetMe:
    """Test /me endpoint for getting current user info"""

    def test_get_me_success(self, client, test_user):
        """Test getting current user information"""
        # Login to get access token
        login_response = client.post(
            f"{AUTH_PREFIX}/login",
            json={
                "email": "test@example.com",
                "password": "TestPass123!"
            }
        )
        access_token = login_response.json()["access_token"]

        # Get current user info
        me_response = client.get(
            f"{AUTH_PREFIX}/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert me_response.status_code == status.HTTP_200_OK
        data = me_response.json()

        # Verify user data
        assert data["email"] == "test@example.com"
        assert data["full_name"] == "Test User"
        assert data["role"] == "therapist"
        assert data["is_active"] is True
        assert "hashed_password" not in data  # Sensitive data excluded

    def test_get_me_without_auth(self, client):
        """Test /me fails without authentication"""
        response = client.get(f"{AUTH_PREFIX}/me")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_me_invalid_token(self, client):
        """Test /me fails with invalid token"""
        response = client.get(
            f"{AUTH_PREFIX}/me",
            headers={"Authorization": "Bearer invalid-token-12345"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestAuthenticationFlow:
    """Test complete authentication flows"""

    def test_full_auth_flow(self, client, test_db):
        """Test complete signup -> login -> refresh -> logout flow"""
        # 1. Signup
        signup_response = client.post(
            f"{AUTH_PREFIX}/signup",
            json={
                "email": "flowtest@example.com",
                "password": "FlowPass123!",
                "first_name": "Flow Test",
                "last_name": "User",
                "role": "therapist"
            }
        )
        assert signup_response.status_code == status.HTTP_201_CREATED
        initial_tokens = signup_response.json()

        # 2. Access protected endpoint with access token
        me_response = client.get(
            f"{AUTH_PREFIX}/me",
            headers={"Authorization": f"Bearer {initial_tokens['access_token']}"}
        )
        assert me_response.status_code == status.HTTP_200_OK
        assert me_response.json()["email"] == "flowtest@example.com"

        # 3. Refresh tokens
        refresh_response = client.post(
            f"{AUTH_PREFIX}/refresh",
            json={"refresh_token": initial_tokens["refresh_token"]}
        )
        assert refresh_response.status_code == status.HTTP_200_OK
        new_tokens = refresh_response.json()

        # 4. Access protected endpoint with new access token
        me_response2 = client.get(
            f"{AUTH_PREFIX}/me",
            headers={"Authorization": f"Bearer {new_tokens['access_token']}"}
        )
        assert me_response2.status_code == status.HTTP_200_OK

        # 5. Logout
        logout_response = client.post(
            f"{AUTH_PREFIX}/logout",
            json={"refresh_token": new_tokens["refresh_token"]},
            headers={"Authorization": f"Bearer {new_tokens['access_token']}"}
        )
        assert logout_response.status_code == status.HTTP_200_OK

        # 6. Verify refresh token no longer works
        refresh_after_logout = client.post(
            f"{AUTH_PREFIX}/refresh",
            json={"refresh_token": new_tokens["refresh_token"]}
        )
        assert refresh_after_logout.status_code == status.HTTP_401_UNAUTHORIZED

    def test_multiple_sessions(self, client, test_user, test_db):
        """Test user can have multiple active sessions"""
        # Login from "device 1"
        login1 = client.post(
            f"{AUTH_PREFIX}/login",
            json={
                "email": "test@example.com",
                "password": "TestPass123!"
            }
        )
        tokens1 = login1.json()

        # Login from "device 2"
        login2 = client.post(
            f"{AUTH_PREFIX}/login",
            json={
                "email": "test@example.com",
                "password": "TestPass123!"
            }
        )
        tokens2 = login2.json()

        # Both access tokens should work
        me1 = client.get(
            f"{AUTH_PREFIX}/me",
            headers={"Authorization": f"Bearer {tokens1['access_token']}"}
        )
        me2 = client.get(
            f"{AUTH_PREFIX}/me",
            headers={"Authorization": f"Bearer {tokens2['access_token']}"}
        )

        assert me1.status_code == status.HTTP_200_OK
        assert me2.status_code == status.HTTP_200_OK

        # Both refresh tokens should work
        refresh1 = client.post(f"{AUTH_PREFIX}/refresh", json={"refresh_token": tokens1["refresh_token"]})
        refresh2 = client.post(f"{AUTH_PREFIX}/refresh", json={"refresh_token": tokens2["refresh_token"]})

        assert refresh1.status_code == status.HTTP_200_OK
        assert refresh2.status_code == status.HTTP_200_OK

        # Logout from device 1 should not affect device 2
        client.post(
            f"{AUTH_PREFIX}/logout",
            json={"refresh_token": tokens1["refresh_token"]},
            headers={"Authorization": f"Bearer {tokens1['access_token']}"}
        )

        # Device 2 should still work
        refresh2_after = client.post(f"{AUTH_PREFIX}/refresh", json={"refresh_token": tokens2["refresh_token"]})
        assert refresh2_after.status_code == status.HTTP_200_OK
