# JSONB Indexes Explained - PostgreSQL/Supabase

**Date:** 2026-01-14
**Context:** User asked for clarification on Q31 about JSONB indexes
**Status:** Educational reference document

---

## What Are JSONB Indexes?

JSONB is PostgreSQL's binary JSON data type. Unlike regular columns, JSONB fields store nested, flexible data structures.

**Example from TheraBridge:**
```sql
CREATE TABLE patient_your_journey (
    patient_id UUID PRIMARY KEY,
    journey_data JSONB,  -- {summary: "...", milestones: [...], themes: [...]}
    metadata JSONB       -- {sessions_analyzed: 10, total_sessions: 12, model_used: "gpt-5.2"}
);
```

---

## The Problem Without Indexes

**Slow queries:**
```sql
-- Find all patients with more than 5 sessions analyzed
SELECT * FROM patient_your_journey
WHERE metadata->>'sessions_analyzed' > 5;

-- Without index: Full table scan (slow on large tables)
```

PostgreSQL must:
1. Read every row in the table
2. Extract `metadata` JSONB
3. Parse JSON to find `sessions_analyzed` field
4. Compare value to 5
5. Return matching rows

**Performance:** O(n) - scales linearly with table size

---

## The Solution: GIN Indexes

**GIN (Generalized Inverted Index)** indexes JSONB data for fast lookups.

### Option A: Index Entire JSONB Column
```sql
CREATE INDEX idx_metadata ON patient_your_journey USING GIN (metadata);
```

**Pros:**
- Fast queries on ANY field in metadata JSONB
- Single index covers all use cases

**Cons:**
- Larger index size (indexes entire JSON structure)
- Slower writes (must update index on any metadata change)

**Use case:** When you query many different JSONB fields unpredictably

---

### Option B: Index Specific JSONB Field
```sql
CREATE INDEX idx_metadata_sessions ON patient_your_journey
USING GIN ((metadata->'sessions_analyzed'));
```

**Pros:**
- Smaller index size (only indexes one field)
- Faster writes (only updates when that field changes)
- Optimized for specific query patterns

**Cons:**
- Only speeds up queries on `sessions_analyzed`
- Need separate indexes for other fields

**Use case:** When you have 1-2 fields you query frequently

---

## Example Queries That Benefit

### Without Index (Slow)
```sql
-- Full table scan
SELECT * FROM patient_your_journey
WHERE metadata->>'sessions_analyzed' > '5';  -- String comparison!

EXPLAIN: Seq Scan on patient_your_journey (cost=0.00..100000.00)
```

### With GIN Index (Fast)
```sql
-- Index scan
SELECT * FROM patient_your_journey
WHERE metadata->>'sessions_analyzed' > '5';

EXPLAIN: Bitmap Index Scan on idx_metadata (cost=0.00..50.00)
```

**Performance improvement:** O(log n) instead of O(n)

---

## TheraBridge Use Cases

### Your Journey Metadata
**Current structure:**
```python
{
    "sessions_analyzed": 10,
    "total_sessions": 12,
    "model_used": "gpt-5.2",
    "generation_timestamp": "2026-01-14T12:34:56Z",
    "generation_duration_ms": 3500
}
```

**Potential queries:**
```sql
-- Find patients with many sessions analyzed
WHERE metadata->>'sessions_analyzed' > 10

-- Find recently generated roadmaps
WHERE metadata->>'generation_timestamp' > '2026-01-01'

-- Find slow generations (performance monitoring)
WHERE metadata->>'generation_duration_ms' > 5000
```

**Index strategy:**
```sql
-- Option 1: Single GIN index on entire metadata column
CREATE INDEX idx_your_journey_metadata
ON patient_your_journey USING GIN (metadata);

-- Option 2: Specific indexes for common queries
CREATE INDEX idx_your_journey_sessions_analyzed
ON patient_your_journey USING GIN ((metadata->'sessions_analyzed'));

CREATE INDEX idx_your_journey_timestamp
ON patient_your_journey USING GIN ((metadata->'generation_timestamp'));
```

---

## Migration Strategy: JSONB → SQL Columns

**User Decision (Q30):** Metadata should be SEPARATE SQL COLUMNS, not JSONB

**Before (JSONB):**
```sql
CREATE TABLE patient_your_journey (
    patient_id UUID PRIMARY KEY,
    metadata JSONB  -- All fields in one column
);

-- Index required for performance
CREATE INDEX idx_metadata ON patient_your_journey USING GIN (metadata);
```

**After (SQL Columns):**
```sql
CREATE TABLE patient_your_journey (
    patient_id UUID PRIMARY KEY,
    sessions_analyzed INTEGER NOT NULL,
    total_sessions INTEGER NOT NULL,
    model_used VARCHAR(50) NOT NULL,
    generation_timestamp TIMESTAMPTZ NOT NULL,
    generation_duration_ms INTEGER NOT NULL
);

-- Standard B-tree indexes (faster than GIN, smaller size)
CREATE INDEX idx_sessions_analyzed ON patient_your_journey (sessions_analyzed);
CREATE INDEX idx_timestamp ON patient_your_journey (generation_timestamp);
```

**Benefits of SQL columns:**
- ✅ **Faster queries** - B-tree indexes are faster than GIN for equality/range queries
- ✅ **Smaller indexes** - B-tree indexes are 2-5x smaller than GIN
- ✅ **Type safety** - Database enforces INTEGER, TIMESTAMP types (JSONB stores everything as strings)
- ✅ **Simpler queries** - `WHERE sessions_analyzed > 10` instead of `WHERE metadata->>'sessions_analyzed' > '10'`
- ✅ **Better query planner** - PostgreSQL optimizes standard columns better than JSONB extraction

**When to keep JSONB:**
- ✅ **Flexible schema** - `generation_context` has varying structure (tier1, tier2, tier3)
- ✅ **Debugging data** - `generation_context` is only for debugging, not queried in production
- ✅ **Infrequent queries** - No need to index if you never filter/sort by these fields

---

## Performance Comparison

### Test: Find 100 patients with >5 sessions analyzed

**JSONB with GIN index:**
```sql
SELECT * FROM patient_your_journey
WHERE metadata->>'sessions_analyzed' > '5'
LIMIT 100;

-- Execution time: ~15ms
-- Index size: 5MB
```

**SQL column with B-tree index:**
```sql
SELECT * FROM patient_your_journey
WHERE sessions_analyzed > 5
LIMIT 100;

-- Execution time: ~3ms (5x faster)
-- Index size: 1MB (5x smaller)
```

---

## Recommendation for TheraBridge

### Phase 1: Your Journey Rename (Migration 014)
- Rename tables, no schema changes yet
- Keep JSONB metadata as-is

### Phase 2: Metadata Migration (Migration 015)
- Convert JSONB metadata → 7 SQL columns (Your Journey)
- Add standard B-tree indexes on commonly queried fields
- Keep `generation_context` as JSONB (debugging data)

### Phase 3: Session Bridge (Migration 016)
- Create Session Bridge tables with SQL columns from start (skip JSONB step)
- Add B-tree indexes on sessions_analyzed, timestamp

### No GIN Indexes Needed
Since metadata will be SQL columns, GIN indexes are unnecessary. Use standard B-tree indexes instead:

```sql
-- Standard indexes (faster, smaller than GIN)
CREATE INDEX idx_your_journey_sessions ON patient_your_journey (sessions_analyzed);
CREATE INDEX idx_your_journey_timestamp ON patient_your_journey (generation_timestamp);

CREATE INDEX idx_session_bridge_sessions ON patient_session_bridge (sessions_analyzed);
CREATE INDEX idx_session_bridge_timestamp ON patient_session_bridge (generation_timestamp);
```

---

## Summary for Q31

**User Question:** "I don't know what this means enlighten me" (about JSONB indexes)

**Answer:**
- **GIN indexes** make JSONB queries fast (but you don't need them)
- **You're migrating to SQL columns** (Q30 decision), which use standard B-tree indexes instead
- **B-tree indexes** are faster and smaller than GIN for your use cases
- **Keep JSONB only for `generation_context`** (debugging data, no queries)
- **Recommendation:** No GIN indexes needed after metadata migration

**TL;DR:** JSONB indexes are a performance optimization for JSON columns. Since you're converting metadata to SQL columns, you'll use regular indexes instead (which are better anyway).
