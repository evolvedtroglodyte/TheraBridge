# Upheal Web Scraper

Professional web scraping infrastructure for competitive analysis of the Upheal therapy platform.

## ⚠️ Legal & Ethical Compliance

**IMPORTANT:** This scraper is designed for competitive analysis and market research only.

- ✅ Respects robots.txt directives
- ✅ Implements rate limiting (0.5 requests/second default)
- ✅ Transparent User-Agent identification
- ✅ Focuses on publicly accessible, non-personal data
- ❌ Does NOT bypass authentication or paywalls
- ❌ Does NOT scrape personal or GDPR-protected data

**Before using:** Review Upheal's Terms of Service and robots.txt at https://www.upheal.io/robots.txt

---

## 🏗️ Architecture

```
Scrapping/
├── src/scraper/
│   ├── config.py          # Pydantic Settings configuration
│   ├── scrapers/
│   │   ├── base.py        # Abstract base scraper
│   │   └── upheal_scraper.py  # Upheal-specific implementation
│   ├── utils/
│   │   ├── http_client.py     # HTTP client with retry logic
│   │   ├── rate_limiter.py    # Token bucket rate limiter
│   │   └── logger.py          # Structured logging
│   └── models/
│       └── schemas.py     # Pydantic data models
├── tests/                 # Unit & integration tests
└── data/                  # Scraped data (gitignored)
```

**Key Design Patterns:**
- **Modular architecture**: Scrapers, utils, models separated
- **Pydantic validation**: Type-safe configuration and data models
- **Async HTTP**: HTTPX for concurrent requests (10x faster)
- **Exponential backoff**: Automatic retry with increasing delays
- **Rate limiting**: Token bucket algorithm respects server load

---

## 🚀 Quick Start

### 1. Setup

```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# (Optional) Install Playwright browsers for JavaScript-heavy pages
playwright install chromium
```

### 2. Configuration

Copy `.env.example` to `.env` and customize:

```bash
cp .env.example .env
```

Key settings:
- `REQUESTS_PER_SECOND`: Rate limit (default 0.5 = 2 seconds between requests)
- `USER_AGENT`: Identify your scraper honestly
- `MAX_RETRIES`: Retry failed requests (default 3)

### 3. Run Scraper

```python
from src.scraper.scrapers.upheal_scraper import UphealScraper

scraper = UphealScraper()
data = scraper.scrape()

# Data saved to data/processed/upheal_YYYYMMDD_HHMMSS.json
```

---

## 📊 What Gets Scraped

**Target pages:**
- Features page (`/features`)
- Pricing page (`/pricing`)

**Data extracted:**
- Product features and descriptions
- Pricing tiers and plans
- Feature comparisons
- Public testimonials (anonymized)

**NOT scraped:**
- Behind-login content
- Personal user data
- Proprietary documentation
- Customer PHI (Protected Health Information)

---

## 🧪 Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=src --cov-report=html

# Specific test
pytest tests/test_upheal_scraper.py -v
```

---

## 📝 Project Status

| Component | Status | Notes |
|-----------|--------|-------|
| Project structure | ✅ Complete | Modular folder organization |
| Configuration | ✅ Complete | Pydantic Settings with .env support |
| HTTP client | ✅ Complete | HTTPX with retry logic |
| Rate limiter | ✅ Complete | Token bucket (0.5 req/sec) |
| Base scraper | ✅ Complete | Abstract class for all scrapers |
| Upheal scraper | ✅ Complete | Feature & pricing extraction |
| Data models | ✅ Complete | Pydantic validation |
| Tests | ✅ Complete | Unit & integration coverage |

---

## 🔒 Compliance Checklist

Before running scraper in production:

- [ ] Review target website's Terms of Service
- [ ] Check robots.txt for disallowed paths
- [ ] Verify User-Agent is transparent with contact info
- [ ] Confirm rate limiting is enabled (3-5 sec delays minimum)
- [ ] Filter out any personal data from results
- [ ] Document business purpose (competitive analysis)
- [ ] Maintain audit logs of scraping activities

---

## 📚 Resources

- [Web Scraping Best Practices 2025](https://www.scraperapi.com/web-scraping/best-practices/)
- [HTTPX Documentation](https://www.python-httpx.org/)
- [Pydantic Settings Guide](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [Ethical Web Scraping Guide](https://scrapingapi.ai/blog/ethical-web-scraping)

---

## 📄 License

MIT License - See LICENSE file for details.

**Disclaimer:** This tool is for educational and competitive analysis purposes only. Users are responsible for ensuring compliance with applicable laws and website terms of service.
