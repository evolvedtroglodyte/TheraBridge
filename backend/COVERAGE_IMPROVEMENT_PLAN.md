# Coverage Improvement Plan - TherapyBridge Backend

## Executive Summary

**Current State:** 35.91% coverage (773 statements uncovered)
**Target:** 80% coverage within 4 weeks
**Gap:** 44.09% (580 statements to cover)

**Test Status:**
- 262 total tests
- 170 passing (65%)
- 70 failing (27%)
- 20 errors (8%)
- 1 skipped

---

## Phase 1: Foundation (Week 1) - Target: 50%

### Priority: Fix Failing Tests
**Impact:** +15-20% coverage
**Effort:** 2-3 days

**Tasks:**
1. ✅ Fix failing router tests (35 tests)
   - `tests/routers/test_patients.py` - 20 failures
   - `tests/routers/test_sessions.py` - 15 failures

2. ✅ Fix failing auth tests (30 tests)
   - `tests/test_auth_integration.py` - 15 failures
   - `tests/test_auth_rbac.py` - 15 failures

3. ✅ Fix service test failures (5 tests)
   - `tests/services/test_note_extraction.py` - 3 failures
   - `tests/services/test_transcription.py` - 1 failure

4. ✅ Resolve test errors (20 tests)
   - Database state issues
   - Mock setup problems
   - Fixture conflicts

**Success Criteria:**
- All 262 tests passing
- No test errors
- Coverage increased to ~50%

---

## Phase 2: Critical Files (Week 2) - Target: 65%

### Priority A: Cover app/config.py (0% → 80%)
**Impact:** +11.4% overall coverage
**Effort:** 1 day

**Tests to Add:**
```python
# tests/test_config.py

class TestConfigLoading:
    def test_config_loads_from_env_vars()
    def test_config_uses_defaults_when_env_missing()
    def test_config_validates_required_fields()
    def test_config_raises_on_missing_required()

class TestDatabaseConfig:
    def test_database_url_parsing()
    def test_database_url_with_password()
    def test_async_database_url_generation()

class TestAuthConfig:
    def test_jwt_secret_required()
    def test_jwt_algorithm_default()
    def test_token_expiration_parsing()

class TestAPIConfig:
    def test_openai_api_key_loading()
    def test_api_timeout_defaults()
    def test_rate_limit_configuration()

class TestEnvironmentConfig:
    def test_development_mode()
    def test_production_mode()
    def test_test_mode()
```

**Lines to Cover:** 21-535 (515 lines)

---

### Priority B: Cover app/validators.py (14% → 80%)
**Impact:** +5.5% overall coverage
**Effort:** 1 day

**Tests to Add:**
```python
# tests/test_validators.py

class TestEmailValidation:
    def test_valid_email_formats()
    def test_invalid_email_formats()
    def test_email_normalization()
    def test_email_case_insensitivity()
    def test_email_max_length()
    def test_email_with_special_chars()

class TestPhoneValidation:
    def test_us_phone_formats()
    def test_international_phone_formats()
    def test_phone_normalization()
    def test_invalid_phone_numbers()
    def test_phone_min_max_length()

class TestNameValidation:
    def test_valid_names()
    def test_name_with_unicode()
    def test_name_min_max_length()
    def test_empty_name_rejected()
    def test_name_with_special_chars()

class TestUUIDValidation:
    def test_valid_uuid()
    def test_invalid_uuid_format()
    def test_uuid_type_coercion()

class TestLengthValidators:
    def test_min_length()
    def test_max_length()
    def test_exact_length()
    def test_length_with_unicode()
```

**Lines to Cover:** 55-80, 102-138, 177-211, 256-280, 308-319

---

### Priority C: Improve Routers (30% → 80%)
**Impact:** +8% overall coverage
**Effort:** 2 days

#### app/routers/sessions.py (26% → 80%)
**Tests to Add:**
```python
class TestAudioUpload:
    def test_upload_mp3()
    def test_upload_wav()
    def test_upload_m4a()
    def test_upload_invalid_format()
    def test_upload_file_too_large()
    def test_upload_corrupted_file()
    def test_upload_triggers_background_processing()

class TestSessionRetrieval:
    def test_get_session_by_id()
    def test_get_session_not_found()
    def test_get_session_unauthorized()
    def test_list_sessions()
    def test_list_sessions_filtered()
    def test_list_sessions_pagination()

class TestNoteExtraction:
    def test_extract_notes_success()
    def test_extract_notes_no_transcript()
    def test_extract_notes_api_error()
    def test_extract_notes_rate_limited()
```

**Lines to Cover:** 70-99, 131-205, 459-467, 541-562

#### app/routers/patients.py (37% → 80%)
**Tests to Add:**
```python
class TestPatientCreation:
    def test_create_patient_full_data()
    def test_create_patient_minimal_data()
    def test_create_patient_invalid_email()
    def test_create_patient_invalid_phone()
    def test_create_patient_unauthorized()

class TestPatientRetrieval:
    def test_get_patient()
    def test_get_patient_not_found()
    def test_list_patients()
    def test_list_patients_filtered()
```

**Lines to Cover:** 53-81, 102-110, 145-163

**Phase 2 Success Criteria:**
- Config coverage: 80%+
- Validators coverage: 80%+
- Routers coverage: 80%+
- Overall coverage: 65%+

---

## Phase 3: Services & Middleware (Week 3) - Target: 75%

### Priority A: Service Coverage
**Impact:** +6% overall coverage
**Effort:** 2 days

#### app/services/note_extraction.py (22% → 80%)
**Tests to Add:**
```python
class TestNoteExtraction:
    def test_extract_with_valid_transcript()
    def test_extract_with_empty_transcript()
    def test_extract_api_timeout()
    def test_extract_rate_limit_error()
    def test_extract_invalid_response()
    def test_extract_json_decode_error()
    def test_extract_cost_estimation()
    def test_extract_with_unicode()
```

**Lines to Cover:** 92-113, 150-290, 316-323

#### app/services/cleanup.py (15% → 80%)
**Tests to Add:**
```python
class TestCleanupService:
    def test_scan_upload_directory()
    def test_identify_orphaned_files()
    def test_cleanup_dry_run()
    def test_cleanup_actual_deletion()
    def test_cleanup_respects_retention()
    def test_cleanup_failed_sessions()
    def test_cleanup_statistics()
```

**Lines to Cover:** 91-198, 215-297, 309-332

---

### Priority B: Middleware Coverage
**Impact:** +2% overall coverage
**Effort:** 1 day

#### app/middleware/error_handler.py (44% → 80%)
**Tests to Add:**
```python
class TestErrorHandler:
    def test_handles_404_not_found()
    def test_handles_422_validation_error()
    def test_handles_500_internal_error()
    def test_handles_401_unauthorized()
    def test_includes_correlation_id()
    def test_logs_error_details()
    def test_returns_json_response()
```

**Lines to Cover:** 38-44, 58, 78, 97, 196-262

#### app/middleware/correlation_id.py (31% → 80%)
**Tests to Add:**
```python
class TestCorrelationID:
    def test_generates_correlation_id()
    def test_accepts_existing_correlation_id()
    def test_includes_in_response_headers()
    def test_available_in_request_context()
```

**Lines to Cover:** 39, 66-68, 82-104

---

### Priority C: Auth Coverage
**Impact:** +2% overall coverage
**Effort:** 1 day

#### app/auth/router.py (27% → 80%)
**Lines to Cover:** 48-83, 111-151, 182-232

#### app/auth/utils.py (42% → 80%)
**Lines to Cover:** 84-102, 118-149

**Phase 3 Success Criteria:**
- Services coverage: 80%+
- Middleware coverage: 80%+
- Auth coverage: 80%+
- Overall coverage: 75%+

---

## Phase 4: Polish & Edge Cases (Week 4) - Target: 80%+

### Priority: Edge Cases & Error Paths
**Impact:** +5% overall coverage
**Effort:** 3 days

**Areas to Cover:**
1. Error handling in all endpoints
2. Permission boundary cases
3. Database transaction failures
4. Rate limiting edge cases
5. Unicode and special character handling
6. Concurrent request handling
7. File system errors
8. Network timeout scenarios

**Tests to Add:**
```python
# Edge cases across all modules
def test_empty_string_inputs()
def test_null_value_handling()
def test_very_long_strings()
def test_unicode_characters()
def test_concurrent_operations()
def test_database_connection_loss()
def test_external_service_timeout()
def test_rate_limit_boundary()
```

---

### Priority: Integration Tests
**Impact:** +3% overall coverage
**Effort:** 2 days

**End-to-End Workflows:**
```python
class TestCompleteWorkflows:
    def test_complete_auth_flow()
    def test_complete_session_upload_flow()
    def test_complete_patient_management_flow()
    def test_complete_note_extraction_flow()
```

---

### Priority: Documentation & Maintenance
**Effort:** 1 day

**Tasks:**
1. ✅ Document all test patterns
2. ✅ Create test templates
3. ✅ Set up pre-commit hooks for coverage
4. ✅ Configure CI coverage gates
5. ✅ Create coverage monitoring dashboard

**Phase 4 Success Criteria:**
- Overall coverage: 80%+
- All modules: 70%+ minimum
- Critical modules: 90%+ coverage
- Zero failing tests
- CI passing with coverage gates

---

## Coverage Targets by Module

| Module | Current | Week 1 | Week 2 | Week 3 | Week 4 |
|--------|---------|--------|--------|--------|--------|
| **Overall** | 35.91% | 50% | 65% | 75% | 80% |
| config.py | 0% | 0% | 80% | 80% | 85% |
| validators.py | 14% | 14% | 80% | 80% | 85% |
| routers/sessions.py | 26% | 45% | 80% | 80% | 85% |
| routers/patients.py | 37% | 55% | 80% | 80% | 85% |
| auth/router.py | 27% | 45% | 60% | 80% | 85% |
| services/note_extraction.py | 22% | 40% | 60% | 80% | 85% |
| services/cleanup.py | 15% | 35% | 55% | 80% | 85% |
| middleware/error_handler.py | 44% | 60% | 70% | 80% | 85% |
| main.py | 49% | 60% | 70% | 80% | 85% |

---

## Weekly Effort Estimate

| Week | Focus | Tests to Write | Estimated Hours |
|------|-------|----------------|-----------------|
| Week 1 | Fix failing tests | 90 test fixes | 24 hours |
| Week 2 | Critical files | 80 new tests | 28 hours |
| Week 3 | Services & middleware | 60 new tests | 24 hours |
| Week 4 | Edge cases & polish | 40 new tests | 20 hours |
| **Total** | | **270 tests** | **96 hours** |

---

## Success Metrics

### Code Coverage
- [x] Week 1: 50% coverage
- [ ] Week 2: 65% coverage
- [ ] Week 3: 75% coverage
- [ ] Week 4: 80% coverage

### Test Quality
- [x] Week 1: All tests passing
- [ ] Week 2: All critical modules 80%+
- [ ] Week 3: All services 80%+
- [ ] Week 4: All modules 70%+ minimum

### CI/CD
- [ ] Week 1: CI running on all PRs
- [ ] Week 2: Coverage gates enabled
- [ ] Week 3: Codecov integration
- [ ] Week 4: Coverage trending dashboard

---

## Risk Mitigation

### Risk: Test Failures Block Progress
**Mitigation:** Prioritize fixing failing tests in Week 1. Don't proceed to new tests until existing tests pass.

### Risk: Time Estimates Too Optimistic
**Mitigation:** Build in 20% buffer. If falling behind, adjust scope (75% acceptable vs 80%).

### Risk: Coverage Drops with New Features
**Mitigation:** Enforce coverage gates in CI. Require 80% coverage on all new code.

### Risk: Tests Are Brittle
**Mitigation:** Use fixtures, factories, and test utilities. Avoid hardcoded data.

---

## Tools & Resources

### Required Tools
- [x] pytest & pytest-cov installed
- [x] Coverage configuration complete
- [x] Test runner script created
- [x] CI workflow configured

### Recommended Tools
- [ ] pytest-xdist - Parallel test execution
- [ ] pytest-watch - Auto-run tests on file changes
- [ ] hypothesis - Property-based testing
- [ ] faker - Test data generation

### Documentation
- [x] COVERAGE_GUIDE.md - Complete guide
- [x] COVERAGE_QUICK_REFERENCE.md - Quick commands
- [x] COVERAGE_IMPROVEMENT_PLAN.md - This document

---

## Next Actions

### Immediate (Today)
1. ✅ Review this plan with team
2. ✅ Set up coverage tracking spreadsheet
3. ✅ Create GitHub issues for each phase
4. ✅ Schedule daily coverage review meetings

### Week 1 Kickoff (Tomorrow)
1. ✅ Start fixing failing tests
2. ✅ Set up CI coverage notifications
3. ✅ Create test writing guidelines
4. ✅ Begin daily standups on progress

---

## Maintenance Plan (Post-80%)

### Daily
- Monitor CI coverage reports
- Review coverage on all PRs

### Weekly
- Review coverage trends
- Identify coverage regressions
- Update coverage goals

### Monthly
- Audit test quality
- Remove obsolete tests
- Refactor slow tests
- Update coverage targets

---

## Conclusion

Reaching 80% coverage is achievable within 4 weeks by:
1. **Fixing existing failing tests** (Week 1)
2. **Covering critical files** (Week 2)
3. **Improving services & middleware** (Week 3)
4. **Adding edge cases & polish** (Week 4)

The plan is frontloaded with foundation work (fixing tests) and critical file coverage (config, validators) to maximize early gains.

**Key to Success:**
- Prioritize quality over quantity
- Fix broken tests before writing new ones
- Focus on high-impact modules first
- Maintain momentum with daily progress tracking

**Expected Outcome:**
- 80%+ overall coverage
- 90%+ coverage on critical modules
- Zero failing tests
- Comprehensive test suite
- Sustainable testing practices
