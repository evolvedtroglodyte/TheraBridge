/**
 * Auth Callback Route
 * Handles OAuth redirects from Supabase (Google, etc.)
 *
 * Flow:
 * 1. Exchange authorization code for session
 * 2. Check if OAuth user (Google, etc.) - OAuth users are pre-verified, go directly to dashboard
 * 3. Email/password users - go to dashboard (verified via email link)
 */

import { NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

export async function GET(request: Request) {
  const requestUrl = new URL(request.url);
  const code = requestUrl.searchParams.get('code');
  const error = requestUrl.searchParams.get('error');
  const errorDescription = requestUrl.searchParams.get('error_description');

  // Handle OAuth errors
  if (error) {
    console.error('Auth error:', error, errorDescription);
    const loginUrl = new URL('/auth/login', requestUrl.origin);
    loginUrl.searchParams.set('error', errorDescription || error);
    return NextResponse.redirect(loginUrl);
  }

  if (!code) {
    return NextResponse.redirect(new URL('/auth/login', requestUrl.origin));
  }

  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
  const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;
  const supabase = createClient(supabaseUrl, supabaseAnonKey);

  try {
    // Exchange code for session
    const { data: sessionData, error: sessionError } = await supabase.auth.exchangeCodeForSession(code);

    if (sessionError || !sessionData.session) {
      console.error('Session exchange error:', sessionError);
      const loginUrl = new URL('/auth/login', requestUrl.origin);
      loginUrl.searchParams.set('error', 'Failed to authenticate');
      return NextResponse.redirect(loginUrl);
    }

    const user = sessionData.user;

    // Check if this is an OAuth user (Google, etc.)
    const provider = user.app_metadata?.provider;
    const isOAuthUser = provider && provider !== 'email';

    if (isOAuthUser) {
      // OAuth users (Google, etc.) are pre-verified by their provider
      // Always redirect directly to dashboard - no additional verification needed
      console.log(`✅ OAuth login successful (${provider}):`, user.email);
      return NextResponse.redirect(new URL('/patient', requestUrl.origin));
    }

    // Email/password user - go to dashboard
    return NextResponse.redirect(new URL('/patient', requestUrl.origin));

  } catch (err) {
    console.error('Callback error:', err);
    const loginUrl = new URL('/auth/login', requestUrl.origin);
    loginUrl.searchParams.set('error', 'Authentication failed');
    return NextResponse.redirect(loginUrl);
  }
}
