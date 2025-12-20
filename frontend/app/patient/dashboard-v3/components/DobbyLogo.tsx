'use client';

/**
 * Dobby AI Logo - Therapy companion mascot
 * - Gradient circle with stylized character
 * - Scalable size via props
 */

interface DobbyLogoProps {
  size?: number;
}

export function DobbyLogo({ size = 48 }: DobbyLogoProps) {
  return (
    <div
      className="rounded-full bg-gradient-to-br from-[#5AB9B4] to-[#B8A5D6] flex items-center justify-center shadow-md"
      style={{ width: size, height: size }}
    >
      <span
        className="text-white font-bold"
        style={{ fontSize: size * 0.4 }}
      >
        D
      </span>
    </div>
  );
}
