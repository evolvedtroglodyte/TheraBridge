/**
 * Supabase client configuration
 * Handles authentication and database queries
 */

import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || '';
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '';

// Only validate at runtime, not during build
if (typeof window !== 'undefined' && (!supabaseUrl || !supabaseAnonKey)) {
  console.error('Missing Supabase environment variables');
}

export const supabase = createClient(
  supabaseUrl || 'https://placeholder.supabase.co',
  supabaseAnonKey || 'placeholder-key'
);

/**
 * Database types (generated from Supabase schema)
 */
export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: 'therapist' | 'patient';
  created_at: string;
  updated_at: string;
}

export interface Patient {
  id: string;
  user_id: string;
  therapist_id: string | null;
  date_of_birth: string | null;
  phone: string | null;
  emergency_contact: string | null;
  created_at: string;
  updated_at: string;
}

export interface TherapySession {
  id: string;
  patient_id: string;
  therapist_id: string | null;
  session_date: string;
  duration_minutes: number | null;

  // Audio processing
  audio_file_url: string | null;
  processing_status: 'pending' | 'processing' | 'completed' | 'failed';
  processing_progress: number;

  // Transcription results
  transcript: TranscriptSegment[] | null;
  summary: string | null;

  // Session analysis
  mood: string | null;
  topics: string[] | null;
  key_insights: string[] | null;
  action_items: string[] | null;

  created_at: string;
  updated_at: string;
}

export interface TranscriptSegment {
  speaker: string;
  text: string;
  start: number;
  end: number;
}

export interface SessionNote {
  id: string;
  session_id: string;
  therapist_id: string | null;
  subjective: string | null;
  objective: string | null;
  assessment: string | null;
  plan: string | null;
  created_by: 'ai' | 'therapist';
  created_at: string;
  updated_at: string;
}

export interface TreatmentGoal {
  id: string;
  patient_id: string;
  title: string;
  description: string | null;
  target_date: string | null;
  status: 'active' | 'completed' | 'paused' | 'cancelled';
  progress: number;
  created_at: string;
  updated_at: string;
}
