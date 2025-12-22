import { useEffect, useState } from 'react';
import { CheckCircle, Clock, Loader2 } from 'lucide-react';
import { motion } from 'framer-motion';
import { useWebSocket } from '@/hooks/useWebSocket';
import { formatTime } from '@/lib/utils';

interface UploadProgressProps {
  jobId: string;
  onComplete: () => void;
}

// Stage display names (simplified to 2 stages)
const STAGE_NAMES: Record<string, string> = {
  transcription: 'Transcribing Speech',
  diarization: 'Identifying Speakers',
};

export default function UploadProgress({ jobId, onComplete }: UploadProgressProps) {
  const { status, error } = useWebSocket(jobId);
  const [elapsedTime, setElapsedTime] = useState(0);
  const [targetProgress, setTargetProgress] = useState(0);
  const [animatedProgress, setAnimatedProgress] = useState(0);
  const [showCompletion, setShowCompletion] = useState(false);

  // Elapsed time counter
  useEffect(() => {
    const interval = setInterval(() => {
      setElapsedTime((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  // Map backend progress to target progress (0-50% for transcription, 50-100% for diarization)
  useEffect(() => {
    if (!status) return;

    const stage = status.stage;
    const backendProgress = status.progress || 0;

    console.log('[UploadProgress] Backend progress:', { stage, backendProgress });

    // Map stages to target progress with 45% and 95% caps
    if (stage === 'preprocessing' || stage === 'transcription') {
      // 0-40% backend → 0-45% target (pause at 45% until transcription completes)
      const rawTarget = backendProgress * 112.5; // 0.4 * 112.5 = 45%
      const target = Math.min(rawTarget, 45);
      setTargetProgress(target);
    } else if (stage === 'diarization' || stage === 'alignment' || stage === 'combining') {
      // First, jump to 50% when entering diarization stage
      // Then map 40-100% backend → 50-95% target (pause at 95% until diarization completes)
      const rawTarget = 50 + ((backendProgress - 0.4) / 0.6) * 45; // Map 0.4-1.0 to 50-95
      const target = Math.min(rawTarget, 95);
      setTargetProgress(target);
    } else if (stage === 'completed') {
      setTargetProgress(100);
    }
  }, [status]);

  // Smooth animation towards target
  useEffect(() => {
    const interval = setInterval(() => {
      setAnimatedProgress((current) => {
        const diff = targetProgress - current;
        if (Math.abs(diff) < 0.5) return targetProgress;
        return current + diff * 0.1; // Smooth easing
      });
    }, 50);
    return () => clearInterval(interval);
  }, [targetProgress]);

  // Detect completion
  useEffect(() => {
    if (status?.status === 'completed' && !showCompletion) {
      console.log('[UploadProgress] Processing completed!');
      setShowCompletion(true);
    }
  }, [status?.status, showCompletion]);

  // Handle redirect after showing completion animation
  useEffect(() => {
    if (showCompletion) {
      console.log('[UploadProgress] Showing completion animation, will redirect in 2 seconds');
      const timer = setTimeout(() => {
        console.log('[UploadProgress] Redirecting to results now');
        onComplete();
      }, 2000);
      return () => clearTimeout(timer);
    }
  }, [showCompletion, onComplete]);

  // Determine current displayed stage based on backend progress
  const backendProgress = status?.progress || 0;
  const currentStage = backendProgress < 0.4 ? 'transcription' : 'diarization';
  const isFailed = status?.status === 'failed';

  if (showCompletion) {
    // Show completion animation (replaces everything)
    return (
      <div className="max-w-2xl mx-auto">
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          className="bg-white border border-gray-200 rounded-lg p-12 shadow-sm"
        >
          <div className="flex flex-col items-center gap-4">
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: 0.2, type: 'spring', stiffness: 200 }}
              className="relative"
            >
              <CheckCircle className="h-20 w-20 text-green-600" />
              <motion.div
                className="absolute inset-0 h-20 w-20 bg-green-600 rounded-full opacity-20"
                animate={{ scale: [1, 1.5, 1], opacity: [0.2, 0, 0.2] }}
                transition={{ duration: 2, repeat: Infinity }}
              />
            </motion.div>
            <div className="text-center">
              <p className="text-2xl font-semibold text-green-900">Processing Complete!</p>
              <p className="text-gray-600 mt-2">Redirecting to results...</p>
            </div>
          </div>
        </motion.div>
      </div>
    );
  }

  if (isFailed) {
    return (
      <div className="max-w-2xl mx-auto">
        <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
          <div className="flex items-center gap-3 p-6 bg-red-50 rounded-lg">
            <div className="h-8 w-8 text-red-600">⚠️</div>
            <div>
              <p className="font-medium text-red-900">Processing Failed</p>
              <p className="text-sm text-red-700">{error || status?.error || 'Unknown error'}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
        <h2 className="text-xl font-semibold mb-6">Processing Audio</h2>
        <div className="space-y-6">
          {/* Animated Progress Bar */}
          <div className="space-y-2">
            <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-primary"
                initial={{ width: 0 }}
                animate={{ width: `${animatedProgress}%` }}
                transition={{ duration: 0.3, ease: 'easeOut' }}
              />
            </div>
          </div>

          {/* Elapsed Time */}
          <div className="flex items-center justify-center gap-2 text-sm text-gray-500">
            <Clock className="h-4 w-4" />
            <span>Elapsed time: {formatTime(elapsedTime)}</span>
          </div>

          {/* Two Stage Boxes */}
          <div className="grid gap-3">
            {['transcription', 'diarization'].map((stage) => {
              const isCurrentStage = currentStage === stage;
              const isPastStage = stage === 'transcription' && currentStage === 'diarization';

              return (
                <motion.div
                  key={stage}
                  className={`
                    flex items-center gap-3 p-4 rounded-lg border transition-all duration-300
                    ${isCurrentStage || isPastStage ? 'bg-primary/5 border-primary/20' : 'bg-gray-50 border-gray-200'}
                  `}
                  animate={isCurrentStage ? { scale: [1, 1.02, 1] } : {}}
                  transition={{ duration: 2, repeat: Infinity }}
                >
                  {isPastStage ? (
                    <CheckCircle className="h-6 w-6 text-green-600 flex-shrink-0" />
                  ) : isCurrentStage ? (
                    <Loader2 className="h-6 w-6 text-primary animate-spin flex-shrink-0" />
                  ) : (
                    <div className="h-6 w-6 rounded-full border-2 border-gray-300 flex-shrink-0" />
                  )}
                  <span className={`text-sm ${isCurrentStage || isPastStage ? 'font-medium text-gray-900' : 'text-gray-500'}`}>
                    {STAGE_NAMES[stage]}
                  </span>
                </motion.div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
