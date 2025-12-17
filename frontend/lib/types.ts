// TypeScript types matching backend Pydantic schemas

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
  name: string;
  category: StrategyCategory;
  status: StrategyStatus;
  context: string;
}

export interface Trigger {
  trigger: string;
  context: string;
  severity: TriggerSeverity;
}

export interface ActionItem {
  task: string;
  category: string;
  details: string;
}

export interface SignificantQuote {
  quote: string;
  context: string;
  timestamp_start?: number | null;
}

export interface RiskFlag {
  type: string;
  evidence: string;
  severity: string;
}

export interface ExtractedNotes {
  key_topics: string[];
  topic_summary: string;
  strategies: Strategy[];
  emotional_themes: string[];
  triggers: Trigger[];
  action_items: ActionItem[];
  significant_quotes: SignificantQuote[];
  session_mood: SessionMood;
  mood_trajectory: MoodTrajectory;
  follow_up_topics: string[];
  unresolved_concerns: string[];
  risk_flags: RiskFlag[];
  therapist_notes: string;
  patient_summary: string;
}

export interface TranscriptSegment {
  start: number;
  end: number;
  speaker: string;
  text: string;
}

export interface Session {
  id: string;
  patient_id: string;
  therapist_id: string;
  session_date: string;
  duration_seconds: number | null;
  audio_filename: string | null;
  audio_url: string | null;
  transcript_text: string | null;
  transcript_segments: TranscriptSegment[] | null;
  extracted_notes: ExtractedNotes | null;
  status: SessionStatus;
  error_message: string | null;
  created_at: string;
  updated_at: string;
  processed_at: string | null;
}

export interface Patient {
  id: string;
  name: string;
  email: string;
  phone: string | null;
  therapist_id: string;
  created_at: string;
  updated_at: string;
}

export interface SessionListItem extends Omit<Session, 'transcript_segments' | 'transcript_text'> {
  // Lightweight session for list views
}
