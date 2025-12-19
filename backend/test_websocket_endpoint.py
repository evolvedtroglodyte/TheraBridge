"""
Test script for WebSocket endpoint - session progress updates

This script demonstrates the WebSocket connection and verifies:
1. Authentication with JWT token
2. Real-time progress updates
3. Heartbeat/ping-pong mechanism
4. Graceful disconnection

Run this script while a session is being processed to see live updates.
"""
import asyncio
import websockets
import json
from uuid import UUID

# Configuration
BACKEND_URL = "ws://localhost:8000/api/sessions/ws"
# Replace with actual session ID and JWT token from your test environment
SESSION_ID = "00000000-0000-0000-0000-000000000000"  # Example UUID
JWT_TOKEN = "your-jwt-token-here"  # Get from login endpoint


async def test_websocket_connection():
    """Test WebSocket connection to session progress endpoint"""
    uri = f"{BACKEND_URL}/{SESSION_ID}?token={JWT_TOKEN}"

    print(f"🔌 Connecting to: {uri}")

    try:
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected successfully!")
            print("📡 Listening for progress updates...\n")

            # Listen for messages
            async for message in websocket:
                data = json.loads(message)

                # Handle different message types
                if data.get("type") == "ping":
                    print(f"💓 Heartbeat: {data.get('timestamp')}")
                elif "progress" in data:
                    # Progress update
                    print(f"📊 Progress Update:")
                    print(f"   Status: {data.get('status')}")
                    print(f"   Progress: {data.get('progress')}%")
                    print(f"   Message: {data.get('message')}")
                    if data.get('estimated_time_remaining'):
                        print(f"   ETA: {data.get('estimated_time_remaining')}s")
                    if data.get('error'):
                        print(f"   ❌ Error: {data.get('error')}")
                    print()

                    # Exit if processing is complete or failed
                    if data.get('status') in ['processed', 'failed']:
                        print("🏁 Session processing complete. Disconnecting...")
                        break
                else:
                    print(f"📩 Received: {data}")

    except websockets.exceptions.InvalidStatusCode as e:
        print(f"❌ Connection rejected: {e}")
        print("   Possible reasons:")
        print("   - Invalid JWT token")
        print("   - Session not found")
        print("   - Not authorized to access this session")
    except websockets.exceptions.WebSocketException as e:
        print(f"❌ WebSocket error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        print("\n👋 WebSocket connection closed")


if __name__ == "__main__":
    print("=" * 60)
    print("WebSocket Progress Updates Test")
    print("=" * 60)
    print()
    print("⚠️  Before running this test:")
    print("1. Start the backend server: uvicorn app.main:app --reload")
    print("2. Update SESSION_ID and JWT_TOKEN in this script")
    print("3. Ensure a session is being processed")
    print()

    asyncio.run(test_websocket_connection())
