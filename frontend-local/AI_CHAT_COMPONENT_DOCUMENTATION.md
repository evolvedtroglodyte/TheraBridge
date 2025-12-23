# AI Chat Component - Complete Documentation

**Component Name:** AIChatCard
**Design System:** Hume.ai-inspired aesthetic
**Framework:** React + TypeScript + Tailwind CSS + Framer Motion
**Generated:** SuperDesign Build (December 2024)

---

## Table of Contents
1. [Overview](#overview)
2. [Component Architecture](#component-architecture)
3. [File Structure](#file-structure)
4. [Design System](#design-system)
5. [Features](#features)
6. [Implementation Details](#implementation-details)
7. [Props & API](#props--api)
8. [State Management](#state-management)
9. [Styling Specifications](#styling-specifications)
10. [Accessibility](#accessibility)
11. [Integration Guide](#integration-guide)
12. [Customization](#customization)

---

## Overview

The **AIChatCard** is a dual-mode AI therapy companion interface that seamlessly transitions between a compact dashboard widget and a fullscreen conversational experience. It implements Hume.ai's refined visual aesthetic while serving therapy-specific use cases.

### Key Characteristics
- **Compact State:** 280px height dashboard widget with prompt carousel
- **Fullscreen State:** Immersive chat interface with message history
- **Design Language:** Monospace typography, 0.555556px borders, pill-shaped buttons
- **Therapy Context:** AI/Therapist mode toggle, character limits, suggested prompts

---

## Component Architecture

### File Structure

```
ai_chat_extract/
├── src/
│   ├── AIChatCard.tsx          # Main component (429 lines)
│   ├── DobbyLogo.tsx            # Custom geometric SVG logo (81 lines)
│   ├── App.tsx                  # Demo wrapper
│   ├── main.tsx                 # Vite entry point
│   └── index.css                # Global styles
├── tailwind.config.ts           # Tailwind configuration
├── package.json                 # Dependencies
└── README.md                    # Basic usage guide
```

### Component Hierarchy

```
<AIChatCard>
  ├── Compact State (AnimatePresence)
  │   ├── DobbyLogo (64px)
  │   ├── Header (Title + Subtitle)
  │   ├── Prompt Carousel (2 visible, 6 total)
  │   ├── Separator Line
  │   ├── InputArea (compact variant)
  │   │   ├── Textarea (auto-resize)
  │   │   ├── ModeToggle (AI/Therapist)
  │   │   ├── CharacterCounter (124/500)
  │   │   └── SendButton (48px circular)
  │   └── ExpandButton (top-right)
  │
  └── Fullscreen State (AnimatePresence)
      ├── TopBar
      │   ├── DobbyLogo (40px)
      │   ├── Title + Status Indicator
      │   └── CloseButton
      ├── ChatArea
      │   ├── IntroSection (Meet Dobby card)
      │   ├── MessageList
      │   │   ├── MessageBubble (user)
      │   │   └── MessageBubble (assistant)
      │   └── ScrollAnchor
      └── BottomSection
          ├── SuggestedPrompts (horizontal scroll)
          └── InputArea (fullscreen variant)
```

---

## Design System

### Visual Language (Hume.ai Specifications)

#### Typography
**All text uses monospace font:**
- Font-family: `Space Mono, IBM Plex Mono, Roboto Mono, monospace`
- Font weights: 350 (light), 400 (regular), 450 (medium)
- Sizes: 11px (subtitle), 12px (labels), 13px (prompts), 14px (body), 16px (compact title), 18px (fullscreen title)

#### Borders
- **Standard thickness:** `0.555556px` (Hume.ai precision)
- **Color:** `rgba(0,0,0,0.1)` or `oklab(0.256147_0.0000116229_0.000005126_/_0.2)`
- **Style:** Solid, subtle, refined

#### Border Radius
- **Cards:** 24px (rounded corners)
- **Pills:** 9999px (fully rounded)
- **Message bubbles:** 20px with asymmetric corners

#### Shadows
- **White highlight:** `0px 1px 0px 0px #ffffff` (Hume.ai signature)
- **Soft shadow:** `0 2px 4px rgba(0,0,0,0.05)`
- **Button hover:** `0 4px 12px rgba(91,185,180,0.3)`

#### Color Palette

**Primary (Therapy Theme):**
```css
--teal-primary: #5AB9B4;
--teal-dark: #4A9D99;
--coral-therapist: #F4A69D;
```

**Neutrals:**
```css
--black: #232323;           /* Text, borders */
--gray-50: #F9FAFB;         /* Backgrounds */
--gray-100: #F3F4F6;        /* Hover states */
--gray-400: #9CA3AF;        /* Placeholders */
--gray-500: oklch(0.556_0_0); /* Character counter */
--gray-600: #4B5563;        /* Subtitle */
--gray-800: #1F2937;        /* Titles */
--white: #FFFFFF;
```

**Gradients:**
```css
/* Compact card background */
background: linear-gradient(135deg, #EBF8FF 0%, #F0F9FF 100%);

/* Send button */
background: linear-gradient(135deg, #5AB9B4 0%, #4A9D99 100%);

/* User message bubble */
background: linear-gradient(135deg, #5AB9B4 0%, #4A9D99 100%);
```

---

## Features

### 1. Dual-State Interface

**Compact Widget (280px height):**
- Dashboard-friendly footprint
- Quick access to chat without navigation
- Prominent Dobby logo (64px)
- Prompt carousel (2 visible suggestions)
- Single-line input with mode selector
- Click anywhere to expand

**Fullscreen Mode:**
- Full viewport overlay with backdrop blur
- Message history display
- Intro section explaining Dobby's capabilities
- Horizontal scrolling suggested prompts
- Multi-line textarea (auto-expands to 120px max)
- Smooth layout transition via Framer Motion

### 2. Mode Selector (AI vs. Therapist)

**AI Mode (default):**
- Icon: Robot 🤖
- Color: Teal gradient
- Behavior: Simulated AI responses
- Use case: Quick questions, session prep, mood tracking

**Therapist Mode:**
- Icon: Message bubble 💬
- Color: Coral/rose
- Behavior: Messages forwarded to human therapist
- Use case: Urgent concerns, therapy questions, scheduling

**Implementation:**
- Pill-shaped toggle buttons
- Active state: Filled background, white text
- Inactive state: White background, dark text
- Hover: 10% opacity tint of respective color

### 3. Suggested Prompts Carousel

**Compact State:**
- 2 prompts visible at a time
- Carousel navigation (left/right chevrons)
- Truncated text: "Why does my moo..."
- Click to populate input field

**Fullscreen State:**
- All 6 prompts visible (horizontal scroll)
- Full text display
- Labeled "Suggested Prompts"
- Click to populate input field

**Prompts:**
1. "Why does my mood drop after family visits?"
2. "Help me prep to discuss boundaries..."
3. "Explain the TIPP technique again"
4. "What should I bring up in next session?"
5. "I had a panic attack - what do I do?"
6. "Send message to my therapist"

### 4. Character Counter

- Format: `124/500` (current/max)
- Position: Bottom right of input area
- Font: 14px monospace, weight 350
- Color: Gray-400
- Updates live as user types
- Hard limit: 500 characters (input truncated)

### 5. DobbyLogo Component

**Custom Geometric Design:**
- Inspired by: Claude terminal logo + Harry Potter house-elf
- Structure: SVG with simple shapes
  - Head: Rounded rectangle (teal gradient)
  - Ears: Triangular paths (pointed, large)
  - Eyes: White circles with black pupils
  - Mouth: Curved path (subtle smile)

**Size Variants:**
- Compact card: 64px × 64px
- Fullscreen top bar: 40px × 40px
- Message avatar: 32px × 32px
- Intro section: 48px × 48px

**Color Variants:**
- Default: Teal gradient (#5AB9B4 → #4A9D99)
- White: Monochrome (for special contexts)

### 6. Message Bubbles

**User Messages:**
- Alignment: Right
- Background: Teal gradient
- Text: White, 14px monospace
- Border-radius: 20px (rounded-tr-sm for asymmetry)
- Avatar: Gray circle with user icon

**AI Messages:**
- Alignment: Left
- Background: White
- Text: Gray-800, 14px monospace
- Border: 0.555556px solid rgba(0,0,0,0.1)
- Border-radius: 20px (rounded-tl-sm)
- Shadow: White highlight
- Avatar: DobbyLogo (32px)

### 7. Auto-Resize Textarea

**Implementation:**
```tsx
useEffect(() => {
  const textarea = textareaRef.current;
  if (textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = `${Math.min(textarea.scrollHeight, 120)}px`;
  }
}, [inputValue]);
```

**Behavior:**
- Starts at min-height (24px compact, 48px fullscreen)
- Expands as user types
- Max-height: 120px (prevents overflow)
- Scrolls if exceeds max

### 8. Keyboard Navigation

- **Enter:** Send message (Shift+Enter for newline)
- **ESC:** Close fullscreen mode
- **Tab:** Navigate between interactive elements
- **Focus indicators:** Visible outlines on buttons/inputs

---

## Props & API

### AIChatCard Props

```tsx
interface AIChatCardProps {
  className?: string; // Additional Tailwind classes
}
```

**Usage:**
```tsx
<AIChatCard className="w-full max-w-md" />
```

### DobbyLogo Props

```tsx
interface DobbyLogoProps {
  size?: number;          // Width/height in px (default: 64)
  className?: string;     // Additional classes
  variant?: 'default' | 'white'; // Color scheme
}
```

**Usage:**
```tsx
<DobbyLogo size={48} variant="white" />
```

---

## State Management

### Component State

```tsx
const [isFullscreen, setIsFullscreen] = useState(false);
const [mode, setMode] = useState<ChatMode>('ai');
const [inputValue, setInputValue] = useState('');
const [messages, setMessages] = useState<ChatMessage[]>(INITIAL_MESSAGES);
const [promptIndex, setPromptIndex] = useState(0);
```

### State Variables

| Variable | Type | Purpose |
|----------|------|---------|
| `isFullscreen` | `boolean` | Toggles compact/fullscreen mode |
| `mode` | `'ai' \| 'therapist'` | Active messaging mode |
| `inputValue` | `string` | Current textarea content |
| `messages` | `ChatMessage[]` | Chat conversation history |
| `promptIndex` | `number` | Carousel position (0-4, step 2) |

### Types

```tsx
type ChatMode = 'ai' | 'therapist';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}
```

---

## Styling Specifications

### Tailwind Configuration

**Required custom config:**
```js
// tailwind.config.ts
export default {
  theme: {
    extend: {
      fontFamily: {
        mono: ['Space Mono', 'IBM Plex Mono', 'Roboto Mono', 'monospace'],
      },
      fontWeight: {
        350: '350',
        450: '450',
      },
      borderRadius: {
        pill: '9999px',
      }
    }
  }
}
```

### Key Tailwind Classes

**Hume.ai Borders:**
```tsx
className="border-[0.555556px] border-black/10"
```

**Monospace Font (all text):**
```tsx
className="font-mono text-[14px] font-[350]"
```

**Pill Buttons:**
```tsx
className="rounded-full px-3 py-1.5 border-[0.555556px]"
```

**White Highlight Shadow:**
```tsx
className="shadow-[0px_1px_0px_0px_#ffffff]"
```

**Teal Gradient:**
```tsx
className="bg-gradient-to-br from-[#5AB9B4] to-[#4A9D99]"
```

### CSS Variables (Optional Enhancement)

```css
:root {
  --hume-border: 0.555556px;
  --teal-primary: #5AB9B4;
  --teal-dark: #4A9D99;
  --coral: #F4A69D;
  --mono-font: 'Space Mono', monospace;
}
```

---

## Accessibility

### ARIA Labels

```tsx
// Send button
<button aria-label="Send message" ... />

// Mode toggle
<button aria-label="Switch to AI mode" ... />
<button aria-label="Switch to Therapist mode" ... />

// Character counter
<span aria-live="polite" aria-label={`${charCount} of ${MAX_CHARS} characters`}>
  {charCount}/{MAX_CHARS}
</span>
```

### Keyboard Support

- ✅ All interactive elements focusable
- ✅ Enter key sends message
- ✅ Shift+Enter adds newline
- ✅ ESC closes fullscreen
- ✅ Tab navigation follows logical order

### Screen Reader

- ✅ Semantic HTML structure
- ✅ Alt text on icons
- ✅ Live regions for dynamic content
- ✅ Role attributes where needed

### Focus Management

```tsx
// Trap focus in fullscreen mode
useEffect(() => {
  if (isFullscreen) {
    textareaRef.current?.focus();
  }
}, [isFullscreen]);
```

---

## Implementation Details

### Animation System (Framer Motion)

**Layout Transition:**
```tsx
<motion.div
  layoutId="chat-card"
  initial={{ opacity: 0, scale: 0.95 }}
  animate={{ opacity: 1, scale: 1 }}
  exit={{ opacity: 0, scale: 0.95 }}
  transition={{ duration: 0.3, ease: [0.23, 1, 0.32, 1] }}
>
```

**Key Features:**
- `layoutId`: Enables morphing between states
- Custom easing: `[0.23, 1, 0.32, 1]` (smooth, natural)
- AnimatePresence: Handles mount/unmount animations

**Message Fade-In:**
```tsx
<motion.div
  initial={{ opacity: 0, y: 10 }}
  animate={{ opacity: 1, y: 0 }}
>
```

### Message Handling

**Send Flow:**
```tsx
const handleSend = () => {
  if (!inputValue.trim()) return;

  // 1. Add user message
  const userMsg = { id, role: 'user', content, timestamp };
  setMessages(prev => [...prev, userMsg]);

  // 2. Clear input
  setInputValue('');

  // 3. Simulate AI response (1s delay)
  setTimeout(() => {
    const aiMsg = { id, role: 'assistant', content, timestamp };
    setMessages(prev => [...prev, aiMsg]);
  }, 1000);
};
```

**Auto-Scroll:**
```tsx
useEffect(() => {
  if (isFullscreen && messagesEndRef.current) {
    messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
  }
}, [messages, isFullscreen]);
```

### Input Validation

**Character Limit:**
```tsx
onChange={(e) => setInputValue(e.target.value.slice(0, MAX_CHARS))}
```

**Empty Check:**
```tsx
disabled={!inputValue.trim()}
```

### Responsive Behavior

**Fullscreen Modal:**
```tsx
className="fixed inset-0 z-50 bg-white/80 backdrop-blur-sm flex items-center justify-center p-4 sm:p-6"
```

**Compact Card:**
```tsx
className="w-full max-w-[480px] h-[280px]"
```

---

## Integration Guide

### 1. Install Dependencies

```bash
npm install framer-motion lucide-react clsx tailwind-merge
```

### 2. Copy Component Files

```
src/
├── components/
│   ├── AIChatCard.tsx
│   └── DobbyLogo.tsx
```

### 3. Update Tailwind Config

```js
// tailwind.config.ts
export default {
  theme: {
    extend: {
      fontFamily: {
        mono: ['Space Mono', 'IBM Plex Mono', 'monospace'],
      },
      fontWeight: {
        350: '350',
        450: '450',
      }
    }
  }
}
```

### 4. Import and Use

```tsx
import { AIChatCard } from './components/AIChatCard';

export default function Dashboard() {
  return (
    <div className="grid grid-cols-2 gap-6 p-8">
      {/* Top row - 50/50 split */}
      <NotesGoalsCard />
      <AIChatCard />

      {/* Other dashboard components */}
    </div>
  );
}
```

### 5. Connect to Backend (Production)

**Replace simulated responses:**

```tsx
const handleSend = async () => {
  // ... add user message ...

  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: inputValue,
        mode: mode,
        sessionId: currentSessionId,
      }),
    });

    const data = await response.json();

    const aiMsg = {
      id: data.messageId,
      role: 'assistant',
      content: data.response,
      timestamp: new Date(data.timestamp),
    };

    setMessages(prev => [...prev, aiMsg]);
  } catch (error) {
    console.error('Chat error:', error);
    // Show error toast
  }
};
```

---

## Customization

### Change Color Theme

**Teal → Purple:**
```tsx
// Replace all instances:
from-[#5AB9B4] to-[#4A9D99]  →  from-[#9F7AEA] to-[#805AD5]
```

### Adjust Character Limit

```tsx
const MAX_CHARS = 1000; // Increase limit
```

### Modify Prompts

```tsx
const SUGGESTED_PROMPTS = [
  { id: 1, text: "Your custom prompt here" },
  // Add more...
];
```

### Change Avatar Style

**Replace DobbyLogo with emoji:**
```tsx
// In message rendering
{msg.role === 'assistant' ? (
  <div className="w-8 h-8 rounded-full bg-teal flex items-center justify-center">
    <span className="text-xl">🤖</span>
  </div>
) : (
  // user avatar
)}
```

### Disable Mode Selector

```tsx
// Remove from InputArea component:
<ModeToggle mode={mode} setMode={setMode} />

// Lock to AI mode:
const [mode, setMode] = useState<ChatMode>('ai');
```

---

## File Contents

### AIChatCard.tsx (429 lines)

**Key Sections:**
- Lines 1-48: Imports, types, utilities
- Lines 50-68: Constants and initial data
- Lines 70-104: ModeToggle sub-component
- Lines 106-428: Main AIChatCard component
  - Lines 109-131: State and effects
  - Lines 133-171: Event handlers
  - Lines 174-215: InputArea reusable component
  - Lines 218-293: Compact state JSX
  - Lines 296-425: Fullscreen state JSX

**Notable Patterns:**
- Component composition (ModeToggle, InputArea)
- Controlled inputs with validation
- Conditional rendering based on state
- Framer Motion layout animations

### DobbyLogo.tsx (81 lines)

**Structure:**
- Lines 1-17: Component definition and props
- Lines 19-27: Color variant logic
- Lines 29-80: SVG structure
  - Lines 38-50: Ears (triangular paths)
  - Lines 52-61: Head (rounded rectangle)
  - Lines 63-69: Eyes and pupils (circles)
  - Lines 71-77: Mouth (curved path)

**Design Notes:**
- Uses simple SVG primitives
- Color variants for different contexts
- Scalable via size prop
- Geometric/minimalist aesthetic

---

## Dependencies

```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "framer-motion": "^11.0.0",
    "lucide-react": "^0.400.0",
    "clsx": "^2.1.0",
    "tailwind-merge": "^2.2.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "typescript": "^5.0.0",
    "vite": "^5.0.0",
    "tailwindcss": "^3.4.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0"
  }
}
```

---

## Performance Considerations

### Optimization Opportunities

1. **Memoize sub-components:**
```tsx
const ModeToggle = React.memo(({ mode, setMode }) => { ... });
```

2. **Virtualize long message lists:**
```tsx
import { useVirtualizer } from '@tanstack/react-virtual';
```

3. **Debounce character counter:**
```tsx
import { useDebouncedValue } from '@/hooks';
const debouncedCount = useDebouncedValue(inputValue.length, 300);
```

4. **Lazy load fullscreen:**
```tsx
const FullscreenChat = React.lazy(() => import('./FullscreenChat'));
```

---

## Testing Recommendations

### Unit Tests (Vitest)

```tsx
describe('AIChatCard', () => {
  it('renders compact state by default', () => {
    render(<AIChatCard />);
    expect(screen.getByText('Chat with Dobby')).toBeInTheDocument();
  });

  it('enforces 500 character limit', () => {
    render(<AIChatCard />);
    const textarea = screen.getByPlaceholderText('Type your message...');
    fireEvent.change(textarea, { target: { value: 'a'.repeat(600) } });
    expect(textarea.value).toHaveLength(500);
  });

  it('toggles between AI and Therapist modes', () => {
    render(<AIChatCard />);
    const therapistBtn = screen.getByText('Therapist');
    fireEvent.click(therapistBtn);
    // Assert mode state change
  });
});
```

### Integration Tests

- Test fullscreen expansion animation
- Verify message sending flow
- Check prompt carousel navigation
- Validate keyboard shortcuts

### Accessibility Tests

```tsx
import { axe, toHaveNoViolations } from 'jest-axe';

it('has no accessibility violations', async () => {
  const { container } = render(<AIChatCard />);
  const results = await axe(container);
  expect(results).toHaveNoViolations();
});
```

---

## Troubleshooting

### Font weights not working

**Problem:** Custom font weights (350, 450) not applying.

**Solution:** Ensure Tailwind config includes custom weights and @font-face declarations load variable fonts:

```css
@font-face {
  font-family: 'Space Mono';
  src: url('/fonts/SpaceMono-VariableFont.woff2') format('woff2-variations');
  font-weight: 100 900;
}
```

### Border thickness appears inconsistent

**Problem:** 0.555556px borders look different across browsers.

**Solution:** This is expected due to sub-pixel rendering. Consider rounding to 0.5px or 1px for consistency, or accept variation as part of Hume.ai's aesthetic.

### Framer Motion animations janky

**Problem:** Layout transitions stuttering.

**Solution:**
1. Ensure `will-change` CSS applied:
```tsx
className="will-change-transform"
```

2. Use GPU acceleration:
```tsx
style={{ transform: 'translateZ(0)' }}
```

### Character counter not updating

**Problem:** Counter shows 0/500 despite input.

**Solution:** Verify state binding:
```tsx
<span>{inputValue.length}/{MAX_CHARS}</span>
```

---

## Version History

**v1.0 (December 2024)**
- Initial SuperDesign build
- Hume.ai aesthetic implementation
- Dual-state interface
- Custom DobbyLogo component
- Mode selector (AI/Therapist)
- Character counter
- Prompt carousel
- Auto-resize textarea
- Framer Motion animations

---

## Credits

- **Design Reference:** Hume.ai text-to-speech component
- **Logo Inspiration:** Claude terminal logo + Harry Potter Dobby character
- **Framework:** React + TypeScript + Tailwind CSS
- **Animations:** Framer Motion
- **Icons:** Lucide React
- **Generated:** SuperDesign AI Component Builder

---

## License

MIT License - Free to use in TherapyBridge project.

---

**End of Documentation**

For additional support or customization requests, refer to the inline code comments in `AIChatCard.tsx` and `DobbyLogo.tsx`.
