'use client';

/**
 * Smart Root Route - Redirects based on first-time status + auth state
 *
 * Flow:
 * 1. Check if user is logged in → Dashboard
 * 2. Check if account exists (localStorage + Supabase) → Login
 * 3. Otherwise → Signup (first-time visitor)
 */

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Brain, Mic, FileText, Shield, BarChart3, Users, ArrowRight, Heart } from 'lucide-react';
import { supabase } from '@/lib/supabase';
import { hasExistingAccount } from '@/lib/first-time-detection';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';

export default function Home() {
  const router = useRouter();
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    async function determineRoute() {
      // Skip redirect if dev bypass is enabled
      if (process.env.NEXT_PUBLIC_DEV_BYPASS_AUTH === 'true') {
        console.log('🔓 Dev bypass enabled - showing landing page');
        setIsChecking(false);
        return;
      }

      try {
        // Step 1: Check if user is already logged in
        const { data: { session } } = await supabase.auth.getSession();

        if (session?.user) {
          // User is logged in - get their role and redirect to dashboard
          const { data: userData } = await supabase
            .from('users')
            .select('role')
            .eq('id', session.user.id)
            .single();

          const dashboardPath = userData?.role === 'therapist'
            ? '/therapist'
            : '/patient';

          console.log(`✅ User logged in - redirecting to ${dashboardPath}`);
          router.replace(dashboardPath);
          return;
        }

        // Step 2: User not logged in - check if any account exists
        const accountExists = await hasExistingAccount();

        if (accountExists) {
          // Account exists - send to login
          console.log('📝 Account exists - redirecting to login');
          router.replace('/auth/login');
        } else {
          // First-time visitor - send to signup
          console.log('🆕 First-time visitor - redirecting to signup');
          router.replace('/auth/signup');
        }
      } catch (error) {
        console.error('❌ Route determination error:', error);
        // On error, default to signup (safer than login)
        router.replace('/auth/signup');
      }
    }

    determineRoute();
  }, [router]);

  // Show loading state while determining route
  if (isChecking) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-background to-secondary">
        <div className="text-center space-y-4">
          <div className="w-16 h-16 bg-primary rounded-2xl flex items-center justify-center mx-auto animate-pulse">
            <svg className="w-10 h-10 text-primary-foreground" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
            </svg>
          </div>
          <p className="text-muted-foreground">Loading TherapyBridge...</p>
        </div>
      </div>
    );
  }

  // This will only show if dev bypass is enabled
  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-secondary">
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-6xl mx-auto space-y-16">
          {/* Hero Section */}
          <div className="text-center space-y-6">
            <div className="flex justify-center">
              <div className="w-16 h-16 bg-primary rounded-2xl flex items-center justify-center">
                <Brain className="w-10 h-10 text-primary-foreground" />
              </div>
            </div>
            <h1 className="text-5xl font-bold tracking-tight">TherapyBridge</h1>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              AI-powered therapy session transcription and clinical note extraction.
              Transform audio recordings into comprehensive, structured therapeutic insights.
            </p>

            <div className="flex gap-4 justify-center pt-4">
              <Link href="/therapist">
                <Button size="lg" className="gap-2">
                  <Users className="w-5 h-5" />
                  Therapist Dashboard
                  <ArrowRight className="w-4 h-4" />
                </Button>
              </Link>
              <Link href="/patient">
                <Button size="lg" variant="outline" className="gap-2">
                  <Heart className="w-5 h-5" />
                  Patient Portal
                </Button>
              </Link>
            </div>
          </div>

          {/* Features */}
          <div className="grid gap-6 md:grid-cols-3">
            <Card>
              <CardHeader>
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
                  <Mic className="w-6 h-6 text-blue-600" />
                </div>
                <CardTitle>Audio Transcription</CardTitle>
                <CardDescription>
                  Upload therapy session recordings and get accurate transcriptions with speaker diarization
                </CardDescription>
              </CardHeader>
            </Card>

            <Card>
              <CardHeader>
                <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4">
                  <Brain className="w-6 h-6 text-purple-600" />
                </div>
                <CardTitle>AI Note Extraction</CardTitle>
                <CardDescription>
                  Automatically extract key topics, strategies, triggers, action items, and clinical insights
                </CardDescription>
              </CardHeader>
            </Card>

            <Card>
              <CardHeader>
                <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mb-4">
                  <FileText className="w-6 h-6 text-green-600" />
                </div>
                <CardTitle>Dual Summaries</CardTitle>
                <CardDescription>
                  Generate both clinical therapist notes and warm, supportive patient summaries
                </CardDescription>
              </CardHeader>
            </Card>
          </div>

          {/* What's Extracted */}
          <Card>
            <CardHeader>
              <CardTitle className="text-2xl">What Gets Extracted</CardTitle>
              <CardDescription>
                Our AI analyzes sessions to extract comprehensive therapeutic insights
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-2">
                <ul className="space-y-2">
                  <li className="flex items-center gap-2 text-sm">
                    <div className="w-2 h-2 bg-primary rounded-full" />
                    Key topics and session summary
                  </li>
                  <li className="flex items-center gap-2 text-sm">
                    <div className="w-2 h-2 bg-primary rounded-full" />
                    Therapeutic strategies and techniques
                  </li>
                  <li className="flex items-center gap-2 text-sm">
                    <div className="w-2 h-2 bg-primary rounded-full" />
                    Triggers and severity assessment
                  </li>
                  <li className="flex items-center gap-2 text-sm">
                    <div className="w-2 h-2 bg-primary rounded-full" />
                    Action items and homework
                  </li>
                </ul>
                <ul className="space-y-2">
                  <li className="flex items-center gap-2 text-sm">
                    <div className="w-2 h-2 bg-primary rounded-full" />
                    Session mood and emotional themes
                  </li>
                  <li className="flex items-center gap-2 text-sm">
                    <div className="w-2 h-2 bg-primary rounded-full" />
                    Significant quotes with context
                  </li>
                  <li className="flex items-center gap-2 text-sm">
                    <div className="w-2 h-2 bg-primary rounded-full" />
                    Risk flags and safety concerns
                  </li>
                  <li className="flex items-center gap-2 text-sm">
                    <div className="w-2 h-2 bg-primary rounded-full" />
                    Follow-up topics and unresolved concerns
                  </li>
                </ul>
              </div>
            </CardContent>
          </Card>

          {/* CTA */}
          <div className="text-center space-y-4 py-8">
            <h2 className="text-3xl font-bold">Ready to get started?</h2>
            <p className="text-muted-foreground">
              Access the therapist dashboard to manage patients and sessions
            </p>
            <Link href="/therapist">
              <Button size="lg" className="gap-2">
                Open Dashboard
                <ArrowRight className="w-4 h-4" />
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
