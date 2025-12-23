# Zod Schemas Usage Guide

This document explains how to use the runtime validation schemas defined in `lib/schemas.ts`.

## Overview

The `schemas.ts` file provides Zod-based runtime validation schemas for all API types returned by the TherapyBridge backend. This ensures type safety not just at compile time, but also at runtime when receiving data from API responses.

## What is Zod?

Zod is a TypeScript-first schema validation library that provides:
- Runtime type checking for JavaScript objects
- Type inference (derive TypeScript types from schemas)
- Clear error messages when validation fails
- Small bundle size

## Core Schemas Available

### Enum Schemas
- `SessionStatusSchema` - Validates session processing status
- `SessionMoodSchema` - Validates session mood ratings
- `MoodTrajectorySchema` - Validates mood trend direction
- `StrategyStatusSchema` - Validates therapeutic strategy status
- `StrategyCategorySchema` - Validates strategy types (breathing, cognitive, etc.)
- `TriggerSeveritySchema` - Validates trigger severity levels

### Format Validators
- `UUIDSchema` - Validates UUID format (v4)
- `EmailSchema` - Validates email addresses
- `ISODateSchema` - Validates ISO 8601 datetime strings
- `DateStringSchema` - Flexible date string validation
- `NonEmptyStringSchema` - Ensures strings aren't empty
- `PositiveIntSchema` - Validates positive integers

### Complex Object Schemas
- `SessionSchema` - Complete session record with all fields
- `PatientSchema` - Patient profile information
- `StrategySchema` - Therapeutic strategy
- `TriggerSchema` - Identified emotional trigger
- `ActionItemSchema` - Task or follow-up item
- `SignificantQuoteSchema` - Notable patient statement
- `RiskFlagSchema` - Safety concern indicator
- `ExtractedNotesSchema` - AI-generated clinical notes
- `TranscriptSegmentSchema` - Individual speaker segment

### Request/Response Schemas
- `SessionUploadRequestSchema` - Audio upload request
- `SessionCreateRequestSchema` - Session creation request
- `PatientCreateRequestSchema` - Patient creation request
- `ErrorResponseSchema` - API error response format
- `PaginatedResponseSchema` - Generic paginated response

### Collection Schemas
- `SessionsListSchema` - Array of sessions
- `PatientsListSchema` - Array of patients
- `StrategiesListSchema` - Array of strategies
- `TriggersListSchema` - Array of triggers
- `ActionItemsListSchema` - Array of action items
- `RiskFlagsListSchema` - Array of risk flags
- `TranscriptSegmentsListSchema` - Array of transcript segments

## Usage Patterns

### 1. Safe Parsing (Recommended)

Returns the parsed data or `null` if validation fails:

```typescript
import { SessionSchema, safeParse } from '@/lib/schemas';

const apiResponse = await fetch('/api/sessions/123').then(r => r.json());
const session = safeParse(SessionSchema, apiResponse);

if (session) {
  console.log(session.id); // TypeScript knows this is string
  // Use the validated data
} else {
  console.error('Invalid session data from API');
}
```

### 2. Type Checking Without Parsing

Check if data matches schema without parsing:

```typescript
import { SessionSchema, isValid } from '@/lib/schemas';

if (isValid(SessionSchema, apiResponse)) {
  // apiResponse is now typed as Session
  console.log(apiResponse.id);
}
```

### 3. Validation with Error Details

Get formatted error information:

```typescript
import { SessionSchema, getValidationErrors } from '@/lib/schemas';

const errors = getValidationErrors(SessionSchema, apiResponse);
if (errors) {
  console.error('Validation errors:', errors);
  // errors contains field-level error details
}
```

### 4. Throwing on Invalid Data

Throws an error if validation fails:

```typescript
import { SessionSchema, validate } from '@/lib/schemas';

try {
  const session = validate(SessionSchema, apiResponse);
  // Use the validated session
} catch (error) {
  console.error('Invalid session data:', error);
}
```

## Real-World Examples

### Validating API Response in a Hook

```typescript
import { useEffect, useState } from 'react';
import { SessionSchema, safeParse, type Session } from '@/lib/schemas';

export function useSession(sessionId: string) {
  const [session, setSession] = useState<Session | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`/api/sessions/${sessionId}`)
      .then(r => r.json())
      .then(data => {
        const validated = safeParse(SessionSchema, data);
        if (validated) {
          setSession(validated);
        } else {
          setError('Received invalid session data from server');
        }
      })
      .catch(err => setError(err.message));
  }, [sessionId]);

  return { session, error };
}
```

### Validating Form Input Before Submission

```typescript
import { PatientCreateRequestSchema, safeParse } from '@/lib/schemas';

function handleSubmit(formData: FormData) {
  const data = {
    name: formData.get('name'),
    email: formData.get('email'),
    therapist_id: formData.get('therapist_id'),
  };

  const validated = safeParse(PatientCreateRequestSchema, data);
  if (validated) {
    // Send to API
    submitPatient(validated);
  } else {
    // Show error to user
    showError('Please check all fields');
  }
}
```

### Validating Array of Items

```typescript
import { PatientsListSchema, safeParse } from '@/lib/schemas';

const patientsList = await fetch('/api/patients').then(r => r.json());
const patients = safeParse(PatientsListSchema, patientsList);

if (patients) {
  patients.forEach(patient => {
    console.log(patient.name, patient.email);
  });
}
```

### Creating Paginated Response Wrapper

```typescript
import { SessionSchema, PaginatedResponseSchema } from '@/lib/schemas';

const PaginatedSessionsSchema = PaginatedResponseSchema(SessionSchema);

const response = await fetch('/api/sessions?page=1').then(r => r.json());
const validated = safeParse(PaginatedSessionsSchema, response);

if (validated) {
  console.log(`Showing ${validated.items.length} of ${validated.total} sessions`);
  validated.items.forEach(session => {
    // Process each session
  });
}
```

## Type Inference

You can extract TypeScript types directly from schemas:

```typescript
import { type Session, type Patient, type ExtractedNotes } from '@/lib/schemas';

// These types are automatically inferred from the schemas
const mySession: Session = { /* ... */ };
const myPatient: Patient = { /* ... */ };
const myNotes: ExtractedNotes = { /* ... */ };
```

## API Error Handling

Validate error responses from the API:

```typescript
import { ErrorResponseSchema, safeParse } from '@/lib/schemas';

try {
  await fetch('/api/sessions', { method: 'POST', body: JSON.stringify(data) });
} catch (error) {
  const errorData = await error.response.json();
  const validatedError = safeParse(ErrorResponseSchema, errorData);

  if (validatedError) {
    console.error('API returned error:', validatedError.detail);
  }
}
```

## Best Practices

1. **Always validate API responses** - Never trust data from the network
2. **Use type inference** - Let Zod infer types rather than manually maintaining duplicates
3. **Handle validation failures gracefully** - Show user-friendly error messages
4. **Use safeParse for user-facing code** - Prevents crashes from unexpected data
5. **Use validate in trusted contexts** - Tests, internal API calls where you control both sides
6. **Log validation errors** - Help debug server-client mismatches

## Testing with Schemas

```typescript
import { SessionSchema } from '@/lib/schemas';

describe('Session validation', () => {
  it('accepts valid session data', () => {
    const valid = {
      id: '550e8400-e29b-41d4-a716-446655440000',
      patient_id: '550e8400-e29b-41d4-a716-446655440001',
      therapist_id: '550e8400-e29b-41d4-a716-446655440002',
      session_date: '2025-12-17T10:30:00Z',
      duration_seconds: 3600,
      status: 'processed',
      created_at: '2025-12-17T10:00:00Z',
      updated_at: '2025-12-17T10:00:00Z',
    };

    expect(SessionSchema.safeParse(valid).success).toBe(true);
  });

  it('rejects invalid session data', () => {
    const invalid = {
      id: 'not-a-uuid',
      status: 'invalid-status',
    };

    expect(SessionSchema.safeParse(invalid).success).toBe(false);
  });
});
```

## Custom Validators

You can create custom validators for specific use cases:

```typescript
import { z } from 'zod';

// Phone number validation
const PhoneSchema = z.string().regex(/^\+?[1-9]\d{1,14}$/, 'Invalid phone number');

// URL slug validation
const SlugSchema = z.string().regex(/^[a-z0-9]+(?:-[a-z0-9]+)*$/, 'Invalid slug format');

// Combined with existing schemas
const PatientWithPhoneSchema = PatientSchema.extend({
  phone: PhoneSchema,
});
```

## Performance Considerations

- Zod schemas are lightweight and suitable for runtime validation
- Validation is synchronous and very fast
- For large arrays, validation time is linear with array size
- Cache parsed data to avoid re-validating same data multiple times

## Debugging Validation Errors

```typescript
import { getValidationErrors } from '@/lib/schemas';

const errors = getValidationErrors(SessionSchema, apiResponse);
if (errors) {
  console.log(JSON.stringify(errors, null, 2));
  // Shows detailed error structure:
  // {
  //   id: { _errors: ['Invalid UUID format'] },
  //   status: { _errors: ['Invalid enum value'] }
  // }
}
```

## Migration from Unvalidated Code

If you have existing code that doesn't use validation:

```typescript
// Before: No validation
const sessions = await fetch('/api/sessions').then(r => r.json());
sessions.forEach(s => console.log(s.id)); // May crash if s.id is undefined

// After: With validation
import { SessionsListSchema, safeParse } from '@/lib/schemas';

const response = await fetch('/api/sessions').then(r => r.json());
const sessions = safeParse(SessionsListSchema, response);
if (sessions) {
  sessions.forEach(s => console.log(s.id)); // TypeScript knows s.id exists
} else {
  console.error('Failed to parse sessions from API');
}
```
