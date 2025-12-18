'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { apiClient } from './api-client';
import { tokenStorage } from './token-storage';

interface User {
  id: string;
  email: string;
  full_name: string;
  role: 'therapist' | 'patient' | 'admin';
  is_active: boolean;
  created_at: string;
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string, firstName: string, lastName: string, role: string) => Promise<void>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }): React.ReactNode {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Check auth status on mount
  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async (): Promise<void> => {
    if (!tokenStorage.hasTokens()) {
      setIsLoading(false);
      return;
    }

    try {
      const result = await apiClient.get<User>('/api/v1/auth/me');
      if (result.success) {
        setUser(result.data);
      } else {
        tokenStorage.clearTokens();
        setUser(null);
      }
    } catch {
      tokenStorage.clearTokens();
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (email: string, password: string): Promise<void> => {
    const result = await apiClient.post<{
      access_token: string;
      refresh_token: string;
    }>('/api/v1/auth/login', { email, password });

    if (result.success) {
      tokenStorage.saveTokens(result.data.access_token, result.data.refresh_token);
      await checkAuth();
    } else {
      throw new Error(result.error || 'Login failed');
    }
  };

  const signup = async (email: string, password: string, firstName: string, lastName: string, role: string): Promise<void> => {
    const result = await apiClient.post<{
      access_token: string;
      refresh_token: string;
    }>('/api/v1/auth/signup', {
      email,
      password,
      first_name: firstName,
      last_name: lastName,
      role,
    });

    if (result.success) {
      tokenStorage.saveTokens(result.data.access_token, result.data.refresh_token);
      await checkAuth();
    } else {
      throw new Error(result.error || 'Signup failed');
    }
  };

  const logout = async (): Promise<void> => {
    const refreshToken = tokenStorage.getRefreshToken();

    if (refreshToken) {
      try {
        await apiClient.post('/api/v1/auth/logout', { refresh_token: refreshToken });
      } catch {
        // Ignore errors (already logged out on server)
      }
    }

    tokenStorage.clearTokens();
    setUser(null);
  };

  const value = {
    user,
    isLoading,
    isAuthenticated: !!user,
    login,
    signup,
    logout,
    checkAuth,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
