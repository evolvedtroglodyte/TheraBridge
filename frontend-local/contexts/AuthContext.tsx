'use client';

/**
 * Authentication Context
 * Provides auth state and methods throughout the app
 *
 * NOTE: This version works WITHOUT a custom users table.
 * User data is derived from Supabase Auth's built-in user object.
 */

import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { supabase } from '@/lib/supabase';
import type { User } from '@/lib/supabase';
import type { Session, User as AuthUser } from '@supabase/supabase-js';

interface AuthContextType {
  user: User | null;
  session: Session | null;
  loading: boolean;
  isLoading: boolean; // Alias for loading
  isAuthenticated: boolean;
  signOut: () => Promise<void>;
  logout: () => Promise<void>; // Alias for signOut
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

/**
 * Convert Supabase Auth user to our User type
 * No database query needed - uses auth metadata
 */
function authUserToUser(authUser: AuthUser): User {
  const metadata = authUser.user_metadata || {};

  // Try to get name from various sources
  const fullName = metadata.full_name || metadata.name || '';
  const nameParts = fullName.split(' ');

  return {
    id: authUser.id,
    email: authUser.email || '',
    first_name: metadata.first_name || nameParts[0] || '',
    last_name: metadata.last_name || nameParts.slice(1).join(' ') || '',
    role: 'patient', // Default role - all users are patients for now
    created_at: authUser.created_at,
    updated_at: authUser.updated_at || authUser.created_at,
  };
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if dev bypass is enabled
    const devBypass = process.env.NEXT_PUBLIC_DEV_BYPASS_AUTH === 'true';

    // Get initial session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      if (session?.user) {
        // Convert auth user to our User type (no database query)
        setUser(authUserToUser(session.user));
        setLoading(false);
      } else if (devBypass) {
        // Create mock user for dev bypass mode
        const mockUser: User = {
          id: 'dev-bypass-user-id',
          email: 'dev@therapybridge.local',
          first_name: 'Dev',
          last_name: 'User',
          role: 'patient',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        };
        setUser(mockUser);
        console.log('🔓 Using mock user (dev bypass mode)');
        setLoading(false);
      } else {
        setLoading(false);
      }
    });

    // Listen for auth changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(async (_event, session) => {
      setSession(session);
      if (session?.user) {
        // Convert auth user to our User type (no database query)
        setUser(authUserToUser(session.user));
        setLoading(false);
      } else if (devBypass) {
        // Keep mock user even if session changes in dev mode
        const mockUser: User = {
          id: 'dev-bypass-user-id',
          email: 'dev@therapybridge.local',
          first_name: 'Dev',
          last_name: 'User',
          role: 'patient',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        };
        setUser(mockUser);
        setLoading(false);
      } else {
        setUser(null);
        setLoading(false);
      }
    });

    return () => {
      subscription.unsubscribe();
    };
  }, []);

  async function handleSignOut() {
    await supabase.auth.signOut();
    setUser(null);
    setSession(null);
  }

  const value = {
    user,
    session,
    loading,
    isLoading: loading, // Alias for backward compatibility
    isAuthenticated: !!user,
    signOut: handleSignOut,
    logout: handleSignOut, // Alias for backward compatibility
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
