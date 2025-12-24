# Testing Patterns

**Analysis Date:** 2026-01-08

## Test Framework

**Frontend Runner:**
- Playwright 1.57.0 - E2E testing
- Config: None (using Playwright defaults)
- Location: `frontend/tests/`

**Backend Runner:**
- pytest 8.1.1+ - Unit and integration tests
- Config: `audio-transcription-pipeline/pytest.ini` (shared config)
- Location: `backend/tests/`

**Assertion Library:**
- Playwright: Built-in expect() matchers
- pytest: Built-in assert statements

**Run Commands:**
```bash
# Frontend E2E tests
cd frontend
npx playwright test                              # Run all tests
npx playwright test --ui                         # Interactive mode
npx playwright test dashboard-fonts.spec.ts      # Single file

# Backend unit tests
cd backend
pytest                                           # Run all tests
pytest tests/test_mood_analysis.py              # Single file
pytest -v                                        # Verbose output

# Audio pipeline tests
cd audio-transcription-pipeline
pytest                                           # Run all tests
pytest -m requires_openai                        # Run tests requiring OpenAI API
```

## Test File Organization

**Location:**
- Frontend: `frontend/tests/*.spec.ts` (separate directory)
- Backend: `backend/tests/test_*.py` (separate directory)
- Audio pipeline: `audio-transcription-pipeline/tests/test_*.py`

**Naming:**
- Frontend: `kebab-case.spec.ts` (e.g., `dashboard-fonts.spec.ts`)
- Backend: `test_snake_case.py` (e.g., `test_mood_analysis.py`)

**Structure:**
```
frontend/
├── tests/
│   ├── dashboard-fonts.spec.ts
│   ├── timeline-export.spec.ts
│   ├── modal-positioning.spec.ts
│   └── demo-button.spec.ts     # 42+ total test files

backend/
├── tests/
│   ├── test_mood_analysis.py
│   ├── test_breakthrough_detection.py
│   ├── test_full_pipeline_demo.py
│   └── test_all_algorithms.py  # 10+ total test files

audio-transcription-pipeline/
└── tests/
    └── test_full_pipeline.py
```

## Test Structure

**Frontend Suite Organization (Playwright):**
```typescript
import { test, expect } from '@playwright/test';

test.describe('Dashboard Font Consistency', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3000/dashboard');
    await page.waitForLoadState('networkidle');
  });

  test('Your Journey card has correct title font', async ({ page }) => {
    const title = page.getByText('Your Journey').first();
    const fontFamily = await title.evaluate(el =>
      window.getComputedStyle(el).fontFamily
    );
    expect(fontFamily).toContain('Crimson Pro');
  });
});
```

**Backend Suite Organization (pytest):**
```python
def load_mock_transcript(session_file: str) -> dict:
    """Load a mock transcript JSON file"""
    mock_data_dir = Path(__file__).parent.parent.parent / "mock-therapy-data" / "sessions"
    file_path = mock_data_dir / session_file

    with open(file_path, 'r') as f:
        return json.load(f)

def test_single_session(session_file: str):
    """Test mood analysis on a single session"""
    transcript_data = load_mock_transcript(session_file)
    analyzer = MoodAnalyzer()
    analysis = analyzer.analyze_session_mood(...)

    # Validate mood score
    assert 0.0 <= analysis.mood_score <= 10.0
    assert analysis.mood_score * 2 % 1 == 0  # Must be 0.5 increments
```

**Patterns:**
- Frontend: `test.describe()` for grouping, `test.beforeEach()` for setup
- Backend: Module-level fixtures, direct function testing
- Structure: Arrange/act/assert (implicit in most tests)

## Mocking

**Framework:**
- Frontend: None (E2E tests use real backend)
- Backend: Manual mocking with fixture files

**Patterns:**
```python
# Backend - Mock transcript data from files
def load_mock_transcript(session_file: str) -> dict:
    mock_data_dir = Path(__file__).parent.parent.parent / "mock-therapy-data" / "sessions"
    file_path = mock_data_dir / session_file
    with open(file_path, 'r') as f:
        return json.load(f)
```

**What to Mock:**
- Backend: Transcript data (use fixture JSON files)
- Frontend: Nothing (E2E tests use real API)

**What NOT to Mock:**
- Service logic (test real implementations)
- Database queries (use test database)

## Fixtures and Factories

**Test Data:**
- Backend: JSON fixture files in `mock-therapy-data/sessions/`
- Frontend: Live server at `http://localhost:3000`

**Location:**
- Backend fixtures: `mock-therapy-data/sessions/*.json` (not in backend/ directory)
- Factory functions: Inline in test files (load_mock_transcript)

## Coverage

**Requirements:**
- No enforced coverage target
- Coverage tracked for awareness only

**Configuration:**
- pytest-cov configured in some projects (`Scrapping/requirements.txt`)
- No coverage config in frontend

**View Coverage:**
```bash
# Backend
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

## Test Types

**Frontend (E2E Tests):**
- Scope: Full application flows with real backend
- Example: Font consistency, modal positioning, button interactions
- Speed: Slower (requires server startup)
- Files: `frontend/tests/*.spec.ts` (42+ test files)

**Backend (Unit Tests):**
- Scope: Single service/function in isolation
- Example: Mood score validation, breakthrough detection
- Speed: Fast (<1s per test)
- Files: `backend/tests/test_*.py` (10+ test files)

**Backend (Integration Tests):**
- Scope: Multiple services together with database
- Example: Full pipeline demo test
- Files: `backend/tests/test_full_pipeline_demo.py`

**E2E Tests:**
- Framework: Playwright
- Scope: Full user flows
- Location: `frontend/tests/`

## Common Patterns

**Frontend Async Testing:**
```typescript
test('should load dashboard', async ({ page }) => {
  await page.goto('http://localhost:3000/dashboard');
  await page.waitForLoadState('networkidle');
  await expect(page.getByText('Your Journey')).toBeVisible();
});
```

**Backend Error Testing:**
```python
def test_invalid_mood_score():
    """Mood score must be 0.0-10.0 in 0.5 increments"""
    analysis = MoodAnalysis(mood_score=11.0, ...)  # Should fail validation
    # Pydantic will raise ValidationError automatically
```

**Visual Verification:**
```typescript
test('NavigationBar uses Inter font', async ({ page }) => {
  const nav = page.locator('nav');
  const fontFamily = await nav.evaluate(el =>
    window.getComputedStyle(el).fontFamily
  );
  expect(fontFamily).toContain('Inter');
});
```

**Snapshot Testing:**
- Not used in this codebase
- Prefer explicit assertions

## pytest Configuration

**File:** `audio-transcription-pipeline/pytest.ini`

```ini
[pytest]
python_files = test_*.py
python_classes = Test*
python_functions = test_*
minversion = 3.9
testpaths = tests
pythonpath = . src

markers =
    requires_sample_audio: marks tests that require sample audio files
    requires_openai: marks tests that require OpenAI API key
    requires_hf: marks tests that require HuggingFace token
    integration: marks tests as integration tests
    slow: marks tests as slow running

addopts =
    -ra
    --strict-markers
    --strict-config
    --showlocals
    -v

asyncio_mode = auto
```

**Markers:** Custom markers for conditional test execution
- `requires_sample_audio` - Tests needing audio files
- `requires_openai` - Tests needing OpenAI API key
- `requires_hf` - Tests needing HuggingFace token
- `integration` - Integration tests (vs unit tests)
- `slow` - Slow-running tests

**Run with markers:**
```bash
pytest -m requires_openai    # Only tests requiring OpenAI
pytest -m "not slow"         # Skip slow tests
```

## Testing Gaps

**Missing Tests:**
- SSE connection logic (`frontend/hooks/use-pipeline-events.ts`)
- Demo token validation edge cases (`backend/app/middleware/demo_auth.py`)
- Polling fallback behavior (`frontend/app/patient/lib/usePatientSessions.ts`)
- Background subprocess orchestration (`backend/app/routers/demo.py`)

**Recommendation:**
- Add unit tests for demo_auth.py (token expiry, malformed tokens)
- Add integration tests for polling → SSE fallback
- Add E2E tests for full demo initialization flow

---

*Testing analysis: 2026-01-08*
*Update when test patterns change*
