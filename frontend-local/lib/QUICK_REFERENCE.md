# API Types - Quick Reference

## Most Common Pattern

```typescript
const result = await apiClient.get<PatientResponse>('/api/patients/123');

if (result.success) {
  console.log(result.data.name);     // Access data
} else {
  console.error(result.error);       // Access error message
  console.log(result.status);        // Access HTTP status
}
```

## HTTP Status Constants

```typescript
HTTP_STATUS.OK                      // 200
HTTP_STATUS.CREATED                 // 201
HTTP_STATUS.BAD_REQUEST             // 400
HTTP_STATUS.UNAUTHORIZED            // 401
HTTP_STATUS.FORBIDDEN               // 403
HTTP_STATUS.NOT_FOUND               // 404
HTTP_STATUS.CONFLICT                // 409
HTTP_STATUS.UNPROCESSABLE_ENTITY    // 422
HTTP_STATUS.INTERNAL_SERVER_ERROR   // 500
```

## API Client Methods

```typescript
await apiClient.get<T>(endpoint, options?)
await apiClient.post<T>(endpoint, data?, options?)
await apiClient.put<T>(endpoint, data?, options?)
await apiClient.patch<T>(endpoint, data?, options?)
await apiClient.delete<T>(endpoint, options?)
```

## Request Options

```typescript
{
  timeout: 30000,                    // 30 seconds
  retry: {
    maxAttempts: 3,
    delayMs: 1000,
    backoffMultiplier: 2,            // Optional
  },
  onError: (error) => {              // Optional callback
    // Handle error
  },
}
```

## Type Guards (for narrowing types)

```typescript
isSuccessResponse(result)
isFailureResponse(result)
isNetworkError(error)
isTimeoutError(error)
isValidationError(error)
```

## Common Patterns

### Handle Validation Errors
```typescript
const result = await apiClient.post<PatientResponse>('/api/patients/', data);

if (isFailureResponse(result) && result.status === HTTP_STATUS.UNPROCESSABLE_ENTITY) {
  const fieldErrors = result.details as Record<string, string>;
  setFormErrors(fieldErrors);
}
```

### Handle 404
```typescript
const result = await apiClient.get<PatientResponse>('/api/patients/123');

if (isFailureResponse(result) && result.status === HTTP_STATUS.NOT_FOUND) {
  console.log('Patient not found');
} else if (result.success) {
  console.log(result.data);
}
```

### With Retry
```typescript
const result = await apiClient.get<PatientResponse>('/api/patients/123', {
  retry: {
    maxAttempts: 3,
    delayMs: 1000,
    backoffMultiplier: 2,
  },
});
```

### In React Component
```typescript
const [patient, setPatient] = useState<PatientResponse | null>(null);
const [error, setError] = useState<string | null>(null);

useEffect(() => {
  const fetch = async () => {
    const result = await apiClient.get<PatientResponse>(`/api/patients/${id}`);
    if (result.success) {
      setPatient(result.data);
    } else {
      setError(result.error);
    }
  };
  fetch();
}, [id]);
```

## Type Definitions

```typescript
type ApiResult<T> = SuccessResult<T> | FailureResult

interface SuccessResult<T> {
  success: true
  status: HttpStatusCode        // 200-299
  data: T
}

interface FailureResult {
  success: false
  status: HttpStatusCode        // 4xx or 5xx
  error: string
  details?: Record<string, unknown>
}
```

## Response Types Available

```typescript
PatientResponse
SessionResponse
AuthTokenResponse
RefreshTokenResponse
```

## Files

- **Type Definitions**: `/lib/api-types.ts`
- **Client Implementation**: `/lib/api-client.ts`
- **Working Examples**: `/lib/api-usage-examples.ts`
- **Full Guide**: `/lib/API_TYPES_GUIDE.md`
- **Summary**: `/STRICT_API_TYPES_SUMMARY.md`

## Key Benefits

✓ Type-safe error handling
✓ No runtime crashes from untyped responses
✓ Exhaustive case handling (TypeScript enforces)
✓ Field-level validation errors
✓ Automatic retry with exponential backoff
✓ Timeout protection
✓ Transparent token refresh
✓ Works with React hooks
✓ IDE autocomplete on all responses
✓ Clear success/failure distinction

## Pro Tips

1. Always use `HTTP_STATUS` constants instead of magic numbers
2. Use type guards when you need explicit type narrowing
3. Configure retry and timeout for slow/unreliable networks
4. Use `onError` callback for centralized error logging
5. Create wrapper functions to keep endpoint URLs in one place
6. Display validation errors (result.details) to users in forms
7. Use `isFailureResponse()` when accessing .error or .details
