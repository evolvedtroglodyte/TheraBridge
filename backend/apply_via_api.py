#!/usr/bin/env python3
"""Apply migrations using Supabase Management API."""

import requests
import sys
from pathlib import Path

PROJECT_REF = "rfckpldoohyjctrqxmiv"
SERVICE_KEY = "sb_secret_HtR41uMvaTUXZvKn0pSE6Q_Uwg8boP_"
SUPABASE_URL = "https://rfckpldoohyjctrqxmiv.supabase.co"

print("=" * 70)
print("🚀 Applying Migrations via Management API")
print("=" * 70)

def read_sql(filename):
    path = Path(__file__).parent / "supabase" / filename
    return path.read_text()

def execute_sql(sql, description):
    """Execute SQL using Supabase Management API."""
    print(f"\n📝 {description}")
    print("-" * 70)
    
    # Try using the database REST API
    url = f"{SUPABASE_URL}/rest/v1/rpc/exec"
    headers = {
        "apikey": SERVICE_KEY,
        "Authorization": f"Bearer {SERVICE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }
    
    # This won't work - Supabase doesn't expose raw SQL execution via REST
    print("   ⚠️  Management API doesn't support raw SQL")
    return False

# Since API approach won't work, provide manual instructions
print("\n" + "=" * 70)
print("📋 MANUAL MIGRATION REQUIRED")
print("=" * 70)
print("\nSupabase doesn't allow programmatic SQL execution for security.")
print("Please copy/paste the following SQL queries:\n")

print("🔗 Go to: https://supabase.com/dashboard/project/rfckpldoohyjctrqxmiv/sql\n")

migrations = [
    ("migrations/007_add_demo_mode_support.sql", "MIGRATION 1: Schema Changes"),
    ("seed_demo_data.sql", "MIGRATION 2: Seed Function"),
    ("cleanup_demo_data.sql", "MIGRATION 3: Cleanup Function")
]

for filename, title in migrations:
    sql = read_sql(filename)
    print("─" * 70)
    print(title)
    print("─" * 70)
    print(sql)
    print("\n✅ Copy above, paste in SQL Editor, click RUN\n")

print("=" * 70)
print("🧪 VERIFICATION QUERY")
print("=" * 70)
print("\nSELECT * FROM seed_demo_user_sessions(gen_random_uuid());")
print("\n✅ Should return patient_id and array of 10 UUIDs\n")
