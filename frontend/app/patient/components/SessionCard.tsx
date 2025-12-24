'use client';

/**
 * SessionCard - Two card variants for therapy sessions
 * 1. Normal Session Card - with mood emoji (happy/neutral/sad)
 * 2. Breakthrough Session Card - with illuminated gold star + hover tooltip
 *
 * Dimensions: 329.3px × 290.5px
 * Colors:
 * - Light mode: Teal accent (#4ECDC4), Gold (#FFCA00)
 * - Dark mode: Purple accent (#7882E7), Gold (#FFE066), White emoji
 */

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { createPortal } from 'react-dom';
import { Session } from '../lib/types';
import { useTheme } from '../contexts/ThemeContext';
import { useSessionData } from '../contexts/SessionDataContext';
import { BreakthroughStar, renderMoodEmoji } from './SessionIcons';
import { LoadingOverlay } from './LoadingOverlay';

interface SessionCardProps {
  session: Session;
  onClick: () => void;
  /** DOM id for scroll targeting from Timeline */
  id?: string;
  /** Scale factor for responsive sizing (default 1.0) */
  scale?: number;
}

// Font families - matching your design
const fontSerif = '"Crimson Pro", Georgia, serif';
const fontSans = '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';

// Card dimensions - exact from your spec
const cardWidth = 329.3;
const cardHeight = 290.5;

export function SessionCard({ session, onClick, id, scale = 1.0 }: SessionCardProps) {
  const { isDark } = useTheme();
  const { loadingSessions } = useSessionData();
  const isLoading = loadingSessions.has(session.id);
  console.log(`[SessionCard Debug] Session ${session.id} isLoading:`, isLoading, 'loadingSessions size:', loadingSessions.size);

  // Color system - matching "Your Journey" card for consistency
  const colors = {
    teal: '#4ECDC4',
    purple: '#7882E7',
    cardDark: '#221e2d',      // Matches "Your Journey" gradient midpoint (from-[#2a2435] to-[#1a1625])
    cardLight: '#FFFFFF',
    borderDark: '#3d3548',    // Matches "Your Journey" border
    borderLight: '#E8E8E8',
    goldLight: '#FFCA00',
    goldDark: '#FFE066',
  };

  const cardBg = isDark ? colors.cardDark : colors.cardLight;
  const cardBorder = isDark ? colors.borderDark : colors.borderLight;
  const text = isDark ? '#e3e4e6' : '#1a1a1a';
  const mutedText = isDark ? '#969799' : '#666666';
  const accent = isDark ? colors.purple : colors.teal;
  const goldColor = isDark ? colors.goldDark : colors.goldLight;

  const isBreakthrough = !!session.milestone;

  // Extract summary from AI-generated Wave 1 analysis (with fallback to legacy field)
  const summary = session.summary || session.patientSummary || '';

  // Determine if session is still being analyzed (no Wave 1 data yet)
  const isAnalyzing = !session.topics || session.topics.length === 0;

  // Extract 1 strategy + 1 condensed action summary (45 chars max)
  const techniquesAndActions = [
    session.strategy,
    session.action_items_summary || session.actions[0] || ''  // Use summary if available, fallback to first action
  ].filter(Boolean);

  // Check if we have any strategies/actions to display
  const hasStrategiesOrActions = techniquesAndActions.length > 0;

  if (isBreakthrough) {
    // ============ BREAKTHROUGH CARD ============
    // eslint-disable-next-line react-hooks/rules-of-hooks
    const [isStarHovered, setIsStarHovered] = useState(false);

    return (
      <>
        {/* Full-screen overlay when star is hovered - rendered via portal */}
        {typeof window !== 'undefined' && isStarHovered && createPortal(
          <AnimatePresence>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              style={{
                position: 'fixed',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                backgroundColor: isDark ? 'rgba(0, 0, 0, 0.6)' : 'rgba(0, 0, 0, 0.4)',
                zIndex: 998,
                pointerEvents: 'none',
              }}
            />
          </AnimatePresence>,
          document.body
        )}

        <motion.div
          id={id}
          onClick={onClick}
          style={{
            width: `${cardWidth}px`,
            height: `${cardHeight}px`,
            backgroundColor: cardBg,
            border: isStarHovered
              ? (isDark ? `2px solid ${goldColor}` : `2px solid white`)
              : `1px solid ${cardBorder}`,
            borderRadius: '16px',
            padding: isStarHovered ? '15px 19px 19px 19px' : '16px 20px 20px 20px', // Adjust for thicker border
            position: 'relative',
            overflow: isLoading ? 'hidden' : 'visible', // Hidden when loading to contain overlay, visible for tooltip
            boxSizing: 'border-box',
            display: 'flex',
            flexDirection: 'column',
            cursor: 'pointer',
            transform: `scale(${scale})`,
            transformOrigin: 'center center',
            zIndex: isStarHovered ? 999 : 'auto', // Elevate above overlay
            boxShadow: isStarHovered
              ? (isDark ? `0 8px 32px rgba(0,0,0,0.5), 0 0 0 4px ${goldColor}40` : '0 8px 32px rgba(0,0,0,0.3), 0 0 0 4px rgba(255,255,255,0.8)')
              : 'none',
          }}
          whileHover={{ scale: 1.01, boxShadow: isStarHovered ? undefined : '0 4px 16px rgba(0,0,0,0.12)' }}
          transition={{ duration: 0.2 }}
          role="button"
          tabIndex={0}
          aria-label={`Breakthrough session on ${session.date}`}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              onClick();
            }
          }}
        >

        {/* Header Row */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '16px',
          width: '100%',
          flexShrink: 0,
        }}>
          <span style={{
            fontFamily: fontSans,
            color: mutedText,
            fontSize: '13px',
            fontWeight: 500,
            flexShrink: 0,
          }}>
            {session.duration}
          </span>
          <span style={{
            fontFamily: fontSerif,
            color: text,
            fontSize: '20px',
            fontWeight: 600,
            flexShrink: 0,
          }}>
            {session.date}
          </span>

          {/* Illuminated Star with Hover Tooltip */}
          <div
            style={{
              position: 'relative',
              flexShrink: 0,
              zIndex: 2,
              width: '24px', // Explicit width matching star size
              height: '24px', // Explicit height matching star size
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
            onMouseEnter={(e) => {
              e.stopPropagation();
              setIsStarHovered(true);
            }}
            onMouseLeave={(e) => {
              e.stopPropagation();
              setIsStarHovered(false);
            }}
            onClick={(e) => {
              e.stopPropagation(); // Prevent card click when clicking star area
            }}
          >
            {/* Tooltip above star */}
            <AnimatePresence>
              {isStarHovered && (
                <motion.div
                  initial={{ opacity: 0, y: 5, x: '-50%' }}
                  animate={{ opacity: 1, y: 0, x: '-50%' }}
                  exit={{ opacity: 0, y: 5, x: '-50%' }}
                  transition={{ duration: 0.2 }}
                  style={{
                    position: 'absolute',
                    bottom: 'calc(100% + 6px)', // 6px above the star
                    left: '50%',
                    backgroundColor: isDark ? 'rgba(0, 0, 0, 0.95)' : 'rgba(0, 0, 0, 0.9)',
                    padding: '10px 16px',
                    borderRadius: '8px',
                    whiteSpace: 'nowrap',
                    pointerEvents: 'none',
                    boxShadow: `0 4px 20px ${goldColor}80, 0 0 40px ${goldColor}40`,
                    border: `1px solid ${goldColor}60`,
                    zIndex: 1000,
                  }}
                >
                  <p style={{
                    fontFamily: fontSerif,
                    color: goldColor,
                    fontSize: '14px',
                    fontWeight: 700,
                    lineHeight: 1.4,
                    margin: 0,
                    filter: `drop-shadow(0 0 8px ${goldColor}90)`,
                    textShadow: `0 0 10px ${goldColor}80`,
                  }}>
                    {session.milestone?.title}
                  </p>
                  {/* Tooltip arrow */}
                  <div style={{
                    position: 'absolute',
                    top: '100%',
                    left: '50%',
                    transform: 'translateX(-50%)',
                    width: 0,
                    height: 0,
                    borderLeft: '6px solid transparent',
                    borderRight: '6px solid transparent',
                    borderTop: `6px solid ${isDark ? 'rgba(0, 0, 0, 0.95)' : 'rgba(0, 0, 0, 0.9)'}`,
                  }} />
                </motion.div>
              )}
            </AnimatePresence>

            {/* Illuminated Star - subtle glow, clearer outline */}
            <motion.div
              animate={{
                filter: isStarHovered
                  ? `drop-shadow(0 0 4px ${goldColor}60) drop-shadow(0 0 8px ${goldColor}40) brightness(1.1)`
                  : `drop-shadow(0 0 2px ${goldColor}50) drop-shadow(0 0 4px ${goldColor}30) brightness(1.0)`,
              }}
              transition={{ duration: 0.2 }}
            >
              <BreakthroughStar size={24} isDark={isDark} />
            </motion.div>
          </div>
        </div>

        {/* Session Summary - same position as normal cards */}
        <div style={{ marginBottom: '16px', flex: 1, overflow: 'hidden' }}>
          <h3 style={{
            fontFamily: fontSans,
            color: mutedText,
            fontSize: '11px',
            fontWeight: 500,
            textTransform: 'uppercase',
            letterSpacing: '1px',
            margin: '0 0 8px 0',
          }}>
            Session Summary
          </h3>
          {isAnalyzing || !summary ? (
            <p style={{
              fontFamily: fontSerif,
              color: mutedText,
              fontSize: '14px',
              fontWeight: 400,
              fontStyle: 'italic',
              lineHeight: 1.6,
              margin: 0,
            }}>
              Analyzing...
            </p>
          ) : (
            <p style={{
              fontFamily: fontSerif,
              color: text,
              fontSize: '14px',
              fontWeight: 400,
              lineHeight: 1.6,
              margin: 0,
              wordWrap: 'break-word',
              overflowWrap: 'break-word',
              display: '-webkit-box',
              WebkitLineClamp: 3,
              WebkitBoxOrient: 'vertical',
              overflow: 'hidden',
            }}>
              {summary}
            </p>
          )}
        </div>

        {/* Divider */}
        <div style={{
          height: '1px',
          backgroundColor: cardBorder,
          margin: '0 0 12px 0',
          width: '100%',
          flexShrink: 0,
        }} />

        {/* Strategies / Action Items - same position as normal cards */}
        <div style={{ flexShrink: 0 }}>
          <h3 style={{
            fontFamily: fontSans,
            color: mutedText,
            fontSize: '11px',
            fontWeight: 500,
            textTransform: 'uppercase',
            letterSpacing: '1px',
            margin: '0 0 8px 0',
          }}>
            Strategies / Action Items
          </h3>
          {!hasStrategiesOrActions ? (
            <p style={{
              fontFamily: fontSerif,
              color: mutedText,
              fontSize: '13px',
              fontWeight: 300,
              fontStyle: 'italic',
              margin: 0,
            }}>
              Analyzing...
            </p>
          ) : (
            <ul style={{
              margin: 0,
              paddingLeft: '0',
              listStyle: 'none',
            }}>
              {techniquesAndActions.map((item, i) => (
                <li key={i} style={{
                  fontFamily: fontSerif,
                  color: accent,
                  fontSize: '13px',
                  fontWeight: 300,
                  lineHeight: 1.5,
                  marginBottom: '6px',
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '8px',
                }}>
                  <span style={{ color: accent, flexShrink: 0 }}>•</span>
                  <span style={{
                    flex: 1,
                    minWidth: 0,
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                  }}>
                    {item}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Loading Overlay */}
        <LoadingOverlay visible={isLoading} />
      </motion.div>
      </>
    );
  }

  // ============ NORMAL CARD ============
  return (
    <motion.div
      id={id}
      onClick={onClick}
      style={{
        width: `${cardWidth}px`,
        height: `${cardHeight}px`,
        backgroundColor: cardBg,
        border: `1px solid ${cardBorder}`,
        borderRadius: '16px',
        padding: '16px 20px 20px 20px',
        position: 'relative',
        overflow: 'hidden',
        boxSizing: 'border-box',
        display: 'flex',
        flexDirection: 'column',
        cursor: 'pointer',
        transform: `scale(${scale})`,
        transformOrigin: 'center center',
      }}
      whileHover={{ scale: 1.01, boxShadow: '0 4px 16px rgba(0,0,0,0.12)' }}
      transition={{ duration: 0.2 }}
      role="button"
      tabIndex={0}
      aria-label={`Session on ${session.date}, mood ${session.mood}`}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onClick();
        }
      }}
    >
      {/* Header Row */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '16px',
        width: '100%',
        flexShrink: 0,
      }}>
        <span style={{
          fontFamily: fontSans,
          color: mutedText,
          fontSize: '13px',
          fontWeight: 500,
          flexShrink: 0,
        }}>
          {session.duration}
        </span>
        <span style={{
          fontFamily: fontSerif,
          color: text,
          fontSize: '20px',
          fontWeight: 600,
          flexShrink: 0,
        }}>
          {session.date}
        </span>
        <div style={{ flexShrink: 0 }}>
          {renderMoodEmoji(session.mood, 24, isDark)}
        </div>
      </div>

      {/* Session Summary */}
      <div style={{ marginBottom: '16px', flex: 1, overflow: 'hidden' }}>
        <h3 style={{
          fontFamily: fontSans,
          color: mutedText,
          fontSize: '11px',
          fontWeight: 500,
          textTransform: 'uppercase',
          letterSpacing: '1px',
          margin: '0 0 8px 0',
        }}>
          Session Summary
        </h3>
        {isAnalyzing || !summary ? (
          <p style={{
            fontFamily: fontSerif,
            color: mutedText,
            fontSize: '14px',
            fontWeight: 400,
            fontStyle: 'italic',
            lineHeight: 1.6,
            margin: 0,
          }}>
            Analyzing...
          </p>
        ) : (
          <p style={{
            fontFamily: fontSerif,
            color: text,
            fontSize: '14px',
            fontWeight: 400,
            lineHeight: 1.6,
            margin: 0,
            wordWrap: 'break-word',
            overflowWrap: 'break-word',
            display: '-webkit-box',
            WebkitLineClamp: 3,
            WebkitBoxOrient: 'vertical',
            overflow: 'hidden',
          }}>
            {summary}
          </p>
        )}
      </div>

      {/* Divider */}
      <div style={{
        height: '1px',
        backgroundColor: cardBorder,
        margin: '0 0 12px 0',
        width: '100%',
        flexShrink: 0,
      }} />

      {/* Strategies / Action Items */}
      <div style={{ flexShrink: 0 }}>
        <h3 style={{
          fontFamily: fontSans,
          color: mutedText,
          fontSize: '11px',
          fontWeight: 500,
          textTransform: 'uppercase',
          letterSpacing: '1px',
          margin: '0 0 8px 0',
        }}>
          Strategies / Action Items
        </h3>
        {!hasStrategiesOrActions ? (
          <p style={{
            fontFamily: fontSerif,
            color: mutedText,
            fontSize: '13px',
            fontWeight: 300,
            fontStyle: 'italic',
            margin: 0,
          }}>
            Analyzing...
          </p>
        ) : (
          <ul style={{
            margin: 0,
            paddingLeft: '0',
            listStyle: 'none',
          }}>
            {techniquesAndActions.map((item, i) => (
              <li key={i} style={{
                fontFamily: fontSerif,
                color: accent,
                fontSize: '13px',
                fontWeight: 300,
                lineHeight: 1.5,
                marginBottom: '6px',
                display: 'flex',
                alignItems: 'flex-start',
                gap: '8px',
              }}>
                <span style={{ color: accent, flexShrink: 0 }}>•</span>
                <span style={{
                  flex: 1,
                  minWidth: 0,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}>
                  {item}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Loading Overlay */}
      <LoadingOverlay visible={isLoading} />
    </motion.div>
  );
}
