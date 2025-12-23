/**
 * Email Existence Check API
 *
 * Checks if an email is already registered in Supabase Auth
 * Uses password reset trigger as a detection method (standard approach)
 *
 * Returns:
 * - exists: true/false
 * - provider: 'email' | 'google' | null (if exists)
 */

import { NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

export async function POST(request: Request) {
  try {
    const { email } = await request.json();

    if (!email || typeof email !== 'string') {
      return NextResponse.json(
        { error: 'Email is required' },
        { status: 400 }
      );
    }

    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
    const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY!;

    // Use service role to query auth.users
    const supabase = createClient(supabaseUrl, supabaseServiceKey, {
      auth: {
        autoRefreshToken: false,
        persistSession: false
      }
    });

    // Query the auth.users table to check if email exists
    const { data: { users }, error } = await supabase.auth.admin.listUsers();

    if (error) {
      console.error('Error checking email:', error);
      return NextResponse.json(
        { error: 'Failed to check email' },
        { status: 500 }
      );
    }

    // Find user with matching email
    const user = users.find(u => u.email?.toLowerCase() === email.toLowerCase());

    if (!user) {
      return NextResponse.json({
        exists: false,
        provider: null
      });
    }

    // Get provider from user metadata
    const provider = user.app_metadata?.provider || 'email';

    return NextResponse.json({
      exists: true,
      provider: provider
    });

  } catch (err) {
    console.error('Email check error:', err);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
