import { tokenStorage } from './token-storage';
import { getValidatedApiUrl } from './env-validation';
import type {
  ApiResult,
  ApiErrorType,
  ApiRequestOptions,
  FailureResult,
  RefreshTokenResponse,
  HttpStatusCode,
} from './api-types';
import {
  HTTP_STATUS,
  isFailureResponse,
  isNetworkError,
  isTimeoutError,
  createFailureResult,
  createSuccessResult,
  isValidationError,
} from './api-types';

// Get validated API base URL (throws error if invalid)
// Falls back to localhost if validation fails (development mode)
let API_BASE_URL: string;
try {
  API_BASE_URL = getValidatedApiUrl();
} catch (error) {
  // In development, fall back to localhost
  API_BASE_URL = 'http://localhost:8000';
  console.warn('Failed to get validated API URL, falling back to localhost:', error);
}

/**
 * Custom error class for API errors with full response details
 */
export class ApiClientError extends Error {
  constructor(
    public readonly status: number,
    public readonly message: string,
    public readonly details?: Record<string, unknown>
  ) {
    super(message);
    this.name = 'ApiClientError';
    Object.setPrototypeOf(this, ApiClientError.prototype);
  }
}

/**
 * Authenticated API client with built-in token refresh and error handling.
 * All methods return typed ApiResult<T> for discriminated union error handling.
 *
 * @example
 * ```ts
 * const result = await apiClient.get<Patient>('/api/v1/patients/123');
 * if (result.success) {
 *   console.log(result.data.name);
 * } else {
 *   console.error(result.error, result.status);
 * }
 * ```
 */
class ApiClient {
  /**
   * Make authenticated API request with full error handling.
   * Automatically adds Authorization header and handles token refresh on 401.
   * Returns discriminated union type for exhaustive error handling.
   *
   * @template T - The expected response data type
   * @param endpoint - API endpoint (e.g., '/api/v1/patients/123')
   * @param options - Request options including custom timeout, retry logic, etc.
   * @returns ApiResult<T> - Success or failure result with full type information
   */
  async request<T>(
    endpoint: string,
    options: ApiRequestOptions = {}
  ): Promise<ApiResult<T>> {
    const { timeout = 30000, retry = { maxAttempts: 1, delayMs: 1000 }, onError, ...fetchOptions } = options;

    let lastError: ApiErrorType | null = null;
    const maxAttempts = retry.maxAttempts || 1;
    let currentAttempt = 0;

    while (currentAttempt < maxAttempts) {
      try {
        currentAttempt++;

        const accessToken = tokenStorage.getAccessToken();

        const config: RequestInit = {
          ...fetchOptions,
          headers: {
            'Content-Type': 'application/json',
            ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
            ...fetchOptions.headers,
          },
        };

        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeout);

        let response: Response;
        try {
          response = await fetch(`${API_BASE_URL}${endpoint}`, {
            ...config,
            signal: controller.signal,
          });
        } catch (error) {
          clearTimeout(timeoutId);

          if (error instanceof DOMException && error.name === 'AbortError') {
            lastError = {
              type: 'timeout',
              message: `Request timeout after ${timeout}ms`,
              timeoutMs: timeout,
            };
          } else {
            lastError = {
              type: 'network',
              message: error instanceof Error ? error.message : 'Network request failed',
              originalError: error instanceof Error ? error : undefined,
            };
          }

          if (currentAttempt >= maxAttempts) {
            onError?.(lastError);
            return this.errorToResult(lastError);
          }

          // Wait before retry
          if (retry && retry.delayMs) {
            const delayMs = retry.delayMs * Math.pow(retry.backoffMultiplier || 1, currentAttempt - 1);
            await new Promise((resolve) => setTimeout(resolve, delayMs));
          }
          continue;
        }

        clearTimeout(timeoutId);

        // Handle 401 (token expired) - attempt refresh
        if (response.status === 401) {
          const refreshResult = await this.handleTokenRefresh();
          if (!refreshResult.success) {
            onError?.(refreshResult as unknown as ApiErrorType);
            return refreshResult as unknown as ApiResult<T>;
          }

          // Retry original request with refreshed token
          if (currentAttempt < maxAttempts) {
            await new Promise((resolve) => setTimeout(resolve, 100));
            continue;
          }
        }

        // Parse response body
        let responseBody: unknown;
        try {
          const contentType = response.headers.get('content-type');
          if (contentType?.includes('application/json')) {
            responseBody = await response.json();
          } else {
            responseBody = await response.text();
          }
        } catch (parseError) {
          lastError = {
            type: 'unknown',
            message: 'Failed to parse response body',
            originalError: parseError instanceof Error ? parseError : undefined,
          };

          if (currentAttempt >= maxAttempts) {
            onError?.(lastError);
            return this.errorToResult(lastError);
          }
          continue;
        }

        // Handle HTTP error status codes
        if (!response.ok) {
          const failureResult = this.createErrorResult(response.status, responseBody);
          lastError = failureResult;

          if (currentAttempt >= maxAttempts) {
            onError?.(failureResult);
            return failureResult as unknown as ApiResult<T>;
          }

          // Retry on server errors (5xx), but not client errors (4xx)
          if (response.status >= 500 && retry && currentAttempt < maxAttempts) {
            const delayMs = (retry.delayMs || 1000) * Math.pow(retry.backoffMultiplier || 1, currentAttempt - 1);
            await new Promise((resolve) => setTimeout(resolve, delayMs));
            continue;
          }

          return failureResult as unknown as ApiResult<T>;
        }

        // Success response
        return createSuccessResult<T>(responseBody as T, response.status as any);
      } catch (error) {
        // Unexpected error
        lastError = {
          type: 'unknown',
          message: error instanceof Error ? error.message : 'Unknown error occurred',
          originalError: error instanceof Error ? error : undefined,
        };

        if (currentAttempt >= maxAttempts) {
          onError?.(lastError);
          return this.errorToResult(lastError);
        }
      }
    }

    // All retries exhausted
    if (lastError) {
      onError?.(lastError);
      return this.errorToResult(lastError);
    }

    return createFailureResult('Request failed', HTTP_STATUS.INTERNAL_SERVER_ERROR);
  }

  /**
   * Handle token refresh when 401 received.
   * Returns typed result to prevent cascading errors.
   */
  private async handleTokenRefresh(): Promise<ApiResult<RefreshTokenResponse>> {
    const refreshToken = tokenStorage.getRefreshToken();

    if (!refreshToken) {
      tokenStorage.clearTokens();
      // Redirect to login in browser context
      if (typeof window !== 'undefined') {
        window.location.href = '/auth/login';
      }
      return createFailureResult('No refresh token available', HTTP_STATUS.UNAUTHORIZED);
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (!response.ok) {
        tokenStorage.clearTokens();
        if (typeof window !== 'undefined') {
          window.location.href = '/auth/login';
        }
        return createFailureResult('Session expired', HTTP_STATUS.UNAUTHORIZED);
      }

      const data = await response.json();
      tokenStorage.saveTokens(data.access_token, data.refresh_token);
      return createSuccessResult(data, HTTP_STATUS.OK);
    } catch (error) {
      tokenStorage.clearTokens();
      if (typeof window !== 'undefined') {
        window.location.href = '/auth/login';
      }
      return createFailureResult(
        error instanceof Error ? error.message : 'Token refresh failed',
        HTTP_STATUS.INTERNAL_SERVER_ERROR
      );
    }
  }

  /**
   * Create a failure result from an error response
   */
  private createErrorResult(status: number, responseBody: unknown): FailureResult {
    if (isValidationError(responseBody)) {
      const details: Record<string, string> = {};
      for (const error of responseBody.detail) {
        const key = error.loc.join('.');
        details[key] = error.msg;
      }
      return createFailureResult(
        'Validation error',
        status as HttpStatusCode,
        details
      );
    }

    if (
      typeof responseBody === 'object' &&
      responseBody !== null &&
      'detail' in responseBody
    ) {
      const detail = (responseBody as Record<string, unknown>).detail;
      return createFailureResult(
        typeof detail === 'string' ? detail : 'API request failed',
        status as HttpStatusCode
      );
    }

    return createFailureResult(
      typeof responseBody === 'string' ? responseBody : 'API request failed',
      status as HttpStatusCode
    );
  }

  /**
   * Convert error types to result
   */
  private errorToResult(error: ApiErrorType): FailureResult {
    if (isFailureResponse(error)) {
      return error;
    }

    if (isNetworkError(error)) {
      return createFailureResult(error.message, HTTP_STATUS.INTERNAL_SERVER_ERROR);
    }

    if (isTimeoutError(error)) {
      return createFailureResult(error.message, HTTP_STATUS.INTERNAL_SERVER_ERROR);
    }

    return createFailureResult(error.message, HTTP_STATUS.INTERNAL_SERVER_ERROR);
  }

  /**
   * GET request (returns ApiResult<T>)
   */
  get<T>(endpoint: string, options?: ApiRequestOptions): Promise<ApiResult<T>> {
    return this.request<T>(endpoint, { ...options, method: 'GET' });
  }

  /**
   * POST request (returns ApiResult<T>)
   */
  post<T>(endpoint: string, data?: Record<string, unknown>, options?: ApiRequestOptions): Promise<ApiResult<T>> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  /**
   * PUT request (returns ApiResult<T>)
   */
  put<T>(endpoint: string, data?: Record<string, unknown>, options?: ApiRequestOptions): Promise<ApiResult<T>> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  /**
   * DELETE request (returns ApiResult<null>)
   */
  delete<T = null>(endpoint: string, options?: ApiRequestOptions): Promise<ApiResult<T>> {
    return this.request<T>(endpoint, { ...options, method: 'DELETE' });
  }

  /**
   * PATCH request (returns ApiResult<T>)
   */
  patch<T>(endpoint: string, data?: Record<string, unknown>, options?: ApiRequestOptions): Promise<ApiResult<T>> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  // ============================================================================
  // Session Notes API Methods
  // ============================================================================

  /**
   * Create a new session note
   * @param sessionId - The therapy session ID
   * @param data - Note creation data (template_id, content)
   * @returns ApiResult<SessionNote>
   */
  createSessionNote<T>(
    sessionId: string,
    data: { template_id: string; content: Record<string, unknown> },
    options?: ApiRequestOptions
  ): Promise<ApiResult<T>> {
    return this.post<T>(`/api/v1/sessions/${sessionId}/notes`, data, options);
  }

  /**
   * Update an existing session note
   * @param noteId - The note ID to update
   * @param data - Partial update data (content, status)
   * @returns ApiResult<SessionNote>
   */
  updateSessionNote<T>(
    noteId: string,
    data: { content?: Record<string, unknown>; status?: string },
    options?: ApiRequestOptions
  ): Promise<ApiResult<T>> {
    return this.patch<T>(`/api/v1/notes/${noteId}`, data, options);
  }

  /**
   * Auto-fill template with AI-extracted data from session
   * @param sessionId - The therapy session ID
   * @param templateType - Template type (soap, dap, birp, etc.)
   * @returns ApiResult<AutofillResponse>
   */
  autofillTemplate<T>(
    sessionId: string,
    templateType: string,
    options?: ApiRequestOptions
  ): Promise<ApiResult<T>> {
    return this.post<T>(`/api/v1/sessions/${sessionId}/autofill`, { template_type: templateType }, options);
  }
}

export const apiClient = new ApiClient();
