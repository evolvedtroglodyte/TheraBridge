# Test Coverage Guide - TherapyBridge Backend

## Overview

This document describes the test coverage setup, how to run coverage reports, interpret results, and recommendations for improving coverage.

**Current Coverage: 35.91%** (262 tests, 1319 statements, 773 missed)

---

## Quick Start

### Running Tests with Coverage

```bash
# Simple way - Use the script
./scripts/run_tests_with_coverage.sh

# Quick mode (skip HTML report)
./scripts/run_tests_with_coverage.sh --quick

# Unit tests only
./scripts/run_tests_with_coverage.sh --unit-only

# Skip threshold check (useful during development)
./scripts/run_tests_with_coverage.sh --no-threshold

# Clean previous reports first
./scripts/run_tests_with_coverage.sh --clean
```

### Manual pytest execution

```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests with coverage
pytest --cov=app --cov-report=html --cov-report=term-missing

# Run specific test file
pytest tests/test_auth_integration.py --cov=app --cov-report=term-missing

# Run specific marker
pytest -m unit --cov=app --cov-report=html
```

---

## Coverage Configuration

### Files Involved

1. **`.coveragerc`** - Main coverage.py configuration
   - Defines source directories
   - Excludes patterns (tests, migrations, venv)
   - Branch coverage settings
   - Report formats and styling

2. **`pytest.ini`** - Pytest configuration
   - Coverage threshold: **80% minimum**
   - Report formats: terminal, HTML, XML, JSON
   - Test markers and discovery patterns

3. **`scripts/run_tests_with_coverage.sh`** - Convenience script
   - Automated test execution
   - Multiple output formats
   - Command-line flags for flexibility

4. **`.github/workflows/backend-tests.yml`** - CI integration
   - Automated testing on push/PR
   - Multi-Python version matrix (3.11, 3.12)
   - Coverage reporting to Codecov
   - Artifact uploads for HTML reports

---

## Understanding Coverage Reports

### Terminal Report

After running tests, you'll see:

```
Name                               Stmts   Miss Branch BrPart   Cover   Missing
-------------------------------------------------------------------------------
app/config.py                        151    151     26      0   0.00%   21-535
app/validators.py                    110     87     54      0  14.02%   55-80, 102-138...
app/auth/models.py                    18      0      0      0 100.00%
-------------------------------------------------------------------------------
TOTAL                               1319    773    232      5  35.91%
```

**Column definitions:**
- **Stmts**: Total statements in file
- **Miss**: Statements not executed
- **Branch**: Total branches (if/else decisions)
- **BrPart**: Partially covered branches
- **Cover**: Coverage percentage
- **Missing**: Line numbers not covered

### HTML Report

Open `htmlcov/index.html` in your browser:

```bash
open htmlcov/index.html
```

**Features:**
- Interactive file browser
- Line-by-line coverage visualization
- Red lines = not covered
- Yellow lines = partially covered
- Green lines = fully covered
- Click files to see detailed coverage

### XML/JSON Reports

- **coverage.xml** - For CI tools (Codecov, SonarQube)
- **coverage.json** - Programmatic access to coverage data

---

## Current Coverage Status

### Overall: 35.91%

### Coverage by Category

#### ✅ Excellent (100% coverage)
- `app/auth/__init__.py`
- `app/auth/config.py`
- `app/auth/models.py`
- `app/auth/schemas.py`
- `app/middleware/__init__.py`
- `app/models/db_models.py`
- `app/models/schemas.py`
- `app/services/transcription.py`

#### ⚠️ Good (66-88%)
- `app/middleware/rate_limit.py` - 88.89%
- `app/database.py` - 66.67%

#### ⚠️ Needs Improvement (34-49%)
- `app/main.py` - 49.44%
- `app/middleware/error_handler.py` - 44.58%
- `app/auth/utils.py` - 42.11%
- `app/routers/patients.py` - 37.21%
- `app/routers/cleanup.py` - 37.29%
- `app/auth/dependencies.py` - 34.29%
- `app/logging_config.py` - 34.25%

#### ❌ Critical (0-33%)
- `app/config.py` - 0.00% (151 statements uncovered)
- `app/validators.py` - 14.02%
- `app/services/cleanup.py` - 15.50%
- `app/services/note_extraction.py` - 22.22%
- `app/routers/sessions.py` - 26.47%
- `app/auth/router.py` - 27.91%
- `app/middleware/correlation_id.py` - 31.43%

---

## Recommendations for Improving Coverage

### Priority 1: Critical Files (0-33% coverage)

#### 1. `app/config.py` (0.00%)
**Why it's critical:** Configuration errors can break the entire application

**Recommended tests:**
```python
# tests/test_config.py
def test_config_loads_from_env():
    """Test configuration loads from environment variables"""
    pass

def test_config_validates_required_fields():
    """Test missing required config raises error"""
    pass

def test_config_defaults_applied():
    """Test default values are used when env vars missing"""
    pass

def test_config_database_url_parsing():
    """Test database URL is correctly parsed"""
    pass
```

**Test types needed:**
- Environment variable loading
- Default value application
- Validation of required fields
- Type conversion and coercion
- Edge cases (empty strings, invalid values)

#### 2. `app/validators.py` (14.02%)
**Why it's critical:** Validators prevent invalid data from entering the system

**Recommended tests:**
```python
# tests/test_validators.py
def test_email_validator_valid():
    """Test email validation accepts valid emails"""
    pass

def test_email_validator_invalid():
    """Test email validation rejects invalid emails"""
    pass

def test_phone_validator_various_formats():
    """Test phone validation handles various formats"""
    pass

def test_uuid_validator():
    """Test UUID validation"""
    pass

def test_length_validators():
    """Test min/max length validation"""
    pass
```

**Missing coverage areas:**
- Lines 55-80: Email validation edge cases
- Lines 102-138: Phone number validation
- Lines 177-211: Name validation
- Lines 256-280: Length validators
- Lines 308-319: UUID validators

#### 3. `app/services/cleanup.py` (15.50%)
**Test types needed:**
- File system operations (mocking)
- Database queries for orphaned files
- Retention period logic
- Dry-run vs. actual deletion

#### 4. `app/services/note_extraction.py` (22.22%)
**Test types needed:**
- OpenAI API integration (mocked)
- Error handling (rate limits, timeouts)
- JSON parsing and validation
- Cost estimation accuracy

**Note:** Some tests exist but have failures. Fix existing tests first.

#### 5. `app/routers/sessions.py` (26.47%)
**Missing coverage:**
- Lines 70-99: Audio upload validation
- Lines 131-205: Background processing
- Lines 459-467: Status updates
- Lines 541-562: Session retrieval

**Test types needed:**
- File upload edge cases
- Background task triggering
- Status transitions
- Permission checks

#### 6. `app/auth/router.py` (27.91%)
**Missing coverage:**
- Lines 48-83: Signup edge cases
- Lines 111-151: Login variations
- Lines 182-232: Token refresh
- Lines 257-266: Logout

**Note:** Many auth tests are failing. Debug and fix these first.

### Priority 2: Medium Coverage Files (34-49%)

#### 1. `app/main.py` (49.44%)
**Missing coverage:**
- Startup/shutdown events
- CORS configuration
- Middleware setup
- Health check endpoints

**Recommended approach:**
```python
# tests/test_main.py
def test_app_startup():
    """Test application starts successfully"""
    pass

def test_cors_headers_present():
    """Test CORS headers in responses"""
    pass

def test_health_endpoint():
    """Test /health endpoint returns 200"""
    pass
```

#### 2. `app/middleware/error_handler.py` (44.58%)
**Test types needed:**
- Different error types (404, 500, validation errors)
- Error response format
- Correlation ID inclusion
- Logging on errors

#### 3. `app/database.py` (66.67%)
**Missing coverage:**
- Connection failure handling
- Session cleanup
- Transaction rollback

### Priority 3: Test Suite Quality

#### Current Test Status
- **Total tests:** 262
- **Passing:** ~170 (65%)
- **Failing:** ~70 (27%)
- **Errors:** ~20 (8%)
- **Skipped:** 1

#### Issues to Fix

1. **Router tests** - Many failures in:
   - `tests/routers/test_patients.py`
   - `tests/routers/test_sessions.py`

2. **Auth tests** - Multiple failures in:
   - `tests/test_auth_integration.py`
   - `tests/test_auth_rbac.py`

3. **Service tests** - Some failures in:
   - `tests/services/test_note_extraction.py`

**Recommendation:** Fix failing tests before writing new ones. Failing tests indicate:
- Changes in implementation not reflected in tests
- Test fixtures need updating
- Database state issues between tests

---

## Coverage Best Practices

### 1. Target 80%+ Overall Coverage
- **Current:** 35.91%
- **Target:** 80%
- **Gap:** 44.09%

To reach 80%, focus on:
1. Fix all failing tests (+15-20%)
2. Cover critical files (config, validators) (+20%)
3. Cover routers and services (+15%)
4. Edge cases and error handling (+10%)

### 2. Write Tests Before Code (TDD)
```python
# 1. Write failing test
def test_create_patient_with_valid_data():
    response = client.post("/patients", json={...})
    assert response.status_code == 201

# 2. Implement feature
# (write the code)

# 3. Test passes
```

### 3. Test Edge Cases
- Empty strings
- Null values
- Very long strings
- Invalid formats
- Boundary values (min/max)
- Unicode characters

### 4. Test Error Paths
- Invalid input
- Database errors
- External API failures
- Permission denied
- Not found scenarios

### 5. Use Test Markers
```python
@pytest.mark.unit
def test_validation_function():
    """Fast unit test"""
    pass

@pytest.mark.integration
@pytest.mark.slow
def test_full_workflow():
    """Slower integration test"""
    pass
```

### 6. Keep Tests Fast
- Mock external services (OpenAI, databases for unit tests)
- Use in-memory SQLite for test database
- Run unit tests frequently, integration tests less often

### 7. Don't Test Framework Code
- No need to test FastAPI internals
- Focus on your business logic
- Test your custom validators, services, and routers

---

## Exclusions from Coverage

The following are intentionally excluded (see `.coveragerc`):

### Directories
- `tests/` - Test files themselves
- `migrations/` - Database migrations
- `venv/` - Virtual environment
- `alembic/` - Migration tool

### Patterns
- `*example.py` - Example/demo files
- `__pycache__/` - Python cache
- `*.pyc` - Compiled Python files

### Code Patterns (via comments)
```python
# Lines marked with this comment are excluded
def debug_function():  # pragma: no cover
    """Only used during development"""
    pass

# Don't cover abstract methods
@abstractmethod
def interface_method(self):  # pragma: no cover
    pass
```

---

## CI Integration

### GitHub Actions Workflow

The workflow runs on:
- Push to `main` or `develop`
- Pull requests to `main` or `develop`
- Only when backend files change

**Features:**
- Tests on Python 3.11 and 3.12
- PostgreSQL service container
- Coverage threshold enforcement (80%)
- Codecov integration
- HTML report artifacts (30 days retention)

### Setting Up Codecov

1. Sign up at https://codecov.io
2. Connect your GitHub repository
3. Get your `CODECOV_TOKEN`
4. Add to GitHub secrets: `Settings > Secrets > Actions > New repository secret`
5. Name: `CODECOV_TOKEN`, Value: (your token)

Coverage will be automatically reported on PRs.

---

## Viewing Coverage Locally

### HTML Report (Recommended)
```bash
./scripts/run_tests_with_coverage.sh
open htmlcov/index.html
```

### Terminal Report
```bash
pytest --cov=app --cov-report=term-missing
```

### Coverage for Specific Module
```bash
pytest --cov=app.routers --cov-report=term-missing
```

### Coverage with Context
```bash
# Show which tests cover each line
pytest --cov=app --cov-context=test --cov-report=html
```

---

## Troubleshooting

### "Coverage threshold not met"
```
FAILED: coverage threshold not met (35.91% < 80.00%)
```

**Solution:** Use `--no-threshold` flag during development:
```bash
./scripts/run_tests_with_coverage.sh --no-threshold
```

Or temporarily lower threshold in `pytest.ini`:
```ini
--cov-fail-under=35  # Lower during development
```

### "No coverage data collected"
**Causes:**
- `--cov` flag missing
- Running tests outside backend directory
- Virtual environment not activated

**Solution:**
```bash
cd backend
source venv/bin/activate
pytest --cov=app
```

### "Module not found" errors
**Cause:** Missing test dependencies

**Solution:**
```bash
pip install pytest pytest-cov pytest-asyncio httpx
```

### HTML report not generated
**Solution:** Ensure you include `--cov-report=html`:
```bash
pytest --cov=app --cov-report=html
```

---

## Next Steps

### Immediate Actions (Week 1)
1. ✅ Fix all failing tests
2. ✅ Cover `app/config.py` (0% → 80%)
3. ✅ Cover `app/validators.py` (14% → 80%)
4. ✅ Reach 50% overall coverage

### Short-term Goals (Month 1)
1. ✅ Cover all routers (sessions, patients) to 80%
2. ✅ Cover all services to 80%
3. ✅ Cover middleware and error handlers to 80%
4. ✅ Reach 70% overall coverage

### Long-term Goals (Quarter 1)
1. ✅ Maintain 80%+ coverage on all new code
2. ✅ Add integration tests for full workflows
3. ✅ Add performance/load tests
4. ✅ Achieve 85%+ overall coverage

---

## Resources

- **pytest documentation:** https://docs.pytest.org/
- **pytest-cov documentation:** https://pytest-cov.readthedocs.io/
- **coverage.py documentation:** https://coverage.readthedocs.io/
- **FastAPI testing:** https://fastapi.tiangolo.com/tutorial/testing/
- **Codecov:** https://codecov.io/

---

## Summary

**Current State:**
- 35.91% coverage (1319 statements, 773 missed)
- 262 tests (170 passing, 70 failing, 20 errors, 1 skipped)
- 8 files with 100% coverage
- Configuration complete and working

**Priority Actions:**
1. Fix 90 failing/error tests → +15-20% coverage
2. Cover critical files (config, validators) → +20% coverage
3. Improve router coverage → +15% coverage
4. Add error path tests → +10% coverage

**Target:** 80% coverage within 1 month

**Tools Available:**
- `./scripts/run_tests_with_coverage.sh` - Easy test execution
- HTML reports in `htmlcov/` - Visual coverage inspection
- CI workflow - Automated coverage on every PR
- Codecov integration - Coverage tracking over time
