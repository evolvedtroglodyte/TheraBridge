'use client';

import * as React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, FileText } from 'lucide-react';
import { cn } from '@/lib/utils';
import { ModalWrapper } from '@/components/dashboard-v2/shared/ModalWrapper';
import { notesGoalsData } from '@/lib/mock-data/dashboard-v2';
import { cardHoverVariants, collapseVariants } from '@/lib/animations';

// ============================================================================
// Types
// ============================================================================

interface NotesGoalsPanelProps {
  /** Optional class name for the compact card */
  className?: string;
  /** Optional callback when panel is expanded */
  onExpand?: () => void;
  /** Optional callback when panel is collapsed */
  onCollapse?: () => void;
}

// ============================================================================
// Collapsible Section Component
// ============================================================================

interface CollapsibleSectionProps {
  id: string;
  title: string;
  content: string;
  isExpanded: boolean;
  onToggle: () => void;
}

function CollapsibleSection({
  id,
  title,
  content,
  isExpanded,
  onToggle,
}: CollapsibleSectionProps) {
  const contentId = `section-content-${id}`;
  const headerId = `section-header-${id}`;

  return (
    <div className="border-b border-border/40 last:border-b-0">
      <button
        id={headerId}
        onClick={onToggle}
        aria-expanded={isExpanded}
        aria-controls={contentId}
        className={cn(
          'w-full flex items-center justify-between py-4 px-2',
          'text-left hover:bg-muted/40 rounded-lg transition-colors',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2'
        )}
      >
        <span
          className="font-semibold text-foreground text-base"
          style={{ fontFamily: 'Crimson Pro, serif' }}
        >
          {title}
        </span>
        <motion.span
          animate={{ rotate: isExpanded ? 180 : 0 }}
          transition={{ duration: 0.2 }}
          className="text-muted-foreground"
        >
          <ChevronDown className="w-5 h-5" />
        </motion.span>
      </button>
      <AnimatePresence initial={false}>
        {isExpanded && (
          <motion.div
            id={contentId}
            role="region"
            aria-labelledby={headerId}
            initial="collapsed"
            animate="expanded"
            exit="collapsed"
            variants={collapseVariants}
            className="overflow-hidden"
          >
            <div className="pb-4 px-2">
              <p
                className="text-sm text-muted-foreground leading-relaxed whitespace-pre-line"
                style={{ fontFamily: 'Inter, sans-serif' }}
              >
                {content}
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ============================================================================
// Main NotesGoalsPanel Component
// ============================================================================

export function NotesGoalsPanel({
  className,
  onExpand,
  onCollapse,
}: NotesGoalsPanelProps) {
  const [isExpanded, setIsExpanded] = React.useState(false);

  // Initialize with first 2 sections expanded (Clinical Progress, Therapeutic Strategies Learned)
  const [expandedSections, setExpandedSections] = React.useState<Set<string>>(() => {
    const initialSections = notesGoalsData.expanded.sections
      .slice(0, 2)
      .map((_, index) => `section-${index}`);
    return new Set(initialSections);
  });

  const handleExpand = () => {
    setIsExpanded(true);
    onExpand?.();
  };

  const handleCollapse = () => {
    setIsExpanded(false);
    onCollapse?.();
  };

  const toggleSection = (sectionId: string) => {
    setExpandedSections((prev) => {
      const next = new Set(prev);
      if (next.has(sectionId)) {
        next.delete(sectionId);
      } else {
        next.add(sectionId);
      }
      return next;
    });
  };

  // Get compact data from mock
  const { bullets, currentFocus } = notesGoalsData.compact;
  const { title: expandedTitle, sections } = notesGoalsData.expanded;

  return (
    <>
      {/* Compact Card View */}
      <motion.div
        variants={cardHoverVariants}
        initial="initial"
        whileHover="hover"
        whileTap="tap"
        onClick={handleExpand}
        className={cn(
          'rounded-2xl p-6 cursor-pointer',
          'border border-border/30',
          'transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
          className
        )}
        style={{
          boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
          // White with subtle warm tint
          background: 'linear-gradient(135deg, #FFFFFF 0%, #FFFBF7 100%)',
          borderRadius: '16px',
          padding: '24px',
        }}
        role="button"
        tabIndex={0}
        aria-label="Open notes and goals details"
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            handleExpand();
          }
        }}
      >
        {/* Header */}
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 bg-primary/10 rounded-xl">
            <FileText className="w-5 h-5 text-primary" />
          </div>
          <h3
            className="text-foreground"
            style={{
              fontFamily: 'Crimson Pro, serif',
              fontSize: '20px',
              fontWeight: 600,
            }}
          >
            Notes / Goals
          </h3>
        </div>

        {/* AI Summary Bullet Points - 3 bullets */}
        <ul className="space-y-2.5 mb-4">
          {bullets.slice(0, 3).map((bullet, index) => (
            <li
              key={index}
              className="flex items-start gap-2"
              style={{ fontFamily: 'Inter, sans-serif', fontSize: '14px' }}
            >
              <span className="w-1.5 h-1.5 rounded-full bg-primary/60 mt-2 flex-shrink-0" />
              <span className="text-foreground/80 leading-relaxed">{bullet}</span>
            </li>
          ))}
        </ul>

        {/* Current Focus Line */}
        <div className="pt-3 border-t border-border/30">
          <p
            className="text-muted-foreground"
            style={{ fontFamily: 'Inter, sans-serif', fontSize: '13px' }}
          >
            <span className="font-medium text-foreground/70">Current focus:</span>{' '}
            {currentFocus.join(', ')}
          </p>
        </div>
      </motion.div>

      {/* Expanded Modal using ModalWrapper */}
      <ModalWrapper
        isOpen={isExpanded}
        onClose={handleCollapse}
        title="Notes / Goals"
        titleIcon={<FileText className="w-6 h-6 text-primary" />}
        className="max-w-2xl"
      >
        {/* Subtitle */}
        <p
          className="text-muted-foreground mb-6 -mt-2"
          style={{ fontFamily: 'Inter, sans-serif', fontSize: '14px' }}
        >
          {expandedTitle}
        </p>

        {/* 5 Collapsible Sections */}
        <div className="space-y-0">
          {sections.map((section, index) => (
            <CollapsibleSection
              key={index}
              id={`section-${index}`}
              title={section.title}
              content={section.content}
              isExpanded={expandedSections.has(`section-${index}`)}
              onToggle={() => toggleSection(`section-${index}`)}
            />
          ))}
        </div>

        {/* Footer */}
        <div className="mt-6 pt-4 border-t border-border/30">
          <p
            className="text-xs text-muted-foreground text-center"
            style={{ fontFamily: 'Inter, sans-serif' }}
          >
            AI-generated insights based on session transcripts. Read-only view.
          </p>
        </div>
      </ModalWrapper>
    </>
  );
}

// Export types for external use
export type { NotesGoalsPanelProps };
