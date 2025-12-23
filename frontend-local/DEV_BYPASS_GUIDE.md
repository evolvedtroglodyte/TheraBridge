# Development Auth Bypass - Quick Guide

## ✅ Setup Complete!

You can now bypass authentication during development in two ways:

---

## Method 1: Global Bypass (Middleware Level) - **ACTIVE NOW**

**Current Status:** ✅ **ENABLED**

This completely bypasses the authentication middleware, letting you access any protected route directly.

### How to Toggle:

**Enable Bypass (Current):**
```env
# .env.local
NEXT_PUBLIC_DEV_BYPASS_AUTH=true
```

**Disable Bypass (For testing auth):**
```env
# .env.local
NEXT_PUBLIC_DEV_BYPASS_AUTH=false
```

### What it does:
- When enabled: You can go directly to `/patient/dashboard-v3` without logging in
- When disabled: Middleware redirects you to `/auth/login`
- Console logs: You'll see `🔓 Auth bypassed (development mode)` in the terminal

---

## Method 2: Skip Button (Login Page) - **ACTIVE NOW**

**Location:** `/auth/login` page

Even when auth is enabled, you can click the "🔓 Skip to Dashboard" button to bypass login.

### What it looks like:
```
┌─────────────────────────────────────┐
│  Email: ___________________        │
│  Password: _______________         │
│  [Login Button - Disabled]         │
│                                     │
│  ─────────────────────────────     │
│  🔓 Skip to Dashboard (Dev Mode)   │ ← NEW BUTTON
│  Auth bypass enabled in .env.local │
└─────────────────────────────────────┘
```

### When it appears:
- Only shows when `NEXT_PUBLIC_DEV_BYPASS_AUTH=true`
- Styled in amber/yellow (stands out from normal UI)
- Includes helpful hint text

---

## Quick Access URLs

With bypass **enabled** (current state):
- **Dashboard:** http://localhost:3000/patient/dashboard-v3 ✅ Works directly
- **Login Page:** http://localhost:3000/auth/login ✅ Works, shows skip button

With bypass **disabled**:
- **Dashboard:** http://localhost:3000/patient/dashboard-v3 → Redirects to login
- **Login Page:** http://localhost:3000/auth/login ✅ Works, no skip button

---

## Testing Auth vs Testing UI

### To Test the Dashboard UI (current mode):
1. Keep `NEXT_PUBLIC_DEV_BYPASS_AUTH=true`
2. Go to http://localhost:3000/patient/dashboard-v3
3. Work on your frontend freely

### To Test the Auth Flow:
1. Set `NEXT_PUBLIC_DEV_BYPASS_AUTH=false` in `.env.local`
2. Restart dev server: `npm run dev`
3. Try accessing dashboard → should redirect to login
4. Complete Supabase Auth setup (see SUPABASE_AUTH_SETUP.md)
5. Test signup/login/logout

---

## Files Modified

1. **middleware.ts**
   - Added dev bypass check at the top
   - Skips all auth logic when bypass is enabled

2. **app/auth/login/page.tsx**
   - Added skip button (only visible when bypass enabled)
   - Button routes to `/patient/dashboard-v3`

3. **.env.local**
   - Added `NEXT_PUBLIC_DEV_BYPASS_AUTH=true`

---

## Security Notes

⚠️ **IMPORTANT:** This bypass is for **local development only!**

- The bypass only works when the env var is set to `'true'`
- In production, this env var won't exist → bypass disabled
- Never deploy with `NEXT_PUBLIC_DEV_BYPASS_AUTH=true`

---

## Removing the Bypass (Before Production)

When you're ready to ship:

1. **Remove from .env.local:**
   ```diff
   - NEXT_PUBLIC_DEV_BYPASS_AUTH=true
   ```

2. **Optional: Clean up code:**
   - Remove skip button from login page (lines 176-189)
   - Remove bypass check from middleware (lines 13-18)

3. **Verify:**
   - Try accessing dashboard → should redirect to login
   - No skip button visible on login page

---

## Current Status Summary

✅ Dev bypass is **ACTIVE**
✅ You can access dashboard directly
✅ Skip button appears on login page
✅ Ready to work on frontend UI

**Next:** Work on your frontend, then disable bypass when you want to test auth flow!
