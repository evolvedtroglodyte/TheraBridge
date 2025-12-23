'use client';

import * as React from 'react';
import { AlertTriangle, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from './button';

interface ConfirmationDialogProps {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description?: string;
  warning?: string;
  onConfirm: () => void | Promise<void>;
  onCancel?: () => void;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: 'destructive' | 'default' | 'warning';
  isDangerous?: boolean;
  isLoading?: boolean;
  disabled?: boolean;
}

const variantStyles = {
  destructive: {
    icon: 'text-red-600 dark:text-red-400',
    title: 'text-red-900 dark:text-red-100',
    button: 'destructive',
  },
  warning: {
    icon: 'text-amber-600 dark:text-amber-400',
    title: 'text-amber-900 dark:text-amber-100',
    button: 'default',
  },
  default: {
    icon: 'text-blue-600 dark:text-blue-400',
    title: 'text-foreground',
    button: 'default',
  },
};

export const ConfirmationDialog = React.forwardRef<
  HTMLDialogElement,
  ConfirmationDialogProps
>(
  (
    {
      isOpen,
      onOpenChange,
      title,
      description,
      warning,
      onConfirm,
      onCancel,
      confirmLabel = 'Confirm',
      cancelLabel = 'Cancel',
      variant = 'default',
      isDangerous = false,
      isLoading = false,
      disabled = false,
    },
    ref
  ) => {
    const dialogRef = React.useRef<HTMLDialogElement>(null);
    const [isConfirming, setIsConfirming] = React.useState(false);
    const [error, setError] = React.useState<string | null>(null);

    React.useEffect(() => {
      const dialog = ref instanceof Object && 'current' in ref ? ref.current : dialogRef.current;
      if (!dialog) return;

      if (isOpen) {
        dialog.showModal();
      } else {
        dialog.close();
      }
    }, [isOpen, ref]);

    const handleClose = () => {
      onOpenChange(false);
      onCancel?.();
      setError(null);
      setIsConfirming(false);
    };

    const handleConfirm = async () => {
      setError(null);
      setIsConfirming(true);

      try {
        await onConfirm();
        handleClose();
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'An error occurred';
        setError(errorMessage);
        setIsConfirming(false);
      }
    };

    const handleBackdropClick = (e: React.MouseEvent<HTMLDialogElement>) => {
      if (e.target === e.currentTarget) {
        handleClose();
      }
    };

    const styles = variantStyles[variant];

    return (
      <dialog
        ref={ref || dialogRef}
        className="w-full max-w-sm rounded-lg shadow-xl backdrop:bg-black/40 backdrop:backdrop-blur-sm open:animate-in open:fade-in-0 open:zoom-in-95 open:animate-duration-200"
        onClick={handleBackdropClick}
      >
        <div className="p-6">
          {/* Header with icon */}
          <div className="flex gap-4 mb-4">
            <div className={cn(
              'flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center',
              variant === 'destructive' ? 'bg-red-100 dark:bg-red-900/30' : 'bg-amber-100 dark:bg-amber-900/30'
            )}>
              <AlertTriangle className={cn('w-6 h-6', styles.icon)} />
            </div>
            <div className="flex-1">
              <h2 className={cn('text-lg font-semibold', styles.title)}>
                {title}
              </h2>
            </div>
          </div>

          {/* Description */}
          {description && (
            <p className="text-sm text-muted-foreground mb-4">
              {description}
            </p>
          )}

          {/* Warning text */}
          {warning && (
            <div className="p-3 rounded-md bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 mb-4">
              <p className="text-sm text-amber-900 dark:text-amber-100">
                {warning}
              </p>
            </div>
          )}

          {/* Error message */}
          {error && (
            <div className="p-3 rounded-md bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 mb-4">
              <p className="text-sm text-red-900 dark:text-red-100">
                {error}
              </p>
            </div>
          )}

          {/* Action buttons */}
          <div className="flex gap-3 justify-end mt-6">
            <Button
              variant="outline"
              onClick={handleClose}
              disabled={isConfirming || isLoading || disabled}
            >
              {cancelLabel}
            </Button>
            <Button
              variant={isDangerous ? 'destructive' : styles.button as 'default' | 'destructive'}
              onClick={handleConfirm}
              disabled={isConfirming || isLoading || disabled}
            >
              {isConfirming || isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  {confirmLabel}
                </>
              ) : (
                confirmLabel
              )}
            </Button>
          </div>

          {/* Close button (keyboard: ESC) */}
          <div className="mt-4 text-center text-xs text-muted-foreground">
            Press <kbd className="px-1.5 py-0.5 bg-muted rounded text-foreground font-mono">ESC</kbd> to close
          </div>
        </div>
      </dialog>
    );
  }
);

ConfirmationDialog.displayName = 'ConfirmationDialog';

export type { ConfirmationDialogProps };
