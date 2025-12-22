/**
 * Next.js Middleware for Auth Protection
 * Protects dashboard routes and redirects unauthenticated users
 */

import { createClient } from '@supabase/supabase-js';
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export async function middleware(req: NextRequest) {
  const res = NextResponse.next();

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
      // Redirect to login if not authenticated
      const redirectUrl = new URL('/auth/login', req.url);
      redirectUrl.searchParams.set('redirectTo', req.nextUrl.pathname);
      return NextResponse.redirect(redirectUrl);
    }
  }

  // Redirect authenticated users away from auth pages
  if (req.nextUrl.pathname.startsWith('/auth/login') || req.nextUrl.pathname.startsWith('/auth/signup')) {
    if (session) {
      // Get user role and redirect to appropriate dashboard
      const { data: userData } = await supabase
        .from('users')
        .select('role')
        .eq('auth_id', session.user.id)
        .single();

      if (userData) {
        const dashboardPath = userData.role === 'therapist' ? '/therapist' : '/patient/dashboard-v3';
        return NextResponse.redirect(new URL(dashboardPath, req.url));
      }
    }
  }

  return res;
}

export const config = {
  matcher: ['/patient/:path*', '/therapist/:path*', '/auth/:path*'],
};
