"use client";

import React, { useState } from "react";
import { motion } from "framer-motion";
import { MessageCircle, TrendingUp, ClipboardList } from "lucide-react";
import { cn } from "@/lib/utils";
import { ModalWrapper } from "@/components/dashboard-v2/shared";
import { therapistBridgeData } from "@/lib/mock-data/dashboard-v2";

// ============================================================================
// Types
// ============================================================================

interface TherapistBridgeItem {
  id: string;
  text: string;
  context?: string;
}

interface TherapistBridgeSection {
  title: string;
  items: TherapistBridgeItem[];
}

interface TherapistBridgeData {
  compact: {
    conversationStarters: TherapistBridgeItem;
    shareProgress: TherapistBridgeItem;
    sessionPrep: TherapistBridgeItem;
  };
  expanded: {
    conversationStarters: TherapistBridgeSection;
    shareProgress: TherapistBridgeSection;
    sessionPrep: TherapistBridgeSection;
    nextSessionDate: string;
  };
}

interface TherapistBridgeCardProps {
  data?: TherapistBridgeData;
  className?: string;
}

// ============================================================================
// Animation Variants
// ============================================================================

const sectionVariants = {
  hidden: { opacity: 0, y: 10 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.1, duration: 0.3 },
  }),
};

// ============================================================================
// Component
// ============================================================================

export function TherapistBridgeCard({
  data = therapistBridgeData,
  className,
}: TherapistBridgeCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <>
      {/* Compact Card - Pill-shaped with warm gradient */}
      <motion.div
        className={cn(
          "relative overflow-hidden cursor-pointer",
          "rounded-[20px] p-5",
          // Soft gradient with warm tint
          "bg-gradient-to-br from-amber-50/90 via-orange-50/80 to-rose-50/70",
          "dark:from-amber-950/30 dark:via-orange-950/20 dark:to-rose-950/20",
          "border border-amber-100/50 dark:border-amber-800/30",
          className
        )}
        style={{
          // Soft glow shadow as specified
          boxShadow: "0 2px 16px rgba(91, 185, 180, 0.15)",
        }}
        initial={{ y: 0 }}
        whileHover={{
          y: -2,
          transition: { duration: 0.2, ease: 'easeOut' }
        }}
        whileTap={{ scale: 0.99 }}
        onClick={() => setIsExpanded(true)}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            setIsExpanded(true);
          }
        }}
        aria-label="Open therapist bridge details"
        aria-expanded={isExpanded}
      >
        {/* Header */}
        <div className="flex items-center gap-2 mb-4">
          <div className="p-2 rounded-full bg-teal-100/60 dark:bg-teal-900/40">
            <MessageCircle className="w-4 h-4 text-teal-600 dark:text-teal-400" />
          </div>
          <h3
            className="font-light text-base text-gray-800 dark:text-gray-200 tracking-wide"
            style={{ fontFamily: "Inter, sans-serif" }}
          >
            Therapist Bridge
          </h3>
        </div>

        {/* Compact Sections - 3 sections stacked (no carousel) */}
        <div className="space-y-4">
          {/* Next Session Topics */}
          <CompactSection
            icon={<MessageCircle className="w-3.5 h-3.5" />}
            title="Next Session Topics"
            items={[data.compact.conversationStarters.text]}
            accentColor="teal"
          />

          {/* Share Progress */}
          <CompactSection
            icon={<TrendingUp className="w-3.5 h-3.5" />}
            title="Share Progress"
            items={[data.compact.shareProgress.text]}
            accentColor="emerald"
          />

          {/* Session Prep */}
          <CompactSection
            icon={<ClipboardList className="w-3.5 h-3.5" />}
            title="Session Prep"
            items={[data.compact.sessionPrep.text]}
            accentColor="amber"
          />
        </div>

        {/* Expand hint */}
        <div className="mt-4 text-center">
          <span
            className="text-xs font-light text-gray-400 dark:text-gray-500"
            style={{ fontFamily: "Inter, sans-serif" }}
          >
            Tap for full details
          </span>
        </div>
      </motion.div>

      {/* Expanded Modal using ModalWrapper */}
      <ModalWrapper
        isOpen={isExpanded}
        onClose={() => setIsExpanded(false)}
        title="Therapist Bridge"
        titleIcon={<MessageCircle className="w-5 h-5 text-teal-600 dark:text-teal-400" />}
        className={cn(
          "max-w-lg",
          "bg-gradient-to-br from-amber-50 via-orange-50 to-rose-50",
          "dark:from-gray-900 dark:via-gray-900 dark:to-gray-900"
        )}
      >
        {/* Next Session Date */}
        <div className="mb-6 text-center">
          <p
            className="text-sm font-light text-gray-500 dark:text-gray-400"
            style={{ fontFamily: "Inter, sans-serif" }}
          >
            Next Session: {data.expanded.nextSessionDate}
          </p>
        </div>

        {/* Expanded Sections - Full detail, read-only text */}
        <div className="space-y-6">
          {/* Conversation Starters */}
          <motion.div
            custom={0}
            variants={sectionVariants}
            initial="hidden"
            animate="visible"
          >
            <ExpandedSection
              icon={<MessageCircle className="w-4 h-4" />}
              title={data.expanded.conversationStarters.title}
              accentColor="teal"
            >
              <div className="space-y-3">
                {data.expanded.conversationStarters.items.map((item) => (
                  <div
                    key={item.id}
                    className="p-3 rounded-xl bg-white/60 dark:bg-gray-800/40 border border-teal-100/30 dark:border-teal-800/20"
                  >
                    <p
                      className="font-light text-sm text-gray-800 dark:text-gray-200 mb-1"
                      style={{ fontFamily: "Inter, sans-serif" }}
                    >
                      {item.text}
                    </p>
                    {item.context && (
                      <p
                        className="text-xs font-light text-gray-500 dark:text-gray-400"
                        style={{ fontFamily: "Inter, sans-serif" }}
                      >
                        {item.context}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </ExpandedSection>
          </motion.div>

          {/* Share Progress */}
          <motion.div
            custom={1}
            variants={sectionVariants}
            initial="hidden"
            animate="visible"
          >
            <ExpandedSection
              icon={<TrendingUp className="w-4 h-4" />}
              title={data.expanded.shareProgress.title}
              accentColor="emerald"
            >
              <div className="space-y-3">
                {data.expanded.shareProgress.items.map((item) => (
                  <div
                    key={item.id}
                    className="p-3 rounded-xl bg-white/60 dark:bg-gray-800/40 border border-emerald-100/30 dark:border-emerald-800/20"
                  >
                    <p
                      className="font-light text-sm text-gray-800 dark:text-gray-200"
                      style={{ fontFamily: "Inter, sans-serif" }}
                    >
                      {item.text}
                    </p>
                    {item.context && (
                      <p
                        className="text-xs font-light text-gray-500 dark:text-gray-400 mt-1"
                        style={{ fontFamily: "Inter, sans-serif" }}
                      >
                        {item.context}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </ExpandedSection>
          </motion.div>

          {/* Session Prep */}
          <motion.div
            custom={2}
            variants={sectionVariants}
            initial="hidden"
            animate="visible"
          >
            <ExpandedSection
              icon={<ClipboardList className="w-4 h-4" />}
              title={data.expanded.sessionPrep.title}
              accentColor="amber"
            >
              <div className="space-y-3">
                {data.expanded.sessionPrep.items.map((item) => (
                  <div
                    key={item.id}
                    className="p-3 rounded-xl bg-white/60 dark:bg-gray-800/40 border border-amber-100/30 dark:border-amber-800/20"
                  >
                    <p
                      className="font-light text-sm text-gray-800 dark:text-gray-200"
                      style={{ fontFamily: "Inter, sans-serif" }}
                    >
                      {item.text}
                    </p>
                    {item.context && (
                      <p
                        className="text-xs font-light text-gray-500 dark:text-gray-400 mt-1"
                        style={{ fontFamily: "Inter, sans-serif" }}
                      >
                        {item.context}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </ExpandedSection>
          </motion.div>
        </div>
      </ModalWrapper>
    </>
  );
}

// ============================================================================
// Sub-Components
// ============================================================================

interface CompactSectionProps {
  icon: React.ReactNode;
  title: string;
  items: string[];
  accentColor: "teal" | "emerald" | "amber";
}

function CompactSection({ icon, title, items, accentColor }: CompactSectionProps) {
  const accentClasses = {
    teal: "text-teal-600 dark:text-teal-400",
    emerald: "text-emerald-600 dark:text-emerald-400",
    amber: "text-amber-600 dark:text-amber-400",
  };

  return (
    <div className="space-y-1.5">
      <div className="flex items-center gap-1.5">
        <span className={cn("opacity-70", accentClasses[accentColor])}>{icon}</span>
        <span
          className="text-xs font-light text-gray-500 dark:text-gray-400 uppercase tracking-wider"
          style={{ fontFamily: "Inter, sans-serif" }}
        >
          {title}
        </span>
      </div>
      <ul className="space-y-1 pl-5">
        {items.map((item, idx) => (
          <li
            key={idx}
            className="text-sm font-light text-gray-700 dark:text-gray-300 leading-relaxed"
            style={{ fontFamily: "Inter, sans-serif" }}
          >
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}

interface ExpandedSectionProps {
  icon: React.ReactNode;
  title: string;
  accentColor: "teal" | "emerald" | "amber";
  children: React.ReactNode;
}

function ExpandedSection({ icon, title, accentColor, children }: ExpandedSectionProps) {
  const accentClasses = {
    teal: "text-teal-600 dark:text-teal-400 bg-teal-100/50 dark:bg-teal-900/30",
    emerald: "text-emerald-600 dark:text-emerald-400 bg-emerald-100/50 dark:bg-emerald-900/30",
    amber: "text-amber-600 dark:text-amber-400 bg-amber-100/50 dark:bg-amber-900/30",
  };

  const iconBg = accentClasses[accentColor].split(" ").slice(1).join(" ");
  const iconText = accentClasses[accentColor].split(" ")[0];

  return (
    <div>
      <div className="flex items-center gap-2 mb-3">
        <div className={cn("p-1.5 rounded-full", iconBg)}>
          <span className={iconText}>{icon}</span>
        </div>
        <h3
          className="text-sm font-medium text-gray-700 dark:text-gray-300 uppercase tracking-wider"
          style={{ fontFamily: "Inter, sans-serif" }}
        >
          {title}
        </h3>
      </div>
      {children}
    </div>
  );
}

export default TherapistBridgeCard;
