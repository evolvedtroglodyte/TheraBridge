'use client';

/**
 * Signup page - Redirects to unified login page
 * All authentication (login + signup) is now handled by /auth/login
 */

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function SignupPage() {
  const router = useRouter();

  useEffect(() => {
    // Redirect to unified auth page
    router.replace('/auth/login');
  }, [router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-white dark:bg-black">
      <p className="text-gray-500 dark:text-gray-400">Redirecting...</p>
    </div>
  );
}
