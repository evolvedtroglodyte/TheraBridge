# Strict API Response Types Guide

This guide explains the comprehensive type system for API communication in the frontend, including discriminated unions for safe error handling and full response typing.

## Overview

The new API type system provides:

- **Discriminated Unions**: `ApiResult<T>` is either `SuccessResult<T>` or `FailureResult`
- **Type Guards**: Runtime-safe checking with functions like `isSuccessResponse()`
- **HTTP Status Constants**: Type-safe status code handling via `HTTP_STATUS`
- **Specific Endpoint Types**: Each endpoint has dedicated request/response types
- **Error Details**: Validation errors, network errors, timeouts all typed separately
- **Automatic Retry & Timeout**: Built-in resilience with configurable behavior

## Key Files

- **`lib/api-types.ts`** - All type definitions, type guards, and helper functions
- **`lib/api-client.ts`** - Updated API client using strict types
- **`lib/api-usage-examples.ts`** - 15+ examples demonstrating all patterns

## Core Concepts

### 1. ApiResult<T> - Discriminated Union

All API calls return `ApiResult<T>`, which is either:

```typescript
// Success case
type SuccessResult<T> = {
  success: true;
  status: HttpStatusCode;        // 200-299
  data: T;
};

// Failure case
type FailureResult = {
  success: false;
  status: HttpStatusCode;        // 4xx or 5xx
  error: string;
  details?: Record<string, unknown>;
};

type ApiResult<T> = SuccessResult<T> | FailureResult;
```

**Why discriminated unions?**
- TypeScript forces you to check `result.success` first
- After checking, the type narrows and only valid properties are available
- Impossible to access `.data` on a failed request at compile time

### 2. HTTP Status Constants

```typescript
const HTTP_STATUS = {
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

type HttpStatusCode = typeof HTTP_STATUS[keyof typeof HTTP_STATUS];
```

Use these instead of magic numbers for better type safety and IDE autocomplete.

### 3. Type Guards

All type guards return `value is SomeType` for compile-time narrowing:

```typescript
isSuccessResponse<T>(response): boolean
isFailureResponse(response): boolean
isValidationError(error): boolean
isNetworkError(error): boolean
isTimeoutError(error): boolean
isUnknownError(error): boolean
```

## Usage Patterns

### Pattern 1: Basic Discriminated Union (Recommended)

```typescript
const result = await apiClient.get<PatientResponse>('/api/patients/123');

if (result.success) {
  // ✅ result.data is available
  console.log(result.data.name);
} else {
  // ✅ result.error is available
  console.error(result.error);
  // ✅ Can check status for specific error handling
  if (result.status === HTTP_STATUS.NOT_FOUND) {
    // Handle 404
  }
}
```

**Benefits:**
- Impossible to forget error handling
- TypeScript prevents accessing `.data` on failure
- Clear, readable intent

### Pattern 2: Type Guards

```typescript
const result = await apiClient.get<PatientResponse>('/api/patients/123');

if (isSuccessResponse<PatientResponse>(result)) {
  // Type is narrowed to SuccessResult<PatientResponse>
  console.log(result.data.name);
}

if (isFailureResponse(result)) {
  // Type is narrowed to FailureResult
  console.error(result.error);
}
```

### Pattern 3: Error Callbacks

```typescript
const result = await apiClient.get<PatientResponse>('/api/patients/123', {
  onError: (error) => {
    if (isNetworkError(error)) {
      // Network connectivity issue
      showOfflineMessage();
    } else if (isTimeoutError(error)) {
      // Request took too long
      showTimeoutMessage();
    } else if (isFailureResponse(error)) {
      // API returned an error status
      logAnalytics(error.status, error.error);
    }
  },
});
```

### Pattern 4: Validation Error Handling

```typescript
const result = await apiClient.post<PatientResponse>('/api/patients/', data);

if (!result.success && result.status === HTTP_STATUS.UNPROCESSABLE_ENTITY) {
  // result.details contains field-level validation errors
  const fieldErrors = result.details as Record<string, string>;

  // Use in React form:
  setFormErrors(fieldErrors);

  // Or display inline:
  fieldErrors.forEach(([field, message]) => {
    console.error(`${field}: ${message}`);
  });
}
```

### Pattern 5: Retry Configuration

```typescript
const result = await apiClient.get<PatientResponse>('/api/patients/123', {
  timeout: 10000,                    // 10 second timeout
  retry: {
    maxAttempts: 3,                  // Try 3 times total
    delayMs: 1000,                   // Wait 1s before first retry
    backoffMultiplier: 2,            // Exponential: 1s, 2s, 4s
  },
});
```

**Retry behavior:**
- Initial request: immediate
- Retry 1 (if 5xx): wait 1s, then retry
- Retry 2 (if 5xx): wait 2s, then retry
- Won't retry on 4xx errors (client errors are not transient)

### Pattern 6: React Hook Integration

```typescript
const [patient, setPatient] = useState<PatientResponse | null>(null);
const [error, setError] = useState<string | null>(null);
const [isLoading, setIsLoading] = useState(false);

useEffect(() => {
  const fetchPatient = async () => {
    setIsLoading(true);
    const result = await apiClient.get<PatientResponse>('/api/patients/123');

    if (result.success) {
      setPatient(result.data);
      setError(null);
    } else {
      setPatient(null);
      setError(result.error);
    }

    setIsLoading(false);
  };

  fetchPatient();
}, []);

return isLoading ? <Spinner /> : error ? <Error message={error} /> : <Patient data={patient!} />;
```

### Pattern 7: Reusable API Functions

```typescript
export async function getPatient(id: string): Promise<ApiResult<PatientResponse>> {
  return apiClient.get<PatientResponse>(`/api/patients/${id}`);
}

export async function createPatient(data: CreatePatientRequest): Promise<ApiResult<PatientResponse>> {
  return apiClient.post<PatientResponse>('/api/patients/', data);
}

// Usage:
const result = await getPatient('123');
if (result.success) {
  console.log(result.data.name);
}
```

## API Client Methods

All methods return `Promise<ApiResult<T>>`:

```typescript
// GET - fetch resource
await apiClient.get<T>(endpoint, options?)

// POST - create resource
await apiClient.post<T>(endpoint, data?, options?)

// PUT - full update
await apiClient.put<T>(endpoint, data?, options?)

// PATCH - partial update
await apiClient.patch<T>(endpoint, data?, options?)

// DELETE - remove resource (returns null)
await apiClient.delete<T>(endpoint, options?)
```

## Request Options

```typescript
interface ApiRequestOptions extends RequestInit {
  timeout?: number;                    // Default: 30000ms
  retry?: {
    maxAttempts: number;               // Default: 1 (no retry)
    delayMs: number;                   // Default: 1000
    backoffMultiplier?: number;        // Default: 1 (no backoff)
  };
  onError?: (error: ApiErrorType) => void;  // Error callback
}
```

## Response Types by Endpoint

### Patients API

```typescript
// Get single patient
type GetPatientResponse = GetPatientSuccessResponse | GetPatientFailureResponse;
interface GetPatientSuccessResponse extends ApiResponse<PatientResponse> {}
interface GetPatientFailureResponse extends FailureResult {}

// List all patients
type ListPatientsResponse = ListPatientsSuccessResponse | ListPatientsFailureResponse;
interface ListPatientsSuccessResponse extends ApiResponse<PatientResponse[]> {}

// Create patient
type CreatePatientResponse = CreatePatientSuccessResponse | CreatePatientFailureResponse;

// Update patient
type UpdatePatientResponse = UpdatePatientSuccessResponse | UpdatePatientFailureResponse;

// Delete patient
type DeletePatientResponse = DeletePatientSuccessResponse | DeletePatientFailureResponse;
```

### Sessions API

```typescript
// Get single session
type GetSessionResponse = GetSessionSuccessResponse | GetSessionFailureResponse;

// List sessions
type ListSessionsResponse = ListSessionsSuccessResponse | ListSessionsFailureResponse;

// Upload session
type UploadSessionResponse = UploadSessionSuccessResponse | UploadSessionFailureResponse;

// Delete session
type DeleteSessionResponse = DeleteSessionSuccessResponse | DeleteSessionFailureResponse;
```

### Authentication API

```typescript
type LoginResponse = LoginSuccessResponse | LoginFailureResponse;
type RefreshResponse = RefreshSuccessResponse | RefreshFailureResponse;
```

## Error Handling

### Network Errors

```typescript
interface NetworkError {
  type: 'network';
  message: string;
  originalError?: Error;
}

// Check for network errors:
if (isNetworkError(error)) {
  // No internet, server unreachable, etc.
}
```

### Timeout Errors

```typescript
interface TimeoutError {
  type: 'timeout';
  message: string;
  timeoutMs: number;
}

// Check for timeout errors:
if (isTimeoutError(error)) {
  // Request took longer than timeout
}
```

### Validation Errors (422)

```typescript
interface ValidationErrorResponse {
  detail: ValidationErrorDetail[];
}

interface ValidationErrorDetail {
  loc: (string | number)[];        // e.g., ['body', 'email']
  msg: string;                      // e.g., 'invalid email format'
  type: string;                     // e.g., 'value_error'
}

// Check for validation errors:
if (!result.success && result.status === HTTP_STATUS.UNPROCESSABLE_ENTITY) {
  // result.details contains field-level errors
}
```

## Comparison: Old vs New Pattern

### Old Pattern (Unsafe)

```typescript
try {
  const patient = await fetchApi<Patient>(`/api/patients/${id}`);
  console.log(patient.name);  // Might crash if error
} catch (error) {
  // Caught error might be network, timeout, parse error, or API error
  console.error(error.message);  // What is this error type?
}
```

**Problems:**
- Can't tell what kind of error occurred
- No type information in catch block
- Might crash if API returns error-shaped object without throwing

### New Pattern (Type Safe)

```typescript
const result = await apiClient.get<PatientResponse>(`/api/patients/${id}`);

if (result.success) {
  console.log(result.data.name);  // ✅ Guaranteed safe
} else {
  // ✅ TypeScript knows this is a FailureResult
  console.error(result.error);

  if (result.status === HTTP_STATUS.NOT_FOUND) {
    // ✅ Type-safe status checking
  }
}
```

**Benefits:**
- Clear success/failure distinction
- Type narrowing prevents mistakes
- Easy to handle specific error types
- No exceptions to catch

## Creating Your Own Endpoints

When adding a new API endpoint:

1. **Define request/response types in `api-types.ts`:**

```typescript
export interface MyResourceResponse {
  readonly id: string;
  readonly name: string;
  // ... other fields
}

export interface GetMyResourceSuccessResponse extends ApiResponse<MyResourceResponse> {}
export interface GetMyResourceFailureResponse extends FailureResult {}
export type GetMyResourceResponse = GetMyResourceSuccessResponse | GetMyResourceFailureResponse;
```

2. **Use in your code:**

```typescript
const result = await apiClient.get<MyResourceResponse>('/api/my-resource/123');

if (result.success) {
  console.log(result.data.name);
} else {
  console.error(result.error);
}
```

## Type-Checking Strategy

The type system ensures:

1. **No unhandled errors** - Must check `result.success`
2. **Type-safe property access** - Can't access `.data` on failure
3. **Specific status checking** - Use `HTTP_STATUS` constants
4. **Field-level errors** - Validation errors are parsed into `details`
5. **Runtime safety** - Type guards support runtime checks

## Migration from Old API

If you have existing code using the old API client:

### Old
```typescript
const patient = await apiClient.get<Patient>('/api/patients/123');
```

### New
```typescript
const result = await apiClient.get<PatientResponse>('/api/patients/123');

if (result.success) {
  const patient = result.data;
  // ... use patient
}
```

The main change is adding the `result.success` check, which TypeScript will enforce.

## Best Practices

1. **Always check `result.success`** - Let TypeScript guide you
2. **Use HTTP_STATUS constants** - Never use magic numbers
3. **Handle validation errors specifically** - Show field-level errors to users
4. **Use retry for network operations** - Better UX for slow connections
5. **Set appropriate timeouts** - Prevent hanging requests
6. **Log errors with context** - Include status code and message
7. **Create wrapper functions** - Keep endpoint URLs in one place
8. **Type your data** - Use `PatientResponse`, `SessionResponse`, etc.

## Examples

See `lib/api-usage-examples.ts` for 15 complete, runnable examples:

- Basic result pattern
- Type guard pattern
- Switch pattern
- Error callback pattern
- Retry logic pattern
- POST/CREATE pattern
- PUT/UPDATE pattern
- DELETE pattern
- PATCH pattern
- Typed list pattern
- Validation error handling
- Custom error type checking
- React hook integration
- Typed wrapper functions
- Parallel requests with Promise.all
