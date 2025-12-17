"""
Integration tests for patients router endpoints.

Tests cover:
- CRUD operations (Create, Read, List)
- Input validation (email format, phone format, name requirements)
- Therapist existence validation
- Patient listing with filters
- Error handling for invalid data
- Pagination limits

Note: Uses async_db_client fixture to test async endpoints with SQLite test database.
"""
import pytest
from fastapi import status
from uuid import uuid4
from app.models.db_models import Patient, User
from app.models.schemas import UserRole

# API prefix for patient endpoints
PATIENT_PREFIX = "/api/patients"


class TestCreatePatient:
    """Test patient creation endpoint"""

    def test_create_patient_success(self, async_db_client, test_db, therapist_user):
        """Test successful patient creation with all fields"""
        response = async_db_client.post(
            f"{PATIENT_PREFIX}/",
            json={
                "name": "John Doe",
                "email": "john.doe@example.com",
                "phone": "555-123-4567",  # Valid format without country code
                "therapist_id": str(therapist_user.id)
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify response structure
        assert "id" in data
        assert data["name"] == "John Doe"
        assert data["email"] == "john.doe@example.com"  # Should be normalized to lowercase
        assert data["phone"] == "5551234567"  # Should be normalized (digits only, no country code)
        assert data["therapist_id"] == str(therapist_user.id)
        assert "created_at" in data
        assert "updated_at" in data

        # Verify patient was created in database
        patient = test_db.query(Patient).filter(Patient.id == data["id"]).first()
        assert patient is not None
        assert patient.name == "John Doe"
        assert patient.therapist_id == therapist_user.id

    def test_create_patient_minimal_fields(self, async_db_client, test_db, therapist_user):
        """Test patient creation with only required fields (name and therapist_id)"""
        response = async_db_client.post(
            f"{PATIENT_PREFIX}/",
            json={
                "name": "Jane Smith",
                "therapist_id": str(therapist_user.id)
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["name"] == "Jane Smith"
        assert data["email"] is None
        assert data["phone"] is None
        assert data["therapist_id"] == str(therapist_user.id)

    def test_create_patient_email_normalization(self, async_db_client, therapist_user):
        """Test that email is normalized to lowercase"""
        response = async_db_client.post(
            f"{PATIENT_PREFIX}/",
            json={
                "name": "Test User",
                "email": "Test.User@EXAMPLE.COM",
                "therapist_id": str(therapist_user.id)
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == "test.user@example.com"

    def test_create_patient_phone_normalization(self, async_db_client, therapist_user):
        """Test that phone number is normalized (removes formatting characters)"""
        test_cases = [
            ("555-123-4567", "5551234567"),  # Dashes removed
            ("555.123.4567", "5551234567"),  # Dots removed
            ("555 123 4567", "5551234567"),  # Spaces removed
            ("+1-555-123-4567", "+15551234567"),  # Country code preserved
            ("+44 20 7123 4567", "+442071234567"),  # International format
        ]

        for input_phone, expected_phone in test_cases:
            response = async_db_client.post(
                f"{PATIENT_PREFIX}/",
                json={
                    "name": "Test User",
                    "phone": input_phone,
                    "therapist_id": str(therapist_user.id)
                }
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["phone"] == expected_phone, f"Failed for input: {input_phone}"

    def test_create_patient_invalid_email_format(self, async_db_client, therapist_user):
        """Test patient creation fails with invalid email format"""
        invalid_emails = [
            "not-an-email",
            "missing-at-sign.com",
            "@no-local-part.com",
            "no-domain@",
            "spaces in@email.com",
            "double@@at.com",
        ]

        for invalid_email in invalid_emails:
            response = async_db_client.post(
                f"{PATIENT_PREFIX}/",
                json={
                    "name": "Test User",
                    "email": invalid_email,
                    "therapist_id": str(therapist_user.id)
                }
            )

            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "email" in response.json()["detail"].lower()

    def test_create_patient_invalid_phone_format(self, async_db_client, therapist_user):
        """Test patient creation fails with invalid phone format"""
        invalid_phones = [
            "123",  # Too short (less than 7 digits)
            "abc-def-ghij",  # Non-numeric
            "12345678901234567890",  # Too long (>15 digits)
            "555",  # Too short (less than 7 digits)
            "(555) 123-4567",  # Starts with paren (no country code before it)
        ]

        for invalid_phone in invalid_phones:
            response = async_db_client.post(
                f"{PATIENT_PREFIX}/",
                json={
                    "name": "Test User",
                    "phone": invalid_phone,
                    "therapist_id": str(therapist_user.id)
                }
            )

            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "phone" in response.json()["detail"].lower(), f"Expected phone error for: {invalid_phone}"

    def test_create_patient_nonexistent_therapist(self, async_db_client):
        """Test patient creation fails with non-existent therapist_id"""
        nonexistent_id = uuid4()

        response = async_db_client.post(
            f"{PATIENT_PREFIX}/",
            json={
                "name": "Test User",
                "therapist_id": str(nonexistent_id)
            }
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "therapist" in response.json()["detail"].lower()
        assert str(nonexistent_id) in response.json()["detail"]

    def test_create_patient_wrong_user_role(self, async_db_client, test_db, patient_user):
        """Test patient creation fails when therapist_id references a non-therapist user"""
        response = async_db_client.post(
            f"{PATIENT_PREFIX}/",
            json={
                "name": "Test User",
                "therapist_id": str(patient_user.id)
            }
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "not a therapist" in response.json()["detail"].lower()

    def test_create_patient_missing_name(self, async_db_client, therapist_user):
        """Test patient creation fails with missing name"""
        response = async_db_client.post(
            f"{PATIENT_PREFIX}/",
            json={
                "therapist_id": str(therapist_user.id)
            }
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_patient_empty_name(self, async_db_client, therapist_user):
        """Test patient creation fails with empty name"""
        empty_names = ["", "   ", "\t", "\n"]

        for empty_name in empty_names:
            response = async_db_client.post(
                f"{PATIENT_PREFIX}/",
                json={
                    "name": empty_name,
                    "therapist_id": str(therapist_user.id)
                }
            )

            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "name" in response.json()["detail"].lower()

    def test_create_patient_name_too_long(self, async_db_client, therapist_user):
        """Test patient creation fails with name exceeding max length"""
        long_name = "A" * 256  # Max is 255 characters

        response = async_db_client.post(
            f"{PATIENT_PREFIX}/",
            json={
                "name": long_name,
                "therapist_id": str(therapist_user.id)
            }
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "name" in response.json()["detail"].lower()
        assert "255" in response.json()["detail"]

    def test_create_patient_missing_therapist_id(self, async_db_client):
        """Test patient creation fails with missing therapist_id"""
        response = async_db_client.post(
            f"{PATIENT_PREFIX}/",
            json={
                "name": "Test User"
            }
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_patient_invalid_therapist_id_format(self, async_db_client):
        """Test patient creation fails with invalid UUID format"""
        response = async_db_client.post(
            f"{PATIENT_PREFIX}/",
            json={
                "name": "Test User",
                "therapist_id": "not-a-uuid"
            }
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_patient_empty_email_string(self, async_db_client, therapist_user):
        """Test that empty email string is treated as None"""
        response = async_db_client.post(
            f"{PATIENT_PREFIX}/",
            json={
                "name": "Test User",
                "email": "",
                "therapist_id": str(therapist_user.id)
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] is None

    def test_create_patient_empty_phone_string(self, async_db_client, therapist_user):
        """Test that empty phone string is treated as None"""
        response = async_db_client.post(
            f"{PATIENT_PREFIX}/",
            json={
                "name": "Test User",
                "phone": "   ",
                "therapist_id": str(therapist_user.id)
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["phone"] is None


class TestGetPatient:
    """Test get patient by ID endpoint"""

    def test_get_patient_success(self, async_db_client, test_db, therapist_user):
        """Test successfully retrieving a patient by ID"""
        # Create test patient
        patient = Patient(
            name="John Doe",
            email="john@example.com",
            phone="+15551234567",
            therapist_id=therapist_user.id
        )
        test_db.add(patient)
        test_db.commit()
        test_db.refresh(patient)

        # Get patient
        response = async_db_client.get(f"{PATIENT_PREFIX}/{patient.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["id"] == str(patient.id)
        assert data["name"] == "John Doe"
        assert data["email"] == "john@example.com"
        assert data["phone"] == "+15551234567"
        assert data["therapist_id"] == str(therapist_user.id)

    def test_get_patient_not_found(self, async_db_client):
        """Test get patient fails with non-existent ID"""
        nonexistent_id = uuid4()

        response = async_db_client.get(f"{PATIENT_PREFIX}/{nonexistent_id}")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert str(nonexistent_id) in response.json()["detail"]

    def test_get_patient_invalid_uuid(self, async_db_client):
        """Test get patient fails with invalid UUID format"""
        response = async_db_client.get(f"{PATIENT_PREFIX}/not-a-uuid")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestListPatients:
    """Test list patients endpoint"""

    def test_list_all_patients(self, async_db_client, test_db, therapist_user):
        """Test listing all patients"""
        # Create test patients
        patients = [
            Patient(name="Patient 1", therapist_id=therapist_user.id),
            Patient(name="Patient 2", therapist_id=therapist_user.id),
            Patient(name="Patient 3", therapist_id=therapist_user.id),
        ]
        test_db.add_all(patients)
        test_db.commit()

        # List all patients
        response = async_db_client.get(f"{PATIENT_PREFIX}/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert len(data) == 3
        assert all("id" in patient for patient in data)
        assert all("name" in patient for patient in data)

    def test_list_patients_ordered_by_created_at_desc(self, async_db_client, test_db, therapist_user):
        """Test that patients are returned in descending order by created_at"""
        import time

        # Create patients with slight time delay to ensure ordering
        patient1 = Patient(name="First Patient", therapist_id=therapist_user.id)
        test_db.add(patient1)
        test_db.commit()
        time.sleep(0.01)

        patient2 = Patient(name="Second Patient", therapist_id=therapist_user.id)
        test_db.add(patient2)
        test_db.commit()
        time.sleep(0.01)

        patient3 = Patient(name="Third Patient", therapist_id=therapist_user.id)
        test_db.add(patient3)
        test_db.commit()

        # List all patients
        response = async_db_client.get(f"{PATIENT_PREFIX}/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Newest first
        assert data[0]["name"] == "Third Patient"
        assert data[1]["name"] == "Second Patient"
        assert data[2]["name"] == "First Patient"

    def test_list_patients_filter_by_therapist(self, async_db_client, test_db, therapist_user):
        """Test filtering patients by therapist_id"""
        # Create another therapist
        therapist2 = User(
            email="therapist2@test.com",
            hashed_password="hashed",
            full_name="Therapist 2",
            role=UserRole.therapist,
            is_active=True
        )
        test_db.add(therapist2)
        test_db.commit()
        test_db.refresh(therapist2)

        # Create patients for different therapists
        patients_t1 = [
            Patient(name="Patient 1 - T1", therapist_id=therapist_user.id),
            Patient(name="Patient 2 - T1", therapist_id=therapist_user.id),
        ]
        patients_t2 = [
            Patient(name="Patient 1 - T2", therapist_id=therapist2.id),
        ]
        test_db.add_all(patients_t1 + patients_t2)
        test_db.commit()

        # Filter by therapist 1
        response = async_db_client.get(f"{PATIENT_PREFIX}/?therapist_id={therapist_user.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert len(data) == 2
        assert all(p["therapist_id"] == str(therapist_user.id) for p in data)

        # Filter by therapist 2
        response = async_db_client.get(f"{PATIENT_PREFIX}/?therapist_id={therapist2.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert len(data) == 1
        assert data[0]["therapist_id"] == str(therapist2.id)

    def test_list_patients_filter_nonexistent_therapist(self, async_db_client):
        """Test filtering by non-existent therapist_id returns 404"""
        nonexistent_id = uuid4()

        response = async_db_client.get(f"{PATIENT_PREFIX}/?therapist_id={nonexistent_id}")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "therapist" in response.json()["detail"].lower()

    def test_list_patients_filter_non_therapist_user(self, async_db_client, patient_user):
        """Test filtering by non-therapist user returns 400"""
        response = async_db_client.get(f"{PATIENT_PREFIX}/?therapist_id={patient_user.id}")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "not a therapist" in response.json()["detail"].lower()

    def test_list_patients_empty_result(self, async_db_client):
        """Test listing patients when database is empty"""
        response = async_db_client.get(f"{PATIENT_PREFIX}/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data == []

    def test_list_patients_default_limit(self, async_db_client, test_db, therapist_user):
        """Test that default limit is applied (100)"""
        # Create more than 100 patients
        patients = [
            Patient(name=f"Patient {i}", therapist_id=therapist_user.id)
            for i in range(150)
        ]
        test_db.add_all(patients)
        test_db.commit()

        # List without limit parameter
        response = async_db_client.get(f"{PATIENT_PREFIX}/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should return default limit of 100
        assert len(data) == 100

    def test_list_patients_custom_limit(self, async_db_client, test_db, therapist_user):
        """Test custom limit parameter"""
        # Create test patients
        patients = [
            Patient(name=f"Patient {i}", therapist_id=therapist_user.id)
            for i in range(50)
        ]
        test_db.add_all(patients)
        test_db.commit()

        # List with limit=10
        response = async_db_client.get(f"{PATIENT_PREFIX}/?limit=10")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert len(data) == 10

    def test_list_patients_limit_validation(self, async_db_client):
        """Test limit parameter validation"""
        # Test limit too small (< 1)
        response = async_db_client.get(f"{PATIENT_PREFIX}/?limit=0")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "limit" in response.json()["detail"].lower()
        assert "positive" in response.json()["detail"].lower()

        response = async_db_client.get(f"{PATIENT_PREFIX}/?limit=-5")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        # Test limit too large (> 1000)
        response = async_db_client.get(f"{PATIENT_PREFIX}/?limit=1001")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "limit" in response.json()["detail"].lower()
        assert "1000" in response.json()["detail"]

    def test_list_patients_limit_edge_cases(self, async_db_client, test_db, therapist_user):
        """Test limit edge cases (1 and 1000)"""
        # Create test patients
        patients = [
            Patient(name=f"Patient {i}", therapist_id=therapist_user.id)
            for i in range(10)
        ]
        test_db.add_all(patients)
        test_db.commit()

        # Test limit=1
        response = async_db_client.get(f"{PATIENT_PREFIX}/?limit=1")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) == 1

        # Test limit=1000 (max allowed)
        response = async_db_client.get(f"{PATIENT_PREFIX}/?limit=1000")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) == 10  # Only 10 patients exist

    def test_list_patients_limit_invalid_type(self, async_db_client):
        """Test limit parameter with invalid type"""
        response = async_db_client.get(f"{PATIENT_PREFIX}/?limit=abc")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_list_patients_combined_filters(self, async_db_client, test_db, therapist_user):
        """Test combining therapist_id filter and limit"""
        # Create patients
        patients = [
            Patient(name=f"Patient {i}", therapist_id=therapist_user.id)
            for i in range(20)
        ]
        test_db.add_all(patients)
        test_db.commit()

        # Filter by therapist with limit
        response = async_db_client.get(
            f"{PATIENT_PREFIX}/?therapist_id={therapist_user.id}&limit=5"
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert len(data) == 5
        assert all(p["therapist_id"] == str(therapist_user.id) for p in data)


class TestPatientDataIntegrity:
    """Test data integrity and edge cases"""

    def test_patient_email_uniqueness_not_enforced(self, async_db_client, test_db, therapist_user):
        """Test that multiple patients can have the same email (not unique constraint)"""
        # Create first patient
        response1 = client.post(
            f"{PATIENT_PREFIX}/",
            json={
                "name": "Patient 1",
                "email": "shared@example.com",
                "therapist_id": str(therapist_user.id)
            }
        )
        assert response1.status_code == status.HTTP_200_OK

        # Create second patient with same email
        response2 = client.post(
            f"{PATIENT_PREFIX}/",
            json={
                "name": "Patient 2",
                "email": "shared@example.com",
                "therapist_id": str(therapist_user.id)
            }
        )
        assert response2.status_code == status.HTTP_200_OK

        # Both should exist
        all_patients = test_db.query(Patient).filter(
            Patient.email == "shared@example.com"
        ).all()
        assert len(all_patients) == 2

    def test_patient_timestamps(self, async_db_client, therapist_user):
        """Test that created_at and updated_at timestamps are set"""
        response = async_db_client.post(
            f"{PATIENT_PREFIX}/",
            json={
                "name": "Test Patient",
                "therapist_id": str(therapist_user.id)
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "created_at" in data
        assert "updated_at" in data
        assert data["created_at"] is not None
        assert data["updated_at"] is not None

    def test_patient_unicode_name(self, async_db_client, therapist_user):
        """Test patient creation with unicode characters in name"""
        unicode_names = [
            "François Müller",
            "María José García",
            "李明",
            "محمد علي",
            "Владимир Иванов",
        ]

        for unicode_name in unicode_names:
            response = async_db_client.post(
                f"{PATIENT_PREFIX}/",
                json={
                    "name": unicode_name,
                    "therapist_id": str(therapist_user.id)
                }
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["name"] == unicode_name

    def test_patient_special_characters_in_name(self, async_db_client, therapist_user):
        """Test patient creation with special characters in name"""
        special_names = [
            "O'Brien",
            "Mary-Anne Smith",
            "John Doe Jr.",
            "Dr. Smith, Ph.D.",
        ]

        for special_name in special_names:
            response = async_db_client.post(
                f"{PATIENT_PREFIX}/",
                json={
                    "name": special_name,
                    "therapist_id": str(therapist_user.id)
                }
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["name"] == special_name

    def test_email_max_length(self, async_db_client, therapist_user):
        """Test email validation respects RFC 5321 max length (320 chars)"""
        # Valid: exactly 320 characters
        local_part = "a" * 64
        domain_part = "b" * 243 + ".example.com"  # Total = 64 + 1 + 255 = 320
        valid_email = f"{local_part}@{domain_part}"

        response = async_db_client.post(
            f"{PATIENT_PREFIX}/",
            json={
                "name": "Test",
                "email": valid_email,
                "therapist_id": str(therapist_user.id)
            }
        )
        assert response.status_code == status.HTTP_200_OK

        # Invalid: exceeds 320 characters
        too_long_email = f"{local_part}@{domain_part}extra"

        response = async_db_client.post(
            f"{PATIENT_PREFIX}/",
            json={
                "name": "Test",
                "email": too_long_email,
                "therapist_id": str(therapist_user.id)
            }
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "320" in response.json()["detail"]
