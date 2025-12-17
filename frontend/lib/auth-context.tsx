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
  signup: (email: string, password: string, fullName: string, role: string) => Promise<void>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Check auth status on mount
  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    if (!tokenStorage.hasTokens()) {
      setIsLoading(false);
      return;
    }

    try {
      const userData = await apiClient.get<User>('/auth/me');
      setUser(userData);
    } catch (error) {
      tokenStorage.clearTokens();
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (email: string, password: string) => {
    const response = await apiClient.post<{
      access_token: string;
      refresh_token: string;
    }>('/auth/login', { email, password });

    tokenStorage.saveTokens(response.access_token, response.refresh_token);
    await checkAuth();
  };

  const signup = async (email: string, password: string, fullName: string, role: string) => {
    const response = await apiClient.post<{
      access_token: string;
      refresh_token: string;
    }>('/auth/signup', {
      email,
      password,
      full_name: fullName,
      role,
    });

    tokenStorage.saveTokens(response.access_token, response.refresh_token);
    await checkAuth();
  };

  const logout = async () => {
    const refreshToken = tokenStorage.getRefreshToken();

    if (refreshToken) {
      try {
        await apiClient.post('/auth/logout', { refresh_token: refreshToken });
      } catch (error) {
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

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
