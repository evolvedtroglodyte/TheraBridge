# Upheal.io Competitive Research - Intelligent Feature Scraping

**Date Created:** 2025-12-18
**Project:** TherapyBridge/Peerbridge
**Purpose:** Competitive analysis and feature discovery

---

## Goal

**Primary Objective:**
Automatically scrape ALL features from Upheal.io that align with the TherapyBridge project, without manually specifying every URL.

**Why This Matters:**
TherapyBridge is building an AI-powered therapy session transcription and analysis platform. Upheal.io is a direct competitor. Understanding their feature set, UX patterns, clinical note formats, and workflow design will inform TherapyBridge development and ensure competitive feature parity.

---

## TherapyBridge Context

### What We're Building

**TherapyBridge** is a comprehensive therapy platform with three main components:

1. **Audio Transcription Pipeline**
   - Converts therapy audio → speaker-labeled transcripts
   - OpenAI Whisper API + pyannote.audio diarization
   - Therapist/client role labeling

2. **Backend API (FastAPI)**
   - Session management with PostgreSQL (Neon)
   - GPT-4o AI extraction for clinical notes
   - Extracts: topics, strategies, triggers, action items, mood, risk flags
   - JWT authentication with role-based access

3. **Frontend Dashboard (Next.js 16 + React 19)**
   - Therapist dashboard: patient management, session upload, analytics
   - Patient portal: session summaries, action items
   - Session timeline visualization
   - Goal tracking and treatment plans

### Features Already Implemented

- ✅ **Feature 1: Authentication** - JWT with refresh tokens, bcrypt, rate limiting
- ✅ **Feature 5: Session Timeline** - Chronological patient journey with milestones
- ✅ **AI Note Extraction** - GPT-4o powered clinical summaries
- ✅ **Audio Pipeline** - Complete transcription + diarization

### Features Planned (Relevant to Upheal Research)

- **Feature 2: Analytics Dashboard** - Cross-session insights, trends
- **Feature 3: Note Templates** - SOAP, DAP, GIRP, BIRP, EMDR formats
- **Feature 4: Treatment Plans** - Goal setting, progress tracking
- **Feature 6: Goal Tracking** - Patient goals with milestone markers
- **Feature 7: Export** - Export to EHR systems, PDF reports
- **Feature 8: Compliance** - HIPAA audit logs, consent management

---

## What to Extract from Upheal.io

### High-Priority Features

1. **Clinical Note Formats**
   - Note templates (SOAP, DAP, GIRP, BIRP, etc.)
   - AI-generated summary structure
   - Treatment plan format
   - Progress note patterns

2. **Session Management**
   - Session list view (filters, search, sorting)
   - Session detail view (transcript display, notes)
   - Audio upload workflow
   - Processing status indicators

3. **Patient Portal**
   - Patient-facing dashboard design
   - How session summaries are presented to patients
   - Action item/homework display
   - Communication patterns (therapist notes vs. patient-friendly language)

4. **Analytics & Insights**
   - Dashboard layout and key metrics
   - Timeline visualization approach
   - Cross-session insights presentation
   - Trend analysis features

5. **Goal Tracking & Treatment Plans**
   - Goal creation workflow
   - Progress tracking UI
   - Milestone markers
   - Treatment plan structure

6. **Workflow & UX Patterns**
   - Navigation structure
   - Information hierarchy
   - Color coding and visual design
   - Mobile responsiveness patterns

7. **Compliance & Security**
   - HIPAA compliance features
   - Audit logs presentation
   - Consent management
   - Data export options

---

## Technical Requirements

### Intelligent Scraper Capabilities Needed

1. **Automatic Link Discovery**
   - Crawl Upheal.io to discover all feature pages automatically
   - Extract navigation menus, sidebar links, feature lists
   - Follow internal links to discover sub-features
   - Build complete site map

2. **Relevance Filtering**
   - Compare discovered pages against TherapyBridge feature list
   - Filter for pages relevant to: sessions, notes, analytics, patients, goals, compliance
   - Exclude: marketing pages, pricing, general info

3. **Structured Data Extraction**
   - Extract feature names and descriptions
   - Capture UI patterns (forms, tables, cards, modals)
   - Screenshot key pages for visual reference
   - Extract clinical note examples if visible
   - Identify workflow steps and user journeys

4. **LLM-Powered Analysis**
   - Use GPT-4o to analyze extracted content
   - Compare Upheal features to TherapyBridge roadmap
   - Identify gaps in TherapyBridge feature set
   - Generate competitive analysis report

---

## Session Summary - 2025-12-18

### What Was Built

**1. Basic Upheal Scraper (Crawl4AI Session Management)**
   - File: `/Users/vishnuanapalli/Desktop/web-scraper/upheal_crawl4ai.py`
   - Uses Crawl4AI's `session_id` for automatic session persistence
   - Two modes: Automatic (predefined pages) and Interactive (scrape any page)
   - Saves markdown, HTML, and screenshots
   - **Limitation:** Requires manual URL list in `PAGES_TO_SCRAPE`

**2. Documentation Created**
   - `UPHEAL_SCRAPING_GUIDE.md` - Complete guide for Crawl4AI approach
   - `QUICKSTART.md` - 30-second quick start
   - `README.md` - Updated with new scraping approach
   - Crawl4AI skill documentation copied from zip file

**3. Research Completed**
   - Analyzed 4 login bypass approaches
   - Compared Playwright vs Selenium vs BeautifulSoup
   - Discovered Crawl4AI session management is simplest approach
   - Confirmed Upheal.io is a SPA requiring JavaScript rendering

### Current State

**What Works:**
- Manual login with session persistence across multiple pages
- Clean markdown + HTML output
- Screenshot capture
- Interactive mode for ad-hoc scraping

**What's Missing:**
- ❌ Automatic link discovery (currently manual URL list)
- ❌ Relevance filtering (scrapes everything in list, no intelligent filtering)
- ❌ LLM-powered feature comparison
- ❌ Structured extraction of UI patterns
- ❌ Competitive analysis report generation

---

## Next Steps

### Phase 1: Intelligent Link Discovery

**Goal:** Automatically discover all Upheal feature pages without manual URL list

**Approach:**
1. Login to Upheal dashboard
2. Extract all navigation links (sidebar, menu, footer)
3. Follow internal links recursively (max depth: 3)
4. Build complete sitemap of discovered URLs
5. Filter out duplicates and external links

**Tools:**
- Crawl4AI's link extraction: `result.links["internal"]`
- Deep crawling pattern from `crawl4ai-skill/SKILL.md`

### Phase 2: LLM-Powered Relevance Filtering

**Goal:** Only scrape pages relevant to TherapyBridge features

**Approach:**
1. For each discovered URL, extract page title and initial content
2. Use GPT-4o to classify page relevance:
   - Input: Page title, URL, first 500 chars
   - Output: Relevant (yes/no), Category (sessions/analytics/notes/etc.), Priority (high/medium/low)
3. Only scrape pages marked as "Relevant: yes"

**Prompt Template:**
```
You are analyzing a competitor therapy platform (Upheal.io) for a therapy platform called TherapyBridge.

TherapyBridge features: [Feature 1-8 descriptions]

Analyze this Upheal page:
- URL: {url}
- Title: {title}
- Preview: {first_500_chars}

Return JSON:
{
  "relevant": true/false,
  "category": "sessions|analytics|notes|patients|goals|compliance|other",
  "priority": "high|medium|low",
  "reason": "Brief explanation"
}
```

### Phase 3: Structured Feature Extraction

**Goal:** Extract specific features and UI patterns, not just raw content

**Approach:**
1. Use Crawl4AI's `JsonCssExtractionStrategy` for structured extraction
2. Define schemas for common patterns:
   - Navigation menus
   - Feature cards
   - Form fields
   - Table structures
   - Modal dialogs

**Example Schema:**
```python
schema = {
    "name": "features",
    "baseSelector": ".feature-card, [data-feature], .feature-section",
    "fields": [
        {"name": "title", "selector": "h2, h3, .feature-title", "type": "text"},
        {"name": "description", "selector": "p, .description", "type": "text"},
        {"name": "icon", "selector": "img, svg", "type": "attribute", "attribute": "src"}
    ]
}
```

### Phase 4: LLM-Powered Competitive Analysis

**Goal:** Generate actionable insights comparing Upheal to TherapyBridge

**Approach:**
1. Feed all scraped content to GPT-4o
2. Request structured comparison report
3. Identify feature gaps in TherapyBridge
4. Suggest UX improvements based on Upheal patterns

**Prompt Template:**
```
You are a product analyst comparing two therapy platforms.

TherapyBridge (our platform):
- Features: [List all 8 features with status]
- Tech stack: [FastAPI, Next.js, GPT-4o, etc.]

Upheal.io (competitor):
- Scraped content: [All markdown files]

Generate a competitive analysis report with:
1. Feature Comparison Matrix (what they have that we don't)
2. UX Pattern Analysis (what we can learn from their design)
3. Gap Analysis (features we should prioritize)
4. Recommended Actions (top 5 features to add/improve)

Format: Markdown with tables and priority rankings
```

---

## Implementation Plan

### Immediate Next Session

**Build:** Intelligent Feature Discovery Scraper

**File:** `upheal_intelligent_scraper.py`

**Capabilities:**
1. Login to Upheal once
2. Discover all links automatically (navigation, sidebar, etc.)
3. Recursively crawl internal links (max depth 3)
4. Use GPT-4o to filter for relevant pages only
5. Extract structured features using CSS schemas
6. Save organized output:
   - `upheal_analysis/sitemap.json` - All discovered URLs
   - `upheal_analysis/relevant_pages.json` - Filtered pages
   - `upheal_analysis/features/` - Extracted features by category
   - `upheal_analysis/screenshots/` - Visual references
   - `upheal_analysis/COMPETITIVE_REPORT.md` - LLM-generated analysis

**User Input Needed:**
- TherapyBridge feature descriptions (can pull from project docs)
- Upheal.io login credentials (for authentication)
- OpenAI API key (for GPT-4o filtering and analysis)

---

## Success Criteria

**The scraper is successful when:**

1. ✅ Zero manual URL input required
2. ✅ Discovers 90%+ of Upheal feature pages automatically
3. ✅ Filters out irrelevant pages (marketing, pricing, etc.)
4. ✅ Extracts structured features in JSON format
5. ✅ Generates actionable competitive analysis report
6. ✅ Provides visual screenshots for UX reference
7. ✅ Runs end-to-end with single command after login

**Output Quality:**
- Competitive report highlights 5-10 key insights
- Feature comparison matrix clearly shows gaps
- UX recommendations are specific and actionable
- Screenshots captured for all high-priority features

---

## Resources

### Scraper Location
`/Users/vishnuanapalli/Desktop/web-scraper/`

### Key Files
- `upheal_crawl4ai.py` - Current basic scraper
- `crawl4ai-skill/SKILL.md` - Crawl4AI documentation
- `UPHEAL_SCRAPING_GUIDE.md` - Usage guide

### TherapyBridge Project
`/Users/vishnuanapalli/Desktop/Rohin & Vish Global Domination/peerbridge proj/`

### Documentation
- `Project MDs/TherapyBridge.md` - Main project doc
- `Project MDs/features/` - Feature specifications
- `backend/README.md` - Backend API docs
- `frontend/README.md` - Frontend docs

---

## Notes

- Upheal.io is HIPAA-compliant - all scraped data should be treated as potentially sensitive
- Review Upheal's Terms of Service before extensive scraping
- Consider rate limiting (2-3 second delays between requests)
- Use OpenAI API budget wisely (GPT-4o filtering can get expensive)
- Focus on features, not patient data or private information

---

**Status:** Ready for intelligent scraper implementation
**Next Action:** Build `upheal_intelligent_scraper.py` with automatic discovery and LLM filtering
