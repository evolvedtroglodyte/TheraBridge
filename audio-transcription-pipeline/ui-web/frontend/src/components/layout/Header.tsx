import { Mic } from 'lucide-react';

export default function Header() {
  return (
    <header className="border-b bg-white shadow-sm">
      <div className="container mx-auto px-4">
        <div className="flex h-16 items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary">
              <Mic className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">
                Audio Transcription
              </h1>
              <p className="text-xs text-gray-500">
                Powered by Whisper AI
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-500">v1.1.0</span>
          </div>
        </div>
      </div>
    </header>
  );
}
