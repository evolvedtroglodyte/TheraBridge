# Services Tests

## Note Extraction Service Tests

### Quick Start
```bash
# Run all tests
pytest tests/services/test_note_extraction.py -v

# Run with coverage
pytest tests/services/test_note_extraction.py --cov=app/services/note_extraction --cov-report=term-missing
```

### Test Structure
- **Location**: `test_note_extraction.py` (767 lines)
- **Tests**: 26 comprehensive unit tests
- **Coverage**: 98.61% of note_extraction.py

### Test Categories
1. **Initialization** (5 tests) - API key, timeouts, error handling
2. **Successful Extraction** (3 tests) - Valid responses, markdown stripping
3. **API Errors** (4 tests) - Rate limits, timeouts, generic errors
4. **JSON Parsing** (2 tests) - Invalid JSON, decode errors
5. **Validation** (3 tests) - Missing fields, invalid enums, nested objects
6. **Cost Estimation** (5 tests) - Various transcript sizes
7. **Edge Cases** (4 tests) - Empty lists, API params, zero-length input

### Key Features Tested
✅ AsyncOpenAI client initialization with custom timeouts  
✅ Comprehensive error handling (RateLimitError, APITimeoutError, APIError)  
✅ JSON parsing with error position reporting  
✅ Pydantic validation for ExtractedNotes schema  
✅ Cost estimation with GPT-4o pricing  
✅ Markdown code block stripping  
✅ Empty optional fields handling  

### Mock Strategy
- Uses `unittest.mock.AsyncMock` for OpenAI client
- Fixtures for common test data (`mock_openai_response`)
- Proper error construction with required OpenAI v1.0+ parameters

### Files
- `test_note_extraction.py` - Main test suite
- `TEST_COVERAGE_SUMMARY.md` - Detailed coverage report
- `README.md` - This file

---
**Status**: ✅ All tests passing | 98.61% coverage achieved
