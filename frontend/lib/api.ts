import type { Patient, Session, ExtractedNotes, SessionStatus } from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new ApiError(response.status, errorText || response.statusText);
  }

  return response.json();
}

// Patients API
export const getPatients = () => fetchApi<Patient[]>('/api/patients/');

export const getPatient = (id: string) => fetchApi<Patient>(`/api/patients/${id}`);

export const createPatient = (data: { name: string; email: string; phone?: string; therapist_id: string }) =>
  fetchApi<Patient>('/api/patients/', {
    method: 'POST',
    body: JSON.stringify(data),
  });

// Sessions API
export const getSessions = (patientId?: string, status?: SessionStatus) => {
  const params = new URLSearchParams();
  if (patientId) params.set('patient_id', patientId);
  if (status) params.set('status', status);
  const queryString = params.toString();
  return fetchApi<Session[]>(`/api/sessions/${queryString ? `?${queryString}` : ''}`);
};

export const getSession = (id: string) => fetchApi<Session>(`/api/sessions/${id}`);

export const getSessionNotes = (id: string) =>
  fetchApi<ExtractedNotes>(`/api/sessions/${id}/notes`);

export const uploadSession = async (patientId: string, file: File): Promise<Session> => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(
    `${API_BASE_URL}/api/sessions/upload?patient_id=${patientId}`,
    {
      method: 'POST',
      body: formData,
    }
  );

  if (!response.ok) {
    const errorText = await response.text();
    throw new ApiError(response.status, errorText || response.statusText);
  }

  return response.json();
};

// Fetcher for SWR
export const fetcher = <T,>(url: string): Promise<T> => {
  if (url.startsWith('/')) {
    return fetchApi<T>(url);
  }
  return fetchApi<T>(url);
};
