import type { WSEvent } from '@/types/transcription';

const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private jobId: string;
  private onMessage: (event: WSEvent) => void;
  private onError?: (error: Event) => void;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  constructor(
    jobId: string,
    onMessage: (event: WSEvent) => void,
    onError?: (error: Event) => void
  ) {
    this.jobId = jobId;
    this.onMessage = onMessage;
    this.onError = onError;
  }

  connect(): void {
    try {
      this.ws = new WebSocket(`${WS_BASE_URL}/ws/transcription/${this.jobId}`);

      this.ws.onopen = () => {
        console.log(`WebSocket connected for job ${this.jobId}`);
        this.reconnectAttempts = 0;
      };

      this.ws.onmessage = (event) => {
        try {
          const data: WSEvent = JSON.parse(event.data);
          this.onMessage(data);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        if (this.onError) {
          this.onError(error);
        }
      };

      this.ws.onclose = () => {
        console.log(`WebSocket closed for job ${this.jobId}`);
        this.attemptReconnect();
      };
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
    }
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(
        `Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`
      );

      setTimeout(() => {
        this.connect();
      }, this.reconnectDelay * this.reconnectAttempts);
    }
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  send(message: string): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(message);
    }
  }
}
