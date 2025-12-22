/**
 * Authentication helper functions using Supabase Auth
 * Provides type-safe wrappers around Supabase auth methods
 */

import { supabase } from './supabase';
import type { User } from './supabase';

export interface SignUpData {
  email: string;
  password: string;
  firstName: string;
  lastName: string;
  role: 'therapist' | 'patient';
}

export interface SignInData {
  email: string;
  password: string;
}

export interface AuthResponse {
  user: User | null;
  error: string | null;
}

/**
 * Sign up a new user
 * Creates both Supabase Auth user and custom user record via trigger
 */
export async function signUp(data: SignUpData): Promise<AuthResponse> {
  const { email, password, firstName, lastName, role } = data;

  const { data: authData, error: authError } = await supabase.auth.signUp({
    email,
    password,
    options: {
      data: {
        first_name: firstName,
        last_name: lastName,
        role: role,
      },
    },
  });

  if (authError) {
    return { user: null, error: authError.message };
  }

  if (!authData.user) {
    return { user: null, error: 'Failed to create user' };
  }

  // Fetch the custom user record that was created by the trigger
  const { data: userData, error: userError } = await supabase
    .from('users')
    .select('*')
    .eq('auth_id', authData.user.id)
    .single();

  if (userError) {
    return { user: null, error: userError.message };
  }

  return { user: userData, error: null };
}

/**
 * Sign in an existing user
 */
export async function signIn(data: SignInData): Promise<AuthResponse> {
  const { email, password } = data;

  const { data: authData, error: authError } = await supabase.auth.signInWithPassword({
    email,
    password,
  });

  if (authError) {
    return { user: null, error: authError.message };
  }

  if (!authData.user) {
    return { user: null, error: 'Failed to sign in' };
  }

  // Fetch the custom user record
  const { data: userData, error: userError } = await supabase
    .from('users')
    .select('*')
    .eq('auth_id', authData.user.id)
    .single();

  if (userError) {
    return { user: null, error: userError.message };
  }

  return { user: userData, error: null };
}

/**
 * Sign out the current user
 */
export async function signOut(): Promise<{ error: string | null }> {
  const { error } = await supabase.auth.signOut();
  return { error: error ? error.message : null };
}

/**
 * Send password reset email
 */
export async function resetPassword(email: string): Promise<{ error: string | null }> {
  const { error } = await supabase.auth.resetPasswordForEmail(email, {
    redirectTo: `${window.location.origin}/auth/reset-password`,
  });
  return { error: error ? error.message : null };
}

/**
 * Update password (after clicking reset link)
 */
export async function updatePassword(newPassword: string): Promise<{ error: string | null }> {
  const { error } = await supabase.auth.updateUser({
    password: newPassword,
  });
  return { error: error ? error.message : null };
}

/**
 * Get current session
 */
export async function getSession() {
  const { data: { session }, error } = await supabase.auth.getSession();
  return { session, error };
}

/**
 * Get current user (both auth user and custom user record)
 */
export async function getCurrentUser(): Promise<{ user: User | null; error: string | null }> {
  const { data: { user: authUser }, error: authError } = await supabase.auth.getUser();

  if (authError || !authUser) {
    return { user: null, error: authError?.message || 'No user found' };
  }

  const { data: userData, error: userError } = await supabase
    .from('users')
    .select('*')
    .eq('auth_id', authUser.id)
    .single();

  if (userError) {
    return { user: null, error: userError.message };
  }

  return { user: userData, error: null };
}

/**
 * Sign in with OAuth provider (Google, GitHub, etc.)
 */
export async function signInWithOAuth(provider: 'google' | 'github') {
  const { data, error } = await supabase.auth.signInWithOAuth({
    provider,
    options: {
      redirectTo: `${window.location.origin}/auth/callback`,
    },
  });

  return { data, error: error ? error.message : null };
}

/**
 * Resend email verification
 */
export async function resendVerificationEmail(email: string): Promise<{ error: string | null }> {
  const { error } = await supabase.auth.resend({
    type: 'signup',
    email,
  });
  return { error: error ? error.message : null };
}
