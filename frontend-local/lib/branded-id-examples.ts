/**
 * Examples and usage patterns for Branded ID Types
 *
 * This file demonstrates best practices for using PatientId, SessionId, and UserId
 * to prevent ID-related type errors at compile time.
 *
 * Branded types create a distinction at the type level between different kinds of IDs
 * even though they're all strings at runtime. This catches mistakes like:
 * - Passing a PatientId where SessionId is expected
 * - Using the wrong ID type in API calls
 * - Mixing up IDs in data structures
 */

import {
  createPatientId,
  createSessionId,
  createUserId,
  isPatientId,
  isSessionId,
  isUserId,
  unwrapId,
  type PatientId,
  type SessionId,
  type UserId,
} from './types';

// ============================================================================
// BASIC CREATION AND TYPE GUARDS
// ============================================================================

/**
 * Creating branded IDs from backend responses
 */
export function exampleCreatingIds() {
  // Creating IDs from backend data
  const patientId = createPatientId('patient-123');
  const sessionId = createSessionId('session-456');
  const userId = createUserId('user-789');

  // Type checker now knows these are different types!
  // This would fail at compile time:
  // const wrong: PatientId = sessionId; // ❌ ERROR: Type 'SessionId' is not assignable to type 'PatientId'

  return { patientId, sessionId, userId };
}

/**
 * Runtime validation with type guards
 */
export function exampleValidatingIds(rawData: any) {
  // When you have untrusted data, use type guards
  if (isPatientId(rawData.patient_id)) {
    // Inside this block, TypeScript knows it's a PatientId
    const patientId: PatientId = rawData.patient_id;
    console.log('Valid patient ID:', patientId);
  } else {
    console.error('Invalid patient ID');
  }

  if (isSessionId(rawData.session_id)) {
    const sessionId: SessionId = rawData.session_id;
    console.log('Valid session ID:', sessionId);
  }
}

/**
 * Unwrapping IDs when you need the raw string
 */
export function exampleUnwrappingIds(
  patientId: PatientId,
  sessionId: SessionId
) {
  // When you need to pass the ID to an API or log it
  const patientIdString = unwrapId(patientId);
  const sessionIdString = unwrapId(sessionId);

  // Now you can use them as regular strings
  console.log(`Patient: ${patientIdString}, Session: ${sessionIdString}`);

  // API call example
  fetch(`/api/sessions/${sessionIdString}`, {
    method: 'GET',
  });
}

// ============================================================================
// FUNCTION SIGNATURES WITH BRANDED TYPES
// ============================================================================

interface ApiResponse<T> {
  success: boolean;
  data: T;
}

/**
 * Example: Function that requires a specific ID type
 *
 * This prevents accidentally passing the wrong ID type
 */
export async function fetchSessionData(
  sessionId: SessionId
): Promise<ApiResponse<any>> {
  // TypeScript ensures only SessionId can be passed here
  // If you try: fetchSessionData(patientId) ❌ ERROR
  const response = await fetch(`/api/sessions/${unwrapId(sessionId)}`);
  return response.json();
}

/**
 * Example: Function that requires a PatientId
 */
export async function fetchPatientDetails(
  patientId: PatientId
): Promise<ApiResponse<any>> {
  // TypeScript ensures only PatientId can be passed here
  const response = await fetch(`/api/patients/${unwrapId(patientId)}`);
  return response.json();
}

/**
 * Example: Function that requires both types
 */
export async function assignSessionToTherapist(
  sessionId: SessionId,
  therapistId: UserId
): Promise<ApiResponse<any>> {
  // Clear at a glance which ID is which
  const response = await fetch(`/api/sessions/${unwrapId(sessionId)}/assign`, {
    method: 'POST',
    body: JSON.stringify({
      therapist_id: unwrapId(therapistId),
    }),
  });
  return response.json();
}

// ============================================================================
// WORKING WITH DATA STRUCTURES
// ============================================================================

/**
 * Example: Type-safe data structures
 */
interface SessionRecord {
  id: SessionId;
  patientId: PatientId;
  therapistId: UserId;
  title: string;
}

interface PatientRecord {
  id: PatientId;
  therapistId: UserId;
  name: string;
  email: string;
}

/**
 * Example: Creating and using type-safe records
 */
export function exampleDataStructures() {
  const session: SessionRecord = {
    id: createSessionId('session-abc123'),
    patientId: createPatientId('patient-xyz789'),
    therapistId: createUserId('user-doc001'),
    title: 'Weekly Check-in',
  };

  // Type-safe usage - passing the right ID types
  console.log(
    `Session ${unwrapId(session.id)} for patient ${unwrapId(session.patientId)}`
  );

  // This would fail at compile time with wrong ID types:
  // fetchPatientDetails(session.id);
  // fetchSessionData(session.patientId);

  // Correct usage:
  void fetchPatientDetails(session.patientId);
  void fetchSessionData(session.id);
}

// ============================================================================
// ARRAYS AND COLLECTIONS
// ============================================================================

/**
 * Example: Working with arrays of branded IDs
 */
export function exampleWorkingWithArrays(patientIds: PatientId[]) {
  // Type-safe array operations
  patientIds.forEach((patientId) => {
    // TypeScript knows each element is a PatientId
    void fetchPatientDetails(patientId);
  });

  // Map to API calls
  const requests = patientIds.map((patientId) =>
    fetch(`/api/patients/${unwrapId(patientId)}`)
  );

  return Promise.all(requests);
}

/**
 * Example: Transforming between ID types (when semantically valid)
 */
export function transformIdType(userId: UserId): UserId {
  // Sometimes you might have a UserId and need to use it as something
  // But the type system prevents accidental mixing
  // This requires explicit conversion with a well-named function

  // Example: A userId that's also a therapist
  const therapistId: UserId = userId;
  return therapistId;
}

// ============================================================================
// ERROR HANDLING WITH BRANDED TYPES
// ============================================================================

/**
 * Example: Safe error handling with branded IDs
 */
export async function safelyFetchSession(sessionId: SessionId) {
  try {
    const response = await fetchSessionData(sessionId);
    if (!response.success) {
      console.error(
        `Failed to fetch session ${unwrapId(sessionId)}: unknown error`
      );
      return null;
    }
    return response.data;
  } catch (error) {
    console.error(
      `Error fetching session ${unwrapId(sessionId)}:`,
      error
    );
    return null;
  }
}

// ============================================================================
// INTEGRATION WITH HOOKS (React Pattern)
// ============================================================================

/**
 * Example: Hook signature with branded types
 * (This is a conceptual example - actual implementation would be in a custom hook)
 */
export interface UseSessionHookOptions {
  sessionId: SessionId;
  enabled?: boolean;
}

export interface UseSessionHookReturn {
  data: any | null;
  isLoading: boolean;
  error: Error | null;
}

/**
 * Hypothetical custom hook with branded types
 */
export function useSessionData(
  options: UseSessionHookOptions
): UseSessionHookReturn {
  // Implementation would fetch data using the branded SessionId
  // The type system prevents accidentally passing a PatientId

  return {
    data: null,
    isLoading: false,
    error: null,
  };
}

// ============================================================================
// CONVERSION FROM BACKEND RESPONSES
// ============================================================================

/**
 * Example: Safe conversion from backend API responses
 */
export function processBackendSession(apiResponse: any): SessionRecord | null {
  try {
    // Validate and create branded types from raw backend data
    const sessionId = createSessionId(apiResponse.id);
    const patientId = createPatientId(apiResponse.patient_id);
    const therapistId = createUserId(apiResponse.therapist_id);

    const record: SessionRecord = {
      id: sessionId,
      patientId,
      therapistId,
      title: apiResponse.title,
    };

    return record;
  } catch (error) {
    console.error('Failed to process session from backend:', error);
    return null;
  }
}

// ============================================================================
// BEST PRACTICES SUMMARY
// ============================================================================

/**
 * BEST PRACTICES FOR BRANDED IDS:
 *
 * 1. CREATE IDs immediately when receiving from backend:
 *    const id = createSessionId(apiResponse.id);
 *
 * 2. Use branded types in function signatures:
 *    function getSession(sessionId: SessionId) { ... }
 *
 * 3. Never mix different ID types:
 *    // Bad: function process(id: string) - loses type safety
 *    // Good: function process(id: SessionId) - type-safe
 *
 * 4. UNWRAP only when necessary:
 *    - API calls: unwrapId(sessionId)
 *    - Logging: console.log(unwrapId(sessionId))
 *    - String interpolation: `Session ${unwrapId(sessionId)}`
 *
 * 5. Use type guards for untrusted data:
 *    if (isSessionId(value)) { // use value as SessionId
 *
 * 6. Keep branded IDs throughout the app:
 *    React state, props, context, etc. should use branded types
 *
 * 7. Document why you're using different ID types:
 *    // Clear what each ID represents
 *
 * BENEFITS:
 * - Compile-time safety: Catch ID mix-ups before runtime
 * - Self-documenting code: Clear what type of ID is expected
 * - Prevents bugs: Cannot accidentally pass wrong ID to function
 * - Zero runtime cost: Compiled away, no performance impact
 */
