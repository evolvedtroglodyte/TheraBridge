/**
 * Comprehensive examples of using the typed API client and response types.
 * This file demonstrates all patterns for safe, type-aware API communication.
 *
 * Key benefits:
 * - Discriminated unions ensure exhaustive error handling
 * - Type guards provide runtime safety
 * - Clear separation between success and failure cases
 * - Automatic retry logic and timeout handling
 */

import { apiClient } from './api-client';
import type {
  PatientResponse,
  SessionResponse,
  GetPatientResponse,
  ListPatientsResponse,
  ApiResult,
  FailureResult,
  SuccessResult,
} from './api-types';
import {
  isSuccessResponse,
  isFailureResponse,
  isNetworkError,
  isTimeoutError,
  HTTP_STATUS,
} from './api-types';

// ============================================================================
// Pattern 1: Basic Result Pattern (Recommended)
// ============================================================================

/**
 * Using discriminated unions for exhaustive error handling.
 * This is the recommended pattern for all API calls.
 */
export async function exampleBasicPattern(): Promise<void> {
  const result = await apiClient.get<PatientResponse>('/api/patients/patient-123');

  // TypeScript forces you to handle both cases
  if (result.success) {
    // result.data is available here
    console.log('Patient name:', result.data.name);
    console.log('Status:', result.status); // Always 200-299
  } else {
    // result.error is available here
    console.error('Error:', result.error);
    console.error('Status:', result.status); // 4xx or 5xx
    // result.details is available for validation errors
  }
}

// ============================================================================
// Pattern 2: Type Guard Pattern
// ============================================================================

/**
 * Using type guards for explicit type checking.
 * Useful when processing responses in generic contexts.
 */
export async function exampleTypeGuardPattern(): Promise<void> {
  const result = await apiClient.get<PatientResponse>('/api/patients/patient-123');

  if (isSuccessResponse<PatientResponse>(result)) {
    // TypeScript narrows the type - only 'data' is available
    const patient = result.data;
    console.log('Found patient:', patient.name, patient.email);
  }

  if (isFailureResponse(result)) {
    // TypeScript narrows the type - only 'error' is available
    console.error('Failed with error:', result.error);
  }
}

// ============================================================================
// Pattern 3: Switch Pattern (Exhaustive)
// ============================================================================

/**
 * Using switch statements for exhaustive status checking.
 * Useful when you need different handling for specific status codes.
 */
export async function exampleSwitchPattern(): Promise<void> {
  const result = await apiClient.get<PatientResponse>('/api/patients/patient-123');

  switch (true) {
    case result.success && result.status === HTTP_STATUS.OK:
      console.log('Found patient:', result.data.name);
      break;

    case !result.success && result.status === HTTP_STATUS.NOT_FOUND:
      console.error('Patient not found');
      break;

    case !result.success && result.status === HTTP_STATUS.UNAUTHORIZED:
      console.error('Not authenticated');
      break;

    case !result.success && result.status >= 500:
      console.error('Server error:', result.error);
      break;

    default:
      console.error('Unexpected response:', result);
  }
}

// ============================================================================
// Pattern 4: Error Callback Pattern
// ============================================================================

/**
 * Using the onError callback for centralized error logging.
 * Useful for analytics, logging, and error recovery.
 */
export async function exampleErrorCallbackPattern(): Promise<void> {
  const result = await apiClient.get<PatientResponse>('/api/patients/patient-123', {
    onError: (error) => {
      // Handle all error types
      if (isNetworkError(error)) {
        console.error('Network error:', error.message);
        // Notify user about network issues
      } else if (isTimeoutError(error)) {
        console.error('Request timeout:', error.timeoutMs, 'ms');
        // Suggest retry
      } else if (isFailureResponse(error)) {
        console.error('API error:', error.status, error.error);
        // Log to analytics
      }
    },
  });
}

// ============================================================================
// Pattern 5: Retry Logic Pattern
// ============================================================================

/**
 * Configure automatic retry with exponential backoff.
 * Useful for unreliable networks or transient server errors.
 */
export async function exampleRetryPattern(): Promise<void> {
  const result = await apiClient.get<PatientResponse>('/api/patients/patient-123', {
    retry: {
      maxAttempts: 3,
      delayMs: 1000,
      backoffMultiplier: 2, // Retry delays: 1s, 2s, 4s
    },
    timeout: 10000,
  });

  if (result.success) {
    console.log('Success after retries:', result.data.name);
  } else {
    console.error('Failed after all retries:', result.error);
  }
}

// ============================================================================
// Pattern 6: POST/Create Pattern
// ============================================================================

/**
 * Creating a new resource with typed request and response.
 */
export async function exampleCreatePattern(): Promise<void> {
  const result = await apiClient.post<PatientResponse>('/api/patients/', {
    name: 'John Doe',
    email: 'john@example.com',
    phone: '+1-555-0123',
    therapist_id: 'therapist-123',
  });

  if (result.success) {
    console.log('Created patient:', result.data.id);
  } else if (isFailureResponse(result)) {
    // result is now FailureResult - has error and details properties
    if (result.status === HTTP_STATUS.UNPROCESSABLE_ENTITY) {
      // Validation error - result.details contains field errors
      console.error('Validation failed:', result.details);
    } else if (result.status === HTTP_STATUS.CONFLICT) {
      console.error('Patient already exists');
    } else {
      console.error('Creation failed:', result.error);
    }
  }
}

// ============================================================================
// Pattern 7: PUT/Update Pattern
// ============================================================================

/**
 * Updating a resource with typed request and response.
 */
export async function exampleUpdatePattern(): Promise<void> {
  const result = await apiClient.put<PatientResponse>(
    '/api/patients/patient-123',
    {
      name: 'Jane Doe',
      email: 'jane@example.com',
    }
  );

  if (result.success) {
    console.log('Updated patient:', result.data);
  } else if (result.status === HTTP_STATUS.NOT_FOUND) {
    console.error('Patient not found');
  }
}

// ============================================================================
// Pattern 8: DELETE Pattern
// ============================================================================

/**
 * Deleting a resource.
 * DELETE returns null as data on success.
 */
export async function exampleDeletePattern(): Promise<void> {
  const result = await apiClient.delete('/api/patients/patient-123');

  if (result.success) {
    // result.data is null for DELETE
    console.log('Patient deleted successfully');
  } else if (result.status === HTTP_STATUS.NOT_FOUND) {
    console.error('Patient not found');
  }
}

// ============================================================================
// Pattern 9: PATCH Pattern
// ============================================================================

/**
 * Partial update using PATCH.
 */
export async function examplePatchPattern(): Promise<void> {
  const result = await apiClient.patch<PatientResponse>(
    '/api/patients/patient-123',
    {
      phone: '+1-555-9999', // Only update phone
    }
  );

  if (result.success) {
    console.log('Patched patient:', result.data);
  }
}

// ============================================================================
// Pattern 10: Typed List Pattern
// ============================================================================

/**
 * Fetching a list of resources.
 */
export async function exampleListPattern(): Promise<void> {
  const result = await apiClient.get<PatientResponse[]>('/api/patients/');

  if (result.success) {
    // result.data is an array
    console.log(`Found ${result.data.length} patients`);
    for (const patient of result.data) {
      console.log(`- ${patient.name} (${patient.email})`);
    }
  }
}

// ============================================================================
// Pattern 11: Validation Error Handling
// ============================================================================

/**
 * Handling and displaying validation errors from the API.
 */
export async function exampleValidationErrorPattern(): Promise<void> {
  const result = await apiClient.post<PatientResponse>('/api/patients/', {
    name: '', // Invalid: empty name
    email: 'not-an-email', // Invalid: bad email
  });

  if (isFailureResponse(result) && result.status === HTTP_STATUS.UNPROCESSABLE_ENTITY) {
    // result.details contains field-level errors
    const fieldErrors = result.details as Record<string, string>;
    console.log('Validation errors:');
    for (const [field, message] of Object.entries(fieldErrors)) {
      console.log(`  ${field}: ${message}`);
    }

    // In a React component, you'd set these to display in a form:
    // setErrors(fieldErrors);
  }
}

// ============================================================================
// Pattern 12: Custom Error Type Checking
// ============================================================================

/**
 * Handling specific error types with custom logic.
 */
export async function exampleErrorTypePattern(): Promise<void> {
  const result = await apiClient.get<PatientResponse>('/api/patients/patient-123', {
    timeout: 5000,
    onError: (error) => {
      if (isNetworkError(error)) {
        // Network down - show offline message
        console.error('No internet connection');
      } else if (isTimeoutError(error)) {
        // Request took too long - might be slow connection
        console.error('Request timed out, check connection');
      } else if (isFailureResponse(error)) {
        // API returned an error
        switch (error.status) {
          case HTTP_STATUS.UNAUTHORIZED:
            // Token expired, need re-login
            console.error('Session expired');
            break;
          case HTTP_STATUS.FORBIDDEN:
            // Insufficient permissions
            console.error('Access denied');
            break;
          case HTTP_STATUS.NOT_FOUND:
            // Resource doesn't exist
            console.error('Not found');
            break;
          default:
            console.error(`API error: ${error.status} ${error.error}`);
        }
      }
    },
  });
}

// ============================================================================
// Pattern 13: React Hook Pattern (Recommended for Components)
// ============================================================================

/**
 * Example of using the API client in a React component.
 * This shows the recommended pattern for React integration.
 */
export async function exampleReactHookPattern() {
  // In a real component:
  // const [patient, setPatient] = useState<PatientResponse | null>(null);
  // const [error, setError] = useState<string | null>(null);
  // const [loading, setLoading] = useState(false);
  //
  // useEffect(() => {
  //   const fetchPatient = async () => {
  //     setLoading(true);
  //     const result = await apiClient.get<PatientResponse>('/api/patients/patient-123');
  //
  //     if (result.success) {
  //       setPatient(result.data);
  //       setError(null);
  //     } else {
  //       setPatient(null);
  //       setError(result.error);
  //     }
  //
  //     setLoading(false);
  //   };
  //
  //   fetchPatient();
  // }, [patientId]);
}

// ============================================================================
// Pattern 14: Async Function with Result Type
// ============================================================================

/**
 * Define strongly-typed async functions that return results.
 * This is useful for creating reusable API wrappers.
 */
async function getPatient(patientId: string): Promise<ApiResult<PatientResponse>> {
  return apiClient.get<PatientResponse>(`/api/patients/${patientId}`);
}

async function listPatients(): Promise<ApiResult<PatientResponse[]>> {
  return apiClient.get<PatientResponse[]>('/api/patients/');
}

async function createPatient(data: {
  name: string;
  email: string;
  phone?: string;
  therapist_id: string;
}): Promise<ApiResult<PatientResponse>> {
  return apiClient.post<PatientResponse>('/api/patients/', data);
}

async function updatePatient(
  patientId: string,
  data: Partial<PatientResponse>
): Promise<ApiResult<PatientResponse>> {
  return apiClient.put<PatientResponse>(`/api/patients/${patientId}`, data);
}

async function deletePatient(patientId: string): Promise<ApiResult<null>> {
  return apiClient.delete(`/api/patients/${patientId}`);
}

/**
 * Example of using these typed functions
 */
export async function exampleWrappedFunctionsPattern(): Promise<void> {
  const getResult = await getPatient('patient-123');

  if (getResult.success) {
    // Now update this patient
    const updateResult = await updatePatient('patient-123', {
      name: 'Updated Name',
    });

    if (updateResult.success) {
      console.log('Updated:', updateResult.data);
    }
  }
}

// ============================================================================
// Pattern 15: Promise.all with Multiple Requests
// ============================================================================

/**
 * Fetching multiple resources in parallel.
 */
export async function exampleParallelRequestsPattern(): Promise<void> {
  const [patient1Result, patient2Result, patientListResult] = await Promise.all([
    apiClient.get<PatientResponse>('/api/patients/patient-1'),
    apiClient.get<PatientResponse>('/api/patients/patient-2'),
    apiClient.get<PatientResponse[]>('/api/patients/'),
  ]);

  // Process results separately
  if (patient1Result.success) {
    console.log('Patient 1:', patient1Result.data.name);
  }

  if (patient2Result.success) {
    console.log('Patient 2:', patient2Result.data.name);
  }

  if (patientListResult.success) {
    console.log('Total patients:', patientListResult.data.length);
  }
}

// ============================================================================
// Summary: Key Benefits of This Pattern
// ============================================================================

/**
 * 1. TYPE SAFETY
 *    - TypeScript enforces handling both success and failure cases
 *    - Compile-time checks prevent missing error handling
 *
 * 2. EXHAUSTIVE ERROR HANDLING
 *    - Discriminated unions force you to handle all cases
 *    - Can't accidentally access .data on a failed request
 *
 * 3. CLEAR INTENT
 *    - Code is self-documenting: result.success tells the story
 *    - No exceptions to catch, no error codes to parse
 *
 * 4. COMPOSABLE
 *    - Easy to combine results from multiple requests
 *    - Works well with async/await and Promise.all
 *
 * 5. FLEXIBLE ERROR HANDLING
 *    - Type guards allow checking for specific error types
 *    - Can differentiate network errors from API errors
 *
 * 6. BUILT-IN RESILIENCE
 *    - Retry logic with exponential backoff
 *    - Timeout handling prevents hanging requests
 *    - Token refresh happens transparently
 */
