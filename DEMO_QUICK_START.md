# Demo System - Quick Start Guide

## 🚀 Testing the Demo (5 Steps)

### Step 1: Apply SQL Migration
```bash
# Connect to Supabase and run:
supabase/migrations/005_seed_demo_function.sql

# Or via Supabase dashboard:
# SQL Editor → paste contents of 005_seed_demo_function.sql → Run
```

### Step 2: Start Backend
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
# Server runs on http://localhost:8000
```

### Step 3: Start Frontend
```bash
cd frontend
npm run dev
# Frontend runs on http://localhost:3000
```

### Step 4: Try Demo
1. Open browser: http://localhost:3000
2. Click "Try Demo (10 Sessions Pre-Loaded)"
3. Wait 2-3 seconds for initialization
4. You'll be redirected to `/patient/dashboard-v3`
5. See 10 therapy sessions (AI analysis running in background)

### Step 5: Verify Multi-Browser Isolation
1. Open incognito window
2. Go to http://localhost:3000
3. Click "Try Demo" again
4. Verify you see different demo data

---

## 📊 Check Analysis Progress

### Option 1: Via API
```bash
# Get your demo token from browser console (after initialization)
curl -H "X-Demo-Token: <your-token>" http://localhost:8000/api/demo/status

# Response shows:
# - analysis_status: "pending" | "processing" | "wave1_complete" | "wave2_complete"
# - wave1_complete: 0-10
# - wave2_complete: 0-10
```

### Option 2: Via Database
```sql
-- Check Wave 1 progress (sessions with mood_score)
SELECT COUNT(*) FROM therapy_sessions WHERE mood_score IS NOT NULL;

-- Check Wave 2 progress (sessions with deep_analysis)
SELECT COUNT(*) FROM therapy_sessions WHERE deep_analysis IS NOT NULL;
```

---

## 🧪 Manual Testing (Optional)

### Test Wave 1 Script
```bash
cd backend
source venv/bin/activate

# Get patient_id from /api/demo/initialize response
python scripts/seed_wave1_analysis.py <patient_id>

# Expected: 5-10 minutes, updates 10 sessions with mood/topics/breakthroughs
```

### Test Wave 2 Script
```bash
cd backend
source venv/bin/activate

# Run AFTER Wave 1 completes
python scripts/seed_wave2_analysis.py <patient_id>

# Expected: 5-10 minutes, updates 10 sessions with deep_analysis
```

---

## 🎯 What You Should See

### Immediately After "Try Demo":
- ✅ Redirected to `/patient/dashboard-v3`
- ✅ 10 sessions visible (Jan 10 - Apr 11)
- ✅ Session titles, dates visible
- ⏳ AI analysis fields empty (processing in background)

### After 10 Minutes (Wave 1 Complete):
- ✅ Mood scores appear
- ✅ Topics and action items visible
- ✅ Breakthrough badges show up
- ⏳ Deep insights still processing

### After 20 Minutes (Wave 2 Complete):
- ✅ All AI analysis visible
- ✅ Progress indicators populated
- ✅ Therapeutic insights available
- ✅ Coping skills tracked

---

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| "Function does not exist" | Apply SQL migration: `005_seed_demo_function.sql` |
| "No module named 'app'" | Run scripts from `backend/` directory |
| "OPENAI_API_KEY not found" | Set in `backend/.env` |
| Demo button doesn't work | Check backend is running on :8000 |
| No sessions appear | Check browser console for errors |
| Analysis never completes | Check backend logs for errors |

---

## 📁 Key Files

| File | Purpose |
|------|---------|
| `supabase/migrations/005_seed_demo_function.sql` | Creates demo user + 10 sessions |
| `backend/scripts/seed_wave1_analysis.py` | Runs mood/topics/breakthrough analysis |
| `backend/scripts/seed_wave2_analysis.py` | Runs deep insights with cumulative context |
| `backend/app/routers/demo.py` | Demo API endpoints |
| `frontend/app/page.tsx` | Landing page with "Try Demo" button |

---

## 💰 Cost Per Demo User

- Wave 1: 30 AI calls × $0.001 = **$0.03**
- Wave 2: 10 AI calls × $0.003 = **$0.03**
- **Total: ~$0.06 per demo user**

---

## 🎉 Success Checklist

- [ ] SQL migration applied successfully
- [ ] Backend running without errors
- [ ] Frontend running without errors
- [ ] "Try Demo" button works
- [ ] 10 sessions appear in dashboard
- [ ] Demo token stored in localStorage
- [ ] Incognito window gets different demo data
- [ ] Wave 1 analysis completes (check `/api/demo/status`)
- [ ] Wave 2 analysis completes (check `/api/demo/status`)
- [ ] All AI insights visible in dashboard

---

**Need help?** See full documentation in `DEMO_INTEGRATION_COMPLETE.md`
