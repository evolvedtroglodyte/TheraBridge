# WebSocket API - Real-time Session Progress Updates

## Overview

The TherapyBridge backend provides a WebSocket endpoint for real-time session processing progress updates. This allows frontend clients to receive live updates as audio files are transcribed and notes are extracted, without polling.

## Endpoint

```
ws://localhost:8000/api/sessions/ws/{session_id}?token={jwt_token}
```

**Production:**
```
wss://api.therapybridge.com/api/sessions/ws/{session_id}?token={jwt_token}
```

## Authentication

WebSocket connections require JWT authentication via query parameter:

```javascript
const ws = new WebSocket(
  `ws://localhost:8000/api/sessions/ws/${sessionId}?token=${jwtToken}`
);
```

**Authentication flow:**
1. Client obtains JWT token from `/api/v1/login` endpoint
2. Client includes token in WebSocket connection URL as query parameter
3. Server validates token before accepting connection
4. Server verifies user has access to the requested session
5. Connection is accepted or rejected with appropriate WebSocket close code

**Authorization rules:**
- **Therapists**: Can monitor any session
- **Patients**: Can only monitor their own sessions
- **Admins**: Can monitor any session

## Message Format

All messages are sent as JSON objects.

### Progress Update Message

Server sends progress updates whenever processing status changes:

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "transcribing",
  "progress": 45,
  "message": "Transcribing audio with Whisper...",
  "updated_at": "2025-12-19T10:30:00Z",
  "created_at": "2025-12-19T10:28:00Z",
  "estimated_time_remaining": 30,
  "error": null
}
```

**Fields:**
- `session_id` (string): UUID of the session
- `status` (string): Current processing status (see Status Values below)
- `progress` (integer): Progress percentage (0-100)
- `message` (string): Human-readable status description
- `updated_at` (string): ISO 8601 timestamp of last update
- `created_at` (string): ISO 8601 timestamp when progress tracking started
- `estimated_time_remaining` (integer|null): Estimated seconds remaining (optional)
- `error` (string|null): Error message if status is "failed"

### Status Values

| Status | Progress | Description |
|--------|----------|-------------|
| `uploading` | 0-20% | File upload in progress |
| `transcribing` | 20-60% | Converting audio to text with Whisper |
| `transcribed` | 60% | Transcription complete |
| `extracting_notes` | 60-95% | Generating clinical notes with GPT-4 |
| `processed` | 100% | Session fully processed and complete |
| `failed` | N/A | Processing failed (check `error` field) |

### Heartbeat/Ping Message

Server sends periodic ping messages every 30 seconds to keep connection alive:

```json
{
  "type": "ping",
  "timestamp": "2025-12-19T10:30:00Z"
}
```

Clients should ignore ping messages or respond with acknowledgment (optional).

## Client Implementation Examples

### JavaScript/TypeScript (Browser)

```javascript
function connectToSession(sessionId, jwtToken) {
  const ws = new WebSocket(
    `ws://localhost:8000/api/sessions/ws/${sessionId}?token=${jwtToken}`
  );

  ws.onopen = () => {
    console.log('WebSocket connected');
  };

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);

    if (data.type === 'ping') {
      // Heartbeat - connection is alive
      return;
    }

    // Progress update
    console.log(`Progress: ${data.progress}% - ${data.message}`);

    // Update UI
    updateProgressBar(data.progress);
    updateStatusText(data.message);

    // Handle completion or failure
    if (data.status === 'processed') {
      console.log('Session processing complete!');
      ws.close();
    } else if (data.status === 'failed') {
      console.error('Processing failed:', data.error);
      ws.close();
    }
  };

  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
  };

  ws.onclose = (event) => {
    console.log('WebSocket closed:', event.code, event.reason);
  };

  return ws;
}
```

### React Hook

```typescript
import { useEffect, useState } from 'react';

interface ProgressUpdate {
  session_id: string;
  status: string;
  progress: number;
  message: string;
  updated_at: string;
  estimated_time_remaining?: number;
  error?: string;
}

function useSessionProgress(sessionId: string, token: string) {
  const [progress, setProgress] = useState<ProgressUpdate | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const ws = new WebSocket(
      `ws://localhost:8000/api/sessions/ws/${sessionId}?token=${token}`
    );

    ws.onopen = () => {
      setIsConnected(true);
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      // Ignore heartbeat messages
      if (data.type === 'ping') return;

      setProgress(data);

      // Auto-close on completion
      if (data.status === 'processed' || data.status === 'failed') {
        ws.close();
      }
    };

    ws.onerror = () => {
      setError('WebSocket connection failed');
      setIsConnected(false);
    };

    ws.onclose = () => {
      setIsConnected(false);
    };

    return () => {
      ws.close();
    };
  }, [sessionId, token]);

  return { progress, isConnected, error };
}

// Usage in component
function UploadProgress({ sessionId }: { sessionId: string }) {
  const token = getAuthToken(); // Your auth token function
  const { progress, isConnected, error } = useSessionProgress(sessionId, token);

  if (error) return <div>Error: {error}</div>;
  if (!isConnected) return <div>Connecting...</div>;
  if (!progress) return <div>Waiting for updates...</div>;

  return (
    <div>
      <h3>{progress.message}</h3>
      <progress value={progress.progress} max={100} />
      <p>{progress.progress}%</p>
      {progress.estimated_time_remaining && (
        <p>ETA: {progress.estimated_time_remaining}s</p>
      )}
      {progress.error && <p style={{ color: 'red' }}>Error: {progress.error}</p>}
    </div>
  );
}
```

### Python Client (using websockets library)

```python
import asyncio
import websockets
import json

async def monitor_session(session_id: str, jwt_token: str):
    uri = f"ws://localhost:8000/api/sessions/ws/{session_id}?token={jwt_token}"

    async with websockets.connect(uri) as websocket:
        print(f"Connected to session {session_id}")

        async for message in websocket:
            data = json.loads(message)

            if data.get("type") == "ping":
                # Heartbeat
                continue

            # Progress update
            print(f"Progress: {data['progress']}% - {data['message']}")

            if data['status'] == 'processed':
                print("Session processing complete!")
                break
            elif data['status'] == 'failed':
                print(f"Processing failed: {data['error']}")
                break

# Run
asyncio.run(monitor_session("session-uuid", "jwt-token"))
```

## Error Handling

### WebSocket Close Codes

| Code | Reason | Description |
|------|--------|-------------|
| 1000 | Normal closure | Connection closed normally after completion |
| 1008 | Policy violation | Authentication failed, session not found, or not authorized |
| 1011 | Server error | Internal server error during processing |

### Common Error Scenarios

**Authentication Required (1008)**
```
Reason: "Authentication required"
```
Client did not provide `token` query parameter.

**Invalid Authentication (1008)**
```
Reason: "Invalid authentication"
```
JWT token is invalid, expired, or user account is inactive.

**Session Not Found (1008)**
```
Reason: "Session not found"
```
The requested session ID does not exist in the database.

**Not Authorized (1008)**
```
Reason: "Not authorized to access this session"
```
User does not have permission to access this session (e.g., patient trying to access another patient's session).

## Connection Lifecycle

1. **Client initiates connection** with JWT token
2. **Server authenticates** token and verifies session access
3. **Server accepts connection** and immediately sends current progress (if available)
4. **Server sends updates** whenever progress changes
5. **Server sends ping** every 30 seconds to keep connection alive
6. **Client or server closes connection** when:
   - Session processing is complete (`status: "processed"`)
   - Processing fails (`status: "failed"`)
   - Client disconnects
   - Authentication expires or fails
   - Network error occurs

## Testing

Use the provided test script:

```bash
cd backend
python test_websocket_endpoint.py
```

**Before running:**
1. Update `SESSION_ID` and `JWT_TOKEN` in the script
2. Start the backend server: `uvicorn app.main:app --reload`
3. Ensure a session is being processed

## Integration with Processing Pipeline

To send progress updates from the processing pipeline, use the ProgressTracker service:

```python
from app.services.progress_tracker import get_progress_tracker
from app.models.schemas import SessionStatus

# Get tracker instance
progress_tracker = get_progress_tracker()

# Update progress
await progress_tracker.update_progress(
    session_id=session.id,
    status=SessionStatus.transcribing,
    progress=45,
    message="Transcribing audio with Whisper...",
    estimated_time_remaining=30
)
```

All connected WebSocket clients will automatically receive the update in real-time.

## Production Considerations

### Scaling

The current implementation uses in-memory storage for subscriptions and is suitable for **single-instance deployments**.

For **multi-instance production deployments**, consider:
- Redis Pub/Sub for cross-instance message broadcasting
- Sticky sessions at load balancer level
- Dedicated WebSocket server instances

### Security

- Always use WSS (WebSocket Secure) in production
- JWT tokens should have reasonable expiration times (1-2 hours)
- Implement rate limiting on WebSocket connections
- Monitor connection count and set limits per user

### Monitoring

Log events to monitor:
- WebSocket connection attempts (success/failure)
- Authentication failures
- Active connection count
- Message send failures
- Unexpected disconnections

## Troubleshooting

### Connection Immediately Closes

**Symptom:** WebSocket connects then immediately closes with code 1008

**Possible Causes:**
1. Missing or invalid JWT token
2. Session ID doesn't exist
3. User not authorized to access session

**Solution:** Check browser console for close reason, verify token is valid

### No Progress Updates Received

**Symptom:** Connection established but no messages received

**Possible Causes:**
1. Session processing hasn't started yet
2. ProgressTracker service not integrated with processing pipeline
3. Session already completed before connection

**Solution:** Verify session is being processed, check server logs

### Connection Drops After ~30 Seconds

**Symptom:** Connection closes after approximately 30 seconds

**Possible Causes:**
1. Client not responding to ping messages
2. Network timeout
3. Proxy/firewall blocking WebSocket

**Solution:** Ensure client keeps connection alive, check network configuration

## API Reference

### Endpoint
```
GET ws://localhost:8000/api/sessions/ws/{session_id}
```

### Path Parameters
- `session_id` (UUID, required): Session to monitor

### Query Parameters
- `token` (string, required): JWT access token

### Response Messages
- Progress updates (JSON with session status and progress)
- Ping messages (heartbeat every 30 seconds)

### WebSocket Close Codes
- `1000`: Normal closure (processing complete)
- `1008`: Authentication/authorization failure
- `1011`: Internal server error
