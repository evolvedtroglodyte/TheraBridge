'use client';

/**
 * TheraBridge Authentication Page
 *
 * Complete auth flow:
 * - Main: Login/Signup options (Email + Google OAuth)
 * - Email Form: Enter email address
 * - Check Email: Confirmation that magic link/OTP was sent
 * - Enter Code: Input field for OTP code
 * - Password: Set or enter password
 * - Error: Authentication error display
 *
 * Features:
 * - Light/Dark mode (click logo to toggle)
 * - Animated buttons with hover/active states
 * - Loading states with spinner
 * - Supabase Magic Link + OTP integration
 * - Google OAuth
 */

import { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { supabase } from '@/lib/supabase';
import { signInWithOAuth } from '@/lib/auth';
import { getTheme, setTheme as saveTheme } from '@/lib/theme-storage';

// Auth step types
type AuthStep = 'main' | 'emailForm' | 'checkEmail' | 'enterCode' | 'password' | 'error';

// Color scheme
const colors = {
  teal: '#4ECDC4',
  tealBorder: '#5ED9D0',
  purple: '#7882E7',
  purpleBorder: '#8894E8',
  black: '#000000',
  white: '#FFFFFF',
  textLight: '#e3e4e6',
  textMuted: '#969799',
  buttonDark: '#1e2025',
  buttonBorderDark: '#2c2e33',
  buttonLight: '#f5f5f5',
  buttonBorderLight: '#e0e0e0',
};

function AuthPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  // Auth state - always starts in light mode, signup by default
  const [darkMode, setDarkMode] = useState(false);
  const [isLogin, setIsLogin] = useState(false); // Default to signup
  const [authStep, setAuthStep] = useState<AuthStep>('main');
  const [email, setEmail] = useState('');
  const [code, setCode] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState('');
  const [isNewUser, setIsNewUser] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [showDemoButton, setShowDemoButton] = useState(true); // For DEMO button toggle

  // Handle URL params from callback (magic link redirect, error, etc.)
  useEffect(() => {
    const error = searchParams.get('error');
    const step = searchParams.get('step');
    const emailParam = searchParams.get('email');
    const isNewParam = searchParams.get('new');
    const oauthParam = searchParams.get('oauth');

    if (error) {
      setErrorMessage(error);
      setAuthStep('error');
    } else if (step === 'enterCode' && emailParam && oauthParam === 'true') {
      // OAuth user needs to verify email - redirected from callback
      setEmail(emailParam);
      setAuthStep('enterCode');
    } else if (step === 'password' && emailParam) {
      // Redirected from callback - go to password setup
      setEmail(emailParam);
      setIsNewUser(isNewParam === 'true');
      setAuthStep('password');
    }
  }, [searchParams]);

  // Handle magic link hash fragments (Supabase redirects with #access_token=...)
  // Note: OAuth users are now handled by the callback route, not here
  useEffect(() => {
    const handleAuthRedirect = async () => {
      // Check if there's a hash fragment with access_token
      if (typeof window !== 'undefined' && window.location.hash.includes('access_token')) {
        setIsLoading('magiclink');

        // Supabase client automatically processes the hash
        const { data: { session }, error: sessionError } = await supabase.auth.getSession();

        if (sessionError || !session?.user) {
          setIsLoading(null);
          return;
        }

        const authUser = session.user;

        // For email/magic link users, check if they need to set a password
        const hasPassword = authUser.user_metadata?.has_password === true;

        if (!hasPassword) {
          // New user or user without password - go to password setup
          setEmail(authUser.email || '');
          setIsNewUser(true);
          setAuthStep('password');
          setIsLoading(null);
          window.history.replaceState(null, '', window.location.pathname);
        } else {
          // User has password - go to dashboard
          window.location.href = '/patient';
        }
      }
    };

    handleAuthRedirect();
  }, [router]);

  // Derived colors based on dark mode
  const bg = darkMode ? colors.black : colors.white;
  const text = darkMode ? colors.textLight : '#1a1a1a';
  const accent = darkMode ? colors.purple : colors.teal;
  const accentBorder = darkMode ? colors.purpleBorder : colors.tealBorder;
  const buttonBg = darkMode ? colors.buttonDark : colors.buttonLight;
  const buttonBorder = darkMode ? colors.buttonBorderDark : colors.buttonBorderLight;
  const mutedText = darkMode ? colors.textMuted : '#666666';
  const theraColor = darkMode ? '#B8B5B0' : '#6B6560';

  // Reset to main auth screen
  const handleBackToLogin = () => {
    setAuthStep('main');
    setEmail('');
    setCode('');
    setPassword('');
    setConfirmPassword('');
    setErrorMessage('');
    setIsNewUser(false);
  };

  // Handle auth button clicks
  const handleButtonClick = async (buttonName: string) => {
    setIsLoading(buttonName);

    if (buttonName === 'email') {
      setTimeout(() => {
        setIsLoading(null);
        setAuthStep('emailForm');
      }, 300);
    } else if (buttonName === 'google') {
      const { error } = await signInWithOAuth('google');
      if (error) {
        setErrorMessage(error);
        setAuthStep('error');
      }
      setIsLoading(null);
    }
  };

  // Handle email submission - check if email exists first
  const handleEmailSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;
    setIsLoading('submit');
    setErrorMessage('');

    try {
      // Check if email already exists
      const response = await fetch('/api/check-email', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });

      const data = await response.json();

      if (!response.ok) {
        setErrorMessage('Failed to verify email. Please try again.');
        setIsLoading(null);
        return;
      }

      // SIGNUP MODE: Check if email already exists
      if (!isLogin && data.exists) {
        if (data.provider === 'google') {
          setErrorMessage('An account with this email already exists (Google account). Please use "Continue with Google" to sign in.');
        } else {
          setErrorMessage('An account with this email already exists. Please log in instead.');
        }
        setIsLoading(null);
        return;
      }

      // LOGIN MODE: Check if email exists
      if (isLogin && !data.exists) {
        setErrorMessage('No account found with this email. Please sign up first.');
        setIsLoading(null);
        return;
      }

      // Proceed to password page
      setIsNewUser(!isLogin);
      setAuthStep('password');
      setIsLoading(null);
    } catch (err) {
      console.error('Email check error:', err);
      setErrorMessage('Something went wrong. Please try again.');
      setIsLoading(null);
    }
  };

  // Handle OTP code verification
  const handleCodeSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!code) return;
    setIsLoading('codeSubmit');

    try {
      const { data, error } = await supabase.auth.verifyOtp({
        email,
        token: code,
        type: 'email',
      });

      if (error) {
        setErrorMessage(error.message || 'Invalid code. Please try again.');
        setAuthStep('error');
        setIsLoading(null);
        return;
      }

      if (data.user) {
        // Check if this is an OAuth user verifying for the first time
        const provider = data.user.app_metadata?.provider;
        const isOAuthUser = provider && provider !== 'email';

        if (isOAuthUser) {
          // Set oauth_verified flag so they don't need to verify again
          const { error: updateError } = await supabase.auth.updateUser({
            data: { oauth_verified: true }
          });

          if (updateError) {
            console.error('Failed to update user metadata:', updateError);
          }

          // OAuth user verified - go straight to dashboard
          window.location.href = '/patient';
          return;
        }

        // Email/password user - go to password setup
        setAuthStep('password');
        setIsLoading(null);
      }
    } catch (err) {
      console.error('Code verification error:', err);
      setErrorMessage('Something went wrong. Please try again.');
      setAuthStep('error');
      setIsLoading(null);
    }
  };

  // Handle password submission - separate flows for login vs signup
  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!password) return;

    setErrorMessage('');

    if (password.length < 6) {
      setErrorMessage('Password must be at least 6 characters');
      return;
    }

    // For signup, check password confirmation
    if (isNewUser && password !== confirmPassword) {
      setErrorMessage('Passwords do not match');
      return;
    }

    setIsLoading('passwordSubmit');

    try {
      if (isNewUser) {
        // SIGNUP FLOW
        const { error: signUpError } = await supabase.auth.signUp({
          email,
          password,
        });

        if (signUpError) {
          // Check if user already exists
          if (signUpError.message.includes('already registered')) {
            setErrorMessage('An account with this email already exists. Please log in instead.');
          } else {
            setErrorMessage(signUpError.message);
          }
          setIsLoading(null);
          return;
        }

        // Sign up successful - go to dashboard
        window.location.href = '/patient/dashboard-v3';
      } else {
        // LOGIN FLOW
        const { error: signInError } = await supabase.auth.signInWithPassword({
          email,
          password,
        });

        if (signInError) {
          // Check if it's an invalid credentials error
          if (signInError.message.includes('Invalid login credentials')) {
            setErrorMessage('Incorrect password. Please try again or sign up for a new account.');
          } else {
            setErrorMessage(signInError.message);
          }
          setIsLoading(null);
          return;
        }

        // Sign in successful - go to dashboard
        window.location.href = '/patient/dashboard-v3';
      }
    } catch (err) {
      console.error('Password submit error:', err);
      setErrorMessage('Something went wrong. Please try again.');
      setIsLoading(null);
    }
  };

  // Geometric Bridge Icon
  // Handle theme toggle (saves to session storage)
  const handleThemeToggle = () => {
    const newTheme = !darkMode;
    setDarkMode(newTheme);
    saveTheme(newTheme ? 'dark' : 'light');
  };

  const GeometricBridgeIcon = ({ size = 48, clickable = false }: { size?: number; clickable?: boolean }) => (
    <svg
      width={size}
      height={size}
      viewBox="0 0 80 80"
      fill="none"
      onClick={clickable ? handleThemeToggle : undefined}
      style={clickable ? {
        cursor: 'pointer',
        transition: 'transform 0.2s ease, filter 0.2s ease',
      } : {}}
      onMouseEnter={clickable ? (e) => {
        e.currentTarget.style.transform = 'scale(1.05)';
        e.currentTarget.style.filter = 'brightness(1.2)';
      } : undefined}
      onMouseLeave={clickable ? (e) => {
        e.currentTarget.style.transform = 'scale(1)';
        e.currentTarget.style.filter = 'brightness(1)';
      } : undefined}
    >
      <path
        d="M10 55 L25 30 L40 40 L55 30 L70 55"
        stroke={accent}
        strokeWidth="4"
        strokeLinejoin="round"
        strokeLinecap="round"
        fill="none"
      />
      <line x1="25" y1="30" x2="25" y2="55" stroke={darkMode ? '#ffffff' : '#333333'} strokeWidth="2.5" opacity="0.5" />
      <line x1="40" y1="40" x2="40" y2="55" stroke={darkMode ? '#ffffff' : '#333333'} strokeWidth="2.5" opacity="0.5" />
      <line x1="55" y1="30" x2="55" y2="55" stroke={darkMode ? '#ffffff' : '#333333'} strokeWidth="2.5" opacity="0.5" />
    </svg>
  );

  // Loading Spinner
  const Spinner = () => (
    <svg
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      className="animate-spin"
    >
      <circle
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="round"
        strokeDasharray="32"
        strokeDashoffset="12"
        opacity="0.9"
      />
    </svg>
  );

  // Auth Button Component
  const AuthButton = ({
    children,
    primary,
    onClick,
    loading,
    icon,
    type = 'button',
  }: {
    children: React.ReactNode;
    primary?: boolean;
    onClick?: () => void;
    loading?: boolean;
    icon?: React.ReactNode;
    type?: 'button' | 'submit';
  }) => (
    <button
      type={type}
      onClick={onClick}
      disabled={loading}
      className="w-full h-12 flex items-center justify-center gap-2 px-4 rounded-md font-medium text-[13px] transition-all duration-150 disabled:opacity-80"
      style={{
        backgroundColor: primary ? accent : buttonBg,
        color: primary ? (darkMode ? '#fefeff' : '#ffffff') : text,
        border: `0.56px solid ${primary ? accentBorder : buttonBorder}`,
        boxShadow: 'rgba(0,0,0,0.06) 0px 4px 4px -1px, rgba(0,0,0,0.118) 0px 1px 1px 0px',
        cursor: loading ? 'wait' : 'pointer',
      }}
      onMouseEnter={(e) => {
        if (!loading) {
          e.currentTarget.style.filter = 'brightness(1.1)';
          e.currentTarget.style.transform = 'translateY(-1px)';
        }
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.filter = 'brightness(1)';
        e.currentTarget.style.transform = 'translateY(0)';
      }}
    >
      {loading ? <Spinner /> : (
        <>
          {icon}
          {children}
        </>
      )}
    </button>
  );

  // Google Icon
  const GoogleIcon = () => (
    <svg width="16" height="16" viewBox="0 0 24 24">
      <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
      <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
      <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
      <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
    </svg>
  );

  // Eye Icon (show password)
  const EyeIcon = () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke={darkMode ? '#ffffff' : '#000000'} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  );

  // Eye Off Icon (hide password)
  const EyeOffIcon = () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke={darkMode ? '#ffffff' : '#000000'} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" />
      <line x1="1" y1="1" x2="23" y2="23" />
    </svg>
  );

  // Input styles
  const inputStyle: React.CSSProperties = {
    width: '100%',
    height: '48px',
    padding: '0 14px',
    fontSize: '13px',
    fontFamily: 'inherit',
    backgroundColor: buttonBg,
    border: `0.56px solid ${buttonBorder}`,
    borderRadius: '6px',
    color: text,
    transition: 'border-color 0.15s ease',
    boxSizing: 'border-box',
    outline: 'none',
  };

  // Get title based on auth step
  const getTitle = () => {
    switch (authStep) {
      case 'emailForm':
        return isLogin ? "What's your email address?" : "What's your email address?";
      case 'checkEmail':
        return 'Check your email';
      case 'enterCode':
        return 'Check your email';
      case 'password':
        return isNewUser ? 'Create your password' : 'Enter your password';
      case 'error':
        return 'Authentication error';
      default:
        return isLogin ? 'Log in to TheraBridge' : 'Create your account';
    }
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        backgroundColor: bg,
        display: 'flex',
        flexDirection: 'column',
        fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        color: text,
        transition: 'background-color 0.3s ease',
        overflow: 'hidden',
      }}
    >
      {/* Header */}
      <header
        style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          padding: '14px 24px',
          backgroundColor: darkMode ? 'rgba(10,10,10,0.8)' : 'rgba(250,250,250,0.8)',
          backdropFilter: 'blur(8px)',
          borderBottom: darkMode ? 'none' : '1px solid #E8E8E8',
          position: 'relative',
          zIndex: 10,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <GeometricBridgeIcon size={36} />
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '5px',
              fontSize: '18px',
              letterSpacing: '3px',
              textTransform: 'uppercase',
            }}
          >
            <span style={{ fontWeight: 300, color: theraColor }}>THERA</span>
            <span style={{ fontWeight: 500, color: accent }}>BRIDGE</span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          padding: '48px 0',
          background: darkMode
            ? 'linear-gradient(rgb(15, 16, 17) 0%, rgb(8, 8, 8) 50%)'
            : 'linear-gradient(rgb(255, 255, 255) 0%, rgb(250, 250, 250) 50%)',
        }}
      >
        {/* Content Container */}
        <div
          style={{
            width: '100%',
            height: 'fit-content',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            marginTop: '207px',
          }}
        >
          {/* Logo - Click to toggle dark/light mode */}
          <div style={{ marginBottom: '32px' }} title="Click to toggle dark/light mode">
            <GeometricBridgeIcon size={53} clickable={true} />
          </div>

          {/* Auth Container */}
          <div style={{ width: '288px', display: 'flex', flexDirection: 'column' }}>
            {/* Title */}
            <h1
              style={{
                fontWeight: 500,
                fontSize: '18px',
                textAlign: 'center',
                margin: '0 0 24px 0',
                color: text,
              }}
            >
              {getTitle()}
            </h1>

            {/* Error Screen */}
            {authStep === 'error' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', alignItems: 'center' }}>
                <p style={{ fontSize: '13px', color: mutedText, textAlign: 'center', margin: '0 0 16px 0', lineHeight: 1.6 }}>
                  {errorMessage}
                </p>
                <AuthButton primary onClick={handleBackToLogin}>
                  {isLogin ? 'Back to login' : 'Back to sign up'}
                </AuthButton>
              </div>
            )}

            {/* Check Email Screen */}
            {authStep === 'checkEmail' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', alignItems: 'center' }}>
                <p style={{ fontSize: '13px', color: mutedText, textAlign: 'center', margin: '0 0 8px 0', lineHeight: 1.6 }}>
                  We&apos;ve sent you a temporary login code.<br />
                  Please check your inbox at<br />
                  <span style={{ color: text, fontWeight: 500 }}>{email}</span>.
                </p>
                <AuthButton onClick={() => setAuthStep('enterCode')}>
                  Enter code manually
                </AuthButton>
                <button
                  onClick={handleBackToLogin}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: text,
                    fontSize: '13px',
                    fontWeight: 450,
                    cursor: 'pointer',
                    padding: '0',
                    marginTop: '16px',
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.textDecoration = 'underline')}
                  onMouseLeave={(e) => (e.currentTarget.style.textDecoration = 'none')}
                >
                  {isLogin ? 'Back to login' : 'Back to sign up'}
                </button>
              </div>
            )}

            {/* Enter Code Screen */}
            {authStep === 'enterCode' && (
              <form onSubmit={handleCodeSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <p style={{ fontSize: '13px', color: mutedText, textAlign: 'center', margin: '0 0 8px 0', lineHeight: 1.6 }}>
                  We&apos;ve sent you a temporary login code.<br />
                  Please check your inbox at<br />
                  <span style={{ color: text, fontWeight: 500 }}>{email}</span>.
                </p>
                <input
                  type="text"
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  placeholder="Enter code"
                  autoFocus
                  style={{
                    ...inputStyle,
                    fontFamily: 'monospace',
                    textAlign: 'center',
                    letterSpacing: '4px',
                  }}
                  onFocus={(e) => (e.currentTarget.style.borderColor = accent)}
                  onBlur={(e) => (e.currentTarget.style.borderColor = buttonBorder)}
                />
                <AuthButton primary type="submit" loading={isLoading === 'codeSubmit'}>
                  Continue with login code
                </AuthButton>
                <button
                  type="button"
                  onClick={handleBackToLogin}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: text,
                    fontSize: '13px',
                    fontWeight: 450,
                    cursor: 'pointer',
                    padding: '0',
                    marginTop: '16px',
                    alignSelf: 'center',
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.textDecoration = 'underline')}
                  onMouseLeave={(e) => (e.currentTarget.style.textDecoration = 'none')}
                >
                  {isLogin ? 'Back to login' : 'Back to sign up'}
                </button>
              </form>
            )}

            {/* Password Screen */}
            {authStep === 'password' && (
              <form onSubmit={handlePasswordSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                {/* Hidden email field for browser password manager */}
                <input
                  type="email"
                  name="email"
                  autoComplete="email"
                  value={email}
                  readOnly
                  style={{ display: 'none' }}
                />
                {isNewUser && (
                  <p style={{ fontSize: '13px', color: mutedText, textAlign: 'center', margin: '0 0 8px 0', lineHeight: 1.6 }}>
                    Set a password for your account
                  </p>
                )}
                {!isNewUser && (
                  <p style={{ fontSize: '13px', color: mutedText, textAlign: 'center', margin: '0 0 8px 0', lineHeight: 1.6 }}>
                    Enter your password for<br />
                    <span style={{ color: text, fontWeight: 500 }}>{email}</span>
                  </p>
                )}

                {errorMessage && (
                  <p style={{ fontSize: '12px', color: '#ef4444', textAlign: 'center', margin: 0 }}>
                    {errorMessage}
                  </p>
                )}

                {/* Password input with eye toggle */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <input
                    type={showPassword ? 'text' : 'password'}
                    name="password"
                    autoComplete={isNewUser ? 'new-password' : 'current-password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder={isNewUser ? 'Create password' : 'Enter password'}
                    autoFocus
                    style={inputStyle}
                    onFocus={(e) => (e.currentTarget.style.borderColor = accent)}
                    onBlur={(e) => (e.currentTarget.style.borderColor = buttonBorder)}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    style={{
                      background: 'none',
                      border: 'none',
                      cursor: 'pointer',
                      padding: '4px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      opacity: 0.7,
                      transition: 'opacity 0.15s ease',
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.opacity = '1')}
                    onMouseLeave={(e) => (e.currentTarget.style.opacity = '0.7')}
                    title={showPassword ? 'Hide password' : 'Show password'}
                  >
                    {showPassword ? <EyeOffIcon /> : <EyeIcon />}
                  </button>
                </div>

                {/* Confirm password input with eye toggle (new users only) */}
                {isNewUser && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <input
                      type={showConfirmPassword ? 'text' : 'password'}
                      name="confirm-password"
                      autoComplete="new-password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      placeholder="Confirm password"
                      style={inputStyle}
                      onFocus={(e) => (e.currentTarget.style.borderColor = accent)}
                      onBlur={(e) => (e.currentTarget.style.borderColor = buttonBorder)}
                    />
                    <button
                      type="button"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      style={{
                        background: 'none',
                        border: 'none',
                        cursor: 'pointer',
                        padding: '4px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        opacity: 0.7,
                        transition: 'opacity 0.15s ease',
                      }}
                      onMouseEnter={(e) => (e.currentTarget.style.opacity = '1')}
                      onMouseLeave={(e) => (e.currentTarget.style.opacity = '0.7')}
                      title={showConfirmPassword ? 'Hide password' : 'Show password'}
                    >
                      {showConfirmPassword ? <EyeOffIcon /> : <EyeIcon />}
                    </button>
                  </div>
                )}

                {/* Remember me checkbox */}
                <label
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    cursor: 'pointer',
                    fontSize: '13px',
                    color: mutedText,
                    userSelect: 'none',
                  }}
                >
                  <input
                    type="checkbox"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                    style={{
                      width: '16px',
                      height: '16px',
                      accentColor: accent,
                      cursor: 'pointer',
                    }}
                  />
                  Remember me
                </label>

                <AuthButton primary type="submit" loading={isLoading === 'passwordSubmit'}>
                  {isNewUser ? 'Create account' : 'Sign in'}
                </AuthButton>

                <button
                  type="button"
                  onClick={handleBackToLogin}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: text,
                    fontSize: '13px',
                    fontWeight: 450,
                    cursor: 'pointer',
                    padding: '0',
                    marginTop: '16px',
                    alignSelf: 'center',
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.textDecoration = 'underline')}
                  onMouseLeave={(e) => (e.currentTarget.style.textDecoration = 'none')}
                >
                  {isLogin ? 'Back to login' : 'Back to sign up'}
                </button>
              </form>
            )}

            {/* Email Form */}
            {authStep === 'emailForm' && (
              <form onSubmit={handleEmailSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <input
                  type="email"
                  name="email"
                  autoComplete="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Enter your email address..."
                  autoFocus
                  style={inputStyle}
                  onFocus={(e) => (e.currentTarget.style.borderColor = accent)}
                  onBlur={(e) => (e.currentTarget.style.borderColor = buttonBorder)}
                />
                <AuthButton primary type="submit" loading={isLoading === 'submit'}>
                  Continue with email
                </AuthButton>
                <button
                  type="button"
                  onClick={handleBackToLogin}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: text,
                    fontSize: '13px',
                    fontWeight: 450,
                    cursor: 'pointer',
                    padding: '0',
                    marginTop: '8px',
                    alignSelf: 'center',
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.textDecoration = 'underline')}
                  onMouseLeave={(e) => (e.currentTarget.style.textDecoration = 'none')}
                >
                  {isLogin ? 'Back to login' : 'Back to sign up'}
                </button>
              </form>
            )}

            {/* Main Auth Screen */}
            {authStep === 'main' && (
              <>
                {/* Auth Buttons */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  <AuthButton primary onClick={() => handleButtonClick('email')} loading={isLoading === 'email'}>
                    Continue with email
                  </AuthButton>
                  <AuthButton onClick={() => handleButtonClick('google')} loading={isLoading === 'google'} icon={<GoogleIcon />}>
                    Continue with Google
                  </AuthButton>
                </div>

                {/* Footer Links */}
                <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', marginTop: '32px' }}>
                  {isLogin ? (
                    <p style={{ fontSize: '13px', fontWeight: 450, color: mutedText, textAlign: 'center', margin: 0, lineHeight: 1.6 }}>
                      Don&apos;t have an account?<br />
                      <span
                        onClick={() => setIsLogin(false)}
                        style={{ color: text, cursor: 'pointer' }}
                        onMouseEnter={(e) => (e.currentTarget.style.textDecoration = 'underline')}
                        onMouseLeave={(e) => (e.currentTarget.style.textDecoration = 'none')}
                      >
                        Sign up
                      </span>
                      {' '}or{' '}
                      <span
                        style={{ color: text, cursor: 'pointer' }}
                        onMouseEnter={(e) => (e.currentTarget.style.textDecoration = 'underline')}
                        onMouseLeave={(e) => (e.currentTarget.style.textDecoration = 'none')}
                      >
                        learn more
                      </span>
                    </p>
                  ) : (
                    <div style={{ textAlign: 'center' }}>
                      <p style={{ fontSize: '13px', fontWeight: 450, color: mutedText, margin: '0 0 16px 0', lineHeight: 1.6 }}>
                        By signing up, you agree to our{' '}
                        <span
                          style={{ color: text, cursor: 'pointer' }}
                          onMouseEnter={(e) => (e.currentTarget.style.textDecoration = 'underline')}
                          onMouseLeave={(e) => (e.currentTarget.style.textDecoration = 'none')}
                        >
                          Terms of Service
                        </span>
                        {' '}and{' '}
                        <span
                          style={{ color: text, cursor: 'pointer' }}
                          onMouseEnter={(e) => (e.currentTarget.style.textDecoration = 'underline')}
                          onMouseLeave={(e) => (e.currentTarget.style.textDecoration = 'none')}
                        >
                          Data Processing Agreement
                        </span>.
                      </p>
                      <p style={{ fontSize: '13px', fontWeight: 450, color: mutedText, margin: 0 }}>
                        Already have an account?{' '}
                        <span
                          onClick={() => setIsLogin(true)}
                          style={{ color: text, cursor: 'pointer' }}
                          onMouseEnter={(e) => (e.currentTarget.style.textDecoration = 'underline')}
                          onMouseLeave={(e) => (e.currentTarget.style.textDecoration = 'none')}
                        >
                          Log in
                        </span>
                      </p>
                    </div>
                  )}
                </div>
              </>
            )}
          </div>

          {/* DEMO BUTTON - Only visible in development */}
          {process.env.NEXT_PUBLIC_DEV_BYPASS_AUTH === 'true' && (
            <div
              style={{
                position: 'fixed',
                bottom: '24px',
                left: '50%',
                transform: 'translateX(-50%)',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '12px',
              }}
            >
              {showDemoButton ? (
                // DEMO button - light red with glow, Dobby font
                <button
                  onClick={() => setShowDemoButton(false)}
                  style={{
                    padding: '10px 24px',
                    fontSize: '13px',
                    fontWeight: 500,
                    fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace',
                    letterSpacing: '4px',
                    textTransform: 'uppercase',
                    color: '#ff6b6b',
                    backgroundColor: 'rgba(255, 107, 107, 0.1)',
                    border: '1px solid rgba(255, 107, 107, 0.3)',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    transition: 'all 0.3s ease',
                    boxShadow: '0 0 20px rgba(255, 107, 107, 0.3)',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = 'rgba(255, 107, 107, 0.15)';
                    e.currentTarget.style.boxShadow = '0 0 30px rgba(255, 107, 107, 0.5)';
                    e.currentTarget.style.transform = 'translateY(-2px)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = 'rgba(255, 107, 107, 0.1)';
                    e.currentTarget.style.boxShadow = '0 0 20px rgba(255, 107, 107, 0.3)';
                    e.currentTarget.style.transform = 'translateY(0)';
                  }}
                >
                  DEMO
                </button>
              ) : (
                // Skip to Dashboard button - revealed after clicking DEMO
                <button
                  onClick={() => router.push('/patient')}
                  style={{
                    padding: '10px 24px',
                    fontSize: '12px',
                    fontWeight: 500,
                    fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace',
                    letterSpacing: '2px',
                    color: '#ff6b6b',
                    backgroundColor: 'rgba(255, 107, 107, 0.1)',
                    border: '1px solid rgba(255, 107, 107, 0.3)',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    transition: 'all 0.3s ease',
                    boxShadow: '0 0 20px rgba(255, 107, 107, 0.3)',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = 'rgba(255, 107, 107, 0.15)';
                    e.currentTarget.style.boxShadow = '0 0 30px rgba(255, 107, 107, 0.5)';
                    e.currentTarget.style.transform = 'translateY(-2px)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = 'rgba(255, 107, 107, 0.1)';
                    e.currentTarget.style.boxShadow = '0 0 20px rgba(255, 107, 107, 0.3)';
                    e.currentTarget.style.transform = 'translateY(0)';
                  }}
                >
                  🔓 Skip to Dashboard
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// Loading fallback for Suspense
function AuthPageLoading() {
  return (
    <div
      style={{
        minHeight: '100vh',
        backgroundColor: '#FFFFFF',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      }}
    >
      <div
        style={{
          width: '24px',
          height: '24px',
          border: '2px solid #e0e0e0',
          borderTopColor: '#4ECDC4',
          borderRadius: '50%',
          animation: 'spin 1s linear infinite',
        }}
      />
      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}

// Export with Suspense wrapper for useSearchParams
export default function AuthPage() {
  return (
    <Suspense fallback={<AuthPageLoading />}>
      <AuthPageContent />
    </Suspense>
  );
}
