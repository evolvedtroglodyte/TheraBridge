-- Test Data for TherapyBridge
-- Creates test users and patients for development/demo

-- Insert test therapist (using proper UUID)
INSERT INTO users (id, email, password_hash, first_name, last_name, role, created_at, updated_at)
VALUES (
  '00000000-0000-0000-0000-000000000001'::uuid,
  'therapist@demo.com',
  '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU8uc9TtFjtu', -- password: demo123
  'Dr. Sarah',
  'Johnson',
  'therapist',
  NOW(),
  NOW()
)
ON CONFLICT (id) DO NOTHING;

-- Insert test patient user (using proper UUID)
INSERT INTO users (id, email, password_hash, first_name, last_name, role, created_at, updated_at)
VALUES (
  '00000000-0000-0000-0000-000000000002'::uuid,
  'patient@demo.com',
  '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU8uc9TtFjtu', -- password: demo123
  'John',
  'Doe',
  'patient',
  NOW(),
  NOW()
)
ON CONFLICT (id) DO NOTHING;

-- Insert patient record (using proper UUID)
INSERT INTO patients (id, user_id, therapist_id, created_at, updated_at)
VALUES (
  '00000000-0000-0000-0000-000000000003'::uuid,
  '00000000-0000-0000-0000-000000000002'::uuid,
  '00000000-0000-0000-0000-000000000001'::uuid,
  NOW(),
  NOW()
)
ON CONFLICT (id) DO NOTHING;

-- Verify insertion
SELECT 'Test users created successfully!' as message;
SELECT id, email, first_name, last_name, role FROM users
WHERE id IN ('00000000-0000-0000-0000-000000000001'::uuid, '00000000-0000-0000-0000-000000000002'::uuid);
SELECT id, user_id, therapist_id FROM patients WHERE id = '00000000-0000-0000-0000-000000000003'::uuid;
