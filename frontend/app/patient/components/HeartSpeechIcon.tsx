'use client';

/**
 * HeartSpeechIcon - Heart-shaped speech bubble for therapist mode
 * Used as avatar for therapist messages in chat
 *
 * - Always orange (#F4A69D to #E88B7E gradient feel, solid #F4A69D)
 * - Represents human connection and therapist communication
 */

interface HeartSpeechIconProps {
  size?: number;
}

export function HeartSpeechIcon({ size = 28 }: HeartSpeechIconProps) {
  // Always orange - doesn't change with theme
  const color = '#F4A69D';

  return (
    <div
      className="flex items-center justify-center"
      style={{ width: size, height: size }}
    >
      <svg
        width={size}
        height={size}
        viewBox="0 0 24 24"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="transition-all duration-300"
      >
        {/* Heart shape with speech bubble tail */}
        <path
          d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"
          fill={color}
        />
        {/* Small speech indicator dots */}
        <circle cx="8" cy="9" r="1" fill="white" opacity="0.8" />
        <circle cx="12" cy="9" r="1" fill="white" opacity="0.8" />
        <circle cx="16" cy="9" r="1" fill="white" opacity="0.8" />
      </svg>
    </div>
  );
}
