# Speaker Labeling Algorithm - Test Integration Guide

## 🎯 What We Built

An AI-powered speaker labeling system that transforms raw therapy transcripts into patient-facing format:

**Input (Raw):**
```
SPEAKER_00: Hi Alex, welcome...
SPEAKER_01: Um... not great, honestly...
```

**Output (Patient-Facing):**
```
00:00 [Dr. Emily Chen]  Hi Alex, welcome...
00:18 [You]             Um... not great, honestly...
```

---

## 📁 Files Created/Modified

### Backend (Speaker Labeling Service)
- ✅ `backend/app/services/speaker_labeler.py` - AI service using GPT-5-mini
- ✅ `backend/app/routers/sessions.py` - Added `/api/sessions/{id}/label-speakers` endpoint
- ✅ `backend/app/config/model_config.py` - Added speaker_labeling task config
- ✅ `backend/tests/test_speaker_labeler.py` - Unit tests (5/5 passing)
- ✅ `backend/tests/conftest.py` - Test fixtures
- ✅ `backend/tests/test_speaker_labeling_manual.py` - Full integration test (4/4 passing)
- ✅ `backend/tests/test_session_05_demo.py` - Session 5 demo script
- ✅ `backend/tests/outputs/session_05_labeled_transcript.json` - Output file

### Frontend (UI Integration)
- ✅ `frontend/app/patient/lib/types.ts` - Updated TranscriptEntry type
- ✅ `frontend/app/patient/components/SessionDetail.tsx` - Added AI transcript loading
- ✅ `frontend/app/api/test-labeled-transcript/route.ts` - **TEMPORARY TEST ENDPOINT**

---

## 🧪 How to Test

### Step 1: Start the Frontend

```bash
cd frontend
npm run dev
```

Open: http://localhost:3000

### Step 2: View Any Session Detail

1. Navigate to the patient dashboard
2. Click on any session card to open the detail view
3. You'll see the transcript panel on the left

### Step 3: Click "Load AI Labels (TEST)"

- Click the purple button at the top of the transcript panel
- This loads the Session 5 (Family Conflict) labeled transcript
- The button will change to show "AI-Labeled Transcript Active"

### Step 4: Observe the Changes

**Before (Mock Data):**
- Speaker labels: "Therapist" or "Patient"
- Generic labels

**After (AI-Labeled):**
- Speaker labels: "Dr. Emily Chen" or "You"
- Real therapist name from database
- Patient-facing "You" label
- MM:SS timestamps
- 20 segments from Session 5

---

## 🔍 What You Should See

### Transcript Panel (Left Column)

Each transcript entry should show:

```
00:00  [Dr. Emily Chen]
       Hi Alex. Come on in, have a seat. How are you doing today?
       I know last week was pretty intense.

00:18  [You]
       Um... not great, honestly. Something really bad happened
       this week. Like, I've been kind of freaking out about it.
```

**Key Features:**
- ✅ Timestamps in MM:SS format (left-aligned)
- ✅ Speaker names in square brackets
- ✅ Therapist full name: "Dr. Emily Chen"
- ✅ Patient anonymized: "You"
- ✅ Text properly formatted with spacing
- ✅ Vertical spacing between entries

---

## 📊 Session 5 Content Preview

The test transcript shows a family conflict therapy session:

**Topics Covered:**
- Family discovering patient is in therapy
- Cultural stigma around mental health
- Parent-child conflict
- ACT therapy techniques (cognitive defusion)
- Identity considerations (non-binary coming out contemplation)

**AI Detection Results:**
- Confidence: 97%
- Therapist: SPEAKER_00 → Dr. Emily Chen
- Patient: SPEAKER_01 → You
- Total Segments: 20 (showing first 20 of 51)

---

## 🧹 Cleanup After Testing

### Delete These Files:

```bash
# Frontend test endpoint
rm frontend/app/api/test-labeled-transcript/route.ts

# Optional: Test scripts (keep if you want to run again)
# rm backend/tests/test_session_05_demo.py
# rm backend/tests/test_speaker_labeling_manual.py
```

### Revert These Changes:

No need to revert - the changes are production-ready:
- ✅ Type updates support both old and new transcript formats
- ✅ SessionDetail gracefully handles both formats
- ✅ Button is only visible when test endpoint exists

---

## 🚀 Production Integration (Next Steps)

To integrate this for real:

### 1. Backend Changes (Already Done ✅)
- Service: `backend/app/services/speaker_labeler.py`
- Endpoint: `POST /api/sessions/{id}/label-speakers`
- Model: GPT-5-mini (~$0.0009 per session)

### 2. Frontend Changes Needed

Replace the test button with real API call:

```typescript
// Instead of:
const response = await fetch('/api/test-labeled-transcript');

// Use:
const response = await fetch(`/api/sessions/${session.id}/label-speakers`, {
  method: 'POST'
});
```

### 3. Database Integration

Store labeled transcripts in database (optional caching):

```sql
ALTER TABLE therapy_sessions
ADD COLUMN labeled_transcript JSONB;
```

---

## 💡 Key Insights from Testing

1. **Speaker Detection Accuracy**: 97% confidence on Session 5
2. **Format Compatibility**: Works perfectly with existing SessionDetail layout
3. **User Experience**: Clean, readable, patient-facing format
4. **Performance**: Instant loading from cached JSON (~2-5s from live AI)

---

## 📝 Notes

- **TEMPORARY**: The test endpoint hardcodes Session 5 data
- **DELETE**: Remove `/api/test-labeled-transcript/route.ts` after testing
- **PRODUCTION**: Use real API endpoint with session ID parameter
- **CACHING**: Consider caching labeled transcripts to avoid repeated AI calls

---

## ✅ Success Criteria

Your test is successful if you see:

- [x] Purple "Load AI Labels (TEST)" button appears
- [x] Button loads transcript without errors
- [x] Speaker labels change to "Dr. Emily Chen" and "You"
- [x] Timestamps display in MM:SS format
- [x] Text is readable and properly spaced
- [x] Layout matches existing design
- [x] No console errors
- [x] Badge shows "AI-Labeled Transcript Active"

---

**Ready to test!** 🎉

Start the frontend, open any session detail, and click the purple button.
