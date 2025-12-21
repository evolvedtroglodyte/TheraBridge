# TherapyBridge - Deployment Guide

**Quick Hackathon Deployment: Vercel + Supabase**

This guide will get you deployed in ~10 minutes.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│         Next.js Dashboard (Vercel)                  │
│  - Patient dashboard UI                             │
│  - Upload page with drag-drop                       │
│  - Real-time progress tracking                      │
│  - Serverless API routes (/api/*)                   │
└────────────────┬────────────────────────────────────┘
                 │
                 ├─► Supabase
                 │   - PostgreSQL (users, sessions, transcripts)
                 │   - Storage (audio files)
                 │   - Row Level Security (RLS)
                 │
                 └─► OpenAI APIs
                     - Whisper API (transcription)
                     - GPT-4 (session analysis)
```

---

## Step 1: Set Up Supabase (5 minutes)

### 1.1 Create Supabase Project

1. Go to [supabase.com](https://supabase.com) and sign up
2. Click "New Project"
3. Fill in:
   - **Name:** therapybridge-hackathon
   - **Database Password:** (generate and save)
   - **Region:** closest to you
4. Wait 2 minutes for project to spin up

### 1.2 Run Database Schema

1. In Supabase dashboard, go to **SQL Editor**
2. Click "New Query"
3. Copy the entire contents of `/supabase/schema.sql` and paste
4. Click "Run" (bottom right)
5. Verify success (should see "Success. No rows returned")

### 1.3 Get Supabase Credentials

1. Go to **Project Settings** → **API**
2. Copy these values:
   - **Project URL** (e.g., `https://abcdefgh.supabase.co`)
   - **anon public** key (long string starting with `eyJ...`)

---

## Step 2: Deploy to Vercel (3 minutes)

### 2.1 Push to GitHub

```bash
cd "frontend/"
git add .
git commit -m "Ready for deployment"
git push origin main
```

### 2.2 Deploy on Vercel

1. Go to [vercel.com](https://vercel.com) and sign up
2. Click "Add New Project"
3. Import your GitHub repository
4. **Root Directory:** `frontend`
5. **Framework Preset:** Next.js (auto-detected)
6. Click "Deploy"

### 2.3 Configure Environment Variables

While deployment is running, add environment variables:

1. Go to **Project Settings** → **Environment Variables**
2. Add these 3 variables:

| Name | Value | Source |
|------|-------|--------|
| `NEXT_PUBLIC_SUPABASE_URL` | `https://your-project.supabase.co` | Supabase Project Settings → API |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | `eyJ...` (long string) | Supabase Project Settings → API |
| `OPENAI_API_KEY` | `sk-proj-...` | Your OpenAI API key |

3. Click "Save"
4. Go to **Deployments** → Click "..." on latest deployment → **Redeploy**

---

## Step 3: Test End-to-End (2 minutes)

### 3.1 Access Your Deployed App

1. Open your Vercel deployment URL (e.g., `https://therapybridge-xxx.vercel.app`)
2. Navigate to `/patient/dashboard-v3`
3. Click "Upload" in the header

### 3.2 Upload Test Audio

1. Drag and drop an MP3 file (or use the file picker)
2. Click "Upload & Process"
3. Watch the progress bar:
   - 10% - Uploading
   - 30% - Transcribing with Whisper
   - 60% - Speaker diarization
   - 80% - Analyzing with GPT-4
   - 100% - Complete!

4. Review results:
   - Session summary
   - Mood detection
   - Topics discussed
   - Key insights
   - Action items
   - Full transcript with speaker labels

### 3.3 Verify Database

1. Go to Supabase dashboard → **Table Editor**
2. Check `therapy_sessions` table
3. You should see your uploaded session with all the data

---

## Architecture Details

### Serverless API Routes

| Endpoint | Purpose | Max Duration |
|----------|---------|--------------|
| `/api/upload` | Upload audio to Supabase Storage | 60s |
| `/api/process` | Transcribe + analyze audio | 300s (5 min) |
| `/api/status/[id]` | Poll processing status | 10s |
| `/api/trigger-processing` | Start async processing | 10s |

### Processing Flow

```
1. User uploads file
   ↓
2. POST /api/upload
   - Upload to Supabase Storage
   - Create session record (status: pending)
   ↓
3. POST /api/trigger-processing (async)
   - Triggers /api/process in background
   ↓
4. /api/process runs
   - Download audio from Supabase
   - Call OpenAI Whisper API (transcription)
   - Simple speaker diarization (Therapist/Client)
   - Call GPT-4 (analysis: mood, topics, insights)
   - Update session record (status: completed)
   ↓
5. Frontend polls GET /api/status/[id]
   - Every 2 seconds
   - Updates progress bar
   - Shows results when complete
```

### Cost Estimates (Hackathon)

**Free Tier Limits:**
- ✅ Vercel: Free (100GB bandwidth, unlimited deployments)
- ✅ Supabase: Free (500MB database, 1GB storage)
- ⚠️ OpenAI: Pay-per-use
  - Whisper API: $0.006/minute (~$0.36 for 60min audio)
  - GPT-4o: $2.50/1M input tokens (~$0.01 per session)

**Total cost for hackathon demo:** < $5

---

## Troubleshooting

### Error: "Missing Supabase environment variables"

**Fix:** Add `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY` to Vercel env vars and redeploy.

### Error: "Failed to upload file"

**Fix:** Check Supabase Storage bucket exists:
1. Go to Supabase → **Storage**
2. Verify `audio-sessions` bucket exists
3. If not, re-run the SQL schema

### Error: "Processing timeout"

**Fix:** For long audio files (>30min), increase `maxDuration` in `/api/process/route.ts`:
```typescript
export const maxDuration = 300; // Increase to 600 for Vercel Pro
```

### Error: "Row Level Security prevents operation"

**Fix:** Temporarily disable RLS for hackathon:
```sql
ALTER TABLE therapy_sessions DISABLE ROW LEVEL SECURITY;
```

---

## Production Considerations

**For a real production deployment, you would need:**

1. **Authentication**
   - Supabase Auth (email/password, OAuth)
   - Replace mock patient/therapist IDs with real user IDs

2. **Speaker Diarization**
   - Replace simple heuristic with pyannote.audio
   - Options: AssemblyAI API, Deepgram API, or self-hosted pyannote

3. **HIPAA Compliance**
   - Enable Supabase encryption at rest
   - Use Supabase vault for sensitive data
   - Business Associate Agreement (BAA) with vendors

4. **Monitoring**
   - Vercel Analytics
   - Sentry for error tracking
   - Supabase logs for database monitoring

5. **Scaling**
   - Upgrade Vercel to Pro ($20/month) for longer function timeouts
   - Upgrade Supabase to Pro ($25/month) for more storage
   - Consider separate microservice for audio processing

---

## Quick Commands

**Local Development:**
```bash
cd frontend/
npm install
npm run dev
# Open http://localhost:3000/patient/dashboard-v3
```

**Deploy:**
```bash
# Push to GitHub
git add .
git commit -m "Update"
git push origin main

# Vercel auto-deploys on push
```

**Update Environment Variables:**
```bash
# Via Vercel dashboard
# Project Settings → Environment Variables → Edit → Redeploy
```

---

## Support

**Issues?** Check:
1. Vercel deployment logs: Vercel Dashboard → Deployments → Function Logs
2. Supabase logs: Supabase Dashboard → Logs
3. Browser console: Right-click → Inspect → Console tab

**Need help?** Review error messages and check API routes in `/frontend/app/api/`

---

**You're ready to demo! 🚀**
