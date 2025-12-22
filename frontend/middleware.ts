/**
 * Next.js Middleware for Auth Protection
 * Simple version - uses Supabase Auth only, no custom database tables
 */

import { createClient } from '@supabase/supabase-js';
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export async function middleware(req: NextRequest) {
  const res = NextResponse.next();

  // 🔓 DEV BYPASS: Skip auth during development
  const devBypass = process.env.NEXT_PUBLIC_DEV_BYPASS_AUTH === 'true';
  if (devBypass) {
    return res;
  }

  // Create Supabase client
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
  const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;
  const supabase = createClient(supabaseUrl, supabaseAnonKey);

  const {
    data: { session },
  } = await supabase.auth.getSession();

  // Protect dashboard routes
  if (req.nextUrl.pathname.startsWith('/patient') || req.nextUrl.pathname.startsWith('/therapist')) {
    if (!session) {
      const redirectUrl = new URL('/auth/login', req.url);
      redirectUrl.searchParams.set('redirectTo', req.nextUrl.pathname);
      return NextResponse.redirect(redirectUrl);
    }
  }

  // Redirect authenticated users away from auth pages
  if (req.nextUrl.pathname.startsWith('/auth/login') || req.nextUrl.pathname.startsWith('/auth/signup')) {
    if (session) {
      // All users go to patient dashboard (no role check needed without database)
      return NextResponse.redirect(new URL('/patient', req.url));
    }
  }

  return res;
}

export const config = {
  matcher: ['/patient/:path*', '/therapist/:path*', '/auth/:path*'],
};
