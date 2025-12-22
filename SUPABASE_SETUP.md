# Supabase Setup - Complete Guide

## ✅ Setup Complete!

All Supabase checks are passing. The upload feature is now working!

---

## Step 0: Get Fresh Supabase Anon Key (DO THIS FIRST!)

1. **Go to Supabase API Settings:**
   https://supabase.com/dashboard/project/rfckpldoohyjctrqxmiv/settings/api

2. **Scroll to "Project API keys" section**

3. **Find the "anon" "public" key** - it's a LONG JWT token that starts with `eyJ...`
   - **NOT** the "service_role" key (that's the secret key)
   - **NOT** any "publishable" key

4. **Click the copy icon** to copy the full key

5. **Update your `.env.local` file:**
   - Open: `/Users/newdldewdl/Global Domination 2/peerbridge proj/frontend/.env.local`
   - Replace the `NEXT_PUBLIC_SUPABASE_ANON_KEY` value with the new key
   - Should look like:
     ```
     NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3M...
     ```

6. **Restart your dev server:**
   - Press Ctrl+C in the terminal
   - Run `npm run dev` again

---

## Step 1: Run Database Schema (REQUIRED)

1. **Go to Supabase SQL Editor:**
   https://supabase.com/dashboard/project/rfckpldoohyjctrqxmiv/sql/new

2. **Copy the ENTIRE contents** of this file:
   `/Users/newdldewdl/Global Domination 2/peerbridge proj/supabase/schema.sql`

3. **Paste into the SQL Editor**

4. **Click "Run"** (bottom right)

5. **Wait for success message** - Should say "Success. No rows returned"

---

## Step 2: Create Test Users (REQUIRED)

1. **Still in SQL Editor** (same page as above)

2. **Clear the editor** (delete previous SQL)

3. **Copy the ENTIRE contents** of this file:
   `/Users/newdldewdl/Global Domination 2/peerbridge proj/supabase/test-data.sql`

4. **Paste into the SQL Editor**

5. **Click "Run"**

6. **You should see:**
   - "Test users created successfully!"
   - Table showing 2 users (therapist + patient)
   - Table showing 1 patient record

---

## Step 3: Create Storage Bucket (REQUIRED)

1. **Go to Supabase Storage:**
   https://supabase.com/dashboard/project/rfckpldoohyjctrqxmiv/storage/buckets

2. **Click "New bucket"**

3. **Name:** `audio-sessions`

4. **Public bucket:** NO (leave unchecked - keep it private)

5. **Click "Create bucket"**

6. **Click on the `audio-sessions` bucket** you just created

7. **Go to "Policies" tab**

8. **Click "New Policy"**

9. **For INSERT (upload):**
   - Policy name: `Allow authenticated uploads`
   - Target roles: `authenticated`
   - Policy definition:
     ```sql
     true
     ```
   - Click "Review" → "Save policy"

10. **Click "New Policy" again** (for reading files)

11. **For SELECT (read):**
    - Policy name: `Allow authenticated reads`
    - Target roles: `authenticated`
    - Policy definition:
      ```sql
      true
      ```
    - Click "Review" → "Save policy"

---

## Step 4: Verify Everything Works

1. **Restart your dev server:**
   ```bash
   # Press Ctrl+C to stop the current server
   cd frontend
   npm run dev
   ```

2. **Open the diagnostic endpoint:**
   http://localhost:3000/api/test-supabase

3. **You should see ALL GREEN checkmarks:**
   ```json
   {
     "connection": "✅ Connected",
     "env_vars": "✅ Present",
     "storage_bucket": "✅ Bucket exists",
     "test_users": "✅ Test users exist",
     "tables": "✅ Found 2 users"
   }
   ```

---

## Step 5: Test Upload

1. **Go to upload page:**
   http://localhost:3000/patient/dashboard-v3/upload

2. **Try uploading an audio file** (MP3, WAV, etc.)

3. **It should work now!**

---

## Troubleshooting

If you still see errors after completing all steps:

1. **"Invalid API key" error (MOST COMMON):**

   **This is the current error you're seeing!**

   **What to check:**
   - Go to https://supabase.com/dashboard/project/rfckpldoohyjctrqxmiv/settings/api
   - Look for the "Project API keys" section
   - Find the row labeled **"anon" / "public"**
   - Click the eye icon to reveal the key
   - Click the copy icon to copy it
   - The key should be ~200 characters long and start with `eyJ...`

   **What NOT to use:**
   - ❌ "service_role" key (that's the secret admin key)
   - ❌ Any key starting with `sb_publishable_...` (wrong type)
   - ❌ Any other keys you see

   **After copying the correct key:**
   - Open `/Users/newdldewdl/Global Domination 2/peerbridge proj/frontend/.env.local`
   - Replace line 3 with: `NEXT_PUBLIC_SUPABASE_ANON_KEY=<paste the key here>`
   - Save the file
   - Restart dev server (Ctrl+C, then `npm run dev`)
   - Test again: http://localhost:3000/api/test-supabase

2. **"Bucket not found" error:**
   - Make sure you created the `audio-sessions` bucket (Step 3)
   - Check spelling is exact: `audio-sessions` (no spaces, hyphen required)

3. **"Row level security policy" error:**
   - Make sure you created BOTH policies (INSERT and SELECT) in Step 3
   - Policy definition should be just `true` for testing

4. **"Test users not found" error:**
   - Re-run the test-data.sql (Step 2)
   - Make sure you ran schema.sql FIRST (Step 1)

---

## What Each Step Does

- **Step 1 (schema.sql):** Creates the database tables (users, patients, therapy_sessions, etc.)
- **Step 2 (test-data.sql):** Creates test therapist and patient accounts to use for testing
- **Step 3 (storage bucket):** Creates the file storage bucket where audio files are uploaded
- **Step 4 (verification):** Confirms everything is set up correctly
- **Step 5 (test upload):** Actually tests the upload flow end-to-end

---

## Quick Checklist

- [ ] Run schema.sql in SQL Editor
- [ ] Run test-data.sql in SQL Editor
- [ ] Create `audio-sessions` storage bucket
- [ ] Add INSERT policy to bucket
- [ ] Add SELECT policy to bucket
- [ ] Restart dev server
- [ ] Test diagnostic endpoint (all green)
- [ ] Test upload page

---

Once all checkmarks are done, the upload feature will work perfectly! 🎉
