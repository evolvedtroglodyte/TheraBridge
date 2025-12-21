// Quick test script to verify Supabase connection
const { createClient } = require('@supabase/supabase-js');

const supabaseUrl = 'https://rfckpldoohyjctrqxmiv.supabase.co';
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJmY2twbGRvb2h5amN0cnF4bWl2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzQ4MzI0OTIsImV4cCI6MjA1MDQwODQ5Mn0.gIaGWkU_tL0MlZRvRMnDCqHE7vx6ydyxWLrH8wXLG_4';

const supabase = createClient(supabaseUrl, supabaseKey);

async function testConnection() {
  console.log('Testing Supabase connection...');

  try {
    // Test 1: Check if we can query users table
    const { data, error } = await supabase
      .from('users')
      .select('*')
      .limit(1);

    if (error) {
      console.error('❌ Error querying users table:', error.message);
      if (error.message.includes('relation "public.users" does not exist')) {
        console.log('\n⚠️  DATABASE SCHEMA NOT CREATED YET!');
        console.log('You need to run the SQL schema in Supabase:');
        console.log('1. Go to: https://supabase.com/dashboard/project/rfckpldoohyjctrqxmiv');
        console.log('2. Click "SQL Editor" → "New Query"');
        console.log('3. Copy contents of supabase/schema.sql');
        console.log('4. Paste and click "Run"');
      }
    } else {
      console.log('✅ Successfully connected to Supabase!');
      console.log('✅ Users table exists');
      console.log('   Found', data?.length || 0, 'users');
    }

    // Test 2: Check if storage bucket exists
    const { data: buckets, error: bucketError } = await supabase
      .storage
      .listBuckets();

    if (bucketError) {
      console.error('❌ Error listing buckets:', bucketError.message);
    } else {
      const audioSessionsBucket = buckets.find(b => b.name === 'audio-sessions');
      if (audioSessionsBucket) {
        console.log('✅ Storage bucket "audio-sessions" exists');
      } else {
        console.log('⚠️  Storage bucket "audio-sessions" NOT found');
        console.log('   This will be created automatically by the SQL schema');
      }
    }

  } catch (err) {
    console.error('❌ Unexpected error:', err);
  }
}

testConnection();
