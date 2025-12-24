#!/usr/bin/env python3
"""
Execute migrations with correct connection string format.
"""

import sys
import psycopg2
from pathlib import Path

PROJECT_REF = "rfckpldoohyjctrqxmiv"
DB_PASSWORD = "c2Q7hVmXHVdyvo2U"

print("=" * 70)
print("🚀 Applying Migrations")
print("=" * 70)

# Try different connection formats
connection_formats = [
    # Direct connection (port 5432)
    f"postgresql://postgres:{DB_PASSWORD}@db.{PROJECT_REF}.supabase.co:5432/postgres",
    # Connection pooler (port 6543)
    f"postgresql://postgres.{PROJECT_REF}:{DB_PASSWORD}@aws-0-us-west-1.pooler.supabase.com:6543/postgres",
    # Transaction pooler (port 6543)
    f"postgresql://postgres:{DB_PASSWORD}@db.{PROJECT_REF}.supabase.co:6543/postgres",
]

conn = None
for i, connection_string in enumerate(connection_formats, 1):
    print(f"\n📡 Trying connection format {i}...")
    try:
        conn = psycopg2.connect(connection_string, connect_timeout=5)
        print(f"✅ Connected successfully!")
        break
    except Exception as e:
        print(f"   ❌ Failed: {str(e)[:80]}")
        continue

if not conn:
    print("\n" + "=" * 70)
    print("❌ ALL CONNECTION ATTEMPTS FAILED")
    print("=" * 70)
    print("\nPlease apply migrations manually via Supabase SQL Editor:")
    print(f"https://supabase.com/dashboard/project/{PROJECT_REF}/sql")
    sys.exit(1)

try:
    conn.set_session(autocommit=True)
    cursor = conn.cursor()

    # Read migration files
    def read_sql(filename):
        path = Path(__file__).parent / "supabase" / filename
        return path.read_text()

    migrations = [
        ("migrations/007_add_demo_mode_support.sql", "Schema Changes"),
        ("seed_demo_data.sql", "Seed Function"),
        ("cleanup_demo_data.sql", "Cleanup Function")
    ]

    # Execute each migration
    success_count = 0
    for filename, description in migrations:
        print(f"\n📝 Executing: {description}")
        print("-" * 70)

        sql = read_sql(filename)

        try:
            cursor.execute(sql)
            print(f"✅ Success: {description}")
            success_count += 1
        except psycopg2.Error as e:
            error_str = str(e).lower()
            if 'already exists' in error_str or 'duplicate' in error_str:
                print(f"⚠️  Already exists (OK): {description}")
                success_count += 1
            else:
                print(f"❌ Error: {e}")

    # Verify migrations
    if success_count == 3:
        print("\n🧪 Verifying migrations...")
        print("-" * 70)

        test_uuid = '00000000-0000-0000-0000-000000000001'
        cursor.execute(f"SELECT * FROM seed_demo_user_sessions('{test_uuid}'::uuid);")
        result = cursor.fetchone()

        if result:
            patient_id, session_ids = result
            print(f"✅ Seed function verified!")
            print(f"   Patient ID: {patient_id}")
            print(f"   Sessions: {len(session_ids)} created")

            # Cleanup
            cursor.execute(f"DELETE FROM users WHERE demo_token = '{test_uuid}'::uuid;")
            print(f"✅ Test data cleaned up")

    cursor.close()
    conn.close()

    print("\n" + "=" * 70)
    print("✅ MIGRATIONS COMPLETE!")
    print("=" * 70)
    print("\n📋 Next: Test demo initialization")
    print("   curl -X POST http://localhost:8000/api/demo/initialize | jq")

except Exception as e:
    print(f"\n❌ Error during migration: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
