-- TherapyBridge: Supabase Auth Migration
-- Migrates from custom auth (password_hash) to Supabase Auth (auth.users)
--
-- Run this AFTER enabling Supabase Auth in the dashboard

-- Step 1: Drop the old password_hash column (we'll use auth.users instead)
ALTER TABLE users DROP COLUMN IF EXISTS password_hash;

-- Step 2: Add auth_id to link to Supabase Auth
ALTER TABLE users ADD COLUMN IF NOT EXISTS auth_id UUID UNIQUE REFERENCES auth.users(id) ON DELETE CASCADE;

-- Step 3: Create a function to sync Supabase Auth users to our users table
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  -- When a new user signs up via Supabase Auth, create a corresponding user record
  INSERT INTO public.users (auth_id, email, first_name, last_name, role)
  VALUES (
    NEW.id,
    NEW.email,
    COALESCE(NEW.raw_user_meta_data->>'first_name', ''),
    COALESCE(NEW.raw_user_meta_data->>'last_name', ''),
    COALESCE(NEW.raw_user_meta_data->>'role', 'patient') -- default to patient
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Step 4: Create a trigger to automatically sync new auth users
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Step 5: Update RLS policies to use auth.uid() correctly
DROP POLICY IF EXISTS users_select_own ON users;
DROP POLICY IF EXISTS users_update_own ON users;

-- Users can only see their own data (using auth_id)
CREATE POLICY users_select_own ON users
  FOR SELECT
  USING (auth.uid() = auth_id);

CREATE POLICY users_update_own ON users
  FOR UPDATE
  USING (auth.uid() = auth_id);

-- Step 6: Update patients policies
DROP POLICY IF EXISTS patients_select_policy ON patients;

CREATE POLICY patients_select_policy ON patients
  FOR SELECT
  USING (
    auth.uid() IN (SELECT auth_id FROM users WHERE id = user_id) OR
    auth.uid() IN (SELECT auth_id FROM users WHERE id = therapist_id)
  );

-- Step 7: Update therapy_sessions policies
DROP POLICY IF EXISTS sessions_select_policy ON therapy_sessions;
DROP POLICY IF EXISTS sessions_insert_policy ON therapy_sessions;
DROP POLICY IF EXISTS sessions_update_policy ON therapy_sessions;

CREATE POLICY sessions_select_policy ON therapy_sessions
  FOR SELECT
  USING (
    auth.uid() IN (
      SELECT u.auth_id FROM users u
      JOIN patients p ON u.id = p.user_id
      WHERE p.id = patient_id
    ) OR
    auth.uid() IN (SELECT auth_id FROM users WHERE id = therapist_id)
  );

CREATE POLICY sessions_insert_policy ON therapy_sessions
  FOR INSERT
  WITH CHECK (
    auth.uid() IN (SELECT auth_id FROM users WHERE id = therapist_id)
  );

CREATE POLICY sessions_update_policy ON therapy_sessions
  FOR UPDATE
  USING (
    auth.uid() IN (SELECT auth_id FROM users WHERE id = therapist_id)
  );

-- Step 8: Update session_notes policies
DROP POLICY IF EXISTS notes_select_policy ON session_notes;

CREATE POLICY notes_select_policy ON session_notes
  FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM therapy_sessions ts
      JOIN patients p ON ts.patient_id = p.id
      JOIN users u1 ON p.user_id = u1.id
      JOIN users u2 ON ts.therapist_id = u2.id
      WHERE ts.id = session_id
        AND (auth.uid() = u1.auth_id OR auth.uid() = u2.auth_id)
    )
  );

-- Step 9: Update treatment_goals policies
DROP POLICY IF EXISTS goals_select_policy ON treatment_goals;

CREATE POLICY goals_select_policy ON treatment_goals
  FOR SELECT
  USING (
    auth.uid() IN (
      SELECT u.auth_id FROM users u
      JOIN patients p ON u.id = p.user_id
      WHERE p.id = patient_id
    ) OR
    auth.uid() IN (
      SELECT u.auth_id FROM users u
      JOIN patients p ON u.id = p.therapist_id
      WHERE p.id = patient_id
    )
  );

-- Success message
DO $$
BEGIN
  RAISE NOTICE '✅ Supabase Auth migration complete!';
  RAISE NOTICE '';
  RAISE NOTICE 'Next steps:';
  RAISE NOTICE '1. Enable Email provider in Supabase Dashboard > Authentication > Providers';
  RAISE NOTICE '2. Configure Site URL: http://localhost:3000';
  RAISE NOTICE '3. Add Redirect URL: http://localhost:3000/auth/callback';
  RAISE NOTICE '4. Test signup flow in your frontend';
END $$;
