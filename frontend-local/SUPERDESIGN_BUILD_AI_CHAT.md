# SuperDesign Build Prompt: TherapyBridge AI Chat (Dobby)

## Component Type
**Production React Component Build** - AI therapy companion chatbot with Hume.ai-inspired aesthetic

## Reference Implementations
- **Current file:** `/tmp/src/components/AIChatCard.tsx`
- **Design reference:** Hume.ai text-to-speech component (`/tmp/hume_extract/components/Component_2_3*.jsx`)
- **Framework:** React + TypeScript + Tailwind CSS + Framer Motion

---

## Design Brief

Redesign AI therapy chatbot to match Hume.ai's elegant, minimal aesthetic while preserving all existing TherapyBridge functionality. Focus on:
1. **Visual refinement** - Hume.ai's subtle borders, pill shapes, monospace typography
2. **Custom branding** - Geometric Dobby logo inspired by Claude terminal + Harry Potter house-elf
3. **Therapy context** - Mode selector for AI vs. Therapist messaging
4. **Production polish** - Character counter, proper spacing, refined interactions

---

## Component States

### 1. Compact Card (Dashboard Widget)
- **Dimensions:** 280px height, responsive width (50% of dashboard top row)
- **Background:** Blue gradient `from-[#EBF8FF] to-[#F0F9FF]` (therapy feel)
- **Purpose:** Quick access to AI chat without leaving dashboard

### 2. Fullscreen Mode
- **Trigger:** Click anywhere on compact card or send button
- **Background:** White (minimal, Hume.ai style)
- **Purpose:** Full conversation interface with chat history

---

## Core Design Philosophy: Hume.ai Aesthetic

**Preserve these Hume.ai patterns exactly:**

### Visual Language
- **Borders:** 0.555556px (very subtle, refined)
- **Border-radius:** 24px (cards), `border-radius: 9999px` (pills - fully rounded)
- **Shadows:** Minimal white highlight `rgb(255,255,255) 0px 1px 0px 0px`
- **Backgrounds:** White for interactive elements, transparent or light tints for containers
- **Color space:** Use `oklab()` color functions for precise colors

### Typography
- **Font family:** Monospace (`font-family: fontMono, monospace, system-ui, sans-serif`) for **ALL TEXT**
- **Font weights:** 350-450 range (Hume.ai uses 350, 400, 450)
- **Uppercase labels:** 12px, uppercase, tracking-tight for metadata/modes
- **Hierarchy through weight:** Not size - use 350 vs 450, not 12px vs 16px

### Button Style
- **Pills:** Fully rounded (`border-radius: 9999px`)
- **Borders:** 0.555556px solid `oklab(0.256147_0.0000116229_0.000005126_/_0.2)`
- **Padding:** Generous (e.g., `px-2.5 py-1.5` for small, `pl-2 pr-3 py-2.5` for larger)
- **Icons + Text:** Icon always precedes text, 8-12px gap
- **Hover:** Subtle background tint, no heavy shadows

### Interactive Elements
- **Send button:** Circular (56px), black `#232323`, white icon, centered
- **Tags/Modes:** Pill buttons with icons, uppercase monospace labels
- **Character counter:** Bottom right, monospace, gray, format `50/500`

---

## Custom Dobby Logo Design

### Logo Concept
**Geometric house-elf character inspired by:**
- **Harry Potter's Dobby** - Large pointed ears, big innocent eyes
- **Claude terminal logo** - Minimalist geometric style, flat design, rounded corners

### Logo Specifications

**Character Design:**
- **Shape composition:** 2-3 simple geometric shapes
  - Large circular head (base shape)
  - Two triangular pointed ears (signature Dobby feature)
  - Two large circular eyes (expressive, innocent)
  - Optional: Small curved line for mouth (friendly smile)
- **Style:** Flat geometric, no gradients within logo (solid fills)
- **Corners:** Rounded (4-8px border-radius on shapes)
- **Proportions:** Ears ~60% of head height, eyes ~25% of head width

**Color Palette:**
- **Primary:** Teal gradient `#5AB9B4 → #4A9D99` (matches therapy theme)
- **Eyes:** White circles with teal pupils (for contrast)
- **Outline:** Optional 1px teal stroke around shapes (for definition)

**Size Variations:**
- **Compact card:** 64px × 64px (larger, prominent)
- **Fullscreen top bar:** 40px × 40px (medium)
- **Message avatar:** 32px × 32px (small)

**No background container:**
- Logo floats freely (like Claude terminal logo)
- No circle, no square background
- Just the character shapes on transparent background

**Wordmark (optional, below logo in compact card):**
- Text: "Dobby" in monospace font
- Size: 12px
- Weight: 450 (medium)
- Color: Gray-600
- Spacing: 4px below logo

### Logo Placement

**Compact Card:**
- Position: Top center
- Size: 64px × 64px
- Margin: 12px below top edge, 8px above title

**Fullscreen Top Bar:**
- Position: Left side, next to "Chat with Dobby" title
- Size: 40px × 40px
- Margin: 10px from left edge, centered vertically

**Message Bubbles:**
- Position: Left of AI messages (as avatar)
- Size: 32px × 32px
- Alternative to robot emoji 🤖

---

## Compact Card Layout

```
┌─────────────────────────────────────────────┐
│                                             │
│         [Dobby Logo - 64px geometric]       │ ← Custom logo
│         Dobby (optional wordmark)           │
│                                             │
│         Chat with Dobby                     │ ← Title (monospace)
│    Prepare for sessions, ask questions,    │ ← Subtitle (monospace)
│        or message your therapist            │
│                                             │
│  ┌───────────────────────────────────────┐ │
│  │  SUGGESTED PROMPTS                    │ │
│  │  ┌─────────────┬─────────────┐       │ │
│  │  │ "Why does  │ │ "Help me   │ [< >]│ │ ← Hume.ai pill style
│  │  │  my mood..." │ │  prep..."  │      │ │
│  │  └─────────────┴─────────────┘       │ │
│  │  ● ○ ○                                │ │
│  └───────────────────────────────────────┘ │
│                                             │
│  ──────────────────────────────────────    │ ← Separator (0.555556px)
│                                             │
│  ┌───────────────────────────────────────┐ │
│  │ Type your message...                  │ │ ← White input (Hume.ai)
│  │                                       │ │
│  │ [🤖 AI] [💬 THERAPIST]     124/500   │ │ ← Mode + counter
│  │                            [Send]     │ │ ← Teal gradient circle
│  └───────────────────────────────────────┘ │
│                                             │
└─────────────────────────────────────────────┘
```

### Compact Card Specifications

**Overall Card:**
- Background: Blue gradient `bg-gradient-to-br from-[#EBF8FF] to-[#F0F9FF]`
- Border-radius: 24px (Hume.ai style)
- Padding: 20px
- Shadow: `0 4px 12px rgba(0,0,0,0.1)` (medium)
- Height: 280px (fixed)

**Dobby Logo:**
- Size: 64px × 64px
- Position: Centered horizontally
- Margin-bottom: 8px (to title)
- Custom geometric design (specs above)

**Title & Subtitle:**
- Font: Monospace (all text uses monospace)
- Title: "Chat with Dobby" - 16px, weight 450, gray-800
- Subtitle: 11px, weight 350, gray-600
- Both centered
- Line-height: 1.4

**Suggested Prompts Section:**
- Background: Transparent
- Padding: 12px vertical

**Prompt Carousel:**
- **Button style (Hume.ai):**
  - Background: White
  - Border: 0.555556px solid `oklab(0.256147_0.0000116229_0.000005126_/_0.2)`
  - Border-radius: 9999px (fully rounded pill)
  - Padding: 10px 16px
  - Font: 13px, monospace, weight 400
  - Color: `#232323`
  - Hover: Background `rgba(91,185,180,0.05)` (teal tint)
  - Shadow: None (flat)

- **Layout:**
  - 2 prompts visible at a time
  - Gap: 8px between prompts
  - Carousel arrows: Chevron icons, 8px, subtle

- **Pagination dots:**
  - Size: 6px circles (slightly larger than session cards)
  - Active: Teal `#5AB9B4`
  - Inactive: Gray-300
  - Gap: 6px between dots

**Separator Line:**
- Width: 100%
- Height: 0.555556px (Hume.ai precision)
- Color: `oklab(0_0_0_/_0.1)` (10% black in oklab)
- Margin: 12px vertical

**Input Area (Hume.ai style):**
- **Container:**
  - Background: White
  - Border: 0.555556px solid `oklab(0.256147_0.0000116229_0.000005126_/_0.2)`
  - Border-radius: 24px
  - Padding: 16px
  - Shadow: `rgb(255,255,255) 0px 1px 0px 0px` (white highlight)

- **Textarea:**
  - Background: Transparent
  - Font: Monospace, 14px, weight 350
  - Placeholder: "Type your message..." gray-400
  - Border: None
  - Outline: None
  - Line-height: 1.5
  - Min-height: 24px
  - Max-height: 72px (3 lines)
  - Auto-resize as user types

- **Focus state:**
  - Border-color: Teal `#5AB9B4`
  - Ring: 2px `rgba(91,185,180,0.2)`
  - Transition: 150ms ease

**Mode Selector (below textarea):**
- **Layout:** Two pill buttons side-by-side
- **Button style (Hume.ai inspired):**
  - Border-radius: 9999px (fully rounded)
  - Border: 0.555556px solid `oklab(0.256147_0.0000116229_0.000005126_/_0.2)`
  - Padding: 6px 12px
  - Font: 12px, monospace, uppercase, weight 450
  - Gap: 8px between icon and text
  - Height: 32px

- **[AI] Mode:**
  - Icon: 🤖 Robot (10px emoji or SVG)
  - Text: "AI" (uppercase)
  - Active state: Background teal `#5AB9B4`, text white, border teal
  - Inactive state: Background white, text `#232323`, border gray

- **[THERAPIST] Mode:**
  - Icon: 💬 Speech bubble (10px emoji or SVG)
  - Text: "THERAPIST" (uppercase)
  - Active state: Background coral `#F4A69D`, text white, border coral
  - Inactive state: Background white, text `#232323`, border gray

- **Interaction:**
  - Toggle between modes (radio button behavior)
  - Only one active at a time
  - Smooth transition: 150ms ease
  - Hover: Subtle background tint of respective color

**Character Counter (Hume.ai exact style):**
- Position: Bottom right of input container
- Font: 14px, monospace, weight 350
- Color: `oklch(0.556_0_0)` (gray-500 in oklab)
- Format: `124/500` (current/max)
- Updates live as user types
- Margin: 8px from right edge, 4px from bottom

**Send Button:**
- **Style (adapted from Hume.ai play button):**
  - Shape: Circular
  - Size: 48px diameter (compact card)
  - Background: Teal gradient `bg-gradient-to-br from-[#5AB9B4] to-[#4A9D99]`
  - Border: 0.555556px solid teal
  - Icon: Arrow up ↑ (white, 20px)
  - Position: Right side, aligned with textarea

- **Hover state:**
  - Transform: `scale(1.05)`
  - Shadow: `0 4px 12px rgba(91,185,180,0.3)`
  - Transition: 150ms ease

- **Disabled state (no input):**
  - Opacity: 0.4
  - Cursor: not-allowed
  - No hover effects

---

## Fullscreen Mode Layout

```
┌─────────────────────────────────────────────────┐
│  [Dobby] ← Back   Chat with Dobby        [×]   │ ← Top bar (white)
├─────────────────────────────────────────────────┤
│                                                 │
│  [Scroll to top to see description]            │ ← Hidden initially
│                                                 │
│  Meet Dobby - Your Therapy Companion           │
│  What I can help with:                         │
│  • Prepare for upcoming sessions               │
│  • Answer mental health questions              │
│  ...                                            │
│                                                 │
│  ═══════════════════════════════════════════   │
│                                                 │
│  [Chat conversation area - white background]   │
│                                                 │
│  👤 How is my progress going?                   │ ← User (right)
│                                                 │
│  [Dobby] Based on your 10 sessions, you've...  │ ← AI (left)
│                                                 │
│  [Messages continue...]                         │
│                                                 │
│  ═══════════════════════════════════════════   │
│                                                 │
│  💡 Suggested prompts:                          │
│  ┌───────────────┬───────────────┐             │
│  │ "Help me prep │ │ "What patterns│  [< >]    │ ← Hume.ai pills
│  └───────────────┴───────────────┘             │
│  ● ○ ○                                          │
│                                                 │
│  ─────────────────────────────────────────      │
│  ┌───────────────────────────────────────────┐ │
│  │ Type your message...              [Send]  │ │ ← Hume.ai input style
│  │                                           │ │
│  │ [🤖 AI] [💬 THERAPIST]      124/500       │ │
│  └───────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

### Fullscreen Specifications

**Top Bar:**
- Height: 60px
- Background: White
- Border-bottom: 0.555556px solid `oklab(0_0_0_/_0.1)`
- Padding: 0 24px

**Top Bar Content:**
- **Left:**
  - Dobby logo: 40px × 40px (geometric)
  - Back button: Arrow + "Back" text (monospace, 14px, teal)
  - Gap: 12px between logo and back button

- **Center:**
  - Title: "Chat with Dobby" (monospace, 18px, weight 450)

- **Right:**
  - Close button: X icon in circle (32px container)
  - Hover: Background gray-100
  - Transition: 150ms ease

**Description Section (scroll reveal):**
- Initially scrolled past (not visible on load)
- User scrolls up to reveal
- Background: `#F9FAFB` (gray-50)
- Padding: 24px
- Border-bottom: 0.555556px solid gray-200

**Description Content:**
```
Meet Dobby - Your Therapy Companion

What I can help with:
• Prepare for upcoming sessions
• Answer mental health questions
• Save topics to discuss later
• Message your therapist directly
• Reference your session data
```
- Typography: Monospace, 14px, weight 350, line-height 1.6
- Heading: Weight 450
- Bullets: Simple • character

**Chat Messages Area:**
- Background: White (Hume.ai minimal style)
- Padding: 24px
- Scrollable: Full height between top bar and input
- Gap: 16px between messages

**Message Bubbles:**

**User Messages (right-aligned):**
- Background: Teal gradient `from-[#5AB9B4] to-[#4A9D99]`
- Text color: White
- Border-radius: 20px (asymmetric - more rounded on left)
- Max-width: 70%
- Padding: 12px 16px
- Font: Monospace, 14px, weight 350
- Line-height: 1.5
- Shadow: `0 2px 4px rgba(91,185,180,0.2)`
- Avatar: 32px circle, gray-200, user icon 👤 (right side)

**AI Messages (left-aligned):**
- Background: White
- Text color: Gray-800
- Border: 0.555556px solid `oklab(0.256147_0.0000116229_0.000005126_/_0.2)`
- Border-radius: 20px (asymmetric - more rounded on right)
- Max-width: 70%
- Padding: 12px 16px
- Font: Monospace, 14px, weight 350
- Line-height: 1.5
- Shadow: `rgb(255,255,255) 0px 1px 0px 0px` (white highlight)
- Avatar: 32px geometric Dobby logo (left side)

**Prompt Suggestions Area (bottom, above input):**
- Background: `#F9FAFB` (gray-50)
- Border-top: 0.555556px solid gray-200
- Padding: 16px
- Same carousel as compact card (Hume.ai pill buttons)
- Label: "💡 Suggested prompts:" (monospace, 12px, gray-600)

**Input Bar (Hume.ai style, fullscreen variant):**
- Max-width: 800px, centered
- Background: White
- Border: 0.555556px solid gray-300
- Border-radius: 24px
- Padding: 20px
- Shadow: `rgb(255,255,255) 0px 1px 0px 0px`

**Focus state:**
- Border-color: Teal
- Ring: 2px teal/20
- Transition: 150ms ease

**Textarea (fullscreen):**
- Font: Monospace, 16px, weight 350
- Placeholder: "Type your message..."
- Min-height: 48px
- Max-height: 120px (auto-expand)
- Line-height: 1.5

**Mode Selector + Counter (fullscreen):**
- Same as compact card
- Positioned below textarea
- Flex layout: justify-between
- Left: Mode buttons
- Right: Character counter

**Send Button (fullscreen):**
- Size: 56px diameter (larger)
- Same style as compact card
- Teal gradient background
- Position: Right side of textarea

---

## Typography System (Monospace for All)

**Font Family:**
```css
font-family: 'Space Mono', 'IBM Plex Mono', 'Roboto Mono', monospace, system-ui, sans-serif;
```

**Type Scale (all monospace):**
| Element | Size | Weight | Color |
|---------|------|--------|-------|
| Fullscreen title | 18px | 450 | Gray-800 |
| Compact title | 16px | 450 | Gray-800 |
| Message text | 14px | 350 | White/Gray-800 |
| Prompt buttons | 13px | 400 | #232323 |
| Mode labels | 12px | 450 | #232323/White |
| Character counter | 14px | 350 | Gray-500 |
| Subtitle | 11px | 350 | Gray-600 |

**Uppercase Usage:**
- Mode labels: "AI", "THERAPIST"
- Tag buttons (if added later)
- Character count label (optional): "CHARACTERS"

**Letter-spacing:**
- Uppercase labels: `-0.42px` (tracking-tight)
- Regular text: Normal

---

## Color Palette

**Primary (Therapy Theme):**
- Soft Teal: `#5AB9B4` (AI mode, buttons, accents)
- Teal Dark: `#4A9D99` (gradient endpoint)
- Gentle Coral: `#F4A69D` (Therapist mode)

**Neutrals (Hume.ai style):**
- Black: `#232323` (text, borders in Hume.ai)
- White: `#FFFFFF` (backgrounds, pill buttons)
- Gray-50: `#F9FAFB` (section backgrounds)
- Gray-200: `#E5E7EB` (borders, separators)
- Gray-300: `#D1D5DB` (inactive elements)
- Gray-400: `#9CA3AF` (placeholders)
- Gray-500: `oklch(0.556_0_0)` (character counter)
- Gray-600: `#4B5563` (subtitle, labels)
- Gray-800: `#1F2937` (message text, titles)

**Gradients:**
- Card background: `linear-gradient(135deg, #EBF8FF 0%, #F0F9FF 100%)`
- Teal button: `linear-gradient(135deg, #5AB9B4 0%, #4A9D99 100%)`

**Oklab Colors (Hume.ai precision):**
- Border color: `oklab(0.256147_0.0000116229_0.000005126_/_0.2)`
- Separator: `oklab(0_0_0_/_0.1)`
- Character counter: `oklch(0.556_0_0)`

---

## Spacing & Measurements

**Compact Card:**
- Card padding: 20px
- Logo size: 64px × 64px
- Logo to title: 8px
- Title to subtitle: 4px
- Subtitle to prompts: 12px
- Prompts to separator: 12px
- Separator to input: 12px
- Input padding: 16px
- Mode button height: 32px
- Send button: 48px diameter

**Fullscreen:**
- Top bar height: 60px
- Top bar padding: 24px horizontal
- Message area padding: 24px
- Message gap: 16px vertical
- Bubble padding: 12px 16px
- Avatar size: 32px (Dobby logo)
- Avatar to bubble gap: 12px
- Input max-width: 800px
- Input padding: 20px
- Send button: 56px diameter

**Border Widths:**
- Standard: 0.555556px (Hume.ai precision)
- Focus ring: 2px

**Border Radius:**
- Cards: 24px
- Pills: 9999px (fully rounded)
- Message bubbles: 20px
- Input container: 24px
- Send button: 50% (circular)

---

## Interaction States

### Hover States (Hume.ai subtle)
- **Prompt buttons:** Background tint `rgba(91,185,180,0.05)`, no shadow
- **Mode buttons:** Background tint of respective color (10% opacity)
- **Send button:** Scale 105%, shadow `0 4px 12px rgba(91,185,180,0.3)`
- **Back/Close:** Background gray-100

### Focus States
- **Input textarea:** Border teal, ring 2px teal/20
- **All buttons:** Outline for keyboard navigation (2px teal)

### Active States
- **Mode selector:** Filled background (teal or coral), white text, colored border
- **Prompt clicked:** Brief highlight, text inserted into input

### Disabled States
- **Send button (empty input):** Opacity 40%, no hover, cursor not-allowed

---

## Animation Specifications

**Hume.ai-style animations (subtle, fast):**
```css
transition: all 150ms ease;  /* Most interactions */
transition: transform 150ms ease, box-shadow 150ms ease;  /* Hover lifts */
transition: background-color 150ms ease;  /* Mode toggles */
```

**Message appear animation:**
```css
/* Fade in + slide up */
@keyframes messageAppear {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
animation: messageAppear 200ms ease-out;
```

**Fullscreen expansion (existing Framer Motion):**
- Spring pop from compact card position
- 400ms duration
- Cubic-bezier easing

---

## Sample Content

### Suggested Prompts (6 total)
1. "Why does my mood drop after family visits?"
2. "Help me prep to discuss boundaries..."
3. "Explain the TIPP technique again"
4. "What should I bring up in next session?"
5. "I had a panic attack - what do I do?"
6. "Send message to my therapist"

### Chat Conversation Example

**User:** "How is my progress going?"

**Dobby:** "Based on your 10 sessions, you've made remarkable progress! Your depression score improved 67% (from 18 to 6), and you've mastered 3 core coping strategies. Your therapist notes significant breakthroughs in boundary-setting and self-compassion. Would you like me to show you specific metrics or prepare talking points for your next session?"

**User:** "What patterns do you see in my sessions?"

**Dobby:** "I've identified a key pattern: work-related stress and perfectionism often trigger family conflict and people-pleasing behaviors. This pattern appeared in Sessions 3, 5, 8, and 10. Your therapist has been helping you address this through assertiveness training and cognitive restructuring. Would you like to explore this pattern further?"

---

## Accessibility Requirements

**Keyboard Navigation:**
- All interactive elements tab-accessible
- Tab order: Logo → Title → Prompts → Input → Mode selector → Send
- Enter in input: Send message
- ESC in fullscreen: Close to compact card

**Screen Reader:**
- ARIA labels:
  - Input: "Message Dobby"
  - Mode buttons: "Select AI mode" / "Select Therapist mode"
  - Send: "Send message"
  - Character counter: "124 of 500 characters"
- Live region for new messages (polite)
- Mode change announcements

**Focus Indicators:**
- Visible outlines on all focusable elements
- 2px teal outline, 2px offset
- Never `outline: none` without alternative

**Color Contrast:**
- WCAG AA minimum (4.5:1 for text)
- White text on teal gradient: Verified
- Gray-800 text on white: Verified
- Mode labels when inactive: Verified

---

## Technical Implementation

### Component Structure

```tsx
interface AIChatCardProps {
  // Component is self-contained, no props needed
}

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

type ChatMode = 'ai' | 'therapist';
```

### State Management

```tsx
const [isFullscreen, setIsFullscreen] = useState(false);
const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);
const [inputValue, setInputValue] = useState('');
const [charCount, setCharCount] = useState(0);
const [mode, setMode] = useState<ChatMode>('ai');
const [promptPage, setPromptPage] = useState(0);
```

### Character Counter Logic

```tsx
const MAX_CHARS = 500;

const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
  const text = e.target.value;
  if (text.length <= MAX_CHARS) {
    setInputValue(text);
    setCharCount(text.length);
  }
};

// Display format
const counterText = `${charCount}/${MAX_CHARS}`;
```

### Mode Selector Logic

```tsx
const handleModeChange = (newMode: ChatMode) => {
  setMode(newMode);
  // Optional: Clear input or show confirmation
};

// Render
<button
  onClick={() => handleModeChange('ai')}
  className={mode === 'ai' ? 'active' : 'inactive'}
>
  🤖 AI
</button>
```

### Textarea Auto-Resize

```tsx
const textareaRef = useRef<HTMLTextAreaElement>(null);

const handleInput = () => {
  const textarea = textareaRef.current;
  if (textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = `${Math.min(textarea.scrollHeight, 120)}px`;
  }
};
```

---

## Hume.ai CSS Pattern Reference

**Exact border style:**
```tsx
className="border-[0.555556px] border-[oklab(0.256147_0.0000116229_0.000005126_/_0.2)]"
```

**Full pill border-radius:**
```tsx
className="rounded-[9999px]"
// Or in Tailwind config:
// borderRadius: { pill: '9999px' }
```

**White highlight shadow:**
```tsx
className="shadow-[rgb(255,255,255)_0px_1px_0px_0px]"
```

**Monospace font:**
```tsx
className="font-[fontMono,monospace,system-ui,sans-serif]"
// Or in Tailwind config:
// fontFamily: { mono: ['Space Mono', 'IBM Plex Mono', 'monospace'] }
```

**Font weight 350:**
```tsx
className="font-[350]"
// Tailwind custom: font-extralight is 200, font-light is 300
// Need custom: { 350: '350', 450: '450' }
```

**Oklab color:**
```tsx
className="text-[oklch(0.556_0_0)]"
// Gray-500 equivalent in oklab color space
```

---

## Build Output Requirements

**Generate production-ready React + TypeScript component:**
- Two states: Compact card + Fullscreen mode
- Hume.ai visual aesthetic throughout
- Monospace typography for all text
- Custom Dobby geometric logo (SVG component)
- Mode selector (AI vs Therapist)
- Character counter (live updating)
- Proper accessibility (ARIA, focus, keyboard)
- Framer Motion animations
- Tailwind CSS (custom config for Hume.ai values)

**Files to output:**
1. `AIChatCard.tsx` - Main component
2. `DobbyLogo.tsx` - Custom geometric logo SVG component
3. `tailwind.config.ts` - Custom values (font weights, border widths)
4. Type definitions inline or imported
5. Usage example with mock data

**Custom Tailwind Config needed:**
```js
module.exports = {
  theme: {
    extend: {
      fontFamily: {
        mono: ['Space Mono', 'IBM Plex Mono', 'Roboto Mono', 'monospace'],
      },
      fontWeight: {
        350: '350',
        450: '450',
      },
      borderWidth: {
        0.5: '0.555556px',
      },
      borderRadius: {
        pill: '9999px',
      },
    },
  },
};
```

---

## Success Criteria

A successful implementation will:
1. ✅ Match Hume.ai's visual aesthetic (borders, pills, shadows, monospace)
2. ✅ Use monospace font for ALL text elements
3. ✅ Include custom geometric Dobby logo (inspired by Claude + Harry Potter)
4. ✅ Show character counter (live updating, 124/500 format)
5. ✅ Implement mode selector (AI vs Therapist toggle)
6. ✅ Preserve all existing functionality (prompts carousel, fullscreen, messages)
7. ✅ Use therapy-appropriate color palette (teal, coral, blue gradient)
8. ✅ Have proper accessibility (keyboard nav, ARIA, focus states)
9. ✅ Feel polished and professional (Hume.ai level quality)
10. ✅ Be fully responsive and production-ready

---

**End of Build Prompt**

Generate a production-ready AI chat component that matches Hume.ai's elegant, minimal aesthetic while maintaining TherapyBridge's therapy-focused functionality and branding.
