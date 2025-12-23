#!/usr/bin/env python3
"""
Test script for patient consistency endpoint
Tests the /api/sessions/patient/{patient_id}/consistency endpoint
"""

import os
import sys
from datetime import datetime
from supabase import create_client, Client

# Set environment variables
os.environ["SUPABASE_URL"] = "https://rfckpldoohyjctrqxmiv.supabase.co"
os.environ["SUPABASE_KEY"] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJmY2twbGRvb2h5amN0cnF4bWl2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjYzMjc3MDUsImV4cCI6MjA4MTkwMzcwNX0.M7_2AJ_V_yMy9X5GNiL3fuQTG0kC1KXNTNqQRqdus80"
os.environ["OPENAI_API_KEY"] = "dummy"  # Not needed for this test
os.environ["ENVIRONMENT"] = "test"

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from app.routers.sessions import get_patient_consistency
from app.database import get_db

# Demo patient ID from seed data
DEMO_PATIENT_ID = "00000000-0000-0000-0000-000000000003"


async def test_consistency_endpoint():
    """Test the consistency calculation endpoint"""
    print("\n" + "="*80)
    print("🧪 Testing Patient Consistency Endpoint")
    print("="*80 + "\n")

    # Get database client
    db = next(get_db())

    # Fetch sessions first to show what we're working with
    print("📊 Fetching demo patient sessions...")
    sessions_response = (
        db.table("therapy_sessions")
        .select("id, session_date")
        .eq("patient_id", DEMO_PATIENT_ID)
        .order("session_date", desc=False)
        .execute()
    )

    sessions = sessions_response.data
    print(f"   Found {len(sessions)} sessions\n")

    if sessions:
        print("   Session dates:")
        for i, session in enumerate(sessions, 1):
            date = datetime.fromisoformat(session["session_date"].replace("Z", "+00:00"))
            print(f"   {i}. {date.strftime('%Y-%m-%d %H:%M')}")
        print()

    # Call the consistency endpoint
    print("🔍 Calculating consistency metrics...")
    result = await get_patient_consistency(
        patient_id=DEMO_PATIENT_ID,
        days=90,
        db=db
    )

    print("\n" + "="*80)
    print("✅ RESULTS")
    print("="*80 + "\n")

    print(f"📈 Overall Consistency Score: {result['consistency_score']}/100")
    print(f"📅 Attendance Rate: {result['attendance_rate']}%")
    print(f"⏱️  Average Gap Between Sessions: {result['average_gap_days']} days")
    print(f"🔥 Longest Streak: {result['longest_streak_weeks']} weeks")
    print(f"❌ Missed Weeks: {result['missed_weeks']}")
    print(f"📊 Total Sessions: {result['total_sessions']} / {result['expected_sessions']} expected")
    print(f"📆 Period: {result['period_start'][:10]} to {result['period_end'][:10]}")

    print(f"\n📊 Weekly Attendance Data ({len(result['weekly_data'])} weeks):")
    for week_data in result['weekly_data'][:10]:  # Show first 10 weeks
        status = "✓" if week_data['attended'] == 1 else "✗"
        count = week_data['session_count']
        print(f"   {week_data['week']}: {status} ({count} session{'s' if count != 1 else ''})")

    if len(result['weekly_data']) > 10:
        print(f"   ... and {len(result['weekly_data']) - 10} more weeks")

    print("\n" + "="*80)
    print("✅ Test completed successfully!")
    print("="*80 + "\n")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_consistency_endpoint())
