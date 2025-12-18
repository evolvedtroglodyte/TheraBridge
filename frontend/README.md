# TherapyBridge Frontend

Modern Next.js 16 + React 19 dashboard for TherapyBridge therapy session management platform.

## Quick Start

```bash
# Install dependencies
npm install

# Configure environment
cp .env.local.example .env.local
# Edit .env.local: Set NEXT_PUBLIC_API_URL=http://localhost:8000

# Run development server
npm run dev
```

Open http://localhost:3000

## Tech Stack

- **Framework**: Next.js 16 (App Router)
- **Language**: TypeScript 5
- **Runtime**: React 19
- **Styling**: Tailwind CSS 3.4 + shadcn/ui
- **Data Fetching**: SWR 2.3 (with optimistic updates)
- **Validation**: Zod 4.2
- **Icons**: Lucide React
- **Date Formatting**: date-fns 4.1
- **Notifications**: Sonner 2.0
- **Theming**: next-themes 0.4

## Features

- **Authentication**: JWT-based auth with automatic token refresh and role-based access
- **Therapist Dashboard**: Manage patients, view sessions, upload audio
- **Real-time Processing**: Live status updates during transcription and AI extraction
- **Session Detail View**: Comprehensive clinical notes with strategies, triggers, action items
- **Search & Filtering**: Search sessions by date, keywords; filter by status/date range
- **Patient Portal**: Simplified view for patients with supportive summaries
- **Responsive Design**: Mobile-first with breakpoint-specific layouts
- **Dark Mode**: System-aware theme switching with localStorage persistence
- **Type-Safe**: Full TypeScript coverage with backend schema integration
- **Form Validation**: Real-time validation with visual feedback
- **Error Handling**: User-friendly error messages with retry suggestions
- **Optimistic UI**: Immediate feedback for uploads and updates

## Environment Variables

Create `.env.local`:

```bash
# API Configuration (required)
NEXT_PUBLIC_API_URL=http://localhost:8000

# Feature flags (optional)
NEXT_PUBLIC_USE_REAL_API=true
```

## Project Structure

```
frontend/
├── app/
│   ├── auth/
│   │   ├── login/page.tsx           # Login with validation
│   │   ├── signup/page.tsx          # Signup with validation
│   │   └── verify/page.tsx          # Email verification
│   ├── therapist/
│   │   ├── page.tsx                 # Patient list dashboard
│   │   ├── patients/[id]/page.tsx   # Patient detail + sessions
│   │   └── sessions/[id]/page.tsx   # Session detail view
│   └── patient/
│       └── page.tsx                 # Patient portal
├── components/
│   ├── ui/                          # Base components (shadcn/ui)
│   │   ├── button.tsx
│   │   ├── input.tsx                # Enhanced with validation states
│   │   ├── form-field.tsx           # Form field with validation
│   │   ├── confirmation-dialog.tsx  # Confirmation dialogs
│   │   ├── error-message.tsx        # Error display component
│   │   ├── progress-bar.tsx         # Progress indicator
│   │   ├── step-indicator.tsx       # Multi-step process indicator
│   │   ├── theme-toggle.tsx         # Dark mode toggle
│   │   └── ...
│   ├── providers/
│   │   ├── theme-provider.tsx       # Dark mode context
│   │   └── toaster-provider.tsx     # Toast notifications
│   ├── session/
│   │   ├── SessionSearchInput.tsx   # Search with clear button
│   │   ├── UploadModal.tsx          # Upload modal UI
│   │   └── NoteWritingModal.tsx     # Note editor modal
│   ├── SessionUploader.tsx          # Drag-drop upload
│   ├── SessionProgressTracker.tsx   # Upload progress visualization
│   └── ...
├── hooks/
│   ├── useAuth.ts                   # Authentication hook
│   ├── useSession.ts                # Session polling
│   ├── useSessions.ts               # Session list
│   ├── useOptimisticSession.ts      # Optimistic single session
│   ├── useOptimisticSessions.ts     # Optimistic session list
│   ├── useOptimisticUpload.ts       # Optimistic file upload
│   ├── useSessionSearch.ts          # Debounced search
│   ├── useSessionFilters.ts         # Status & date filtering
│   ├── usePagination.ts             # Client-side pagination
│   └── ...
└── lib/
    ├── auth-context.tsx             # Auth state management
    ├── api-client.ts                # HTTP client with auth
    ├── api.ts                       # API functions
    ├── validation.ts                # Form validation rules
    ├── error-formatter.ts           # User-friendly error messages
    ├── token-storage.ts             # JWT token management
    ├── schemas.ts                   # Zod schemas
    ├── types.ts                     # TypeScript types
    └── utils.ts                     # Helper functions
```

## Authentication

### Setup

Wrap your app with `AuthProvider` in `app/layout.tsx`:

```tsx
import { AuthProvider } from '@/lib/auth-context';

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        <AuthProvider>
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}
```

### Usage

```tsx
import { useAuth } from '@/lib/auth-context';

function MyComponent() {
  const { user, isAuthenticated, login, logout } = useAuth();

  if (!isAuthenticated) {
    return <LoginForm />;
  }

  return <div>Welcome, {user?.full_name}!</div>;
}
```

### Features

- JWT access/refresh token management
- Automatic token refresh on 401 responses
- Role-based access control (therapist, patient, admin)
- Email verification flow
- Protected route patterns
- Secure token storage in localStorage

### API Endpoints Required

- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/signup` - Create account
- `POST /api/v1/auth/logout` - Logout
- `POST /api/v1/auth/refresh` - Refresh access token
- `GET /api/v1/auth/me` - Get current user
- `POST /api/v1/auth/verify-email` - Verify email

## Form Validation

Real-time validation with visual feedback using reusable rules.

### Built-in Rules

```tsx
import {
  emailRules,
  passwordRules,
  passwordStrongRules,
  fullNameRules,
  validateFields,
  isAllValid
} from '@/lib/validation';
```

### Usage

```tsx
import { FormField } from '@/components/ui/form-field';
import { emailRules } from '@/lib/validation';

function MyForm() {
  const [email, setEmail] = useState('');

  return (
    <FormField
      name="email"
      label="Email Address"
      type="email"
      value={email}
      onChange={setEmail}
      rules={emailRules}
      validateOnChange
      showErrors
    />
  );
}
```

### Features

- Real-time validation as user types
- Visual states (idle, valid, error) with icons
- Field-specific error messages
- Success indicators ("Looks good!")
- Accessible (ARIA labels, describedby)
- Custom validation rules support

## Error Handling

User-friendly error messages with retry suggestions.

### Error Message Component

```tsx
import { ErrorMessage } from '@/components/ui/error-message';

<ErrorMessage
  message="Upload failed"
  description="File exceeds 100MB limit"
  variant="alert"  // inline | alert | toast | banner
  severity="error" // error | warning | info
  dismissible
  action={{ label: 'Retry', onClick: () => retry() }}
/>
```

### Error Formatters

```tsx
import { formatUploadError, formatAuthError } from '@/lib/error-formatter';

try {
  await uploadSession(file);
} catch (err) {
  const formatted = formatUploadError(err);
  setError(formatted); // { message, description, suggestion, retryable }
}
```

### Features

- Context-specific error messages (upload, auth, network)
- HTTP status code → user-friendly mapping
- Retry suggestions included
- Field-level validation errors
- Auto-dismiss for toast variant

## State Management

### SWR Data Fetching

```tsx
import { useSessions } from '@/hooks/useSessions';

const { sessions, isLoading, error, refresh } = useSessions({
  patientId: 'p-123',
  status: 'processed'
});
```

**Features:**
- Automatic caching and deduplication
- Intelligent polling (5s while processing, stops when complete)
- Focus/reconnect revalidation
- Optimistic updates support

### Optimistic UI Updates

Makes the UI feel 10x faster by updating immediately before server confirmation.

```tsx
import { useOptimisticSession } from '@/hooks/useOptimisticSession';

const { session, mutate } = useOptimisticSession(sessionId);

// Update UI immediately, auto-revert on error
await mutate({ ...session, status: 'processed' });
```

**Available Hooks:**
- `useOptimisticSession` - Single session with optimistic mutations
- `useOptimisticSessions` - Session list operations (add, update, delete)
- `useOptimisticUpload` - File upload with immediate feedback & progress

**Features:**
- Automatic rollback on errors
- Real-time progress tracking (0-100%)
- Type-safe mutations
- No manual error cleanup needed

## Dark Mode

System-aware theme switching with localStorage persistence.

### Setup

Already configured in `app/layout.tsx` with `ThemeProvider`.

### Usage

```tsx
import { useTheme } from 'next-themes';
import { ThemeToggle } from '@/components/ui/theme-toggle';

function MyComponent() {
  const { theme, setTheme } = useTheme();

  return <ThemeToggle />; // Sun/moon toggle button
}
```

### Styling

```tsx
<div className="bg-white dark:bg-slate-900">
  <p className="text-gray-900 dark:text-gray-100">Text content</p>
</div>
```

**Features:**
- Automatic system preference detection
- No flash of unstyled content (FOUC)
- Smooth transitions
- Persisted in localStorage (`therapybridge-theme`)

## Responsive Design

Mobile-first with Tailwind breakpoints.

### Breakpoints

```
Mobile:     0-640px   (base, no prefix)
Landscape:  640px+    (sm:)
Tablet:     768px+    (md:)
Desktop:    1024px+   (lg:)
Large:      1280px+   (xl:)
```

### Common Patterns

```tsx
// Stack on mobile, row on desktop
<div className="flex flex-col sm:flex-row gap-4">

// Responsive grid
<div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">

// Responsive padding
<div className="px-4 sm:px-6 md:px-8">

// Responsive typography
<h1 className="text-2xl sm:text-3xl md:text-4xl font-bold">
```

### Touch Targets

All interactive elements are 44px+ (height and width) for mobile accessibility.

## Pagination

Client-side pagination with configurable page sizes.

```tsx
import { usePagination } from '@/hooks/usePagination';
import { Pagination } from '@/components/ui/pagination';

const {
  currentPage,
  pageSize,
  totalPages,
  paginatedItems,
  onPageChange,
  onPageSizeChange
} = usePagination(data, { initialPageSize: 10 });

// Render paginated items
{paginatedItems.map(item => <Item key={item.id} {...item} />)}

// Pagination controls
<Pagination
  currentPage={currentPage}
  totalPages={totalPages}
  pageSize={pageSize}
  totalItems={data.length}
  onPageChange={onPageChange}
  onPageSizeChange={onPageSizeChange}
/>
```

**Features:**
- Page number buttons with ellipsis
- Previous/Next navigation
- Page size selector (10, 25, 50, 100)
- Item counter ("Showing X to Y of Z items")
- Works with search and sorting

## Session Search & Filtering

Powerful search and filtering for session lists.

```tsx
import { useSessionSearch } from '@/hooks/useSessionSearch';
import { useSessionFilters } from '@/hooks/useSessionFilters';

const { searchQuery, filteredSessions, handleSearchChange, clearSearch } =
  useSessionSearch(sessions, patientName);

const { filteredSessions: sessionsByFilters, statusFilter, setStatusFilter,
  dateRangeFilter, setDateRangeFilter } = useSessionFilters(sessions);

// Combine both filters
const displaySessions = hasActiveSearch
  ? filteredSessions.filter(s => sessionsByFilters.some(sf => sf.id === s.id))
  : sessionsByFilters;
```

**Search Fields:**
- Session date
- Patient name
- Session topics and keywords
- Note content

**Filters:**
- Status: All, Processing, Completed, Failed
- Date Range: All Time, Last 7 Days, Last 30 Days, Last 3 Months

## Toast Notifications

Global toast notifications using Sonner.

```tsx
import { toast } from 'sonner';

// Basic toasts
toast.success('Upload complete');
toast.error('Something went wrong');
toast.info('Processing...');

// With description
toast.success('Upload complete', {
  description: 'Your session has been processed.'
});

// Promise-based
toast.promise(uploadFile(), {
  loading: 'Uploading...',
  success: 'Upload complete!',
  error: 'Upload failed'
});
```

**Features:**
- Position: Top-right
- Theme-aware (syncs with dark mode)
- Dismissible with close button
- Auto-dismiss on timeout

## Progress Indicators

### Progress Bar

```tsx
import { ProgressBar } from '@/components/ui/progress-bar';

<ProgressBar
  value={65}
  size="lg"                    // sm | md | lg
  variant="success"             // default | success | warning | destructive
  showLabel
  animated
/>
```

### Step Indicator

```tsx
import { StepIndicator } from '@/components/ui/step-indicator';

<StepIndicator
  steps={steps}
  currentStepIndex={1}
  orientation="horizontal"      // horizontal | vertical
  showDescriptions
/>
```

### Session Progress Tracker

Automatic progress tracking based on session status.

```tsx
import { SessionProgressTracker } from '@/components/SessionProgressTracker';

<SessionProgressTracker
  session={sessionData}
  compact={false}
  showDescriptions
/>
```

Maps backend statuses to progress:
- `uploading` → 25%
- `transcribing` → 50%
- `extracting_notes` → 75%
- `processed` → 100%

## Confirmation Dialogs

Production-ready confirmation dialogs using native HTML `<dialog>`.

```tsx
import { ConfirmationDialog } from '@/components/ui/confirmation-dialog';

<ConfirmationDialog
  isOpen={showConfirm}
  onOpenChange={setShowConfirm}
  title="Delete Session?"
  description="This cannot be undone."
  warning="All session data will be permanently removed."
  onConfirm={async () => {
    await deleteSession(sessionId);
  }}
  variant="destructive"  // destructive | warning | default
  isDangerous
/>
```

**Variants:**
- `destructive` - Red icon, red button (for delete operations)
- `warning` - Amber icon (for important actions)
- `default` - Blue icon (for standard confirmations)

**Features:**
- Native HTML `<dialog>` element
- Keyboard navigation (ESC to close, Enter to confirm)
- Loading states for async operations
- Error handling without dismissing
- Full ARIA accessibility

## API Integration

### API Client

Auto-authenticated HTTP client with retry logic.

```tsx
import { apiClient } from '@/lib/api-client';

const result = await apiClient.get<Patient>('/api/v1/patients/123');

if (result.success) {
  console.log(result.data);
} else {
  console.error(result.error, result.status);
}
```

**Features:**
- Automatic `Authorization` header injection
- Auto-refresh expired tokens on 401
- Retry failed requests after token refresh
- Type-safe results with discriminated unions
- Network and timeout error handling

### Required Backend Endpoints

```
Authentication:
POST   /api/v1/auth/login
POST   /api/v1/auth/signup
POST   /api/v1/auth/logout
POST   /api/v1/auth/refresh
GET    /api/v1/auth/me
POST   /api/v1/auth/verify-email

Patients:
GET    /api/v1/patients/
GET    /api/v1/patients/{id}

Sessions:
GET    /api/v1/sessions/
GET    /api/v1/sessions/{id}
GET    /api/v1/sessions/{id}/notes
POST   /api/v1/sessions/upload

Templates:
GET    /api/v1/templates/
GET    /api/v1/templates/{id}
```

## Available Scripts

```bash
# Development
npm run dev          # Start dev server (http://localhost:3000)

# Production
npm run build        # Build for production (.next/)
npm start            # Start production server

# Code Quality
npm run lint         # Run ESLint checks
```

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari 15+
- Mobile Safari (iOS 15+)
- Chrome Mobile (latest)

## Accessibility

- WCAG AA compliant color contrast
- Keyboard navigation throughout
- ARIA labels on all interactive elements
- Screen reader support
- Focus indicators visible
- Touch targets 44px+ on mobile
- No reliance on color alone for information

## Testing

**Current State:** Manual testing only

**Manual Testing:**
- Chrome DevTools responsive design mode
- Test at breakpoints: 375px, 640px, 768px, 1024px
- Schema validation via `npx tsx lib/schemas.test.ts`

**Future:** Automated testing framework recommended (Jest/Vitest + React Testing Library)

## Deployment

**Recommended Platform:** Vercel (native Next.js support, zero-config)

**Alternatives:** Netlify, AWS Amplify, or any Node.js hosting

**Build Configuration:**
- TypeScript compilation
- Tailwind CSS purging
- React optimization
- No custom webpack config needed

**Environment Variables:**
Set `NEXT_PUBLIC_API_URL` to your backend URL (production).

## Troubleshooting

### "Failed to load patients" Error
- Ensure backend is running: http://localhost:8000/docs
- Check CORS is enabled on backend
- Verify `.env.local` has correct `NEXT_PUBLIC_API_URL`

### Authentication Issues
- Clear localStorage and try fresh login
- Check backend `/auth/me` endpoint returns user
- Verify JWT tokens are valid (not expired)

### Upload Not Working
- Check file format (MP3, WAV, M4A, MP4, etc.)
- Ensure file is under 100MB
- Verify patient ID is valid

### Build Errors
```bash
# Clean and rebuild
rm -rf .next node_modules
npm install
npm run build
```

### Dark Mode Not Working
- Clear localStorage key `therapybridge-theme`
- Ensure `ThemeProvider` wraps app in layout.tsx
- Check CSS variables in `app/globals.css`

## Performance Optimizations

- **Automatic caching** via SWR deduplication
- **Smart polling** - Only when data might change
- **Optimistic updates** - Instant UI feedback
- **Code splitting** - Next.js automatic route-based splitting
- **Image optimization** - Next.js built-in image optimization
- **Debounced search** - Reduces unnecessary API calls

## Contributing

1. Follow existing code patterns
2. Use TypeScript for all new files
3. Add validation for all forms
4. Include error handling with user-friendly messages
5. Ensure mobile responsiveness (test at 375px, 768px, 1024px)
6. Support dark mode (use Tailwind `dark:` classes)
7. Add ARIA labels for accessibility
8. Update this README for new features

## Documentation

All documentation is consolidated in this README. The following topics are covered above:

- **Authentication** - JWT-based auth with token refresh
- **Form Validation** - Real-time validation with visual feedback
- **Error Handling** - User-friendly error messages
- **State Management** - SWR data fetching and optimistic updates
- **Dark Mode** - Theme switching with system preference detection
- **Responsive Design** - Mobile-first with Tailwind breakpoints
- **Pagination** - Client-side pagination with page size selector
- **Search & Filtering** - Session search and status/date filtering
- **Toast Notifications** - Global toast system with Sonner
- **Progress Indicators** - Progress bars, step indicators, session tracking
- **Confirmation Dialogs** - Native HTML dialog confirmations
- **API Integration** - Auto-authenticated HTTP client
- **Accessibility** - WCAG AA compliance and keyboard navigation
- **Testing** - Manual testing procedures
- **Deployment** - Build and deployment instructions
- **Troubleshooting** - Common issues and solutions

---

**Version:** Next.js 16.0.10 + React 19.2.1
**Last Updated:** 2025-12-18
