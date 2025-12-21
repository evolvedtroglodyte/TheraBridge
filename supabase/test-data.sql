-- Test Data for TherapyBridge
-- Creates test users and patients for development/demo

-- Insert test therapist
INSERT INTO users (id, email, password_hash, first_name, last_name, role, created_at, updated_at)
VALUES (
  'therapist-456',
  'therapist@demo.com',
  '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU8uc9TtFjtu', -- password: demo123
  'Dr. Sarah',
  'Johnson',
  'therapist',
  NOW(),
  NOW()
)
ON CONFLICT (id) DO NOTHING;

-- Insert test patient user
INSERT INTO users (id, email, password_hash, first_name, last_name, role, created_at, updated_at)
VALUES (
  'user-patient-123',
  'patient@demo.com',
  '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU8uc9TtFjtu', -- password: demo123
  'John',
  'Doe',
  'patient',
  NOW(),
  NOW()
)
ON CONFLICT (id) DO NOTHING;

-- Insert patient record
INSERT INTO patients (id, user_id, therapist_id, created_at, updated_at)
VALUES (
  'patient-123',
  'user-patient-123',
  'therapist-456',
  NOW(),
  NOW()
)
ON CONFLICT (id) DO NOTHING;

-- Verify insertion
SELECT 'Test users created successfully!' as message;
SELECT * FROM users WHERE id IN ('therapist-456', 'user-patient-123');
SELECT * FROM patients WHERE id = 'patient-123';
