"""
Add hashed_password column to users table if it doesn't exist
"""
from app.database import sync_engine
from sqlalchemy import text

def add_password_column():
    """Add hashed_password column to users table"""
    with sync_engine.connect() as conn:
        try:
            # Check if column exists
            result = conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name='users' AND column_name='hashed_password'
            """))

            if result.fetchone():
                print("✅ hashed_password column already exists")
            else:
                # Add the column
                conn.execute(text("""
                    ALTER TABLE users
                    ADD COLUMN hashed_password VARCHAR NOT NULL DEFAULT 'temp'
                """))
                conn.commit()
                print("✅ Added hashed_password column to users table")

        except Exception as e:
            print(f"❌ Error: {e}")
            conn.rollback()

if __name__ == "__main__":
    add_password_column()
