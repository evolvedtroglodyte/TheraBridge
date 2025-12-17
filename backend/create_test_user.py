"""
Create a test user for authentication testing
"""
from app.database import SessionLocal
from app.models.db_models import User, UserRole
from app.auth.models import AuthSession  # Import to resolve relationship
from app.auth.utils import get_password_hash
import uuid

def create_test_user():
    """Create a test therapist user"""
    db = SessionLocal()

    try:
        # Check if user already exists
        existing = db.query(User).filter(User.email == "test@therapist.com").first()
        if existing:
            print(f"✅ Test user already exists: {existing.email}")
            return

        # Create new test user
        test_user = User(
            id=uuid.uuid4(),
            email="test@therapist.com",
            hashed_password=get_password_hash("password123"),
            full_name="Test Therapist",
            role=UserRole.THERAPIST,
            is_active=True
        )

        db.add(test_user)
        db.commit()
        db.refresh(test_user)

        print(f"✅ Created test user:")
        print(f"   Email: {test_user.email}")
        print(f"   Password: password123")
        print(f"   Role: {test_user.role.value}")
        print(f"   ID: {test_user.id}")

    except Exception as e:
        print(f"❌ Error creating test user: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_test_user()
