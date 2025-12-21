-- TherapyBridge Supabase Schema
-- Simplified schema for hackathon demo
-- Focus: Audio transcription + session management

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table (therapists and patients)
CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  first_name VARCHAR(100) NOT NULL,
  last_name VARCHAR(100) NOT NULL,
  role VARCHAR(20) NOT NULL CHECK (role IN ('therapist', 'patient')),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Patients table (extended user info for patients)
CREATE TABLE IF NOT EXISTS patients (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  therapist_id UUID REFERENCES users(id) ON DELETE SET NULL,
  date_of_birth DATE,
  phone VARCHAR(20),
  emergency_contact VARCHAR(255),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Therapy sessions table
CREATE TABLE IF NOT EXISTS therapy_sessions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  patient_id UUID REFERENCES patients(id) ON DELETE CASCADE,
  therapist_id UUID REFERENCES users(id) ON DELETE SET NULL,
  session_date TIMESTAMP WITH TIME ZONE NOT NULL,
  duration_minutes INTEGER,

  -- Audio processing
  audio_file_url TEXT,
  processing_status VARCHAR(20) DEFAULT 'pending' CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed')),
  processing_progress INTEGER DEFAULT 0,

  -- Transcription results
  transcript JSONB, -- Full transcript with speaker diarization
  summary TEXT,

  -- Session analysis
  mood VARCHAR(50),
  topics TEXT[],
  key_insights TEXT[],
  action_items TEXT[],

  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Session notes table (AI-extracted clinical notes)
CREATE TABLE IF NOT EXISTS session_notes (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  session_id UUID REFERENCES therapy_sessions(id) ON DELETE CASCADE,
  therapist_id UUID REFERENCES users(id) ON DELETE SET NULL,

  -- Note content
  subjective TEXT,
  objective TEXT,
  assessment TEXT,
  plan TEXT,

  -- Metadata
  created_by VARCHAR(20) DEFAULT 'ai' CHECK (created_by IN ('ai', 'therapist')),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Treatment goals table
CREATE TABLE IF NOT EXISTS treatment_goals (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  patient_id UUID REFERENCES patients(id) ON DELETE CASCADE,
  title VARCHAR(255) NOT NULL,
  description TEXT,
  target_date DATE,
  status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'completed', 'paused', 'cancelled')),
  progress INTEGER DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_patients_user_id ON patients(user_id);
CREATE INDEX IF NOT EXISTS idx_patients_therapist_id ON patients(therapist_id);
CREATE INDEX IF NOT EXISTS idx_therapy_sessions_patient_id ON therapy_sessions(patient_id);
CREATE INDEX IF NOT EXISTS idx_therapy_sessions_therapist_id ON therapy_sessions(therapist_id);
CREATE INDEX IF NOT EXISTS idx_therapy_sessions_status ON therapy_sessions(processing_status);
CREATE INDEX IF NOT EXISTS idx_session_notes_session_id ON session_notes(session_id);
CREATE INDEX IF NOT EXISTS idx_treatment_goals_patient_id ON treatment_goals(patient_id);

-- Row Level Security (RLS) Policies
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE patients ENABLE ROW LEVEL SECURITY;
ALTER TABLE therapy_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE session_notes ENABLE ROW LEVEL SECURITY;
ALTER TABLE treatment_goals ENABLE ROW LEVEL SECURITY;

-- Users can only see their own data
CREATE POLICY users_select_own ON users FOR SELECT USING (auth.uid() = id);
CREATE POLICY users_update_own ON users FOR UPDATE USING (auth.uid() = id);

-- Patients can see their own data, therapists can see their patients
CREATE POLICY patients_select_policy ON patients FOR SELECT USING (
  auth.uid() = user_id OR
  auth.uid() = therapist_id
);

-- Sessions: patients see their own, therapists see their patients' sessions
CREATE POLICY sessions_select_policy ON therapy_sessions FOR SELECT USING (
  auth.uid() IN (
    SELECT user_id FROM patients WHERE id = patient_id
  ) OR
  auth.uid() = therapist_id
);

CREATE POLICY sessions_insert_policy ON therapy_sessions FOR INSERT WITH CHECK (
  auth.uid() = therapist_id
);

CREATE POLICY sessions_update_policy ON therapy_sessions FOR UPDATE USING (
  auth.uid() = therapist_id
);

-- Notes: same as sessions
CREATE POLICY notes_select_policy ON session_notes FOR SELECT USING (
  EXISTS (
    SELECT 1 FROM therapy_sessions ts
    JOIN patients p ON ts.patient_id = p.id
    WHERE ts.id = session_id AND (auth.uid() = p.user_id OR auth.uid() = ts.therapist_id)
  )
);

-- Goals: patients see their own, therapists see their patients' goals
CREATE POLICY goals_select_policy ON treatment_goals FOR SELECT USING (
  auth.uid() IN (
    SELECT user_id FROM patients WHERE id = patient_id
  ) OR
  auth.uid() IN (
    SELECT therapist_id FROM patients WHERE id = patient_id
  )
);

-- Storage bucket for audio files
INSERT INTO storage.buckets (id, name, public)
VALUES ('audio-sessions', 'audio-sessions', false)
ON CONFLICT (id) DO NOTHING;

-- Storage policies
CREATE POLICY "Authenticated users can upload audio"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (bucket_id = 'audio-sessions');

CREATE POLICY "Users can access their own audio files"
ON storage.objects FOR SELECT
TO authenticated
USING (bucket_id = 'audio-sessions');
