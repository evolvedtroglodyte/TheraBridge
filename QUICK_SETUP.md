# TherapyBridge - Quick Setup Guide

**Get your hackathon demo running in 10 minutes!**

---

## Step 1: Supabase Setup (3 minutes)

1. **Create Supabase Project**
   - Go to [supabase.com](https://supabase.com)
   - Sign up / Log in
   - Click "New Project"
   - Name: `therapybridge-hackathon`
   - Generate strong database password (SAVE THIS!)
   - Region: Choose closest to you
   - Click "Create new project"
   - Wait ~2 minutes for provisioning

2. **Run Database Schema**
   - In Supabase dashboard, click "SQL Editor" (left sidebar)
   - Click "New Query"
   - Open `/supabase/schema.sql` from this repo
   - Copy entire contents and paste into Supabase SQL editor
   - Click "Run" (bottom right)
   - Success! You should see "Success. No rows returned"

3. **Get Your Credentials**
   - Click "Project Settings" (gear icon in sidebar)
   - Click "API" in the left menu
   - Copy these two values (you'll need them next):
     - **Project URL** (e.g., `https://abcdefghijk.supabase.co`)
     - **anon public key** (long string starting with `eyJ...`)

---

## Step 2: Local Development (2 minutes)

1. **Install Dependencies**
   ```bash
   cd frontend/
   npm install
   ```

2. **Configure Environment Variables**

   Edit `frontend/.env.local`:
   ```env
   # Replace these with your actual values:
   NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
   NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...your-key-here

   # Your OpenAI API key (already configured)
   OPENAI_API_KEY=sk-proj-...
   ```

3. **Start Development Server**
   ```bash
   npm run dev
   ```

   Open: [http://localhost:3000/patient/dashboard-v3](http://localhost:3000/patient/dashboard-v3)

4. **Test Upload**
   - Click "Upload" in header
   - Drag and drop an audio file (MP3, WAV, M4A, etc.)
   - Click "Upload & Process"
   - Watch the magic happen! ✨

---

## Step 3: Deploy to Railway (5 minutes)

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Ready for deployment"
   git push origin main
   ```

2. **Create Railway Project**
   - Go to [railway.app](https://railway.app)
   - Sign up with GitHub (get $5 FREE credit!)
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Authorize Railway to access your repository
   - Select your repository
   - **Important:** Set Root Directory to `frontend`
   - Railway auto-detects Next.js ✅
   - Click "Deploy"

3. **Add Environment Variables** (while deployment is running)
   - Click on your service in Railway dashboard
   - Go to "Variables" tab
   - Add these 3 variables:

   | Variable Name | Value | Where to get it |
   |--------------|-------|-----------------|
   | `NEXT_PUBLIC_SUPABASE_URL` | `https://xxx.supabase.co` | Supabase → Project Settings → API |
   | `NEXT_PUBLIC_SUPABASE_ANON_KEY` | `eyJ...` | Supabase → Project Settings → API |
   | `OPENAI_API_KEY` | `sk-proj-...` | Your OpenAI account |

   - Click "Deploy" after adding all variables
   - Railway will automatically redeploy

4. **Get Your Public URL**
   - Go to "Settings" tab
   - Under "Networking" → "Public Networking"
   - Click "Generate Domain"
   - Copy your URL (e.g., `therapybridge-production.up.railway.app`)

5. **Test Your Live App**
   - Open your Railway URL
   - Navigate to `/patient/dashboard-v3`
   - Click "Upload"
   - Upload a test audio file
   - Verify transcription works end-to-end

---

## Troubleshooting

### Error: "Missing Supabase environment variables"
**Solution:** Make sure you added the env vars in Railway and redeployed.

### Error: "Failed to upload file"
**Solution:** Check Supabase Storage:
1. Supabase Dashboard → Storage
2. Verify `audio-sessions` bucket exists
3. If not, re-run the SQL schema

### Error: "Processing failed"
**Solution:** Check function logs:
1. Railway Dashboard → Your service → Deployments
2. Click on latest deployment → View Logs
3. Check error messages in real-time

### Error: "Row Level Security policy violation"
**Solution:** For hackathon demo, you can temporarily disable RLS:
```sql
ALTER TABLE therapy_sessions DISABLE ROW LEVEL SECURITY;
ALTER TABLE users DISABLE ROW LEVEL SECURITY;
ALTER TABLE patients DISABLE ROW LEVEL SECURITY;
```
(In Supabase SQL Editor)

---

## Demo Flow

**Perfect Demo Sequence:**

1. **Show Dashboard** (`/patient/dashboard-v3`)
   - Point out: Timeline, AI Chat, Notes/Goals cards
   - Mention: "This is the patient's personalized dashboard"

2. **Click Upload**
   - Show drag-drop interface
   - Explain: "Supports MP3, WAV, M4A, any audio format"

3. **Upload Audio File**
   - Use a 1-3 minute therapy session recording
   - Show progress bar
   - Explain: "Real-time processing with OpenAI Whisper + GPT-4"
   - Point out stages:
     - ✓ Uploading
     - ✓ Transcribing
     - ✓ Speaker diarization
     - ✓ AI analysis

4. **Show Results**
   - Session summary
   - Mood detection
   - Topics discussed
   - Key insights
   - Action items
   - Full transcript with speaker labels

5. **Navigate Back to Dashboard**
   - Show how session appears in timeline
   - Demonstrate: Click session → Full detail view

---

## Test Audio Files

Need test audio? Use these:

1. **Quick Test (30 seconds):**
   - Record yourself on your phone: "Hi, I'm feeling stressed about work..."
   - Export as MP3

2. **Realistic Demo (2-3 minutes):**
   - Find therapy session roleplay on YouTube
   - Download audio with: `youtube-dl -x --audio-format mp3 [URL]`

3. **Mock Therapy Conversation:**
   ```
   Therapist: "How have you been feeling this week?"
   Client: "I've been struggling with anxiety at work..."
   Therapist: "Can you tell me more about what triggers that anxiety?"
   [etc.]
   ```

---

## Costs (Hackathon)

**Free Tier:**
- ✅ Railway: $5 credit/month (no credit card required!)
- ✅ Supabase: 500MB database, 1GB file storage

**Pay-per-use:**
- ⚠️ OpenAI Whisper API: $0.006/minute of audio
- ⚠️ OpenAI GPT-4: ~$0.01 per analysis

**Total:** ~$0.40 per 10-minute session
**Hackathon budget:** $10-20 for 25-50 demos

---

## Next Steps (Post-Hackathon)

If you want to take this to production:

1. **Add Authentication**
   - Use Supabase Auth
   - Replace mock patient/therapist IDs

2. **Improve Diarization**
   - Integrate pyannote.audio
   - Or use AssemblyAI API

3. **Add Therapist View**
   - Review and edit AI-generated notes
   - Approve before finalizing

4. **HIPAA Compliance**
   - Enable encryption at rest
   - Sign BAAs with vendors
   - Implement audit logs

---

## You're Ready! 🚀

Your hackathon demo is now:
- ✅ Deployed globally on Railway (ethical, transparent pricing!)
- ✅ Connected to Supabase database
- ✅ Processing audio with OpenAI
- ✅ Showing real-time progress
- ✅ Displaying beautiful results

**Go win that hackathon!** 🏆
