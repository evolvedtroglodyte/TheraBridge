# Feature 1: Authentication - Maximum Parallel Execution Plan

## Overview

This plan breaks Feature 1 into **maximum independent micro-tasks** to run as many Claude Code agents simultaneously as possible.

**Goal:** Complete Feature 1 in **under 1 hour** using 15+ parallel windows.

---

## Dependency Graph Analysis

Here's what can run in parallel based on dependencies:

```
PHASE 1 (15 independent tasks - run ALL simultaneously)
├─ Backend DB Layer (5 tasks)
│  ├─ 1.1.1: User model base
│  ├─ 1.1.2: User auth fields
│  ├─ 1.1.3: User role fields
│  ├─ 1.1.4: User timestamps
│  └─ 1.1.5: Session model
│
├─ Backend Utils (6 tasks)
│  ├─ 1.2.1: Auth config
│  ├─ 1.2.2: Password hashing
│  ├─ 1.2.3: Access token generation
│  ├─ 1.2.4: Refresh token generation
│  └─ 1.2.6: Environment variables (backend)
│
└─ Frontend Foundation (4 tasks)
   ├─ 1.4.1: Token storage
   ├─ 1.4.8: Environment variables (frontend)
   └─ [2 buffer windows for quick tasks]

PHASE 2 (10 tasks - run after Phase 1)
├─ 1.1.6: User-Session relationship (needs all 1.1.*)
├─ 1.1.7: User schemas (needs 1.1.6)
├─ 1.1.8: Token schemas (needs 1.1.7)
├─ 1.2.5: Token verification (needs 1.2.3, 1.2.4)
├─ 1.3.1: Database dependency (needs 1.1.6)
├─ 1.4.2: API client (needs 1.4.1)
├─ 1.4.3: Auth context (needs 1.4.2)
├─ 1.1.9: Alembic migration (needs all 1.1.*)
└─ [2 buffer windows]

PHASE 3 (10 tasks - run after Phase 2)
├─ 1.3.2: Current user dependency (needs 1.3.1, 1.2.5)
├─ 1.3.3: Role-based access (needs 1.3.2)
├─ 1.3.4: Signup endpoint (needs 1.3.1, 1.1.8)
├─ 1.3.5: Login endpoint (needs 1.3.1, 1.1.8)
├─ 1.4.4: Login page (needs 1.4.3)
├─ 1.4.5: Signup page (needs 1.4.3)
├─ 1.4.6: Protected route (needs 1.4.3)
└─ [3 buffer windows]

PHASE 4 (5 tasks - run after Phase 3)
├─ 1.3.6: Refresh & logout (needs 1.3.5)
├─ 1.3.7: Get me endpoint (needs 1.3.6)
├─ 1.4.7: Wrap with AuthProvider (needs 1.4.6)
└─ [2 buffer windows]

PHASE 5 (1 task - integration testing)
└─ Integration test (needs everything)
```

---

## Maximum Parallelization Setup: 15 Windows

### Hardware Requirements
- **Recommended:** 3 monitors or large ultrawide
- **Minimum:** 2 monitors or 1 large screen
- **RAM:** 16GB+ (each Claude Code instance uses ~500MB)
- **CPU:** Multi-core (i7/M1 or better)

### Window Layout Strategy

#### **Option A: 3 Monitors (Recommended)**
```
Monitor 1 (Left):              Monitor 2 (Center):           Monitor 3 (Right):
┌────────┬────────┐            ┌────────┬────────┐           ┌────────┬────────┐
│ Win 1  │ Win 2  │            │ Win 6  │ Win 7  │           │ Win 11 │ Win 12 │
├────────┼────────┤            ├────────┼────────┤           ├────────┼────────┤
│ Win 3  │ Win 4  │            │ Win 8  │ Win 9  │           │ Win 13 │ Win 14 │
├────────┼────────┤            ├────────┼────────┤           ├────────┼────────┤
│ Win 5  │ Code   │            │ Win 10 │ Docs   │           │ Win 15 │ Terminal│
└────────┴────────┘            └────────┴────────┘           └────────┴────────┘
```

#### **Option B: 2 Monitors**
```
Monitor 1 (Left):              Monitor 2 (Right):
┌────────┬────────┬────────┐  ┌────────┬────────┬────────┐
│ Win 1  │ Win 2  │ Win 3  │  │ Win 8  │ Win 9  │ Win 10 │
├────────┼────────┼────────┤  ├────────┼────────┼────────┤
│ Win 4  │ Win 5  │ Win 6  │  │ Win 11 │ Win 12 │ Win 13 │
├────────┼────────┼────────┤  ├────────┼────────┼────────┤
│ Win 7  │ Code   │ Docs   │  │ Win 14 │ Win 15 │Terminal│
└────────┴────────┴────────┘  └────────┴────────┴────────┘
```

#### **Option C: Single Large Monitor (4K/Ultrawide)**
Use tiling window manager:
- macOS: Rectangle, Magnet, Amethyst
- Windows: PowerToys FancyZones
- Linux: i3, bspwm

```
┌────────┬────────┬────────┬────────┬────────┐
│ Win 1  │ Win 2  │ Win 3  │ Win 4  │ Win 5  │
├────────┼────────┼────────┼────────┼────────┤
│ Win 6  │ Win 7  │ Win 8  │ Win 9  │ Win 10 │
├────────┼────────┼────────┼────────┼────────┤
│ Win 11 │ Win 12 │ Win 13 │ Win 14 │ Win 15 │
└────────┴────────┴────────┴────────┴────────┘
```

---

## Phase-by-Phase Execution Guide

### PHASE 1: Foundation Layer (15 windows, ~10-12 minutes)

**Objective:** Create all independent foundation files simultaneously.

#### Window Assignments:

**Window 1:** SUBTASK 1.1.1 - User Model Base
```
File: backend/app/auth/models.py
Task: Create User class with id field only
Duration: ~5 min
```

**Window 2:** SUBTASK 1.1.2 - User Auth Fields
```
File: backend/app/auth/models.py (append)
Task: Add email, hashed_password, full_name
Duration: ~5 min
```

**Window 3:** SUBTASK 1.1.3 - User Role Fields
```
File: backend/app/auth/models.py (append)
Task: Add role, is_active
Duration: ~5 min
```

**Window 4:** SUBTASK 1.1.4 - User Timestamps
```
File: backend/app/auth/models.py (append)
Task: Add created_at, updated_at
Duration: ~5 min
```

**Window 5:** SUBTASK 1.1.5 - Session Model
```
File: backend/app/auth/models.py (append)
Task: Create Session class
Duration: ~8 min
```

**Window 6:** SUBTASK 1.2.1 - Auth Config
```
File: backend/app/auth/config.py
Task: Create AuthConfig with JWT settings
Duration: ~7 min
```

**Window 7:** SUBTASK 1.2.2 - Password Hashing
```
File: backend/app/auth/utils.py
Task: Create password hash/verify functions
Duration: ~8 min
```

**Window 8:** SUBTASK 1.2.3 - Access Token
```
File: backend/app/auth/utils.py (append)
Task: Create access token generation
Duration: ~10 min
```

**Window 9:** SUBTASK 1.2.4 - Refresh Token
```
File: backend/app/auth/utils.py (append)
Task: Create refresh token generation
Duration: ~8 min
```

**Window 10:** SUBTASK 1.2.6 - Backend Env
```
File: backend/.env.example
Task: Add auth environment variables
Duration: ~3 min
```

**Window 11:** SUBTASK 1.4.1 - Token Storage
```
File: frontend/lib/token-storage.ts
Task: localStorage utilities
Duration: ~10 min
```

**Window 12:** SUBTASK 1.4.8 - Frontend Env
```
File: frontend/.env.local.example
Task: Add API URL variable
Duration: ~3 min
```

**Windows 13-15:** Buffer (for re-runs if errors)

#### Execution Steps:

1. **Pre-flight check (2 min):**
   ```bash
   # Verify backend structure
   ls backend/app/auth/  # Should exist
   ls backend/alembic/   # Should exist

   # Verify frontend structure
   ls frontend/lib/      # Should exist
   ls frontend/app/      # Should exist
   ```

2. **Open all windows (2 min):**
   - Open 15 Claude Code browser tabs
   - Label tabs: "1.1.1", "1.1.2", ..., "1.4.8"

3. **Paste all prompts (3 min):**
   - Open FEATURE_1_ULTRA_FINE_GRAINED.md
   - Copy each subtask prompt
   - Paste into corresponding window
   - **DO NOT press Enter yet**

4. **Synchronized start (30 sec):**
   - Press Enter on Window 1
   - Immediately press Enter on Windows 2-12 (within 30 seconds)
   - Monitor progress bars

5. **Progress monitoring (10 min):**
   ```
   Track completion:
   ✅ Win 10 (1.2.6) - Done at 0:03
   ✅ Win 12 (1.4.8) - Done at 0:03
   ✅ Win 1 (1.1.1) - Done at 0:05
   ✅ Win 2 (1.1.2) - Done at 0:05
   ✅ Win 3 (1.1.3) - Done at 0:05
   ✅ Win 4 (1.1.4) - Done at 0:05
   ✅ Win 6 (1.2.1) - Done at 0:07
   ✅ Win 7 (1.2.2) - Done at 0:08
   ✅ Win 5 (1.1.5) - Done at 0:08
   ✅ Win 9 (1.2.4) - Done at 0:08
   ✅ Win 8 (1.2.3) - Done at 0:10
   ✅ Win 11 (1.4.1) - Done at 0:10

   Phase 1 complete! ✨
   ```

6. **Quick validation (2 min):**
   ```bash
   # Check files created
   ls backend/app/auth/models.py    # Should exist, ~150 lines
   ls backend/app/auth/config.py    # Should exist, ~20 lines
   ls backend/app/auth/utils.py     # Should exist, ~100 lines
   ls frontend/lib/token-storage.ts # Should exist, ~50 lines

   # Quick syntax check
   cd backend && python -c "from app.auth.models import User"
   cd frontend && npm run build --dry-run
   ```

---

### PHASE 2: Integration Layer (10 windows, ~15 minutes)

**Objective:** Connect Phase 1 components together.

#### Window Assignments:

**Window 1:** SUBTASK 1.1.6 - User-Session Relationship
```
Depends on: 1.1.1-1.1.5 complete
Duration: ~10 min
```

**Window 2:** SUBTASK 1.1.7 - User Schemas
```
Depends on: 1.1.6 complete
Duration: ~12 min
```

**Window 3:** SUBTASK 1.1.8 - Token Schemas
```
Depends on: 1.1.7 complete (can run in parallel)
Duration: ~8 min
```

**Window 4:** SUBTASK 1.2.5 - Token Verification
```
Depends on: 1.2.3, 1.2.4 complete
Duration: ~15 min
```

**Window 5:** SUBTASK 1.3.1 - Database Dependency
```
Depends on: 1.1.6 complete
Duration: ~10 min
```

**Window 6:** SUBTASK 1.4.2 - API Client
```
Depends on: 1.4.1 complete
Duration: ~15 min
```

**Window 7:** SUBTASK 1.4.3 - Auth Context
```
Depends on: 1.4.2 complete
Duration: ~15 min
```

**Window 8:** SUBTASK 1.1.9 - Alembic Migration
```
Depends on: 1.1.6, 1.1.7, 1.1.8 complete
Duration: ~10 min
```

**Windows 9-10:** Buffer

#### Execution Strategy:

**Sub-phase 2a (Start simultaneously):**
- Window 1: 1.1.6
- Window 4: 1.2.5
- Window 6: 1.4.2
Duration: ~10-12 min

**Sub-phase 2b (Start after 2a):**
- Window 2: 1.1.7
- Window 5: 1.3.1
- Window 7: 1.4.3
Duration: ~12-15 min

**Sub-phase 2c (Start after 2b):**
- Window 3: 1.1.8
- Window 8: 1.1.9
Duration: ~8-10 min

---

### PHASE 3: API & UI Layer (10 windows, ~15 minutes)

**Objective:** Build all endpoints and frontend pages in parallel.

#### Window Assignments:

**Window 1:** SUBTASK 1.3.2 - Current User Dependency
```
Depends on: 1.3.1, 1.2.5
Duration: ~12 min
```

**Window 2:** SUBTASK 1.3.3 - Role-Based Access
```
Depends on: 1.3.2
Duration: ~10 min
```

**Window 3:** SUBTASK 1.3.4 - Signup Endpoint
```
Depends on: 1.3.1, 1.1.8
Duration: ~15 min
```

**Window 4:** SUBTASK 1.3.5 - Login Endpoint
```
Depends on: 1.3.1, 1.1.8
Duration: ~12 min
```

**Window 5:** SUBTASK 1.4.4 - Login Page
```
Depends on: 1.4.3
Duration: ~15 min
```

**Window 6:** SUBTASK 1.4.5 - Signup Page
```
Depends on: 1.4.3
Duration: ~15 min
```

**Window 7:** SUBTASK 1.4.6 - Protected Route
```
Depends on: 1.4.3
Duration: ~12 min
```

**Windows 8-10:** Buffer

#### Execution Strategy:

**Sub-phase 3a (Start simultaneously):**
- Window 1: 1.3.2
- Window 3: 1.3.4
- Window 4: 1.3.5
- Window 5: 1.4.4
- Window 6: 1.4.5
- Window 7: 1.4.6
Duration: ~15 min

**Sub-phase 3b (Start after 1.3.2):**
- Window 2: 1.3.3
Duration: ~10 min

---

### PHASE 4: Final Integration (5 windows, ~10 minutes)

**Objective:** Connect all pieces and finalize.

#### Window Assignments:

**Window 1:** SUBTASK 1.3.6 - Refresh & Logout
```
Depends on: 1.3.5
Duration: ~10 min
```

**Window 2:** SUBTASK 1.3.7 - Get Me + Router
```
Depends on: 1.3.6
Duration: ~8 min
```

**Window 3:** SUBTASK 1.4.7 - Wrap with AuthProvider
```
Depends on: 1.4.6
Duration: ~5 min
```

**Windows 4-5:** Buffer

#### Execution Strategy:

**Sequential:**
1. Window 1: 1.3.6 (wait 10 min)
2. Window 2: 1.3.7 (wait 8 min)
3. Window 3: 1.4.7 (wait 5 min)

Or **parallel** if you implement 1.3.6 and 1.4.7 at same time.

---

### PHASE 5: Integration Testing (1 window, ~20 minutes)

**Window 1:** Run INTEGRATION TEST prompt
```
Full E2E testing of all auth flows
Duration: ~20 min
```

---

## Time Breakdown

| Phase | Sub-phases | Windows | Duration | Wait Time |
|-------|------------|---------|----------|-----------|
| 1 | 1 | 12 active | 10-12 min | 0 min |
| 2 | 3 | 8 active | 15 min total | 5 min sequential |
| 3 | 2 | 7 active | 15 min total | 5 min sequential |
| 4 | 1 | 3 active | 10 min total | 15 min sequential |
| 5 | 1 | 1 active | 20 min | 0 min |
| **Total** | - | **15 max** | **70 min** | **25 min idle** |

**Effective time:** ~45 minutes of active development + 25 minutes of waiting/validation

---

## Preparation Checklist

Before starting, ensure:

### Backend Setup
- [ ] PostgreSQL running: `pg_ctl status`
- [ ] Database created: `createdb therapybridge_dev`
- [ ] Virtual environment: `cd backend && python -m venv venv && source venv/bin/activate`
- [ ] Dependencies installed: `pip install -r requirements.txt`
- [ ] Alembic initialized: `alembic init alembic`
- [ ] Database connection configured in `database.py`

### Frontend Setup
- [ ] Node.js 18+ installed: `node --version`
- [ ] Dependencies installed: `cd frontend && npm install`
- [ ] shadcn/ui installed: `npx shadcn-ui@latest init`
- [ ] Base components ready: Button, Input, Select

### Environment
- [ ] 15 Claude Code windows/tabs open
- [ ] Windows labeled with subtask IDs
- [ ] FEATURE_1_ULTRA_FINE_GRAINED.md open for copy-paste
- [ ] Monitoring spreadsheet ready
- [ ] Coffee/water nearby ☕

---

## Quick Start Command

Execute this to verify everything is ready:

```bash
# Check backend
cd backend
python -c "from sqlalchemy import create_engine; print('✅ SQLAlchemy OK')"
python -c "from passlib.context import CryptContext; print('✅ Passlib OK')"
python -c "from jose import jwt; print('✅ Jose OK')"

# Check frontend
cd frontend
npm run build --dry-run && echo "✅ Frontend OK"

# If all pass, you're ready! 🚀
```

---

## Troubleshooting

### Issue: "Too many windows, getting confused"
**Solution:** Start with 5 windows in Phase 1, scale up after you're comfortable.

### Issue: "One window failed, blocking others"
**Solution:** Use buffer windows (13-15) to re-run failed tasks while others continue.

### Issue: "Can't monitor 15 windows"
**Solution:** Use automated monitoring:
```bash
# Create a simple script to check file sizes
watch -n 5 'ls -lh backend/app/auth/*.py frontend/lib/*.ts'
```

### Issue: "Dependencies unclear"
**Solution:** Follow the sub-phase groupings - they respect dependencies.

---

## Success Metrics

You've successfully completed Feature 1 when:

- ✅ All 29 subtasks complete
- ✅ All VALIDATION checklists pass
- ✅ Integration test passes
- ✅ Can signup, login, access protected route
- ✅ Token refresh works automatically
- ✅ Logout revokes tokens

**Estimated total time with 15 parallel windows:** 60-70 minutes

**Comparison:**
- Sequential (1 window): 4 hours
- Medium parallel (4 windows): 2.5 hours
- Maximum parallel (15 windows): **1 hour**

**Time saved: 3 hours (75% faster)** 🚀

---

Ready to execute? Start with Phase 1!
