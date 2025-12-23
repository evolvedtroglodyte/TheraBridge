'use client';

import * as React from 'react';
import { X } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from './button';

interface DialogProps {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  title?: string;
  description?: string;
  children: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
  showClose?: boolean;
  className?: string;
}

const sizeStyles = {
  sm: 'max-w-sm',
  md: 'max-w-md',
  lg: 'max-w-lg',
  xl: 'max-w-xl',
  full: 'max-w-full w-full h-full m-0 rounded-none',
};

export const Dialog = React.forwardRef<HTMLDialogElement, DialogProps>(
  (
    {
      isOpen,
      onOpenChange,
      title,
      description,
      children,
      size = 'md',
      showClose = true,
      className,
    },
    ref
  ) => {
    const dialogRef = React.useRef<HTMLDialogElement>(null);

    React.useEffect(() => {
      const dialog =
        ref instanceof Object && 'current' in ref ? ref.current : dialogRef.current;
      if (!dialog) return;

      if (isOpen) {
        dialog.showModal();
      } else {
        dialog.close();
      }
    }, [isOpen, ref]);

    const handleClose = () => {
      onOpenChange(false);
    };

    const handleBackdropClick = (e: React.MouseEvent<HTMLDialogElement>) => {
      if (e.target === e.currentTarget) {
        handleClose();
      }
    };

    return (
      <dialog
        ref={ref || dialogRef}
        className={cn(
          'w-full rounded-lg shadow-xl backdrop:bg-black/40 backdrop:backdrop-blur-sm',
          'open:animate-in open:fade-in-0 open:zoom-in-95 open:animate-duration-200',
          'p-0 overflow-hidden',
          sizeStyles[size],
          className
        )}
        onClick={handleBackdropClick}
      >
        <div className="flex flex-col h-full max-h-[90vh]">
          {/* Header */}
          {(title || showClose) && (
            <div className="flex items-start justify-between p-6 border-b">
              <div className="flex-1">
                {title && (
                  <h2 className="text-lg font-semibold text-foreground">{title}</h2>
                )}
                {description && (
                  <p className="text-sm text-muted-foreground mt-1">{description}</p>
                )}
              </div>
              {showClose && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleClose}
                  className="ml-4 -mt-2"
                >
                  <X className="w-4 h-4" />
                </Button>
              )}
            </div>
          )}

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-6">{children}</div>
        </div>
      </dialog>
    );
  }
);

Dialog.displayName = 'Dialog';

export type { DialogProps };
