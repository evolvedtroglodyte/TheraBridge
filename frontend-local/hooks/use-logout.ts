'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';

export function useLogout() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();
  const { logout } = useAuth();

  const performLogout = async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Call the logout function from auth context
      logout();

      // Clear any session data
      localStorage.removeItem('sessionData');
      localStorage.removeItem('userPreferences');

      // Redirect to login page
      router.push('/auth/login');
      return true;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to logout';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  return {
    performLogout,
    isLoading,
    error,
  };
}
