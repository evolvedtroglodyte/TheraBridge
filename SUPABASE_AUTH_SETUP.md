# Supabase Auth Setup - Complete Guide

## ✅ Backend Setup Complete!

I've created all the backend infrastructure for Supabase Auth. Here's what you need to do next:

---

## Step 1: Run Database Migration (REQUIRED)

This migrates from custom password auth to Supabase Auth.

1. **Go to Supabase SQL Editor:**
   https://supabase.com/dashboard/project/rfckpldoohyjctrqxmiv/sql/new

2. **Copy the ENTIRE contents** of this file:
   `supabase/auth-migration.sql`

3. **Paste into the SQL Editor**

4. **Click "Run"** (bottom right)

5. **Wait for success message** - You should see:
   ```
   ✅ Supabase Auth migration complete!

   Next steps:
   1. Enable Email provider in Supabase Dashboard > Authentication > Providers
   2. Configure Site URL: http://localhost:3000
   3. Add Redirect URL: http://localhost:3000/auth/callback
   4. Test signup flow in your frontend
   ```

---

## Step 2: Configure Auth Providers in Supabase Dashboard

### 2.1 Enable Email Provider

1. **Go to Authentication Settings:**
   https://supabase.com/dashboard/project/rfckpldoohyjctrqxmiv/auth/providers

2. **Click on "Email" provider**

3. **Enable the following:**
   - ✅ Enable Email provider
   - ✅ Confirm email (email verification)

4. **Save changes**

### 2.2 Configure Site URL

1. **Scroll down to "URL Configuration" on the same page**

2. **Set the following:**
   - **Site URL:** `http://localhost:3000`
   - **Redirect URLs:** Add `http://localhost:3000/auth/callback`

3. **Save changes**

### 2.3 Enable Social Auth Providers (Optional)

**Google OAuth:**
1. Click on "Google" provider
2. Enable it
3. You'll need to create a Google OAuth app:
   - Go to https://console.cloud.google.com/apis/credentials
   - Create OAuth 2.0 Client ID
   - Add authorized redirect URI: `https://rfckpldoohyjctrqxmiv.supabase.co/auth/v1/callback`
   - Copy Client ID and Client Secret to Supabase

**GitHub OAuth:**
1. Click on "GitHub" provider
2. Enable it
3. Create a GitHub OAuth app:
   - Go to https://github.com/settings/developers
   - New OAuth App
   - Authorization callback URL: `https://rfckpldoohyjctrqxmiv.supabase.co/auth/v1/callback`
   - Copy Client ID and Client Secret to Supabase

---

## Step 3: Configure Email Templates (Optional)

Customize the emails users receive for verification and password reset.

1. **Go to Email Templates:**
   https://supabase.com/dashboard/project/rfckpldoohyjctrqxmiv/auth/templates

2. **Customize these templates:**
   - **Confirm signup** - Email verification link
   - **Reset password** - Password reset link
   - **Magic Link** - Passwordless login (optional)

3. **Use these variables in templates:**
   - `{{ .ConfirmationURL }}` - Email verification link
   - `{{ .Token }}` - Verification token
   - `{{ .TokenHash }}` - Token hash
   - `{{ .SiteURL }}` - Your site URL

---

## What I've Built (Backend)

### ✅ Database Migration (`supabase/auth-migration.sql`)
- Removes `password_hash` column (no longer needed)
- Adds `auth_id` column to link to Supabase Auth
- Creates trigger to auto-sync new Supabase Auth users to your `users` table
- Updates all RLS policies to use `auth.uid()`

### ✅ Auth Helper Functions (`frontend/lib/auth.ts`)
- `signUp()` - Create new user with email/password
- `signIn()` - Login with email/password
- `signOut()` - Logout
- `resetPassword()` - Send password reset email
- `updatePassword()` - Update password after reset
- `getSession()` - Get current session
- `getCurrentUser()` - Get current user data
- `signInWithOAuth()` - Social login (Google, GitHub)
- `resendVerificationEmail()` - Resend verification

### ✅ Auth Context (`frontend/contexts/AuthContext.tsx`)
- React Context for auth state
- `useAuth()` hook for accessing auth in components
- Automatic session management
- User data sync with database

### ✅ Protected Routes (`frontend/middleware.ts`)
- Redirects unauthenticated users to `/auth/login`
- Redirects authenticated users away from auth pages
- Role-based dashboard redirects (therapist vs patient)

### ✅ OAuth Callback (`frontend/app/auth/callback/route.ts`)
- Handles OAuth redirects
- Handles email verification links
- Redirects to dashboard after successful auth

---

## Next Steps for Frontend

Now you can build the UI! Here's what you need:

### 1. Login Page (`app/auth/login/page.tsx`)
Use the auth functions:
```tsx
import { signIn, signInWithOAuth } from '@/lib/auth';

// Email/password login
const { user, error } = await signIn({ email, password });

// OAuth login
const { data, error } = await signInWithOAuth('google');
```

### 2. Signup Page
```tsx
import { signUp } from '@/lib/auth';

const { user, error } = await signUp({
  email,
  password,
  firstName,
  lastName,
  role: 'patient' // or 'therapist'
});
```

### 3. Forgot Password Page
```tsx
import { resetPassword } from '@/lib/auth';

const { error } = await resetPassword(email);
// User receives email with reset link
```

### 4. Reset Password Page
```tsx
import { updatePassword } from '@/lib/auth';

const { error } = await updatePassword(newPassword);
```

### 5. Use Auth in Components
```tsx
'use client';

import { useAuth } from '@/contexts/AuthContext';

export function MyComponent() {
  const { user, loading, signOut } = useAuth();

  if (loading) return <div>Loading...</div>;
  if (!user) return <div>Not logged in</div>;

  return (
    <div>
      <p>Welcome {user.first_name}!</p>
      <button onClick={signOut}>Sign out</button>
    </div>
  );
}
```

### 6. Wrap App with AuthProvider

Update your root layout:
```tsx
// app/layout.tsx
import { AuthProvider } from '@/contexts/AuthContext';

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        <AuthProvider>
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}
```

---

## Testing the Auth Flow

1. **Start dev server:**
   ```bash
   npm run dev
   ```

2. **Test signup:**
   - Go to `/auth/signup` (you'll build this)
   - Create account with email/password
   - Check email for verification link (if enabled)
   - Click link → redirects to dashboard

3. **Test login:**
   - Go to `/auth/login`
   - Enter credentials
   - Should redirect to dashboard

4. **Test protected routes:**
   - Try accessing `/patient/dashboard-v3` without logging in
   - Should redirect to `/auth/login`

5. **Test password reset:**
   - Go to `/auth/forgot-password`
   - Enter email
   - Check email for reset link
   - Click link → redirects to `/auth/reset-password`
   - Enter new password

---

## Available Auth Data

When a user is logged in, you have access to:

**From `useAuth()` hook:**
```tsx
{
  user: {
    id: string;
    auth_id: string;  // Links to auth.users
    email: string;
    first_name: string;
    last_name: string;
    role: 'therapist' | 'patient';
    created_at: string;
    updated_at: string;
  },
  session: {
    access_token: string;
    refresh_token: string;
    expires_at: number;
    // ... more session data
  },
  loading: boolean;
  signOut: () => Promise<void>;
}
```

---

## Troubleshooting

### "Email not confirmed" error
- Enable email confirmation in providers settings
- Or disable it for local development

### OAuth redirect not working
- Check redirect URLs are correct
- Make sure callback route exists at `/app/auth/callback/route.ts`

### User not syncing to database
- Check the trigger was created successfully
- Run `auth-migration.sql` again
- Check Supabase logs for errors

### Session not persisting
- Make sure `AuthProvider` wraps your app
- Check browser cookies are enabled
- Clear cache and try again

---

## Security Notes

- ✅ Passwords are hashed by Supabase (bcrypt)
- ✅ JWT tokens are signed and verified
- ✅ Row Level Security (RLS) policies protect data
- ✅ Email verification prevents spam signups
- ✅ Password reset uses secure tokens
- ✅ OAuth uses industry-standard flows

---

## Production Deployment

When deploying to production:

1. **Update Site URL:**
   - Change from `http://localhost:3000` to your production domain
   - Update redirect URLs accordingly

2. **Configure Email Service:**
   - Use custom SMTP (SendGrid, Mailgun, etc.)
   - Customize email templates with your branding

3. **Enable Rate Limiting:**
   - Supabase has built-in rate limiting
   - Configure in Auth Settings

4. **Monitor Auth Logs:**
   - Check Supabase Dashboard > Auth > Logs
   - Monitor failed login attempts
   - Watch for suspicious activity

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────┐
│  Frontend (Next.js)                             │
│  ┌─────────────────────────────────────────┐   │
│  │  Auth Pages (login, signup, etc.)      │   │
│  │  ├─ /auth/login                         │   │
│  │  ├─ /auth/signup                        │   │
│  │  ├─ /auth/forgot-password               │   │
│  │  └─ /auth/reset-password                │   │
│  └─────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────┐   │
│  │  Auth Context (useAuth hook)            │   │
│  │  └─ Provides user, session, signOut     │   │
│  └─────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────┐   │
│  │  Middleware (protected routes)          │   │
│  │  └─ Redirects unauthenticated users     │   │
│  └─────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────┐
│  Supabase Auth (auth.users)                     │
│  ├─ Email/password authentication               │
│  ├─ OAuth (Google, GitHub)                      │
│  ├─ Email verification                          │
│  ├─ Password reset                              │
│  └─ JWT session management                      │
└─────────────────────────────────────────────────┘
                       │
                       ▼ (trigger syncs)
┌─────────────────────────────────────────────────┐
│  Your Database (public.users)                   │
│  ├─ auth_id → links to auth.users               │
│  ├─ first_name, last_name, role                 │
│  └─ Custom user data                            │
└─────────────────────────────────────────────────┘
```

---

**You're all set on the backend! Now build the frontend auth pages and test the flow.** 🚀
