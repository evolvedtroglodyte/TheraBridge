# Runtime Validation with Zod Schemas

This directory contains comprehensive runtime validation schemas for all API types used by the TherapyBridge frontend.

## Quick Start

Import and validate API responses:

```typescript
import { SessionSchema, safeParse } from '@/lib/schemas';

const response = await fetch('/api/sessions/123').then(r => r.json());
const session = safeParse(SessionSchema, response);

if (session) {
  console.log(session.id); // Fully type-safe
}
```

## Files in This Directory

### Core Schema File
- **`schemas.ts`** (9.7 KB)
  - 6 enum schemas for status and classification types
  - 7 format validators (UUID, email, date, URL, etc.)
  - 9 complex object schemas for domain models
  - 5 request/response schemas for API communication
  - 7 collection schemas for arrays of objects
  - 4 utility functions for validation
  - Full TypeScript type inference

### Documentation
- **`SCHEMAS_USAGE.md`** (9.9 KB)
  - Complete usage guide with 10+ examples
  - Best practices and patterns
  - Integration examples with hooks
  - Testing strategies
  - Real-world usage scenarios

- **`SCHEMAS_SUMMARY.md`** (5.8 KB)
  - Implementation overview
  - Feature inventory
  - Benefits and characteristics
  - Next steps for integration

- **`README_SCHEMAS.md`** (This file)
  - Quick navigation and overview
  - File descriptions
  - Key exports summary

### Tests & Examples
- **`schemas.test.ts`** (2.8 KB)
  - Reference test implementations
  - Validation examples for all major types
  - Can be run to verify schema correctness

## Key Exports Summary

### Enum Schemas
```typescript
SessionStatusSchema          // 'uploading' | 'transcribing' | ...
SessionMoodSchema            // 'very_low' | 'low' | ...
MoodTrajectorySchema         // 'improving' | 'declining' | ...
StrategyStatusSchema         // 'introduced' | 'practiced' | ...
StrategyCategorySchema       // 'breathing' | 'cognitive' | ...
TriggerSeveritySchema        // 'mild' | 'moderate' | 'severe'
```

### Format Validators
```typescript
UUIDSchema                   // RFC 4122 UUID format
EmailSchema                  // RFC 5322 email format
ISODateSchema                // ISO 8601 datetime strings
DateStringSchema             // Flexible date string parsing
NonEmptyStringSchema         // Non-empty strings
PositiveIntSchema            // Positive integers
```

### Domain Object Schemas
```typescript
SessionSchema                // Complete session record
PatientSchema                // Patient profile
StrategySchema               // Therapeutic strategy
TriggerSchema                // Emotional trigger
ActionItemSchema             // Session follow-up task
SignificantQuoteSchema       // Notable quote from session
RiskFlagSchema               // Safety concern
ExtractedNotesSchema         // AI-generated clinical notes
TranscriptSegmentSchema      // Speaker segment in transcript
```

### Request/Response Schemas
```typescript
SessionUploadRequestSchema   // Audio upload request
SessionCreateRequestSchema   // New session creation
PatientCreateRequestSchema   // New patient registration
ErrorResponseSchema          // API error response
PaginatedResponseSchema      // Generic paginated list
```

### Collection Schemas
```typescript
SessionsListSchema           // Array<Session>
PatientsListSchema           // Array<Patient>
StrategiesListSchema         // Array<Strategy>
TriggersListSchema           // Array<Trigger>
ActionItemsListSchema        // Array<ActionItem>
RiskFlagsListSchema          // Array<RiskFlag>
TranscriptSegmentsListSchema // Array<TranscriptSegment>
```

### Utility Functions
```typescript
safeParse<T>(schema, data)           // Returns T | null
validate<T>(schema, data)            // Returns T (throws on error)
getValidationErrors<T>(schema, data) // Returns error details
isValid<T>(schema, data)             // Type guard: data is T
```

## Validation Coverage

Each schema validates:
- ✓ Field presence (required vs optional)
- ✓ Field types (string, number, boolean, array, etc.)
- ✓ Enum values (exact match required)
- ✓ String formats (UUID, email, URL, ISO date)
- ✓ Number ranges (positive, non-negative, etc.)
- ✓ Nested object structures
- ✓ Array contents and length
- ✓ Nullable fields
- ✓ Optional fields with .optional()
- ✓ Custom validation rules

## Common Usage Patterns

### Pattern 1: API Response Validation
```typescript
const response = await fetch('/api/sessions');
const sessions = safeParse(SessionsListSchema, await response.json());
if (sessions) {
  sessions.forEach(s => console.log(s.id));
}
```

### Pattern 2: Form Input Validation
```typescript
const validated = safeParse(PatientCreateRequestSchema, formData);
if (validated) {
  await api.createPatient(validated);
} else {
  setError('Invalid form data');
}
```

### Pattern 3: Type Guard
```typescript
import { isValid, type Session } from '@/lib/schemas';

if (isValid(SessionSchema, data)) {
  // data is now typed as Session
  processSession(data);
}
```

### Pattern 4: Error Handling
```typescript
const errors = getValidationErrors(SessionSchema, data);
if (errors) {
  Object.entries(errors).forEach(([field, error]) => {
    console.error(`${field}: ${error._errors?.[0]}`);
  });
}
```

## Integration Checklist

- [ ] Review `SCHEMAS_USAGE.md` for detailed examples
- [ ] Update `api-client.ts` to validate all API responses
- [ ] Add validation to form submission handlers
- [ ] Create schema validation tests
- [ ] Update error handling for validation failures
- [ ] Add validation to API request/response interceptors
- [ ] Document any custom validators needed
- [ ] Test with sample API responses

## Bundle Impact

- Zod library: ~8 KB gzipped
- This schema file: ~3 KB gzipped
- Total impact: ~11 KB added to bundle
- No runtime cost for unused schemas (tree-shakeable)

## Performance Notes

- All validation is synchronous
- Validation time: O(1) to O(n) depending on schema
- Minimal overhead: typically <1ms per validation
- Suitable for frequent validation (on every API response)

## Keeping Schemas in Sync

1. Source of truth: `lib/types.ts`
2. When types change, update corresponding schema
3. Run `schemas.test.ts` to verify changes
4. Update `SCHEMAS_USAGE.md` if new patterns emerge

## Troubleshooting

### "Property X does not exist"
```typescript
// This means validation passed but TypeScript doesn't know the type
const data = safeParse(SessionSchema, response); // Returns Session | null
// Must check: if (data) { data.property }
```

### "Invalid enum value"
```typescript
// Enum value must match exactly
SessionMoodSchema.parse('very_low');  // OK
SessionMoodSchema.parse('veryLow');   // ERROR
```

### "Invalid UUID format"
```typescript
// UUID must be valid RFC 4122 format
UUIDSchema.parse('550e8400-e29b-41d4-a716-446655440000'); // OK
UUIDSchema.parse('123');                                  // ERROR
```

## Getting Help

1. Check `SCHEMAS_USAGE.md` for examples
2. Look at `schemas.test.ts` for reference implementations
3. Review Zod documentation: https://zod.dev
4. Check schema definition in `schemas.ts` for validation rules

## Type Inference

All TypeScript types are automatically derived from schemas:

```typescript
import { type Session, type Patient, type ExtractedNotes } from '@/lib/schemas';

// These types match the schema definitions exactly
const mySession: Session = { /* ... */ };
```

No need to manually maintain separate TypeScript interfaces!

## Next Steps

1. **Immediate**: Read `SCHEMAS_USAGE.md` for usage patterns
2. **Short-term**: Integrate validation into `api-client.ts`
3. **Medium-term**: Add schema validation to form components
4. **Long-term**: Expand validation for new API endpoints as they're added

---

Created: 2025-12-17
Last Updated: 2025-12-17
Zod Version: ^4.0.0
TypeScript Version: ^5
