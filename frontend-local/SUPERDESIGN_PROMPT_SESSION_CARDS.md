# Superdesign Wireframe Prompt: TherapyBridge Session Cards

## Context
Design wireframes for therapy session cards in a patient dashboard. These cards appear in a 4-column grid showing historical therapy sessions. Each card must be compact yet informative, with a two-column internal split.

---

## Card Specifications

### Overall Card Dimensions
- **Width**: ~220px (responsive in 4-column grid)
- **Height**: ~200-220px (consistent height, auto if needed)
- **Border radius**: 12px (default rounded, not too sharp)
- **Shadow**: Soft drop shadow `0 2px 8px rgba(0,0,0,0.08)`
- **Background**: White with subtle warm tint
- **Hover effect**: Lift up 4px + shadow deepens to `0 6px 16px rgba(0,0,0,0.12)`

### Mood-Based Left Border Accent
- **Width**: 3px solid vertical bar on left edge
- **Colors**:
  - Positive mood (😊): Soft green `#A8C69F` or Teal `#5AB9B4`
  - Neutral mood (😐): Lavender `#B8A5D6`
  - Low mood (😔): Gentle rose/coral `#F4A69D` (NOT harsh red)

---

## Card Layout Structure

The card has THREE distinct visual sections:

### 1. TOP: Milestone Badge (Optional - Only 5 of 10 cards)
- **Position**: Absolutely positioned on TOP EDGE, breaking the border (floating above)
- **Style**: Pill-shaped badge with star icon
- **Background**: Amber-100 `#FEF3C7`
- **Text color**: Amber-900 `#92400E`
- **Glow effect**: Subtle golden glow `0 0 12px rgba(251,191,36,0.4)`
- **Content**: Star icon + "BREAKTHROUGH" or "COMPLETED" in small caps
- **Typography**: 11px, uppercase, medium weight, letter-spacing: 0.5px
- **Example**: `⭐ BREAKTHROUGH`
- **Visual prominence**: Should feel special but not overwhelming

### 2. METADATA ROW (Below milestone, top of card content)
- **Format**: `[Date] • [Duration] • [Mood Emoji]`
- **Examples**:
  - `Dec 10 • 45m • 😊`
  - `Nov 5 • 50m • 😔`
- **Typography**: 13px, medium weight, gray-600 (#4B5563)
- **Bullet separator**: Gray-400 `•` character
- **Spacing**: Tight horizontal spacing, 2-3px gap between elements
- **Margin bottom**: 12px before two-column section

### 3. TWO-COLUMN SPLIT (Main content area)
The card is divided **vertically** into two equal columns (50% each).

#### LEFT COLUMN: Session Topics
- **NO HEADER LABEL** (implicit - don't show "Session Topics")
- **Content**: 2-3 topic keywords/phrases
- **Display format**: Line breaks or commas (your design choice)
- **Typography**: 14px, regular weight, gray-700 (#374151)
- **Example content**:
  ```
  Self-worth
  Past relationships
  ```
  OR
  ```
  Boundaries, Family dynamics
  ```
- **Max length**: ~15 words total (condensed preview, not full sentences)
- **Line clamping**: 3-4 lines max

#### RIGHT COLUMN: Strategy + Actions
- **NO HEADER LABEL** (implicit - don't show "Session Strategy")
- **Content structure**:
  1. **Strategy name** (prominent)
  2. **2 action items** (secondary, bullets or pills)

- **Strategy typography**:
  - 14px, **semibold**, teal-600 `#0D9488`
  - Stands out visually from topics

- **Actions typography**:
  - 13px, regular weight, gray-600
  - Prefix with bullet `•` or small pill badges
  - 2 lines max (truncate with ellipsis if needed)

- **Example content**:
  ```
  Laddering technique

  • Self-compassion
  • Behavioral experiment
  ```

**CRITICAL DESIGN RULE**:
- NO visible column dividers or headers saying "SESSION TOPICS" or "SESSION STRATEGY"
- The visual distinction comes from CONTENT and TYPOGRAPHY, not labels
- Total card content: **Max 20 words** (this is a condensed preview, not full detail)

---

## Visual Hierarchy (Typography Scale)

| Element | Size | Weight | Color |
|---------|------|--------|-------|
| Milestone badge text | 11px | Medium (500) | Amber-900 |
| Date/Duration | 13px | Medium (500) | Gray-600 |
| Session topics | 14px | Regular (400) | Gray-700 |
| Strategy name | 14px | **Semibold (600)** | Teal-600 `#0D9488` |
| Action items | 13px | Regular (400) | Gray-600 |

---

## Example Card Layouts

### Example 1: Card WITH Milestone
```
┌─────────────────────────────────────────────┐
│ ⭐ BREAKTHROUGH (floating above border)     │ ← Golden glow badge
├─────────────────────────────────────────────┤
│ [3px teal border]                           │
│                                             │
│  Dec 10 • 45m • 😊                          │ ← Metadata row
│                                             │
│  ┌──────────────┬──────────────┐           │
│  │              │              │           │
│  │ Self-worth   │ Laddering    │ ← Strategy (teal, bold)
│  │ Past         │ technique    │
│  │ relationships│              │
│  │              │ • Self-      │ ← Actions (gray, bullets)
│  │              │   compassion │
│  │              │ • Behavioral │
│  │              │   experiment │
│  └──────────────┴──────────────┘           │
│                                             │
└─────────────────────────────────────────────┘
```

### Example 2: Card WITHOUT Milestone
```
┌─────────────────────────────────────────────┐
│ [3px rose border for low mood]              │
│                                             │
│  Nov 5 • 50m • 😔                           │ ← Metadata row
│                                             │
│  ┌──────────────┬──────────────┐           │
│  │              │              │           │
│  │ Childhood    │ Trauma-      │ ← Strategy (teal, bold)
│  │ trauma       │ focused CBT  │
│  │ Trust issues │              │
│  │              │ • Grounding  │ ← Actions (gray)
│  │              │ • Safety plan│
│  └──────────────┴──────────────┘           │
│                                             │
└─────────────────────────────────────────────┘
```

### Example 3: Card with Neutral Mood
```
┌─────────────────────────────────────────────┐
│ [3px lavender border]                       │
│                                             │
│  Dec 3 • 48m • 😐                           │ ← Metadata row
│                                             │
│  ┌──────────────┬──────────────┐           │
│  │              │              │           │
│  │ Work stress, │ Cognitive    │ ← Strategy (teal, bold)
│  │ Perfectionism│ restructuring│
│  │              │              │
│  │              │ • Challenge  │ ← Actions
│  │              │   thoughts   │
│  │              │ • Priority   │
│  │              │   matrix     │
│  └──────────────┴──────────────┘           │
│                                             │
└─────────────────────────────────────────────┘
```

---

## Design Goals & Constraints

### ✅ Design Goals
1. **Scannable at a glance** - User should instantly see: date, mood, main topic, strategy used
2. **Therapy-appropriate aesthetics** - Calm, warm, trustworthy (not corporate/clinical)
3. **Milestone prominence** - Breakthrough sessions should stand out visually
4. **Compact yet readable** - Information hierarchy through typography, not labels
5. **Mood color psychology** - Left border provides instant mood context without being harsh

### ❌ Avoid
1. **Don't add header labels** like "SESSION TOPICS" or "SESSION STRATEGY" (implicit structure)
2. **Don't cram too much text** - This is a preview card, not the full session detail
3. **Don't use harsh red** for low mood - Use gentle rose/coral instead
4. **Don't use vertical dividers** between columns - Let white space create separation
5. **Don't make milestone badges too large** - Subtle prominence, not overwhelming

---

## Color Palette Reference

### Primary Colors (from design system)
- **Soft Teal**: `#5AB9B4` (strategy text, positive mood border)
- **Warm Lavender**: `#B8A5D6` (neutral mood border)
- **Gentle Coral**: `#F4A69D` (low mood border)

### Neutrals
- **Warm Cream**: `#F7F5F3` (page background, not card)
- **White**: `#FFFFFF` (card background)
- **Gray-600**: `#4B5563` (metadata, action items)
- **Gray-700**: `#374151` (topic text)

### Milestone Accent
- **Amber-100**: `#FEF3C7` (badge background)
- **Amber-900**: `#92400E` (badge text)
- **Gold glow**: `rgba(251,191,36,0.4)` (badge shadow)

---

## Spacing & Padding

- **Card padding**: 16px all sides
- **Milestone badge**: -8px top offset (floats above card edge)
- **Metadata row margin-bottom**: 12px
- **Column gap**: 12px (space between left and right columns)
- **Line height**: 1.4-1.5 for readability
- **Badge padding**: 6px horizontal, 4px vertical

---

## Sample Content for Wireframes

Use these realistic therapy session examples:

### Session 1 (Milestone, Positive)
- Date: `Dec 10`
- Duration: `45m`
- Mood: 😊
- Topics: `Self-worth, Past relationships`
- Strategy: `Laddering technique`
- Actions: `Self-compassion practice`, `Behavioral experiment`
- Milestone: `⭐ BREAKTHROUGH`

### Session 2 (No Milestone, Neutral)
- Date: `Dec 3`
- Duration: `48m`
- Mood: 😐
- Topics: `Work stress, Perfectionism`
- Strategy: `Cognitive restructuring`
- Actions: `Challenge thoughts`, `Priority matrix`

### Session 3 (No Milestone, Low)
- Date: `Nov 5`
- Duration: `50m`
- Mood: 😔
- Topics: `Childhood trauma, Trust issues`
- Strategy: `Trauma-focused CBT`
- Actions: `Grounding techniques`, `Safety plan`

### Session 4 (Milestone, Neutral)
- Date: `Nov 26`
- Duration: `45m`
- Mood: 😐
- Topics: `Sleep issues, Anxiety`
- Strategy: `Sleep hygiene protocol`
- Actions: `Bedtime routine`, `Screen limits`
- Milestone: `⭐ COMPLETED 3-WEEK PLAN`

---

## Interaction States (Optional for Wireframes)

### Hover State
- **Transform**: Lift up 4px (`translateY(-4px)`)
- **Shadow**: Increase to `0 6px 16px rgba(0,0,0,0.12)`
- **Cursor**: Pointer
- **Optional**: Subtle accent bar reveal at top (gradient sweep)

### Click Behavior
- Opens fullscreen session detail view (not shown in card wireframe)

---

## Grid Context

These cards appear in a **4-column grid** with:
- **Gap between cards**: 16px
- **8 cards per page** (4 columns × 2 rows)
- **Pagination**: Dots below grid (● ○ for 2 pages)
- **Order**: Newest first (Dec 17 → Oct 15)

---

## Deliverable Request

**Please create 4-6 wireframe variations showing:**

1. **Card WITH milestone badge** (positive mood, teal border)
2. **Card WITHOUT milestone** (neutral mood, lavender border)
3. **Card WITHOUT milestone** (low mood, coral border)
4. **Grid view** showing 4 cards side-by-side (demonstrates spacing)
5. **Hover state variant** (optional - showing lifted shadow)
6. **Mobile/responsive variant** (optional - 2 cards per row for smaller screens)

**Design considerations to explore:**
- Should topics be comma-separated or line breaks?
- Should actions use bullets `•` or small pill badges?
- How condensed can we make the text while maintaining readability?
- Should there be subtle background tint variations between left/right columns?

---

## Typography (Font Families)

- **Headings**: Crimson Pro (serif) - NOT used in cards
- **Body text**: Inter (sans-serif) - Used for all card content
- **Data/Numbers**: Space Mono (monospace) - NOT used in cards

Use **Inter** exclusively for session cards.

---

## Reference Architecture Document

This prompt is based on:
- **Document**: `PAGE_LAYOUT_ARCHITECTURE.md` v3.0
- **Section**: Component Specifications → 6. Session Cards Grid (lines 622-790)
- **Key specs**: Two-column split (lines 653-706), Milestone badge (lines 681-688)

---

## Current Implementation Issues (What NOT to do)

The current implementation has these problems - **avoid these**:

❌ **Visible column headers** saying "SESSION TOPICS" and "SESSION STRATEGY" (too explicit)
❌ **Too much text** - showing full sentences instead of condensed keywords
❌ **Weak visual hierarchy** - everything same weight/color
❌ **Headers take up space** - reduces room for actual content
❌ **Not scannable** - user has to read too much to understand the card

**Goal**: Create implicit structure through typography and layout, not labels.

---

## Success Criteria

A successful wireframe will:
1. ✅ Show clear two-column split WITHOUT visible headers
2. ✅ Use typography weight/color to distinguish topics vs. strategy
3. ✅ Keep total content to ~20 words (condensed preview)
4. ✅ Make milestone badges feel special but not overwhelming
5. ✅ Demonstrate mood-based left border clearly
6. ✅ Feel calm and therapy-appropriate (not corporate)
7. ✅ Be scannable in 2-3 seconds per card

---

**End of Prompt**

Generate wireframes showing these session cards in various states (with/without milestones, different moods, grid context). Focus on clean visual hierarchy through typography rather than explicit labels.
