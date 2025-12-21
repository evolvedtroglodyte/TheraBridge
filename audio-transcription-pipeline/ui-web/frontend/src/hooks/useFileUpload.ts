import { useState } from 'react';
import { apiClient } from '@/lib/api-client';
import { classifyError } from '@/lib/utils';

interface UseFileUploadReturn {
  upload: (file: File) => Promise<string | null>;
  isUploading: boolean;
  error: string | null;
  progress: number;
}

export function useFileUpload(): UseFileUploadReturn {
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);

  const upload = async (file: File): Promise<string | null> => {
    console.log('[useFileUpload] Upload started');
    setIsUploading(true);
    setError(null);
    setProgress(0);

    try {
      // Simulate upload progress (real progress would come from XMLHttpRequest.upload)
      const progressInterval = setInterval(() => {
        setProgress((prev) => Math.min(prev + 10, 90));
      }, 200);

      console.log('[useFileUpload] Calling API uploadFile...');
      const response = await apiClient.uploadFile(file);
      console.log('[useFileUpload] API response:', response);

      clearInterval(progressInterval);
      setProgress(100);
      setIsUploading(false);
      console.log('[useFileUpload] Upload complete, returning job_id:', response.job_id);

      return response.job_id;
    } catch (err) {
      console.error('[useFileUpload] Upload error:', err);
      setError(classifyError(err));
      setIsUploading(false);
      setProgress(0);
      return null;
    }
  };

  return { upload, isUploading, error, progress };
}
