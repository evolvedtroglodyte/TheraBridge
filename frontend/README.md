# TherapyBridge Frontend

Modern Next.js 14 dashboard for TherapyBridge therapy session management platform.

## Features

- **Therapist Dashboard**: Manage patients, view sessions, upload audio
- **Real-time Processing**: Live status updates during transcription and AI extraction
- **Session Detail View**: Comprehensive clinical notes with strategies, triggers, action items
- **Patient Portal**: Simplified view for patients with supportive summaries
- **Responsive Design**: Mobile-first design with Tailwind CSS
- **Type-Safe**: Full TypeScript coverage with backend schema integration

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS + shadcn/ui
- **Data Fetching**: SWR (with auto-polling)
- **Icons**: Lucide React
- **Date Formatting**: date-fns

## Quick Start

### Prerequisites
- Node.js 18+ installed
- Backend API running on http://localhost:8000
- At least one patient and therapist in the database

### Setup

```bash
# Install dependencies
npm install

# Configure environment
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
echo "NEXT_PUBLIC_USE_REAL_API=true" >> .env.local

# Run development server
npm run dev
```

Open http://localhost:3000

### First-Time Usage

1. **Landing Page** (/) - Overview of features
2. **Therapist Dashboard** (/therapist) - View all patients
3. **Patient Detail** (/therapist/patients/[id]) - Upload audio, manage sessions
4. **Session Detail** (/therapist/sessions/[id]) - View notes, transcript, strategies

### Supported Audio Formats

- MP3, WAV, M4A, MP4, MPEG, WebM, MPGA
- Max file size: 100MB

## Project Structure

```
frontend/
├── app/
│   ├── page.tsx                    # Landing page
│   ├── layout.tsx                  # Root layout
│   ├── therapist/
│   │   ├── page.tsx                # Patient list
│   │   ├── patients/[id]/page.tsx  # Patient detail + sessions
│   │   └── sessions/[id]/page.tsx  # Session detail view
│   └── patient/
│       └── page.tsx                # Patient portal
├── components/
│   ├── ui/                         # shadcn/ui base components
│   ├── SessionStatusBadge.tsx      # Status indicator
│   ├── MoodIndicator.tsx           # Mood visualization
│   ├── StrategyCard.tsx            # Strategy display
│   ├── TriggerCard.tsx             # Trigger display
│   ├── ActionItemCard.tsx          # Action item checkbox
│   ├── SessionCard.tsx             # Session preview
│   ├── SessionUploader.tsx         # Drag-drop upload
│   └── TranscriptViewer.tsx        # Transcript display
├── hooks/
│   ├── useSession.ts               # Session polling hook
│   ├── usePatients.ts              # Patients data hook
│   └── useSessions.ts              # Sessions list hook
└── lib/
    ├── api.ts                      # API client functions
    ├── types.ts                    # TypeScript types
    └── utils.ts                    # Helper functions
```

## Key Routes

- `/` - Landing page with feature overview
- `/therapist` - Patient list (therapist dashboard)
- `/therapist/patients/[id]` - Patient detail with session upload
- `/therapist/sessions/[id]` - Full session notes and transcript
- `/patient` - Patient portal (simplified view)

## Environment Variables

Create `.env.local`:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Real-Time Updates

The app uses SWR for automatic polling:

- **Session status**: Polls every 5 seconds while processing
- **Session list**: Refreshes every 10 seconds to catch new uploads
- **Patient data**: Revalidates on focus

## Available Scripts

```bash
# Development server
npm run dev

# Production build
npm run build

# Start production server
npm start

# Lint code
npm run lint
```

## Backend Integration

The frontend connects to the FastAPI backend at `http://localhost:8000` (configurable via `NEXT_PUBLIC_API_URL`).

**Required Backend Endpoints**:
- `GET /api/patients/` - List patients
- `GET /api/patients/{id}` - Get patient
- `GET /api/sessions/` - List sessions (filterable by patient_id, status)
- `GET /api/sessions/{id}` - Get session
- `GET /api/sessions/{id}/notes` - Get extracted notes
- `POST /api/sessions/upload` - Upload session audio

## TypeScript Types

All TypeScript types in `lib/types.ts` match the backend Pydantic schemas exactly, ensuring type safety across the stack.

## Mobile Support

Fully responsive design:
- Collapsible navigation on mobile
- Touch-friendly drag-and-drop upload
- Stacked card layouts on small screens
- Readable font sizes and spacing

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari 15+
- Mobile browsers (iOS Safari, Chrome Mobile)

## Troubleshooting

### "Failed to load patients" Error
- Ensure backend is running: http://localhost:8000/docs
- Check CORS is enabled on backend
- Verify `.env.local` has correct API URL

### Upload Not Working
- Check file format is supported (MP3, WAV, M4A, etc.)
- Ensure file is under 100MB
- Verify patient_id is valid

### Build Errors
```bash
# Clean and rebuild
rm -rf .next node_modules
npm install
npm run build
```
