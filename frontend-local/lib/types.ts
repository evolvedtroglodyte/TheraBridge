// TypeScript types matching backend Pydantic schemas

// ============================================================================
// Branded Types for Type-Safe ID Handling
// ============================================================================
// These branded types prevent accidentally passing the wrong ID type to functions.
// Example: You can't pass a PatientId where a SessionId is expected.
// ============================================================================

/**
 * Branded type for patient IDs.
 * Prevents accidentally using wrong ID types at compile time.
 */
export type PatientId = string & { readonly __brand: 'PatientId' };

/**
 * Branded type for session IDs.
 * Prevents accidentally using wrong ID types at compile time.
 */
export type SessionId = string & { readonly __brand: 'SessionId' };

/**
 * Branded type for user/therapist IDs.
 * Prevents accidentally using wrong ID types at compile time.
 */
export type UserId = string & { readonly __brand: 'UserId' };

/**
 * Helper function to create a branded PatientId.
 * Use this when you have a raw string patient ID from the backend.
 *
 * @example
 * const patientId = createPatientId('patient-123');
 */
export function createPatientId(id: string): PatientId {
  if (!id || id.trim().length === 0) {
    throw new Error('PatientId cannot be empty');
  }
  return id as PatientId;
}

/**
 * Helper function to create a branded SessionId.
 * Use this when you have a raw string session ID from the backend.
 *
 * @example
 * const sessionId = createSessionId('session-456');
 */
export function createSessionId(id: string): SessionId {
  if (!id || id.trim().length === 0) {
    throw new Error('SessionId cannot be empty');
  }
  return id as SessionId;
}

/**
 * Helper function to create a branded UserId.
 * Use this when you have a raw string user/therapist ID from the backend.
 *
 * @example
 * const userId = createUserId('user-789');
 */
export function createUserId(id: string): UserId {
  if (!id || id.trim().length === 0) {
    throw new Error('UserId cannot be empty');
  }
  return id as UserId;
}

/**
 * Type guard to check if a value is a valid PatientId.
 * Useful for runtime validation of untrusted data.
 *
 * @example
 * if (isPatientId(someValue)) {
 *   // TypeScript now knows it's a PatientId
 * }
 */
export function isPatientId(value: any): value is PatientId {
  return typeof value === 'string' && value.trim().length > 0;
}

/**
 * Type guard to check if a value is a valid SessionId.
 * Useful for runtime validation of untrusted data.
 *
 * @example
 * if (isSessionId(someValue)) {
 *   // TypeScript now knows it's a SessionId
 * }
 */
export function isSessionId(value: any): value is SessionId {
  return typeof value === 'string' && value.trim().length > 0;
}

/**
 * Type guard to check if a value is a valid UserId.
 * Useful for runtime validation of untrusted data.
 *
 * @example
 * if (isUserId(someValue)) {
 *   // TypeScript now knows it's a UserId
 * }
 */
export function isUserId(value: any): value is UserId {
  return typeof value === 'string' && value.trim().length > 0;
}

/**
 * Helper to safely extract a raw string from a branded ID type.
 * Useful when you need to pass the ID to an API call or log it.
 *
 * @example
 * const rawId = unwrapId(patientId); // Returns the string value
 */
export function unwrapId(id: PatientId | SessionId | UserId): string {
  return id as string;
}

// ============================================================================

export type SessionStatus =
  | 'uploading'
  | 'transcribing'
  | 'transcribed'
  | 'extracting_notes'
  | 'processed'
  | 'failed';

export type SessionMood =
  | 'very_low'
  | 'low'
  | 'neutral'
  | 'positive'
  | 'very_positive';

export type MoodTrajectory =
  | 'improving'
  | 'declining'
  | 'stable'
  | 'fluctuating';

export type StrategyStatus =
  | 'introduced'
  | 'practiced'
  | 'assigned'
  | 'reviewed';

export type StrategyCategory =
  | 'breathing'
  | 'cognitive'
  | 'behavioral'
  | 'mindfulness'
  | 'interpersonal';

export type TriggerSeverity = 'mild' | 'moderate' | 'severe';

export interface Strategy {
  readonly name: string;
  readonly category: StrategyCategory;
  readonly status: StrategyStatus;
  readonly context: string;
}

export interface Trigger {
  readonly trigger: string;
  readonly context: string;
  readonly severity: TriggerSeverity;
}

export interface ActionItem {
  readonly task: string;
  readonly category: string;
  readonly details: string;
}

export interface SignificantQuote {
  readonly quote: string;
  readonly context: string;
  readonly timestamp_start?: number | null;
}

export interface RiskFlag {
  readonly type: string;
  readonly evidence: string;
  readonly severity: string;
}

export interface ExtractedNotes {
  readonly key_topics: ReadonlyArray<string>;
  readonly topic_summary: string;
  readonly strategies: ReadonlyArray<Strategy>;
  readonly emotional_themes: ReadonlyArray<string>;
  readonly triggers: ReadonlyArray<Trigger>;
  readonly action_items: ReadonlyArray<ActionItem>;
  readonly significant_quotes: ReadonlyArray<SignificantQuote>;
  readonly session_mood: SessionMood;
  readonly mood_trajectory: MoodTrajectory;
  readonly follow_up_topics: ReadonlyArray<string>;
  readonly unresolved_concerns: ReadonlyArray<string>;
  readonly risk_flags: ReadonlyArray<RiskFlag>;
  readonly therapist_notes: string;
  readonly patient_summary: string;
}

export interface TranscriptSegment {
  readonly start: number;
  readonly end: number;
  readonly speaker: string;
  readonly text: string;
}

export interface Session {
  readonly id: string;
  readonly patient_id: string;
  readonly therapist_id: string;
  readonly session_date: string;
  readonly duration_seconds: number | null;
  readonly audio_filename: string | null;
  readonly audio_url: string | null;
  readonly transcript_text: string | null;
  readonly transcript_segments: ReadonlyArray<TranscriptSegment> | null;
  readonly extracted_notes: ExtractedNotes | null;
  readonly status: SessionStatus;
  readonly error_message: string | null;
  readonly created_at: string;
  readonly updated_at: string;
  readonly processed_at: string | null;
}

export interface Patient {
  readonly id: string;
  readonly name: string;
  readonly email: string;
  readonly phone: string | null;
  readonly therapist_id: string;
  readonly created_at: string;
  readonly updated_at: string;
}

// ============================================================================
// Template and Note Types
// ============================================================================

export type TemplateFieldType =
  | 'text'
  | 'textarea'
  | 'select'
  | 'multiselect'
  | 'checkbox'
  | 'number'
  | 'date'
  | 'scale';

export type TemplateType = 'soap' | 'dap' | 'birp' | 'progress' | 'custom';

export type NoteStatus = 'draft' | 'completed' | 'signed';

export interface TemplateField {
  readonly id: string;
  readonly label: string;
  readonly type: TemplateFieldType;
  readonly required: boolean;
  readonly options?: ReadonlyArray<string> | null;
  readonly ai_mapping?: string | null;
  readonly placeholder?: string | null;
  readonly help_text?: string | null;
}

export interface TemplateSection {
  readonly id: string;
  readonly name: string;
  readonly description?: string | null;
  readonly fields: ReadonlyArray<TemplateField>;
}

export interface TemplateStructure {
  readonly sections: ReadonlyArray<TemplateSection>;
}

export interface Template {
  readonly id: string;
  readonly name: string;
  readonly description?: string | null;
  readonly template_type: TemplateType;
  readonly is_system: boolean;
  readonly is_shared: boolean;
  readonly created_by?: string | null;
  readonly structure: TemplateStructure;
  readonly created_at: string;
  readonly updated_at: string;
}

export interface SessionNote {
  readonly id: string;
  readonly session_id: string;
  readonly template_id?: string | null;
  readonly content: Record<string, unknown>;
  readonly status: NoteStatus;
  readonly signed_at?: string | null;
  readonly signed_by?: string | null;
  readonly created_at: string;
  readonly updated_at: string;
}

export interface AutofillResponse {
  readonly template_type: TemplateType;
  readonly auto_filled_content: Record<string, unknown>;
  readonly confidence_scores: Record<string, number>;
  readonly missing_fields: Record<string, ReadonlyArray<string>>;
  readonly metadata: Record<string, unknown>;
}
