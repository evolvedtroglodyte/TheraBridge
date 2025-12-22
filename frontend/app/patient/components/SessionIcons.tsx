/**
 * Session Card Icons
 * - Breakthrough Star with gold glow effect
 * - Mood Emojis (happy, neutral, sad) with teal/white colors
 * - Used in SessionCard component for visual session indicators
 */

interface IconProps {
  size?: number;
  isDark?: boolean;
}

// Breakthrough Star - Rounded 5-point with illumination
export function BreakthroughStar({ size = 24, isDark = false }: IconProps) {
  const goldColor = isDark ? '#FFE066' : '#FFCA00';

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      style={{ filter: `drop-shadow(0 0 6px ${goldColor}90)` }}
    >
      <path
        d="M16 3L18.8 11.2C19 11.8 19.5 12.2 20.1 12.2H28.5C28.9 12.2 29.1 12.7 28.8 13L21.8 18.3C21.3 18.7 21.1 19.3 21.3 19.9L24 28.1C24.1 28.5 23.7 28.8 23.3 28.6L16.4 23.4C15.9 23.1 15.2 23.1 14.7 23.4L7.8 28.6C7.4 28.9 6.9 28.5 7.1 28.1L9.8 19.9C10 19.3 9.8 18.7 9.3 18.3L2.3 13C1.9 12.7 2.1 12.2 2.6 12.2H11C11.6 12.2 12.1 11.8 12.3 11.2L15.1 3C15.3 2.5 15.8 2.5 16 3Z"
        fill={goldColor}
      />
    </svg>
  );
}

// Happy Emoji - Smiling face
export function HappyEmoji({ size = 24, isDark = false }: IconProps) {
  const emojiColor = isDark ? '#FFFFFF' : '#4ECDC4';

  return (
    <svg width={size} height={size} viewBox="0 0 32 32" fill="none">
      <circle cx="16" cy="16" r="14" stroke={emojiColor} strokeWidth="2" fill="none" />
      <circle cx="11" cy="14" r="1.5" fill={emojiColor} />
      <circle cx="21" cy="14" r="1.5" fill={emojiColor} />
      <path d="M11 20Q16 24 21 20" stroke={emojiColor} strokeWidth="2" strokeLinecap="round" fill="none" />
    </svg>
  );
}

// Neutral Emoji - Straight line mouth
export function NeutralEmoji({ size = 24, isDark = false }: IconProps) {
  const emojiColor = isDark ? '#FFFFFF' : '#4ECDC4';

  return (
    <svg width={size} height={size} viewBox="0 0 32 32" fill="none">
      <circle cx="16" cy="16" r="14" stroke={emojiColor} strokeWidth="2" fill="none" />
      <circle cx="11" cy="13" r="2" fill={emojiColor} />
      <circle cx="21" cy="13" r="2" fill={emojiColor} />
      <line x1="10" y1="21" x2="22" y2="21" stroke={emojiColor} strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

// Sad Emoji - Frowning face
export function SadEmoji({ size = 24, isDark = false }: IconProps) {
  const emojiColor = isDark ? '#FFFFFF' : '#4ECDC4';

  return (
    <svg width={size} height={size} viewBox="0 0 32 32" fill="none">
      <circle cx="16" cy="16" r="14" stroke={emojiColor} strokeWidth="2" fill="none" />
      <circle cx="10" cy="14" r="1" fill={emojiColor} />
      <circle cx="22" cy="14" r="1" fill={emojiColor} />
      <path d="M11 22Q16 18 21 22" stroke={emojiColor} strokeWidth="2" strokeLinecap="round" fill="none" />
    </svg>
  );
}

// Helper to render mood emoji based on mood type
export function renderMoodEmoji(mood: string, size = 24, isDark = false) {
  switch (mood) {
    case 'positive':
    case 'happy':
      return <HappyEmoji size={size} isDark={isDark} />;
    case 'neutral':
      return <NeutralEmoji size={size} isDark={isDark} />;
    case 'low':
    case 'sad':
      return <SadEmoji size={size} isDark={isDark} />;
    default:
      return <NeutralEmoji size={size} isDark={isDark} />;
  }
}
