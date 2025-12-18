import type { Patient, Session, ExtractedNotes, SessionStatus, Template } from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Custom error class for API errors
 * Includes HTTP status code and error message from the server
 */
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
export const getPatients = (): Promise<Patient[]> => fetchApi<Patient[]>('/api/v1/patients/');

export const getPatient = (id: string): Promise<Patient> => fetchApi<Patient>(`/api/v1/patients/${id}`);

export const createPatient = (data: { name: string; email: string; phone?: string; therapist_id: string }): Promise<Patient> =>
  fetchApi<Patient>('/api/v1/patients/', {
    method: 'POST',
    body: JSON.stringify(data),
  });

// Sessions API
export const getSessions = (patientId?: string, status?: SessionStatus): Promise<Session[]> => {
  const params = new URLSearchParams();
  if (patientId) params.set('patient_id', patientId);
  if (status) params.set('status', status);
  const queryString = params.toString();
  return fetchApi<Session[]>(`/api/v1/sessions/${queryString ? `?${queryString}` : ''}`);
};

export const getSession = (id: string): Promise<Session> => fetchApi<Session>(`/api/v1/sessions/${id}`);

export const getSessionNotes = (id: string): Promise<ExtractedNotes> =>
  fetchApi<ExtractedNotes>(`/api/v1/sessions/${id}/notes`);

export const uploadSession = async (patientId: string, file: File): Promise<Session> => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(
    `${API_BASE_URL}/api/v1/sessions/upload?patient_id=${patientId}`,
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

// Templates API
export const getTemplates = (templateType?: string, includeShared?: boolean): Promise<Template[]> => {
  const params = new URLSearchParams();
  if (templateType) params.set('template_type', templateType);
  if (includeShared !== undefined) params.set('include_shared', String(includeShared));
  const queryString = params.toString();
  return fetchApi<Template[]>(`/api/v1/templates/${queryString ? `?${queryString}` : ''}`);
};

export const getTemplate = (id: string): Promise<Template> =>
  fetchApi<Template>(`/api/v1/templates/${id}`);

// Fetcher for SWR - typed for use with SWR hooks
export const fetcher = async <T,>(url: string): Promise<T> => {
  if (url.startsWith('/')) {
    return fetchApi<T>(url);
  }
  return fetchApi<T>(url);
};
