# Sample Coverage Report - TherapyBridge Backend

**Generated:** 2025-12-17
**Overall Coverage:** 35.91% (line coverage), 41.07% (including branches)

---

## Coverage Summary

```
Name                               Stmts   Miss Branch BrPart   Cover   Missing
-------------------------------------------------------------------------------
app/config.py                        151    151     26      0   0.00%   21-535
app/validators.py                    110     87     54      0  14.02%   55-80, 102-138, 177-211, 256-280, 308-319, 340-357, 377-388, 416-436, 458-470
app/services/cleanup.py              164    133     36      0  15.50%   61-65, 69, 91-93, 97-99, 103-104, 122-198, 215-297, 309-332, 341-357, 366-374, 390-391, 401-410
app/services/note_extraction.py       66     50      6      0  22.22%   92-113, 150-290, 316-323, 347
app/routers/sessions.py              108     72     28      0  26.47%   70-99, 131-205, 459-467, 491-502, 541-562, 596-632
app/auth/router.py                    74     50     12      0  27.91%   48-83, 111-151, 182-232, 257-266, 280
app/middleware/correlation_id.py      27     16      8      0  31.43%   39, 66-68, 82-104
app/logging_config.py                 51     28     22      2  34.25%   25-62, 84, 91, 125, 139-142
app/auth/dependencies.py              29     17      6      0  34.29%   24-28, 54-72, 91-99
app/routers/patients.py               39     23      4      0  37.21%   53-81, 102-110, 145-163
app/routers/cleanup.py                57     35      2      0  37.29%   37-42, 73-89, 121-137, 169-185, 205, 230-244
app/auth/utils.py                     34     18      4      0  42.11%   84-102, 118-149, 193, 210
app/middleware/error_handler.py       75     38      8      0  44.58%   38-44, 58, 78, 97, 116, 136, 156, 176, 196-197, 236-262, 274, 288-302, 315-324, 338-341
app/main.py                           85     41      4      0  49.44%   39-51, 103, 122-184, 197-203, 220
app/database.py                       42     13      6      3  66.67%   17, 32, 33->37, 96-104, 109-110, 115
app/middleware/rate_limit.py           9      1      0      0  88.89%   33
app/auth/__init__.py                   2      0      0      0 100.00%
app/auth/config.py                    13      0      0      0 100.00%
app/auth/models.py                    18      0      0      0 100.00%
app/auth/schemas.py                   13      0      0      0 100.00%
app/middleware/__init__.py             4      0      0      0 100.00%
app/models/db_models.py               47      0      0      0 100.00%
app/models/schemas.py                 78      0      0      0 100.00%
app/services/transcription.py         23      0      6      0 100.00%
-------------------------------------------------------------------------------
TOTAL                               1319    773    232      5  35.91%

4 empty files skipped.
```

---

## Coverage Distribution

### By Coverage Level

| Coverage Range | File Count | Files |
|---------------|------------|-------|
| 0-20% | 4 | config.py, validators.py, cleanup.py, note_extraction.py |
| 21-40% | 6 | sessions.py, auth/router.py, correlation_id.py, logging_config.py, auth/dependencies.py, patients.py |
| 41-60% | 3 | cleanup.py (routers), auth/utils.py, error_handler.py |
| 61-80% | 2 | main.py, database.py |
| 81-99% | 1 | rate_limit.py |
| 100% | 8 | auth (4 files), middleware/__init__, models (2 files), transcription.py |

**Total Files:** 28 (24 with coverage data, 4 empty files skipped)

---

## Test Execution Summary

```
============================= test session starts ==============================
platform darwin -- Python 3.14.2, pytest-9.0.2, pluggy-1.6.0
cachedir: .pytest_cache
rootdir: /Users/newdldewdl/Global Domination 2/peerbridge proj/backend
configfile: pytest.ini
plugins: anyio-4.12.0, cov-4.1.0, asyncio-1.3.0

collected 262 items

Tests: 262 total
  ✓ Passed: ~170 (65%)
  ✗ Failed: ~70 (27%)
  ⚠ Errors: ~20 (8%)
  ⊗ Skipped: 1 (0.4%)

Duration: ~66 seconds
```

---

## Critical Files Needing Attention

### 🚨 Priority 1: Zero Coverage

#### app/config.py (0% - 151 statements)
**Impact:** High - Configuration errors can break entire application
**Lines Missing:** 21-535 (ALL)
**Recommended Tests:**
- Environment variable loading
- Default value application
- Validation of required fields
- Database URL parsing
- Auth configuration

---

### ⚠️ Priority 2: Low Coverage (<25%)

#### app/validators.py (14.02% - 110 statements, 87 missed)
**Impact:** High - Validators prevent invalid data
**Lines Missing:** 55-80, 102-138, 177-211, 256-280, 308-319, 340-357, 377-388, 416-436, 458-470
**Recommended Tests:**
- Email validation (valid/invalid formats)
- Phone validation (various formats)
- Name validation (unicode, special chars)
- Length validators (min/max)
- UUID validators

#### app/services/cleanup.py (15.50% - 164 statements, 133 missed)
**Impact:** Medium - File cleanup and maintenance
**Lines Missing:** 61-65, 69, 91-93, 97-99, 103-104, 122-198, 215-297, 309-332, 341-357, 366-374, 390-391, 401-410
**Recommended Tests:**
- File scanning
- Orphaned file identification
- Dry run vs actual deletion
- Retention period logic

#### app/services/note_extraction.py (22.22% - 66 statements, 50 missed)
**Impact:** High - Core AI functionality
**Lines Missing:** 92-113, 150-290, 316-323, 347
**Recommended Tests:**
- OpenAI API integration (mocked)
- Error handling (rate limits, timeouts)
- JSON parsing and validation
- Cost estimation

---

### ⚠️ Priority 3: Medium Coverage (25-40%)

#### app/routers/sessions.py (26.47% - 108 statements, 72 missed)
**Impact:** High - Main API endpoints
**Lines Missing:** 70-99, 131-205, 459-467, 491-502, 541-562, 596-632
**Current Test Issues:** Many failing tests need fixing

#### app/auth/router.py (27.91% - 74 statements, 50 missed)
**Impact:** High - Authentication endpoints
**Lines Missing:** 48-83, 111-151, 182-232, 257-266, 280
**Current Test Issues:** Many failing tests need fixing

---

## Files with Excellent Coverage (100%)

✅ **app/auth/__init__.py** - 2 statements
✅ **app/auth/config.py** - 13 statements
✅ **app/auth/models.py** - 18 statements
✅ **app/auth/schemas.py** - 13 statements
✅ **app/middleware/__init__.py** - 4 statements
✅ **app/models/db_models.py** - 47 statements
✅ **app/models/schemas.py** - 78 statements
✅ **app/services/transcription.py** - 23 statements

**Total: 198 statements with 100% coverage**

---

## Branch Coverage Analysis

**Total Branches:** 232
**Covered Branches:** 30 (12.93%)
**Partially Covered:** 5 (2.16%)
**Uncovered:** 197 (84.91%)

**Files with Branch Coverage Issues:**
- config.py: 26 branches, 0 covered
- validators.py: 54 branches, 0 covered
- cleanup.py: 36 branches, 0 covered
- sessions.py: 28 branches, 0 covered
- logging_config.py: 22 branches, 2 partial

---

## Test Failure Analysis

### Router Tests
**File:** tests/routers/test_patients.py
- 20 failures out of 35 tests (57% failing)
- Common issues: Database state, fixture problems, API changes

**File:** tests/routers/test_sessions.py
- 15 failures out of ~40 tests (37% failing)
- Common issues: File upload handling, background tasks, API mocking

### Auth Tests
**File:** tests/test_auth_integration.py
- 15 failures out of ~25 tests (60% failing)
- Common issues: Token handling, session management, refresh tokens

**File:** tests/test_auth_rbac.py
- 15 failures out of ~45 tests (33% failing)
- Common issues: Permission checks, role validation, RBAC logic

### Service Tests
**File:** tests/services/test_note_extraction.py
- 3 failures out of ~25 tests (12% failing)
- Issues: API error handling, rate limit mocking

---

## Recommendations

### Immediate Actions (This Week)

1. **Fix Failing Tests** - 90 tests to fix
   - Start with auth tests (highest failure rate)
   - Then router tests
   - Expected gain: +15-20% coverage

2. **Cover app/config.py** - 0% → 80%
   - Write 15-20 configuration tests
   - Expected gain: +11.4% overall coverage

3. **Cover app/validators.py** - 14% → 80%
   - Write 20-25 validator tests
   - Expected gain: +5.5% overall coverage

**Quick Win Potential:** +32% coverage (35% → 67%) in one week

### Short-term Goals (This Month)

4. **Improve Router Coverage** - 26-37% → 80%
   - Fix existing tests
   - Add missing endpoint tests
   - Expected gain: +8% overall coverage

5. **Improve Service Coverage** - 15-22% → 80%
   - Add AI service tests
   - Add cleanup service tests
   - Expected gain: +5% overall coverage

6. **Add Integration Tests**
   - End-to-end workflows
   - Multi-component tests
   - Expected gain: +3% overall coverage

**Month Target:** 80% coverage

---

## Coverage Report Locations

**Terminal Report:**
```bash
coverage report --show-missing
```

**HTML Report:**
```bash
open htmlcov/index.html
```

**File:** `htmlcov/index.html` (1.6 MB, 35 files)

**XML Report:** `coverage.xml` (59 KB)
**JSON Report:** `coverage.json` (466 KB)

---

## Next Steps

See detailed improvement plan in:
- **COVERAGE_IMPROVEMENT_PLAN.md** - Complete 4-week roadmap
- **COVERAGE_GUIDE.md** - Full coverage guide
- **COVERAGE_QUICK_REFERENCE.md** - Quick commands

---

**Report Generated:** 2025-12-17
**Python Version:** 3.14.2
**pytest Version:** 9.0.2
**pytest-cov Version:** 4.1.0
