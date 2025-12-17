# Performance Testing for TherapyBridge Backend

Comprehensive load testing scripts to measure backend performance under concurrent load.

## Overview

This directory contains two complementary load testing approaches:

1. **Locust-based testing** (`load_test.py`) - Interactive, web-based load testing
2. **Pytest-based testing** (`pytest_load_test.py`) - Programmatic, CI/CD-friendly testing

## Prerequisites

```bash
# Install dependencies
pip install locust pytest-xdist httpx psutil pytest-asyncio
```

## Test Scenarios

### 1. Locust Load Tests (Recommended for Interactive Testing)

**Features:**
- Real-time web UI for monitoring
- Adjustable user count and spawn rate
- Distributed testing support
- Performance graphs and statistics

**Usage:**

```bash
# Web UI mode (recommended for initial testing)
locust -f tests/performance/load_test.py --host=http://localhost:8000

# Then open http://localhost:8089 in browser
# Configure users, spawn rate, and start test

# Headless mode (for automation)
locust -f tests/performance/load_test.py --host=http://localhost:8000 \
       --users 50 --spawn-rate 5 --run-time 5m --headless

# Test specific scenario using tags
locust -f tests/performance/load_test.py --host=http://localhost:8000 \
       --tags upload --users 10 --spawn-rate 2 --headless

# Available tags:
# - read: Read-heavy operations
# - write: Write operations (uploads, updates)
# - upload: Upload endpoints
# - extract: Note extraction endpoints
# - health: Health check endpoints
# - rate_limit: Rate limiting tests
# - db_pool: Database pool stress tests
```

**Test Users:**

- `TherapyBridgeUser`: Simulates realistic user behavior with think time
- `RateLimitTestUser`: Rapid-fire requests to test rate limiting
- `DatabaseConnectionPoolUser`: Database-heavy operations

### 2. Pytest Load Tests (Recommended for CI/CD)

**Features:**
- Programmatic test execution
- Detailed performance metrics in JSON
- Easy integration with CI/CD pipelines
- Parallel execution with pytest-xdist

**Usage:**

```bash
# Run all tests with 10 concurrent workers
pytest tests/performance/pytest_load_test.py -n 10 -v

# Run specific test
pytest tests/performance/pytest_load_test.py::test_concurrent_sessions -n 20 -v

# Run with detailed output
pytest tests/performance/pytest_load_test.py -n 10 -v -s

# Run specific categories
pytest tests/performance/pytest_load_test.py -k "concurrent" -n 10 -v
pytest tests/performance/pytest_load_test.py -k "rate_limit" -v
```

**Available Tests:**

1. `test_concurrent_health_checks` - Baseline throughput (100 requests)
2. `test_concurrent_sessions` - Read-heavy load (50 concurrent requests)
3. `test_concurrent_uploads` - Upload stress test (10 concurrent)
4. `test_rate_limit_enforcement` - Verify rate limits work (150 rapid requests)
5. `test_database_pool_stress` - Connection pool limits (100 concurrent)
6. `test_sustained_load` - 500 requests over 60 seconds
7. `test_memory_leak_detection` - Monitor memory during 200 requests

## Performance Metrics Collected

Both testing approaches collect:

- **Latency metrics:**
  - Average response time
  - Min/Max response time
  - P50, P95, P99 percentiles

- **Throughput:**
  - Requests per second (RPS)
  - Total requests completed
  - Error rate percentage

- **Resource usage:**
  - Memory consumption (initial, peak, growth)
  - CPU utilization
  - Database connection pool status

- **Error tracking:**
  - Status code distribution
  - Error details and timestamps

## Results

Performance metrics are saved to `tests/performance/results/` as JSON files:

```
tests/performance/results/
├── concurrent_sessions_20241217_120530.json
├── rate_limit_enforcement_20241217_120645.json
├── metrics_20241217_120800.json
└── ...
```

Each result file contains:
- Test configuration
- Performance metrics (latency, throughput)
- Error details
- Resource usage statistics

## Baseline Performance Expectations

Based on typical FastAPI + PostgreSQL performance:

| Metric | Target | Warning | Critical |
|--------|--------|---------|----------|
| Health check P95 | <100ms | <500ms | >1s |
| Session list P95 | <500ms | <2s | >5s |
| Upload P95 | <5s | <10s | >20s |
| Requests/sec | >100 | >50 | <50 |
| Error rate | <1% | <5% | >10% |

## Pre-Test Checklist

1. **Start the backend server:**
   ```bash
   cd backend
   source venv/bin/activate
   uvicorn app.main:app --reload
   ```

2. **Ensure test user exists:**
   - Email: `test@example.com`
   - Password: `TestPass123!`
   - Role: `therapist`

3. **Create test data (optional):**
   ```bash
   # Run this to create sample patients and sessions
   pytest tests/test_auth_integration.py::test_register_therapist
   ```

4. **Check database connection pool settings:**
   - Pool size: 5-20 connections (adjust in `app/database.py`)
   - Max overflow: 10 (adjust based on expected load)

5. **Monitor system resources:**
   ```bash
   # In separate terminal
   htop  # or top on macOS
   ```

## Load Testing Best Practices

### 1. Start Small, Scale Up

```bash
# Start with low load
locust -f tests/performance/load_test.py --host=http://localhost:8000 \
       --users 5 --spawn-rate 1 --run-time 2m --headless

# Gradually increase
locust -f tests/performance/load_test.py --host=http://localhost:8000 \
       --users 20 --spawn-rate 2 --run-time 5m --headless

# Full load test
locust -f tests/performance/load_test.py --host=http://localhost:8000 \
       --users 100 --spawn-rate 10 --run-time 10m --headless
```

### 2. Test Rate Limiting

```bash
# Rapid requests to verify rate limiting
pytest tests/performance/pytest_load_test.py::test_rate_limit_enforcement -v
```

Expected behavior:
- Initial requests succeed (200)
- After limit (100/min), receive 429 Too Many Requests
- Retry-After header present in 429 responses

### 3. Database Connection Pool

```bash
# Test with high concurrency
pytest tests/performance/pytest_load_test.py::test_database_pool_stress -n 50 -v
```

Watch for errors like:
- "QueuePool limit exceeded"
- "Connection timeout"
- Database connection errors

If errors occur, increase pool size in `app/database.py`.

### 4. Memory Leak Detection

```bash
# Run sustained load while monitoring memory
pytest tests/performance/pytest_load_test.py::test_memory_leak_detection -v -s
```

Look for:
- Steady memory growth over time
- Memory not released after requests complete
- Memory growth exceeding 50MB for 200 requests

## Troubleshooting

### Issue: High error rate (>10%)

**Possible causes:**
- Database connection pool exhausted
- API rate limits too aggressive
- Server resource constraints

**Solutions:**
1. Increase database pool size
2. Adjust rate limits in `app/middleware/rate_limit.py`
3. Scale server resources (CPU, memory)
4. Check application logs for errors

### Issue: High latency (P95 >2s for reads)

**Possible causes:**
- Database query performance
- Insufficient server resources
- Network latency

**Solutions:**
1. Add database indexes on frequently queried columns
2. Enable query logging and analyze slow queries
3. Increase server CPU/memory
4. Check database connection latency

### Issue: Rate limits not enforced

**Verification:**
```bash
pytest tests/performance/pytest_load_test.py::test_rate_limit_enforcement -v
```

**Solutions:**
1. Verify rate limiter is registered in `app/main.py`
2. Check endpoints have `@limiter.limit()` decorator
3. Verify `Request` parameter in endpoint signatures

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Performance Tests

on:
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM

jobs:
  performance:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: testpass
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r backend/requirements.txt
          pip install locust pytest-xdist httpx psutil

      - name: Run backend
        run: |
          cd backend
          uvicorn app.main:app &
          sleep 10

      - name: Run performance tests
        run: |
          cd backend
          pytest tests/performance/pytest_load_test.py -n 10 -v

      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: performance-results
          path: backend/tests/performance/results/
```

## Recommended Testing Schedule

1. **Pre-deployment**: Run `pytest_load_test.py` with moderate concurrency
2. **Post-deployment**: Run locust with gradual ramp-up
3. **Daily**: Automated pytest runs in CI/CD
4. **Weekly**: Full load test with 100+ concurrent users
5. **Pre-release**: Extended sustained load test (1+ hour)

## Advanced Scenarios

### Distributed Load Testing

For testing with >1000 users, use Locust in distributed mode:

```bash
# Master node
locust -f tests/performance/load_test.py --host=http://localhost:8000 \
       --master --expect-workers=3

# Worker nodes (run on separate machines)
locust -f tests/performance/load_test.py --worker --master-host=<master-ip>
```

### Custom Scenarios

Edit `load_test.py` to add custom scenarios:

```python
@task(5)
@tag("custom")
def my_custom_scenario(self):
    """Custom test scenario."""
    # Your test logic here
    pass
```

Run with: `locust -f tests/performance/load_test.py --tags custom`

## Additional Resources

- [Locust Documentation](https://docs.locust.io/)
- [pytest-xdist Documentation](https://pytest-xdist.readthedocs.io/)
- [FastAPI Performance Tips](https://fastapi.tiangolo.com/deployment/concepts/)
- [PostgreSQL Performance Tuning](https://wiki.postgresql.org/wiki/Performance_Optimization)

## Support

For issues or questions:
1. Check backend logs: `backend/logs/app.log`
2. Review performance results in `tests/performance/results/`
3. Monitor system resources with `htop` or `top`
4. Check database logs for query performance
