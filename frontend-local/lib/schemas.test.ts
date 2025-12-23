import {
  SessionSchema,
  PatientSchema,
  UUIDSchema,
  EmailSchema,
  DateStringSchema,
  safeParse,
  validate,
  isValid,
  SessionStatusSchema,
  StrategySchema,
  TriggerSchema,
  ActionItemSchema,
  ExtractedNotesSchema,
  TranscriptSegmentSchema,
  SignificantQuoteSchema,
  RiskFlagSchema,
  SessionMoodSchema,
  MoodTrajectorySchema,
} from './schemas';

// Test UUID validation
const validUUID = '550e8400-e29b-41d4-a716-446655440000';
console.log('Valid UUID:', isValid(UUIDSchema, validUUID)); // true
console.log('Invalid UUID:', isValid(UUIDSchema, 'not-a-uuid')); // false

// Test Email validation
const validEmail = 'test@example.com';
console.log('Valid Email:', isValid(EmailSchema, validEmail)); // true
console.log('Invalid Email:', isValid(EmailSchema, 'not-an-email')); // false

// Test Date String validation
const validDate = '2025-12-17T10:30:00Z';
console.log('Valid Date:', isValid(DateStringSchema, validDate)); // true

// Test Status validation
const validStatus = 'processed';
console.log('Valid Status:', isValid(SessionStatusSchema, validStatus)); // true
console.log('Invalid Status:', isValid(SessionStatusSchema, 'invalid')); // false

// Test Mood validation
const validMood = 'positive';
console.log('Valid Mood:', isValid(SessionMoodSchema, validMood)); // true

// Test basic object validation
const validStrategy = {
  name: 'Deep Breathing',
  category: 'breathing',
  status: 'introduced',
  context: 'Used during anxiety episodes',
};
console.log('Valid Strategy:', safeParse(StrategySchema, validStrategy) !== null);

// Test trigger validation
const validTrigger = {
  trigger: 'Social situations',
  context: 'Mentions feeling anxious around large groups',
  severity: 'moderate',
};
console.log('Valid Trigger:', safeParse(TriggerSchema, validTrigger) !== null);

// Test action item validation
const validActionItem = {
  task: 'Practice breathing exercises',
  category: 'homework',
  details: 'Do 5 minutes daily',
};
console.log('Valid ActionItem:', safeParse(ActionItemSchema, validActionItem) !== null);

// Test transcript segment
const validSegment = {
  start: 0,
  end: 5.5,
  speaker: 'therapist',
  text: 'Hello, how are you feeling today?',
};
console.log('Valid Segment:', safeParse(TranscriptSegmentSchema, validSegment) !== null);

// Test significant quote
const validQuote = {
  quote: 'I feel much better when I practice the breathing',
  context: 'Patient reflection on progress',
  timestamp_start: 120.5,
};
console.log('Valid Quote:', safeParse(SignificantQuoteSchema, validQuote) !== null);

// Test risk flag
const validRiskFlag = {
  type: 'suicidal_ideation',
  evidence: 'Patient mentioned thoughts of self-harm',
  severity: 'high',
};
console.log('Valid RiskFlag:', safeParse(RiskFlagSchema, validRiskFlag) !== null);

console.log('\nAll schema validations completed successfully!');
