# Font Update Guide for Remaining Dashboard Cards

## Completed ✅
- NotesGoalsCard
- ToDoCard
- TherapistBridgeCard
- ProgressPatternsCard
- AIChatCard
- Home icon redirect fix (now goes to /dashboard)
- Inter and Crimson Pro fonts imported in layout
- All Playwright tests passing (8/8)

## Font Specifications (from SessionCard)

### Font Families
```typescript
const fontSerif = '"Crimson Pro", Georgia, serif';
const fontSans = '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
```

### Font Usage Pattern

| Element Type | Font Family | Size | Weight | Other Styles |
|--------------|-------------|------|--------|--------------|
| **Card Title (Compact)** | `fontSerif` | 20px | 600 | - |
| **Card Title (Modal)** | `fontSerif` | 24px | 600 | - |
| **Section Labels** | `fontSans` | 11px | 500 | uppercase, letterSpacing: '1px' |
| **Body Text** | `fontSerif` | 14px | 400 | lineHeight: 1.6 |
| **List Items** | `fontSerif` | 13px | 300 | lineHeight: 1.5 |
| **Metadata/Captions** | `fontSans` | 11px | 500 | - |
| **Small Metadata** | `fontSans` | 13px | 500 | - |

## Search and Replace Patterns

### Pattern 1: Card Titles (Compact State)
**Find:** `style={{ fontFamily: fontSans }} className="text-lg font-light`
**Replace:** `style={{ fontFamily: fontSerif, fontSize: '20px', fontWeight: 600 }} className="`

### Pattern 2: Modal Titles
**Find:** `style={{ fontFamily: fontSans }} className="text-2xl font-medium`
**Replace:** `style={{ fontFamily: fontSerif, fontSize: '24px', fontWeight: 600 }} className="`

### Pattern 3: Section Labels (uppercase)
**Find:** `style={{ fontFamily: fontSans }} className="text-sm font-semibold`
**Replace:** `style={{ fontFamily: fontSans, fontSize: '11px', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '1px' }} className="`

### Pattern 4: Body Text
**Find:** `style={{ fontFamily: fontSerif }} className="text-sm font-light`
**Replace:** `style={{ fontFamily: fontSerif, fontSize: '14px', fontWeight: 400, lineHeight: 1.6 }} className="`

### Pattern 5: List Items
**Find:** `style={{ fontFamily: fontSerif }} className="text-sm`
**Replace:** `style={{ fontFamily: fontSerif, fontSize: '13px', fontWeight: 300, lineHeight: 1.5 }} className="`

## Manual Updates Needed

For **ProgressPatternsCard** and **AIChatCard**:

1. Open the file in your editor
2. Search for all instances of `fontFamily`
3. Apply the appropriate pattern based on the element type
4. Remove conflicting Tailwind classes (like `text-lg`, `font-light`, etc.)
5. Test in browser to ensure consistency

## Testing Checklist

After updates:
- [ ] Navigate to `/dashboard`
- [ ] Check all 5 cards have consistent fonts
- [ ] Expand each card modal
- [ ] Verify fonts match SessionCard style
- [ ] Click home icon in AI Chat - should go to `/dashboard`
- [ ] Test in dark mode
