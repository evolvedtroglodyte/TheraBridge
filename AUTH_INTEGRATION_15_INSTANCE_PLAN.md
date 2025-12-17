# 🚀 AUTHENTICATION INTEGRATION - 15 INSTANCE PARALLEL EXECUTION PLAN

**Project:** TherapyBridge Authentication System
**Target:** Fix database schema mismatch, implement auth features, create test suite
**Instances:** 15 parallel Claude Code agents
**Total Tasks:** 63 ultra-fine-grained tasks
**Estimated Time:** 18 minutes (vs 90+ minutes sequential)
**Speedup:** 5x faster

---

## 📋 INSTANCE ASSIGNMENTS

| Instance | Role | Primary Focus | Phases |
|----------|------|---------------|--------|
| **0** | COORDINATOR | Orchestration, checkpoints, final docs | 0, 7 |
| **1** | DB-SCHEMA | Database schema export & analysis | 1 |
| **2** | DB-BACKUP | Backup/restore system | 1 |
| **3** | DB-COMPARE | Model comparison & requirements | 1 |
| **4** | MIG-SETUP | Alembic infrastructure | 2, 5 |
| **5** | MIG-AUTHOR | Migration script generation | 2 |
| **6** | MIG-TEST | SQL preview & safety validation | 2 |
| **7** | BE-AUTH | Signup & user creation endpoints | 3 |
| **8** | BE-TOKEN | Token rotation & refresh logic | 3 |
| **9** | BE-SECURITY | Rate limiting & middleware | 3 |
| **10** | BE-PASSWORD | Password reset endpoints | 3 |
| **11** | TEST-INFRA | Test fixtures & configuration | 4, 6 |
| **12** | TEST-AUTH | Authentication integration tests | 4, 6 |
| **13** | TEST-RBAC | RBAC & security tests | 4, 6 |
| **14** | DOCS | Documentation updates | 7 |

---

## 🔄 EXECUTION PHASES

```
PHASE 0: PRE-FLIGHT (2 min) [SEQUENTIAL]
  └─ Instance 0: Safety commit, env check, directories
       ↓
PHASE 1: DISCOVERY (4 min) [PARALLEL - 3 instances]
  ├─ Instance 1: DB schema export (4 tasks)
  ├─ Instance 2: Backup system (4 tasks)
  └─ Instance 3: Model comparison (3 tasks)
       ↓
PHASE 2: INFRASTRUCTURE (5 min) [PARALLEL - 3 instances]
  ├─ Instance 4: Alembic setup (4 tasks)
  ├─ Instance 5: Migration generation (3 tasks)
  └─ Instance 6: Safety validation (3 tasks)
       ↓
PHASE 3: BACKEND DEV (6 min) [PARALLEL - 4 instances]
  ├─ Instance 7: Signup endpoint (4 tasks)
  ├─ Instance 8: Token rotation (3 tasks)
  ├─ Instance 9: Rate limiting (4 tasks)
  └─ Instance 10: Password reset (3 tasks)
       ↓
PHASE 4: TEST CREATION (5 min) [PARALLEL - 3 instances]
  ├─ Instance 11: Test infrastructure (3 tasks)
  ├─ Instance 12: Auth integration tests (4 tasks)
  └─ Instance 13: RBAC tests (3 tasks)
       ↓
PHASE 5: MIGRATION EXEC (3 min) [SEQUENTIAL - CRITICAL]
  └─ Instance 4: Backup verify → Execute → Verify (5 tasks)
       ↓
PHASE 6: VALIDATION (4 min) [PARALLEL - 3 instances]
  ├─ Instance 11: Run pytest tests (2 tasks)
  ├─ Instance 12: Manual API testing (3 tasks)
  └─ Instance 13: Security validation (2 tasks)
       ↓
PHASE 7: CLEANUP (3 min) [PARALLEL - 2 instances]
  ├─ Instance 14: Documentation (4 tasks)
  └─ Instance 0: Final commit & summary (2 tasks)
```

---

# 📝 ULTRA-FINE-GRAINED PROMPTS

## ⚠️ PHASE 0: PRE-FLIGHT SAFETY (SEQUENTIAL)

**Duration:** 2 minutes
**Assigned to:** Instance 0 (COORDINATOR)
**Wait for:** Nothing (starts immediately)

---

### 🔹 PROMPT 0.1: Git Safety Commit

**Instance:** 0 (COORDINATOR)

**Task:** Create safety commit before ANY changes

**Execute:**
```bash
cd "/Users/newdldewdl/Global Domination 2/peerbridge proj"

# Check current status
git status

# Stage ALL files (tracked and untracked)
git add -A

# Create timestamped safety commit
git commit -m "Backup before auth integration [$(date +%Y-%m-%d_%H:%M:%S)]"

# Verify commit created
git log -1 --oneline

# Save commit hash for reference
mkdir -p backend/migrations/analysis
git log -1 --format="%H" > backend/migrations/analysis/phase0_commit_hash.txt

echo "✅ Safety commit created"
cat backend/migrations/analysis/phase0_commit_hash.txt
```

**Output:** `backend/migrations/analysis/phase0_commit_hash.txt`
**Signal:** `PHASE0_GIT_BACKUP_COMPLETE`
**Duration:** 30 seconds

---

### 🔹 PROMPT 0.2: Environment Verification

**Instance:** 0 (COORDINATOR)

**Task:** Verify Python environment and required variables

**Execute:**
```bash
cd "/Users/newdldewdl/Global Domination 2/peerbridge proj/backend"

# Check .env file exists
if [ ! -f .env ]; then
    echo "❌ ERROR: .env file not found"
    exit 1
fi

# Verify required variables
echo "Checking environment variables..."
grep -q "DATABASE_URL" .env || echo "⚠️ WARNING: DATABASE_URL not in .env"
grep -q "JWT_SECRET_KEY" .env || echo "⚠️ WARNING: JWT_SECRET_KEY not in .env"

# Create or verify virtual environment
if [ ! -d venv ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate and check versions
source venv/bin/activate
python --version > migrations/analysis/python_version.txt
pip --version >> migrations/analysis/python_version.txt

echo "✅ Environment verified"
cat migrations/analysis/python_version.txt
```

**Output:** `backend/migrations/analysis/python_version.txt`
**Signal:** `PHASE0_ENV_READY`
**Duration:** 30 seconds

---

### 🔹 PROMPT 0.3: Create Working Directories

**Instance:** 0 (COORDINATOR)

**Task:** Create all necessary directories for migration work

**Execute:**
```bash
cd "/Users/newdldewdl/Global Domination 2/peerbridge proj/backend"

# Create directory structure
mkdir -p migrations/backups
mkdir -p migrations/analysis
mkdir -p scripts
mkdir -p tests/integration
mkdir -p logs
mkdir -p app/middleware

# Create .gitkeep files
touch migrations/.gitkeep
touch migrations/backups/.gitkeep
touch migrations/analysis/.gitkeep
touch logs/.gitkeep

echo "✅ Directory structure created"
ls -la migrations/
```

**Output:** Directory structure created
**Signal:** `PHASE0_DIRS_READY`
**Duration:** 10 seconds

---

**CHECKPOINT 0:** Wait for all Phase 0 signals:
- `PHASE0_GIT_BACKUP_COMPLETE`
- `PHASE0_ENV_READY`
- `PHASE0_DIRS_READY`

**Coordinator action:** Verify all signals received → Emit `PHASE0_COMPLETE`

---

## 🔍 PHASE 1: DISCOVERY & ANALYSIS (PARALLEL)

**Duration:** 4 minutes
**Assigned to:** Instances 1, 2, 3
**Wait for:** `PHASE0_COMPLETE`

---

### INSTANCE 1: DB-SCHEMA (Database Schema Export)

---

### 🔹 PROMPT 1.1: Export Users Table Schema

**Instance:** 1 (DB-SCHEMA)

**Task:** Export current users table schema from PostgreSQL

**Execute:**
```bash
cd "/Users/newdldewdl/Global Domination 2/peerbridge proj/backend"
source venv/bin/activate

# Create schema export script
cat > scripts/export_users_schema.py << 'SCRIPT_EOF'
import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

try:
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    cur = conn.cursor()

    # Get table columns
    cur.execute("""
        SELECT
            column_name,
            data_type,
            character_maximum_length,
            is_nullable,
            column_default
        FROM information_schema.columns
        WHERE table_name = 'users'
        ORDER BY ordinal_position;
    """)

    with open('migrations/analysis/users_table_schema.txt', 'w') as f:
        f.write('USERS TABLE SCHEMA (Current Database)\n')
        f.write('='*80 + '\n\n')

        columns = cur.fetchall()
        for col in columns:
            name, dtype, max_len, nullable, default = col
            len_str = f"({max_len})" if max_len else ""
            f.write(f"{name:<30} {dtype}{len_str:<20} NULL:{nullable:<3} DEFAULT:{default}\n")

        f.write(f'\nTotal columns: {len(columns)}\n')

    print(f"✅ Users schema exported: {len(columns)} columns")
    cur.close()
    conn.close()

except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)
SCRIPT_EOF

# Install psycopg2 if needed
pip install psycopg2-binary --quiet

# Execute script
python scripts/export_users_schema.py
cat migrations/analysis/users_table_schema.txt
```

**Output:** `backend/migrations/analysis/users_table_schema.txt`
**Signal:** `USERS_SCHEMA_EXPORTED`
**Duration:** 1 minute

---

### 🔹 PROMPT 1.2: Export Auth Sessions Table Schema

**Instance:** 1 (DB-SCHEMA)

**Task:** Check if auth_sessions exists and export schema

**Execute:**
```bash
cd "/Users/newdldewdl/Global Domination 2/peerbridge proj/backend"
source venv/bin/activate

cat > scripts/export_auth_sessions_schema.py << 'SCRIPT_EOF'
import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

try:
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    cur = conn.cursor()

    # Check if table exists
    cur.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_name = 'auth_sessions'
        );
    """)
    table_exists = cur.fetchone()[0]

    with open('migrations/analysis/auth_sessions_table_schema.txt', 'w') as f:
        f.write('AUTH_SESSIONS TABLE SCHEMA\n')
        f.write('='*80 + '\n\n')

        if table_exists:
            cur.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = 'auth_sessions'
                ORDER BY ordinal_position;
            """)
            columns = cur.fetchall()
            for col in columns:
                name, dtype, nullable, default = col
                f.write(f"{name:<30} {dtype:<20} NULL:{nullable:<3} DEFAULT:{default}\n")
            f.write(f'\nTotal columns: {len(columns)}\n')
            print(f"✅ auth_sessions EXISTS with {len(columns)} columns")
        else:
            f.write('❌ Table does NOT exist - must be created\n')
            print("⚠️ auth_sessions does NOT exist")

    cur.close()
    conn.close()

except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)
SCRIPT_EOF

python scripts/export_auth_sessions_schema.py
cat migrations/analysis/auth_sessions_table_schema.txt
```

**Output:** `backend/migrations/analysis/auth_sessions_table_schema.txt`
**Signal:** `AUTH_SESSIONS_SCHEMA_EXPORTED`
**Duration:** 1 minute

---

### 🔹 PROMPT 1.3: Export Database Indexes

**Instance:** 1 (DB-SCHEMA)

**Task:** Export all indexes on users and auth_sessions tables

**Execute:**
```bash
cd "/Users/newdldewdl/Global Domination 2/peerbridge proj/backend"
source venv/bin/activate

cat > scripts/export_indexes.py << 'SCRIPT_EOF'
import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

try:
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    cur = conn.cursor()

    cur.execute("""
        SELECT
            t.tablename,
            i.indexname,
            array_agg(a.attname ORDER BY array_position(ix.indkey, a.attnum)) as columns,
            ix.indisunique as is_unique,
            ix.indisprimary as is_primary
        FROM pg_indexes i
        JOIN pg_class c ON c.relname = i.indexname
        JOIN pg_index ix ON ix.indexrelid = c.oid
        JOIN pg_attribute a ON a.attrelid = ix.indrelid AND a.attnum = ANY(ix.indkey)
        JOIN pg_tables t ON t.tablename = i.tablename
        WHERE t.tablename IN ('users', 'auth_sessions')
        GROUP BY t.tablename, i.indexname, ix.indisunique, ix.indisprimary
        ORDER BY t.tablename, i.indexname;
    """)

    with open('migrations/analysis/database_indexes.txt', 'w') as f:
        f.write('DATABASE INDEXES\n')
        f.write('='*80 + '\n\n')

        indexes = cur.fetchall()
        if indexes:
            for idx in indexes:
                table, name, cols, unique, primary = idx
                cols_str = ', '.join(cols)
                flags = []
                if primary:
                    flags.append('PRIMARY KEY')
                if unique:
                    flags.append('UNIQUE')
                flags_str = ', '.join(flags) if flags else 'REGULAR'
                f.write(f"{table:<20} {name:<40} [{cols_str}] ({flags_str})\n")
            f.write(f'\nTotal indexes: {len(indexes)}\n')
            print(f"✅ Exported {len(indexes)} indexes")
        else:
            f.write('No indexes found\n')
            print("⚠️ No indexes found")

    cur.close()
    conn.close()

except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)
SCRIPT_EOF

python scripts/export_indexes.py
cat migrations/analysis/database_indexes.txt
```

**Output:** `backend/migrations/analysis/database_indexes.txt`
**Signal:** `DB_INDEXES_EXPORTED`
**Duration:** 1 minute

---

### 🔹 PROMPT 1.4: Count Existing Data

**Instance:** 1 (DB-SCHEMA)

**Task:** Count records in all relevant tables

**Execute:**
```bash
cd "/Users/newdldewdl/Global Domination 2/peerbridge proj/backend"
source venv/bin/activate

cat > scripts/count_data.py << 'SCRIPT_EOF'
import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

try:
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    cur = conn.cursor()

    # Count users
    cur.execute('SELECT COUNT(*) FROM users;')
    user_count = cur.fetchone()[0]

    # Count auth_sessions if exists
    cur.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_name = 'auth_sessions'
        );
    """)
    auth_exists = cur.fetchone()[0]

    if auth_exists:
        cur.execute('SELECT COUNT(*) FROM auth_sessions;')
        session_count = cur.fetchone()[0]
    else:
        session_count = 'N/A'

    # Count therapy sessions
    cur.execute('SELECT COUNT(*) FROM sessions;')
    therapy_count = cur.fetchone()[0]

    with open('migrations/analysis/data_counts.txt', 'w') as f:
        f.write('DATABASE RECORD COUNTS\n')
        f.write('='*80 + '\n\n')
        f.write(f"Users: {user_count}\n")
        f.write(f"Auth Sessions: {session_count}\n")
        f.write(f"Therapy Sessions: {therapy_count}\n")
        f.write(f'\nMigration Impact: {user_count} user records will be modified\n')

    print(f"✅ Counts: {user_count} users, {session_count} auth sessions")
    cur.close()
    conn.close()

except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)
SCRIPT_EOF

python scripts/count_data.py
cat migrations/analysis/data_counts.txt
```

**Output:** `backend/migrations/analysis/data_counts.txt`
**Signal:** `DATA_COUNTS_COMPLETE`
**Duration:** 30 seconds

---

### INSTANCE 2: DB-BACKUP (Backup System Creation)

---

### 🔹 PROMPT 2.1: Create Backup Script

**Instance:** 2 (DB-BACKUP)

**Task:** Create comprehensive database backup script

**Execute:**
```bash
cd "/Users/newdldewdl/Global Domination 2/peerbridge proj/backend"

cat > scripts/backup_database.py << 'SCRIPT_EOF'
#!/usr/bin/env python3
"""Backup all database data before migration"""
import os
import json
from datetime import datetime
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv()

def serialize_datetime(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def backup_database():
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))

    backup_data = {
        'backup_timestamp': datetime.utcnow().isoformat(),
        'tables': {}
    }

    tables = ['users', 'sessions', 'conversation_turns', 'therapeutic_notes']

    # Check if auth_sessions exists
    with conn.cursor() as cur:
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'auth_sessions'
            );
        """)
        if cur.fetchone()[0]:
            tables.append('auth_sessions')

    # Backup each table
    for table in tables:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(f'SELECT * FROM {table};')
                rows = cur.fetchall()
                backup_data['tables'][table] = [dict(row) for row in rows]
                print(f"✅ Backed up {len(rows)} rows from {table}")
        except Exception as e:
            print(f"⚠️ Could not backup {table}: {e}")
            backup_data['tables'][table] = {'error': str(e)}

    # Save to file
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    filename = f'migrations/backups/backup_{timestamp}.json'

    with open(filename, 'w') as f:
        json.dump(backup_data, f, indent=2, default=serialize_datetime)

    conn.close()

    print(f'\n✅ BACKUP COMPLETE: {filename}')
    print(f'Total tables: {len(backup_data["tables"])}')

    # Save filename for reference
    with open('migrations/backups/latest_backup.txt', 'w') as f:
        f.write(filename)

    return filename

if __name__ == '__main__':
    backup_database()
SCRIPT_EOF

chmod +x scripts/backup_database.py
echo "✅ Backup script created"
```

**Output:** `backend/scripts/backup_database.py`
**Signal:** `BACKUP_SCRIPT_CREATED`
**Duration:** 2 minutes

---

### 🔹 PROMPT 2.2: Execute Pre-Migration Backup

**Instance:** 2 (DB-BACKUP)

**Task:** Run backup script to create snapshot

**Execute:**
```bash
cd "/Users/newdldewdl/Global Domination 2/peerbridge proj/backend"
source venv/bin/activate

# Install psycopg2 if needed
pip install psycopg2-binary --quiet

# Run backup
python scripts/backup_database.py

# Verify backup created
BACKUP_FILE=$(cat migrations/backups/latest_backup.txt)

if [ -f "$BACKUP_FILE" ]; then
    echo "✅ Backup verified: $BACKUP_FILE"
    ls -lh "$BACKUP_FILE"
else
    echo "❌ Backup failed"
    exit 1
fi
```

**Output:** Backup JSON file in `backend/migrations/backups/`
**Signal:** `PRE_MIGRATION_BACKUP_COMPLETE`
**Duration:** 1 minute

---

### 🔹 PROMPT 2.3: Create Restore Script

**Instance:** 2 (DB-BACKUP)

**Task:** Create data restore script for emergencies

**Execute:**
```bash
cd "/Users/newdldewdl/Global Domination 2/peerbridge proj/backend"

cat > scripts/restore_database.py << 'SCRIPT_EOF'
#!/usr/bin/env python3
"""Restore database from backup JSON"""
import os
import json
import sys
from datetime import datetime
from dotenv import load_dotenv
import psycopg2

load_dotenv()

def restore_database(backup_file):
    if not os.path.exists(backup_file):
        print(f"❌ Backup file not found: {backup_file}")
        sys.exit(1)

    with open(backup_file, 'r') as f:
        backup_data = json.load(f)

    print(f"📦 Backup from: {backup_data['backup_timestamp']}")
    print(f"Tables: {list(backup_data['tables'].keys())}")
    print()
    print("⚠️ WARNING: Manual data restoration required")
    print("⚠️ Review backup JSON before restoring")
    print()

    for table, rows in backup_data['tables'].items():
        if isinstance(rows, dict) and 'error' in rows:
            print(f"⚠️ {table}: Backup error - {rows['error']}")
        else:
            print(f"   {table}: {len(rows)} rows")

    print()
    print("To restore:")
    print("1. Review backup JSON file")
    print("2. Rollback migration: alembic downgrade -1")
    print("3. Re-insert data manually")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        try:
            with open('migrations/backups/latest_backup.txt', 'r') as f:
                backup_file = f.read().strip()
        except:
            print("Usage: python restore_database.py <backup_file>")
            sys.exit(1)
    else:
        backup_file = sys.argv[1]

    restore_database(backup_file)
SCRIPT_EOF

chmod +x scripts/restore_database.py
echo "✅ Restore script created"
```

**Output:** `backend/scripts/restore_database.py`
**Signal:** `RESTORE_SCRIPT_CREATED`
**Duration:** 1 minute

---

### 🔹 PROMPT 2.4: Create Rollback Guide

**Instance:** 2 (DB-BACKUP)

**Task:** Create comprehensive rollback documentation

**Execute:**
```bash
cd "/Users/newdldewdl/Global Domination 2/peerbridge proj/backend"

cat > migrations/ROLLBACK_GUIDE.md << 'DOC_EOF'
# 🚨 EMERGENCY ROLLBACK GUIDE

## When to Use

- Migration fails partway through
- Data corruption detected
- Need to revert to pre-migration state

## Rollback Procedure

### 1. Stop Backend Server

```bash
pkill -f "uvicorn app.main:app" || true
ps aux | grep uvicorn
```

### 2. Check Current Migration

```bash
cd backend
source venv/bin/activate
alembic current
alembic history
```

### 3. Rollback Migration

```bash
# Rollback one migration
alembic downgrade -1

# OR rollback to specific revision
alembic downgrade <revision_id>

# OR rollback all
alembic downgrade base
```

### 4. Verify Database

```bash
psql $DATABASE_URL

\d users
\d auth_sessions
SELECT COUNT(*) FROM users;
```

### 5. Restore Data (if needed)

```bash
ls -lh migrations/backups/
python scripts/restore_database.py migrations/backups/backup_YYYYMMDD_HHMMSS.json
```

### 6. Restart Backend

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

## Prevention Checklist

Before migration:

- [ ] Backup created
- [ ] Backup verified
- [ ] SQL preview reviewed
- [ ] Team notified
- [ ] Tested on dev database

## Recovery Contacts

- **Backup Location:** `backend/migrations/backups/`
- **Latest Backup:** Check `migrations/backups/latest_backup.txt`
- **Migration Logs:** `migrations/analysis/migration_output.log`

## Common Issues

**"Can't locate revision"** → Check `alembic/versions/` exists

**"Connection refused"** → Verify DATABASE_URL in .env

**"Column already exists"** → Migration partially applied, rollback manually

## Git Rollback

```bash
git log --oneline -10
git revert <commit_hash>
```

---

**Last Updated:** 2025-12-17
DOC_EOF

echo "✅ Rollback guide created"
cat migrations/ROLLBACK_GUIDE.md
```

**Output:** `backend/migrations/ROLLBACK_GUIDE.md`
**Signal:** `ROLLBACK_GUIDE_CREATED`
**Duration:** 1 minute

---

### INSTANCE 3: DB-COMPARE (Model Comparison)

---

### 🔹 PROMPT 3.1: Analyze SQLAlchemy Models

**Instance:** 3 (DB-COMPARE)

**Task:** Extract field definitions from User and AuthSession models

**Execute:**
```bash
cd "/Users/newdldewdl/Global Domination 2/peerbridge proj/backend"
source venv/bin/activate

cat > scripts/analyze_models.py << 'SCRIPT_EOF'
"""Extract field information from SQLAlchemy models"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.auth.models import User, AuthSession
from sqlalchemy import inspect as sqla_inspect

def analyze_model(model_class):
    inspector = sqla_inspect(model_class)
    fields = []

    for column in inspector.columns:
        field_info = {
            'name': column.name,
            'type': str(column.type),
            'nullable': column.nullable,
            'primary_key': column.primary_key,
            'unique': getattr(column, 'unique', False),
            'default': str(column.default) if column.default else None,
        }
        fields.append(field_info)

    return fields

def main():
    with open('migrations/analysis/model_fields.txt', 'w') as f:
        f.write('SQLALCHEMY MODEL FIELD ANALYSIS\n')
        f.write('='*80 + '\n\n')

        # User model
        f.write('USER MODEL (app/auth/models.py):\n')
        f.write('-'*80 + '\n')
        user_fields = analyze_model(User)
        for field in user_fields:
            f.write(f"  {field['name']:<30} {field['type']:<20} "
                   f"null={field['nullable']} pk={field['primary_key']}\n")
        f.write(f'\nTotal User fields: {len(user_fields)}\n\n')

        # AuthSession model
        f.write('AUTHSESSION MODEL (app/auth/models.py):\n')
        f.write('-'*80 + '\n')
        auth_fields = analyze_model(AuthSession)
        for field in auth_fields:
            f.write(f"  {field['name']:<30} {field['type']:<20} "
                   f"null={field['nullable']} pk={field['primary_key']}\n")
        f.write(f'\nTotal AuthSession fields: {len(auth_fields)}\n')

    print(f"✅ Model analysis complete")
    print(f"   User: {len(user_fields)} fields")
    print(f"   AuthSession: {len(auth_fields)} fields")

if __name__ == '__main__':
    main()
SCRIPT_EOF

python scripts/analyze_models.py
cat migrations/analysis/model_fields.txt
```

**Output:** `backend/migrations/analysis/model_fields.txt`
**Signal:** `MODEL_FIELDS_ANALYZED`
**Duration:** 1 minute

---

### 🔹 PROMPT 3.2: Compare Schema vs Models

**Instance:** 3 (DB-COMPARE)

**Wait for:** `USERS_SCHEMA_EXPORTED` + `MODEL_FIELDS_ANALYZED`

**Task:** Compare database schema against SQLAlchemy models

**Execute:**
```bash
cd "/Users/newdldewdl/Global Domination 2/peerbridge proj/backend"
source venv/bin/activate

cat > scripts/compare_schema.py << 'SCRIPT_EOF'
"""Compare database schema vs SQLAlchemy models"""

def parse_db_schema(filename):
    columns = set()
    with open(filename, 'r') as f:
        for line in f:
            if line.strip() and not line.startswith('=') and not line.startswith('USERS'):
                parts = line.split()
                if parts and not parts[0].startswith('Total'):
                    columns.add(parts[0])
    return columns

def parse_model_fields(filename):
    fields = set()
    with open(filename, 'r') as f:
        in_user_section = False
        for line in f:
            if 'USER MODEL' in line:
                in_user_section = True
            elif 'AUTHSESSION MODEL' in line or 'Total' in line:
                in_user_section = False
            elif in_user_section and line.strip() and line.startswith('  '):
                parts = line.split()
                if parts:
                    fields.add(parts[0])
    return fields

# Parse files
db_columns = parse_db_schema('migrations/analysis/users_table_schema.txt')
model_fields = parse_model_fields('migrations/analysis/model_fields.txt')

# Find mismatches
missing_in_db = model_fields - db_columns
extra_in_db = db_columns - model_fields
matching = model_fields & db_columns

# Generate report
with open('migrations/analysis/schema_comparison.md', 'w') as f:
    f.write('# Database vs Model Schema Comparison\n\n')
    f.write(f'**Date:** {__import__("datetime").datetime.now().isoformat()}\n\n')

    f.write('## ❌ Fields in Model but MISSING in Database\n\n')
    if missing_in_db:
        for field in sorted(missing_in_db):
            f.write(f'- `{field}`\n')
    else:
        f.write('✅ None\n')

    f.write('\n## ⚠️ Fields in Database but NOT in Model\n\n')
    if extra_in_db:
        for field in sorted(extra_in_db):
            f.write(f'- `{field}`\n')
    else:
        f.write('✅ None\n')

    f.write('\n## ✅ Matching Fields\n\n')
    for field in sorted(matching):
        f.write(f'- `{field}`\n')

    f.write(f'\n## Summary\n\n')
    f.write(f'- Model fields: {len(model_fields)}\n')
    f.write(f'- Database columns: {len(db_columns)}\n')
    f.write(f'- Missing in DB: {len(missing_in_db)}\n')
    f.write(f'- Extra in DB: {len(extra_in_db)}\n')
    f.write(f'- Matching: {len(matching)}\n')

print(f"✅ Schema comparison complete")
print(f"   Missing: {len(missing_in_db)}, Extra: {len(extra_in_db)}, Match: {len(matching)}")
SCRIPT_EOF

python scripts/compare_schema.py
cat migrations/analysis/schema_comparison.md
```

**Output:** `backend/migrations/analysis/schema_comparison.md`
**Signal:** `SCHEMA_COMPARISON_COMPLETE`
**Duration:** 1 minute

---

### 🔹 PROMPT 3.3: Generate Migration Requirements

**Instance:** 3 (DB-COMPARE)

**Wait for:** `SCHEMA_COMPARISON_COMPLETE` + `AUTH_SESSIONS_SCHEMA_EXPORTED`

**Task:** Create detailed migration requirements document

**Execute:**
```bash
cd "/Users/newdldewdl/Global Domination 2/peerbridge proj/backend"

cat > migrations/analysis/migration_requirements.md << 'REQ_EOF'
# Migration Requirements

**Generated:** $(date)

## Required Actions

### 1. Add Missing Columns to users Table

REQ_EOF

# Extract missing columns
grep "^- \`" migrations/analysis/schema_comparison.md | head -10 >> migrations/analysis/migration_requirements.md

cat >> migrations/analysis/migration_requirements.md << 'REQ_EOF'

### 2. Handle auth_sessions Table

REQ_EOF

if grep -q "does NOT exist" migrations/analysis/auth_sessions_table_schema.txt; then
    echo "- **CREATE** auth_sessions table" >> migrations/analysis/migration_requirements.md
else
    echo "- **VERIFY** auth_sessions schema" >> migrations/analysis/migration_requirements.md
fi

cat >> migrations/analysis/migration_requirements.md << 'REQ_EOF'

### 3. Add Required Indexes

- `users.email` - UNIQUE
- `auth_sessions.refresh_token_hash` - Regular
- `auth_sessions.user_id` - Foreign key

### 4. Data Migration

- New columns nullable initially (for existing rows)
- `is_active` defaults to TRUE
- `created_at`/`updated_at` use server defaults

### 5. Rollback

- See `migrations/ROLLBACK_GUIDE.md`
- Use `alembic downgrade -1`
REQ_EOF

echo "✅ Requirements generated"
cat migrations/analysis/migration_requirements.md
```

**Output:** `backend/migrations/analysis/migration_requirements.md`
**Signal:** `MIGRATION_REQUIREMENTS_GENERATED`
**Duration:** 1 minute

---

**CHECKPOINT 1:** Wait for Phase 1 signals:
- `USERS_SCHEMA_EXPORTED`
- `AUTH_SESSIONS_SCHEMA_EXPORTED`
- `DB_INDEXES_EXPORTED`
- `DATA_COUNTS_COMPLETE`
- `BACKUP_SCRIPT_CREATED`
- `PRE_MIGRATION_BACKUP_COMPLETE`
- `RESTORE_SCRIPT_CREATED`
- `ROLLBACK_GUIDE_CREATED`
- `MODEL_FIELDS_ANALYZED`
- `SCHEMA_COMPARISON_COMPLETE`
- `MIGRATION_REQUIREMENTS_GENERATED`

**Coordinator action:** Verify all signals → Emit `PHASE1_COMPLETE`

---

*Due to length constraints, the remaining phases (2-7) follow the same detailed pattern. Each phase contains 10-15 ultra-fine-grained prompts with complete bash/Python scripts.*

*Request specific phases:*
- "Generate Phase 2 prompts (Alembic infrastructure)"
- "Generate Phase 3 prompts (Backend development)"
- "Generate Phase 4 prompts (Testing)"
- "Generate Phase 5 prompts (Migration execution)"
- "Generate Phase 6 prompts (Validation)"
- "Generate Phase 7 prompts (Cleanup & documentation)"

*Each phase takes ~5,000 lines to fully detail with copy-pasteable commands.*

---

## 🎯 EXECUTION INSTRUCTIONS

1. **Run Phase 0** (Sequential - Instance 0 only)
   - Execute Prompts 0.1, 0.2, 0.3
   - Wait for `PHASE0_COMPLETE`

2. **Run Phase 1** (Parallel - Instances 1, 2, 3)
   - Instance 1: Execute Prompts 1.1-1.4
   - Instance 2: Execute Prompts 2.1-2.4
   - Instance 3: Execute Prompts 3.1-3.3
   - All execute simultaneously
   - Wait for `PHASE1_COMPLETE`

3. **Request Next Phase Prompts**
   - Say: "Generate Phase 2 prompts with same detail level"
   - Execute Phase 2 in parallel
   - Continue phase-by-phase

---

**Total Implementation:** 63 prompts across 7 phases, 15 instances, 18 minutes estimated time
