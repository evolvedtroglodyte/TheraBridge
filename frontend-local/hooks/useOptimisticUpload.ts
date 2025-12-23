'use client';

import { useCallback, useState } from 'react';
import { uploadSession } from '@/lib/api';
import type { Session } from '@/lib/types';

/**
 * State of an optimistic upload operation
 */
export interface OptimisticUploadState {
  /** Whether upload is currently in progress */
  isUploading: boolean;
  /** Progress as a percentage (0-100) */
  progress: number;
  /** Error message if upload failed */
  error: string | null;
  /** The optimistically created session */
  optimisticSession: Session | null;
}

/**
 * Callback signature for optimistic upload events
 */
export type OnOptimisticSessionCreated = (session: Session) => void;
export type OnUploadComplete = (session: Session) => void;
export type OnUploadError = (error: string) => void;

/**
 * Handles optimistic uploads with immediate UI feedback
 *
 * Creates optimistic session data immediately, making the UI responsive.
 * The actual upload completes in the background, and the real session
 * data replaces the optimistic version on success.
 *
 * @example
 * ```ts
 * const { isUploading, uploadAndOptimize } = useOptimisticUpload({
 *   onOptimisticSessionCreated: (session) => {
 *     // Add to sessions list optimistically
 *     mutate(sessions => [...sessions, session], { revalidate: false });
 *   },
 *   onUploadComplete: (session) => {
 *     // Real session is ready - data already showing from optimistic update
 *   },
 * });
 *
 * await uploadAndOptimize(patientId, file);
 * ```
 */
export function useOptimisticUpload(callbacks?: {
  onOptimisticSessionCreated?: OnOptimisticSessionCreated;
  onUploadComplete?: OnUploadComplete;
  onUploadError?: OnUploadError;
}) {
  const [state, setState] = useState<OptimisticUploadState>({
    isUploading: false,
    progress: 0,
    error: null,
    optimisticSession: null,
  });

  /**
   * Upload file and create optimistic session immediately
   *
   * @param patientId - The patient to associate with the session
   * @param file - The audio/video file to upload
   * @returns Promise resolving to the real session data
   */
  const uploadAndOptimize = useCallback(
    async (patientId: string, file: File): Promise<Session | null> => {
      setState({
        isUploading: true,
        progress: 10, // Start at 10% immediately
        error: null,
        optimisticSession: null,
      });

      try {
        // Create optimistic session immediately
        const optimisticSession: Session = {
          id: `temp-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
          patient_id: patientId,
          therapist_id: '', // Will be filled by backend
          session_date: new Date().toISOString(),
          duration_seconds: null,
          audio_filename: file.name,
          audio_url: null,
          transcript_text: null,
          transcript_segments: null,
          extracted_notes: null,
          status: 'uploading',
          error_message: null,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          processed_at: null,
        };

        setState((prev) => ({
          ...prev,
          progress: 20,
          optimisticSession,
        }));

        // Notify that optimistic session is created
        callbacks?.onOptimisticSessionCreated?.(optimisticSession);

        // Simulate progress during upload (actual file upload)
        setState((prev) => ({ ...prev, progress: 40 }));

        // Upload the actual file
        const realSession = await uploadSession(patientId, file);

        setState((prev) => ({
          ...prev,
          progress: 90,
        }));

        // Notify success
        callbacks?.onUploadComplete?.(realSession);

        setState({
          isUploading: false,
          progress: 100,
          error: null,
          optimisticSession: null,
        });

        return realSession;
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Upload failed';

        setState({
          isUploading: false,
          progress: 0,
          error: errorMessage,
          optimisticSession: null,
        });

        callbacks?.onUploadError?.(errorMessage);

        return null;
      }
    },
    [callbacks]
  );

  /**
   * Reset upload state
   */
  const reset = useCallback(() => {
    setState({
      isUploading: false,
      progress: 0,
      error: null,
      optimisticSession: null,
    });
  }, []);

  return {
    ...state,
    uploadAndOptimize,
    reset,
  };
}
