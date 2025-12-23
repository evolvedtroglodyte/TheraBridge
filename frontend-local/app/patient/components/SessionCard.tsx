'use client';

/**
 * SessionCard - Two card variants for therapy sessions
 * 1. Normal Session Card - with mood emoji (happy/neutral/sad)
 * 2. Breakthrough Session Card - with gold star and breakthrough section
 *
 * Dimensions: 329.3px × 290.5px
 * Colors:
 * - Light mode: Teal accent (#4ECDC4), Gold (#FFCA00)
 * - Dark mode: Purple accent (#7882E7), Gold (#FFE066), White emoji
 */

import { motion } from 'framer-motion';
import { Session } from '../lib/types';
import { useTheme } from '../contexts/ThemeContext';
import { BreakthroughStar, renderMoodEmoji } from './SessionIcons';

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

  // Color system matching your exact design
  const colors = {
    teal: '#4ECDC4',
    purple: '#7882E7',
    cardDark: '#1e2025',
    cardLight: '#FFFFFF',
    borderDark: '#2c2e33',
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

  // Extract summary from patientSummary (first 200 chars)
  const summary = session.patientSummary || 'Session summary not available.';

  // Extract techniques/actions (limit to 2)
  const techniquesAndActions = session.actions.slice(0, 2);

  if (isBreakthrough) {
    // ============ BREAKTHROUGH CARD ============
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
        whileHover={{ scale: scale * 1.01, boxShadow: '0 4px 16px rgba(0,0,0,0.12)' }}
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
          marginBottom: '12px',
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
            <BreakthroughStar size={24} isDark={isDark} />
          </div>
        </div>

        {/* Breakthrough Section */}
        <div style={{ marginBottom: '12px', flexShrink: 0 }}>
          <h3 style={{
            fontFamily: fontSans,
            color: goldColor,
            fontSize: '11px',
            fontWeight: 500,
            textTransform: 'uppercase',
            letterSpacing: '1px',
            margin: '0 0 6px 0',
            filter: `drop-shadow(0 0 6px ${goldColor}90)`,
          }}>
            Breakthrough
          </h3>
          <p style={{
            fontFamily: fontSerif,
            color: goldColor,
            fontSize: '13px',
            fontWeight: 400,
            lineHeight: 1.5,
            margin: 0,
            filter: `drop-shadow(0 0 4px ${goldColor}70)`,
            wordWrap: 'break-word',
            overflowWrap: 'break-word',
            display: '-webkit-box',
            WebkitLineClamp: 2,
            WebkitBoxOrient: 'vertical',
            overflow: 'hidden',
          }}>
            {session.milestone?.title}
          </p>
        </div>

        {/* Session Summary */}
        <div style={{ marginBottom: '12px', flex: 1, overflow: 'hidden' }}>
          <h3 style={{
            fontFamily: fontSans,
            color: mutedText,
            fontSize: '11px',
            fontWeight: 500,
            textTransform: 'uppercase',
            letterSpacing: '1px',
            margin: '0 0 6px 0',
          }}>
            Session Summary
          </h3>
          <p style={{
            fontFamily: fontSerif,
            color: text,
            fontSize: '13px',
            fontWeight: 400,
            lineHeight: 1.5,
            margin: 0,
            wordWrap: 'break-word',
            overflowWrap: 'break-word',
            display: '-webkit-box',
            WebkitLineClamp: 2,
            WebkitBoxOrient: 'vertical',
            overflow: 'hidden',
          }}>
            {summary}
          </p>
        </div>

        {/* Divider */}
        <div style={{
          height: '1px',
          backgroundColor: cardBorder,
          margin: '0 0 10px 0',
          width: '100%',
          flexShrink: 0,
        }} />

        {/* Techniques / Action Items */}
        <div style={{ flexShrink: 0 }}>
          <h3 style={{
            fontFamily: fontSans,
            color: mutedText,
            fontSize: '11px',
            fontWeight: 500,
            textTransform: 'uppercase',
            letterSpacing: '1px',
            margin: '0 0 6px 0',
          }}>
            Techniques / Action Items
          </h3>
          <ul style={{
            margin: 0,
            paddingLeft: '0',
            listStyle: 'none',
          }}>
            {techniquesAndActions.map((item, i) => (
              <li key={i} style={{
                fontFamily: fontSerif,
                color: accent,
                fontSize: '12px',
                fontWeight: 300,
                lineHeight: 1.4,
                marginBottom: '4px',
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
        </div>
      </motion.div>
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
      whileHover={{ scale: scale * 1.01, boxShadow: '0 4px 16px rgba(0,0,0,0.12)' }}
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
      </div>

      {/* Divider */}
      <div style={{
        height: '1px',
        backgroundColor: cardBorder,
        margin: '0 0 12px 0',
        width: '100%',
        flexShrink: 0,
      }} />

      {/* Techniques / Action Items */}
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
          Techniques / Action Items
        </h3>
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
      </div>
    </motion.div>
  );
}
