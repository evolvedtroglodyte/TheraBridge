/**
 * Timeline Export Utilities
 *
 * Provides PDF generation and shareable link functionality for the patient timeline.
 * Uses html2pdf.js for client-side PDF generation.
 */

import { TimelineEvent, SessionTimelineEvent, MajorEventEntry } from './types';

// ============================================
// Types
// ============================================

export interface ExportOptions {
  title?: string;
  includeReflections?: boolean;
  dateRange?: { start: Date; end: Date };
}

export interface TimelineStats {
  sessionCount: number;
  majorEventCount: number;
  milestoneCount: number;
  dateRange: string;
}

// ============================================
// Stats Calculation
// ============================================

/**
 * Calculate summary statistics for the timeline
 */
export function calculateTimelineStats(events: TimelineEvent[]): TimelineStats {
  const sessions = events.filter((e): e is SessionTimelineEvent => e.eventType === 'session');
  const majorEvents = events.filter((e): e is MajorEventEntry => e.eventType === 'major_event');
  const milestones = sessions.filter(s => s.milestone);

  // Get date range
  const dates = events.map(e => e.timestamp).sort((a, b) => a.getTime() - b.getTime());
  const earliest = dates[0];
  const latest = dates[dates.length - 1];

  const formatDate = (d: Date) => d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  const dateRange = earliest && latest
    ? `${formatDate(earliest)} - ${formatDate(latest)}`
    : 'No data';

  return {
    sessionCount: sessions.length,
    majorEventCount: majorEvents.length,
    milestoneCount: milestones.length,
    dateRange,
  };
}

// ============================================
// HTML Generation for PDF
// ============================================

/**
 * Generate HTML content for PDF export.
 * This creates a clean, printable layout.
 */
export function generatePdfHtml(
  events: TimelineEvent[],
  options: ExportOptions = {}
): string {
  const { title = 'My Therapy Journey', includeReflections = true } = options;
  const stats = calculateTimelineStats(events);

  const entriesHtml = events.map(event => {
    if (event.eventType === 'session') {
      return generateSessionEntryHtml(event);
    } else {
      return generateMajorEventEntryHtml(event, includeReflections);
    }
  }).join('');

  return `
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        * {
          margin: 0;
          padding: 0;
          box-sizing: border-box;
        }
        body {
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
          color: #374151;
          line-height: 1.5;
          padding: 40px;
        }
        .header {
          margin-bottom: 30px;
          padding-bottom: 20px;
          border-bottom: 2px solid #e5e7eb;
        }
        .title {
          font-size: 28px;
          font-weight: 300;
          color: #111827;
          margin-bottom: 8px;
        }
        .subtitle {
          font-size: 14px;
          color: #6b7280;
        }
        .stats {
          display: flex;
          gap: 24px;
          margin-top: 16px;
        }
        .stat {
          text-align: center;
        }
        .stat-value {
          font-size: 24px;
          font-weight: 600;
          color: #5AB9B4;
        }
        .stat-label {
          font-size: 12px;
          color: #6b7280;
          text-transform: uppercase;
        }
        .timeline {
          margin-top: 30px;
        }
        .entry {
          padding: 16px 0;
          border-bottom: 1px solid #f3f4f6;
          page-break-inside: avoid;
        }
        .entry:last-child {
          border-bottom: none;
        }
        .entry-header {
          display: flex;
          align-items: center;
          gap: 12px;
          margin-bottom: 8px;
        }
        .entry-type {
          display: inline-block;
          padding: 2px 8px;
          border-radius: 4px;
          font-size: 11px;
          font-weight: 500;
          text-transform: uppercase;
        }
        .entry-type.session {
          background: #dbeafe;
          color: #1e40af;
        }
        .entry-type.event {
          background: #f3e8ff;
          color: #7c3aed;
        }
        .entry-type.milestone {
          background: #fef3c7;
          color: #92400e;
        }
        .entry-date {
          font-size: 14px;
          color: #6b7280;
        }
        .entry-title {
          font-size: 16px;
          font-weight: 500;
          color: #111827;
          margin-bottom: 4px;
        }
        .entry-details {
          font-size: 14px;
          color: #6b7280;
        }
        .entry-reflection {
          margin-top: 12px;
          padding: 12px;
          background: #faf5ff;
          border-left: 3px solid #a78bfa;
          font-style: italic;
          font-size: 14px;
          color: #4b5563;
        }
        .milestone-badge {
          margin-top: 8px;
          padding: 8px 12px;
          background: #fffbeb;
          border-radius: 6px;
          font-size: 13px;
          color: #92400e;
        }
        .footer {
          margin-top: 40px;
          padding-top: 20px;
          border-top: 1px solid #e5e7eb;
          font-size: 12px;
          color: #9ca3af;
          text-align: center;
        }
      </style>
    </head>
    <body>
      <div class="header">
        <h1 class="title">${title}</h1>
        <p class="subtitle">${stats.dateRange}</p>
        <div class="stats">
          <div class="stat">
            <div class="stat-value">${stats.sessionCount}</div>
            <div class="stat-label">Sessions</div>
          </div>
          <div class="stat">
            <div class="stat-value">${stats.majorEventCount}</div>
            <div class="stat-label">Major Events</div>
          </div>
          <div class="stat">
            <div class="stat-value">${stats.milestoneCount}</div>
            <div class="stat-label">Milestones</div>
          </div>
        </div>
      </div>

      <div class="timeline">
        ${entriesHtml}
      </div>

      <div class="footer">
        Generated on ${new Date().toLocaleDateString('en-US', {
          month: 'long',
          day: 'numeric',
          year: 'numeric'
        })}
      </div>
    </body>
    </html>
  `;
}

function generateSessionEntryHtml(event: SessionTimelineEvent): string {
  const hasMilestone = !!event.milestone;
  const typeClass = hasMilestone ? 'milestone' : 'session';
  const typeLabel = hasMilestone ? 'Milestone' : 'Session';

  return `
    <div class="entry">
      <div class="entry-header">
        <span class="entry-type ${typeClass}">${typeLabel}</span>
        <span class="entry-date">${event.date}</span>
      </div>
      <div class="entry-title">${event.topic}</div>
      <div class="entry-details">
        ${event.strategy} • ${event.duration}
      </div>
      ${hasMilestone ? `
        <div class="milestone-badge">
          ⭐ ${event.milestone!.title}
        </div>
      ` : ''}
    </div>
  `;
}

function generateMajorEventEntryHtml(event: MajorEventEntry, includeReflection: boolean): string {
  return `
    <div class="entry">
      <div class="entry-header">
        <span class="entry-type event">Major Event</span>
        <span class="entry-date">${event.date}</span>
      </div>
      <div class="entry-title">${event.title}</div>
      <div class="entry-details">${event.summary}</div>
      ${includeReflection && event.reflection ? `
        <div class="entry-reflection">
          "${event.reflection}"
        </div>
      ` : ''}
    </div>
  `;
}

// ============================================
// PDF Export (requires html2pdf.js)
// ============================================

/**
 * Export timeline to PDF.
 *
 * NOTE: This function requires html2pdf.js to be loaded.
 * For now, we'll create a fallback that opens a print dialog.
 */
export async function exportToPdf(
  events: TimelineEvent[],
  options: ExportOptions = {}
): Promise<void> {
  const html = generatePdfHtml(events, options);

  // TODO: When implementing with html2pdf.js:
  // const element = document.createElement('div');
  // element.innerHTML = html;
  // await html2pdf().from(element).save('my-therapy-journey.pdf');

  // For now, open in new window for printing
  const printWindow = window.open('', '_blank');
  if (printWindow) {
    printWindow.document.write(html);
    printWindow.document.close();
    printWindow.focus();
    // Small delay to ensure content is loaded
    setTimeout(() => {
      printWindow.print();
    }, 250);
  }
}

// ============================================
// Shareable Link (Mock)
// ============================================

/**
 * Generate a mock shareable link.
 * In production, this would create a backend-stored snapshot.
 */
export function generateShareableLink(): string {
  // Generate a mock unique ID
  const mockId = Math.random().toString(36).substring(2, 10);
  return `https://therapybridge.app/share/timeline/${mockId}`;
}

/**
 * Copy shareable link to clipboard
 */
export async function copyShareableLink(): Promise<boolean> {
  const link = generateShareableLink();

  try {
    await navigator.clipboard.writeText(link);
    return true;
  } catch {
    // Fallback for older browsers
    const textArea = document.createElement('textarea');
    textArea.value = link;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    document.body.appendChild(textArea);
    textArea.select();

    try {
      document.execCommand('copy');
      return true;
    } catch {
      return false;
    } finally {
      document.body.removeChild(textArea);
    }
  }
}
