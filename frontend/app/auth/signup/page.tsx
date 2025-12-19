'use client';

import { useState, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/lib/auth-context';
import { Button } from '@/components/ui/button';
import { FormField } from '@/components/ui/form-field';
import { ErrorMessage } from '@/components/ui/error-message';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  firstNameRules,
  lastNameRules,
  emailRules,
  passwordStrongRules,
  validateFields,
  isAllValid,
} from '@/lib/validation';
import type { FormattedError } from '@/lib/error-formatter';
import { formatAuthError } from '@/lib/error-formatter';
import type { FailureResult } from '@/lib/api-types';

export default function SignupPage() {
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<'therapist' | 'patient'>('patient');
  const [serverError, setServerError] = useState<FormattedError | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const { signup } = useAuth();
  const router = useRouter();

  // Memoized validation - computed on demand, not stored in state
  const fieldValidation = useMemo(() => {
    return validateFields(
      { firstName, lastName, email, password },
      {
        firstName: firstNameRules,
        lastName: lastNameRules,
        email: emailRules,
        password: passwordStrongRules,
      }
    );
  }, [firstName, lastName, email, password]);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setServerError(null);

    // Check if form is valid (using memoized validation)
    if (!isAllValid(fieldValidation)) {
      return;
    }

    setIsLoading(true);

    try {
      await signup(email, password, firstName, lastName, role);

      // Redirect based on role
      if (role === 'therapist') {
        router.push('/therapist');
      } else {
        router.push('/patient');
      }
    } catch (err) {
      let formattedError: FormattedError;

      if (err instanceof Error) {
        // Check for specific error messages
        if (err.message.includes('already') || err.message.includes('duplicate')) {
          formattedError = formatAuthError({
            success: false,
            status: 409,
            error: 'Email already registered',
          } as FailureResult);
        } else if (err.message.includes('Invalid') || err.message.includes('validation')) {
          formattedError = {
            message: 'Invalid input',
            description: 'Please check your email and password',
            suggestion: 'Make sure your email is valid and password is strong',
            severity: 'error',
            retryable: false,
          };
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
          message: 'Signup failed',
          description: 'An unexpected error occurred',
          suggestion: 'Please try again',
          severity: 'error',
          retryable: true,
        };
      }

      setServerError(formattedError);
    } finally {
      setIsLoading(false);
    }
  };

  const isFormValid = isAllValid(fieldValidation);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 py-12 px-4">
      <div className="max-w-md w-full bg-white dark:bg-gray-800 p-8 rounded-lg shadow-md">
        <h1 className="text-2xl font-bold mb-2 text-center text-gray-900 dark:text-white">
          Create Account
        </h1>
        <p className="text-center text-gray-600 dark:text-gray-400 text-sm mb-6">
          Join TherapyBridge to get started
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

          {/* First Name Field */}
          <FormField
            name="firstName"
            label="First Name"
            type="text"
            value={firstName}
            onChange={setFirstName}
            rules={firstNameRules}
            placeholder="John"
            required
            validateOnChange
            validateOnBlur
            showErrors
            showValidationIcon
          />

          {/* Last Name Field */}
          <FormField
            name="lastName"
            label="Last Name"
            type="text"
            value={lastName}
            onChange={setLastName}
            rules={lastNameRules}
            placeholder="Doe"
            required
            validateOnChange
            validateOnBlur
            showErrors
            showValidationIcon
          />

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

          {/* Password Field with Strength Requirements */}
          <FormField
            name="password"
            label="Password"
            type="password"
            value={password}
            onChange={setPassword}
            rules={passwordStrongRules}
            placeholder="••••••••"
            required
            validateOnChange
            validateOnBlur
            showErrors
            showValidationIcon
            helpText="Must be 8+ chars with uppercase, lowercase, and numbers"
          />

          {/* Role Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              I am a... <span className="text-red-500">*</span>
            </label>
            <Select value={role} onValueChange={(val) => setRole(val as 'therapist' | 'patient')}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="patient">Patient</SelectItem>
                <SelectItem value="therapist">Therapist</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Submit Button */}
          <Button
            type="submit"
            className="w-full"
            disabled={isLoading || !isFormValid}
          >
            {isLoading ? (
              <span className="flex items-center gap-2">
                <span className="animate-spin">⏳</span>
                Creating account...
              </span>
            ) : (
              'Sign Up'
            )}
          </Button>
        </form>

        {/* Login Link */}
        <p className="mt-6 text-center text-sm text-gray-600 dark:text-gray-400">
          Already have an account?{' '}
          <Link href="/auth/login" className="text-blue-600 dark:text-blue-400 hover:underline font-medium">
            Login
          </Link>
        </p>
      </div>
    </div>
  );
}
