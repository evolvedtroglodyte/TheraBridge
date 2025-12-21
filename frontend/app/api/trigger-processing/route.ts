/**
 * Trigger Processing Endpoint
 * Automatically called after upload to start async processing
 */

import { NextRequest, NextResponse } from 'next/server';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function POST(request: NextRequest) {
  try {
    const { session_id } = await request.json();

    if (!session_id) {
      return NextResponse.json(
        { error: 'Missing session_id' },
        { status: 400 }
      );
    }

    // Trigger async processing (fire-and-forget)
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || request.nextUrl.origin;

    fetch(`${baseUrl}/api/process`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id }),
    }).catch(err => {
      console.error('Background processing error:', err);
    });

    return NextResponse.json({
      success: true,
      message: 'Processing started in background',
    });

  } catch (error) {
    console.error('Trigger error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
