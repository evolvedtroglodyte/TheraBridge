import { z } from 'zod';

// ============================================================================
// ENUM SCHEMAS
// ============================================================================

export const SessionStatusSchema = z.enum([
  'uploading',
  'transcribing',
  'transcribed',
  'extracting_notes',
  'processed',
  'failed',
]);

export const SessionMoodSchema = z.enum([
  'very_low',
  'low',
  'neutral',
  'positive',
  'very_positive',
]);

export const MoodTrajectorySchema = z.enum([
  'improving',
  'declining',
  'stable',
  'fluctuating',
]);

export const StrategyStatusSchema = z.enum([
  'introduced',
  'practiced',
  'assigned',
  'reviewed',
]);

export const StrategyCategorySchema = z.enum([
  'breathing',
  'cognitive',
  'behavioral',
  'mindfulness',
  'interpersonal',
]);

export const TriggerSeveritySchema = z.enum(['mild', 'moderate', 'severe']);

// ============================================================================
// UTILITY VALIDATORS
// ============================================================================

/**
 * UUID validation - matches standard UUID format (v4)
 */
export const UUIDSchema = z.string().uuid('Invalid UUID format');

/**
 * Email validation
 */
export const EmailSchema = z.string().email('Invalid email format');

/**
 * ISO 8601 date string validation
 */
export const ISODateSchema = z.string().datetime({
  message: 'Invalid ISO 8601 date format',
});

/**
 * Flexible date string validation (accepts ISO 8601 and common formats)
 */
export const DateStringSchema = z.string().refine(
  (date) => {
    const parsed = new Date(date);
    return !isNaN(parsed.getTime());
  },
  { message: 'Invalid date format' }
);

/**
 * Non-empty string validation
 */
export const NonEmptyStringSchema = z.string().min(1, 'Cannot be empty');

/**
 * Positive integer validation
 */
export const PositiveIntSchema = z.number().int().positive('Must be a positive integer');

// ============================================================================
// COMPLEX OBJECT SCHEMAS
// ============================================================================

/**
 * Strategy schema - therapeutic strategy used in treatment
 */
export const StrategySchema = z.object({
  name: NonEmptyStringSchema,
  category: StrategyCategorySchema,
  status: StrategyStatusSchema,
  context: NonEmptyStringSchema,
});

export type Strategy = z.infer<typeof StrategySchema>;

/**
 * Trigger schema - identified emotional or situational triggers
 */
export const TriggerSchema = z.object({
  trigger: NonEmptyStringSchema,
  context: NonEmptyStringSchema,
  severity: TriggerSeveritySchema,
});

export type Trigger = z.infer<typeof TriggerSchema>;

/**
 * Action Item schema - tasks and follow-ups from session
 */
export const ActionItemSchema = z.object({
  task: NonEmptyStringSchema,
  category: NonEmptyStringSchema,
  details: NonEmptyStringSchema,
});

export type ActionItem = z.infer<typeof ActionItemSchema>;

/**
 * Significant Quote schema - notable statements from session
 */
export const SignificantQuoteSchema = z.object({
  quote: NonEmptyStringSchema,
  context: NonEmptyStringSchema,
  timestamp_start: z.number().nonnegative('Timestamp must be non-negative').nullable().optional(),
});

export type SignificantQuote = z.infer<typeof SignificantQuoteSchema>;

/**
 * Risk Flag schema - potential safety concerns
 */
export const RiskFlagSchema = z.object({
  type: NonEmptyStringSchema,
  evidence: NonEmptyStringSchema,
  severity: NonEmptyStringSchema,
});

export type RiskFlag = z.infer<typeof RiskFlagSchema>;

/**
 * Extracted Notes schema - AI-generated clinical notes from session
 */
export const ExtractedNotesSchema = z.object({
  key_topics: z.array(NonEmptyStringSchema),
  topic_summary: NonEmptyStringSchema,
  strategies: z.array(StrategySchema),
  emotional_themes: z.array(NonEmptyStringSchema),
  triggers: z.array(TriggerSchema),
  action_items: z.array(ActionItemSchema),
  significant_quotes: z.array(SignificantQuoteSchema),
  session_mood: SessionMoodSchema,
  mood_trajectory: MoodTrajectorySchema,
  follow_up_topics: z.array(NonEmptyStringSchema),
  unresolved_concerns: z.array(NonEmptyStringSchema),
  risk_flags: z.array(RiskFlagSchema),
  therapist_notes: NonEmptyStringSchema,
  patient_summary: NonEmptyStringSchema,
});

export type ExtractedNotes = z.infer<typeof ExtractedNotesSchema>;

/**
 * Transcript Segment schema - individual speaker segments in transcript
 */
export const TranscriptSegmentSchema = z.object({
  start: z.number().nonnegative('Start time must be non-negative'),
  end: z.number().nonnegative('End time must be non-negative'),
  speaker: NonEmptyStringSchema,
  text: NonEmptyStringSchema,
});

export type TranscriptSegment = z.infer<typeof TranscriptSegmentSchema>;

/**
 * Session schema - complete session record with all data
 */
export const SessionSchema = z.object({
  id: UUIDSchema,
  patient_id: UUIDSchema,
  therapist_id: UUIDSchema,
  session_date: DateStringSchema,
  duration_seconds: z.number().nonnegative('Duration must be non-negative').nullable().optional(),
  audio_filename: NonEmptyStringSchema.nullable().optional(),
  audio_url: z.string().url('Invalid URL format').nullable().optional(),
  transcript_text: NonEmptyStringSchema.nullable().optional(),
  transcript_segments: z.array(TranscriptSegmentSchema).nullable().optional(),
  extracted_notes: ExtractedNotesSchema.nullable().optional(),
  status: SessionStatusSchema,
  error_message: NonEmptyStringSchema.nullable().optional(),
  created_at: ISODateSchema,
  updated_at: ISODateSchema,
  processed_at: ISODateSchema.nullable().optional(),
});

export type Session = z.infer<typeof SessionSchema>;

/**
 * Patient schema - patient profile
 */
export const PatientSchema = z.object({
  id: UUIDSchema,
  name: NonEmptyStringSchema,
  email: EmailSchema,
  phone: z.string().nullable().optional(),
  therapist_id: UUIDSchema,
  created_at: ISODateSchema,
  updated_at: ISODateSchema,
});

export type Patient = z.infer<typeof PatientSchema>;

// ============================================================================
// REQUEST/RESPONSE SCHEMAS
// ============================================================================

/**
 * Session upload request schema
 */
export const SessionUploadRequestSchema = z.object({
  patient_id: UUIDSchema,
  session_date: DateStringSchema,
  audio_file: z.instanceof(File, { message: 'Must be a File object' }),
});

export type SessionUploadRequest = z.infer<typeof SessionUploadRequestSchema>;

/**
 * Session creation request schema
 */
export const SessionCreateRequestSchema = z.object({
  patient_id: UUIDSchema,
  session_date: DateStringSchema,
});

export type SessionCreateRequest = z.infer<typeof SessionCreateRequestSchema>;

/**
 * Patient creation request schema
 */
export const PatientCreateRequestSchema = z.object({
  name: NonEmptyStringSchema,
  email: EmailSchema,
  phone: z.string().optional(),
  therapist_id: UUIDSchema,
});

export type PatientCreateRequest = z.infer<typeof PatientCreateRequestSchema>;

/**
 * Paginated response schema (generic)
 */
export const PaginatedResponseSchema = <T extends z.ZodTypeAny>(itemSchema: T) =>
  z.object({
    items: z.array(itemSchema),
    total: PositiveIntSchema,
    page: PositiveIntSchema,
    page_size: PositiveIntSchema,
    has_more: z.boolean(),
  });

/**
 * API error response schema
 */
export const ErrorResponseSchema = z.object({
  detail: z.union([
    NonEmptyStringSchema,
    z.array(
      z.object({
        loc: z.array(z.union([z.string(), z.number()])),
        msg: NonEmptyStringSchema,
        type: NonEmptyStringSchema,
      })
    ),
  ]),
});

export type ErrorResponse = z.infer<typeof ErrorResponseSchema>;

// ============================================================================
// VALIDATION UTILITY FUNCTIONS
// ============================================================================

/**
 * Safely parse and validate data against a schema
 * Returns either the parsed data or null if validation fails
 */
export function safeParse<T>(schema: z.ZodSchema<T>, data: unknown): T | null {
  const result = schema.safeParse(data);
  if (!result.success) {
    console.error('Validation error:', result.error.format());
    return null;
  }
  return result.data;
}

/**
 * Validate and throw on invalid data
 * Use this when you want exceptions for invalid data
 */
export function validate<T>(schema: z.ZodSchema<T>, data: unknown): T {
  return schema.parse(data);
}

/**
 * Get validation errors as a formatted object
 */
export function getValidationErrors<T>(schema: z.ZodSchema<T>, data: unknown) {
  const result = schema.safeParse(data);
  if (!result.success) {
    return result.error.format();
  }
  return null;
}

/**
 * Check if data is valid without parsing
 */
export function isValid<T>(schema: z.ZodSchema<T>, data: unknown): data is T {
  return schema.safeParse(data).success;
}

// ============================================================================
// COLLECTION SCHEMAS
// ============================================================================

/**
 * Sessions list (array of sessions)
 */
export const SessionsListSchema = z.array(SessionSchema);

/**
 * Patients list (array of patients)
 */
export const PatientsListSchema = z.array(PatientSchema);

/**
 * Strategies list (array of strategies)
 */
export const StrategiesListSchema = z.array(StrategySchema);

/**
 * Triggers list (array of triggers)
 */
export const TriggersListSchema = z.array(TriggerSchema);

/**
 * Action items list (array of action items)
 */
export const ActionItemsListSchema = z.array(ActionItemSchema);

/**
 * Risk flags list (array of risk flags)
 */
export const RiskFlagsListSchema = z.array(RiskFlagSchema);

/**
 * Transcript segments list (array of segments)
 */
export const TranscriptSegmentsListSchema = z.array(TranscriptSegmentSchema);
