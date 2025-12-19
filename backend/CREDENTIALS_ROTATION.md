# Credentials Rotation Guide

## CRITICAL SECURITY NOTICE

**All credentials in this repository have been exposed in version control and MUST be rotated immediately.**

The following `.env` files were committed to the git repository with active credentials:
- `backend/.env` - Backend API configuration
- `audio-transcription-pipeline/.env` - Audio processing pipeline configuration

**Git history preserves these credentials indefinitely.** Even after rotation, the old credentials remain visible in commit history. Consider this repository compromised until all credentials are rotated.

---

## Exposed Credentials Inventory

### 1. OpenAI API Key

**Location:**
- `backend/.env` (line 27)
- `audio-transcription-pipeline/.env` (line 7)

**Exposed Value Pattern:** `sk-proj-EjcOnpeQb9dmtoq0BxMF...`

**Risk Level:** HIGH
- Unauthorized usage can incur significant API charges
- Access to GPT-4o model for note extraction
- Could be used to process sensitive patient data through your account

**Rotation Instructions:**

1. **Immediately revoke the exposed key:**
   - Visit: https://platform.openai.com/api-keys
   - Login to your OpenAI account
   - Find the exposed key (starts with `sk-proj-EjcOnpeQb9dmtoq0BxMF`)
   - Click the trash icon or "Revoke" button
   - Confirm revocation

2. **Generate a new API key:**
   - On the same page, click "Create new secret key"
   - Name it descriptively (e.g., "TherapyBridge Backend - Production")
   - Copy the key immediately (it won't be shown again)
   - Store it securely (see "Secure Storage Recommendations" below)

3. **Update application configuration:**
   - Update `backend/.env` (line 27): `OPENAI_API_KEY=<new-key>`
   - Update `audio-transcription-pipeline/.env` (line 7): `OPENAI_API_KEY=<new-key>`
   - DO NOT commit these changes to git
   - Ensure `.env` is in `.gitignore`

4. **Verify the rotation:**
   - Restart backend server: `cd backend && uvicorn app.main:app --reload`
   - Test AI note extraction endpoint
   - Check OpenAI dashboard for recent API usage with new key

**Dashboard:** https://platform.openai.com/usage

---

### 2. Neon PostgreSQL Database Password

**Location:**
- `backend/.env` (line 14) - in `DATABASE_URL` connection string
- `audio-transcription-pipeline/.env` (line 23) - in `DATABASE_URL` connection string

**Exposed Value Pattern:** `postgresql://neondb_owner:npg_o7Bwa8JNmtyU@ep-withered-frost-ahsas8wd-pooler...`

**Risk Level:** CRITICAL
- Direct access to production database containing Protected Health Information (PHI)
- HIPAA compliance violation if patient data is accessed
- Potential for data exfiltration, modification, or deletion
- Database contains therapist accounts, patient records, session transcripts, and clinical notes

**Rotation Instructions:**

1. **Reset database password:**
   - Visit: https://console.neon.tech
   - Login to your Neon account
   - Navigate to your project: `ep-withered-frost-ahsas8wd`
   - Go to "Settings" → "Reset password"
   - Generate a new password (copy it immediately)
   - Alternative: Use Neon CLI: `neonctl connection-string --password-only`

2. **Update connection strings:**
   - Format: `postgresql://neondb_owner:<NEW_PASSWORD>@ep-withered-frost-ahsas8wd-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require`
   - Update `backend/.env` (line 14): `DATABASE_URL=<new-connection-string>`
   - Update `audio-transcription-pipeline/.env` (line 23): `DATABASE_URL=<new-connection-string>`
   - DO NOT commit these changes to git

3. **Test database connectivity:**
   ```bash
   cd backend
   source venv/bin/activate
   python -c "from app.database import engine; engine.connect(); print('Database connection successful')"
   ```

4. **Update all deployment environments:**
   - Development environment variables
   - Staging environment (if applicable)
   - Production deployment configuration
   - CI/CD pipeline secrets
   - Team member local `.env` files

**Dashboard:** https://console.neon.tech/app/projects/ep-withered-frost-ahsas8wd

---

### 3. HuggingFace Token

**Location:**
- `audio-transcription-pipeline/.env` (line 17)

**Exposed Value Pattern:** `hf_lfmUbZedBlPUSPAwHUQ...`

**Risk Level:** MEDIUM
- Access to download pyannote speaker diarization models
- Could be used to access private HuggingFace repositories
- Potential for unauthorized model downloads or API usage

**Rotation Instructions:**

1. **Revoke the exposed token:**
   - Visit: https://huggingface.co/settings/tokens
   - Login to your HuggingFace account
   - Find the exposed token (starts with `hf_lfmUbZedBlPUSPAwHUQ`)
   - Click "Manage" → "Delete" or revoke the token
   - Confirm deletion

2. **Generate a new token:**
   - On the same page, click "New token"
   - Name: "TherapyBridge Audio Pipeline"
   - Role: Select "Read" (sufficient for model downloads)
   - Click "Generate token"
   - Copy the token immediately

3. **Ensure model access is granted:**
   - Visit: https://huggingface.co/pyannote/speaker-diarization-3.1
   - Click "Agree and access repository" (if not already done)
   - Repeat for: https://huggingface.co/pyannote/segmentation-3.0

4. **Update application configuration:**
   - Update `audio-transcription-pipeline/.env` (line 17): `HF_TOKEN=<new-token>`
   - DO NOT commit this change to git

5. **Verify the rotation:**
   ```bash
   cd audio-transcription-pipeline
   source venv/bin/activate
   python -c "from pyannote.audio import Pipeline; Pipeline.from_pretrained('pyannote/speaker-diarization-3.1'); print('HuggingFace token valid')"
   ```

**Dashboard:** https://huggingface.co/settings/tokens

---

### 4. Vast.ai API Key

**Location:**
- `audio-transcription-pipeline/.env` (line 26)

**Exposed Value Pattern:** `3bc8f2a123265fa1bde15a9f1ca891ddc31a18280d787cdd62f840c9b9c141fc`

**Risk Level:** HIGH
- Unauthorized GPU instance provisioning (charged per second)
- Potential for expensive compute abuse
- Access to your Vast.ai account balance

**Rotation Instructions:**

1. **Revoke the exposed API key:**
   - Visit: https://cloud.vast.ai/account
   - Login to your Vast.ai account
   - Navigate to "API Keys" section
   - Find the exposed key (ending in `...b9c141fc`)
   - Click "Delete" or "Revoke"
   - Confirm deletion

2. **Generate a new API key:**
   - On the same page, click "Create New API Key"
   - Name it descriptively (e.g., "TherapyBridge GPU Pipeline")
   - Copy the key immediately

3. **Update application configuration:**
   - Update `audio-transcription-pipeline/.env` (line 26): `VAST_API_KEY=<new-key>`
   - DO NOT commit this change to git

4. **Verify the rotation:**
   ```bash
   cd audio-transcription-pipeline
   source venv/bin/activate
   python -c "import requests; r = requests.get('https://console.vast.ai/api/v0/machines', headers={'Authorization': 'Bearer <new-key>'}); print('Vast.ai API key valid' if r.status_code == 200 else 'Invalid key')"
   ```

5. **Check for unauthorized usage:**
   - Review recent billing history for unexpected charges
   - Check instance provisioning logs for unauthorized activity
   - Monitor for active instances you didn't create

**Dashboard:** https://cloud.vast.ai/account

---

### 5. JWT Secret Key

**Location:**
- `backend/.env` (line 42)

**Exposed Value:** `dev-secret-key-not-for-production-8a7f3e2d9c1b4a6e5f8d7c3b2a1e9f4d`

**Risk Level:** CRITICAL
- Allows forging of authentication tokens for any user
- Complete bypass of authentication system
- Unauthorized access to all therapist and patient accounts
- Ability to impersonate any user in the system

**Rotation Instructions:**

1. **Generate a new cryptographically secure secret:**
   ```bash
   openssl rand -hex 32
   ```
   Copy the output (64-character hexadecimal string)

2. **Update application configuration:**
   - Update `backend/.env` (line 42): `JWT_SECRET_KEY=<new-secret>`
   - DO NOT commit this change to git

3. **Understand the impact:**
   - **All existing JWT tokens will be invalidated immediately**
   - All logged-in users will be logged out
   - Users must re-authenticate with email/password
   - Refresh tokens will also be invalidated

4. **Coordinate the rotation:**
   - Schedule during low-traffic period if in production
   - Notify users of upcoming forced logout (if applicable)
   - Ensure support team is ready for "can't login" issues

5. **Update all deployment environments:**
   - Development: Update `.env`
   - Staging: Update environment variables
   - Production: Update secrets manager/environment config
   - Restart all backend instances after updating

6. **Verify the rotation:**
   ```bash
   cd backend
   source venv/bin/activate
   uvicorn app.main:app --reload
   # Test login endpoint - should receive new token
   # Old tokens should be rejected with 401 Unauthorized
   ```

**Note:** This is the only credential that doesn't require a third-party dashboard rotation. The secret is self-managed.

---

## Secure Storage Recommendations

**NEVER commit credentials to version control.** Use one of these alternatives:

### Option 1: Environment Variables (Recommended for Production)

**AWS Systems Manager Parameter Store:**
```bash
aws ssm put-parameter \
  --name "/therapybridge/prod/openai-api-key" \
  --value "sk-proj-..." \
  --type "SecureString"
```

**Vercel Environment Variables:**
- Project Settings → Environment Variables
- Add secrets per environment (Development, Preview, Production)

**Heroku Config Vars:**
```bash
heroku config:set OPENAI_API_KEY=sk-proj-...
```

### Option 2: Secrets Manager (Enterprise)

**AWS Secrets Manager:**
```bash
aws secretsmanager create-secret \
  --name therapybridge/production \
  --secret-string '{"DATABASE_URL":"postgresql://...","OPENAI_API_KEY":"sk-proj-..."}'
```

**Google Cloud Secret Manager:**
```bash
echo -n "sk-proj-..." | gcloud secrets create openai-api-key --data-file=-
```

### Option 3: Local Development with .env Files

**CRITICAL: Ensure `.env` is gitignored:**

```bash
# Add to .gitignore (already done in this repo)
**/.env
**/.env.local
**/.env.*.local
!**/.env.example
```

**Use `.env.example` templates:**
- Create `.env.example` with dummy values
- Commit `.env.example` to version control
- Never commit actual `.env` files
- Share rotation instructions, not credentials

---

## Post-Rotation Checklist

After rotating all credentials, complete these steps:

- [ ] All 5 credentials rotated and tested
- [ ] Old credentials confirmed revoked on service dashboards
- [ ] Application tested with new credentials (backend, frontend, pipeline)
- [ ] All deployment environments updated (dev, staging, prod)
- [ ] Team members notified to update local `.env` files
- [ ] CI/CD pipeline secrets updated
- [ ] `.env` files confirmed in `.gitignore`
- [ ] No credentials in git history going forward
- [ ] Monitoring dashboards checked for unauthorized usage
- [ ] Documentation updated with rotation date

**Document rotation completion:**
```
Credentials rotated on: [DATE]
Rotated by: [NAME]
Affected services: OpenAI, Neon, HuggingFace, Vast.ai, JWT
Verification completed: [✓/✗]
```

---

## Prevention: Preventing Future Credential Exposure

### 1. Pre-Commit Hooks

Install `detect-secrets` to prevent credential commits:

```bash
pip install detect-secrets
detect-secrets scan --baseline .secrets.baseline
detect-secrets audit .secrets.baseline
```

Add to `.git/hooks/pre-commit`:
```bash
#!/bin/bash
detect-secrets scan --baseline .secrets.baseline
if [ $? -ne 0 ]; then
  echo "❌ Credentials detected! Commit blocked."
  exit 1
fi
```

### 2. GitHub Secret Scanning

**Enable for this repository:**
- Settings → Security → Code security and analysis
- Enable "Secret scanning"
- Enable "Push protection" (blocks commits with secrets)

### 3. Regular Credential Audits

**Monthly checklist:**
- [ ] Review all `.env.example` files for dummy values only
- [ ] Scan codebase for hardcoded credentials: `grep -r "sk-" --exclude-dir=venv`
- [ ] Check git history for accidental commits: `git log -p | grep -i "password\|secret\|api.key"`
- [ ] Rotate credentials quarterly as best practice

### 4. Team Training

**Onboarding checklist for new developers:**
- [ ] Never commit `.env` files
- [ ] Always use `.env.example` templates
- [ ] Store production credentials in secrets manager only
- [ ] Report accidental commits immediately (even if caught before push)
- [ ] Understand that git history preserves everything forever

---

## Incident Response Contact

**If you discover additional exposed credentials:**

1. **Immediately rotate** the exposed credential
2. **Document** the exposure in this file
3. **Notify** the team lead and security officer
4. **Review** access logs for unauthorized usage
5. **Update** the post-rotation checklist

**Security Contact:** [Add your security team contact here]

---

## Additional Resources

- [OWASP Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [GitHub Secret Scanning Documentation](https://docs.github.com/en/code-security/secret-scanning)
- [AWS Secrets Manager Best Practices](https://docs.aws.amazon.com/secretsmanager/latest/userguide/best-practices.html)
- [NIST Special Publication 800-57: Key Management](https://csrc.nist.gov/publications/detail/sp/800-57-part-1/rev-5/final)

---

**Last Updated:** 2025-12-18
**Next Scheduled Review:** 2026-01-18 (Monthly)
