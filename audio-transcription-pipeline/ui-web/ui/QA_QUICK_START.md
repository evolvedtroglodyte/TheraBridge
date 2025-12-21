# QA Test Suite - Quick Start Guide

## Running the Automated Tests

### Prerequisites
- Server dependencies installed (FastAPI, uvicorn)
- Test samples available in `tests/samples/`
- Python 3.13+ with project venv

### Step 1: Start the Server

```bash
cd /Users/newdldewdl/Global\ Domination\ 2/peerbridge\ proj/audio-transcription-pipeline
source venv/bin/activate
cd ui
python server.py
```

Server should start on: http://localhost:8000

Verify with health check:
```bash
curl http://localhost:8000/health
```

### Step 2: Run the Test Suite

In a new terminal:

```bash
cd /Users/newdldewdl/Global\ Domination\ 2/peerbridge\ proj/audio-transcription-pipeline
source venv/bin/activate
cd ui
python qa_test_suite.py
```

### Step 3: Review Results

Test results will be displayed in console and saved to:
- **UI_TEST_REPORT.md** - Comprehensive markdown report (361 lines)

## Test Coverage

The automated test suite covers:

✓ **File Type Validation** (2 tests)
- Valid MP3 upload
- Valid M4A upload

✓ **Invalid File Rejection** (4 tests)
- TXT file rejection
- JPG file rejection
- Empty file handling (0 bytes)
- Corrupted file handling

✓ **File Size Limits** (3 tests)
- Small files (0.5MB)
- Medium files (15MB)
- Large files (21MB)

✓ **API Integration** (1 test)
- Status endpoint validation

## Current Test Results

**Pass Rate:** 80% (8/10 tests passing)

**Known Issues:**
1. Empty files (0 bytes) are accepted (should be rejected)
2. Corrupted audio files are accepted (should be rejected)

Both issues have fix recommendations in the test report.

## Manual Browser Testing

Automated tests only cover API/backend validation. Manual testing required for:

- [ ] Chrome - UI interactions, drag-and-drop
- [ ] Firefox - File API compatibility
- [ ] Safari - macOS audio formats
- [ ] Edge - Windows compatibility

See **UI_TEST_REPORT.md** section "Browser Compatibility Testing" for detailed checklist.

## Test Files Location

**Valid test samples:**
```
tests/samples/
├── Carl Rogers and Gloria...mp3 (17.6MB)
├── compressed-cbt-session.m4a (15.4MB)
├── LIVE Cognitive Behavioral Therapy Session.mp3 (22.2MB)
└── small_test.mp3 (0.5MB)
```

**Invalid test files:**
```
tests/samples/invalid_test_files/
├── empty.mp3 (0 bytes)
├── corrupted.mp3 (10KB random data)
├── test.txt (text file)
└── test.jpg (image file)
```

## Interpreting Results

### PASS ✓
- Test behaved as expected
- No action needed

### FAIL ✗
- Test found a bug or unexpected behavior
- Review UI_TEST_REPORT.md for details and fix recommendations
- Check "Failed Tests - Detailed Analysis" section

### Performance Metrics
- Upload times are logged for each test
- Baseline: ~60-100 MB/s upload speed (local server)

## Quick Validation Checks

Test the server manually:

```bash
# Upload a valid file
curl -X POST http://localhost:8000/api/upload \
  -F "file=@tests/samples/small_test.mp3" \
  -F "num_speakers=2"

# Check status (replace JOB_ID)
curl http://localhost:8000/api/status/JOB_ID

# Test invalid file (should reject)
curl -X POST http://localhost:8000/api/upload \
  -F "file=@tests/samples/invalid_test_files/test.txt"
```

## Troubleshooting

**Server won't start:**
- Check if port 8000 is already in use: `lsof -i :8000`
- Install dependencies: `pip install fastapi uvicorn python-multipart`

**Tests fail to connect:**
- Verify server is running: `curl http://localhost:8000/health`
- Check API_BASE_URL in qa_test_suite.py (default: localhost:8000)

**Import errors:**
- Activate the project venv: `source venv/bin/activate`
- Install test dependencies: `pip install requests`

## Next Steps

1. **Review the full report:** Open `UI_TEST_REPORT.md`
2. **Fix identified bugs:** See Appendix in report for code suggestions
3. **Run manual browser tests:** Follow checklist in report
4. **Test additional formats:** WAV, OGG, FLAC (add to test suite)
5. **Test edge cases:** Very large files (>100MB, >200MB)

## Contact

For questions about the test suite or results:
- Review `UI_TEST_REPORT.md` (comprehensive documentation)
- Check `qa_test_suite.py` source code (well-commented)
- Refer to Wave 4 completion summary

---

**QA Engineer:** Instance I1
**Wave:** 4 - Quality Assurance
**Date:** 2025-12-20
**Status:** ✓ Complete
