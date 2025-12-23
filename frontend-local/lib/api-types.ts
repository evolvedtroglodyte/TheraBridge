/**
 * Comprehensive API response types with strict typing.
 * This module defines all possible API response shapes, error types, and status codes.
 *
 * Key patterns:
 * - Success responses use ApiResponse<T> with data payload
 * - Error responses include status code, error message, and optional details
 * - Union types allow exhaustive type-checking of response combinations
 * - Branded types for IDs ensure compile-time safety
 */

import type { PatientId, SessionId, UserId } from './types';

// ============================================================================
// HTTP Status Codes (Type-Safe Constants)
// ============================================================================

export const HTTP_STATUS = {
  OK: 200,
  CREATED: 201,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  CONFLICT: 409,
  UNPROCESSABLE_ENTITY: 422,
  INTERNAL_SERVER_ERROR: 500,
  SERVICE_UNAVAILABLE: 503,
} as const;

export type HttpStatusCode = (typeof HTTP_STATUS)[keyof typeof HTTP_STATUS];

// ============================================================================
// Error Response Types
// ============================================================================

/**
 * Validation error detail for a single field
 */
export interface ValidationErrorDetail {
  readonly loc: ReadonlyArray<string | number>;
  readonly msg: string;
  readonly type: string;
}

/**
 * Generic error response from API
 */
export interface ApiErrorResponse {
  readonly detail: string;
}

/**
 * Validation error response (422 Unprocessable Entity)
 */
export interface ValidationErrorResponse {
  readonly detail: ReadonlyArray<ValidationErrorDetail>;
}

/**
 * Error response with optional details
 */
export interface ErrorResponseWithDetails {
  readonly status: HttpStatusCode;
  readonly error: string;
  readonly message: string;
  readonly details?: Record<string, unknown>;
  readonly timestamp: string;
}

/**
 * Union type for all possible error response shapes
 */
export type ErrorResponseBody = ApiErrorResponse | ValidationErrorResponse | ErrorResponseWithDetails;

// ============================================================================
// Success Response Types
// ============================================================================

/**
 * Generic success response wrapper for all API endpoints
 * Use this type for successful API calls
 *
 * @template T - The type of data in the response
 *
 * @example
 * ```ts
 * type GetPatientResponse = ApiResponse<Patient>;
 * type ListPatientsResponse = ApiResponse<ReadonlyArray<Patient>>;
 * type CreatePatientResponse = ApiResponse<Patient>;
 * ```
 */
export interface ApiResponse<T> {
  readonly status: HttpStatusCode;
  readonly data: T;
  readonly timestamp?: string;
  readonly message?: string;
}

/**
 * Paginated response for list endpoints
 */
export interface PaginatedResponse<T> {
  readonly items: ReadonlyArray<T>;
  readonly total: number;
  readonly page: number;
  readonly per_page: number;
  readonly total_pages: number;
}

/**
 * Success response with pagination
 */
export interface ApiPaginatedResponse<T> extends ApiResponse<PaginatedResponse<T>> {}

/**
 * Empty success response (for DELETE, etc.)
 */
export interface ApiEmptyResponse extends ApiResponse<null> {}

// ============================================================================
// Union Types for Complete Response Handling
// ============================================================================

/**
 * Success result type
 */
export interface SuccessResult<T> {
  readonly success: true;
  readonly status: HttpStatusCode;
  readonly data: T;
  readonly error?: never;
}

/**
 * Failure result type
 */
export interface FailureResult {
  readonly success: false;
  readonly status: HttpStatusCode;
  readonly error: string;
  readonly details?: Record<string, unknown>;
  readonly data?: never;
}

/**
 * Result type that is either success or failure (discriminated union)
 * Use this for better error handling with type-safe exhaustiveness checking
 *
 * @template T - The type of data in the success case
 *
 * @example
 * ```ts
 * const result = await apiClient.getPatient(patientId);
 * if (result.success) {
 *   console.log(result.data.name);
 * } else {
 *   console.error(result.error);
 * }
 * ```
 */
export type ApiResult<T> = SuccessResult<T> | FailureResult;

// ============================================================================
// Specific Endpoint Response Types
// ============================================================================

/**
 * Authentication responses
 */
export interface AuthTokenResponse {
  readonly access_token: string;
  readonly refresh_token: string;
  readonly token_type: string;
  readonly expires_in: number;
}

export interface LoginSuccessResponse extends ApiResponse<AuthTokenResponse> {}
export interface LoginFailureResponse extends FailureResult {}
export type LoginResponse = LoginSuccessResponse | LoginFailureResponse;

/**
 * Token refresh response
 */
export interface RefreshTokenResponse {
  readonly access_token: string;
  readonly refresh_token: string;
  readonly token_type: string;
  readonly expires_in: number;
}

export interface RefreshSuccessResponse extends ApiResponse<RefreshTokenResponse> {}
export interface RefreshFailureResponse extends FailureResult {}
export type RefreshResponse = RefreshSuccessResponse | RefreshFailureResponse;

/**
 * Patient endpoint responses
 */
export interface PatientResponse {
  readonly id: PatientId;
  readonly name: string;
  readonly email: string;
  readonly phone: string | null;
  readonly therapist_id: UserId;
  readonly created_at: string;
  readonly updated_at: string;
}

export interface GetPatientSuccessResponse extends ApiResponse<PatientResponse> {}
export interface GetPatientFailureResponse extends FailureResult {}
export type GetPatientResponse = GetPatientSuccessResponse | GetPatientFailureResponse;

export interface ListPatientsSuccessResponse extends ApiResponse<ReadonlyArray<PatientResponse>> {}
export interface ListPatientsFailureResponse extends FailureResult {}
export type ListPatientsResponse = ListPatientsSuccessResponse | ListPatientsFailureResponse;

export interface CreatePatientSuccessResponse extends ApiResponse<PatientResponse> {}
export interface CreatePatientFailureResponse extends FailureResult {}
export type CreatePatientResponse = CreatePatientSuccessResponse | CreatePatientFailureResponse;

export interface UpdatePatientSuccessResponse extends ApiResponse<PatientResponse> {}
export interface UpdatePatientFailureResponse extends FailureResult {}
export type UpdatePatientResponse = UpdatePatientSuccessResponse | UpdatePatientFailureResponse;

export interface DeletePatientSuccessResponse extends ApiEmptyResponse {}
export interface DeletePatientFailureResponse extends FailureResult {}
export type DeletePatientResponse = DeletePatientSuccessResponse | DeletePatientFailureResponse;

/**
 * Session endpoint responses
 */
export interface SessionResponse {
  readonly id: SessionId;
  readonly patient_id: PatientId;
  readonly therapist_id: UserId;
  readonly session_date: string;
  readonly duration_seconds: number | null;
  readonly audio_filename: string | null;
  readonly audio_url: string | null;
  readonly transcript_text: string | null;
  readonly transcript_segments: ReadonlyArray<{
    readonly start: number;
    readonly end: number;
    readonly speaker: string;
    readonly text: string;
  }> | null;
  readonly extracted_notes: {
    readonly key_topics: ReadonlyArray<string>;
    readonly topic_summary: string;
    readonly strategies: ReadonlyArray<{
      readonly name: string;
      readonly category: string;
      readonly status: string;
      readonly context: string;
    }>;
    readonly emotional_themes: ReadonlyArray<string>;
    readonly triggers: ReadonlyArray<{
      readonly trigger: string;
      readonly context: string;
      readonly severity: string;
    }>;
    readonly action_items: ReadonlyArray<{
      readonly task: string;
      readonly category: string;
      readonly details: string;
    }>;
    readonly significant_quotes: ReadonlyArray<{
      readonly quote: string;
      readonly context: string;
      readonly timestamp_start?: number | null;
    }>;
    readonly session_mood: string;
    readonly mood_trajectory: string;
    readonly follow_up_topics: ReadonlyArray<string>;
    readonly unresolved_concerns: ReadonlyArray<string>;
    readonly risk_flags: ReadonlyArray<{
      readonly type: string;
      readonly evidence: string;
      readonly severity: string;
    }>;
    readonly therapist_notes: string;
    readonly patient_summary: string;
  } | null;
  readonly status: 'uploading' | 'transcribing' | 'transcribed' | 'extracting_notes' | 'processed' | 'failed';
  readonly error_message: string | null;
  readonly created_at: string;
  readonly updated_at: string;
  readonly processed_at: string | null;
}

export interface GetSessionSuccessResponse extends ApiResponse<SessionResponse> {}
export interface GetSessionFailureResponse extends FailureResult {}
export type GetSessionResponse = GetSessionSuccessResponse | GetSessionFailureResponse;

export interface ListSessionsSuccessResponse extends ApiResponse<ReadonlyArray<SessionResponse>> {}
export interface ListSessionsFailureResponse extends FailureResult {}
export type ListSessionsResponse = ListSessionsSuccessResponse | ListSessionsFailureResponse;

export interface UploadSessionSuccessResponse extends ApiResponse<SessionResponse> {}
export interface UploadSessionFailureResponse extends FailureResult {}
export type UploadSessionResponse = UploadSessionSuccessResponse | UploadSessionFailureResponse;

export interface DeleteSessionSuccessResponse extends ApiEmptyResponse {}
export interface DeleteSessionFailureResponse extends FailureResult {}
export type DeleteSessionResponse = DeleteSessionSuccessResponse | DeleteSessionFailureResponse;

// ============================================================================
// Type Guards for Safe Response Handling
// ============================================================================

/**
 * Type guard to check if a response is successful
 *
 * @example
 * ```ts
 * const result = await fetchPatient(id);
 * if (isSuccessResponse(result)) {
 *   // TypeScript knows result has 'data' and 'success' properties
 *   console.log(result.data.name);
 * }
 * ```
 */
export function isSuccessResponse<T>(response: unknown): response is SuccessResult<T> {
  return (
    typeof response === 'object' &&
    response !== null &&
    'success' in response &&
    (response as Record<string, unknown>).success === true
  );
}

/**
 * Type guard to check if a response is a failure
 *
 * @example
 * ```ts
 * const result = await fetchPatient(id);
 * if (isFailureResponse(result)) {
 *   // TypeScript knows result has 'error' property
 *   console.error(result.error);
 * }
 * ```
 */
export function isFailureResponse(response: unknown): response is FailureResult {
  return (
    typeof response === 'object' &&
    response !== null &&
    'success' in response &&
    (response as Record<string, unknown>).success === false
  );
}

/**
 * Type guard to check if an error is a validation error
 */
export function isValidationError(error: unknown): error is ValidationErrorResponse {
  return (
    typeof error === 'object' &&
    error !== null &&
    'detail' in error &&
    Array.isArray((error as Record<string, unknown>).detail)
  );
}

/**
 * Type guard to check if an object is an ApiResponse
 */
export function isApiResponse<T>(value: unknown): value is ApiResponse<T> {
  return (
    typeof value === 'object' &&
    value !== null &&
    'status' in value &&
    'data' in value &&
    typeof (value as Record<string, unknown>).status === 'number'
  );
}

// ============================================================================
// Helper Functions for Response Creation
// ============================================================================

/**
 * Create a typed success result
 *
 * @example
 * ```ts
 * const result = createSuccessResult(patient, 200);
 * ```
 */
export function createSuccessResult<T>(
  data: T,
  status: HttpStatusCode = HTTP_STATUS.OK
): SuccessResult<T> {
  return {
    success: true,
    status,
    data,
  };
}

/**
 * Create a typed failure result
 *
 * @example
 * ```ts
 * const result = createFailureResult('Patient not found', 404);
 * ```
 */
export function createFailureResult(
  error: string,
  status: HttpStatusCode = HTTP_STATUS.INTERNAL_SERVER_ERROR,
  details?: Record<string, unknown>
): FailureResult {
  return {
    success: false,
    status,
    error,
    details,
  };
}

// ============================================================================
// Network Error Handling
// ============================================================================

/**
 * Represents a network error that occurred before reaching the API
 */
export interface NetworkError {
  readonly type: 'network';
  readonly message: string;
  readonly originalError?: Error;
}

/**
 * Represents a timeout error
 */
export interface TimeoutError {
  readonly type: 'timeout';
  readonly message: string;
  readonly timeoutMs: number;
}

/**
 * Represents an unknown error (parsing, etc.)
 */
export interface UnknownError {
  readonly type: 'unknown';
  readonly message: string;
  readonly originalError?: Error;
}

/**
 * All possible error types that can occur during API communication
 */
export type ApiErrorType = FailureResult | NetworkError | TimeoutError | UnknownError;

/**
 * Type guard for network errors
 */
export function isNetworkError(error: unknown): error is NetworkError {
  return (
    typeof error === 'object' &&
    error !== null &&
    'type' in error &&
    (error as Record<string, unknown>).type === 'network'
  );
}

/**
 * Type guard for timeout errors
 */
export function isTimeoutError(error: unknown): error is TimeoutError {
  return (
    typeof error === 'object' &&
    error !== null &&
    'type' in error &&
    (error as Record<string, unknown>).type === 'timeout'
  );
}

/**
 * Type guard for unknown errors
 */
export function isUnknownError(error: unknown): error is UnknownError {
  return (
    typeof error === 'object' &&
    error !== null &&
    'type' in error &&
    (error as Record<string, unknown>).type === 'unknown'
  );
}

// ============================================================================
// Request Options
// ============================================================================

/**
 * Extended request options for API calls
 */
export interface ApiRequestOptions extends RequestInit {
  /** Override default timeout (ms) */
  timeout?: number;
  /** Include retry logic */
  retry?: {
    readonly maxAttempts: number;
    readonly delayMs: number;
    readonly backoffMultiplier?: number;
  };
  /** Custom error handler */
  onError?: (error: ApiErrorType) => void;
}
