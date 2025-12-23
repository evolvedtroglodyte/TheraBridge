/**
 * Test Supabase Connection
 * Diagnostic endpoint to verify Supabase setup
 */

import { NextResponse } from 'next/server';
import { supabase } from '@/lib/supabase';

export const dynamic = 'force-dynamic';

export async function GET() {
  const results = {
    connection: '❌ Not tested',
    env_vars: '❌ Missing',
    storage_bucket: '❌ Not found',
    test_users: '❌ Not found',
    tables: '❌ Not found',
  };

  const debug = {
    url: process.env.NEXT_PUBLIC_SUPABASE_URL || 'NOT SET',
    anonKeyPrefix: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY?.substring(0, 20) || 'NOT SET',
    anonKeyLength: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY?.length || 0,
  };

  try {
    // 1. Check environment variables
    if (process.env.NEXT_PUBLIC_SUPABASE_URL && process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY) {
      results.env_vars = '✅ Present';
    }

    // 2. Test database connection - check if users table exists
    const { data: users, error: usersError } = await supabase
      .from('users')
      .select('id, email, role')
      .limit(5);

    if (usersError) {
      results.tables = `❌ Error: ${usersError.message}`;
    } else {
      results.tables = `✅ Found ${users?.length || 0} users`;
      results.connection = '✅ Connected';
    }

    // 3. Check if test users exist
    const { data: testUsers, error: testError } = await supabase
      .from('users')
      .select('id, email, role')
      .in('id', [
        '00000000-0000-0000-0000-000000000001',
        '00000000-0000-0000-0000-000000000002'
      ]);

    if (testError) {
      results.test_users = `❌ Error: ${testError.message}`;
    } else if (testUsers && testUsers.length === 2) {
      results.test_users = '✅ Test users exist';
    } else {
      results.test_users = `⚠️ Only ${testUsers?.length || 0}/2 test users found`;
    }

    // 4. Check storage buckets
    const { data: buckets, error: bucketsError } = await supabase
      .storage
      .listBuckets();

    if (bucketsError) {
      results.storage_bucket = `❌ Error: ${bucketsError.message}`;
      console.error('Bucket list error:', bucketsError);
    } else {
      console.log('Found buckets:', buckets);
      const audioSessionsBucket = buckets?.find(b => b.name === 'audio-sessions');
      if (audioSessionsBucket) {
        results.storage_bucket = '✅ Bucket exists';
      } else {
        results.storage_bucket = `❌ Bucket not found (found: ${buckets?.map(b => b.name).join(', ') || 'none'})`;
      }
    }

    // 5. Try to access the bucket directly
    const { data: bucketTest, error: bucketTestError } = await supabase
      .storage
      .from('audio-sessions')
      .list('', { limit: 1 });

    if (bucketTestError) {
      results.storage_bucket += ` | Direct access: ${bucketTestError.message}`;
    } else {
      results.storage_bucket = '✅ Bucket exists and accessible';
    }

  } catch (error) {
    results.connection = `❌ Error: ${error instanceof Error ? error.message : 'Unknown error'}`;
  }

  return NextResponse.json({
    status: Object.values(results).every(v => v.startsWith('✅')) ? 'All checks passed!' : 'Some checks failed',
    results,
    debug,
    instructions: {
      env_vars: 'Check frontend/.env.local has NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY',
      tables: 'Run supabase/schema.sql in Supabase SQL Editor',
      test_users: 'Run supabase/test-data.sql in Supabase SQL Editor',
      storage_bucket: 'Create "audio-sessions" bucket in Supabase Storage dashboard',
    }
  }, { status: 200 });
}
