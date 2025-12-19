/**
 * Environment Variable Validation for TherapyBridge Frontend
 *
 * Validates required environment variables on app startup and provides
 * helpful warnings for configuration issues.
 *
 * @module env-validation
 */

/**
 * Validation result for a single environment variable
 */
interface ValidationResult {
  key: string;
  value: string | undefined;
  isValid: boolean;
  error?: string;
  warning?: string;
}

/**
 * Health check result
 */
interface HealthCheckResult {
  isHealthy: boolean;
  url: string;
  error?: string;
  responseTime?: number;
}

/**
 * Overall environment validation result
 */
export interface EnvValidationResult {
  isValid: boolean;
  results: ValidationResult[];
  healthCheck?: HealthCheckResult;
  errors: string[];
  warnings: string[];
}

/**
 * Validates NEXT_PUBLIC_API_URL format
 */
function validateApiUrl(url: string | undefined): ValidationResult {
  const key = 'NEXT_PUBLIC_API_URL';

  if (!url) {
    return {
      key,
      value: url,
      isValid: false,
      error: 'NEXT_PUBLIC_API_URL is not defined. Set it in .env.local (e.g., http://localhost:8000)',
    };
  }

  // Check for trailing slash
  if (url.endsWith('/')) {
    return {
      key,
      value: url,
      isValid: false,
      error: 'NEXT_PUBLIC_API_URL must not have a trailing slash. Remove the trailing "/" from your .env.local',
    };
  }

  // Check for /api/v1 suffix (API client adds this automatically)
  if (url.endsWith('/api/v1') || url.includes('/api/v1/')) {
    return {
      key,
      value: url,
      isValid: false,
      warning: 'NEXT_PUBLIC_API_URL should not include "/api/v1". The API client adds this automatically. Consider using just the base URL (e.g., http://localhost:8000)',
    };
  }

  // Check for valid URL format
  try {
    const parsedUrl = new URL(url);

    // Warn if using HTTP in production (non-localhost)
    if (parsedUrl.protocol === 'http:' && !parsedUrl.hostname.includes('localhost') && !parsedUrl.hostname.includes('127.0.0.1')) {
      return {
        key,
        value: url,
        isValid: true,
        warning: 'NEXT_PUBLIC_API_URL uses HTTP instead of HTTPS for a non-localhost URL. Consider using HTTPS in production.',
      };
    }

    return {
      key,
      value: url,
      isValid: true,
    };
  } catch (error) {
    return {
      key,
      value: url,
      isValid: false,
      error: `NEXT_PUBLIC_API_URL is not a valid URL: ${url}. Example: http://localhost:8000`,
    };
  }
}

/**
 * Validates NEXT_PUBLIC_USE_REAL_API flag
 */
function validateUseRealApi(value: string | undefined): ValidationResult {
  const key = 'NEXT_PUBLIC_USE_REAL_API';

  if (!value) {
    return {
      key,
      value,
      isValid: true,
      warning: 'NEXT_PUBLIC_USE_REAL_API not set. Defaulting to mock API mode. Set to "true" to use real backend.',
    };
  }

  const normalized = value.toLowerCase();
  if (normalized !== 'true' && normalized !== 'false') {
    return {
      key,
      value,
      isValid: true,
      warning: `NEXT_PUBLIC_USE_REAL_API should be "true" or "false", got "${value}". Will be evaluated as boolean.`,
    };
  }

  return {
    key,
    value,
    isValid: true,
  };
}

/**
 * Performs health check on the backend API
 *
 * @param baseUrl - The API base URL to check
 * @param timeoutMs - Request timeout in milliseconds (default: 5000)
 * @returns Health check result
 */
async function performHealthCheck(baseUrl: string, timeoutMs = 5000): Promise<HealthCheckResult> {
  const healthUrl = `${baseUrl}/health`;
  const startTime = Date.now();

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    const response = await fetch(healthUrl, {
      method: 'GET',
      signal: controller.signal,
      // Don't send credentials for health check
      credentials: 'omit',
    });

    clearTimeout(timeoutId);
    const responseTime = Date.now() - startTime;

    if (response.ok) {
      return {
        isHealthy: true,
        url: healthUrl,
        responseTime,
      };
    }

    return {
      isHealthy: false,
      url: healthUrl,
      responseTime,
      error: `Backend returned status ${response.status}. Check if the backend is running and accessible.`,
    };
  } catch (error) {
    const responseTime = Date.now() - startTime;

    if (error instanceof DOMException && error.name === 'AbortError') {
      return {
        isHealthy: false,
        url: healthUrl,
        responseTime,
        error: `Backend health check timed out after ${timeoutMs}ms. The backend may be slow or unreachable.`,
      };
    }

    return {
      isHealthy: false,
      url: healthUrl,
      responseTime,
      error: `Cannot reach backend at ${baseUrl}. Ensure the backend is running and CORS is configured. Error: ${error instanceof Error ? error.message : 'Unknown error'}`,
    };
  }
}

/**
 * Validates all required environment variables
 *
 * @param options - Validation options
 * @param options.performHealthCheck - Whether to perform backend health check (default: false)
 * @param options.healthCheckTimeout - Health check timeout in ms (default: 5000)
 * @returns Validation result with all errors and warnings
 */
export async function validateEnvironment(options: {
  performHealthCheck?: boolean;
  healthCheckTimeout?: number;
} = {}): Promise<EnvValidationResult> {
  const results: ValidationResult[] = [];
  const errors: string[] = [];
  const warnings: string[] = [];

  // Validate NEXT_PUBLIC_API_URL
  const apiUrlResult = validateApiUrl(process.env.NEXT_PUBLIC_API_URL);
  results.push(apiUrlResult);
  if (!apiUrlResult.isValid && apiUrlResult.error) {
    errors.push(apiUrlResult.error);
  }
  if (apiUrlResult.warning) {
    warnings.push(apiUrlResult.warning);
  }

  // Validate NEXT_PUBLIC_USE_REAL_API
  const useRealApiResult = validateUseRealApi(process.env.NEXT_PUBLIC_USE_REAL_API);
  results.push(useRealApiResult);
  if (!useRealApiResult.isValid && useRealApiResult.error) {
    errors.push(useRealApiResult.error);
  }
  if (useRealApiResult.warning) {
    warnings.push(useRealApiResult.warning);
  }

  let healthCheck: HealthCheckResult | undefined;

  // Perform health check if requested and API URL is valid
  if (options.performHealthCheck && apiUrlResult.isValid && apiUrlResult.value) {
    const useRealApi = process.env.NEXT_PUBLIC_USE_REAL_API?.toLowerCase() === 'true';

    if (useRealApi) {
      healthCheck = await performHealthCheck(
        apiUrlResult.value,
        options.healthCheckTimeout || 5000
      );

      if (!healthCheck.isHealthy && healthCheck.error) {
        warnings.push(healthCheck.error);
      }
    }
  }

  return {
    isValid: errors.length === 0,
    results,
    healthCheck,
    errors,
    warnings,
  };
}

/**
 * Logs validation results to console with appropriate styling
 *
 * @param result - The validation result to log
 */
export function logValidationResults(result: EnvValidationResult): void {
  console.group('🔍 TherapyBridge Environment Validation');

  // Log errors
  if (result.errors.length > 0) {
    console.group('❌ Errors:');
    result.errors.forEach(error => console.error(`  • ${error}`));
    console.groupEnd();
  }

  // Log warnings
  if (result.warnings.length > 0) {
    console.group('⚠️  Warnings:');
    result.warnings.forEach(warning => console.warn(`  • ${warning}`));
    console.groupEnd();
  }

  // Log health check
  if (result.healthCheck) {
    const { isHealthy, url, responseTime, error } = result.healthCheck;

    if (isHealthy) {
      console.log(`✅ Backend health check passed (${url}) - ${responseTime}ms`);
    } else {
      console.warn(`⚠️  Backend health check failed (${url}) - ${error}`);
    }
  }

  // Log individual results
  console.group('📋 Configuration:');
  result.results.forEach(({ key, value, isValid }) => {
    const icon = isValid ? '✓' : '✗';
    const displayValue = value || '(not set)';
    console.log(`  ${icon} ${key}: ${displayValue}`);
  });
  console.groupEnd();

  // Final status
  if (result.isValid) {
    console.log('✅ All required environment variables are valid');
  } else {
    console.error('❌ Environment validation failed. Fix the errors above.');
  }

  console.groupEnd();
}

/**
 * Validates environment and logs results to console.
 * Recommended to call this on app startup.
 *
 * @param options - Validation options
 * @returns Validation result
 *
 * @example
 * ```ts
 * // In app/layout.tsx or a startup hook
 * if (typeof window !== 'undefined') {
 *   validateAndLog({ performHealthCheck: true });
 * }
 * ```
 */
export async function validateAndLog(options: {
  performHealthCheck?: boolean;
  healthCheckTimeout?: number;
} = {}): Promise<EnvValidationResult> {
  const result = await validateEnvironment(options);
  logValidationResults(result);
  return result;
}

/**
 * Gets the validated API base URL or throws an error
 *
 * @returns The validated API base URL
 * @throws Error if API URL is invalid
 */
export function getValidatedApiUrl(): string {
  const url = process.env.NEXT_PUBLIC_API_URL;

  if (!url) {
    throw new Error('NEXT_PUBLIC_API_URL is not defined. Check your .env.local file.');
  }

  if (url.endsWith('/')) {
    throw new Error('NEXT_PUBLIC_API_URL must not have a trailing slash. Remove the trailing "/" from .env.local');
  }

  try {
    new URL(url);
  } catch {
    throw new Error(`NEXT_PUBLIC_API_URL is not a valid URL: ${url}`);
  }

  return url;
}
