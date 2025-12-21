# TherapyBridge - Railway Deployment Guide

**Ethical, developer-friendly deployment on Railway.app**

Railway is a better alternative to Vercel:
- ✅ Transparent pricing ($5/month credit on free tier)
- ✅ No dark patterns or surprise bills
- ✅ Supports full-stack apps (frontend + backend + databases)
- ✅ Git-based deployments with zero config
- ✅ Built-in PostgreSQL (alternative to Supabase if needed)

---

## Quick Deploy (10 minutes)

### Option 1: Railway + Supabase (Recommended)

**Why this combo:**
- Railway hosts your Next.js app + serverless functions
- Supabase provides PostgreSQL + file storage (generous free tier)
- Total cost: FREE for hackathon (Railway $5 credit + Supabase free tier)

### Option 2: Railway Only (All-in-one)

**Why this works:**
- Railway can host PostgreSQL database directly
- Railway provides file storage via volumes
- Everything in one place
- Total cost: ~$5-10/month after free credit

**For hackathon, I recommend Option 1** (Railway + Supabase) to maximize free tier usage.

---

## Step 1: Set Up Supabase (3 minutes)

Same as before:

1. **Create Supabase Project**
   - Go to [supabase.com](https://supabase.com)
   - Sign up / Log in
   - Click "New Project"
   - Name: `therapybridge-hackathon`
   - Generate database password (save it!)
   - Region: Choose closest to you
   - Wait ~2 minutes

2. **Run Database Schema**
   - SQL Editor → New Query
   - Copy/paste contents of `/supabase/schema.sql`
   - Click "Run"
   - Success!

3. **Get Credentials**
   - Project Settings → API
   - Copy:
     - **Project URL** (e.g., `https://xxx.supabase.co`)
     - **anon public key** (starts with `eyJ...`)

---

## Step 2: Deploy to Railway (5 minutes)

### 2.1 Create Railway Project

1. **Sign up at [railway.app](https://railway.app)**
   - Use GitHub login (easiest)
   - Get $5 free credit (no credit card required!)

2. **Create New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Authorize Railway to access your repository
   - Select your repo

3. **Configure Build Settings**
   - Railway auto-detects Next.js ✅
   - **Root Directory:** `frontend`
   - **Build Command:** `npm run build` (auto-detected)
   - **Start Command:** `npm start` (auto-detected)
   - Click "Deploy"

### 2.2 Add Environment Variables

1. **In Railway dashboard, click your service**
2. **Go to "Variables" tab**
3. **Add these 3 variables:**

```env
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...your-supabase-key
OPENAI_API_KEY=sk-proj-...your-openai-key
```

4. **Click "Deploy"** (Railway will redeploy automatically)

### 2.3 Get Your Public URL

1. **Go to "Settings" tab**
2. **Under "Networking" → "Public Networking"**
3. **Click "Generate Domain"**
4. **Copy your URL** (e.g., `therapybridge-production.up.railway.app`)

---

## Step 3: Test Your Deployment (2 minutes)

1. **Open your Railway URL**
2. **Navigate to `/patient/dashboard-v3`**
3. **Click "Upload" in header**
4. **Upload a test audio file**
5. **Verify transcription works end-to-end**

---

## Railway Configuration File (Optional)

Create `railway.json` in frontend directory for advanced config:

```json
{
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "npm install && npm run build"
  },
  "deploy": {
    "startCommand": "npm start",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

---

## Cost Breakdown (Railway + Supabase)

### Free Tier
- ✅ Railway: $5 credit/month (no credit card!)
- ✅ Supabase: 500MB database + 1GB storage
- ✅ Total: FREE for hackathon (usage <$5/month)

### After Free Credit ($5/month)
- Railway compute: ~$5-10/month for small app
- Supabase: Free tier covers hackathon demo needs
- OpenAI: ~$0.40 per session (pay-per-use)

**Hackathon budget:** $0-5 for entire demo period

---

## Local Development

```bash
cd frontend/
npm install
npm run dev
# Open http://localhost:3000/patient/dashboard-v3
```

---

## Architecture (Railway + Supabase)

```
┌─────────────────────────────────────────────────────┐
│         Next.js App (Railway)                       │
│  - Frontend UI (React 19)                           │
│  - API Routes (serverless-style)                    │
│  - Automatic HTTPS                                  │
│  - Zero-config deployment                           │
└────────────────┬────────────────────────────────────┘
                 │
                 ├─► Supabase
                 │   - PostgreSQL (sessions, users, notes)
                 │   - Storage (audio files)
                 │   - Row Level Security
                 │
                 └─► OpenAI APIs
                     - Whisper (transcription)
                     - GPT-4 (analysis)
```

---

## Advantages Over Vercel

| Feature | Railway | Vercel |
|---------|---------|--------|
| Pricing | Transparent ($5 credit) | Confusing tiers, surprise bills |
| Backend support | ✅ Full backend support | ⚠️ Serverless only |
| Database hosting | ✅ Built-in PostgreSQL | ❌ Must use external |
| Developer ethics | ✅ Developer-first | ⚠️ Questionable practices |
| Free tier | $5 credit, clear limits | Limited, easy to exceed |
| Setup time | 5 minutes | 10 minutes |

---

## Troubleshooting

### Build fails: "Cannot find module '@supabase/supabase-js'"

**Solution:** Railway is using the wrong directory.
1. Go to Settings → Build
2. Set **Root Directory** to `frontend`
3. Redeploy

### API routes return 404

**Solution:** Railway hasn't detected Next.js API routes.
1. Check that `frontend/package.json` has `"type": "module"` removed
2. Ensure Next.js version is 16.x
3. Redeploy

### Environment variables not working

**Solution:** Railway needs redeploy after adding env vars.
1. Add all 3 env vars (Supabase URL, key, OpenAI key)
2. Go to Deployments tab
3. Click "Redeploy" on latest deployment

### "Max retries exceeded" error

**Solution:** Railway is auto-restarting due to crashes.
1. Check logs: Deployments → View Logs
2. Look for error messages
3. Common causes:
   - Missing environment variables
   - Invalid Supabase credentials
   - OpenAI API key quota exceeded

---

## Railway CLI (Optional - for power users)

Install Railway CLI for faster deployments:

```bash
# Install
npm i -g @railway/cli

# Login
railway login

# Link to project
railway link

# Deploy
railway up

# View logs
railway logs

# Add env var
railway variables set NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
```

---

## Alternative: Railway-Only Deployment (No Supabase)

If you want everything on Railway:

1. **Add PostgreSQL database**
   - Railway dashboard → New → PostgreSQL
   - Automatically provisions database
   - Get connection URL from variables

2. **Add Redis (optional, for caching)**
   - Railway dashboard → New → Redis
   - Use for session caching

3. **Update schema**
   - Connect to Railway PostgreSQL via CLI
   - Run `supabase/schema.sql` (compatible with regular PostgreSQL)

4. **File storage**
   - Use Railway volumes for file storage
   - Or use Cloudflare R2 (free 10GB)

---

## Continuous Deployment

Railway auto-deploys on git push:

```bash
git add .
git commit -m "Update feature"
git push origin main
# Railway automatically deploys! 🚀
```

---

## Monitoring & Logs

**View logs:**
1. Railway dashboard → Your service
2. Deployments tab → Click latest deployment
3. View real-time logs

**Metrics:**
1. Go to "Metrics" tab
2. See CPU, memory, network usage
3. Monitor costs in real-time

---

## You're Ready! 🚀

Railway deployment is:
- ✅ **Ethical** - No dark patterns, transparent pricing
- ✅ **Fast** - 5-minute setup
- ✅ **Powerful** - Full backend support
- ✅ **Free** - $5 credit covers hackathon demos
- ✅ **Simple** - Zero config, git-based deployment

**Deploy now:** Just push to GitHub and link Railway!

---

## Support Resources

- **Railway Docs:** [docs.railway.app](https://docs.railway.app)
- **Railway Discord:** [discord.gg/railway](https://discord.gg/railway)
- **Railway Templates:** [railway.app/templates](https://railway.app/templates)

**Go build something amazing! 🎉**
