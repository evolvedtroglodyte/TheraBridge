# Upload Page Design Specification
**Version:** 1.0
**Date:** December 2025
**Status:** Design Only (Not Implemented)

---

## Overview

The Upload page provides two methods for patients to submit therapy session audio:
1. **Live Recording** - Record directly in the browser
2. **File Upload** - Drag-and-drop or browse for existing audio files

### Design Philosophy
- **Split-screen layout** - Record on left, Upload on right
- **Visual hierarchy** - Clear separation with distinct call-to-actions
- **Accessibility** - Keyboard navigation, screen reader support
- **Feedback** - Real-time visual feedback for all actions

---

## Page Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│  HEADER (same as dashboard)                                         │
│  [Home] [🌙] | Dashboard | Ask AI | [Upload - Active]               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────┐ │ ┌─────────────────────────────┐ │
│  │                             │ │ │                             │ │
│  │     🎙️ RECORD SESSION       │ │ │     📁 UPLOAD FILE          │ │
│  │                             │ │ │                             │ │
│  │  ┌─────────────────────┐   │ │ │  ┌─────────────────────┐   │ │
│  │  │                     │   │ │ │  │                     │   │ │
│  │  │   [Waveform Area]   │   │ │ │  │   Drop Zone         │   │ │
│  │  │                     │   │ │ │  │   - - - - - - - -   │   │ │
│  │  │   Live visualization│   │ │ │  │                     │   │ │
│  │  │   during recording  │   │ │ │  │   📎 Drag & drop    │   │ │
│  │  │                     │   │ │ │  │   audio files here  │   │ │
│  │  └─────────────────────┘   │ │ │  │                     │   │ │
│  │                             │ │ │  │   or                │   │ │
│  │  ⏱️ 00:00:00               │ │ │  │                     │   │ │
│  │                             │ │ │  │   [Browse Files]    │   │ │
│  │  ┌───┐  ┌───┐  ┌───┐      │ │ │  │                     │   │ │
│  │  │ ⏺ │  │ ⏸ │  │ ⏹ │      │ │ │  └─────────────────────┘   │ │
│  │  │Rec│  │Pse│  │Stp│      │ │ │                             │ │
│  │  └───┘  └───┘  └───┘      │ │ │  Supported: MP3, WAV, M4A,  │ │
│  │                             │ │ │  OGG, FLAC, WebM           │ │
│  │  [Save Recording]          │ │ │  Max size: 500MB            │ │
│  │                             │ │ │                             │ │
│  └─────────────────────────────┘ │ └─────────────────────────────┘ │
│               │                                                     │
│               │  ← Vertical Divider →                              │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│  RECENT UPLOADS (Optional section below)                            │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐                              │
│  │Dec 20│ │Dec 18│ │Dec 15│ │Dec 12│  Status: Processing/Done     │
│  └──────┘ └──────┘ └──────┘ └──────┘                              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Component Specifications

### 1. Record Section (Left Panel)

**Container:**
- Background: `bg-gradient-to-br from-[#EBF8FF] to-[#F0F9FF]` (light)
- Background: `dark:from-[#1a1625] dark:to-[#2a2435]` (dark)
- Border-radius: `24px`
- Padding: `32px`
- Min-height: `500px`

**Waveform Visualization:**
```
┌─────────────────────────────────────┐
│                                     │
│    ▁▂▃▅▆▇█▇▆▅▃▂▁▂▃▅▆▇█▇▆▅▃▂▁     │
│                                     │
│    Real-time audio waveform         │
│    using Web Audio API              │
│                                     │
└─────────────────────────────────────┘
```

**States:**
1. **Idle** - Flat line, "Click Record to start" message
2. **Recording** - Live waveform, pulsing red indicator, timer counting up
3. **Paused** - Frozen waveform, yellow indicator
4. **Stopped** - Static waveform preview, playback controls appear

**Controls:**
| Button | Icon | Color | Action |
|--------|------|-------|--------|
| Record | ⏺ Circle | Red `#EF4444` | Start/Resume recording |
| Pause | ⏸ Double bar | Yellow `#F59E0B` | Pause recording |
| Stop | ⏹ Square | Gray `#6B7280` | End recording |

**Timer Display:**
- Font: `font-mono text-3xl`
- Format: `HH:MM:SS`
- Color: `text-gray-800 dark:text-gray-200`

**Save Button:**
- Appears after recording stops
- Primary gradient: `from-[#5AB9B4] to-[#4A9D99]`
- Full width
- Text: "Save Recording"

---

### 2. Upload Section (Right Panel)

**Container:**
- Background: `bg-white dark:bg-[#2a2435]`
- Border: `border-2 border-dashed border-gray-300 dark:border-[#3d3548]`
- Border-radius: `24px`
- Padding: `32px`
- Min-height: `500px`

**Drop Zone States:**

1. **Default:**
   ```
   ┌─────────────────────────┐
   │                         │
   │       📎               │
   │                         │
   │   Drag & drop audio     │
   │   files here            │
   │                         │
   │        or               │
   │                         │
   │   [Browse Files]        │
   │                         │
   └─────────────────────────┘
   ```

2. **Drag Over (Active):**
   - Border: `border-[#5AB9B4] border-solid`
   - Background: `bg-[#5AB9B4]/10`
   - Scale: `scale-[1.02]`
   - Icon: Animated bounce

3. **File Selected:**
   ```
   ┌─────────────────────────┐
   │                         │
   │   🎵 session_dec20.mp3  │
   │   ──────────────────    │
   │   45.2 MB | 52:34       │
   │                         │
   │   [✓ Upload]  [✕ Clear] │
   │                         │
   └─────────────────────────┘
   ```

4. **Uploading:**
   ```
   ┌─────────────────────────┐
   │                         │
   │   🎵 session_dec20.mp3  │
   │   ████████░░░░  67%     │
   │   Uploading...          │
   │                         │
   │   [Cancel]              │
   │                         │
   └─────────────────────────┘
   ```

5. **Success:**
   - Green checkmark animation
   - "Upload complete!" message
   - Auto-redirect to processing status after 2s

6. **Error:**
   - Red border pulse
   - Error message with retry option
   - Common errors: file too large, unsupported format, network error

**Supported Formats:**
- Audio: MP3, WAV, M4A, OGG, FLAC, WebM, AAC
- Max file size: 500MB
- Display: Small text below drop zone

---

### 3. Vertical Divider

**Design:**
```css
.divider {
  width: 1px;
  background: linear-gradient(
    to bottom,
    transparent 0%,
    #E5E7EB 20%,
    #E5E7EB 80%,
    transparent 100%
  );
  /* dark mode */
  dark:background: linear-gradient(
    to bottom,
    transparent 0%,
    #3d3548 20%,
    #3d3548 80%,
    transparent 100%
  );
}
```

**With "OR" badge:**
```
        │
        │
      ┌───┐
      │OR │  ← Centered badge
      └───┘
        │
        │
```

---

## Interaction Patterns

### Recording Flow:
1. User clicks Record button
2. Browser requests microphone permission (if first time)
3. Waveform starts animating
4. Timer starts counting
5. User can Pause/Resume
6. User clicks Stop
7. Waveform freezes, playback controls appear
8. User can preview before saving
9. Click "Save Recording" → Upload begins
10. Success → Redirect to processing status

### Upload Flow:
1. User drags file over drop zone OR clicks "Browse Files"
2. File validation (type, size)
3. If valid: Show file preview with metadata
4. Click "Upload" button
5. Progress bar animation
6. Success → Redirect to processing status
7. Error → Show error message with retry

### Keyboard Navigation:
- `Tab` - Move between Record/Upload sections
- `Space/Enter` - Activate focused button
- `Escape` - Cancel current operation

---

## Visual Design Tokens

### Colors (matching dashboard):
```css
--teal-primary: #5AB9B4;
--teal-dark: #4A9D99;
--purple-accent: #a78bfa;
--coral-accent: #F4A69D;

--record-red: #EF4444;
--pause-yellow: #F59E0B;
--success-green: #10B981;
--error-red: #DC2626;

--bg-light: #F7F5F3;
--bg-dark: #1a1625;
--card-dark: #2a2435;
--border-dark: #3d3548;
```

### Typography:
- Headings: `font-mono uppercase tracking-wide`
- Body: System font stack
- Timer: `font-mono text-3xl font-bold`

### Spacing:
- Section gap: `24px`
- Inner padding: `32px`
- Button gap: `12px`

### Animations:
- Hover: `transition-all duration-200`
- Waveform: 60fps canvas animation
- Progress bar: `transition-all duration-300 ease-out`
- Success checkmark: Spring animation (same as modals)

---

## Responsive Behavior

### Desktop (>1024px):
- Side-by-side layout (50/50 split)
- Full waveform visualization

### Tablet (768px - 1024px):
- Stacked layout (Record on top, Upload below)
- Waveform height reduced

### Mobile (<768px):
- Single column
- Simplified waveform (bars instead of continuous)
- Larger touch targets for buttons

---

## Technical Considerations

### Web Audio API:
- Use `AudioContext` for waveform visualization
- `MediaRecorder` API for recording
- Fallback for unsupported browsers

### File Handling:
- Validate MIME type client-side
- Stream large files in chunks
- Show accurate progress for large uploads

### State Management:
- Recording state in component
- Upload progress in component
- Success/error states trigger navigation

---

## Future Enhancements (Not in v1):

1. **Multi-file upload** - Batch upload multiple sessions
2. **Recording quality settings** - Low/Medium/High bitrate
3. **Audio trimming** - Cut silence from beginning/end
4. **Session metadata** - Add notes, mood rating before upload
5. **Cloud sync** - Resume interrupted uploads
6. **Offline recording** - Save locally, upload when online

---

## Approval Checklist

- [ ] Layout matches user requirements (record left, upload right)
- [ ] Waveform visualization design approved
- [ ] Color scheme consistent with dashboard
- [ ] All supported file formats listed
- [ ] Error states designed
- [ ] Mobile responsive behavior defined
- [ ] Accessibility requirements met

---

**Ready for implementation after user approval.**
