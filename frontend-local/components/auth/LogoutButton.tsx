'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { LogOut, Loader2 } from 'lucide-react';
import { Button, type ButtonProps } from '@/components/ui/button';
import { ConfirmationDialog } from '@/components/ui/confirmation-dialog';
import { useAuth } from '@/contexts/AuthContext';

interface LogoutButtonProps extends ButtonProps {
  showIcon?: boolean;
  variant?: ButtonProps['variant'];
}

export function LogoutButton({ showIcon = true, variant = 'ghost', ...props }: LogoutButtonProps) {
  const [showConfirm, setShowConfirm] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();
  const { logout } = useAuth();

  const handleLogoutClick = () => {
    setShowConfirm(true);
  };

  const handleConfirmLogout = async () => {
    setIsLoading(true);
    try {
      // Clear auth context
      logout();

      // Clear any session storage
      localStorage.removeItem('sessionData');
      localStorage.removeItem('userPreferences');
      sessionStorage.clear();

      // Redirect to login
      router.push('/auth/login');
    } catch (error) {
      setIsLoading(false);
      throw error;
    }
  };

  return (
    <>
      <Button
        variant={variant}
        onClick={handleLogoutClick}
        title="Logout from TherapyBridge"
        {...props}
      >
        {showIcon && <LogOut className="w-4 h-4 mr-2" />}
        Logout
      </Button>

      <ConfirmationDialog
        isOpen={showConfirm}
        onOpenChange={setShowConfirm}
        title="Logout?"
        description="You will be logged out of your TherapyBridge account."
        warning="Make sure you've saved any important information before logging out."
        onConfirm={handleConfirmLogout}
        confirmLabel="Logout"
        cancelLabel="Stay Logged In"
        variant="default"
        isDangerous={false}
        isLoading={isLoading}
      />
    </>
  );
}

export type { LogoutButtonProps };
