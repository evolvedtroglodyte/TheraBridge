/**
 * Type definitions for TherapyBridge Dashboard
 * - Session data structures
 * - Task and milestone types
 * - Timeline and mood tracking types
 */

export type MoodType = 'positive' | 'neutral' | 'low';

export interface Session {
  id: string;
  date: string;
  duration: string;
  therapist: string;
  mood: MoodType;
  topics: string[];
  strategy: string;
  actions: string[];
  milestone?: Milestone;
  transcript?: TranscriptEntry[];
  patientSummary?: string;
}

export interface Milestone {
  title: string;
  description: string;
}

export interface TranscriptEntry {
  speaker: 'Therapist' | 'Patient';
  text: string;
}

export interface Task {
  id: string;
  text: string;
  completed: boolean;
  sessionId: string;
  sessionDate: string;
}

/**
 * Chart data point types for different progress metrics.
 * Each metric type has a specific data structure for Recharts.
 */
export interface MoodTrendDataPoint {
  session: string;
  mood: number;
}

export interface HomeworkImpactDataPoint {
  week: string;
  completion: number;
  mood: number;
}

export interface SessionConsistencyDataPoint {
  week: string;
  attended: number;
}

export interface StrategyEffectivenessDataPoint {
  strategy: string;
  effectiveness: number;
}

// Union type for all chart data point types
export type ChartDataPoint =
  | MoodTrendDataPoint
  | HomeworkImpactDataPoint
  | SessionConsistencyDataPoint
  | StrategyEffectivenessDataPoint;

export interface ProgressMetric {
  title: string;
  description: string;
  chartData: ChartDataPoint[];
  insight: string;
  emoji: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

/**
 * Legacy TimelineEntry - kept for backwards compatibility
 * @deprecated Use TimelineEvent union type instead
 */
export interface TimelineEntry {
  sessionId: string;
  date: string;
  duration: string;  // e.g., "45 min"
  topic: string;
  strategy: string;  // Therapeutic technique used
  mood: MoodType;
  milestone?: Milestone;
}

// ============================================
// Timeline Event Types (Mixed Timeline)
// ============================================

/**
 * Discriminator for timeline event types.
 * - 'session': From audio transcript processing
 * - 'major_event': From chatbot, AI-detected and patient-confirmed
 */
export type TimelineEventType = 'session' | 'major_event';

/**
 * Base fields shared by all timeline events.
 */
interface BaseTimelineEvent {
  id: string;
  date: string;           // Display date (e.g., "Dec 17")
  timestamp: Date;        // For chronological sorting
  eventType: TimelineEventType;
}

/**
 * Session timeline event - derived from audio transcripts.
 * Milestones/breakthroughs are detected from transcript content.
 */
export interface SessionTimelineEvent extends BaseTimelineEvent {
  eventType: 'session';
  sessionId: string;
  duration: string;
  topic: string;
  strategy: string;
  mood: MoodType;
  milestone?: Milestone;
}

/**
 * Major event from chatbot - AI-detected significant life events.
 * Must be confirmed by patient before appearing on timeline.
 */
export interface MajorEventEntry extends BaseTimelineEvent {
  eventType: 'major_event';
  title: string;
  summary: string;            // AI-generated context summary
  chatContext: string;        // Summarized chat context (not full conversation)
  relatedSessionId?: string;  // Optional link to related session
  confirmedByPatient: boolean;
  reflection?: string;        // Patient-added reflection (optional)
}

/**
 * Union type for all timeline events.
 * Use eventType discriminator to narrow types:
 *
 * @example
 * if (event.eventType === 'session') {
 *   // TypeScript knows event is SessionTimelineEvent
 *   console.log(event.mood);
 * } else {
 *   // TypeScript knows event is MajorEventEntry
 *   console.log(event.title);
 * }
 */
export type TimelineEvent = SessionTimelineEvent | MajorEventEntry;
