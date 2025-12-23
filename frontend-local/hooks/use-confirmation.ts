import { useState, useCallback } from 'react';

interface ConfirmationOptions {
  title: string;
  description?: string;
  warning?: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: 'destructive' | 'default' | 'warning';
  isDangerous?: boolean;
}

export function useConfirmation() {
  const [state, setState] = useState<{
    isOpen: boolean;
    title: string;
    description: string;
    warning: string;
    confirmLabel: string;
    cancelLabel: string;
    variant: 'destructive' | 'default' | 'warning';
    isDangerous: boolean;
    onConfirm: ((options?: any) => Promise<void> | void) | null;
  }>({
    isOpen: false,
    title: '',
    description: '',
    warning: '',
    confirmLabel: 'Confirm',
    cancelLabel: 'Cancel',
    variant: 'default',
    isDangerous: false,
    onConfirm: null,
  });

  const [isLoading, setIsLoading] = useState(false);

  const confirm = useCallback(
    async (options: ConfirmationOptions, onConfirmCallback: () => Promise<void> | void) => {
      return new Promise<boolean>((resolve) => {
        setState({
          isOpen: true,
          title: options.title,
          description: options.description || '',
          warning: options.warning || '',
          confirmLabel: options.confirmLabel || 'Confirm',
          cancelLabel: options.cancelLabel || 'Cancel',
          variant: options.variant || 'default',
          isDangerous: options.isDangerous || false,
          onConfirm: async () => {
            setIsLoading(true);
            try {
              await onConfirmCallback();
              resolve(true);
            } catch (error) {
              throw error;
            } finally {
              setIsLoading(false);
            }
          },
        });
      });
    },
    []
  );

  const close = useCallback(() => {
    setState((prev) => ({ ...prev, isOpen: false }));
  }, []);

  return {
    ...state,
    isLoading,
    confirm,
    onOpenChange: (isOpen: boolean) => {
      if (!isOpen) {
        close();
      }
    },
    onConfirm: state.onConfirm || (() => {}),
  };
}
