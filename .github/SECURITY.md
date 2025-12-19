# Security Policy - Development & Credential Protection

## Overview

This document provides security guidelines for developers working on TherapyBridge. It focuses on preventing credential leaks, securing the development environment, and maintaining secure coding practices.

**For production security features (HIPAA compliance, MFA, encryption):** See `/backend/SECURITY.md`

**Last Updated:** 2025-12-18

---

## Table of Contents

1. [Pre-commit Hooks Setup](#pre-commit-hooks-setup)
2. [Credential Management](#credential-management)
3. [Environment Variables](#environment-variables)
4. [Git Security Best Practices](#git-security-best-practices)
5. [Reporting Security Issues](#reporting-security-issues)

---

## Pre-commit Hooks Setup

Pre-commit hooks automatically scan your code for secrets, credentials, and security issues **before** they are committed to git history.

### Quick Start

```bash
# Install pre-commit (one-time setup)
pip install pre-commit

# Install the git hook scripts (run from repository root)
cd /path/to/peerbridge-proj
pre-commit install

# Test the hooks on all files
pre-commit run --all-files
```

### Recommended Configuration

Create `.pre-commit-config.yaml` in the repository root:

```yaml
# Pre-commit hooks for security and code quality
# See https://pre-commit.com for more information

repos:
  # Detect hardcoded secrets, passwords, API keys
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args:
          - '--baseline'
          - '.secrets.baseline'
          - '--exclude-files'
          - '\.secrets\.baseline$'
          - '--exclude-files'
          - 'package-lock\.json$'
          - '--exclude-files'
          - 'poetry\.lock$'
        exclude: |
          (?x)^(
              .*\.ipynb|
              .*\.min\.js|
              backend/tests/.*|
              frontend/node_modules/.*
          )$

  # Prevent committing to main branch
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: check-added-large-files
        args: ['--maxkb=1000']
      - id: check-case-conflict
      - id: check-merge-conflict
      - id: check-yaml
        exclude: '^frontend/.*\.yaml$'  # Some frontend yamls may have templates
      - id: check-json
      - id: detect-private-key
      - id: end-of-file-fixer
      - id: trailing-whitespace
      - id: no-commit-to-branch
        args: ['--branch', 'main', '--branch', 'master']

  # Python-specific checks
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3.13
        files: '^(backend|audio-transcription-pipeline|Scrapping)/.*\.py$'

  # Detect AWS credentials
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: detect-aws-credentials
        args: ['--allow-missing-credentials']

  # Prettier for frontend code formatting
  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v3.1.0
    hooks:
      - id: prettier
        files: '^frontend/.*\.(ts|tsx|js|jsx|json|css|md)$'
        exclude: '^frontend/(node_modules|.next)/.*$'
```

### Setting Up detect-secrets

`detect-secrets` is the primary tool for preventing credential leaks.

#### Installation

```bash
# Install detect-secrets
pip install detect-secrets

# OR use pipx for isolated installation
pipx install detect-secrets
```

#### Creating a Baseline

The baseline file tells detect-secrets which "secrets" are false positives (like example keys in documentation).

```bash
# Generate initial baseline (run from repository root)
detect-secrets scan --baseline .secrets.baseline

# Review the baseline file
cat .secrets.baseline

# Add baseline to git
git add .secrets.baseline
git commit -m "Add detect-secrets baseline"
```

#### Updating the Baseline

When you intentionally add a new false positive (e.g., example API key in documentation):

```bash
# Update baseline with new findings
detect-secrets scan --baseline .secrets.baseline

# Review changes
git diff .secrets.baseline

# Commit updated baseline
git add .secrets.baseline
git commit -m "Update secrets baseline"
```

#### Auditing Detected Secrets

```bash
# Interactively audit all detected secrets
detect-secrets audit .secrets.baseline

# Mark secrets as real (r) or false positive (n)
# Press 'r' for real secret (blocks commit)
# Press 'n' for false positive (allows commit)
# Press 's' to skip
```

### What Gets Detected

detect-secrets scans for:

- **API Keys:** AWS, OpenAI, Stripe, SendGrid, etc.
- **Passwords:** Hardcoded passwords in code
- **Private Keys:** SSH keys, TLS certificates, JWT secrets
- **Tokens:** OAuth tokens, session tokens, access tokens
- **Database URLs:** Connection strings with credentials
- **High Entropy Strings:** Random-looking strings that might be secrets

### Example: Blocked Commit

```bash
$ git commit -m "Add OpenAI integration"

Detect secrets...................................................Failed
- hook id: detect-secrets
- exit code: 1

ERROR: Potential secrets detected!

backend/.env:
  Line 15: OPENAI_API_KEY=sk-proj-abc123...

Please remove secrets or update .secrets.baseline if this is a false positive.
```

### Bypassing Pre-commit Hooks (Emergency Only)

```bash
# Skip ALL pre-commit hooks (use with extreme caution)
git commit --no-verify -m "Emergency fix"

# Better: Skip specific hook
SKIP=detect-secrets git commit -m "Intentional secret for testing"
```

**WARNING:** Only bypass hooks if you understand the security implications.

---

## Credential Management

### Golden Rules

1. **NEVER commit credentials to git** - Use environment variables
2. **NEVER share .env files** - Each developer creates their own
3. **NEVER hardcode secrets in code** - Use config files or env vars
4. **ALWAYS use .env.example templates** - Document required variables
5. **ALWAYS rotate credentials if leaked** - Assume compromise immediately

### Environment File Hierarchy

```
Project Root
├── .env                           # ❌ NEVER commit (in .gitignore)
├── .env.example                   # ✅ Commit (template only)
│
├── backend/
│   ├── .env                       # ❌ NEVER commit
│   └── .env.example               # ✅ Commit
│
├── frontend/
│   ├── .env.local                 # ❌ NEVER commit
│   └── .env.local.example         # ✅ Commit
│
└── audio-transcription-pipeline/
    ├── .env                       # ❌ NEVER commit
    └── .env.example               # ✅ Commit
```

### Creating Safe .env.example Files

```bash
# Bad - contains real secret
OPENAI_API_KEY=sk-proj-abc123def456...

# Good - placeholder only
OPENAI_API_KEY=your_openai_api_key_here

# Better - with description
OPENAI_API_KEY=your_openai_api_key_here  # Get from https://platform.openai.com/api-keys
```

### Rotating Compromised Credentials

If credentials are accidentally committed:

1. **Immediately revoke/rotate the credential**
   - OpenAI: Delete API key at https://platform.openai.com/api-keys
   - AWS: Delete access key in IAM console
   - Database: Change password immediately

2. **Remove from git history** (if not pushed)
   ```bash
   # Amend last commit
   git commit --amend

   # OR reset to previous commit
   git reset --soft HEAD^
   ```

3. **If already pushed to remote:**
   ```bash
   # Contact repository administrator
   # Credential is now public - rotation is mandatory

   # Use git-filter-repo to rewrite history (destructive)
   pip install git-filter-repo
   git filter-repo --path backend/.env --invert-paths
   git push --force
   ```

4. **Verify removal:**
   ```bash
   # Search git history for secret
   git log -p | grep "sk-proj-abc123"
   ```

5. **Update documentation** - Add to incident log

---

## Environment Variables

### Backend (.env)

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/therapybridge

# Authentication
JWT_SECRET_KEY=generate_with_openssl_rand_base64_32
JWT_REFRESH_SECRET_KEY=generate_with_openssl_rand_base64_32
ENCRYPTION_MASTER_KEY=generate_with_fernet_key_gen

# External APIs
OPENAI_API_KEY=your_openai_api_key
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_S3_BUCKET_NAME=your_bucket_name
AWS_REGION=us-east-1

# Email (choose one)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_specific_password

SENDGRID_API_KEY=your_sendgrid_api_key
SENDGRID_FROM_EMAIL=noreply@therapybridge.com

# Security
CORS_ORIGINS=http://localhost:3000,https://therapybridge.com
SECURITY_HSTS_ENABLED=false  # true in production

# Feature flags
ENABLE_EMAIL_VERIFICATION=false
ENABLE_MFA=true
```

#### Generating Secure Secrets

```bash
# JWT secrets (base64 encoded random bytes)
openssl rand -base64 32

# Fernet encryption key (for ENCRYPTION_MASTER_KEY)
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Random hex string
openssl rand -hex 32
```

### Frontend (.env.local)

```bash
# Backend API
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

# Feature flags
NEXT_PUBLIC_USE_REAL_API=false
NEXT_PUBLIC_ENABLE_ANALYTICS=false

# Third-party services (optional)
NEXT_PUBLIC_SENTRY_DSN=your_sentry_dsn
NEXT_PUBLIC_GOOGLE_ANALYTICS_ID=your_ga_id
```

### Audio Pipeline (.env)

```bash
# OpenAI API
OPENAI_API_KEY=your_openai_api_key

# HuggingFace (for speaker diarization)
HF_TOKEN=your_huggingface_token

# Paths
AUDIO_INPUT_DIR=/path/to/audio/files
AUDIO_OUTPUT_DIR=/path/to/output
```

### Environment Variable Security Checklist

- [ ] All .env files are in .gitignore
- [ ] All .env.example files have placeholder values (no real secrets)
- [ ] All required variables are documented in .env.example
- [ ] Production secrets use secure random generation (not "changeme")
- [ ] Database credentials are unique per environment (dev/staging/prod)
- [ ] API keys have appropriate scopes/permissions (principle of least privilege)
- [ ] Secrets are rotated regularly (quarterly for production)
- [ ] Secrets are stored in secure vaults in production (AWS Secrets Manager, etc.)

---

## Git Security Best Practices

### Before Every Commit

```bash
# 1. Review changes
git diff

# 2. Check for accidental inclusions
git status

# 3. Look for credentials in staged files
git diff --cached | grep -iE '(password|secret|api_key|token)'

# 4. Commit with descriptive message
git commit -m "Add OpenAI integration (uses env var)"
```

### Committing Safely

```bash
# Stage specific files only (avoid git add .)
git add backend/app/services/openai_service.py
git add backend/app/routers/ai_router.py

# Review what will be committed
git diff --staged

# Commit
git commit -m "Add OpenAI service for AI extraction"
```

### Avoid Common Pitfalls

```bash
# ❌ DON'T: Add everything
git add .
git add -A

# ✅ DO: Add specific files
git add backend/app/services/new_feature.py

# ❌ DON'T: Commit large files
git add uploads/audio/session_1gb.mp3

# ✅ DO: Use .gitignore
echo "uploads/audio/*.mp3" >> .gitignore

# ❌ DON'T: Commit sensitive logs
git add logs/production.log

# ✅ DO: Exclude logs
echo "logs/*.log" >> .gitignore
```

### Checking Git History for Secrets

```bash
# Search all history for potential secrets
git log -p | grep -iE '(password|secret|api_key|token|sk-proj|sk-|AKIA)'

# Search specific file history
git log -p -- backend/.env

# Use git-secrets tool (GitHub's tool)
git clone https://github.com/awslabs/git-secrets.git
cd git-secrets
make install
cd /path/to/peerbridge-proj
git secrets --install
git secrets --scan
```

### Cleaning Git History (If Secrets Leaked)

**WARNING:** These commands rewrite history and require force push. Coordinate with team first.

```bash
# Option 1: BFG Repo-Cleaner (fastest)
# Download from https://rtyley.github.io/bfg-repo-cleaner/
java -jar bfg.jar --delete-files .env
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Option 2: git-filter-repo (most thorough)
pip install git-filter-repo
git filter-repo --path backend/.env --invert-paths
git filter-repo --replace-text <(echo "sk-proj-LEAKED_KEY==>***REMOVED***")

# Force push (DANGEROUS - warn team first)
git push --force --all
git push --force --tags
```

---

## Reporting Security Issues

### Vulnerability Disclosure

If you discover a security vulnerability:

1. **DO NOT create a public GitHub issue**
2. **DO NOT discuss in public channels (Slack, Discord, etc.)**
3. **DO** email security@therapybridge.com with:
   - Description of vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if known)

### Response Timeline

- **Acknowledgment:** Within 24 hours
- **Initial Assessment:** Within 72 hours
- **Fix Development:** 7-30 days (depending on severity)
- **Disclosure:** After fix is deployed

### Severity Levels

| Severity | Description | Examples | Response Time |
|----------|-------------|----------|---------------|
| **Critical** | Remote code execution, data breach | SQL injection, authentication bypass | 24 hours |
| **High** | Privilege escalation, PII exposure | XSS, CSRF, session hijacking | 72 hours |
| **Medium** | Information disclosure, DoS | Error messages revealing internals | 7 days |
| **Low** | Minor issues, configuration problems | Missing security headers | 30 days |

### Security Contacts

- **General Security:** security@therapybridge.com
- **HIPAA Compliance:** compliance@therapybridge.com
- **Emergency (Critical Issues):** 1-800-XXX-XXXX (24/7)

---

## Additional Security Tools

### Static Analysis

```bash
# Python: Bandit (security linter)
pip install bandit
bandit -r backend/app/

# Python: Safety (dependency vulnerability scanner)
pip install safety
safety check --file backend/requirements.txt

# JavaScript/TypeScript: npm audit
cd frontend
npm audit
npm audit fix
```

### Dependency Scanning

```bash
# Snyk (multi-language vulnerability scanner)
npm install -g snyk
snyk auth
snyk test

# OWASP Dependency-Check
dependency-check --project TherapyBridge --scan backend/
```

### Secret Scanning Services

**GitHub Secret Scanning** (automatic for public repos)
- Detects common secret patterns
- Notifies repository admins
- Free for public repos, included in GitHub Advanced Security

**GitGuardian** (real-time secret detection)
```bash
# Install GitGuardian CLI
pip install ggshield

# Scan repository
ggshield secret scan repo .
```

**TruffleHog** (deep git history scanning)
```bash
# Install
pip install truffleHog

# Scan entire repository history
trufflehog --regex --entropy=True https://github.com/yourorg/peerbridge.git
```

---

## CI/CD Security Checks

### GitHub Actions Workflow

Create `.github/workflows/security.yml`:

```yaml
name: Security Checks

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  secrets-scan:
    name: Scan for secrets
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Full history for secret scanning

      - name: Install detect-secrets
        run: pip install detect-secrets

      - name: Scan for secrets
        run: |
          detect-secrets scan --baseline .secrets.baseline
          detect-secrets audit .secrets.baseline

  dependency-scan:
    name: Scan dependencies
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run Snyk
        uses: snyk/actions/python-3.10@master
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
        with:
          args: --severity-threshold=high

  static-analysis:
    name: Static analysis
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run Bandit
        run: |
          pip install bandit
          bandit -r backend/app/ -f json -o bandit-report.json

      - name: Upload results
        uses: actions/upload-artifact@v4
        with:
          name: bandit-report
          path: bandit-report.json
```

---

## Security Checklist for Pull Requests

Before submitting a PR:

- [ ] Pre-commit hooks passed locally
- [ ] No credentials in code or config files
- [ ] All secrets use environment variables
- [ ] .env files not committed (check `git status`)
- [ ] .env.example updated with new variables (if any)
- [ ] No debug code or console.logs with sensitive data
- [ ] No commented-out code with credentials
- [ ] Dependencies updated (no known vulnerabilities)
- [ ] Tests pass (including security tests)
- [ ] Code reviewed for SQL injection, XSS, CSRF risks
- [ ] Authentication/authorization checks in place
- [ ] Input validation implemented
- [ ] Error messages don't leak sensitive info

---

## Resources

### Official Documentation

- [detect-secrets](https://github.com/Yelp/detect-secrets)
- [pre-commit](https://pre-commit.com/)
- [git-secrets](https://github.com/awslabs/git-secrets)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [HIPAA Security Rule](https://www.hhs.gov/hipaa/for-professionals/security/index.html)

### Tools

- [GitGuardian](https://www.gitguardian.com/)
- [TruffleHog](https://github.com/trufflesecurity/trufflehog)
- [Snyk](https://snyk.io/)
- [Bandit](https://bandit.readthedocs.io/)
- [BFG Repo-Cleaner](https://rtyley.github.io/bfg-repo-cleaner/)

### Training

- [GitHub Security Lab](https://securitylab.github.com/)
- [OWASP WebGoat](https://owasp.org/www-project-webgoat/)
- [AWS Security Best Practices](https://aws.amazon.com/security/best-practices/)

---

**Document Version:** 1.0
**Last Updated:** 2025-12-18
**Next Review:** 2026-01-18
**Owner:** Security Team
