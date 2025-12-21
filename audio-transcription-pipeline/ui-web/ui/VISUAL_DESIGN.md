# Results Display - Visual Design Specification

## Design Overview

The Results Display component follows a clean, professional design with:
- **Color Palette**: Blue/Green for speakers, gray for UI elements
- **Typography**: System fonts, clear hierarchy
- **Layout**: Responsive grid, mobile-first
- **Interactions**: Hover states, active highlights, smooth transitions

## Color Palette

### Primary Colors
```css
--primary-blue: #3B82F6;    /* Therapist, primary actions */
--primary-green: #10B981;   /* Client, success states */
--primary-amber: #F59E0B;   /* Speaker 2 */
--primary-red: #EF4444;     /* Speaker 3, errors */
```

### UI Colors
```css
--bg-primary: #FFFFFF;      /* Card backgrounds */
--bg-secondary: #F8FAFC;    /* Segment backgrounds */
--border: #E2E8F0;          /* Borders */
--text-primary: #1E293B;    /* Headings */
--text-secondary: #64748B;  /* Timestamps, meta */
```

### Dark Theme (Optional)
```css
--bg-primary: #1E293B;
--bg-secondary: #0F172A;
--border: #334155;
--text-primary: #F1F5F9;
--text-secondary: #94A3B8;
```

## Layout Structure

### Desktop (>1024px)
```
┌─────────────────────────────────────────────────────────┐
│                    RESULTS HEADER                       │
│            [Export Transcript] [Export JSON] [New]      │
├─────────────────────────────────────────────────────────┤
│                   WAVEFORM SECTION                      │
│  ┌───────────────────────────────────────────────────┐  │
│  │          Interactive Waveform with Regions        │  │
│  └───────────────────────────────────────────────────┘  │
│       [Play] [Stop] [Zoom In] [Zoom Out] 00:00/01:23   │
├─────────────────────────────────────────────────────────┤
│                  PROCESSING METRICS                     │
│  [Total Time] [Audio Length] [Transcription] [RTF]     │
├──────────────────────────┬──────────────────────────────┤
│   TRANSCRIPT (2/3)       │  SPEAKER STATS (1/3)         │
│  ┌────────────────────┐  │ ┌──────────────────────────┐ │
│  │ [Therapist] 00:00  │  │ │ Speaker  │ Turns │ Time  │ │
│  │ Hello, how are you?│  │ │──────────┼───────┼───────│ │
│  │                    │  │ │Therapist │   4   │ 18.2s │ │
│  │ [Client] 00:03     │  │ │Client    │   3   │ 24.8s │ │
│  │ I've been feeling..│  │ └──────────────────────────┘ │
│  │                    │  │                              │
│  │ [Therapist] 00:09  │  │ Speaking Distribution:       │
│  │ I understand...    │  │ ████████ Therapist 42%       │
│  │                    │  │ ████████████ Client 58%      │
│  │ (scrollable)       │  │                              │
│  └────────────────────┘  │                              │
└──────────────────────────┴──────────────────────────────┘
```

### Tablet (768px - 1024px)
```
┌─────────────────────────────────────────────────────────┐
│                    RESULTS HEADER                       │
├─────────────────────────────────────────────────────────┤
│                   WAVEFORM SECTION                      │
├─────────────────────────────────────────────────────────┤
│                  PROCESSING METRICS                     │
├─────────────────────────────────────────────────────────┤
│               TRANSCRIPT (full width)                   │
│  ┌───────────────────────────────────────────────────┐  │
│  │ Transcript segments                               │  │
│  └───────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────┤
│              SPEAKER STATS (full width)                 │
│  ┌───────────────────────────────────────────────────┐  │
│  │ Statistics table and chart                        │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Mobile (<768px)
```
┌─────────────────────┐
│  RESULTS HEADER     │
│  [Actions stacked]  │
├─────────────────────┤
│  WAVEFORM           │
│  (compact)          │
├─────────────────────┤
│  METRICS            │
│  (2x2 grid)         │
├─────────────────────┤
│  TRANSCRIPT         │
│  (full width)       │
├─────────────────────┤
│  SPEAKER STATS      │
│  (stacked)          │
└─────────────────────┘
```

## Component Design Details

### 1. Waveform Section

**Visual Design**:
```
┌──────────────────────────────────────────────────┐
│ Audio Waveform                                   │
│ ┌──────────────────────────────────────────────┐ │
│ │                                              │ │
│ │  ▁▂▃▅▇███████████▇▅▃▂▁▁▂▃▅▇████████▇▅▃▂▁▁ │ │
│ │  ▓▓▓▓▓░░░░░░░░  ▓▓▓▓▓░░░░░░  ▓▓▓▓▓       │ │
│ │  Blue(Therapist) Green(Client) Blue       │ │
│ │              ▼ (playback cursor)          │ │
│ │                                              │ │
│ └──────────────────────────────────────────────┘ │
│ [▶ Play] [■ Stop] [🔍+ In] [🔍- Out]  00:23/01:45│
└──────────────────────────────────────────────────┘
```

**Specifications**:
- Height: 128px
- Waveform color: #94A3B8 (gray)
- Progress color: #1E293B (dark)
- Cursor color: #0EA5E9 (cyan)
- Bar width: 2px, gap: 1px, radius: 2px
- Regions: 20% opacity overlay of speaker color

**Interaction States**:
- **Hover over region**: Lighten by 10%
- **Active segment**: Full opacity, pulsing border
- **Playing**: Cursor moves smoothly

### 2. Transcript Segment

**Visual Design**:
```
┌────────────────────────────────────────────────┐
│ ┌ [Therapist]              00:00 - 00:03     │ │
│ │                                            │ │
│ │  Hello, how are you feeling today?        │ │
│ │                                            │ │
│ └────────────────────────────────────────────┘ │
└────────────────────────────────────────────────┘
│ ← 3px blue border (speaker color)
```

**Specifications**:
- Padding: 1rem (16px)
- Margin bottom: 0.75rem (12px)
- Border radius: 0.375rem (6px)
- Background: #F8FAFC (light gray)
- Border left: 3px solid (speaker color when active)

**Speaker Badge**:
```css
padding: 0.25rem 0.75rem;
border-radius: 9999px;
font-size: 0.75rem (12px);
font-weight: 600;
text-transform: uppercase;
color: white;
background: [speaker-color];
```

**Timestamp**:
```css
font-size: 0.75rem (12px);
font-family: 'Courier New', monospace;
color: #64748B (gray);
```

**Interaction States**:
- **Default**: Light gray background
- **Hover**: Darker gray (#F1F5F9), translate 2px right
- **Active**: Blue tint (#EFF6FF), blue border, shadow

### 3. Speaker Statistics Table

**Visual Design**:
```
┌───────────┬───────┬──────────┬───────┬──────────┐
│ Speaker   │ Turns │ Duration │ Words │ Avg Turn │
├───────────┼───────┼──────────┼───────┼──────────┤
│ Therapist │   4   │  18.2s   │  120  │   4.5s   │
│ Client    │   3   │  24.8s   │  156  │   8.3s   │
└───────────┴───────┴──────────┴───────┴──────────┘
```

**Specifications**:
- Header: #F8FAFC background, 2px bottom border
- Rows: 1px bottom border (#F1F5F9)
- Padding: 0.75rem 0.5rem
- Font size: 0.875rem (14px)
- Row hover: #F8FAFC background

### 4. Speaker Distribution Chart

**Visual Design**:
```
Speaking Time Distribution:

[Therapist]  ████████████░░░░░░░░░░░░░░░░ 42.3%

[Client]     ████████████████████░░░░░░░░ 57.7%
```

**Specifications**:
- Bar height: 24px
- Bar background: #F1F5F9 (light gray)
- Fill: Speaker color (solid)
- Border radius: 0.25rem (4px)
- Label: Speaker badge + percentage
- Margin between bars: 1rem

**Animation**:
```css
.chart-bar-fill {
  transition: width 0.5s ease;
}
```

### 5. Processing Metrics Grid

**Visual Design**:
```
┌──────────────┬──────────────┬──────────────┬──────────┐
│  Total Time  │ Audio Length │Transcription │   RTF    │
│    45.2s     │    43.0s     │    12.3s     │  1.05x   │
└──────────────┴──────────────┴──────────────┴──────────┘
```

**Each Metric Card**:
```
┌──────────────┐
│  LABEL       │  ← 0.75rem font, gray, uppercase
│              │
│   VALUE      │  ← 1.5rem font, bold, dark
└──────────────┘
```

**Specifications**:
- Grid: auto-fit, min 140px per item
- Card padding: 1rem
- Card background: #F8FAFC
- Card border radius: 0.375rem
- Label: uppercase, 0.75rem, #64748B
- Value: 1.5rem, bold, #1E293B

## Typography

### Headings
```css
h2 (Results Header):
  font-size: 1.875rem (30px)
  font-weight: 700
  color: #1E293B

h3 (Section Titles):
  font-size: 1.125rem (18px)
  font-weight: 600
  color: #1E293B
```

### Body Text
```css
Segment Text:
  font-size: 0.9375rem (15px)
  line-height: 1.6
  color: #334155

Timestamps:
  font-size: 0.75rem (12px)
  font-family: 'Courier New', monospace
  color: #64748B

Speaker Labels:
  font-size: 0.75rem (12px)
  font-weight: 600
  text-transform: uppercase
  letter-spacing: 0.025em
```

## Buttons

### Primary Button
```css
background: #3B82F6 (blue)
color: white
padding: 0.5rem 1rem
border-radius: 0.375rem
font-size: 0.875rem

hover:
  background: #2563EB (darker blue)
```

### Secondary Button
```css
background: white
color: #475569 (gray)
border: 1px solid #E2E8F0
padding: 0.5rem 1rem
border-radius: 0.375rem

hover:
  background: #F1F5F9
  border-color: #CBD5E1
```

### Icon Button
```css
width: 2rem
height: 2rem
border-radius: 0.375rem
display: flex
align-items: center
justify-content: center

hover:
  background: #F1F5F9
```

## Spacing System

```css
--space-xs: 0.25rem (4px)
--space-sm: 0.5rem (8px)
--space-md: 1rem (16px)
--space-lg: 1.5rem (24px)
--space-xl: 2rem (32px)
```

## Shadows

```css
Cards:
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1)

Active Segment:
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1)
```

## Animations

### Transcript Segment Hover
```css
transition: all 0.2s ease;
transform: translateX(2px);
```

### Chart Bar Fill
```css
transition: width 0.5s ease;
```

### Loading Spinner
```css
@keyframes spin {
  to { transform: rotate(360deg); }
}

animation: spin 1s linear infinite;
```

## Responsive Breakpoints

```css
/* Mobile */
@media (max-width: 768px) {
  - Stack layout (single column)
  - Smaller fonts (-10%)
  - Compact padding
  - Full-width buttons
}

/* Tablet */
@media (max-width: 1024px) {
  - Single column grid
  - Moderate padding
  - Side-by-side buttons
}

/* Desktop */
@media (min-width: 1024px) {
  - 2-column grid (2fr + 1fr)
  - Full padding
  - Optimal spacing
}
```

## Print Styles

```css
@media print {
  /* Hide */
  - Waveform section
  - Metrics section
  - Action buttons
  - Controls

  /* Show */
  - Transcript (full)
  - Speaker stats (table only)

  /* Modify */
  - Remove shadows
  - Black borders
  - Grayscale speaker badges
  - Page break avoidance
}
```

## Accessibility

### Color Contrast
- All text meets WCAG AA standards (4.5:1 minimum)
- Speaker badges have sufficient contrast (white on color)

### Focus States
```css
:focus {
  outline: 2px solid #3B82F6;
  outline-offset: 2px;
}
```

### ARIA Labels
- All buttons have aria-label
- Sections have proper heading hierarchy
- Interactive elements are keyboard accessible

## Icon Style

- **Library**: Feather Icons style (inline SVG)
- **Size**: 16px - 24px
- **Stroke**: 2px
- **Color**: currentColor (inherits from parent)

---

**Design System**: Tailwind CSS inspired
**Browser Support**: Modern browsers (Chrome, Firefox, Safari, Edge)
**Mobile**: iOS Safari, Chrome Android
**Last Updated**: December 2025
