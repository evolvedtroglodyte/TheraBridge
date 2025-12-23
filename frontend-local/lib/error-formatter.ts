/**
 * Error formatter utility for converting API errors to user-friendly messages
 * Provides contextual, actionable error messages based on error type and status code
 */

import type { FailureResult, ApiErrorType, ValidationErrorResponse } from './api-types';
import { isNetworkError, isTimeoutError, isUnknownError } from './api-types';

export interface FormattedError {
  message: string;
  description?: string;
  suggestion?: string;
  severity: 'error' | 'warning' | 'info';
  retryable: boolean;
  fieldErrors?: Record<string, string>;
}

/**
 * Format API error response to user-friendly message
 *
 * @example
 * ```ts
 * const result = await apiClient.get('/patients/123');
 * if (!result.success) {
 *   const error = formatApiError(result);
 *   console.log(error.message); // "Patient not found"
 *   console.log(error.suggestion); // "Check the patient ID and try again"
 * }
 * ```
 */
export function formatApiError(error: FailureResult | ApiErrorType): FormattedError {
  // Network errors
  if (isNetworkError(error)) {
    return {
      message: 'Network connection error',
      description: 'Unable to connect to the server',
      suggestion: 'Check your internet connection and try again',
      severity: 'error',
      retryable: true,
    };
  }

  // Timeout errors
  if (isTimeoutError(error)) {
    return {
      message: 'Request timeout',
      description: 'The request took too long to complete',
      suggestion: 'Check your connection and try again. If the problem persists, the server may be slow.',
      severity: 'warning',
      retryable: true,
    };
  }

  // Unknown errors
  if (isUnknownError(error)) {
    return {
      message: 'An unexpected error occurred',
      description: 'Something went wrong on our end',
      suggestion: 'Please try again. If the problem persists, contact support.',
      severity: 'error',
      retryable: true,
    };
  }

  // Failure result - status code based errors
  if ('status' in error) {
    return formatErrorByStatusCode(error.status, error.error, error.details);
  }

  // Fallback
  return {
    message: 'An error occurred',
    description: 'Something went wrong',
    severity: 'error',
    retryable: false,
  };
}

/**
 * Format error based on HTTP status code
 */
function formatErrorByStatusCode(
  status: number,
  message: string,
  details?: Record<string, unknown>
): FormattedError {
  switch (status) {
    // 400 Bad Request
    case 400:
      return {
        message: 'Invalid request',
        description: message || 'The request was malformed or invalid',
        suggestion: 'Check your input and try again',
        severity: 'error',
        retryable: false,
        fieldErrors: extractFieldErrors(details),
      };

    // 401 Unauthorized
    case 401:
      return {
        message: 'Session expired',
        description: 'Your session has expired',
        suggestion: 'Please log in again',
        severity: 'warning',
        retryable: false, // Will redirect to login
      };

    // 403 Forbidden
    case 403:
      return {
        message: 'Access denied',
        description: 'You do not have permission to access this resource',
        suggestion: 'Contact your administrator if you believe this is an error',
        severity: 'error',
        retryable: false,
      };

    // 404 Not Found
    case 404:
      return {
        message: 'Resource not found',
        description: message || 'The requested resource does not exist',
        suggestion: 'Verify the ID and try again, or refresh the page',
        severity: 'error',
        retryable: false,
      };

    // 409 Conflict
    case 409:
      return {
        message: 'Resource conflict',
        description: message || 'This resource cannot be modified due to a conflict',
        suggestion: 'Refresh the page and try again',
        severity: 'warning',
        retryable: true,
      };

    // 422 Unprocessable Entity (Validation Error)
    case 422:
      return {
        message: 'Validation failed',
        description: message || 'Please check your input and try again',
        suggestion: 'Fix the errors below and resubmit',
        severity: 'error',
        retryable: false,
        fieldErrors: extractFieldErrors(details),
      };

    // 429 Too Many Requests
    case 429:
      return {
        message: 'Too many requests',
        description: 'You are making requests too quickly',
        suggestion: 'Please wait a moment and try again',
        severity: 'warning',
        retryable: true,
      };

    // 500 Internal Server Error
    case 500:
      return {
        message: 'Server error',
        description: 'An error occurred on the server',
        suggestion: 'Try again in a few moments. If the problem persists, contact support.',
        severity: 'error',
        retryable: true,
      };

    // 503 Service Unavailable
    case 503:
      return {
        message: 'Service unavailable',
        description: 'The server is temporarily unavailable',
        suggestion: 'The service may be under maintenance. Try again soon.',
        severity: 'warning',
        retryable: true,
      };

    // Default for other 4xx errors
    case 400:
    case 401:
    case 403:
    case 404:
    case 405:
    case 408:
    case 410:
    case 414:
    case 429:
      if (status >= 400 && status < 500) {
        return {
          message: 'Request error',
          description: message || 'Your request could not be processed',
          suggestion: 'Check your input and try again',
          severity: 'error',
          retryable: false,
        };
      }
      break;

    // Default for 5xx errors
    case 502:
    case 504:
      if (status >= 500 && status < 600) {
        return {
          message: 'Server error',
          description: message || 'The server encountered an error',
          suggestion: 'Try again in a few moments',
          severity: 'error',
          retryable: true,
        };
      }
  }

  // Ultimate fallback
  return {
    message: message || 'An error occurred',
    description: `Error code: ${status}`,
    severity: 'error',
    retryable: status >= 500,
  };
}

/**
 * Extract field-specific errors from validation details
 */
function extractFieldErrors(details?: Record<string, unknown>): Record<string, string> | undefined {
  if (!details || typeof details !== 'object') {
    return undefined;
  }

  const fieldErrors: Record<string, string> = {};
  let hasErrors = false;

  for (const [key, value] of Object.entries(details)) {
    if (typeof value === 'string') {
      fieldErrors[key] = value;
      hasErrors = true;
    } else if (Array.isArray(value) && value.length > 0 && typeof value[0] === 'string') {
      fieldErrors[key] = value[0];
      hasErrors = true;
    }
  }

  return hasErrors ? fieldErrors : undefined;
}

/**
 * Format error for specific contexts (upload, auth, data fetching, etc.)
 */

export function formatUploadError(error: FailureResult | ApiErrorType): FormattedError {
  const baseError = formatApiError(error);

  if (isNetworkError(error)) {
    return {
      ...baseError,
      message: 'Upload failed due to network error',
      suggestion: 'Check your internet connection and try uploading again',
    };
  }

  if (isTimeoutError(error)) {
    return {
      ...baseError,
      message: 'Upload timed out',
      suggestion: 'The file may be too large or your connection is slow. Try with a smaller file.',
    };
  }

  if ('status' in error) {
    // Check for file too large (413) or unsupported media type (415)
    // Based on the error message instead since those status codes aren't in HTTP_STATUS
    if (error.error && error.error.toLowerCase().includes('too large')) {
      return {
        message: 'File too large',
        description: 'The file exceeds the maximum allowed size',
        suggestion: 'Try uploading a smaller file (max 100MB)',
        severity: 'error',
        retryable: false,
      };
    }

    if (error.error && error.error.toLowerCase().includes('type') && error.error.toLowerCase().includes('file')) {
      return {
        message: 'Invalid file type',
        description: 'This file type is not supported',
        suggestion: 'Upload an audio or video file (MP3, WAV, M4A, etc.)',
        severity: 'error',
        retryable: false,
      };
    }

    if (error.status >= 500) {
      return {
        ...baseError,
        message: 'Upload failed - server error',
        suggestion: 'Try again in a few moments. The server may be processing uploads.',
      };
    }
  }

  return {
    ...baseError,
    message: 'Upload failed',
    suggestion: 'Try uploading again',
  };
}

export function formatAuthError(error: FailureResult | ApiErrorType): FormattedError {
  const baseError = formatApiError(error);

  if ('status' in error) {
    if (error.status === 401) {
      return {
        message: 'Invalid credentials',
        description: 'Email or password is incorrect',
        suggestion: 'Check your email and password and try again',
        severity: 'error',
        retryable: false,
      };
    }

    if (error.status === 409) {
      return {
        message: 'Email already registered',
        description: 'An account with this email already exists',
        suggestion: 'Try logging in, or use a different email address',
        severity: 'error',
        retryable: false,
      };
    }
  }

  return {
    ...baseError,
    message: 'Authentication failed',
    suggestion: 'Please try again',
  };
}

export function formatDataFetchError(error: FailureResult | ApiErrorType): FormattedError {
  const baseError = formatApiError(error);

  if ('status' in error) {
    if (error.status === 404) {
      return {
        message: 'Data not found',
        description: 'The requested information could not be found',
        suggestion: 'Refresh the page or go back and try again',
        severity: 'error',
        retryable: true,
      };
    }
  }

  return {
    ...baseError,
    message: 'Failed to load data',
    suggestion: 'Try refreshing the page',
  };
}

/**
 * Format validation error response with field details
 */
export function formatValidationError(
  response: ValidationErrorResponse
): FormattedError {
  const fieldErrors: Record<string, string> = {};

  if (Array.isArray(response.detail)) {
    for (const error of response.detail) {
      const fieldPath = error.loc.join('.');
      fieldErrors[fieldPath] = error.msg;
    }
  }

  return {
    message: 'Please check your input',
    description: 'One or more fields have errors',
    severity: 'error',
    retryable: false,
    fieldErrors,
  };
}

/**
 * Create a user-friendly error message for display
 */
export function getUserFriendlyErrorMessage(error: FailureResult | ApiErrorType): string {
  const formatted = formatApiError(error);
  if (formatted.suggestion) {
    return `${formatted.message}. ${formatted.suggestion}`;
  }
  return formatted.message;
}
