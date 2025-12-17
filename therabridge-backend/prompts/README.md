# TherapyBridge Prompt System - File Index

This folder contains the **ultra-fine-grained prompt system** for building Feature 1 (Authentication) with maximum parallelization.

---

## 📁 File Organization

### **🎯 START HERE:**

**1. START_NOW_15_WINDOWS.md** ⭐ **← YOUR MAIN EXECUTION GUIDE**
   - Step-by-step instructions for 15-window parallel execution
   - Phase-by-phase breakdown with exact timings
   - Copy-paste checklist for each window
   - **Use this file to actually build Feature 1**

---

### **📖 Core Documentation:**

**2. FEATURE_1_ULTRA_FINE_GRAINED.md** (67KB)
   - All 29 subtask prompts in detail
   - Source file for copy-pasting into Claude Code windows
   - Each subtask has: CONTEXT, DEPENDENCIES, IMPLEMENTATION, VALIDATION
   - Integration testing prompt at the end

**3. FEATURE_1_MAXIMUM_PARALLEL_EXECUTION.md** (15KB)
   - Dependency graph analysis
   - 5-phase parallelization strategy
   - Window layout recommendations (3 monitors, 2 monitors, 1 ultrawide)
   - Time estimates and optimization strategies
   - Troubleshooting guide

---

### **📊 Tracking & Monitoring:**

**4. VISUAL_PROGRESS_TRACKER.md** (6.2KB)
   - Print this or display on second monitor
   - Real-time phase progress bars
   - Window status table
   - Completion waves timeline
   - Final validation checklist

**5. EXECUTION_DASHBOARD_TEMPLATE.md** (7.5KB)
   - Detailed tracking spreadsheet
   - Phase-by-phase tables with status/time tracking
   - Blocker/issue log
   - Notes section
   - File location quick reference

---

### **📚 Supporting Guides:**

**6. MAXIMUM_PARALLELIZATION_GUIDE.md** (12KB)
   - General parallelization philosophy
   - Multi-feature parallelization strategies
   - Tools for managing many windows (tmux, VS Code, etc.)
   - Monitoring and error handling strategies
   - Swarm mode (10+ features simultaneously)

**7. HOW_TO_USE_PROMPTS.md** (8.8KB)
   - Tutorial on parallel agent execution
   - Execution methods (sequential, parallel, micro-batch)
   - Model selection guide (Opus vs Sonnet vs Haiku)
   - Troubleshooting common issues
   - Feature execution order recommendations

**8. FEATURE_1_AUTH_PROMPTS.md** (7.2KB)
   - Medium-grained version (4 tracks instead of 29 subtasks)
   - Alternative if ultra-fine-grained is too detailed
   - Integration test checklist

---

## 🚀 Quick Start (3 Steps)

### **Step 1: Open Files**
```bash
# Main execution guide
open prompts/START_NOW_15_WINDOWS.md

# Prompt source (for copy-pasting)
open prompts/FEATURE_1_ULTRA_FINE_GRAINED.md

# Visual tracker (optional)
open prompts/VISUAL_PROGRESS_TRACKER.md
```

### **Step 2: Setup Windows**
- Open 15 Claude Code browser tabs
- Label them: 1.1.1, 1.1.2, ..., 1.4.8, BUFFER (x3)

### **Step 3: Execute Phase 1**
- Follow START_NOW_15_WINDOWS.md → Phase 1 → Step 1
- Copy 12 prompts from FEATURE_1_ULTRA_FINE_GRAINED.md
- Paste into windows 1-12
- Press Enter on all 12 within 30 seconds
- Wait ~12 minutes for completion

---

## 📊 File Sizes & Content

| File | Size | Subtasks | Est. Time |
|------|------|----------|-----------|
| FEATURE_1_ULTRA_FINE_GRAINED.md | 67KB | 29 | - |
| FEATURE_1_MAXIMUM_PARALLEL_EXECUTION.md | 15KB | - | - |
| START_NOW_15_WINDOWS.md | 11KB | - | 70 min total |
| MAXIMUM_PARALLELIZATION_GUIDE.md | 12KB | - | - |
| HOW_TO_USE_PROMPTS.md | 8.8KB | - | - |
| EXECUTION_DASHBOARD_TEMPLATE.md | 7.5KB | - | - |
| VISUAL_PROGRESS_TRACKER.md | 6.2KB | - | - |
| FEATURE_1_AUTH_PROMPTS.md | 7.2KB | 4 tracks | - |

---

## 🎯 What Each File Does

### **START_NOW_15_WINDOWS.md**
**Purpose:** Your step-by-step execution checklist
**When to use:** When you're ready to actually build Feature 1
**Key sections:**
- Window setup instructions
- Phase 1-5 execution steps with exact prompts to copy
- Time tracking template
- Emergency troubleshooting

### **FEATURE_1_ULTRA_FINE_GRAINED.md**
**Purpose:** The master prompt library
**When to use:** Reference while executing (copy prompts from here)
**Key sections:**
- Track 1.1: Database Models (9 subtasks)
- Track 1.2: Auth Utils (6 subtasks)
- Track 1.3: API Endpoints (7 subtasks)
- Track 1.4: Frontend Components (8 subtasks)
- Integration Testing (1 comprehensive prompt)

### **FEATURE_1_MAXIMUM_PARALLEL_EXECUTION.md**
**Purpose:** Strategy and theory behind the parallelization
**When to use:** Before starting, to understand the approach
**Key sections:**
- Dependency graph visualization
- Phase breakdown with parallelization map
- Window layout strategies
- Preparation checklist

### **VISUAL_PROGRESS_TRACKER.md**
**Purpose:** Real-time visual tracking
**When to use:** Print/display on second monitor during execution
**Key sections:**
- Time tracker table
- Phase progress bars (ASCII art)
- Window status grid
- Completion waves timeline

### **EXECUTION_DASHBOARD_TEMPLATE.md**
**Purpose:** Detailed tracking spreadsheet
**When to use:** For precise time/status tracking during execution
**Key sections:**
- Phase-by-phase tables with start/end times
- Blocker/issue log
- Notes section
- File location reference

### **MAXIMUM_PARALLELIZATION_GUIDE.md**
**Purpose:** General parallelization principles and tools
**When to use:** For advanced optimization or multi-feature builds
**Key sections:**
- Parallelization philosophy
- Tools (tmux, VS Code, multiple monitors)
- Multi-feature strategies
- Swarm mode (40+ windows)

### **HOW_TO_USE_PROMPTS.md**
**Purpose:** Tutorial on using the prompt system
**When to use:** First time using this system, or to learn alternatives
**Key sections:**
- Execution methods comparison
- Model selection guide
- Troubleshooting tips
- Feature execution order

### **FEATURE_1_AUTH_PROMPTS.md**
**Purpose:** Simplified medium-grained version
**When to use:** If 29 subtasks feels too granular
**Key sections:**
- 4 track prompts (instead of 29 subtasks)
- Integration test checklist

---

## 🗺️ Recommended Reading Order

**For first-time users:**
1. START_NOW_15_WINDOWS.md (skim to understand flow)
2. FEATURE_1_ULTRA_FINE_GRAINED.md (skim first subtask to see format)
3. VISUAL_PROGRESS_TRACKER.md (print or open on second monitor)
4. Then execute using START_NOW_15_WINDOWS.md

**For experienced users:**
1. START_NOW_15_WINDOWS.md
2. Execute immediately

**For understanding the system:**
1. HOW_TO_USE_PROMPTS.md
2. MAXIMUM_PARALLELIZATION_GUIDE.md
3. FEATURE_1_MAXIMUM_PARALLEL_EXECUTION.md

---

## 📝 Related Files (Outside This Folder)

**Root level:**
- `../PLAN.md` - Original high-level plan for all 8 features
- `../PROMPT_SYSTEM.md` - Medium-grained prompts for Features 1-8

**Docs folder:**
- `../docs/FEATURE_1_AUTH.md` - Feature 1 specification
- `../docs/QUICK_START.md` - General project quick start

---

## ⚡ Quick Reference Commands

**Check files exist:**
```bash
cd /path/to/therabridge-backend/prompts
ls -lh *.md
```

**Open all execution files:**
```bash
open START_NOW_15_WINDOWS.md
open FEATURE_1_ULTRA_FINE_GRAINED.md
open VISUAL_PROGRESS_TRACKER.md
```

**Search for specific subtask:**
```bash
grep -n "SUBTASK 1.3.4" FEATURE_1_ULTRA_FINE_GRAINED.md
```

---

## 🎓 Learning Path

**Beginner (First time with parallel execution):**
- Read: HOW_TO_USE_PROMPTS.md
- Start with: 3 windows (learning mode)
- Use: EXECUTION_DASHBOARD_TEMPLATE.md for tracking
- Time: ~2-3 hours

**Intermediate (Comfortable with Claude Code):**
- Read: START_NOW_15_WINDOWS.md
- Start with: 6 windows (comfortable mode)
- Use: VISUAL_PROGRESS_TRACKER.md for tracking
- Time: ~1.5 hours

**Advanced (Maximum speed):**
- Read: FEATURE_1_MAXIMUM_PARALLEL_EXECUTION.md
- Start with: 15 windows (maximum mode)
- Use: Both trackers
- Time: ~70 minutes

---

## 🔄 File Update Log

**Created:** December 16, 2024

**Files created in this session:**
1. FEATURE_1_ULTRA_FINE_GRAINED.md (29 subtasks)
2. FEATURE_1_MAXIMUM_PARALLEL_EXECUTION.md (parallelization strategy)
3. START_NOW_15_WINDOWS.md (execution guide)
4. VISUAL_PROGRESS_TRACKER.md (visual tracking)
5. EXECUTION_DASHBOARD_TEMPLATE.md (detailed tracking)
6. MAXIMUM_PARALLELIZATION_GUIDE.md (general principles)
7. HOW_TO_USE_PROMPTS.md (tutorial)
8. FEATURE_1_AUTH_PROMPTS.md (medium-grained alternative)
9. README.md (this file)

**Last verified:** December 16, 2024
**Total files:** 9
**Total size:** ~135KB

---

## 🎯 Next Steps After Feature 1

Once Feature 1 is complete, you can:

1. **Create similar ultra-fine-grained prompts for Features 2-8**
   - Use FEATURE_1_ULTRA_FINE_GRAINED.md as template
   - Follow same subtask structure
   - Analyze dependencies for each feature

2. **Build multiple features in parallel**
   - Use MAXIMUM_PARALLELIZATION_GUIDE.md → Swarm Mode
   - Run Features 1, 6, 8 simultaneously (different complexity)

3. **Optimize your window setup**
   - Document what worked best for you
   - Adjust phase timings based on actual performance

---

**Ready to start?** Open `START_NOW_15_WINDOWS.md` and begin! 🚀
