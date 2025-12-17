# Load Testing Quick Start Guide

Get started with performance testing in 5 minutes.

## Step 1: Install Dependencies

```bash
cd backend
pip install locust pytest-xdist psutil
```

## Step 2: Start Backend Server

```bash
# Terminal 1: Start backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

## Step 3: Create Test User (First Time Only)

```bash
# Terminal 2: Create test user
cd backend
source venv/bin/activate

# Run any test that creates users or manually create via API
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123!",
    "full_name": "Test User",
    "role": "therapist"
  }'
```

## Step 4: Run Your First Load Test

### Option A: Quick Baseline (No Authentication)

```bash
# Fastest way to test - no auth required
pytest tests/performance/baseline_test.py -v -s
```

Expected output:
```
BASELINE HEALTH CHECK PERFORMANCE
====================================================
Requests: 20
Average: 45.23ms
Min: 32.10ms
Max: 89.45ms
P95: 67.80ms
====================================================
```

### Option B: Locust Web UI (Interactive)

```bash
# Start locust with web interface
locust -f tests/performance/load_test.py --host=http://localhost:8000

# Open browser to http://localhost:8089
# Set users: 10
# Set spawn rate: 2
# Click "Start"
```

### Option C: Automated Pytest Tests

```bash
# Run all load tests with 10 concurrent workers
pytest tests/performance/pytest_load_test.py -n 10 -v -s
```

## Step 5: Review Results

Results are saved to `tests/performance/results/`:

```bash
# View latest results
ls -lt tests/performance/results/ | head -5

# View specific result
cat tests/performance/results/baseline_report_20241217_120530.json
```

## Common Test Scenarios

### 1. Rate Limit Testing

```bash
# Verify rate limits are enforced
pytest tests/performance/pytest_load_test.py::test_rate_limit_enforcement -v
```

### 2. Database Connection Pool

```bash
# Test with high concurrency
pytest tests/performance/pytest_load_test.py::test_database_pool_stress -n 50 -v
```

### 3. Upload Performance

```bash
# Test concurrent uploads
pytest tests/performance/pytest_load_test.py::test_concurrent_uploads -n 10 -v
```

### 4. Sustained Load

```bash
# 5-minute moderate load
./tests/performance/run_load_tests.sh moderate
```

## Troubleshooting

### Backend not running
```
ERROR: Connection refused
```
**Fix:** Start backend with `uvicorn app.main:app --reload`

### Authentication failed
```
ERROR: 401 Unauthorized
```
**Fix:** Create test user (see Step 3)

### Rate limit errors (429)
```
Many 429 responses
```
**Fix:** This is expected! It means rate limiting is working.

### Database pool errors
```
QueuePool limit exceeded
```
**Fix:** Increase pool size in `app/database.py`

## Next Steps

- Review full documentation in `README.md`
- Adjust test parameters for your environment
- Set up CI/CD integration (see README.md)
- Run extended load tests before deployment

## Performance Targets

| Metric | Target | Your Result |
|--------|--------|-------------|
| Health check P95 | <100ms | _____ |
| Session list P95 | <500ms | _____ |
| Upload P95 | <5s | _____ |
| Requests/sec | >100 | _____ |
| Error rate | <1% | _____ |

Fill in your results after running tests!
