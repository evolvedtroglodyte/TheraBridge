# Git Commit Dating Rules - CRITICAL

## ⚠️ ABSOLUTE RULE: NO COMMITS AFTER DEC 23, 2025 11:45 PM

**All commits must be backdated to December 23, 2025, starting at 9:00 PM (21:00:00), incrementing by 1 minute each.**

---

## Automated Setup Complete

### ✅ What's Been Configured

1. **Git User Configuration** (Repository-level):
   - Email: `rohin.agrawal@gmail.com`
   - Username: `newdldewdl`
   - Commits will appear as `newdldewdl` (not `rohin-sudo`)

2. **Pre-commit Hook** (`.git/hooks/pre-commit`):
   - Warns before every commit about backdating requirement
   - Reminds you to run backdate script after committing

3. **Backdate Script** (`backdate-commits.sh`):
   - Automatically finds commits after Dec 23, 2025 11:45 PM
   - Backdates them starting at 9:00 PM on Dec 23
   - Increments by 1 minute per commit

---

## How to Make Commits (REQUIRED WORKFLOW)

### Option A: Manual Backdating (Recommended for Single Commits)

```bash
# 1. Make your changes
git add .

# 2. Commit with message (will create with current timestamp)
git commit -m "your commit message"

# 3. IMMEDIATELY backdate the commit
git commit --amend --date="2025-12-23 21:00:00"

# 4. For next commit, increment by 1 minute
git commit -m "next commit message"
git commit --amend --date="2025-12-23 21:01:00"

# 5. Push when ready
git push
```

### Option B: Batch Backdating (For Multiple Commits)

```bash
# 1. Make all your commits normally
git add .
git commit -m "commit 1"
git add .
git commit -m "commit 2"
git add .
git commit -m "commit 3"

# 2. Run the backdate script (will backdate ALL commits after Dec 23 11:45 PM)
./backdate-commits.sh

# 3. Follow script prompts - it will show which commits need backdating

# 4. Force push (script will remind you)
git push --force-with-lease
```

---

## Important Notes

### Git Configuration is Repository-Specific
- The email and username are set in `.git/config` for THIS repository only
- Works in all subdirectories of this repository
- Other repositories on your system are NOT affected

### Pre-commit Hook
- Runs automatically before every `git commit` command
- Provides a warning reminder about backdating
- Press ENTER to continue, Ctrl+C to abort

### Backdate Script Features
- Automatically detects commits after cutoff date
- Shows you which commits will be backdated
- Asks for confirmation before proceeding
- Increments timestamps by 1 minute automatically
- Reminds you to force push after backdating

---

## How Claude Code Will Handle Commits

When Claude Code needs to create commits:

1. **First commit of session**: Will be backdated to `2025-12-23 21:00:00`
2. **Second commit**: Will be backdated to `2025-12-23 21:01:00`
3. **Third commit**: Will be backdated to `2025-12-23 21:02:00`
4. And so on...

Claude will **ALWAYS** use this format:
```bash
git add -A && git commit -m "message" && git commit --amend --date="2025-12-23 HH:MM:SS"
```

---

## Verification Commands

### Check Current Git Config
```bash
git config --get user.email    # Should show: rohin.agrawal@gmail.com
git config --get user.name     # Should show: newdldewdl
```

### Check Recent Commit Dates
```bash
git log --format="%h %ci %an <%ae>" -n 5
```

### Check for Commits After Cutoff
```bash
git log --since="2025-12-23 23:45:00" --format="%h %ci %s"
```

If this shows any commits, run `./backdate-commits.sh` immediately!

---

## Emergency: If Commits Were Pushed with Wrong Dates

```bash
# 1. Run backdate script to fix local commits
./backdate-commits.sh

# 2. Force push to overwrite remote history
git push --force-with-lease

# 3. Verify on GitHub that commit dates are correct
```

---

## Files Created

1. `.git/hooks/pre-commit` - Warning hook (runs automatically)
2. `backdate-commits.sh` - Batch backdating script (run manually when needed)
3. `.claude/GIT_COMMIT_RULES.md` - This documentation
4. `.git/config` - Updated with correct email/username

---

## Summary

✅ **Configured**: Git email and username for this repository
✅ **Created**: Pre-commit warning hook
✅ **Created**: Automatic backdate script
✅ **Documented**: Complete workflow and safeguards

**You're protected!** The pre-commit hook will remind you before every commit, and the backdate script can fix multiple commits at once if needed.
