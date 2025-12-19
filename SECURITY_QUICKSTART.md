# Security Quickstart Guide

**5-minute setup to prevent credential leaks and security issues**

## Quick Setup

```bash
# 1. Run the setup script (from repository root)
./scripts/setup-pre-commit.sh

# 2. Test it works
git add .
git commit -m "Test pre-commit hooks"

# 3. If hooks block your commit, you're protected! ✅
```

## What You Get

✅ **Automatic secret scanning** - Blocks commits with API keys, passwords, tokens
✅ **Large file prevention** - No more accidental 1GB file uploads
✅ **Private key detection** - SSH keys and certificates stay out of git
✅ **Branch protection** - Can't commit directly to main/master
✅ **Code formatting** - Auto-format Python (Black) and frontend (Prettier)

## Common Commands

```bash
# Run all hooks manually
pre-commit run --all-files

# Update hooks to latest versions
pre-commit autoupdate

# Skip hooks (EMERGENCY ONLY)
git commit --no-verify -m "Emergency fix"

# Check specific file
pre-commit run --files backend/app/config.py
```

## What Gets Blocked

❌ API keys (OpenAI, AWS, Stripe, etc.)
❌ Database credentials
❌ Private SSH/TLS keys
❌ Hardcoded passwords
❌ JWT secrets
❌ Large files (>1MB)
❌ Direct commits to main branch

## Example: Blocked Commit

```bash
$ git commit -m "Add database config"

Detect secrets...Failed
- hook id: detect-secrets
- exit code: 1

backend/config.py:
  Line 10: DATABASE_URL=postgresql://user:password@...

❌ Credential detected! Remove or add to .secrets.baseline
```

## How to Fix

### 1. Remove the secret
```bash
# Use environment variable instead
DATABASE_URL=os.environ.get("DATABASE_URL")
```

### 2. Add to .env (gitignored)
```bash
echo "DATABASE_URL=postgresql://..." >> backend/.env
```

### 3. Update .env.example (template only)
```bash
echo "DATABASE_URL=your_database_url_here" >> backend/.env.example
```

### 4. Commit safely
```bash
git add backend/config.py backend/.env.example
git commit -m "Use env vars for database config"
```

## False Positives

If detect-secrets flags example code or documentation:

```bash
# Update baseline (marks as safe)
detect-secrets scan --baseline .secrets.baseline

# Review changes
git diff .secrets.baseline

# Commit updated baseline
git add .secrets.baseline
git commit -m "Update secrets baseline for docs examples"
```

## Need Help?

📖 **Full documentation:** `.github/SECURITY.md`
🔒 **Production security:** `backend/SECURITY.md`
📧 **Security team:** security@therapybridge.com

## Emergency: Secret Already Committed

1. **Stop** - Don't push to remote if possible
2. **Rotate** - Immediately revoke/change the credential
3. **Remove from history:**
   ```bash
   # Amend last commit (if not pushed)
   git commit --amend

   # OR reset (if not pushed)
   git reset --soft HEAD^
   ```
4. **If already pushed** - Contact security@therapybridge.com immediately

## Pro Tips

💡 Use `.env.example` files for templates (no real secrets)
💡 Generate secure secrets: `openssl rand -base64 32`
💡 Review changes before commit: `git diff --staged`
💡 Stage specific files: `git add path/to/file.py` (avoid `git add .`)
💡 Keep credentials in password manager, not in code

---

**Remember:** Pre-commit hooks are your first line of defense. If they block something, there's usually a good reason! 🛡️
