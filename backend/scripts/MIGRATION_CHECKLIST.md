# Goal Migration Pre-Flight Checklist

Before running the migration in production, verify these items:

## Prerequisites ✓

- [ ] **Alembic migrations applied**
  ```bash
  cd backend
  alembic current  # Should show: d5e6f7g8h9i0
  ```

- [ ] **treatment_goals table exists**
  ```sql
  SELECT EXISTS (
    SELECT FROM information_schema.tables
    WHERE table_name = 'treatment_goals'
  );
  ```

- [ ] **Virtual environment activated**
  ```bash
  source venv/bin/activate
  python --version  # Should be 3.13
  ```

- [ ] **Database backup created** (recommended)
  ```bash
  python scripts/backup_database.py
  ```

## Pre-Migration Validation ✓

- [ ] **Check data exists**
  ```sql
  SELECT COUNT(*)
  FROM therapy_sessions
  WHERE extracted_notes->'action_items' IS NOT NULL;
  ```

- [ ] **Verify foreign key relationships**
  ```sql
  -- All sessions have valid patient_id
  SELECT COUNT(*)
  FROM therapy_sessions
  WHERE patient_id IS NULL
    AND extracted_notes->'action_items' IS NOT NULL;
  -- Should return 0

  -- All sessions have valid therapist_id
  SELECT COUNT(*)
  FROM therapy_sessions
  WHERE therapist_id IS NULL
    AND extracted_notes->'action_items' IS NOT NULL;
  -- Should return 0
  ```

- [ ] **Sample action_items structure**
  ```sql
  SELECT
    id,
    extracted_notes->'action_items' as action_items
  FROM therapy_sessions
  WHERE extracted_notes->'action_items' IS NOT NULL
  LIMIT 3;
  ```

## Dry Run Testing ✓

- [ ] **Run dry-run with verbose output**
  ```bash
  python scripts/migrate_goals_from_jsonb.py --dry-run --verbose
  ```

- [ ] **Review dry-run summary**
  - Sessions Processed > 0
  - Goals Created count reasonable
  - No unexpected errors
  - Duplicate detection working

- [ ] **Verify no database changes made**
  ```sql
  SELECT COUNT(*) FROM treatment_goals;
  -- Should be 0 (or previous count if re-running)
  ```

## Migration Execution ✓

- [ ] **Run actual migration**
  ```bash
  python scripts/migrate_goals_from_jsonb.py --verbose
  ```

- [ ] **Monitor output for errors**
  - No "❌" error symbols
  - Progress reports every 10 sessions
  - Final summary shows "✅ Migration completed successfully"

- [ ] **Verify exit code**
  ```bash
  echo $?
  # Should be 0 (success)
  ```

## Post-Migration Verification ✓

- [ ] **Count migrated goals**
  ```sql
  SELECT COUNT(*) FROM treatment_goals;
  ```

- [ ] **Compare counts**
  ```sql
  -- Total action_items in JSONB
  SELECT
    COUNT(*) as sessions_with_items,
    SUM(jsonb_array_length(extracted_notes->'action_items')) as total_action_items
  FROM therapy_sessions
  WHERE extracted_notes->'action_items' IS NOT NULL;

  -- Migrated goals
  SELECT COUNT(*) as migrated_goals FROM treatment_goals;

  -- Difference should match "Skipped (Duplicate)" + "Skipped (Invalid)" from summary
  ```

- [ ] **Verify data integrity**
  ```sql
  -- All goals have valid patient_id
  SELECT COUNT(*)
  FROM treatment_goals g
  LEFT JOIN users u ON g.patient_id = u.id
  WHERE u.id IS NULL;
  -- Should return 0

  -- All goals have valid therapist_id
  SELECT COUNT(*)
  FROM treatment_goals g
  LEFT JOIN users u ON g.therapist_id = u.id
  WHERE u.id IS NULL;
  -- Should return 0

  -- All goals have valid session_id (if not null)
  SELECT COUNT(*)
  FROM treatment_goals g
  LEFT JOIN therapy_sessions s ON g.session_id = s.id
  WHERE g.session_id IS NOT NULL AND s.id IS NULL;
  -- Should return 0
  ```

- [ ] **Spot-check sample goals**
  ```sql
  SELECT
    g.id,
    g.description,
    g.category,
    g.status,
    g.created_at,
    s.session_date,
    u.email as patient_email
  FROM treatment_goals g
  JOIN therapy_sessions s ON g.session_id = s.id
  JOIN users u ON g.patient_id = u.id
  ORDER BY g.created_at DESC
  LIMIT 5;
  ```

- [ ] **Verify no duplicates created**
  ```sql
  SELECT
    patient_id,
    description,
    COUNT(*) as duplicate_count
  FROM treatment_goals
  GROUP BY patient_id, description
  HAVING COUNT(*) > 1;
  -- Should return 0 rows
  ```

## Rollback (If Needed) ✓

Only use if migration fails or creates incorrect data:

```sql
-- Preview what will be deleted
SELECT COUNT(*)
FROM treatment_goals
WHERE session_id IS NOT NULL;

-- Delete migrated goals (ones with session_id link)
-- DELETE FROM treatment_goals WHERE session_id IS NOT NULL;

-- Verify deletion
SELECT COUNT(*) FROM treatment_goals;
```

## Sign-Off

- [ ] **Database Engineer:** Migration script tested and working ✅
- [ ] **API Engineer:** Endpoints work with migrated data
- [ ] **Frontend Engineer:** UI displays migrated goals correctly
- [ ] **QA Engineer:** Data integrity validated

## Notes

**Migration Date:** ________________

**Executed By:** ________________

**Rows Migrated:** ________________

**Issues Encountered:** ________________

**Resolution:** ________________

---

**Script Location:** `/backend/scripts/migrate_goals_from_jsonb.py`
**Documentation:** `/backend/scripts/MIGRATION_README.md`
**Report:** `/backend/scripts/WAVE1_DB_ENGINEER_REPORT.md`
