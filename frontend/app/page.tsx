import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Users, Heart, Mic, Brain, FileText, ArrowRight } from 'lucide-react';

export default function Home() {
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
