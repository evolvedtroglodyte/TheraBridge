export type JobStatus = 'pending' | 'processing' | 'completed' | 'failed';

export interface Speaker {
  id: string;
  label: string;
  total_duration: number;
  segment_count: number;
}

export interface Segment {
  start: number;
  end: number;
  text: string;
  speaker_id?: string;
  confidence?: number;
}

export interface PerformanceMetrics {
  total_processing_time_seconds: number;
  api_latency_seconds?: number;
  computation_time_seconds?: number;
  current_memory_mb?: number;
}

export interface TranscriptionMetadata {
  source_file: string;
  file_size_mb: number;
  duration: number;
  language: string;
  timestamp: string;
  pipeline_type: string;
}

export interface TranscriptionResult {
  id: string;
  status: JobStatus;
  filename: string;
  metadata?: TranscriptionMetadata;
  performance?: PerformanceMetrics;
  speakers: Speaker[];
  segments: Segment[];
  quality?: Record<string, any>;
  error?: string;
  created_at: string;
  completed_at?: string;
}

export interface JobResponse {
  job_id: string;
  status: JobStatus;
  message: string;
}

export interface JobStatusResponse {
  job_id: string;
  status: JobStatus;
  progress: number;
  stage: string;
  error?: string;
}

export interface WSEvent {
  type: 'progress' | 'completed' | 'error';
  job_id: string;
  stage?: string;
  progress?: number;
  result?: TranscriptionResult;
  error?: string;
}
