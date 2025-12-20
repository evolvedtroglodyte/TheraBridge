# SuperDesign Build Prompt: TherapyBridge Session Cards

## Component Type
**Production React Component Build** - Session card for therapy session grid display

## Reference Implementation
- **Current file:** `/tmp/src/components/SessionCard.tsx`
- **Framework:** React + TypeScript + Tailwind CSS + Framer Motion
- **Purpose:** Compact session preview cards in 4-column grid layout

---

## Design Brief

Redesign therapy session cards to match architectural specification with focus on:
1. **Information density** - Condensed preview (max 20 words total)
2. **Implicit hierarchy** - No visible column headers, typography creates structure
3. **Visual refinement** - Subtle separator, proper text overflow handling
4. **Therapy-appropriate aesthetic** - Calm, warm, trustworthy visual language

---

## Current Implementation Issues

**Problems to fix:**
1. ❌ **Explicit headers** - "SESSION TOPICS" and "SESSION STRATEGY" labels take up space
2. ❌ **Text overflow** - Content leaks to next line, breaks card layout
3. ❌ **Content density** - Too verbose, showing full sentences and all action items
4. ❌ **Weak hierarchy** - Everything same visual weight, hard to scan

**What's working (preserve):**
- ✅ Two-column internal split (50/50)
- ✅ Milestone badge (floating on top border)
- ✅ Mood-based left border accent
- ✅ Hover effects (lift + shadow)
- ✅ Metadata row format

---

## Component Structure

### Layout Hierarchy

```
┌─────────────────────────────────────────────┐
│ ⭐ BREAKTHROUGH (if milestone)              │ ← Floating badge
├─────────────────────────────────────────────┤
│ [3px mood border]                           │
│                                             │
│  Dec 10 • 45m • 😊                          │ ← Metadata row
│                                             │
│  ┌──────────────┬─│────────────┐           │
│  │              │ │            │           │ ← Subtle separator
│  │ Self-worth,  │ │ Laddering  │           │
│  │ Past         │ │ technique  │           │
│  │ relationships│ │            │           │
│  │              │ │            │           │
│  └──────────────┴─│────────────┘           │
│                                             │
└─────────────────────────────────────────────┘
```

### Implicit Two-Column Structure

**NO visible headers.** Typography and layout create the structure:

**Left Column (50%):**
- **Content:** 2-3 topic keywords only (comma-separated or line breaks)
- **Typography:** 14px, regular (400), gray-700 `#374151`
- **Line clamping:** `line-clamp-2` (max 2 lines, ellipsis overflow)
- **Example:** "Self-worth, Past relationships" or "Work stress, Perfectionism"

**Vertical Separator:**
- **Style:** 1px solid line, full height of content area
- **Color:** Gray-200 `#E5E7EB`
- **Position:** Between columns (at 50% mark)
- **Opacity:** 0.5 (subtle, not distracting)

**Right Column (50%):**
- **Content:** Strategy name ONLY (no action items)
- **Typography:** 14px, **semibold (600)**, teal-600 `#0D9488`
- **Line clamping:** `line-clamp-2` (max 2 lines, ellipsis overflow)
- **Example:** "Laddering technique" or "Cognitive restructuring"

---

## Detailed Specifications

### Card Container

**Dimensions:**
- Width: Responsive (grid-based, ~220px in 4-column layout)
- Height: ~200-220px (consistent across cards)
- Aspect ratio: Flexible, content-driven

**Styling:**
- Background: White with subtle warm tint `bg-gradient-to-br from-white to-[#FEFDFB]`
- Border-radius: 12px
- Border-left: 3px solid (mood color)
- Box-shadow: `0 2px 8px rgba(0,0,0,0.08)` (soft)
- Padding: 16px all sides

**Mood-Based Left Border:**
- Positive (😊): `#5AB9B4` (soft teal)
- Neutral (😐): `#B8A5D6` (lavender)
- Low (😔): `#F4A69D` (gentle coral/rose)

**Hover State:**
- Transform: `translateY(-4px)` (lift effect)
- Box-shadow: `0 6px 16px rgba(0,0,0,0.12)` (deeper)
- Transition: 200ms ease-out
- Cursor: pointer

### Milestone Badge (Optional)

**When present (5 of 10 sessions):**

**Position:**
- Absolutely positioned on top edge
- Breaking the card border (floating above)
- Z-index: 10
- Left: 16px from card edge
- Top: -8px (negative offset)

**Styling:**
- Background: Amber-100 `#FEF3C7`
- Border-radius: 9999px (full pill)
- Padding: 4px 10px
- Box-shadow: `0 0 12px rgba(251,191,36,0.4)` (golden glow)

**Content:**
- Icon: Star (filled) - 10px, amber-900
- Text: "BREAKTHROUGH" or "COMPLETED" - 9px, uppercase, medium (500), amber-900 `#92400E`
- Gap: 4px between icon and text
- Letter-spacing: 0.5px (tracking-wide)

### Metadata Row

**Format:** `Date • Duration • Mood`

**Order:** Date first, then duration, then mood emoji
- Example: `Dec 10 • 45m • 😊`

**Styling:**
- Typography: 13px, medium (500), gray-600 `#4B5563`
- Bullet separator: `•` gray-400, 2-3px gap
- Margin-bottom: 12px (spacing before columns)
- Flex layout: items-center, gap-2

**Date format:** "Dec 10" (short month + day)
**Duration format:** "45m" (abbreviated)
**Mood emoji:** Standard emoji (😊 😐 😔) - 16px size

### Two-Column Content Area

**Container:**
- Display: Grid, 2 columns (50% / 50%)
- Gap: 12px (horizontal space between columns)
- Flex: 1 (grows to fill available space)

**Vertical Separator:**
- Position: Absolute or pseudo-element `::after`
- Height: 100% of content area
- Width: 1px
- Background: `#E5E7EB` (gray-200)
- Opacity: 0.5
- Left: 50% (centered between columns)
- Transform: translateX(-50%)

**Left Column - Topics:**
- **Content:** 2-3 keywords maximum
- **Typography:**
  - Font-size: 14px
  - Font-weight: 400 (regular)
  - Color: `#374151` (gray-700)
  - Line-height: 1.4
- **Overflow:** `line-clamp-2` (truncate after 2 lines with ellipsis)
- **Word-break:** `break-words` (prevent single word overflow)
- **Example content:**
  - "Self-worth, Past relationships"
  - "Work stress, Perfectionism"
  - "Boundaries, Family"

**Right Column - Strategy:**
- **Content:** Strategy name only (NO action items)
- **Typography:**
  - Font-size: 14px
  - Font-weight: 600 (semibold) ← **Visual distinction**
  - Color: `#0D9488` (teal-600) ← **Color distinction**
  - Line-height: 1.4
- **Overflow:** `line-clamp-2` (truncate after 2 lines with ellipsis)
- **Word-break:** `break-words`
- **Example content:**
  - "Laddering technique"
  - "Cognitive restructuring"
  - "Sleep hygiene protocol"

---

## Typography Scale

| Element | Size | Weight | Color | Line Height |
|---------|------|--------|-------|-------------|
| Milestone badge text | 9px | 500 | Amber-900 | 12px |
| Date/Duration | 13px | 500 | Gray-600 | 1.2 |
| Topics (left) | 14px | **400** | Gray-700 | 1.4 |
| Strategy (right) | 14px | **600** | Teal-600 | 1.4 |

**Font family:** Inter (sans-serif) for all text

---

## Content Condensation Rules

**Total card content limit:** ~20 words maximum

**Topics (left column):**
- Use 2-3 keywords only (not full sentences)
- Comma-separated or line breaks
- Examples:
  - ✅ "Self-worth, Past relationships"
  - ✅ "Work stress, Perfectionism"
  - ❌ "Self-worth exploration and discussion about past relationships" (too verbose)

**Strategy (right column):**
- Strategy name only (1-3 words)
- NO action items, NO bullet lists
- Examples:
  - ✅ "Laddering technique"
  - ✅ "Cognitive restructuring"
  - ✅ "DBT skills training"
  - ❌ "Laddering technique - helped identify core beliefs" (too verbose)

**Overflow handling:**
- `line-clamp-2` on both columns
- Ellipsis (`...`) when truncated
- `overflow-hidden` to prevent visual leakage

---

## Color Palette

**Primary Colors:**
- Soft Teal: `#5AB9B4` (positive mood border, strategy text)
- Warm Lavender: `#B8A5D6` (neutral mood border)
- Gentle Coral: `#F4A69D` (low mood border)

**Neutrals:**
- White: `#FFFFFF` (card background base)
- Warm Tint: `#FEFDFB` (gradient to)
- Gray-700: `#374151` (topic text)
- Gray-600: `#4B5563` (metadata text)
- Gray-400: `#9CA3AF` (bullet separator)
- Gray-200: `#E5E7EB` (separator line)

**Milestone Colors:**
- Amber-100: `#FEF3C7` (badge background)
- Amber-900: `#92400E` (badge text)
- Gold glow: `rgba(251,191,36,0.4)` (shadow)

---

## Interaction States

### Default State
- Box-shadow: `0 2px 8px rgba(0,0,0,0.08)`
- Transform: none
- Mood border: 3px solid (color based on mood)

### Hover State
- Transform: `translateY(-4px)`
- Box-shadow: `0 6px 16px rgba(0,0,0,0.12)`
- Transition: `all 200ms ease-out`
- Cursor: pointer
- Optional: Subtle top accent bar reveal (gradient sweep)

### Focus State (keyboard navigation)
- Outline: 2px solid teal-500
- Outline-offset: 2px
- Accessible focus indicator

---

## Animation Specifications

**Hover animation:**
```css
transition: transform 200ms ease-out, box-shadow 200ms ease-out;
```

**Click animation (opens fullscreen session):**
- Spring pop expansion (handled by parent component)
- Card serves as animation origin point

---

## Responsive Behavior

**Desktop (1024px+):**
- 4 columns × 2 rows = 8 cards per page
- Gap: 16px between cards
- Full specifications as above

**Future tablet/mobile (not in MVP):**
- 2 columns on mobile
- Cards maintain aspect ratio
- Text remains clamped at 2 lines

---

## Accessibility Requirements

**Keyboard Navigation:**
- Card is focusable: `tabindex="0"`
- Enter/Space to activate (open fullscreen)
- Focus indicator: visible outline

**Screen Reader:**
- ARIA label: "Session {number} on {date}, mood {mood}, topics {topics}, strategy {strategy}"
- ARIA role: "button" (interactive card)
- Milestone announced: "Breakthrough session" or "Milestone completed"

**Semantic HTML:**
- Use semantic elements where appropriate
- Proper heading hierarchy (if needed)

---

## Technical Implementation

### React Component Structure

```tsx
interface SessionCardProps {
  session: Session;
  onClick: () => void;
}

// Session type
interface Session {
  id: string;
  date: string;         // "Dec 10"
  duration: string;     // "45m"
  mood: 'positive' | 'neutral' | 'low';
  topics: string[];     // Max 2-3 keywords
  strategy: string;     // Strategy name only
  milestone?: {
    title: string;      // "Breakthrough: Self-compassion"
  };
}
```

### Component Implementation Notes

**Remove from current implementation:**
- ❌ Column headers: "Session Topics" and "Session Strategy"
- ❌ "Actions:" label and action item bullets
- ❌ Verbose topic descriptions

**Add to implementation:**
- ✅ Vertical separator line (1px, centered)
- ✅ `line-clamp-2` on both topic and strategy text
- ✅ Content condensation (2-3 keywords max)

**Preserve from current implementation:**
- ✅ Milestone badge logic and styling
- ✅ Mood-based border color function
- ✅ Hover animation with Framer Motion
- ✅ Click handler for fullscreen

### Tailwind CSS Classes Reference

**Card container:**
```tsx
className="relative bg-gradient-to-br from-white to-[#FEFDFB] rounded-xl p-4 cursor-pointer overflow-visible h-full flex flex-col"
style={{ borderLeft: `3px solid ${moodColor}`, boxShadow: '0 2px 8px rgba(0,0,0,0.08)' }}
```

**Metadata row:**
```tsx
className="flex items-center gap-2 mb-3 text-xs font-medium text-gray-600"
```

**Two-column grid:**
```tsx
className="grid grid-cols-2 gap-3 flex-1 relative"
```

**Vertical separator:**
```tsx
// Pseudo-element or absolute div
className="absolute left-1/2 top-0 bottom-0 w-px bg-gray-200 opacity-50 -translate-x-1/2"
```

**Left column (topics):**
```tsx
className="text-sm text-gray-700 line-clamp-2 break-words"
```

**Right column (strategy):**
```tsx
className="text-sm font-semibold text-teal-600 line-clamp-2 break-words"
```

---

## Mock Data Examples

**Session with milestone (positive mood):**
```tsx
{
  id: 's9',
  date: 'Dec 10',
  duration: '45m',
  mood: 'positive',
  topics: ['Self-worth', 'Past relationships'],  // 2 keywords
  strategy: 'Laddering technique',               // Strategy only
  milestone: {
    title: 'Breakthrough: Self-compassion'
  }
}
```

**Session without milestone (neutral mood):**
```tsx
{
  id: 's8',
  date: 'Dec 3',
  duration: '48m',
  mood: 'neutral',
  topics: ['Work stress', 'Perfectionism'],      // 2 keywords
  strategy: 'Cognitive restructuring'            // Strategy only
}
```

**Session without milestone (low mood):**
```tsx
{
  id: 's4',
  date: 'Nov 5',
  duration: '50m',
  mood: 'low',
  topics: ['Childhood trauma', 'Trust'],         // 2 keywords
  strategy: 'Trauma-focused CBT'                 // Strategy only
}
```

---

## Visual Design Principles

**1. Information Hierarchy:**
- Most prominent: Milestone badge (gold glow, top position)
- Secondary: Strategy name (semibold, teal color)
- Tertiary: Topics (regular weight, gray)
- Supporting: Metadata (smaller, gray-600)

**2. Progressive Disclosure:**
- Card shows condensed preview (~20 words)
- Click opens fullscreen with full session details
- Compact state encourages scanning/browsing
- Fullscreen state for deep reading

**3. Visual Rhythm:**
- Consistent card heights create grid harmony
- 2-line text clamping prevents layout shifts
- Mood borders provide color-coded pattern
- Milestone badges break rhythm intentionally (draw attention)

**4. Therapy-Appropriate Aesthetics:**
- Soft, rounded corners (12px) - approachable
- Warm color tints - comforting
- No harsh reds - gentle coral for low mood
- Subtle shadows - calm, not dramatic

---

## Success Criteria

A successful implementation will:
1. ✅ Remove all visible column headers ("SESSION TOPICS", "SESSION STRATEGY")
2. ✅ Create implicit structure through typography (weight, color)
3. ✅ Show subtle 1px vertical separator between columns
4. ✅ Condense content to 2-3 keywords (topics) + strategy name only
5. ✅ Prevent text overflow with `line-clamp-2` on both columns
6. ✅ Maintain metadata order: Date • Duration • Mood
7. ✅ Preserve milestone badge, mood border, hover effects
8. ✅ Total card content ~20 words maximum
9. ✅ Be scannable in 2-3 seconds per card
10. ✅ Feel therapy-appropriate (calm, warm, trustworthy)

---

## Build Output Requirements

**Generate production-ready React + TypeScript component:**
- Functional component with TypeScript interfaces
- Tailwind CSS classes (no custom CSS unless necessary)
- Framer Motion for hover animations
- Proper accessibility attributes (ARIA labels, focus states)
- Responsive design considerations
- Clean, maintainable code structure

**Files to output:**
- `SessionCard.tsx` - Main component
- Type definitions included inline or imported from `types.ts`
- Usage example with mock data

---

**End of Build Prompt**

Generate a production-ready session card component matching these exact specifications. Focus on implicit hierarchy through typography, content condensation, and proper overflow handling.
