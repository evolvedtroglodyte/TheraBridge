# Superdesign Wireframe Prompt: TherapyBridge AI Chat (Dobby)

## Context
Design wireframes for an AI therapy companion chatbot interface inspired by Hume.ai's elegant design. The component needs both a **compact card** (dashboard widget) and a **fullscreen chat** mode. The chatbot helps patients prepare for therapy sessions, ask questions, and message their therapist.

---

## Design Reference: Hume.ai Component
The Hume.ai text-to-speech interface has excellent design patterns to adapt:
- ✅ Clean, minimal aesthetic with rounded corners
- ✅ Pill-shaped buttons with icons
- ✅ Subtle borders (0.5px) and white backgrounds
- ✅ Character counter for input tracking
- ✅ Tag/mode selector system
- ✅ Large textarea with placeholder
- ✅ Circular action button (play → send)

**Adapt these patterns for therapy chatbot context.**

---

## Component States

### 1. Compact Card (Dashboard Widget)
**Dimensions:** ~280px height, responsive width (50% of top row)
**Purpose:** Quick access to AI chat without leaving dashboard

### 2. Fullscreen Mode
**Trigger:** Click anywhere on compact card or click send button
**Purpose:** Full conversation interface with chat history

---

## Compact Card Layout

```
┌─────────────────────────────────────────────┐
│                                             │
│         [Dobby Avatar - 48px circle]        │ ← Centered logo/icon
│                                             │
│         Chat with Dobby                     │ ← Title (16px, semibold)
│    Prepare for sessions, ask questions,    │ ← Subtitle (11px, gray)
│        or message your therapist            │
│                                             │
│  ┌───────────────────────────────────────┐ │
│  │                                       │ │
│  │  SUGGESTED PROMPTS (2 visible)        │ │ ← Carousel section
│  │  ┌─────────────┬─────────────┐       │ │
│  │  │ "Why does  │ │ "Help me   │ [< >]│ │
│  │  │  my mood..." │ │  prep..."  │      │ │
│  │  └─────────────┴─────────────┘       │ │
│  │  ● ○ ○  (pagination dots)            │ │
│  │                                       │ │
│  └───────────────────────────────────────┘ │
│                                             │
│  ──────────────────────────────────────    │ ← Separator line
│                                             │
│  ┌───────────────────────────────────────┐ │
│  │ Type your message...          [Send]  │ │ ← Input area (Hume.ai style)
│  │                                       │ │
│  │ [AI] [Therapist]        50/500       │ │ ← Mode selector + counter
│  └───────────────────────────────────────┘ │
│                                             │
└─────────────────────────────────────────────┘
```

### Compact Card Specifications

**Overall Card:**
- Background: Light gradient (soft blue tint) `from-[#EBF8FF] to-[#F0F9FF]`
- Border-radius: 20px (very rounded)
- Padding: 20px
- Shadow: Medium (`0 4px 12px rgba(0,0,0,0.1)`)
- Height: 280px (fixed)

**Dobby Avatar:**
- Size: 48px × 48px circular
- Background: Gradient teal `from-teal to-teal-dark`
- Icon: Robot emoji 🤖 or custom Dobby character
- Shadow: Soft (`0 2px 8px rgba(0,0,0,0.15)`)
- Centered horizontally

**Title & Subtitle:**
- Title: "Chat with Dobby" - 16px, semibold, gray-800
- Subtitle: 11px, regular, gray-600
- Both centered
- Margin: 8px below avatar, 12px below subtitle

**Suggested Prompts Carousel:**
- 2 prompts visible at a time
- Each prompt: Pill button, white background, 13px text
- Border: 1px solid gray-200
- Rounded: 12px
- Padding: 10px 16px
- Hover: Shadow lift + teal tint background
- Carousel arrows: Chevron icons, 8px × 8px
- Pagination dots: 1.5px circles, teal when active
- Gap between prompts: 8px

**Input Area (Hume.ai inspired):**
- Container: White background, 2px border gray-200
- Border-radius: 16px
- Padding: 12px
- Focus state: Border changes to teal, ring effect
- Textarea: Single-line appearance (expandable)
- Placeholder: "Type your message..." gray-400

**Mode Selector (below input):**
- Two pill buttons: [AI] [Therapist]
- Style: Similar to Hume.ai "Conversational" tag
- Border: 0.5px solid, gray-300
- Padding: 6px 12px
- Font: 12px, uppercase, mono font
- Active state: Filled background (teal)
- Icons: Small icon + text

**Character Counter:**
- Position: Bottom right of input
- Format: "50/500" (current/max)
- Font: 12px, mono, gray-500
- Updates live as user types

**Send Button:**
- Position: Right side of textarea (inline)
- Style: Circular, 40px diameter
- Background: Black or teal gradient
- Icon: Arrow up (white)
- Hover: Scale up slightly + shadow

---

## Fullscreen Mode Layout

```
┌─────────────────────────────────────────────────┐
│  ← Back                                   [×]   │ ← Top bar (60px)
│  Chat with Dobby                                │
├─────────────────────────────────────────────────┤
│                                                 │
│  [Scroll to top to see full description]       │ ← Hidden initially
│                                                 │
│  ═══════════════════════════════════════════   │
│                                                 │
│  [Chat conversation area]                       │
│                                                 │
│  👤 User: How is my progress going?             │ ← User messages (right)
│                                                 │
│  🤖 Dobby: Based on your 10 sessions, you've... │ ← AI messages (left)
│                                                 │
│  [Chat messages continue...]                    │
│                                                 │
│  ═══════════════════════════════════════════   │
│                                                 │
│  💡 Suggested prompts:                          │ ← Carousel at bottom
│  ┌───────────────┬───────────────┐             │
│  │ "Help me prep │ │ "What patterns│  [< >]    │
│  │  for session" │ │  do you see?" │           │
│  └───────────────┴───────────────┘             │
│  ● ○ ○                                          │
│                                                 │
│  ─────────────────────────────────────────      │
│  ┌───────────────────────────────────────────┐ │
│  │ Type your message...              [Send]  │ │
│  │                                           │ │
│  │ [AI] [Therapist]            124/500      │ │
│  └───────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

### Fullscreen Specifications

**Top Bar:**
- Height: 60px
- Border bottom: 1px solid gray-200
- Background: White
- Left: Back arrow + "Back" text (teal color)
- Center: "Chat with Dobby" title (18px, semibold)
- Right: X close button (circular, hover bg gray-100)

**Description (scroll reveal):**
- Initially scrolled past viewport
- User scrolls up to reveal
- Content:
  ```
  Meet Dobby - Your Therapy Companion

  What I can help with:
  • Prepare for upcoming sessions
  • Answer mental health questions
  • Save topics to discuss later
  • Message your therapist directly
  • Reference your session data
  ```
- Background: Light gray-50
- Padding: 24px
- Border bottom: 1px solid gray-200

**Chat Messages Area:**
- Background: Gradient `from-gray-50 to-white`
- Padding: 24px
- Scrollable (full height between top bar and input)
- Gap between messages: 16px

**Message Bubbles:**
- **User messages:**
  - Align: Right
  - Background: Gradient teal `from-teal to-teal-dark`
  - Text color: White
  - Border-radius: 20px (more rounded on left)
  - Max-width: 70%
  - Padding: 12px 16px
  - Avatar: 32px circle, gray-200, user icon 👤
  - Shadow: Soft

- **AI messages (Dobby):**
  - Align: Left
  - Background: White
  - Text color: Gray-800
  - Border: 1px solid gray-200
  - Border-radius: 20px (more rounded on right)
  - Max-width: 70%
  - Padding: 12px 16px
  - Avatar: 32px circle, teal gradient, robot icon 🤖
  - Shadow: Soft

**Prompt Suggestions (bottom area):**
- Background: Gray-50
- Border top: 1px solid gray-200
- Padding: 16px
- Same carousel as compact card
- 💡 Light bulb icon before "Suggested prompts:"

**Input Bar (Hume.ai style):**
- Max-width: 800px, centered
- Background: White
- Border: 2px solid gray-300
- Border-radius: 16px
- Padding: 16px
- Focus state: Border teal, ring effect
- Textarea: Expandable (auto-height up to 120px)
- Mode selector: Below textarea
- Character counter: Bottom right
- Send button: Right side, larger (48px)

---

## Hume.ai Design Elements to Adapt

### 1. Voice Selector → Mode Selector
**Hume.ai has:** Voice dropdown with icon + label
**Adapt to:** Mode toggle between [AI] and [Therapist]

**Design:**
- Two pill buttons side-by-side
- Icons: 🤖 AI robot | 💬 Therapist speech bubble
- Label below icon (small, 10px, uppercase)
- Active state: Filled background (teal)
- Inactive state: White background, border only

### 2. "Conversational" Tag → Context Tags
**Hume.ai has:** "Conversational" pill button tag
**Adapt to:** Therapy context tags (optional feature)

**Possible tags:**
- "Session Prep" - preparing for upcoming session
- "Question" - asking mental health question
- "Check-in" - mood/progress check
- "Urgent" - crisis support needed

**Design:** Same as Hume.ai tag style
- Pill shape, 0.5px border
- Uppercase, 12px mono font
- Icon + text
- Click to toggle/select

### 3. Character Counter
**Hume.ai has:** "50/500" in bottom right
**Keep for:** Encouraging concise messages (optional)

**Design:** Exact same as Hume.ai
- Position: Bottom right
- Font: 14px, mono, gray-500
- Format: "current/max"

### 4. Play Button → Send Button
**Hume.ai has:** Black circular play button (56px)
**Adapt to:** Send/submit button

**Design:**
- Circular, 48px diameter (compact), 56px (fullscreen)
- Background: Black or teal gradient
- Icon: Arrow up ↑ or send icon →
- Hover: Scale 105% + shadow lift
- Disabled state: Opacity 40%, no hover effect

---

## Color Palette (Therapy-Appropriate)

**Primary Colors:**
- Soft Teal: `#5AB9B4` (buttons, accents, AI mode)
- Warm Lavender: `#B8A5D6` (secondary accents)
- Gentle Coral: `#F4A69D` (therapist mode, warnings)

**Neutrals:**
- Warm Cream: `#F7F5F3` (page background)
- White: `#FFFFFF` (card backgrounds, message bubbles)
- Gray-50 to Gray-900: Standard gray scale
- Black: `#232323` (send button, text)

**Gradients:**
- Teal gradient: `linear-gradient(135deg, #5AB9B4, #4A9D99)`
- Blue tint: `linear-gradient(135deg, #EBF8FF, #F0F9FF)` (card background)

---

## Typography

**Font Families:**
- Sans-serif: Inter (body, UI elements)
- Monospace: Space Mono or IBM Plex Mono (character counter, mode labels)
- Headings: Crimson Pro (optional for title)

**Type Scale:**
- Title (compact): 16px, semibold
- Title (fullscreen): 18px, semibold
- Subtitle: 11px, regular
- Message text: 14px, regular
- Prompt buttons: 13px, medium
- Mode labels: 12px, uppercase, mono
- Character counter: 14px, mono

---

## Spacing & Measurements

**Compact Card:**
- Card padding: 20px
- Avatar size: 48px
- Avatar to title: 8px
- Title to subtitle: 4px
- Subtitle to prompts: 12px
- Prompts to separator: 12px
- Separator to input: 12px

**Fullscreen:**
- Top bar height: 60px
- Message padding: 24px horizontal
- Message gap: 16px vertical
- Bubble padding: 12px 16px
- Avatar size: 32px
- Avatar to bubble gap: 12px

**Input Area (both states):**
- Border width: 2px
- Border-radius: 16px
- Padding: 12px (compact), 16px (fullscreen)
- Send button: 40px (compact), 48px (fullscreen)

---

## Interaction States

### Hover States
- **Prompt buttons:** Shadow lift + teal tint background
- **Send button:** Scale 105% + shadow deepen
- **Mode selector:** Teal border glow
- **Back/Close buttons:** Gray background (gray-100)

### Focus States
- **Input textarea:** Border changes to teal, 2px ring (teal/20)
- **All buttons:** Outline for keyboard navigation

### Active States
- **Mode selector:** Filled background (teal), white text
- **Prompt clicked:** Inserts text into input, brief highlight

### Disabled States
- **Send button:** Opacity 40%, no hover, cursor not-allowed
- **When input empty:** Send button disabled

---

## Sample Content for Wireframes

### Suggested Prompts (6 total, 2 visible per page)
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

## Deliverable Request

**Please create 4-6 wireframe variations showing:**

1. **Compact card - default state** (avatar, prompts, input with mode selector)
2. **Compact card - input focused** (showing teal ring, send button enabled)
3. **Fullscreen - conversation view** (showing 3-4 messages back and forth)
4. **Fullscreen - scrolled to top** (revealing description section)
5. **Mode selector variations** (AI mode vs. Therapist mode active)
6. **Prompt interaction** (showing carousel navigation, page 2 of 3)

**Design considerations to explore:**
- Should mode selector be tabs or toggle switch?
- Should character counter be always visible or only when typing?
- Should prompts carousel have arrows or just swipe/dots?
- Should Dobby avatar be robot emoji 🤖 or custom illustration?
- Should message bubbles have timestamps?

---

## Hume.ai Design Patterns to Preserve

**✅ Keep these exact patterns:**
- 0.5px borders (subtle, refined)
- Pill-shaped buttons with large border-radius
- White backgrounds for interactive elements
- Monospace font for metadata (counter, tags)
- Circular action button (send)
- Uppercase labels for modes/tags
- Character counter format (current/max)

**✅ Adapt these patterns:**
- Voice selector → AI/Therapist mode toggle
- "Conversational" tag → Therapy context tags
- Play button → Send button
- Text-to-speech controls → Chat controls

---

## Visual Hierarchy

**Most prominent (draw eye first):**
1. Dobby avatar (centered, gradient, shadowed)
2. Send button (circular, black/teal, contrasting)
3. Suggested prompts (white pills, interactive)

**Secondary (supporting info):**
4. Title and subtitle (hierarchy through size)
5. Mode selector (functional but not distracting)
6. Input textarea (clean, minimal)

**Tertiary (utility):**
7. Character counter (small, gray, corner)
8. Pagination dots (tiny, unobtrusive)
9. Separator line (1px, subtle)

---

## Accessibility Requirements

- **Keyboard navigation:** All interactive elements tab-accessible
- **Focus indicators:** Visible outlines on all buttons/inputs
- **ARIA labels:** "Send message", "Select AI mode", "Next prompts"
- **Screen reader:** Announce mode changes, message sent confirmations
- **Color contrast:** WCAG AA minimum (4.5:1 for text)
- **Touch targets:** 44px minimum (send button, mode selector)

---

## Technical Notes

**Animation preferences:**
- Prompt carousel: Slide transition (300ms ease-in-out)
- Hover states: Transform + shadow (200ms ease-out)
- Mode toggle: Background fill (150ms ease)
- Message appear: Fade in + slide up (200ms)
- Send button: Scale on hover (150ms spring)

**Responsive behavior (future):**
- Compact card: Maintains aspect ratio, shrinks on mobile
- Fullscreen: Always full viewport
- Input area: Stacks mode selector below textarea on narrow screens

---

## Success Criteria

A successful wireframe will:
1. ✅ Preserve Hume.ai's elegant, minimal aesthetic
2. ✅ Adapt design to therapy chatbot context appropriately
3. ✅ Show clear visual hierarchy (avatar → prompts → input)
4. ✅ Demonstrate both compact and fullscreen modes
5. ✅ Include mode selector and character counter
6. ✅ Feel calm and therapy-appropriate (not corporate/clinical)
7. ✅ Be scannable and inviting to use

---

**End of Prompt**

Generate wireframes showing this AI therapy chatbot in both compact card and fullscreen states, preserving Hume.ai's design elegance while adapting to mental health context. Focus on clean visual hierarchy, subtle interactions, and therapy-appropriate aesthetics.
