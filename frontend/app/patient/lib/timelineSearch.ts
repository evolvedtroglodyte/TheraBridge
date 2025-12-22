/**
 * Timeline Search Utilities
 *
 * Provides search/filter functionality for the unified timeline.
 * Searches across sessions and major events with different field targets.
 */

import { TimelineEvent, SessionTimelineEvent, MajorEventEntry } from './types';

/**
 * Fields to search for each event type
 */
const SESSION_SEARCH_FIELDS: (keyof SessionTimelineEvent)[] = [
  'topic',
  'strategy',
  'date',
];

const MAJOR_EVENT_SEARCH_FIELDS: (keyof MajorEventEntry)[] = [
  'title',
  'summary',
  'date',
];

/**
 * Check if a string field contains the search query (case-insensitive)
 */
function fieldContainsQuery(value: unknown, query: string): boolean {
  if (typeof value !== 'string') return false;
  return value.toLowerCase().includes(query.toLowerCase());
}

/**
 * Check if a session event matches the search query
 */
function sessionMatchesQuery(event: SessionTimelineEvent, query: string): boolean {
  // Check standard fields
  for (const field of SESSION_SEARCH_FIELDS) {
    if (fieldContainsQuery(event[field], query)) {
      return true;
    }
  }

  // Check milestone title if present
  if (event.milestone && fieldContainsQuery(event.milestone.title, query)) {
    return true;
  }

  return false;
}

/**
 * Check if a major event matches the search query
 */
function majorEventMatchesQuery(event: MajorEventEntry, query: string): boolean {
  for (const field of MAJOR_EVENT_SEARCH_FIELDS) {
    if (fieldContainsQuery(event[field], query)) {
      return true;
    }
  }
  return false;
}

/**
 * Filter timeline events by search query.
 *
 * @param events - The unified timeline to filter
 * @param query - The search query string
 * @returns Filtered array of events matching the query
 *
 * @example
 * const results = filterTimelineByQuery(unifiedTimeline, 'boundary');
 * // Returns events with 'boundary' in topic, title, summary, etc.
 */
export function filterTimelineByQuery(
  events: TimelineEvent[],
  query: string
): TimelineEvent[] {
  // Return all events if query is empty
  const trimmedQuery = query.trim();
  if (!trimmedQuery) {
    return events;
  }

  return events.filter((event) => {
    if (event.eventType === 'session') {
      return sessionMatchesQuery(event, trimmedQuery);
    } else {
      return majorEventMatchesQuery(event, trimmedQuery);
    }
  });
}

/**
 * Highlight matching text in a string.
 * Returns JSX-safe segments for rendering.
 *
 * @param text - The text to highlight
 * @param query - The search query
 * @returns Array of segments with highlight flags
 */
export interface HighlightSegment {
  text: string;
  isHighlight: boolean;
}

export function getHighlightSegments(
  text: string,
  query: string
): HighlightSegment[] {
  if (!query.trim()) {
    return [{ text, isHighlight: false }];
  }

  const segments: HighlightSegment[] = [];
  const lowerText = text.toLowerCase();
  const lowerQuery = query.toLowerCase().trim();

  let lastIndex = 0;
  let index = lowerText.indexOf(lowerQuery);

  while (index !== -1) {
    // Add non-matching segment before this match
    if (index > lastIndex) {
      segments.push({
        text: text.slice(lastIndex, index),
        isHighlight: false,
      });
    }

    // Add matching segment
    segments.push({
      text: text.slice(index, index + query.length),
      isHighlight: true,
    });

    lastIndex = index + query.length;
    index = lowerText.indexOf(lowerQuery, lastIndex);
  }

  // Add remaining non-matching segment
  if (lastIndex < text.length) {
    segments.push({
      text: text.slice(lastIndex),
      isHighlight: false,
    });
  }

  return segments.length > 0 ? segments : [{ text, isHighlight: false }];
}
