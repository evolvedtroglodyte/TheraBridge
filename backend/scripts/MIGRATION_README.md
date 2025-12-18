# Treatment Goals Migration Guide

## Overview

This document describes the data migration process for Feature 6 Goal Tracking. The migration backfills the `treatment_goals` table from JSONB `action_items` stored in `therapy_sessions.extracted_notes`.

## Migration Script

**Location:** `backend/scripts/migrate_goals_from_jsonb.py`

**Purpose:** Migrate historical action items from JSONB to structured relational table

## Prerequisites

1. **Database schema is up to date:**
   ```bash
   cd backend
   alembic upgrade head
   ```

2. **Environment configured:**
   - `.env` file exists with `DATABASE_URL`
   - Database connection is accessible

3. **Backup recommended:**
   ```bash
   python scripts/backup_database.py
   ```

## Usage

### Dry Run (Recommended First Step)

Preview what the migration will do without making changes:

```bash
cd backend
python scripts/migrate_goals_from_jsonb.py --dry-run --verbose
```

### Execute Migration

Run the actual migration:

```bash
python scripts/migrate_goals_from_jsonb.py
```

### With Verbose Output

See detailed progress for each session and goal:

```bash
python scripts/migrate_goals_from_jsonb.py --verbose
```

## What the Script Does

1. **Queries therapy sessions** with `extracted_notes.action_items`
2. **For each action_item:**
   - Extracts: `task`, `category`, `details`
   - Maps to TreatmentGoal:
     - `task` → `description`
     - `category` → `category`
     - Status set to `'assigned'`
   - Links to `session_id`, `patient_id`, `therapist_id`
   - Uses session date as goal `created_at`

3. **Handles edge cases:**
   - Skips empty/invalid action items
   - Checks for duplicate goals (same description + patient)
   - Uses transaction per session for rollback safety

4. **Progress logging:**
   - Reports every 10 sessions
   - Shows final statistics

## Migration Data Mapping

### Source (JSONB)
```json
{
  "action_items": [
    {
      "task": "Practice deep breathing twice daily",
      "category": "behavioral",
      "details": "Use 4-7-8 technique for 5 minutes"
    }
  ]
}
```

### Destination (Relational)
```sql
INSERT INTO treatment_goals (
  patient_id,           -- From therapy_sessions.patient_id
  therapist_id,         -- From therapy_sessions.therapist_id
  session_id,           -- From therapy_sessions.id
  description,          -- "Practice deep breathing twice daily - Use 4-7-8 technique for 5 minutes"
  category,             -- "behavioral"
  status,               -- "assigned"
  created_at            -- From therapy_sessions.session_date
)
```

## Safety Features

### Idempotency
- Can be run multiple times safely
- Duplicate detection prevents duplicate goals
- Transaction-per-session ensures partial success

### Rollback on Error
- Each session processed in its own transaction
- If session fails, only that session is rolled back
- Other sessions continue processing

### Validation
- Skips action items with missing `task` field
- Handles null/missing `extracted_notes`
- Logs all errors without crashing

## Expected Output

### Dry Run Example
```
======================================================================
STARTING GOAL MIGRATION FROM JSONB ACTION_ITEMS
======================================================================
🔍 DRY RUN MODE - No database changes will be made
Batch Size: 50
Verbose Mode: True

Found 42 sessions with extracted_notes.action_items

  Processing Session a1b2c3d4-e5f6-7890-abcd-ef1234567890
  Date: 2024-11-15 14:30:00
  Patient ID: f1e2d3c4-b5a6-7890-1234-567890abcdef
  Action Items Found: 3

  Action Item 1/3:
    [DRY RUN] Would create goal: [behavioral] Practice deep breathing...

⏳ Progress: 10/42 sessions processed...
⏳ Progress: 20/42 sessions processed...
...

✅ Migration completed successfully!

======================================================================
GOAL MIGRATION SUMMARY
======================================================================
Execution Time: 3.42 seconds
Sessions Processed: 42
Sessions with Action Items: 42
Goals Created: 127
Goals Skipped (Duplicate): 8
Goals Skipped (Invalid): 2
Errors Encountered: 0
======================================================================
```

### Actual Migration Example
```
======================================================================
STARTING GOAL MIGRATION FROM JSONB ACTION_ITEMS
======================================================================
Batch Size: 50
Verbose Mode: False

Found 42 sessions with extracted_notes.action_items

⏳ Progress: 10/42 sessions processed...
⏳ Progress: 20/42 sessions processed...
⏳ Progress: 30/42 sessions processed...
⏳ Progress: 40/42 sessions processed...

✅ Migration completed successfully!

======================================================================
GOAL MIGRATION SUMMARY
======================================================================
Execution Time: 2.87 seconds
Sessions Processed: 42
Sessions with Action Items: 42
Goals Created: 127
Goals Skipped (Duplicate): 8
Goals Skipped (Invalid): 2
Errors Encountered: 0
======================================================================
```

## Troubleshooting

### Error: "DATABASE_URL not found in environment"
**Solution:** Ensure `.env` file exists in `backend/` directory with valid `DATABASE_URL`

### Error: "relation 'treatment_goals' does not exist"
**Solution:** Run Alembic migrations first:
```bash
alembic upgrade head
```

### Error: "asyncpg.exceptions.ForeignKeyViolationError"
**Solution:** Data integrity issue. Check that:
- Referenced `patient_id` exists in `users` table
- Referenced `therapist_id` exists in `users` table
- Referenced `session_id` exists in `therapy_sessions` table

### Migration creates duplicates
**Solution:** The script has duplicate detection. If duplicates exist:
1. Check the `description` field differs (script uses exact match)
2. Run with `--verbose` to see which goals are being skipped

## Verification Queries

After migration, verify success:

### Count migrated goals
```sql
SELECT COUNT(*) FROM treatment_goals;
```

### Compare counts
```sql
-- Count action_items in JSONB
SELECT
  COUNT(*) as sessions_with_items,
  SUM(jsonb_array_length(extracted_notes->'action_items')) as total_items
FROM therapy_sessions
WHERE extracted_notes->'action_items' IS NOT NULL;

-- Count migrated goals
SELECT COUNT(*) FROM treatment_goals;
```

### View sample goals
```sql
SELECT
  id,
  patient_id,
  description,
  category,
  status,
  created_at
FROM treatment_goals
ORDER BY created_at DESC
LIMIT 10;
```

## Rollback (If Needed)

If migration needs to be rolled back:

```sql
-- Delete all migrated goals
DELETE FROM treatment_goals WHERE session_id IS NOT NULL;

-- Verify deletion
SELECT COUNT(*) FROM treatment_goals;
```

## Next Steps

After successful migration:

1. **Verify data integrity** using verification queries above
2. **Test goal endpoints** in Feature 6 API router
3. **Update analytics queries** to use `treatment_goals` instead of JSONB
4. **Deploy to production** after staging validation

## Contact

For issues or questions, contact Database Engineer #1 (Wave 1 team).
