/**
 * Demo API Client
 * Handles demo initialization, reset, and status checks
 */

import { apiClient } from './api-client';
import { demoTokenStorage } from './demo-token-storage';

export interface DemoInitResponse {
  demo_token: string;
  patient_id: string;
  session_ids: string[];
  expires_at: string;
  message: string;
}

export interface DemoResetResponse {
  patient_id: string;
  session_ids: string[];
  message: string;
}

export interface SessionStatus {
  session_id: string;
  session_date: string;
  has_transcript: boolean;
  wave1_complete: boolean;
  wave2_complete: boolean;
}

export interface DemoStatusResponse {
  demo_token: string;
  patient_id: string;
  session_count: number;
  created_at: string;
  expires_at: string;
  is_expired: boolean;
  analysis_status: string;
  wave1_complete: number;
  wave2_complete: number;
  sessions: SessionStatus[];
}

export const demoApiClient = {
  /**
   * Initialize a new demo user with 10 pre-loaded sessions
   * Note: This can take 60-90 seconds due to Wave 1 + Wave 2 analysis
   */
  async initialize(): Promise<DemoInitResponse | null> {
    console.log('[Demo API] Initializing demo user...');

    // Use 120-second timeout for demo initialization (Wave 1 + Wave 2 takes ~90s)
    const result = await apiClient.post<DemoInitResponse>('/api/demo/initialize', {}, {
      timeout: 120000, // 2 minutes
    });

    if (result.success) {
      console.log('[Demo API] ✓ Demo initialized:', result.data);

      // Save token to localStorage
      demoTokenStorage.store(
        result.data.demo_token,
        result.data.patient_id,
        result.data.session_ids,
        result.data.expires_at
      );

      return result.data;
    } else {
      console.error('[Demo API] ✗ Demo initialization failed:', result.error);
      return null;
    }
  },

  /**
   * Reset demo user (delete all sessions and re-seed with 10 fresh ones)
   * Note: This can take 60-90 seconds due to Wave 1 + Wave 2 analysis
   */
  async reset(): Promise<DemoResetResponse | null> {
    const token = demoTokenStorage.getToken();
    if (!token) {
      console.error('[Demo API] No demo token found for reset');
      return null;
    }

    console.log('[Demo API] Resetting demo...');

    const result = await apiClient.post<DemoResetResponse>(
      '/api/demo/reset',
      {},
      {
        headers: {
          'X-Demo-Token': token,
        },
        timeout: 120000, // 2 minutes for Wave 1 + Wave 2 analysis
      }
    );

    if (result.success) {
      console.log('[Demo API] ✓ Demo reset:', result.data);
      return result.data;
    } else {
      console.error('[Demo API] ✗ Demo reset failed:', result.error);
      return null;
    }
  },

  /**
   * Get demo user status (session count, expiry, etc.)
   */
  async getStatus(): Promise<DemoStatusResponse | null> {
    const token = demoTokenStorage.getToken();
    if (!token) {
      console.error('[Demo API] No demo token found for status check');
      return null;
    }

    const result = await apiClient.get<DemoStatusResponse>('/api/demo/status', {
      headers: {
        'X-Demo-Token': token,
      },
    });

    if (result.success) {
      return result.data;
    } else {
      console.error('[Demo API] ✗ Status check failed:', result.error);
      return null;
    }
  },

  /**
   * Upload a demo transcript (session_12_thriving.json, etc.)
   */
  async uploadDemoTranscript(sessionFile: string): Promise<{ session_id: string; status: string } | null> {
    const token = demoTokenStorage.getToken();
    if (!token) {
      console.error('[Demo API] No demo token found for upload');
      return null;
    }

    console.log('[Demo API] Uploading demo transcript:', sessionFile);

    const result = await apiClient.post<{ session_id: string; status: string; message: string }>(
      `/api/sessions/upload-demo-transcript?session_file=${sessionFile}`,
      {},
      {
        headers: {
          'X-Demo-Token': token,
        },
      }
    );

    if (result.success) {
      console.log('[Demo API] ✓ Demo transcript uploaded:', result.data);
      return result.data;
    } else {
      console.error('[Demo API] ✗ Demo transcript upload failed:', result.error);
      return null;
    }
  },

  /**
   * Stop all running background processes for the demo
   * Terminates transcript population, Wave 1, and Wave 2 analysis
   */
  async stop(): Promise<{ message: string; terminated: string[] } | null> {
    const token = demoTokenStorage.getToken();
    if (!token) {
      console.error('[Demo API] No demo token found for stop');
      return null;
    }

    console.log('[Demo API] Stopping demo processing...');

    const result = await apiClient.post<{ message: string; patient_id: string; terminated: string[] }>(
      '/api/demo/stop',
      {},
      {
        headers: {
          'X-Demo-Token': token,
        },
      }
    );

    if (result.success) {
      console.log('[Demo API] ✓ Demo processing stopped:', result.data);
      return result.data;
    } else {
      console.error('[Demo API] ✗ Stop demo failed:', result.error);
      return null;
    }
  },
};
