'use client';

import { toast } from 'sonner';
import { Button } from '@/components/ui/button';

/**
 * ToastExample Component
 * Demonstrates all available toast notification types and patterns.
 * Import and use this to test toast functionality in your application.
 *
 * Usage:
 * import { ToastExample } from '@/components/examples/toast-example';
 *
 * export default function MyPage() {
 *   return <ToastExample />;
 * }
 */
export function ToastExample() {
  const handleSuccessToast = () => {
    toast.success('Success!', {
      description: 'Your operation completed successfully.',
    });
  };

  const handleErrorToast = () => {
    toast.error('Error', {
      description: 'Something went wrong. Please try again.',
    });
  };

  const handleInfoToast = () => {
    toast.info('Information', {
      description: 'This is an informational message.',
    });
  };

  const handleLoadingToast = () => {
    const id = toast.loading('Processing...', {
      description: 'This operation may take a few moments.',
    });

    // Simulate operation completion
    setTimeout(() => {
      toast.success('Completed!', {
        description: 'Your operation has finished.',
        id,
      });
    }, 3000);
  };

  const handlePromiseToast = () => {
    toast.promise(
      new Promise((resolve) => {
        setTimeout(() => {
          resolve('Data fetched successfully');
        }, 2000);
      }),
      {
        loading: 'Fetching data...',
        success: 'Data loaded!',
        error: 'Failed to fetch data',
      }
    );
  };

  const handleCustomToast = () => {
    toast.success(
      <div className="space-y-2">
        <h3 className="font-semibold">Custom Toast</h3>
        <p className="text-sm">This is a custom JSX toast with multiple elements.</p>
      </div>
    );
  };

  const handleSessionUploadFlow = async () => {
    const id = toast.loading('Uploading session...', {
      description: 'Preparing your audio file.',
    });

    try {
      // Simulate upload
      await new Promise((resolve) => setTimeout(resolve, 1500));

      toast.loading('Transcribing audio...', {
        description: 'Converting speech to text.',
        id,
      });

      // Simulate transcription
      await new Promise((resolve) => setTimeout(resolve, 2000));

      toast.loading('Analyzing session...', {
        description: 'Extracting therapy notes.',
        id,
      });

      // Simulate analysis
      await new Promise((resolve) => setTimeout(resolve, 1500));

      toast.success('Session processed!', {
        description: 'Your therapy session is ready for review.',
        id,
      });
    } catch (error) {
      toast.error('Processing failed', {
        description: 'Please try uploading your session again.',
        id,
      });
    }
  };

  const handleMultipleToasts = () => {
    toast.info('First message');
    setTimeout(() => toast.info('Second message'), 500);
    setTimeout(() => toast.success('Final message'), 1000);
  };

  return (
    <div className="w-full max-w-2xl mx-auto p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold mb-2">Toast Notification Examples</h1>
        <p className="text-gray-600">
          Click the buttons below to see different toast notification types in action.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* Basic Toast Types */}
        <div className="space-y-3 p-4 border rounded-lg bg-slate-50">
          <h2 className="font-semibold text-lg">Basic Toast Types</h2>

          <Button
            onClick={handleSuccessToast}
            variant="default"
            className="w-full bg-green-600 hover:bg-green-700"
          >
            Success Toast
          </Button>

          <Button
            onClick={handleErrorToast}
            variant="destructive"
            className="w-full"
          >
            Error Toast
          </Button>

          <Button
            onClick={handleInfoToast}
            variant="outline"
            className="w-full"
          >
            Info Toast
          </Button>
        </div>

        {/* Advanced Toast Types */}
        <div className="space-y-3 p-4 border rounded-lg bg-slate-50">
          <h2 className="font-semibold text-lg">Advanced Toast Types</h2>

          <Button
            onClick={handleLoadingToast}
            variant="outline"
            className="w-full"
          >
            Loading Toast (Auto-success)
          </Button>

          <Button
            onClick={handlePromiseToast}
            variant="outline"
            className="w-full"
          >
            Promise Toast
          </Button>

          <Button
            onClick={handleCustomToast}
            variant="outline"
            className="w-full"
          >
            Custom JSX Toast
          </Button>
        </div>
      </div>

      {/* Real-World Examples */}
      <div className="space-y-3 p-4 border rounded-lg bg-slate-50">
        <h2 className="font-semibold text-lg">Real-World Examples</h2>

        <Button
          onClick={handleSessionUploadFlow}
          variant="default"
          className="w-full"
        >
          Session Upload Flow (Multi-stage)
        </Button>

        <Button
          onClick={handleMultipleToasts}
          variant="outline"
          className="w-full"
        >
          Multiple Sequential Toasts
        </Button>
      </div>

      {/* Code Example */}
      <div className="p-4 border rounded-lg bg-slate-900 text-slate-100 font-mono text-sm overflow-x-auto">
        <pre>{`import { toast } from 'sonner';

// Success
toast.success('Success!', {
  description: 'Operation completed.',
});

// Error
toast.error('Error', {
  description: 'Something went wrong.',
});

// Loading (then update)
const id = toast.loading('Processing...');
setTimeout(() => {
  toast.success('Done!', { id });
}, 2000);`}</pre>
      </div>

      <div className="p-4 border rounded-lg bg-blue-50">
        <p className="text-sm text-blue-900">
          <strong>Tip:</strong> All toasts appear in the top-right corner. The close button
          allows users to dismiss them manually. Use success/error/info toasts to provide
          feedback on user actions.
        </p>
      </div>
    </div>
  );
}
