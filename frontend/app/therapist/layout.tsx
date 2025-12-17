import Link from 'next/link';
import { Users, Home } from 'lucide-react';

export default function TherapistLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-background">
      <header className="border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-8">
              <Link href="/therapist" className="flex items-center gap-2">
                <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center">
                  <Users className="w-6 h-6 text-primary-foreground" />
                </div>
                <div>
                  <h1 className="text-xl font-bold">TherapyBridge</h1>
                  <p className="text-xs text-muted-foreground">Therapist Dashboard</p>
                </div>
              </Link>
              <nav className="flex items-center gap-4">
                <Link
                  href="/therapist"
                  className="flex items-center gap-2 px-3 py-2 text-sm hover:bg-accent rounded-md transition-colors"
                >
                  <Home className="w-4 h-4" />
                  Patients
                </Link>
              </nav>
            </div>
          </div>
        </div>
      </header>
      <main className="container mx-auto px-4 py-8">
        {children}
      </main>
    </div>
  );
}
