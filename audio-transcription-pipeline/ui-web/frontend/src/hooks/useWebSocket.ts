import { useEffect, useRef, useState } from 'react';
import { WebSocketClient } from '@/lib/websocket';
import type { WSEvent, JobStatusResponse } from '@/types/transcription';

interface UseWebSocketReturn {
  status: JobStatusResponse | null;
  isConnected: boolean;
  error: string | null;
}

export function useWebSocket(jobId: string | null): UseWebSocketReturn {
  const [status, setStatus] = useState<JobStatusResponse | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const wsClientRef = useRef<WebSocketClient | null>(null);

  useEffect(() => {
    if (!jobId) return;

    // Create WebSocket client
    const wsClient = new WebSocketClient(
      jobId,
      (event: WSEvent) => {
        console.log('[WebSocket] Received event:', event);

        if (event.type === 'progress') {
          console.log('[WebSocket] Progress update:', {
            stage: event.stage,
            progress: event.progress,
          });
          setStatus({
            job_id: event.job_id,
            status: 'processing',
            progress: event.progress || 0,
            stage: event.stage || 'processing',
          });
        } else if (event.type === 'completed') {
          console.log('[WebSocket] Processing completed!');
          setStatus({
            job_id: event.job_id,
            status: 'completed',
            progress: 1.0,
            stage: 'completed',
          });
        } else if (event.type === 'error') {
          console.error('[WebSocket] Error event:', event.error);
          setError(event.error || 'Unknown error occurred');
          setStatus({
            job_id: event.job_id,
            status: 'failed',
            progress: 0,
            stage: 'failed',
            error: event.error,
          });
        }
      },
      (err) => {
        console.error('WebSocket error:', err);
        setError('Connection error');
        setIsConnected(false);
      }
    );

    wsClient.connect();
    wsClientRef.current = wsClient;
    setIsConnected(true);

    // Cleanup on unmount
    return () => {
      wsClient.disconnect();
      wsClientRef.current = null;
      setIsConnected(false);
    };
  }, [jobId]);

  return { status, isConnected, error };
}
