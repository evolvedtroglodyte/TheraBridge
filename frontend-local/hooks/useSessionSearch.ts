'use client';

import { useState, useMemo, useCallback } from 'react';
import type { Session } from '@/lib/types';

/**
 * Hook for debounced session search and filtering
 * Searches across session dates and related patient names
 */
export function useSessionSearch(sessions: Session[] | undefined, patientName?: string) {
  const [searchQuery, setSearchQuery] = useState('');

  // Filter sessions based on search query with debounced search
  const filteredSessions = useMemo(() => {
    if (!sessions) return [];
    if (!searchQuery.trim()) return sessions;

    const query = searchQuery.toLowerCase().trim();

    return sessions.filter((session) => {
      // Search by session date
      const sessionDate = new Date(session.session_date);
      const formattedDate = sessionDate.toLocaleDateString('en-US');
      const shortDate = sessionDate.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      });

      if (formattedDate.toLowerCase().includes(query) || shortDate.toLowerCase().includes(query)) {
        return true;
      }

      // Search by patient name (if provided)
      if (patientName && patientName.toLowerCase().includes(query)) {
        return true;
      }

      // Search by extracted notes content (topic summary, key topics)
      if (session.extracted_notes) {
        const topicSummary = session.extracted_notes.topic_summary?.toLowerCase() || '';
        const keyTopics = session.extracted_notes.key_topics?.join(' ').toLowerCase() || '';

        if (topicSummary.includes(query) || keyTopics.includes(query)) {
          return true;
        }
      }

      return false;
    });
  }, [sessions, searchQuery, patientName]);

  const handleSearchChange = useCallback((value: string) => {
    setSearchQuery(value);
  }, []);

  const clearSearch = useCallback(() => {
    setSearchQuery('');
  }, []);

  return {
    searchQuery,
    filteredSessions,
    handleSearchChange,
    clearSearch,
    hasActiveSearch: searchQuery.trim().length > 0,
    resultCount: filteredSessions.length,
  };
}
