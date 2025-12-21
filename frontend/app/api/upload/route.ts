/**
 * Audio Upload API Endpoint
 * Handles file upload to Supabase Storage and creates session record
 */

import { NextRequest, NextResponse } from 'next/server';
import { supabase } from '@/lib/supabase';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function POST(request: NextRequest) {
  try {
    // Get form data
    const formData = await request.formData();
    const file = formData.get('file') as File;
    const patientId = formData.get('patient_id') as string;
    const therapistId = formData.get('therapist_id') as string;

    if (!file) {
      return NextResponse.json(
        { error: 'No file provided' },
        { status: 400 }
      );
    }

    if (!patientId || !therapistId) {
      return NextResponse.json(
        { error: 'Missing patient_id or therapist_id' },
        { status: 400 }
      );
    }

    // Validate file type
    const allowedTypes = ['audio/mp3', 'audio/mpeg', 'audio/wav', 'audio/m4a', 'audio/ogg', 'audio/flac'];
    if (!allowedTypes.includes(file.type)) {
      return NextResponse.json(
        { error: 'Invalid file type. Supported: MP3, WAV, M4A, OGG, FLAC' },
        { status: 400 }
      );
    }

    // Generate unique filename
    const timestamp = Date.now();
    const fileExt = file.name.split('.').pop();
    const fileName = `${patientId}/${timestamp}.${fileExt}`;

    // Upload to Supabase Storage
    const fileBuffer = await file.arrayBuffer();
    const { data: uploadData, error: uploadError } = await supabase.storage
      .from('audio-sessions')
      .upload(fileName, fileBuffer, {
        contentType: file.type,
        upsert: false,
      });

    if (uploadError) {
      console.error('Upload error:', uploadError);
      return NextResponse.json(
        { error: 'Failed to upload file' },
        { status: 500 }
      );
    }

    // Get public URL
    const { data: urlData } = supabase.storage
      .from('audio-sessions')
      .getPublicUrl(fileName);

    // Create therapy session record
    const { data: sessionData, error: sessionError } = await supabase
      .from('therapy_sessions')
      .insert({
        patient_id: patientId,
        therapist_id: therapistId,
        session_date: new Date().toISOString(),
        audio_file_url: urlData.publicUrl,
        processing_status: 'pending',
        processing_progress: 0,
      })
      .select()
      .single();

    if (sessionError) {
      console.error('Session creation error:', sessionError);
      return NextResponse.json(
        { error: 'Failed to create session record' },
        { status: 500 }
      );
    }

    return NextResponse.json({
      success: true,
      session_id: sessionData.id,
      file_url: urlData.publicUrl,
      message: 'File uploaded successfully. Processing will begin shortly.',
    });

  } catch (error) {
    console.error('Upload error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
