"use client";

import { useEffect, useState, useCallback, useRef } from "react";

interface PipelineEvent {
  timestamp: string;
  patient_id: string;
  phase: "TRANSCRIPT" | "WAVE1" | "WAVE2";
  event: string;
  status: string;
  session_id?: string;
  session_date?: string;
  duration_ms?: number;
  details?: Record<string, any>;
}

interface UsePipelineEventsOptions {
  patientId: string;
  enabled?: boolean;
  onEvent?: (event: PipelineEvent) => void;
  onWave1SessionComplete?: (sessionId: string, sessionDate: string) => void;
  onWave2SessionComplete?: (sessionId: string, sessionDate: string) => void;
}

export function usePipelineEvents(options: UsePipelineEventsOptions) {
  const {
    patientId,
    enabled = true,
    onEvent,
    onWave1SessionComplete,
    onWave2SessionComplete,
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const [events, setEvents] = useState<PipelineEvent[]>([]);
  const eventSourceRef = useRef<EventSource | null>(null);
  const handleEventRef = useRef<((event: PipelineEvent) => void) | null>(null);

  const handleEvent = useCallback(
    (event: PipelineEvent) => {
      // Add to events list
      setEvents((prev) => [...prev, event]);

      // Call custom event handler
      if (onEvent) {
        onEvent(event);
      }

      // Detect Wave 1 session completion
      if (
        event.phase === "WAVE1" &&
        event.event === "COMPLETE" &&
        event.status === "success" &&
        event.session_id &&
        event.session_date
      ) {
        console.log(
          `✅ Wave 1 complete for session ${event.session_date} (${event.session_id})`
        );
        if (onWave1SessionComplete) {
          onWave1SessionComplete(event.session_id, event.session_date);
        }
      }

      // Detect Wave 2 session completion
      if (
        event.phase === "WAVE2" &&
        event.event === "COMPLETE" &&
        event.status === "success" &&
        event.session_id &&
        event.session_date
      ) {
        console.log(
          `✅ Wave 2 complete for session ${event.session_date} (${event.session_id})`
        );
        if (onWave2SessionComplete) {
          onWave2SessionComplete(event.session_id, event.session_date);
        }
      }
    },
    [onEvent, onWave1SessionComplete, onWave2SessionComplete]
  );

  // Update ref when handleEvent changes
  useEffect(() => {
    handleEventRef.current = handleEvent;
  }, [handleEvent]);

  useEffect(() => {
    if (!enabled || !patientId) {
      console.log('[SSE] Connection disabled or no patient ID');

      // Clean up existing connection if patient ID was cleared
      if (eventSourceRef.current) {
        console.log('[SSE] Patient ID cleared - disconnecting existing SSE');
        eventSourceRef.current.close();
        eventSourceRef.current = null;
        setIsConnected(false);
        setConnectionError(null);
      }
      return;
    }

    // Check if this is a patient ID change (not initial mount)
    const previousPatientId = eventSourceRef.current?.url.split('/').pop();
    if (previousPatientId && previousPatientId !== patientId) {
      console.log(`[SSE] Patient ID changed: ${previousPatientId} → ${patientId}`);
      console.log('[SSE] Disconnecting from old patient...');
      eventSourceRef.current.close();
      eventSourceRef.current = null;
      setIsConnected(false);
      setConnectionError(null);
    }

    console.log(`[SSE] Connecting to patient ${patientId}...`);

    // Create EventSource connection
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const sseUrl = `${apiUrl}/api/sse/events/${patientId}`;

    console.log(`[SSE] URL: ${sseUrl}`);

    const eventSource = new EventSource(sseUrl);
    eventSourceRef.current = eventSource;

    eventSource.onopen = () => {
      console.log(`📡 SSE connected to patient ${patientId}`);
      setIsConnected(true);
      setConnectionError(null);
    };

    eventSource.onmessage = (messageEvent) => {
      try {
        const event: PipelineEvent = JSON.parse(messageEvent.data);

        // Ignore initial "connected" event
        if (event.event === 'connected') {
          console.log('[SSE] ✓ Connection confirmed by server');
          return;
        }

        // Use ref to avoid stale closure
        if (handleEventRef.current) {
          handleEventRef.current(event);
        }
      } catch (error) {
        console.error("[SSE] Failed to parse event:", error);
        console.error("[SSE] Raw data:", messageEvent.data);
      }
    };

    eventSource.onerror = (error) => {
      console.error("[SSE] Connection error:", error);

      // Check readyState to determine error type
      const readyState = eventSource.readyState;

      if (readyState === EventSource.CLOSED) {
        console.error(`[SSE] ✗ Connection closed by server (patient ${patientId} may not exist)`);
        setConnectionError('Patient not found (404) or forbidden (403)');
        setIsConnected(false);

        // Close connection permanently for 404/403
        eventSource.close();
        eventSourceRef.current = null;
      } else if (readyState === EventSource.CONNECTING) {
        console.log('[SSE] Reconnecting...');
        setConnectionError('Reconnecting...');
        setIsConnected(false);
      } else {
        console.error('[SSE] ✗ Unknown error state');
        setConnectionError('Connection failed');
        setIsConnected(false);
      }
    };

    // Cleanup on unmount or patient ID change
    return () => {
      console.log(`📡 SSE disconnected from patient ${patientId}`);
      eventSource.close();
      setIsConnected(false);
      setConnectionError(null);
    };
  }, [enabled, patientId]);

  return {
    isConnected,
    connectionError,
    events,
    latestEvent: events[events.length - 1] || null,
  };
}
