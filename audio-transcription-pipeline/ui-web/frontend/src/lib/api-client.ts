import type {
  TranscriptionResult,
  JobResponse,
  JobStatusResponse,
} from '@/types/transcription';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class APIClient {
  private baseURL: string;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  /**
   * Upload an audio file for transcription
   */
  async uploadFile(file: File): Promise<JobResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${this.baseURL}/api/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Upload failed' }));
      throw new Error(error.detail || 'Upload failed');
    }

    return response.json();
  }

  /**
   * Get transcription result by job ID
   */
  async getTranscription(jobId: string): Promise<TranscriptionResult> {
    const response = await fetch(`${this.baseURL}/api/transcriptions/${jobId}`);

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Failed to fetch transcription' }));
      throw new Error(error.detail || 'Failed to fetch transcription');
    }

    return response.json();
  }

  /**
   * Get job status with progress
   */
  async getJobStatus(jobId: string): Promise<JobStatusResponse> {
    const response = await fetch(`${this.baseURL}/api/transcriptions/${jobId}/status`);

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Failed to fetch status' }));
      throw new Error(error.detail || 'Failed to fetch status');
    }

    return response.json();
  }

  /**
   * List all transcriptions
   */
  async listTranscriptions(): Promise<TranscriptionResult[]> {
    const response = await fetch(`${this.baseURL}/api/transcriptions`);

    if (!response.ok) {
      throw new Error('Failed to fetch transcriptions');
    }

    const data = await response.json();
    return data.jobs;
  }

  /**
   * Delete a transcription
   */
  async deleteTranscription(jobId: string): Promise<void> {
    const response = await fetch(`${this.baseURL}/api/transcriptions/${jobId}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      throw new Error('Failed to delete transcription');
    }
  }
}

export const apiClient = new APIClient();
