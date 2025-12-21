/**
 * Audio Processing API Endpoint
 * Transcribes audio using OpenAI Whisper API and performs speaker diarization
 */

import { NextRequest, NextResponse } from 'next/server';
import { supabase } from '@/lib/supabase';
import OpenAI from 'openai';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';
export const maxDuration = 300; // 5 minutes max for Vercel Pro

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

export async function POST(request: NextRequest) {
  try {
    const { session_id } = await request.json();

    if (!session_id) {
      return NextResponse.json(
        { error: 'Missing session_id' },
        { status: 400 }
      );
    }

    // Get session from database
    const { data: session, error: sessionError } = await supabase
      .from('therapy_sessions')
      .select('*')
      .eq('id', session_id)
      .single();

    if (sessionError || !session) {
      return NextResponse.json(
        { error: 'Session not found' },
        { status: 404 }
      );
    }

    if (!session.audio_file_url) {
      return NextResponse.json(
        { error: 'No audio file associated with this session' },
        { status: 400 }
      );
    }

    // Update status to processing
    await supabase
      .from('therapy_sessions')
      .update({
        processing_status: 'processing',
        processing_progress: 10,
      })
      .eq('id', session_id);

    // Download audio file from Supabase Storage
    const fileName = session.audio_file_url.split('/').pop();
    const { data: audioData, error: downloadError } = await supabase.storage
      .from('audio-sessions')
      .download(fileName!);

    if (downloadError) {
      console.error('Download error:', downloadError);
      await updateSessionError(session_id, 'Failed to download audio file');
      return NextResponse.json(
        { error: 'Failed to download audio file' },
        { status: 500 }
      );
    }

    // Update progress
    await supabase
      .from('therapy_sessions')
      .update({ processing_progress: 30 })
      .eq('id', session_id);

    // Transcribe using OpenAI Whisper API
    const transcription = await openai.audio.transcriptions.create({
      file: new File([audioData], fileName!, { type: 'audio/mpeg' }),
      model: 'whisper-1',
      response_format: 'verbose_json',
      timestamp_granularities: ['segment'],
    });

    // Update progress
    await supabase
      .from('therapy_sessions')
      .update({ processing_progress: 60 })
      .eq('id', session_id);

    // Simple speaker diarization (basic heuristic for demo)
    // In production, use pyannote.audio or Assembly AI
    const segments = (transcription as any).segments || [];
    const diarizedSegments = segments.map((seg: any, idx: number) => ({
      speaker: idx % 2 === 0 ? 'Therapist' : 'Client',
      text: seg.text,
      start: seg.start,
      end: seg.end,
    }));

    // Update progress
    await supabase
      .from('therapy_sessions')
      .update({ processing_progress: 80 })
      .eq('id', session_id);

    // Extract key information using GPT-4
    const analysisPrompt = `You are a therapy session analyst. Analyze this transcript and extract:
1. Overall mood/tone of the session
2. Main topics discussed (as array)
3. Key insights (as array)
4. Action items for patient (as array)
5. Brief summary (2-3 sentences)

Transcript:
${transcription.text}

Respond in JSON format:
{
  "mood": "...",
  "topics": ["...", "..."],
  "key_insights": ["...", "..."],
  "action_items": ["...", "..."],
  "summary": "..."
}`;

    const analysis = await openai.chat.completions.create({
      model: 'gpt-4o',
      messages: [{ role: 'user', content: analysisPrompt }],
      response_format: { type: 'json_object' },
    });

    const analysisResult = JSON.parse(analysis.choices[0].message.content || '{}');

    // Calculate duration
    const durationMinutes = segments.length > 0
      ? Math.ceil(segments[segments.length - 1].end / 60)
      : null;

    // Update session with results
    const { error: updateError } = await supabase
      .from('therapy_sessions')
      .update({
        transcript: diarizedSegments,
        summary: analysisResult.summary,
        mood: analysisResult.mood,
        topics: analysisResult.topics,
        key_insights: analysisResult.key_insights,
        action_items: analysisResult.action_items,
        duration_minutes: durationMinutes,
        processing_status: 'completed',
        processing_progress: 100,
        updated_at: new Date().toISOString(),
      })
      .eq('id', session_id);

    if (updateError) {
      console.error('Update error:', updateError);
      await updateSessionError(session_id, 'Failed to save results');
      return NextResponse.json(
        { error: 'Failed to save results' },
        { status: 500 }
      );
    }

    return NextResponse.json({
      success: true,
      session_id,
      message: 'Processing completed successfully',
    });

  } catch (error) {
    console.error('Processing error:', error);
    const session_id = (await request.json()).session_id;
    if (session_id) {
      await updateSessionError(session_id, 'Processing failed');
    }
    return NextResponse.json(
      { error: 'Processing failed' },
      { status: 500 }
    );
  }
}

async function updateSessionError(sessionId: string, errorMessage: string) {
  await supabase
    .from('therapy_sessions')
    .update({
      processing_status: 'failed',
      summary: errorMessage,
    })
    .eq('id', sessionId);
}
