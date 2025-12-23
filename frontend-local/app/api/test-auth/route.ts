/**
 * Test Auth Setup - Diagnostic endpoint
 * Visit: http://localhost:3000/api/test-auth
 */

import { NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

export async function GET() {
  const checks: Record<string, string> = {};

  try {
    // Check 1: Environment variables
    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
    const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

    if (supabaseUrl && supabaseAnonKey) {
      checks.env_vars = '✅ Environment variables present';
    } else {
      checks.env_vars = '❌ Missing environment variables';
      return NextResponse.json({ checks, error: 'Missing env vars' });
    }

    // Check 2: Supabase connection
    const supabase = createClient(supabaseUrl, supabaseAnonKey);

    // Check 3: Database connection (test query)
    const { data: users, error: usersError } = await supabase
      .from('users')
      .select('count')
      .limit(1);

    if (usersError) {
      checks.database = `❌ Database error: ${usersError.message}`;
    } else {
      checks.database = '✅ Database connection working';
    }

    // Check 4: Auth schema (check for auth_id column)
    const { data: schemaCheck, error: schemaError } = await supabase
      .from('users')
      .select('auth_id')
      .limit(1);

    if (schemaError) {
      if (schemaError.message.includes('column "auth_id" does not exist')) {
        checks.auth_migration = '❌ Run auth-migration.sql first! (auth_id column missing)';
      } else {
        checks.auth_migration = `❌ Schema error: ${schemaError.message}`;
      }
    } else {
      checks.auth_migration = '✅ Auth migration applied (auth_id column exists)';
    }

    // Check 5: Auth configuration
    const { data: authSettings } = await supabase.auth.getSession();
    checks.auth_configured = '✅ Supabase Auth is accessible';

    return NextResponse.json({
      checks,
      next_steps: checks.auth_migration?.includes('❌')
        ? [
            '1. Go to Supabase SQL Editor',
            '2. Run the contents of supabase/auth-migration.sql',
            '3. Refresh this page',
          ]
        : [
            '✅ Backend is ready!',
            '1. Configure auth providers in Supabase Dashboard',
            '2. Build the auth UI pages (/auth/login, /auth/signup)',
            '3. Test the complete auth flow',
          ],
    });
  } catch (error: any) {
    return NextResponse.json({
      checks,
      error: error.message,
    });
  }
}
