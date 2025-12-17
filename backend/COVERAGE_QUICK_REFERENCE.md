# Coverage Quick Reference

## Current Status
- **Coverage:** 35.91%
- **Target:** 80%
- **Tests:** 262 total (170 passing, 70 failing, 20 errors)

---

## Running Coverage

```bash
# Easiest way
./scripts/run_tests_with_coverage.sh

# Quick mode (no HTML)
./scripts/run_tests_with_coverage.sh --quick

# Skip threshold check
./scripts/run_tests_with_coverage.sh --no-threshold

# Clean first
./scripts/run_tests_with_coverage.sh --clean

# Manual pytest
pytest --cov=app --cov-report=html --cov-report=term-missing

# Specific module
pytest tests/test_auth.py --cov=app.auth --cov-report=term
```

---

## Viewing Reports

```bash
# HTML (best)
open htmlcov/index.html

# Terminal
coverage report --show-missing

# Specific file
coverage report --show-missing --include="app/config.py"
```

---

## Files by Coverage Priority

### 🚨 Critical (0-33%) - Fix First
| File | Coverage | Missing Lines |
|------|----------|---------------|
| `app/config.py` | 0.00% | 21-535 (ALL) |
| `app/validators.py` | 14.02% | 55-80, 102-138, 177-211, 256-280 |
| `app/services/cleanup.py` | 15.50% | 91-198, 215-297 |
| `app/services/note_extraction.py` | 22.22% | 92-113, 150-290 |
| `app/routers/sessions.py` | 26.47% | 70-99, 131-205, 459-467 |
| `app/auth/router.py` | 27.91% | 48-83, 111-151, 182-232 |

### ⚠️ Medium (34-49%) - Improve Soon
| File | Coverage |
|------|----------|
| `app/main.py` | 49.44% |
| `app/middleware/error_handler.py` | 44.58% |
| `app/auth/utils.py` | 42.11% |
| `app/routers/patients.py` | 37.21% |

### ✅ Good (80%+)
- `app/models/db_models.py` - 100%
- `app/models/schemas.py` - 100%
- `app/auth/models.py` - 100%
- `app/services/transcription.py` - 100%
- `app/middleware/rate_limit.py` - 88.89%

---

## Test Commands

```bash
# All tests
pytest

# Fast tests only
pytest -m unit

# Slow tests only
pytest -m integration

# Auth tests only
pytest -m auth

# Specific file
pytest tests/test_auth_integration.py

# Specific test
pytest tests/test_auth_integration.py::test_login_success

# Verbose output
pytest -v

# Show print statements
pytest -s

# Stop on first failure
pytest -x

# Run last failed tests
pytest --lf
```

---

## Test Markers

Use these to categorize tests:

```python
@pytest.mark.unit          # Fast unit test
@pytest.mark.integration   # Integration test
@pytest.mark.slow          # Takes >1 second
@pytest.mark.auth          # Authentication test
@pytest.mark.rbac          # Role-based access control
@pytest.mark.db            # Requires database
@pytest.mark.api           # API endpoint test
```

---

## Configuration Files

| File | Purpose |
|------|---------|
| `pytest.ini` | Pytest settings, markers, coverage threshold |
| `.coveragerc` | Coverage.py config, exclusions, report formats |
| `scripts/run_tests_with_coverage.sh` | Convenient test runner |
| `.github/workflows/backend-tests.yml` | CI automation |

---

## Coverage Threshold

**Current:** 80% minimum (set in `pytest.ini`)

### Temporarily bypass threshold
```bash
# Option 1: Use script flag
./scripts/run_tests_with_coverage.sh --no-threshold

# Option 2: Edit pytest.ini
--cov-fail-under=35  # Lower value
```

---

## Excluded from Coverage

- `tests/` - Test files
- `migrations/` - Database migrations
- `venv/` - Virtual environment
- `alembic/` - Migration tool
- `*example.py` - Example files
- Lines with `# pragma: no cover`

---

## Common Issues

### "No coverage collected"
```bash
# Ensure you're in backend/ and venv is active
cd backend
source venv/bin/activate
pytest --cov=app
```

### "Module not found"
```bash
# Install test dependencies
pip install pytest pytest-cov pytest-asyncio httpx
```

### "Threshold not met"
```bash
# Bypass threshold during development
./scripts/run_tests_with_coverage.sh --no-threshold
```

### "Tests failing"
```bash
# Run specific test with verbose output
pytest tests/test_file.py::test_name -vv -s
```

---

## Improving Coverage

### 1. Fix Failing Tests First
- 70 failing tests
- 20 error tests
- Fixing these could add +15-20% coverage

### 2. Cover Critical Files
- `app/config.py` (0% → 80%) = +11.4% overall
- `app/validators.py` (14% → 80%) = +5.5% overall

### 3. Test Edge Cases
- Empty strings
- Null values
- Invalid formats
- Boundary values
- Error conditions

### 4. Test Error Paths
- Invalid input
- Database errors
- API failures
- Permission denied
- Not found

---

## CI Integration

Coverage runs automatically on:
- Push to `main` or `develop`
- Pull requests

Reports uploaded to:
- Codecov (if configured)
- GitHub Actions artifacts

---

## Quick Wins

**Easy ways to boost coverage:**

1. **Fix failing tests** → +15% coverage
2. **Test config.py** → +11% coverage
3. **Test validators.py** → +5% coverage
4. **Test error handlers** → +3% coverage

**Total easy gain:** +34% (35% → 69%)

---

## Resources

- Full guide: `COVERAGE_GUIDE.md`
- HTML reports: `htmlcov/index.html`
- pytest docs: https://docs.pytest.org/
- coverage.py docs: https://coverage.readthedocs.io/
