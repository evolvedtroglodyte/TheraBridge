/**
 * MarkdownMessage - Renders Dobby's responses with markdown formatting
 *
 * Features:
 * - Preserves paragraph breaks (double newlines)
 * - Renders **bold text**
 * - Renders bullet lists (lines starting with • or -)
 * - Renders numbered lists (lines starting with 1. 2. etc.)
 * - Detects and highlights crisis resources with clickable phone numbers
 */

import React from 'react';

interface MarkdownMessageProps {
  content: string;
  isDark: boolean;
}

// Crisis resource detection patterns
const CRISIS_PATTERNS = {
  '988': /988 Suicide & Crisis Lifeline|988.*?Lifeline/gi,
  'crisis-text': /Crisis Text Line.*?741741/gi,
  '911': /call 911|911.*?emergency/gi,
};

export function MarkdownMessage({ content, isDark }: MarkdownMessageProps) {
  // Split content into blocks (paragraphs separated by double newlines)
  const blocks = content.split('\n\n').filter(block => block.trim());

  return (
    <div className="space-y-3">
      {blocks.map((block, blockIndex) => {
        const trimmedBlock = block.trim();

        // Check if block is a numbered list (starts with 1. or 2. etc.)
        if (/^\d+\./.test(trimmedBlock)) {
          const listItems = trimmedBlock.split('\n').filter(line => line.trim());
          return (
            <ol key={blockIndex} className="list-decimal list-inside space-y-1 ml-2">
              {listItems.map((item, itemIndex) => {
                const cleanedItem = item.replace(/^\d+\.\s*/, '').trim();
                return (
                  <li key={itemIndex} className="leading-relaxed">
                    {renderInlineFormatting(cleanedItem, isDark)}
                  </li>
                );
              })}
            </ol>
          );
        }

        // Check if block is a bullet list (lines starting with • or -)
        if (/^[•\-]/.test(trimmedBlock)) {
          const listItems = trimmedBlock.split('\n').filter(line => /^[•\-]/.test(line.trim()));
          return (
            <ul key={blockIndex} className="list-disc list-inside space-y-1 ml-2">
              {listItems.map((item, itemIndex) => {
                const cleanedItem = item.replace(/^[•\-]\s*/, '').trim();
                return (
                  <li key={itemIndex} className="leading-relaxed">
                    {renderInlineFormatting(cleanedItem, isDark)}
                  </li>
                );
              })}
            </ul>
          );
        }

        // Check if block contains crisis resources
        const isCrisisResource = Object.values(CRISIS_PATTERNS).some(pattern =>
          pattern.test(trimmedBlock)
        );

        if (isCrisisResource) {
          return (
            <div
              key={blockIndex}
              className={`p-3 rounded-lg border ${
                isDark
                  ? 'bg-red-950/30 border-red-800/50'
                  : 'bg-red-50 border-red-200'
              }`}
            >
              <CrisisResourceBlock content={trimmedBlock} isDark={isDark} />
            </div>
          );
        }

        // Regular paragraph
        return (
          <p key={blockIndex} className="leading-relaxed">
            {renderInlineFormatting(trimmedBlock, isDark)}
          </p>
        );
      })}
    </div>
  );
}

/**
 * Renders inline formatting (bold text, links, etc.)
 */
function renderInlineFormatting(text: string, isDark: boolean): React.ReactNode {
  const parts: React.ReactNode[] = [];
  let currentIndex = 0;

  // Regex to match **bold text**
  const boldRegex = /\*\*(.*?)\*\*/g;
  let match;

  while ((match = boldRegex.exec(text)) !== null) {
    // Add text before the bold
    if (match.index > currentIndex) {
      parts.push(text.substring(currentIndex, match.index));
    }

    // Add bold text
    parts.push(
      <strong key={match.index} className="font-semibold">
        {match[1]}
      </strong>
    );

    currentIndex = match.index + match[0].length;
  }

  // Add remaining text
  if (currentIndex < text.length) {
    parts.push(text.substring(currentIndex));
  }

  return parts.length > 0 ? parts : text;
}

/**
 * Renders crisis resource blocks with clickable phone numbers
 */
function CrisisResourceBlock({ content, isDark }: { content: string; isDark: boolean }) {
  // Parse phone numbers and make them clickable
  const renderWithClickableNumbers = (text: string) => {
    // Match phone numbers: 988, 741741, 911
    const phoneRegex = /(988|741741|911)/g;
    const parts = text.split(phoneRegex);

    return parts.map((part, index) => {
      if (/^(988|741741|911)$/.test(part)) {
        return (
          <a
            key={index}
            href={`tel:${part}`}
            className={`font-semibold underline ${
              isDark ? 'text-red-300 hover:text-red-200' : 'text-red-700 hover:text-red-800'
            }`}
            onClick={(e) => {
              // For non-phone devices, copy to clipboard instead
              if (!('ontouchstart' in window)) {
                e.preventDefault();
                navigator.clipboard.writeText(part);
                // TODO: Show toast notification
              }
            }}
          >
            {part}
          </a>
        );
      }
      return renderInlineFormatting(part, isDark);
    });
  };

  return (
    <div className="space-y-1">
      {content.split('\n').map((line, index) => (
        <div key={index} className="leading-relaxed">
          {renderWithClickableNumbers(line.trim())}
        </div>
      ))}
    </div>
  );
}
