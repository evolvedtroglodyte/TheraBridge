# TherapyBridge Dashboard - Superdesign Prompt for Gemini 3 Pro

## Project Context
Design a state-of-the-art therapy progress dashboard that feels warm, calming, and trustworthy. This is a widget-based interface where each component acts as a self-contained "mini-app" with unique visual styling. The design should feel modern and premium while maintaining therapy-appropriate aesthetics (no harsh colors, no gamification, no stress-inducing visuals).

---

## Design Philosophy

**Core Principles:**
1. **Progressive disclosure** - Information reveals gradually through user-initiated interactions
2. **Widget differentiation** - Each card feels visually distinct (different border-radius, shadows, backgrounds)
3. **Seamless transitions** - Spring animations (iPhone-style) for all modal expansions
4. **Therapeutic aesthetics** - Calm, warm, serene color palette with soft shadows and rounded corners
5. **Information hierarchy** - Most important data visible at a glance, details available on expansion

**Visual Style Keywords:**
- Glassmorphism (frosted glass effects with blur and transparency on certain cards)
- Neumorphism (soft extruded plastic look on Progress Patterns card)
- Microinteractions (subtle feedback animations on hover, click, completion)
- Drop shadows (varied depths creating clear visual hierarchy)
- Border radius variation (8px sharp for To-Do, 20px pill-shaped for Therapist Bridge)
- Gradient backgrounds (soft teal→lavender, warm cream base)
- Whitespace mastery (generous spacing between components for breathing room)

---

## Target Viewport & Layout Specifications

**Viewport:** 1440px width (desktop-optimized)
**Container:** 1400px max-width, centered with `margin: 0 auto`
**Page background:** Warm cream (#F7F5F3) with subtle texture or gradient

### Grid Layout Structure

**Visual hierarchy (top to bottom):**

```
┌─────────────────────────────────────────────────────────────────────┐
│  STICKY HEADER (minimal height ~60px)                               │
│  [Home Icon] [Sun Icon] | Dashboard | Ask AI | Upload               │
├──────────────────────────────┬──────────────────────────────────────┤
│  TOP ROW (2 equal panels)                                           │
│  ┌──────────────────────────┐  ┌──────────────────────────────────┐│
│  │  Notes / Goals           │  │  AI Chat Integration (Dobby)     ││
│  │  (50% width)             │  │  (50% width)                     ││
│  │  Height: ~280px          │  │  Height: ~280px                  ││
│  │  [Expandable to Modal]   │  │  [Expandable to Fullscreen]      ││
│  └──────────────────────────┘  └──────────────────────────────────┘│
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│  MIDDLE ROW (3 equal cards - 33.33% / 33.33% / 33.33%)             │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐            │
│  │  To-Do        │ │  Progress     │ │  Therapist    │            │
│  │  Card 1       │ │  Patterns     │ │  Bridge       │            │
│  │  Height:~300px│ │  Card 2       │ │  Card 3       │            │
│  │  [Expandable] │ │  Height:~300px│ │  Height:~300px│            │
│  │  [Carousel]   │ │  [Expandable] │ │  [Expandable] │            │
│  │               │ │  [Carousel]   │ │               │            │
│  └───────────────┘ └───────────────┘ └───────────────┘            │
│                                                                     │
├──────────────────────────────────────┬──────────────────────────────┤
│  BOTTOM ROW (80% / 20% split)        │                              │
│                                      │                              │
│  SESSION CARDS GRID (80% width)      │  TIMELINE SIDEBAR (20%)      │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐   │  ┌────────────────────────┐ │
│  │Dec17│ │Dec10│ │Dec 3│ │Nov26│   │  │  Timeline              │ │
│  │ 50m │ │ 45m │ │ 48m │ │ 45m │   │  │  ● Dec 17              │ │
│  │  😊 │ │  😊 │ │  😐 │ │  😐 │   │  │  │  Boundaries         │ │
│  └─────┘ └─────┘ └─────┘ └─────┘   │  │  │                     │ │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐   │  │  ⭐ Dec 10             │ │
│  │Nov19│ │Nov12│ │Nov 5│ │Oct29│   │  │  │  Self-worth        │ │
│  │ 50m │ │ 45m │ │ 50m │ │ 45m │   │  │  │  Breakthrough      │ │
│  │  😔 │ │  😐 │ │  😔 │ │  😔 │   │  │  │                     │ │
│  └─────┘ └─────┘ └─────┘ └─────┘   │  │  ● Dec 3               │ │
│                                      │  │  │  Work stress        │ │
│       ● ○  (Pagination dots)         │  │  │                     │ │
│                                      │  │  [Scrollable]          │ │
│  [Click for Fullscreen Detail]      │  │  [Popover on click]    │ │
└──────────────────────────────────────┴──────────────────────────────┘
```

**Grid gaps:**
- Horizontal gap between cards/panels: 24px
- Vertical gap between sections: 40px
- Container padding: 48px horizontal, 48px vertical

---

## Component Specifications with Visual Styling

### 1. Notes / Goals Panel (Top Left)

**Purpose:** AI-generated therapy journey summary

**Compact State Visual Design:**
- **Background:** White with subtle warm tint (hint of peach/cream gradient)
- **Border-radius:** 16px (rounded, friendly)
- **Shadow:** Soft drop shadow (`0 2px 8px rgba(0,0,0,0.08)`)
- **Padding:** 24px
- **Height:** ~280px
- **Typography:**
  - Title: 20px, Crimson Pro (serif), semibold, #2D3748
  - Body text: 14px, Inter, regular, #4A5568
  - Bullet points with teal accent dots
- **Content preview:**
  ```
  Notes / Goals
  ─────────────
  Based on 10 sessions, you've:
  • Reduced depression 67%
  • Mastered 3 coping strategies
  • Core pattern: work stress → conflict

  Current focus: Boundaries, Self-compassion
  ```
- **Hover state:**
  - Transform: scale(1.01)
  - Shadow increase: `0 4px 16px rgba(0,0,0,0.12)`
  - Subtle border accent (teal glow)
  - Cursor: pointer
  - Microinteraction: 200ms ease-out transition

**Expanded State (Modal):**
- **Size:** ~700px wide, variable height (max 80vh)
- **Background:** White
- **Border-radius:** 24px (larger for modal)
- **Shadow:** Elevated modal shadow (`0 20px 60px rgba(0,0,0,0.2)`)
- **Backdrop:** Grey overlay (`rgba(0,0,0,0.3)`) with backdrop blur (glassmorphism)
- **Close button:** X icon (32px) in top-right, 44px click target
- **Content:** Collapsible sections with ▼ indicators
  - ▼ Clinical Progress
  - ▼ Therapeutic Strategies Learned
  - ▼ Identified Patterns
  - ▼ Current Treatment Focus
  - ▼ Long-term Goals
- **Scrollable:** If content exceeds modal height
- **Animation:** Spring pop from card position (transform: scale(0.9→1), opacity: 0→1, 400ms cubic-bezier(0.34, 1.56, 0.64, 1))

---

### 2. AI Chat Integration - "Dobby" (Top Right)

**Purpose:** Therapy companion chatbot for session prep, questions, therapist messaging

**Compact State Visual Design:**
- **Background:** Light gradient (soft blue tint: #EBF8FF → #F0F9FF)
- **Border-radius:** 16px
- **Shadow:** Medium (`0 4px 12px rgba(0,0,0,0.1)`)
- **Padding:** 24px
- **Height:** ~280px
- **Logo:** Dobby character icon/avatar (~60px, centered at top)
- **Description text:** "Chat with Dobby to prepare for sessions, ask questions, and message your therapist."
- **Prompt carousel:**
  - 2 prompts visible at a time, 6 total (3 pages)
  - Pill-shaped buttons (~120px wide, 36px height)
  - Horizontal carousel with dots (● ○ ○)
  - Background: White with subtle shadow
  - Text: 13px, medium weight, #2D3748
  - Example prompts:
    - "Why does my mood drop after..."
    - "Help me prep to discuss boundaries..."
  - Arrows: < > for navigation
- **Chat input:**
  - Border: 1px solid #E2E8F0
  - Border-radius: 8px
  - Padding: 12px 16px
  - Placeholder: "Type your message..."
  - Send button: ↑ icon (teal accent)
  - Focus state: Teal border glow

**Fullscreen State:**
- **Size:** Full viewport (100vw × 100vh)
- **Background:** White (no backdrop)
- **Top bar:**
  - Height: 60px
  - Left: ← Back arrow
  - Center: "Chat with Dobby"
  - Right: X close button
  - Border-bottom: 1px solid #E2E8F0
- **Chat area:**
  - Full height scrollable
  - Chat bubbles:
    - User messages: Right-aligned, teal background (#5AB9B4), white text
    - Dobby messages: Left-aligned, light gray background (#F7FAFC), dark text
  - Border-radius: 16px on bubbles
  - Max-width: 70% per bubble
  - Spacing: 12px between messages
- **Description (hidden initially):**
  - Scroll to top reveals expanded description
  - Organized list format (not paragraph)
- **Prompt suggestions at bottom:**
  - Same carousel as compact state
  - Sticky at bottom above input
- **Animation:** Spring pop to fullscreen (same as modal)

---

### 3. To-Do Card (Middle Row - Left, Card 1)

**Purpose:** Homework task tracker with completion progress

**Compact State Visual Design:**
- **Background:** Flat white (no gradient) - UNIQUE STYLE
- **Border:** 1px solid #E2E8F0 (subtle border)
- **Border-radius:** 8px (sharp, functional look) - DISTINCT FROM OTHER CARDS
- **Shadow:** Minimal (`0 1px 4px rgba(0,0,0,0.06)`)
- **Padding:** 20px
- **Height:** ~300px
- **Typography:** Inter, regular weight (systematic feel)
- **Progress bar:**
  - Height: 8px
  - Border-radius: 4px
  - Background: #E2E8F0 (gray)
  - Fill: Gradient (teal #5AB9B4 → purple #B8A5D6)
  - Label: "50% (3/6)" on right side
- **Task list:**
  - Custom circular checkboxes (16px)
  - Unchecked: Border only (teal)
  - Checked: Filled teal with checkmark
  - Task text: 14px, regular
  - Completed tasks: Strikethrough + faded (opacity 0.5)
  - 3 tasks visible, "+3 more tasks" indicator
- **Carousel dots:** ● ○ ○ (future functionality for different task views)
- **Hover state:** Subtle lift (translateY(-2px)), shadow increase

**Expanded State (Modal):**
- **Layout:** Full task list with sections
  - Active Tasks (top)
  - Completed Tasks (bottom, separated by divider line)
- **Each task shows:**
  - Checkbox + task text
  - "From: Session 10 (Dec 17)" in smaller gray text
- **Actions:**
  - [+ Add New Task] button
  - [Archive Completed] [Delete Selected] buttons at bottom
- **Completed tasks:** Move to bottom with smooth animation (microinteraction)
- **Scrollable:** If tasks exceed modal height

---

### 4. Progress Patterns Card (Middle Row - Center, Card 2)

**Purpose:** Visual data insights with charts showing therapy progress

**Compact State Visual Design:**
- **Background:** Gradient (soft teal #5AB9B4 → lavender #B8A5D6) - UNIQUE STYLE
- **Border-radius:** 16px (fully rounded)
- **Shadow:** Elevated (`0 4px 12px rgba(0,0,0,0.1)`)
- **Padding:** 20px
- **Height:** ~300px
- **Typography:** Inter, medium weight (data-focused)
- **Neumorphism effect:** Subtle inner shadow + outer glow for soft 3D appearance
- **Carousel (4 pages):**
  - Page 1: Mood Trend (line chart)
  - Page 2: Homework Impact (bar chart)
  - Page 3: Session Consistency (calendar heatmap)
  - Page 4: Strategy Effectiveness (correlation chart)
- **Chart visualization (Page 1 - Mood Trend example):**
  - Line chart: X-axis = sessions, Y-axis = mood score
  - Line color: White with glow
  - Data points: White circles with subtle shadow
  - Grid lines: Semi-transparent white
  - Mock data: 10 sessions showing upward trend
  - Large emoji/icon: 📈
  - Text: "+30% improvement" (large, bold, white)
  - Subtext: Brief insight (1 line, smaller text)
- **Numbers:** Space Mono font (monospaced clarity)
- **Carousel dots:** ● ○ ○ ○ (Page 1 active)
- **Hover state:** Slight scale up (1.02), glow increase

**Expanded State (Modal):**
- **Layout:** All 4 metrics shown in vertical scroll (collapsible sections)
- **Each section:**
  - Collapsible header with ▼ indicator
  - Larger interactive chart (hover shows values)
  - Detailed text insights (2-3 sentences)
  - 200-300px height per chart
- **Charts with mock data:**
  - **Mood Trend:** Line chart, 10 data points, positive slope
  - **Homework Impact:** Bar chart, completion % vs mood correlation
  - **Session Consistency:** Calendar heatmap, weekly sessions highlighted
  - **Strategy Effectiveness:** Horizontal bar chart, strategy names + effectiveness scores
- **Chart colors:** Match gradient theme (teal/lavender/coral accents)
- **Interactive:** Hover states on data points (tooltip microinteraction)

---

### 5. Therapist Bridge Card (Middle Row - Right, Card 3)

**Purpose:** Session prep, conversation starters, progress sharing prompts

**Compact State Visual Design:**
- **Background:** Soft gradient with warm tint (#FFF5F0 → #FFF8F3) - UNIQUE STYLE
- **Border-radius:** 20px (pill-shaped, very rounded) - DISTINCT
- **Shadow:** Soft glow (`0 2px 16px rgba(91,185,180,0.15)`) with teal tint
- **Padding:** 24px
- **Height:** ~300px
- **Typography:** Inter, light weight (conversational feel)
- **Content (3 sections stacked):**
  ```
  Next Session Topics
  • Family boundaries

  Share Progress
  • Completed 3-week sleep plan

  Session Prep
  • Review anxiety journal
  ```
- **Section headings:** 15px, medium weight, teal accent (#5AB9B4)
- **Bullet items:** 14px, light weight, gray-700
- **No carousel:** All sections visible in compact state
- **Hover state:** Subtle glow increase, slight lift

**Expanded State (Modal):**
- **Layout:** 3 sections with full detail (read-only text)
  1. Conversation Starters (3-4 prompts with context)
  2. Share Progress with Therapist (3-4 achievements)
  3. Session Prep (3-4 action items)
- **Each bullet:** Full sentence with context
- **No interactive elements:** Pure informational content
- **Scrollable:** If content exceeds modal height
- **Typography:** Generous line-height (1.7) for easy reading

---

### 6. Session Cards Grid (Bottom Row - Left, 80% width)

**Purpose:** Chronological therapy session cards with quick previews

**Grid Layout:**
- **Columns:** 4
- **Rows:** 2 (8 cards per page)
- **Gap:** 16px between cards
- **Order:** Newest first (Dec 17 → Oct 15)
- **Pagination:** 2 pages total (Page 1: 8 cards, Page 2: 2 cards centered)
- **Dots:** ● ○ (Page 1 active)
- **Transition:** Horizontal slide (300ms ease-in-out)

**Individual Session Card Design:**

**Card structure (two-column internal split):**
```
┌─────────────────────────────────────────────┐
│ ⭐ Breakthrough: Self-compassion            │ ← Milestone badge (top border)
├─────────────────────────────────────────────┤
│  Dec 10  •  45m  •  😊                      │ ← Metadata row
├──────────────────────┬──────────────────────┤
│  SESSION TOPICS      │  SESSION STRATEGY    │
│  (Left 50%)          │  (Right 50%)         │
│                      │                      │
│  Self-worth          │  Laddering technique │
│  Past relationships  │                      │
│                      │  Actions:            │
│                      │  • Self-compassion   │
│                      │  • Behavioral exp.   │
└──────────────────────┴──────────────────────┘
```

**Visual specifications:**
- **Size:** Variable width (responsive to grid), ~200px height
- **Background:** White with subtle warm tint
- **Border-radius:** 12px
- **Shadow:** Soft (`0 2px 8px rgba(0,0,0,0.08)`)
- **Mood-based left border accent:**
  - Positive (😊): 3px left border, green-400 (#68D391)
  - Neutral (😐): 3px left border, blue-400 (#63B3ED)
  - Low (😔): 3px left border, rose-300 (#FDA4AF) - gentle, not harsh red
- **Milestone badge:**
  - Position: Absolutely positioned on top edge (breaks border)
  - Style: Pill badge with ⭐ icon
  - Background: Amber-100 (#FEF3C7)
  - Text: Amber-900 (#92400E), 12px, small caps, medium weight
  - Shadow: Gold glow (`0 0 12px rgba(251,191,36,0.4)`)
  - Z-index: elevated
  - Only on 5 sessions (S1, S2, S5, S7, S9)
- **Metadata row:**
  - Format: "[Date] • [Duration] • [Mood Emoji]"
  - Typography: 13px, medium weight, gray-600
  - Bullet separator: gray-400
- **Two-column split:**
  - Left: Session topics (2-3 keywords, line breaks)
  - Right: Strategy name (semibold, teal-600) + 2 action items (bullets)
  - Internal gap: 12px
  - Typography: 14px topics, 13px actions
- **Hover state:**
  - Lift: translateY(-4px)
  - Shadow increase: `0 6px 16px rgba(0,0,0,0.12)`
  - Top accent bar reveal (gradient sweep animation)
  - Cursor: pointer
  - Microinteraction: 200ms ease-out

**Fullscreen Session Detail:**
- **Trigger:** Click any session card
- **Layout:** Two-column split (50% transcript / 50% analysis)
- **Top bar:**
  - ← Back to Dashboard (left)
  - "Session 9 - Dec 10, 2025" (center)
  - ⭐ Breakthrough: Self-compassion (below title)
  - X close (right)
- **Left column (Transcript):**
  - Diarized transcript with speaker labels
  - "Therapist:" and "Patient:" labels (semibold)
  - Chat bubble style or simple labels
  - Scrollable
- **Right column (Analysis):**
  - Topics Discussed (bullet list)
  - Strategy Used (text block)
  - Session Mood (text)
  - Action Items (bullet list)
  - Patient Summary (text paragraph)
  - Scrollable independently
- **Animation:** Spring pop to fullscreen

---

### 7. Timeline Sidebar (Bottom Row - Right, 20% width)

**Purpose:** Quick navigation showing all sessions chronologically

**Compact State Visual Design:**
- **Background:** White
- **Border:** 1px solid #E2E8F0
- **Border-radius:** 12px
- **Padding:** 16px
- **Sticky positioning:** Stays visible while scrolling
- **Height:** Matches session cards grid height (~650px)
- **Scrollable:** If content exceeds height

**Timeline visual elements:**
- **Connector line:**
  - Vertical gradient line (2px width)
  - Gradient: top to bottom, teal (#5AB9B4) → lavender (#B8A5D6) → coral (#F4A69D)
  - Runs down left side
- **Timeline dots:**
  - Standard sessions: 10px circles, mood-colored (green/blue/rose)
  - Milestone sessions: 14px star icons (⭐) with subtle glow
  - Connected to vertical line
- **Entry content:**
  - Date: 13px, medium weight, gray-800
  - Topic: 12px, regular weight, gray-600, truncated (1-2 words)
  - Milestone text: 11px, italic, amber-700
- **Vertical spacing:** 16px between entries
- **NO emojis:** Use colored dots instead
- **Hover state:** Highlight entry (background: gray-50), cursor pointer
- **Click behavior:** Scrolls to corresponding session card (smooth scroll microinteraction)

**Expanded State (Popover):**
- **Trigger:** Click any timeline entry
- **Style:** Floating card next to timeline (not modal)
- **Size:** ~300px wide, auto height
- **Background:** White
- **Border-radius:** 12px
- **Shadow:** Elevated (`0 8px 24px rgba(0,0,0,0.12)`)
- **Arrow:** 8px triangular pointer connecting to timeline entry
- **Content:**
  - Session title + date
  - Duration, mood
  - Topics (bullet list)
  - Strategy name
  - Milestone description (if applicable)
  - [View Full Session →] link button
- **Close:** Click outside or X button
- **Animation:** Fade in + slight scale (200ms ease-out)
- **Positioning:** Dynamically positioned to avoid viewport edges (left or right of timeline)

---

## Expansion States & Animations

### Modal Specifications (Cards 1, 2, 3, 5 expanded states)

**Visual design:**
- **Size:** Variable (max 80vw width, 80vh height)
- **Background:** White
- **Border-radius:** 24px (larger than card state)
- **Padding:** 32px
- **Shadow:** Elevated modal (`0 20px 60px rgba(0,0,0,0.2)`)
- **Backdrop:** Grey overlay (`rgba(0,0,0,0.3)`) with backdrop-filter: blur(8px) (glassmorphism)
- **Z-index:** 1000

**Close behaviors:**
- X button (top-right, 32px icon, 44px click target)
- Click grey backdrop (outside modal)
- Visual indication: cursor changes when hovering backdrop

**Animation (Spring Pop - iPhone-style):**
- **Opening:**
  - Initial state: `transform: scale(0.9), opacity: 0`
  - Final state: `transform: scale(1), opacity: 1`
  - Duration: 400ms
  - Easing: `cubic-bezier(0.34, 1.56, 0.64, 1)` (spring bounce effect)
  - Origin: From card position (transform-origin set to card location)
- **Closing:**
  - Reverse animation
  - Duration: 300ms
  - Easing: ease-out

### Fullscreen Specifications (AI Chat, Session Cards)

**Visual design:**
- **Size:** Full viewport (100vw × 100vh)
- **Background:** White (no grey backdrop)
- **No border-radius:** Fills screen edge-to-edge
- **Top bar:** 60px height, border-bottom separator
  - Left: ← Back arrow (teal accent)
  - Center: Title/context
  - Right: X close button
- **Z-index:** 2000 (above modals)

**Animation:** Same spring pop effect but scales to full viewport

### Popover Specifications (Timeline expanded state)

**Visual design:**
- **Size:** ~300px wide, auto height (fits content)
- **Background:** White
- **Border-radius:** 12px
- **Shadow:** `0 8px 24px rgba(0,0,0,0.12)`
- **Arrow:** 8px triangular pointer (CSS border trick or SVG)
- **Z-index:** 500 (below modals)

**Animation:**
- **Opening:** Fade in + slight scale up
  - Initial: `opacity: 0, transform: scale(0.95)`
  - Final: `opacity: 1, transform: scale(1)`
  - Duration: 200ms
  - Easing: ease-out

---

## Interaction Patterns & Microinteractions

### Hover States (All Interactive Elements)

**Standard hover behavior:**
- **Cursor:** pointer
- **Transform:** scale(1.01) OR translateY(-2px) depending on component
- **Shadow:** Increase depth (add 4-8px to Y offset)
- **Transition:** 200ms ease-out
- **Border/Accent:** Subtle color shift or glow

**Session cards unique hover:**
- Top accent bar reveal (gradient sweep animation from left to right)
- Duration: 300ms
- Gradient: teal → lavender

### Click Targets (Accessibility)

**Minimum size:** 44px × 44px (WCAG AAA guideline)
- Buttons: height 44px, padding 12px 24px
- Checkboxes: 16px visual, 44px click area (invisible padding)
- Close buttons: 32px icon, 44px click area
- Carousel arrows: 44px × 44px

### Carousel Behavior (Progress Patterns, AI Chat Prompts)

**Specifications:**
- **Direction:** Horizontal (left/right)
- **Gesture:** Swipe or click < > arrows
- **Transition:** Slide animation (300ms ease-in-out)
- **Dots indicator:** ● = active (teal), ○ = inactive (gray-300)
- **Manual only:** No auto-advance
- **No loop:** Stop at first/last page

### Loading States (Skeleton Screens)

**Initial page load:**
- **Skeleton screens:** Shimmer animation on all cards
- **Shimmer effect:** Gradient moving left to right (gray-200 → gray-100 → gray-200)
- **Load order:** Staggered (top row → middle row → bottom row)
- **Stagger delay:** 100ms between rows
- **Animation:** Fade in (opacity 0 → 1, 400ms)

**Component loading:**
- Spinner or skeleton within card
- Disable interactions (cursor: not-allowed, opacity: 0.6)

### Completion Microinteractions (To-Do Checkbox)

**When checkbox is clicked:**
1. Checkbox fill animation (scale pulse: 0.8 → 1.2 → 1, 300ms)
2. Checkmark draw animation (stroke-dashoffset animation, 200ms)
3. Task text strikethrough animation (width: 0% → 100%, 300ms)
4. Task fades (opacity: 1 → 0.5, 300ms)
5. Task moves to bottom of list (smooth reorder animation, 500ms ease-out)
6. Progress bar fills (width animation, 400ms ease-out)

---

## Color Palette (Serene Therapy Theme)

**Primary Colors:**
- **Soft Teal:** #5AB9B4 (Primary CTAs, progress indicators, accent)
- **Warm Lavender:** #B8A5D6 (Secondary accents, anxiety metrics)
- **Gentle Coral:** #F4A69D (Warnings, low-mood indicators - NOT harsh red)

**Neutral Colors:**
- **Warm Cream:** #F7F5F3 (Page background)
- **White:** #FFFFFF (Card backgrounds)
- **Gray Scale:**
  - gray-50: #F7FAFC
  - gray-100: #EDF2F7
  - gray-200: #E2E8F0
  - gray-300: #CBD5E0
  - gray-400: #A0AEC0
  - gray-600: #718096
  - gray-700: #4A5568
  - gray-800: #2D3748
  - gray-900: #1A202C

**Mood Colors (Session Cards):**
- **Positive:** Soft Green #68D391 or Teal #5AB9B4
- **Neutral:** Soft Blue #63B3ED or Lavender #B8A5D6
- **Low:** Gentle Rose #FDA4AF (gentle, calming, NOT harsh red)

**Milestone/Accent:**
- **Amber-100:** #FEF3C7 (Milestone badge background)
- **Amber-900:** #92400E (Milestone badge text)
- **Gold glow:** rgba(251,191,36,0.4) (Milestone badge shadow)

**Gradients:**
- **Progress bar:** Linear 90deg, #5AB9B4 0%, #B8A5D6 100%
- **Progress Patterns background:** Linear 135deg, #5AB9B4 0%, #B8A5D6 100%
- **Timeline connector:** Vertical, #5AB9B4 0%, #B8A5D6 50%, #F4A69D 100%
- **Therapist Bridge background:** Linear 135deg, #FFF5F0 0%, #FFF8F3 100%

**Allow creative freedom:** Use this palette as reference but explore variations within the "serene therapy" theme (warm, calm, soft, trustworthy). Gemini can adjust saturation, add subtle textures, or introduce complementary accent colors.

---

## Typography System

**Font Families:**
- **Headings:** Crimson Pro (serif) - editorial, warm, humanistic
- **Body:** Inter (sans-serif) - clean, readable, modern
- **Data/Numbers:** Space Mono (monospace) - optional for charts and metrics

**Type Scale:**
- **Page Title:** 48px, semibold
- **Section Headers:** 20px, semibold
- **Card Titles:** 18px, medium
- **Body Text:** 14px, regular
- **Small Text:** 12px, regular
- **Large Numbers (scores):** 48-56px, bold

**Font Weights:**
- **Light:** 300 (Therapist Bridge - conversational feel)
- **Regular:** 400 (To-Do, body text - functional)
- **Medium:** 500 (Progress Patterns, headers - data-focused)
- **Semibold:** 600 (headings)
- **Bold:** 700 (large numbers, emphasis)

**Line Heights:**
- **Headings:** 1.2
- **Body text:** 1.6
- **Compact cards:** 1.5
- **Expanded modals:** 1.7 (more generous for reading)

---

## Spacing & Layout System

**Base unit:** 4px (all spacing should be multiples of 4)

**Spacing scale:**
- xs: 4px
- sm: 8px
- md: 12px
- lg: 16px
- xl: 24px
- 2xl: 32px
- 3xl: 48px

**Common usage:**
- **Card padding:** 24px (xl)
- **Card gap:** 24px (xl)
- **Section gap:** 40px (between top/middle/bottom rows)
- **Button padding:** 12px 24px (md xl)
- **Input padding:** 12px 16px (md lg)
- **Modal padding:** 32px (2xl)

**Whitespace philosophy:** Generous breathing room between components. Don't overcrowd - therapy dashboards should feel calm and spacious.

---

## Shadow System (Depth Hierarchy)

**Shadow levels:**
- **None:** box-shadow: none
- **Subtle:** 0 1px 4px rgba(0,0,0,0.06) (To-Do card)
- **Soft:** 0 2px 8px rgba(0,0,0,0.08) (Session cards, Notes/Goals)
- **Medium:** 0 4px 12px rgba(0,0,0,0.1) (Progress Patterns, AI Chat)
- **Elevated:** 0 8px 24px rgba(0,0,0,0.12) (Timeline popover)
- **Modal:** 0 20px 60px rgba(0,0,0,0.2) (Expanded modals)

**Special glows:**
- **Milestone glow:** 0 0 12px rgba(251,191,36,0.4) (gold)
- **Therapist Bridge glow:** 0 2px 16px rgba(91,185,180,0.15) (teal)

**Hover shadow increase:** Add 4-8px to Y offset, increase blur radius by 4-8px

---

## Border Radius Variation (Widget Differentiation)

**Scale:**
- **Sharp:** 8px (To-Do card - functional, systematic)
- **Default:** 12px (Session cards, Timeline - standard rounded)
- **Rounded:** 16px (Most cards, modal inner elements - friendly)
- **Very rounded:** 20px (Therapist Bridge - pill-shaped, conversational)
- **Modal:** 24px (Outer modal container - premium feel)

**Philosophy:** Each card should feel like a distinct widget app with unique personality through border-radius variation.

---

## Responsive Behavior (Desktop-Only for MVP)

**Target viewport:** 1440px width (desktop-optimized)
- Min-width: 1024px
- Optimized for: 1440px - 1920px viewports
- Container: 1400px max-width, centered

**No tablet/mobile layouts needed** - This is a desktop web app for MVP/demo purposes.

---

## Artboard Specifications for Gemini Output

**Please generate multiple artboards showing:**

### Artboard 1: Full Dashboard - Compact State (Primary View)
- **Size:** 1440px × 2400px (full page scroll)
- **Content:** All components in compact state (default view)
- **Background:** Warm cream (#F7F5F3)
- **Show:** Sticky header, all 7 components, proper spacing
- **Annotations:** Component names labeled

### Artboard 2: Notes/Goals Expanded (Modal State)
- **Size:** 1440px × 900px
- **Content:** Notes/Goals modal open on grey backdrop
- **Show:** Spring animation state (scale transformation visual)
- **Details:** Collapsible sections with ▼ indicators, scrollable content

### Artboard 3: AI Chat Fullscreen (Dobby Conversation)
- **Size:** 1440px × 900px
- **Content:** AI Chat in fullscreen mode with mock conversation
- **Show:** Top bar, chat bubbles (user + Dobby), prompt carousel at bottom, input field
- **Details:** Demonstrate scroll-to-top description reveal

### Artboard 4: Session Card Fullscreen Detail
- **Size:** 1440px × 900px
- **Content:** Session detail view with two-column split
- **Show:** Left = diarized transcript, Right = analysis panel
- **Details:** Milestone badge in header, scrollable content

### Artboard 5: Progress Patterns Expanded Modal
- **Size:** 1440px × 900px
- **Content:** All 4 metrics shown in vertical scroll
- **Show:** Large interactive charts with mock data visualization
- **Details:** Mood trend line chart, homework bar chart, consistency heatmap, strategy effectiveness chart

### Artboard 6: Component States Showcase
- **Size:** 1920px × 1080px (landscape)
- **Content:** Side-by-side comparison showing:
  - Left: Compact card states
  - Right: Expanded modal states
- **Show:** To-Do, Progress Patterns, Therapist Bridge comparisons
- **Purpose:** Demonstrate expansion transformations

### Artboard 7: Hover States & Microinteractions
- **Size:** 1920px × 1080px (landscape)
- **Content:** Grid showing hover states for all interactive elements
- **Show:**
  - Session cards (default vs hover with accent bar)
  - Buttons (default vs hover)
  - Checkboxes (unchecked, checked, completion animation frames)
  - Timeline entries (default vs hover vs popover)
- **Purpose:** Demonstrate microinteraction details

### Artboard 8: Timeline Popover Detail
- **Size:** 800px × 600px (zoomed detail)
- **Content:** Timeline sidebar with popover open
- **Show:** Popover arrow connection, session preview content
- **Details:** Floating card design, shadow, positioning

### Artboard 9: Skeleton Loading States
- **Size:** 1440px × 2400px
- **Content:** Dashboard with skeleton screens (shimmer effect)
- **Show:** All cards in loading state before data loads
- **Details:** Shimmer gradient animation visualization

### Artboard 10: Animation Flow Diagram
- **Size:** 1920px × 1080px
- **Content:** Visual diagram showing expansion animation
- **Show:** 4 frames of spring animation (card → scale 0.9 → scale 1.1 → scale 1)
- **Details:** Transform states with timing annotations
- **Purpose:** Technical reference for developers

---

## Design Constraints & Must-Avoid

**❌ DO NOT INCLUDE:**
- Multiple simultaneous modals/fullscreens (only ONE expansion at a time)
- Auto-advancing carousels (all manual navigation)
- Emojis in Timeline sidebar (use colored dots instead)
- Harsh red colors for low mood (use gentle rose/coral)
- Gamification elements (confetti, achievements, badges beyond milestones)
- Clinical progress cards showing PHQ-9/GAD-7 scores (removed from this design)
- Checkbox or button interactions in Therapist Bridge expanded state (read-only)

**✅ MUST INCLUDE:**
- Unique visual styling for each widget (different border-radius, shadows, backgrounds)
- Spring animations for modal expansions (show before/after states)
- Grey backdrop with glassmorphism (backdrop blur) for modals
- Milestone badges breaking top border on session cards
- Two-column internal split on session cards (topics left, strategy right)
- Mood-based left border accents on session cards (green/blue/rose)
- Vertical gradient connector line on timeline (teal → lavender → coral)
- Pill-shaped prompts in AI Chat carousel
- Progress bar gradient (teal → purple) on To-Do card
- Generous whitespace (therapy-appropriate calm spacing)

---

## Technical Design Notes for Implementation

**Frameworks suggested:**
- **React 19** with Next.js 16 (App Router)
- **Tailwind CSS** for utility-first styling
- **Framer Motion** for spring animations
- **Radix UI** or **shadcn/ui** for accessible components (modals, popovers, accordions)
- **Recharts** or **Chart.js** for data visualizations

**CSS Features:**
- **Glassmorphism:** `backdrop-filter: blur(8px)` on modal backdrops
- **Neumorphism:** Combined inner/outer shadows on Progress Patterns card
- **CSS Grid:** Layout system for responsive grid
- **CSS Custom Properties:** Color palette as CSS variables
- **CSS Animations:** Keyframe animations for shimmer, sweep, pulse

**Accessibility:**
- ARIA labels for all interactive elements
- Focus trap within modals (tab cycling)
- Keyboard navigation (Tab, Enter, ESC, Arrow keys)
- Screen reader announcements for state changes
- Color contrast ratios meeting WCAG AA (minimum 4.5:1 for body text)

---

## Design Inspiration & Visual References

**Style influences:**
- **Apple Health app** - Clean data visualization, calm aesthetics
- **Headspace app** - Warm gradients, friendly UI, breathing room
- **Notion** - Widget-based modular interface
- **Linear** - Spring animations, premium feel, attention to microinteractions
- **Calm app** - Serene color palette, soft shadows, therapeutic design

**Avoid references:**
- Medical/clinical dashboards (too sterile, harsh)
- Fitness tracking apps (too aggressive, gamified)
- Social media layouts (too busy, distracting)

---

## Success Criteria for Superdesign Output

**The design should make the viewer feel:**
- 😌 Calm and reassured (not stressed or overwhelmed)
- 🌸 Warmth and trust (therapy-appropriate emotions)
- ✨ Delighted by subtle interactions (microinteractions spark joy)
- 📊 Informed and empowered (clear data hierarchy)
- 🎨 Impressed by polish (premium, state-of-the-art quality)

**Visual quality bar:**
- Dribbble "Popular" level design quality
- Portfolio-worthy presentation
- Production-ready specs (not just concept art)
- Detailed enough for developers to implement directly

---

## Final Notes

**Creative freedom zones:**
- Texture overlays on page background (subtle grain, noise)
- Icon style (line icons vs filled vs custom illustrations)
- Chart visualization aesthetics (bar shapes, line styles, data point markers)
- Micro-typography choices (letter-spacing, text-transform for labels)
- Subtle animations (page load sequences, hover effects beyond specs)

**Strict adherence required:**
- Layout proportions (50/50, 33/33/33, 80/20 splits)
- Color palette (teal/lavender/coral as primary, warm neutrals)
- Widget differentiation (each card must feel visually distinct)
- Expansion states (modal vs fullscreen vs popover patterns)
- Spacing system (24px gaps, 40px section spacing, 48px container padding)

---

## Gemini 3 Pro - Generate a state-of-the-art therapy dashboard design following this specification. Create multiple artboards showing compact states, expanded modals, fullscreen views, and microinteraction details. The design should feel warm, calm, premium, and delightful to use. Make this a portfolio-worthy, production-ready design system.
