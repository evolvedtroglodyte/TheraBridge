/**
 * Session Status API Endpoint
 * Returns processing status and progress for a session
 */

import { NextRequest, NextResponse } from 'next/server';
import { supabase } from '@/lib/supabase';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ sessionId: string }> }
) {
  try {
    const { sessionId } = await params;

    if (!sessionId) {
      return NextResponse.json(
        { error: 'Missing session ID' },
        { status: 400 }
      );
    }

    // Get session from database
    const { data: session, error } = await supabase
      .from('therapy_sessions')
      .select('*')
      .eq('id', sessionId)
      .single();

    if (error || !session) {
      return NextResponse.json(
        { error: 'Session not found' },
        { status: 404 }
      );
    }

    return NextResponse.json({
      session_id: session.id,
      status: session.processing_status,
      progress: session.processing_progress,
      completed: session.processing_status === 'completed',
      failed: session.processing_status === 'failed',
      results: session.processing_status === 'completed' ? {
        transcript: session.transcript,
        summary: session.summary,
        mood: session.mood,
        topics: session.topics,
        key_insights: session.key_insights,
        action_items: session.action_items,
        duration_minutes: session.duration_minutes,
      } : null,
    });

  } catch (error) {
    console.error('Status error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
