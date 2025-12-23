import { Skeleton } from '@/components/ui/skeleton';
import { Card, CardContent, CardHeader } from '@/components/ui/card';

/**
 * Skeleton loader for session detail page
 * Matches the structure of SessionDetailPage
 */
export function SessionDetailSkeleton() {
  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* Back Button */}
      <Skeleton className="h-10 w-40" />

      {/* Session Header Card */}
      <Card>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="space-y-2">
              <div className="flex items-center gap-4">
                <Skeleton className="h-8 w-64" />
                <Skeleton className="h-6 w-24" />
              </div>
              <div className="flex items-center gap-4">
                <Skeleton className="h-4 w-48" />
                <Skeleton className="h-4 w-32" />
              </div>
            </div>
            <Skeleton className="h-12 w-12 rounded-full" />
          </div>
        </CardHeader>
      </Card>

      {/* Clinical Summary Card */}
      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-40 mb-2" />
          <Skeleton className="h-4 w-64" />
        </CardHeader>
        <CardContent className="space-y-3">
          {Array.from({ length: 4 }).map((_, index) => (
            <Skeleton key={index} className="h-4 w-full" />
          ))}
          <Skeleton className="h-4 w-5/6" />
        </CardContent>
      </Card>

      {/* Key Topics Card */}
      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-40" />
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap gap-2">
            {Array.from({ length: 5 }).map((_, index) => (
              <Skeleton key={index} className="h-6 w-24" />
            ))}
          </div>
          <div className="space-y-2">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-5/6" />
          </div>
        </CardContent>
      </Card>

      {/* Strategies and Triggers */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Strategies Section */}
        <div className="space-y-4">
          <Skeleton className="h-6 w-48" />
          <div className="space-y-3">
            {Array.from({ length: 3 }).map((_, index) => (
              <Card key={index}>
                <CardContent className="pt-6">
                  <Skeleton className="h-5 w-32 mb-2" />
                  <Skeleton className="h-4 w-full mb-2" />
                  <Skeleton className="h-4 w-4/5" />
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Triggers Section */}
        <div className="space-y-4">
          <Skeleton className="h-6 w-48" />
          <div className="space-y-3">
            {Array.from({ length: 3 }).map((_, index) => (
              <Card key={index}>
                <CardContent className="pt-6">
                  <Skeleton className="h-5 w-32 mb-2" />
                  <Skeleton className="h-4 w-full mb-2" />
                  <Skeleton className="h-4 w-4/5" />
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </div>

      {/* Action Items */}
      <div className="space-y-4">
        <Skeleton className="h-6 w-48" />
        <div className="grid gap-3 md:grid-cols-2">
          {Array.from({ length: 4 }).map((_, index) => (
            <Card key={index}>
              <CardContent className="pt-6">
                <Skeleton className="h-5 w-32 mb-2" />
                <Skeleton className="h-4 w-full mb-2" />
                <Skeleton className="h-4 w-5/6" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Mood & Emotional Themes */}
      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-40" />
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-4">
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-10 w-10 rounded-full" />
          </div>
          <div>
            <Skeleton className="h-4 w-32 mb-2" />
            <div className="flex flex-wrap gap-2">
              {Array.from({ length: 4 }).map((_, index) => (
                <Skeleton key={index} className="h-6 w-20" />
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Significant Quotes */}
      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-48" />
        </CardHeader>
        <CardContent className="space-y-4">
          {Array.from({ length: 2 }).map((_, index) => (
            <div key={index} className="border-l-4 border-primary pl-4 py-2">
              <Skeleton className="h-4 w-full mb-2" />
              <Skeleton className="h-4 w-5/6 mb-2" />
              <Skeleton className="h-3 w-96" />
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Risk Flags */}
      <Card className="border-red-200 bg-red-50">
        <CardHeader>
          <Skeleton className="h-6 w-48" />
        </CardHeader>
        <CardContent className="space-y-3">
          {Array.from({ length: 2 }).map((_, index) => (
            <div key={index} className="bg-white p-4 rounded-md border border-red-200">
              <div className="flex items-start justify-between mb-2">
                <Skeleton className="h-5 w-32" />
                <Skeleton className="h-6 w-20" />
              </div>
              <Skeleton className="h-4 w-full" />
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Follow-up Topics & Unresolved Concerns */}
      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-64" />
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Skeleton className="h-4 w-40 mb-2" />
            <ul className="space-y-2">
              {Array.from({ length: 3 }).map((_, index) => (
                <li key={index} className="flex gap-2">
                  <span className="text-muted-foreground">•</span>
                  <Skeleton className="h-4 w-full" />
                </li>
              ))}
            </ul>
          </div>
          <div>
            <Skeleton className="h-4 w-40 mb-2" />
            <ul className="space-y-2">
              {Array.from({ length: 2 }).map((_, index) => (
                <li key={index} className="flex gap-2">
                  <span className="text-muted-foreground">•</span>
                  <Skeleton className="h-4 w-full" />
                </li>
              ))}
            </ul>
          </div>
        </CardContent>
      </Card>

      {/* Transcript Viewer */}
      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-32" />
        </CardHeader>
        <CardContent className="space-y-4">
          {Array.from({ length: 8 }).map((_, index) => (
            <div key={index} className="space-y-2">
              <div className="flex gap-2">
                <Skeleton className="h-4 w-24" />
                <Skeleton className="h-4 w-16" />
              </div>
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-5/6" />
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
