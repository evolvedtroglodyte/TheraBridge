# Scripts Test Directory

This directory contains tests for migration scripts and database utilities.

## Test Files

### test_migrate_goals.py
Comprehensive test suite for the goals migration script that backfills `treatment_goals` table from legacy JSONB data.

**Coverage**: 25 test cases covering:
- Empty database scenarios
- Valid data migration
- Idempotency (duplicate prevention)
- Edge cases (NULL values, malformed data)
- Dry-run mode
- Bulk operations
- Error handling
- Data integrity

**See**: `TEST_REPORT.md` for detailed test documentation

## Running Tests

### All script tests
```bash
pytest tests/scripts/ -v
```

### Specific test file
```bash
pytest tests/scripts/test_migrate_goals.py -v
```

### With coverage
```bash
pytest tests/scripts/test_migrate_goals.py --cov=scripts --cov-report=html
```

### Specific test category
```bash
pytest tests/scripts/test_migrate_goals.py -k "idempotency" -v
pytest tests/scripts/test_migrate_goals.py -k "dry_run" -v
pytest tests/scripts/test_migrate_goals.py -k "edge" -v
```

## Test Markers

All tests in this directory use the `@pytest.mark.migration` marker.

Run only migration tests:
```bash
pytest -m migration -v
```

## Adding New Script Tests

1. Create test file: `test_<script_name>.py`
2. Add fixtures for test data
3. Create helper functions for common operations
4. Write test cases following existing patterns
5. Update this README

## Test Patterns

### Standard Test Structure
```python
def test_operation_scenario(test_db, fixtures):
    """
    Test description.
    Expected: behavior description.
    """
    # Arrange - setup test data
    initial_state = get_initial_state(test_db)

    # Act - run operation
    result = run_operation(test_db)

    # Assert - verify results
    assert result == expected_result
    assert_database_state(test_db, expected_state)
```

### Fixture Pattern
```python
@pytest.fixture(scope="function")
def test_data(test_db, dependencies):
    """Create test data with dependencies."""
    data = create_test_data(dependencies)
    test_db.add(data)
    test_db.commit()
    test_db.refresh(data)
    return data
```

### Helper Function Pattern
```python
def run_migration(db: Session, dry_run: bool = False):
    """Helper to run migration with consistent error handling."""
    try:
        from scripts.migrate_module import migrate
    except ImportError:
        pytest.skip("Migration script not found")
    return migrate(db, dry_run=dry_run)
```

## Database Testing Best Practices

1. **Use function-scoped fixtures** - Each test gets fresh database
2. **Commit fixture data** - Ensure data is visible to queries
3. **Refresh objects** - Reload objects after commits
4. **Clean up** - test_db fixture handles cleanup automatically
5. **Test transactions** - Verify rollback behavior
6. **Check foreign keys** - Validate relationships load correctly
7. **Test NULL handling** - Edge cases with missing data
8. **Validate timestamps** - Ensure created_at/updated_at set correctly

## Coverage Goals

- **Line Coverage**: > 90%
- **Branch Coverage**: > 85%
- **Function Coverage**: 100%

## Debugging Failed Tests

### View detailed output
```bash
pytest tests/scripts/test_migrate_goals.py -v -s
```

### Stop on first failure
```bash
pytest tests/scripts/test_migrate_goals.py -x
```

### Run specific test
```bash
pytest tests/scripts/test_migrate_goals.py::test_migration_field_mapping -v
```

### Debug with pdb
```bash
pytest tests/scripts/test_migrate_goals.py --pdb
```

## Migration Script Implementation Checklist

When implementing a new migration script:

- [ ] Create script in `backend/scripts/`
- [ ] Implement main migration function
- [ ] Add dry-run mode support
- [ ] Return statistics dictionary
- [ ] Handle errors gracefully
- [ ] Use transactions for atomicity
- [ ] Add logging
- [ ] Create tests in this directory
- [ ] Achieve > 90% coverage
- [ ] Test on staging database
- [ ] Document in script docstring

## Resources

- **SQLAlchemy Docs**: https://docs.sqlalchemy.org/
- **Pytest Docs**: https://docs.pytest.org/
- **Database Models**: `backend/app/models/`
- **Existing Tests**: `backend/tests/`
- **Fixtures**: `backend/tests/conftest.py`
