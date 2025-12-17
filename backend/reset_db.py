"""
Drop and recreate all database tables (DESTRUCTIVE - development only!)
"""
import asyncio
from app.database import engine, Base
from app.models.db_models import User, Patient, Session  # Import all models
from app.auth.models import AuthSession  # Import auth models

async def reset_database():
    """Drop all tables and recreate them"""
    print("⚠️  WARNING: This will DELETE ALL DATA in the database!")
    print("   Dropping all tables...")

    async with engine.begin() as conn:
        # Drop all tables
        await conn.run_sync(Base.metadata.drop_all)
        print("✅ All tables dropped")

        # Recreate all tables
        await conn.run_sync(Base.metadata.create_all)
        print("✅ All tables recreated with current schema")

if __name__ == "__main__":
    asyncio.run(reset_database())
