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
    // Extract the full path from the public URL
    const urlParts = session.audio_file_url.split('/audio-sessions/');
    const filePath = urlParts[1]; // e.g., "00000000-0000-0000-0000-000000000003/1766346127574.mp3"

    const { data: audioData, error: downloadError } = await supabase.storage
      .from('audio-sessions')
      .download(filePath);

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
      .update({ processing_progress: 20 })
      .eq('id', session_id);

    // Call your REAL audio-transcription-pipeline backend for transcription + pyannote diarization
    console.log('[Process] Calling REAL backend with pyannote diarization...');

    const actualFileName = filePath.split('/').pop() || 'audio.mp3';
    const formData = new FormData();
    formData.append('audio', new File([audioData], actualFileName, { type: 'audio/mpeg' }));

    const backendResponse = await fetch('http://localhost:8000/api/transcribe', {
      method: 'POST',
      body: formData,
    });

    if (!backendResponse.ok) {
      throw new Error(`Backend transcription failed: ${backendResponse.statusText}`);
    }

    const backendData = await backendResponse.json();
    console.log('[Process] Got backend job ID:', backendData.job_id);

    // Poll backend for completion (REAL pyannote processing)
    let processingComplete = false;
    let backendResults: any = null;
    let pollAttempts = 0;
    const MAX_POLL_ATTEMPTS = 60; // 2 minutes max

    while (!processingComplete && pollAttempts < MAX_POLL_ATTEMPTS) {
      await new Promise(resolve => setTimeout(resolve, 2000));
      pollAttempts++;

      const statusResponse = await fetch(`http://localhost:8000/api/jobs/${backendData.job_id}/status`);
      const statusData = await statusResponse.json();

      console.log('[Process] Backend status:', statusData.status, `(${statusData.progress}%)`);

      // Update our progress
      await supabase
        .from('therapy_sessions')
        .update({ processing_progress: Math.min(80, 20 + statusData.progress * 0.6) })
        .eq('id', session_id);

      if (statusData.status === 'completed') {
        processingComplete = true;
        const resultsResponse = await fetch(`http://localhost:8000/api/jobs/${backendData.job_id}/result`);
        backendResults = await resultsResponse.json();
      } else if (statusData.status === 'failed') {
        throw new Error('Backend processing failed');
      }
    }

    if (!backendResults) {
      throw new Error('Backend processing timed out');
    }

    console.log('[Process] Got REAL diarized transcription with', backendResults.segments?.length || 0, 'segments');

    // Extract REAL pyannote diarized segments
    const diarizedSegments = backendResults.segments || [];

    // Update progress
    await supabase
      .from('therapy_sessions')
      .update({ processing_progress: 85 })
      .eq('id', session_id);

    // Extract key information using GPT-4
    const fullTranscript = diarizedSegments.map((seg: any) =>
      `${seg.speaker}: ${seg.text}`
    ).join('\n');

    const analysisPrompt = `You are a therapy session analyst. Analyze this transcript and extract:
1. Overall mood/tone of the session
2. Main topics discussed (as array)
3. Key insights (as array)
4. Action items for patient (as array)
5. Brief summary (2-3 sentences)

Transcript:
${fullTranscript}

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

    // Calculate duration from REAL backend results
    const durationMinutes = backendResults.duration_minutes || null;

    // Update session with results
    console.log('[Process] Updating session with results:', {
      session_id,
      hasTranscript: !!diarizedSegments,
      hasSummary: !!analysisResult.summary,
      mood: analysisResult.mood,
    });

    const { data: updateData, error: updateError } = await supabase
      .from('therapy_sessions')
      .update({
        transcript: diarizedSegments,
        summary: analysisResult.summary,
        mood: analysisResult.mood,
        topics: analysisResult.topics || [],
        key_insights: analysisResult.key_insights || [],
        action_items: analysisResult.action_items || [],
        duration_minutes: durationMinutes,
        processing_status: 'completed',
        processing_progress: 100,
      })
      .eq('id', session_id)
      .select();

    if (updateError) {
      console.error('Update error:', updateError);
      await updateSessionError(session_id, `Failed to save results: ${updateError.message}`);
      return NextResponse.json(
        { error: `Failed to save results: ${updateError.message}` },
        { status: 500 }
      );
    }

    console.log('[Process] Update successful:', updateData);

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
