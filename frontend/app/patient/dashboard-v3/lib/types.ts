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

export interface ProgressMetric {
  title: string;
  description: string;
  chartData: any[];
  insight: string;
  emoji: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export interface TimelineEntry {
  sessionId: string;
  date: string;
  topic: string;
  mood: MoodType;
  milestone?: Milestone;
}
