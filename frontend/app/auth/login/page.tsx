'use client';

import { useState, useEffect, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/lib/auth-context';
import { Button } from '@/components/ui/button';
import { FormField } from '@/components/ui/form-field';
import { ErrorMessage } from '@/components/ui/error-message';
import { emailRules, passwordRules, validateFields, isAllValid } from '@/lib/validation';
import type { FormattedError } from '@/lib/error-formatter';
import { formatAuthError } from '@/lib/error-formatter';
import type { FailureResult } from '@/lib/api-types';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [serverError, setServerError] = useState<FormattedError | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [shouldRedirect, setShouldRedirect] = useState(false);

  const { login, user, isAuthenticated } = useAuth();
  const router = useRouter();

  // Handle redirect after successful login when user state is updated
  useEffect(() => {
    if (shouldRedirect && isAuthenticated && user) {
      if (user.role === 'therapist') {
        router.push('/therapist');
      } else if (user.role === 'patient') {
        router.push('/patient');
      } else {
        router.push('/');
      }
    }
  }, [shouldRedirect, isAuthenticated, user, router]);

  // Memoized validation - computed on demand, not stored in state
  const fieldValidation = useMemo(() => {
    return validateFields(
      { email, password },
      { email: emailRules, password: passwordRules }
    );
  }, [email, password]);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setServerError(null);

    // Check if form is valid (using memoized validation)
    if (!isAllValid(fieldValidation)) {
      return;
    }

    setIsLoading(true);

    try {
      await login(email, password);
      setShouldRedirect(true); // Trigger redirect in useEffect once user state updates
    } catch (err: unknown) {
      let formattedError: FormattedError;

      if (err instanceof Error) {
        // Check for specific error messages from auth context
        if (err.message.includes('Invalid') || err.message.includes('incorrect')) {
          formattedError = formatAuthError({
            success: false,
            status: 401,
            error: 'Invalid email or password',
          } as FailureResult);
        } else if (err.message.includes('network')) {
          formattedError = {
            message: 'Network error',
            description: 'Unable to connect to the server',
            suggestion: 'Check your internet connection and try again',
            severity: 'error',
            retryable: true,
          };
        } else {
          formattedError = formatAuthError({
            success: false,
            status: 500,
            error: err.message,
          } as FailureResult);
        }
      } else {
        formattedError = {
          message: 'Login failed',
          description: 'An unexpected error occurred',
          suggestion: 'Please try again',
          severity: 'error',
          retryable: true,
        };
      }

      setServerError(formattedError);
      setIsLoading(false);
    }
  };

  const isFormValid = isAllValid(fieldValidation);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
      <div className="max-w-md w-full bg-white dark:bg-gray-800 p-8 rounded-lg shadow-md">
        <h1 className="text-2xl font-bold mb-2 text-center text-gray-900 dark:text-white">
          Welcome Back
        </h1>
        <p className="text-center text-gray-600 dark:text-gray-400 text-sm mb-6">
          Login to TherapyBridge to access your account
        </p>

        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Server Error Alert */}
          {serverError && (
            <ErrorMessage
              message={serverError.message}
              description={serverError.description}
              variant="alert"
              severity={serverError.severity}
              dismissible
              onDismiss={() => setServerError(null)}
            />
          )}

          {/* Email Field */}
          <FormField
            name="email"
            label="Email Address"
            type="email"
            value={email}
            onChange={setEmail}
            rules={emailRules}
            placeholder="you@example.com"
            required
            validateOnChange
            validateOnBlur
            showErrors
            showValidationIcon
          />

          {/* Password Field */}
          <FormField
            name="password"
            label="Password"
            type="password"
            value={password}
            onChange={setPassword}
            rules={passwordRules}
            placeholder="••••••••"
            required
            validateOnChange
            validateOnBlur
            showErrors
            showValidationIcon
            helpText="At least 8 characters"
          />

          {/* Submit Button */}
          <Button
            type="submit"
            className="w-full"
            disabled={isLoading || !isFormValid}
          >
            {isLoading ? (
              <span className="flex items-center gap-2">
                <span className="animate-spin">⏳</span>
                Logging in...
              </span>
            ) : (
              'Login'
            )}
          </Button>
        </form>

        {/* Sign Up Link */}
        <p className="mt-6 text-center text-sm text-gray-600 dark:text-gray-400">
          Don&apos;t have an account?{' '}
          <Link href="/auth/signup" className="text-blue-600 dark:text-blue-400 hover:underline font-medium">
            Sign up
          </Link>
        </p>
      </div>
    </div>
  );
}
