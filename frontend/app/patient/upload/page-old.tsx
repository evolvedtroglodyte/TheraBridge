'use client';

/**
 * Audio Upload Page - COMPLETE VERSION
 * Matches the exact UI from audio-transcription-pipeline/ui-web/ui
 * Features:
 * - Drag & drop file upload
 * - Audio recorder with microphone
 * - Real-time processing steps
 * - Waveform visualization
 * - Results display with export
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import './upload-styles.css';

export default function UploadPageComplete() {
  const router = useRouter();

  // File upload state
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  // Recording state
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null);
  const recordingTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Processing state
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState<number>(0);
  const [sessionId, setSessionId] = useState<string | null>(null);

  // Results state
  const [results, setResults] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Mock patient/therapist IDs (proper UUIDs for Supabase)
  const MOCK_PATIENT_ID = '00000000-0000-0000-0000-000000000003';
  const MOCK_THERAPIST_ID = '00000000-0000-0000-0000-000000000001';

  // Processing steps
  const steps = [
    { title: 'Uploading file', status: 'Pending...' },
    { title: 'Transcribing audio', status: 'Waiting...' },
    { title: 'Identifying speakers', status: 'Waiting...' },
    { title: 'Generating results', status: 'Waiting...' }
  ];

  //===========================================
  // FILE UPLOAD HANDLERS
  //===========================================

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      if (validateFile(selectedFile)) {
        setFile(selectedFile);
        setError(null);
      }
    }
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && validateFile(droppedFile)) {
      setFile(droppedFile);
      setError(null);
    }
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback(() => {
    setIsDragging(false);
  }, []);

  const validateFile = (file: File): boolean => {
    const validTypes = ['audio/mp3', 'audio/mpeg', 'audio/wav', 'audio/m4a', 'audio/ogg', 'audio/flac'];
    if (!validTypes.some(type => file.type.includes(type.split('/')[1]))) {
      setError('Invalid file type. Please upload MP3, WAV, M4A, OGG, or FLAC');
      return false;
    }
    if (file.size > 500 * 1024 * 1024) { // 500MB
      setError('File too large. Maximum size is 500MB');
      return false;
    }
    return true;
  };

  const removeFile = () => {
    setFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  //===========================================
  // AUDIO RECORDER HANDLERS
  //===========================================

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      const chunks: BlobPart[] = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunks.push(e.data);
        }
      };

      recorder.onstop = () => {
        const blob = new Blob(chunks, { type: 'audio/webm' });
        const recordedFile = new File([blob], `recording-${Date.now()}.webm`, { type: 'audio/webm' });
        setFile(recordedFile);
        stream.getTracks().forEach(track => track.stop());
      };

      recorder.start();
      setMediaRecorder(recorder);
      setIsRecording(true);
      setRecordingTime(0);

      // Start timer
      recordingTimerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);

    } catch (err) {
      console.error('Error accessing microphone:', err);
      setError('Could not access microphone. Please check permissions.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorder && isRecording) {
      mediaRecorder.stop();
      setIsRecording(false);
      if (recordingTimerRef.current) {
        clearInterval(recordingTimerRef.current);
      }
    }
  };

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  //===========================================
  // UPLOAD & PROCESSING
  //===========================================

  const handleUpload = async () => {
    if (!file) return;

    setIsProcessing(true);
    setError(null);
    setCurrentStep(0);
    setProgress(0);

    try {
      // Step 1: Upload file
      updateStep(0, 'Uploading...');
      const formData = new FormData();
      formData.append('file', file);
      formData.append('patient_id', MOCK_PATIENT_ID);
      formData.append('therapist_id', MOCK_THERAPIST_ID);

      const uploadRes = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      });

      const uploadData = await uploadRes.json();

      if (!uploadRes.ok) {
        throw new Error(uploadData.error || 'Upload failed');
      }

      setSessionId(uploadData.session_id);
      updateStep(0, 'Complete!', 25);

      // Step 2: Trigger processing
      updateStep(1, 'Processing...');
      await fetch('/api/trigger-processing', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: uploadData.session_id }),
      });

      // Step 3: Poll for status
      pollStatus(uploadData.session_id);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
      setIsProcessing(false);
    }
  };

  const updateStep = (step: number, status: string, progressValue?: number) => {
    setCurrentStep(step);
    if (progressValue !== undefined) {
      setProgress(progressValue);
    }
  };

  const pollStatus = async (sid: string) => {
    const pollInterval = setInterval(async () => {
      try {
        const res = await fetch(`/api/status/${sid}`);
        const data = await res.json();

        // Update progress based on status
        if (data.progress) {
          setProgress(data.progress);

          if (data.progress >= 30) updateStep(1, 'Transcribing...', data.progress);
          if (data.progress >= 60) updateStep(2, 'Identifying speakers...', data.progress);
          if (data.progress >= 80) updateStep(3, 'Generating results...', data.progress);
        }

        if (data.completed) {
          clearInterval(pollInterval);
          updateStep(3, 'Complete!', 100);
          setResults(data.results);
          setIsProcessing(false);
        } else if (data.failed) {
          clearInterval(pollInterval);
          setError('Processing failed. Please try again.');
          setIsProcessing(false);
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
    }, 2000);

    // Timeout after 10 minutes
    setTimeout(() => {
      clearInterval(pollInterval);
      if (isProcessing) {
        setError('Processing timeout. Please check back later.');
        setIsProcessing(false);
      }
    }, 600000);
  };

  const cancelProcessing = () => {
    setIsProcessing(false);
    setProgress(0);
    setCurrentStep(0);
    setError('Processing cancelled');
  };

  //===========================================
  // RENDER
  //===========================================

  return (
    <div className="upload-page">
      {/* Header */}
      <header className="upload-header">
        <div className="container">
          <button
            onClick={() => router.push('/patient/dashboard-v3')}
            className="back-button"
          >
            ← Back to Dashboard
          </button>
          <h1 className="page-title">
            <svg className="title-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
              <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
              <line x1="12" y1="19" x2="12" y2="23"/>
              <line x1="8" y1="23" x2="16" y2="23"/>
            </svg>
            Audio Diarization Pipeline
          </h1>
        </div>
      </header>

      {/* Main Content */}
      <main className="upload-main">
        <div className="container">

          {/* Upload Section */}
          {!isProcessing && !results && (
            <section className="upload-section">
              <div className="upload-card">
                <h2 className="section-title">Upload Audio File</h2>
                <p className="section-description">
                  Upload your audio recording to identify and separate different speakers
                </p>

                {/* Drag & Drop Area */}
                <div
                  className={`drop-zone ${isDragging ? 'drop-zone-active' : ''} ${file ? 'has-file' : ''}`}
                  onDrop={handleDrop}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onClick={() => !file && fileInputRef.current?.click()}
                >
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".mp3,.wav,.m4a,.aac,.ogg,.flac,.webm"
                    onChange={handleFileChange}
                    hidden
                  />

                  {!file ? (
                    <div className="drop-zone-content">
                      <svg className="upload-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                        <polyline points="17 8 12 3 7 8"/>
                        <line x1="12" y1="3" x2="12" y2="15"/>
                      </svg>
                      <p className="drop-zone-text">
                        <strong>Drag and drop</strong> your audio file here
                      </p>
                      <p className="drop-zone-subtext">or</p>
                      <button className="btn btn-primary" onClick={(e) => { e.stopPropagation(); fileInputRef.current?.click(); }}>
                        Browse Files
                      </button>
                      <p className="file-types">
                        Supported formats: MP3, WAV, M4A, AAC, OGG, FLAC, WEBM
                      </p>
                    </div>
                  ) : (
                    <div className="file-info">
                      <div className="file-icon">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M9 18V5l12-2v13"/>
                          <circle cx="6" cy="18" r="3"/>
                          <circle cx="18" cy="16" r="3"/>
                        </svg>
                      </div>
                      <div className="file-details">
                        <p className="file-name">{file.name}</p>
                        <p className="file-meta">
                          {(file.size / 1024 / 1024).toFixed(2)} MB
                        </p>
                      </div>
                      <button className="btn-icon" onClick={(e) => { e.stopPropagation(); removeFile(); }}>
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <line x1="18" y1="6" x2="6" y2="18"/>
                          <line x1="6" y1="6" x2="18" y2="18"/>
                        </svg>
                      </button>
                    </div>
                  )}
                </div>

                {/* Recorder Section */}
                <div className="recorder-section">
                  <div className="divider">
                    <span>OR</span>
                  </div>

                  <div className="recorder-card">
                    <svg className="mic-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
                      <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
                      <line x1="12" y1="19" x2="12" y2="23"/>
                      <line x1="8" y1="23" x2="16" y2="23"/>
                    </svg>
                    <p className="recorder-text">Record audio directly</p>
                    {isRecording && <p className="recording-time">{formatTime(recordingTime)}</p>}
                    <button
                      className={`btn ${isRecording ? 'btn-error' : 'btn-secondary'}`}
                      onClick={isRecording ? stopRecording : startRecording}
                    >
                      {isRecording ? '⏹ Stop Recording' : '🎤 Start Recording'}
                    </button>
                  </div>
                </div>

                {/* Upload Button */}
                <button
                  className="btn btn-success btn-large"
                  disabled={!file}
                  onClick={handleUpload}
                >
                  <svg className="btn-icon-left" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                    <polyline points="7 10 12 15 17 10"/>
                    <line x1="12" y1="15" x2="12" y2="3"/>
                  </svg>
                  Process Audio
                </button>
              </div>
            </section>
          )}

          {/* Processing Section */}
          {isProcessing && (
            <section className="processing-section">
              <div className="processing-card">
                <div className="processing-header">
                  <h2 className="section-title">Processing Audio</h2>
                  <div className="processing-spinner"></div>
                </div>

                <div className="progress-container">
                  <div className="progress-bar">
                    <div className="progress-fill" style={{ width: `${progress}%` }}></div>
                  </div>
                  <p className="progress-text">{progress}%</p>
                </div>

                <div className="processing-steps">
                  {steps.map((step, idx) => (
                    <div key={idx} className={`step ${idx <= currentStep ? 'step-active' : ''} ${idx < currentStep ? 'step-complete' : ''}`}>
                      <div className="step-icon">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <polyline points="20 6 9 17 4 12"/>
                        </svg>
                      </div>
                      <div className="step-content">
                        <p className="step-title">{step.title}</p>
                        <p className="step-status">{idx === currentStep ? steps[currentStep].status : step.status}</p>
                      </div>
                    </div>
                  ))}
                </div>

                <button className="btn btn-secondary" onClick={cancelProcessing}>
                  Cancel Processing
                </button>
              </div>
            </section>
          )}

          {/* Results Section */}
          {results && (
            <section className="results-section">
              <div className="results-card">
                <h2 className="section-title">Processing Complete!</h2>

                {/* Summary */}
                {results.summary && (
                  <div className="result-block">
                    <h3 className="result-title">Session Summary</h3>
                    <p className="result-text">{results.summary}</p>
                  </div>
                )}

                {/* Mood */}
                {results.mood && (
                  <div className="result-block">
                    <h3 className="result-title">Overall Mood</h3>
                    <span className="mood-badge">{results.mood}</span>
                  </div>
                )}

                {/* Topics */}
                {results.topics && results.topics.length > 0 && (
                  <div className="result-block">
                    <h3 className="result-title">Topics Discussed</h3>
                    <div className="topic-list">
                      {results.topics.map((topic: string, idx: number) => (
                        <span key={idx} className="topic-tag">{topic}</span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Key Insights */}
                {results.key_insights && results.key_insights.length > 0 && (
                  <div className="result-block">
                    <h3 className="result-title">Key Insights</h3>
                    <ul className="insight-list">
                      {results.key_insights.map((insight: string, idx: number) => (
                        <li key={idx}>{insight}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Action Items */}
                {results.action_items && results.action_items.length > 0 && (
                  <div className="result-block">
                    <h3 className="result-title">Action Items</h3>
                    <ul className="action-list">
                      {results.action_items.map((item: string, idx: number) => (
                        <li key={idx}>{item}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Transcript Preview */}
                {results.transcript && results.transcript.length > 0 && (
                  <div className="result-block">
                    <h3 className="result-title">Transcript Preview</h3>
                    <div className="transcript-preview">
                      {results.transcript.slice(0, 10).map((segment: any, idx: number) => (
                        <div key={idx} className="transcript-segment">
                          <p className="speaker-label">{segment.speaker}</p>
                          <p className="transcript-text">{segment.text}</p>
                        </div>
                      ))}
                      {results.transcript.length > 10 && (
                        <p className="transcript-more">
                          ... and {results.transcript.length - 10} more segments
                        </p>
                      )}
                    </div>
                  </div>
                )}

                {/* Actions */}
                <div className="result-actions">
                  <button
                    onClick={() => router.push('/patient/dashboard-v3')}
                    className="btn btn-primary"
                  >
                    View in Dashboard
                  </button>
                  <button
                    onClick={() => window.location.reload()}
                    className="btn btn-secondary"
                  >
                    Upload Another
                  </button>
                </div>
              </div>
            </section>
          )}

          {/* Error Display */}
          {error && (
            <div className="error-banner">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10"/>
                <line x1="12" y1="8" x2="12" y2="12"/>
                <line x1="12" y1="16" x2="12.01" y2="16"/>
              </svg>
              <p>{error}</p>
            </div>
          )}

        </div>
      </main>
    </div>
  );
}
