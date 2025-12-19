"""
Upheal Page Relevance Filter

LLM-based intelligent filtering to identify Upheal pages relevant to TherapyBridge features.
Uses GPT-4o-mini for cost-effective page classification.

Usage:
    python upheal_relevance_filter.py           # Run with real LLM (requires OPENAI_API_KEY)
    python upheal_relevance_filter.py --mock    # Run in mock mode (rule-based, no API needed)

Reads:
    - data/upheal_sitemap.json (discovered pages from Wave 1)
    - UPHEAL_COMPETITIVE_RESEARCH.md (TherapyBridge context)

Outputs:
    - data/upheal_filtered_sitemap.json (only relevant pages with priority)

Cost estimate: ~$0.10-0.30 for 30 pages using gpt-4o-mini
"""

import json
import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Literal
from dataclasses import dataclass, asdict
import os
import re

# OpenAI is optional for mock mode
try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    AsyncOpenAI = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
SITEMAP_PATH = DATA_DIR / "upheal_sitemap.json"
FILTERED_SITEMAP_PATH = DATA_DIR / "upheal_filtered_sitemap.json"
RESEARCH_MD_PATH = PROJECT_ROOT / "UPHEAL_COMPETITIVE_RESEARCH.md"

# GPT-4o-mini pricing (as of 2024): $0.15/1M input tokens, $0.60/1M output tokens
MODEL = "gpt-4o-mini"
MAX_TOKENS_PER_REQUEST = 200
ESTIMATED_INPUT_TOKENS_PER_PAGE = 500
ESTIMATED_OUTPUT_TOKENS_PER_PAGE = 100


@dataclass
class PageRelevance:
    """Classification result for a single page."""
    url: str
    original_category: str
    link_text: Optional[str]
    relevant: bool
    category: str  # sessions|analytics|notes|patients|goals|compliance|other|excluded
    priority: Literal["high", "medium", "low"]
    reason: str
    classified_at: str


@dataclass
class FilterStats:
    """Statistics for the filtering operation."""
    total_pages_input: int
    total_pages_filtered: int
    high_priority_count: int
    medium_priority_count: int
    low_priority_count: int
    excluded_count: int
    categories_breakdown: dict
    estimated_input_tokens: int
    estimated_output_tokens: int
    estimated_cost_usd: float
    filter_started: str
    filter_completed: str


# TherapyBridge feature context for classification
THERAPYBRIDGE_CONTEXT = """
TherapyBridge is building an AI-powered therapy session transcription and analysis platform.
We need to analyze competitor Upheal.io to identify features relevant to our roadmap.

TherapyBridge Features (Current & Planned):
1. AUTHENTICATION: JWT with refresh tokens, role-based access (therapist/patient)
2. SESSION TIMELINE: Chronological patient journey with milestones
3. AI NOTE EXTRACTION: GPT-4o powered clinical summaries from transcripts
4. AUDIO PIPELINE: Transcription + speaker diarization

Planned Features We Want to Research:
- ANALYTICS DASHBOARD: Cross-session insights, trends, metrics visualization
- NOTE TEMPLATES: SOAP, DAP, GIRP, BIRP, EMDR clinical note formats
- TREATMENT PLANS: Goal setting, progress tracking, milestone markers
- GOAL TRACKING: Patient goals with progress indicators
- EXPORT: Export to EHR systems, PDF reports
- COMPLIANCE: HIPAA audit logs, consent management

RELEVANT Page Categories (INCLUDE these):
- Clinical note formats (SOAP, DAP, GIRP, BIRP, etc.)
- Session management (upload, list, detail views, transcripts)
- Patient portal (dashboard, summaries, action items)
- Analytics & insights (trends, metrics, dashboards)
- Goal tracking & treatment plans
- Compliance features (HIPAA, audit logs, security)
- AI features (automated notes, insights, analysis)

EXCLUDED Page Categories (IGNORE these):
- Pricing, billing, payment, subscription pages
- Marketing, about us, careers, press pages
- General contact, support ticket pages
- Login/signup pages (unless showing onboarding UX)
- Blog posts (unless feature announcements)
- Legal pages (terms, privacy policy - unless HIPAA specific)
"""


CLASSIFICATION_PROMPT = """You are analyzing a page from Upheal.io (therapy software competitor) for TherapyBridge.

{context}

Analyze this Upheal page:
- URL: {url}
- Link Text: {link_text}
- Category (from sitemap): {category}

Return a JSON object with your classification:
{{
  "relevant": true/false,
  "category": "sessions|analytics|notes|patients|goals|compliance|other|excluded",
  "priority": "high|medium|low",
  "reason": "Brief explanation (max 50 words)"
}}

Priority Guidelines:
- HIGH: Direct feature match (note templates, session views, analytics dashboard, treatment plans)
- MEDIUM: Related features (patient portal, settings that affect features, integrations)
- LOW: Tangentially related (help docs about features, security pages)
- For EXCLUDED pages, set relevant=false, category="excluded", priority="low"

Respond with ONLY the JSON object, no markdown formatting."""


async def load_sitemap() -> dict:
    """Load the sitemap JSON from Wave 1 discovery."""
    if not SITEMAP_PATH.exists():
        raise FileNotFoundError(f"Sitemap not found at {SITEMAP_PATH}. Run Wave 1 discovery first.")

    with open(SITEMAP_PATH, 'r') as f:
        return json.load(f)


def extract_all_pages(sitemap: dict) -> list[dict]:
    """Extract all pages from sitemap into a flat list."""
    pages = []

    # Get pages from each category
    for category, page_list in sitemap.get("pages_by_category", {}).items():
        for page in page_list:
            page["original_category"] = category
            pages.append(page)

    # Also include excluded pages (we'll re-classify them)
    for page in sitemap.get("excluded_pages", []):
        page["original_category"] = "excluded"
        pages.append(page)

    return pages


async def classify_page(client: AsyncOpenAI, page: dict) -> PageRelevance:
    """Classify a single page using GPT-4o-mini."""

    prompt = CLASSIFICATION_PROMPT.format(
        context=THERAPYBRIDGE_CONTEXT,
        url=page.get("url", ""),
        link_text=page.get("link_text", "Unknown"),
        category=page.get("original_category", "unknown")
    )

    try:
        response = await client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=MAX_TOKENS_PER_REQUEST,
            temperature=0.1  # Low temperature for consistent classification
        )

        content = response.choices[0].message.content.strip()

        # Parse JSON response
        # Handle potential markdown code block wrapping
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]

        result = json.loads(content)

        return PageRelevance(
            url=page.get("url", ""),
            original_category=page.get("original_category", "unknown"),
            link_text=page.get("link_text"),
            relevant=result.get("relevant", False),
            category=result.get("category", "other"),
            priority=result.get("priority", "low"),
            reason=result.get("reason", "Classification failed"),
            classified_at=datetime.now().isoformat()
        )

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response for {page.get('url')}: {e}")
        logger.error(f"Raw response: {content}")
        # Default to excluding unparseable responses
        return PageRelevance(
            url=page.get("url", ""),
            original_category=page.get("original_category", "unknown"),
            link_text=page.get("link_text"),
            relevant=False,
            category="other",
            priority="low",
            reason=f"Classification parse error: {str(e)[:50]}",
            classified_at=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"Classification failed for {page.get('url')}: {e}")
        return PageRelevance(
            url=page.get("url", ""),
            original_category=page.get("original_category", "unknown"),
            link_text=page.get("link_text"),
            relevant=False,
            category="other",
            priority="low",
            reason=f"Classification error: {str(e)[:50]}",
            classified_at=datetime.now().isoformat()
        )


def mock_classify_page(page: dict) -> PageRelevance:
    """
    Rule-based mock classification for testing without OpenAI API.
    Uses URL patterns and category to determine relevance.
    """
    url = page.get("url", "").lower()
    link_text = (page.get("link_text") or "").lower()
    original_category = page.get("original_category", "unknown").lower()

    # Exclusion patterns (marketing, pricing, etc.)
    exclude_patterns = [
        r"pricing", r"billing", r"payment", r"checkout", r"subscribe",
        r"about", r"careers", r"press", r"contact", r"blog",
        r"terms", r"privacy-policy", r"cookie", r"legal",
        r"login", r"signup", r"register", r"forgot"
    ]

    # High priority patterns (direct feature matches)
    high_priority_patterns = {
        "notes": [r"soap", r"dap", r"girp", r"birp", r"ai-notes", r"progress-notes", r"templates"],
        "sessions": [r"session", r"transcript", r"recording", r"upload"],
        "analytics": [r"analytics", r"insights", r"dashboard", r"reports", r"metrics"],
        "patients": [r"patient", r"client", r"portal"],
        "goals": [r"goal", r"treatment-plan", r"progress", r"milestone"],
        "compliance": [r"hipaa", r"security", r"audit", r"compliance"]
    }

    # Medium priority patterns (related features)
    medium_priority_patterns = {
        "settings": [r"settings", r"account", r"profile"],
        "features": [r"features", r"integrations"]
    }

    # Check exclusions first
    for pattern in exclude_patterns:
        if re.search(pattern, url) or re.search(pattern, link_text):
            return PageRelevance(
                url=page.get("url", ""),
                original_category=original_category,
                link_text=page.get("link_text"),
                relevant=False,
                category="excluded",
                priority="low",
                reason=f"Excluded: matches '{pattern}' pattern",
                classified_at=datetime.now().isoformat()
            )

    # Check high priority patterns
    for category, patterns in high_priority_patterns.items():
        for pattern in patterns:
            if re.search(pattern, url) or re.search(pattern, link_text):
                return PageRelevance(
                    url=page.get("url", ""),
                    original_category=original_category,
                    link_text=page.get("link_text"),
                    relevant=True,
                    category=category,
                    priority="high",
                    reason=f"High priority: matches '{pattern}' for TherapyBridge {category} feature",
                    classified_at=datetime.now().isoformat()
                )

    # Check medium priority patterns
    for category, patterns in medium_priority_patterns.items():
        for pattern in patterns:
            if re.search(pattern, url) or re.search(pattern, link_text):
                return PageRelevance(
                    url=page.get("url", ""),
                    original_category=original_category,
                    link_text=page.get("link_text"),
                    relevant=True,
                    category=category,
                    priority="medium",
                    reason=f"Medium priority: matches '{pattern}' pattern",
                    classified_at=datetime.now().isoformat()
                )

    # Check if original category suggests relevance
    relevant_categories = ["features", "sessions", "analytics", "patients", "notes", "compliance", "dashboard"]
    if original_category in relevant_categories:
        return PageRelevance(
            url=page.get("url", ""),
            original_category=original_category,
            link_text=page.get("link_text"),
            relevant=True,
            category=original_category if original_category in ["sessions", "analytics", "notes", "patients", "compliance"] else "other",
            priority="medium",
            reason=f"Relevant by category: original category '{original_category}'",
            classified_at=datetime.now().isoformat()
        )

    # Default: exclude help/support, include everything else as low priority
    if original_category in ["help", "support"]:
        return PageRelevance(
            url=page.get("url", ""),
            original_category=original_category,
            link_text=page.get("link_text"),
            relevant=True,
            category="other",
            priority="low",
            reason="Low priority: help/support documentation",
            classified_at=datetime.now().isoformat()
        )

    # Default fallback
    return PageRelevance(
        url=page.get("url", ""),
        original_category=original_category,
        link_text=page.get("link_text"),
        relevant=True,
        category="other",
        priority="low",
        reason="Included by default (may contain relevant info)",
        classified_at=datetime.now().isoformat()
    )


async def mock_batch_classify_pages(pages: list[dict]) -> list[PageRelevance]:
    """Process all pages using mock rule-based classification."""
    results = []
    for page in pages:
        result = mock_classify_page(page)
        results.append(result)
    return results


async def batch_classify_pages(client: AsyncOpenAI, pages: list[dict]) -> list[PageRelevance]:
    """Classify all pages with controlled concurrency."""

    # Process pages concurrently but with rate limiting
    # OpenAI gpt-4o-mini has generous rate limits, but we'll be conservative
    BATCH_SIZE = 5  # Process 5 pages concurrently

    results = []
    total = len(pages)

    for i in range(0, total, BATCH_SIZE):
        batch = pages[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        total_batches = (total + BATCH_SIZE - 1) // BATCH_SIZE

        logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} pages)")

        # Process batch concurrently
        tasks = [classify_page(client, page) for page in batch]
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in batch_results:
            if isinstance(result, Exception):
                logger.error(f"Batch task failed: {result}")
            else:
                results.append(result)

        # Small delay between batches to avoid rate limiting
        if i + BATCH_SIZE < total:
            await asyncio.sleep(0.5)

    return results


def build_filtered_sitemap(results: list[PageRelevance], original_sitemap: dict) -> dict:
    """Build the filtered sitemap from classification results."""

    # Separate relevant and excluded pages
    relevant_pages = [r for r in results if r.relevant]
    excluded_pages = [r for r in results if not r.relevant]

    # Group by new category
    pages_by_category = {}
    for page in relevant_pages:
        cat = page.category
        if cat not in pages_by_category:
            pages_by_category[cat] = []
        pages_by_category[cat].append(asdict(page))

    # Group by priority
    pages_by_priority = {
        "high": [asdict(p) for p in relevant_pages if p.priority == "high"],
        "medium": [asdict(p) for p in relevant_pages if p.priority == "medium"],
        "low": [asdict(p) for p in relevant_pages if p.priority == "low"]
    }

    # Calculate stats
    stats = FilterStats(
        total_pages_input=len(results),
        total_pages_filtered=len(relevant_pages),
        high_priority_count=len(pages_by_priority["high"]),
        medium_priority_count=len(pages_by_priority["medium"]),
        low_priority_count=len(pages_by_priority["low"]),
        excluded_count=len(excluded_pages),
        categories_breakdown={cat: len(pages) for cat, pages in pages_by_category.items()},
        estimated_input_tokens=len(results) * ESTIMATED_INPUT_TOKENS_PER_PAGE,
        estimated_output_tokens=len(results) * ESTIMATED_OUTPUT_TOKENS_PER_PAGE,
        estimated_cost_usd=round(
            (len(results) * ESTIMATED_INPUT_TOKENS_PER_PAGE * 0.15 / 1_000_000) +
            (len(results) * ESTIMATED_OUTPUT_TOKENS_PER_PAGE * 0.60 / 1_000_000),
            4
        ),
        filter_started=original_sitemap.get("discovery_started", datetime.now().isoformat()),
        filter_completed=datetime.now().isoformat()
    )

    filtered_sitemap = {
        "source": "upheal_relevance_filter.py",
        "model": MODEL,
        "base_url": original_sitemap.get("base_url", "https://www.upheal.io"),
        "filter_stats": asdict(stats),
        "pages_by_priority": pages_by_priority,
        "pages_by_category": pages_by_category,
        "excluded_pages": [asdict(p) for p in excluded_pages],
        "all_relevant_pages": [asdict(p) for p in relevant_pages]
    }

    return filtered_sitemap


def print_summary(filtered_sitemap: dict):
    """Print a summary of the filtering results."""
    stats = filtered_sitemap["filter_stats"]

    print("\n" + "=" * 60)
    print("UPHEAL RELEVANCE FILTER - SUMMARY")
    print("=" * 60)

    print(f"\nTotal pages processed: {stats['total_pages_input']}")
    print(f"Relevant pages kept:   {stats['total_pages_filtered']}")
    print(f"Pages excluded:        {stats['excluded_count']}")

    filter_rate = (1 - stats['total_pages_filtered'] / stats['total_pages_input']) * 100 if stats['total_pages_input'] > 0 else 0
    print(f"Filter rate:           {filter_rate:.1f}% filtered out")

    print(f"\nPriority Breakdown:")
    print(f"  HIGH priority:   {stats['high_priority_count']} pages")
    print(f"  MEDIUM priority: {stats['medium_priority_count']} pages")
    print(f"  LOW priority:    {stats['low_priority_count']} pages")

    print(f"\nCategory Breakdown:")
    for cat, count in sorted(stats['categories_breakdown'].items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count} pages")

    print(f"\nEstimated LLM Cost:")
    print(f"  Input tokens:  ~{stats['estimated_input_tokens']:,}")
    print(f"  Output tokens: ~{stats['estimated_output_tokens']:,}")
    print(f"  Total cost:    ~${stats['estimated_cost_usd']:.4f}")

    # Show example high-priority page
    high_priority = filtered_sitemap["pages_by_priority"].get("high", [])
    if high_priority:
        example = high_priority[0]
        print(f"\nExample HIGH priority page:")
        print(f"  URL: {example['url']}")
        print(f"  Category: {example['category']}")
        print(f"  Reason: {example['reason']}")

    print("\n" + "=" * 60)
    print(f"Output saved to: {FILTERED_SITEMAP_PATH}")
    print("=" * 60 + "\n")


async def main(use_mock: bool = False):
    """Main entry point for the relevance filter."""

    mode = "MOCK (rule-based)" if use_mock else f"LLM ({MODEL})"

    print("\n" + "=" * 60)
    print("UPHEAL RELEVANCE FILTER")
    print(f"Mode: {mode}")
    print("=" * 60 + "\n")

    client = None

    if not use_mock:
        # Check for OpenAI API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            # Try to load from .env file
            env_path = PROJECT_ROOT / ".env"
            if env_path.exists():
                with open(env_path) as f:
                    for line in f:
                        if line.startswith("OPENAI_API_KEY="):
                            api_key = line.strip().split("=", 1)[1].strip('"\'')
                            break

        if not api_key:
            logger.error("OPENAI_API_KEY not found. Set it as environment variable or in .env file.")
            logger.info("Tip: Run with --mock flag for rule-based classification without API key.")
            return

        if not OPENAI_AVAILABLE:
            logger.error("OpenAI package not installed. Run: pip install openai")
            logger.info("Tip: Run with --mock flag for rule-based classification without OpenAI.")
            return

        # Initialize OpenAI client
        client = AsyncOpenAI(api_key=api_key)

    # Load sitemap from Wave 1
    logger.info(f"Loading sitemap from {SITEMAP_PATH}")
    try:
        sitemap = await load_sitemap()
    except FileNotFoundError as e:
        logger.error(str(e))
        return

    # Extract all pages
    pages = extract_all_pages(sitemap)
    logger.info(f"Found {len(pages)} pages to classify")

    # Classify all pages
    if use_mock:
        logger.info("Starting classification using MOCK rule-based classifier...")
        results = await mock_batch_classify_pages(pages)
    else:
        logger.info(f"Starting classification using {MODEL}...")
        results = await batch_classify_pages(client, pages)

    # Build filtered sitemap
    logger.info("Building filtered sitemap...")
    filtered_sitemap = build_filtered_sitemap(results, sitemap)

    # Add mode info to output
    filtered_sitemap["classification_mode"] = "mock" if use_mock else "llm"

    # Adjust cost estimate for mock mode
    if use_mock:
        filtered_sitemap["filter_stats"]["estimated_input_tokens"] = 0
        filtered_sitemap["filter_stats"]["estimated_output_tokens"] = 0
        filtered_sitemap["filter_stats"]["estimated_cost_usd"] = 0.0

    # Save results
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(FILTERED_SITEMAP_PATH, 'w') as f:
        json.dump(filtered_sitemap, f, indent=2)

    # Print summary
    print_summary(filtered_sitemap)

    return filtered_sitemap


if __name__ == "__main__":
    # Parse command line arguments
    use_mock = "--mock" in sys.argv or "-m" in sys.argv

    if "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__)
        print("\nOptions:")
        print("  --mock, -m    Use rule-based classification (no API key needed)")
        print("  --help, -h    Show this help message")
        sys.exit(0)

    asyncio.run(main(use_mock=use_mock))
