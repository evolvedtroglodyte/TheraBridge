import { useState, useRef, useEffect } from 'react';
import { Mic, Square, Pause, Play, Upload } from 'lucide-react';
import Button from '@/components/ui/Button';
import { formatTime } from '@/lib/utils';
import { useFileUpload } from '@/hooks/useFileUpload';

interface AudioRecorderProps {
  onUploadSuccess: (jobId: string, file: File) => void;
}

export default function AudioRecorder({ onUploadSuccess }: AudioRecorderProps) {
  const [isRecording, setIsRecording] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [recordedBlob, setRecordedBlob] = useState<Blob | null>(null);
  const [recordingTime, setRecordingTime] = useState(0);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [isGeneratingWaveform, setIsGeneratingWaveform] = useState(false);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animationFrameRef = useRef<number | null>(null);

  const { upload, isUploading } = useFileUpload();

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl);
      }
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
    };
  }, [audioUrl]);

  // Draw static waveform from recorded audio
  const drawStaticWaveform = async (audioBlob: Blob) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    setIsGeneratingWaveform(true);

    try {
      const audioContext = new AudioContext();
      const arrayBuffer = await audioBlob.arrayBuffer();
      const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);

      const canvasContext = canvas.getContext('2d');
      if (!canvasContext) return;

      const data = audioBuffer.getChannelData(0);
      const step = Math.ceil(data.length / canvas.width);
      const amp = canvas.height / 2;

      canvasContext.fillStyle = 'rgb(249, 250, 251)';
      canvasContext.fillRect(0, 0, canvas.width, canvas.height);

      canvasContext.lineWidth = 1;
      canvasContext.strokeStyle = 'rgb(59, 130, 246)';
      canvasContext.beginPath();

      for (let i = 0; i < canvas.width; i++) {
        let min = 1.0;
        let max = -1.0;
        for (let j = 0; j < step; j++) {
          const datum = data[i * step + j];
          if (datum < min) min = datum;
          if (datum > max) max = datum;
        }
        canvasContext.moveTo(i, (1 + min) * amp);
        canvasContext.lineTo(i, (1 + max) * amp);
      }

      canvasContext.stroke();
      audioContext.close();
    } catch (error) {
      console.error('Error generating waveform:', error);
    } finally {
      setIsGeneratingWaveform(false);
    }
  };

  // Visualize audio waveform during recording
  const visualizeAudio = (stream: MediaStream) => {
    const audioContext = new AudioContext();
    const analyser = audioContext.createAnalyser();
    const source = audioContext.createMediaStreamSource(stream);

    analyser.fftSize = 2048;
    source.connect(analyser);

    audioContextRef.current = audioContext;
    analyserRef.current = analyser;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const canvasContext = canvas.getContext('2d');
    if (!canvasContext) return;

    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    const draw = () => {
      animationFrameRef.current = requestAnimationFrame(draw);

      analyser.getByteTimeDomainData(dataArray);

      canvasContext.fillStyle = 'rgb(249, 250, 251)';
      canvasContext.fillRect(0, 0, canvas.width, canvas.height);

      canvasContext.lineWidth = 2;
      canvasContext.strokeStyle = 'rgb(59, 130, 246)';
      canvasContext.beginPath();

      const sliceWidth = (canvas.width * 1.0) / bufferLength;
      let x = 0;

      for (let i = 0; i < bufferLength; i++) {
        const v = dataArray[i] / 128.0;
        const y = (v * canvas.height) / 2;

        if (i === 0) {
          canvasContext.moveTo(x, y);
        } else {
          canvasContext.lineTo(x, y);
        }

        x += sliceWidth;
      }

      canvasContext.lineTo(canvas.width, canvas.height / 2);
      canvasContext.stroke();
    };

    draw();
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);

      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        setRecordedBlob(blob);
        const url = URL.createObjectURL(blob);
        setAudioUrl(url);

        // Stop all tracks
        stream.getTracks().forEach((track) => track.stop());

        // Stop visualization
        if (animationFrameRef.current) {
          cancelAnimationFrame(animationFrameRef.current);
        }
        if (audioContextRef.current) {
          audioContextRef.current.close();
          audioContextRef.current = null;
        }

        // Draw static waveform
        drawStaticWaveform(blob);
      };

      mediaRecorder.start();
      setIsRecording(true);
      setIsPaused(false);
      setRecordingTime(0);

      // Start timer
      timerRef.current = setInterval(() => {
        setRecordingTime((prev) => prev + 1);
      }, 1000);

      // Start visualization
      visualizeAudio(stream);
    } catch (error) {
      console.error('Error accessing microphone:', error);
      alert('Failed to access microphone. Please check permissions.');
    }
  };

  const pauseRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      if (isPaused) {
        mediaRecorderRef.current.resume();
        setIsPaused(false);
      } else {
        mediaRecorderRef.current.pause();
        setIsPaused(true);
      }
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setIsPaused(false);

      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    }
  };

  const handleUploadRecording = async () => {
    if (!recordedBlob) return;

    // Convert Blob to File
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const file = new File([recordedBlob], `recording_${timestamp}.webm`, {
      type: 'audio/webm',
    });

    try {
      console.log('[AudioRecorder] Uploading recording...', { filename: file.name });
      const jobId = await upload(file);
      console.log('[AudioRecorder] Upload complete, got job ID:', jobId);
      if (jobId) {
        onUploadSuccess(jobId, file);
      }
    } catch (error) {
      console.error('[AudioRecorder] Upload failed:', error);
    }
  };

  const handleReset = () => {
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
    }
    setRecordedBlob(null);
    setAudioUrl(null);
    setRecordingTime(0);
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
        <h2 className="text-xl font-semibold mb-6">Record Audio</h2>
        <div className="space-y-4">
          {/* Waveform Visualization */}
          <div className="bg-gray-50 rounded-lg p-4 relative">
            <canvas
              ref={canvasRef}
              width={600}
              height={100}
              className="w-full h-24"
            />
            {isGeneratingWaveform && (
              <div className="absolute inset-0 flex items-center justify-center bg-gray-50 bg-opacity-80">
                <p className="text-sm text-gray-600">Generating waveform...</p>
              </div>
            )}
          </div>

          {/* Recording Timer */}
          {(isRecording || recordedBlob) && (
            <div className="text-center">
              <div className="text-2xl font-mono font-medium">
                {formatTime(recordingTime)}
              </div>
              {isRecording && (
                <div className="text-sm text-gray-500 mt-1">
                  {isPaused ? 'Paused' : 'Recording...'}
                </div>
              )}
            </div>
          )}

          {/* Recorded Audio Playback */}
          {audioUrl && !isRecording && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <p className="text-sm font-medium text-green-900 mb-2">
                Recording Complete
              </p>
              <audio
                src={audioUrl}
                controls
                className="w-full"
              />
            </div>
          )}

          {/* Control Buttons */}
          <div className="flex gap-3 justify-center">
            {!isRecording && !recordedBlob && (
              <Button
                onClick={startRecording}
                className="gap-2"
              >
                <Mic className="h-4 w-4" />
                Start Recording
              </Button>
            )}

            {isRecording && (
              <>
                <Button
                  onClick={pauseRecording}
                  variant="outline"
                  className="gap-2"
                >
                  {isPaused ? (
                    <>
                      <Play className="h-4 w-4" />
                      Resume
                    </>
                  ) : (
                    <>
                      <Pause className="h-4 w-4" />
                      Pause
                    </>
                  )}
                </Button>

                <Button
                  onClick={stopRecording}
                  variant="outline"
                  className="gap-2"
                >
                  <Square className="h-4 w-4" />
                  Stop
                </Button>
              </>
            )}

            {recordedBlob && !isRecording && (
              <>
                <Button
                  onClick={handleUploadRecording}
                  disabled={isUploading}
                  isLoading={isUploading}
                  className="gap-2 flex-1"
                >
                  <Upload className="h-4 w-4" />
                  {isUploading ? 'Uploading...' : 'Upload & Transcribe'}
                </Button>
                <Button
                  onClick={handleReset}
                  variant="outline"
                  disabled={isUploading}
                >
                  Reset
                </Button>
              </>
            )}
          </div>

          {/* Instructions */}
          {!isRecording && !recordedBlob && (
            <div className="text-center text-sm text-gray-500">
              <p>Click "Start Recording" to begin recording from your microphone.</p>
              <p className="mt-1">You can pause/resume during recording.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
