"""Sandbox endpoint — score a user-submitted company through the full pipeline.

Flow: company name → Tavily web research → feature extraction → 17-dimension scoring → tier classification

Deep mode (single company): dimension-specific queries, advanced search depth,
URL follow-up scraping for richer signal extraction.
"""
import asyncio
import math
import json
import re
import logging
import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
from bs4 import BeautifulSoup
from database import get_db
from config import get_settings
from models.company import Company, DimensionScore, CompanyScore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sandbox", tags=["sandbox"])

# ── Scoring engine constants ──────────────────────────────────────────────────

DERIVED_WEIGHTS = {
    "data_quality": 0.997, "data_integration": 0.913, "analytics_maturity": 1.126,
    "cloud_architecture": 0.559, "tech_stack_modernity": 0.297, "ai_engineering": 0.519,
    "ai_product_features": 4.447, "revenue_ai_upside": 2.019, "margin_ai_upside": 0.644,
    "product_differentiation": 0.481, "ai_talent_density": 2.346, "leadership_ai_vision": 1.432,
    "org_change_readiness": 0.534, "partner_ecosystem": 0.972, "ai_governance": 0.422,
    "regulatory_readiness": 0.32, "ai_momentum": 0.272,
}
TOTAL_WEIGHT = sum(DERIVED_WEIGHTS.values())

CATEGORIES = {
    "Data & Analytics": ["data_quality", "data_integration", "analytics_maturity"],
    "Technology & Infrastructure": ["cloud_architecture", "tech_stack_modernity", "ai_engineering"],
    "AI Product & Value": ["ai_product_features", "revenue_ai_upside", "margin_ai_upside", "product_differentiation"],
    "Organization & Talent": ["ai_talent_density", "leadership_ai_vision", "org_change_readiness", "partner_ecosystem"],
    "Governance & Risk": ["ai_governance", "regulatory_readiness"],
    "Velocity & Momentum": ["ai_momentum"],
}

DIMENSION_LABELS = {
    "data_quality": "Data Quality & Availability", "data_integration": "Data Integration & APIs",
    "analytics_maturity": "Analytics Maturity", "cloud_architecture": "Cloud Architecture",
    "tech_stack_modernity": "Tech Stack Modernity", "ai_engineering": "AI/ML Engineering",
    "ai_product_features": "AI Product Features", "revenue_ai_upside": "Revenue AI Upside",
    "margin_ai_upside": "Margin AI Upside", "product_differentiation": "Product Differentiation",
    "ai_talent_density": "AI Talent Density", "leadership_ai_vision": "Leadership AI Vision",
    "org_change_readiness": "Org Change Readiness", "partner_ecosystem": "Partner Ecosystem",
    "ai_governance": "AI Governance", "regulatory_readiness": "Regulatory Readiness",
    "ai_momentum": "AI Momentum",
}


# ── Scoring functions ─────────────────────────────────────────────────────────

def classify_tier(score: float) -> str:
    if score >= 4.0:
        return "AI-Ready"
    if score >= 3.2:
        return "AI-Buildable"
    if score >= 2.5:
        return "AI-Emerging"
    return "AI-Limited"


def assign_wave(score: float) -> int:
    if score >= 3.5:
        return 1
    if score >= 2.8:
        return 2
    return 3


def compute_composite(pillar_scores: dict[str, float]) -> float:
    weighted = sum(pillar_scores.get(d, 0) * w for d, w in DERIVED_WEIGHTS.items())
    return round(weighted / TOTAL_WEIGHT, 2)


def compute_category_scores(pillar_scores: dict[str, float]) -> dict[str, float]:
    result = {}
    for cat, dims in CATEGORIES.items():
        vals = [pillar_scores[d] for d in dims if d in pillar_scores]
        result[cat] = round(sum(vals) / len(vals), 2) if vals else 0.0
    return result


# ── Web research → feature extraction ─────────────────────────────────────────

async def research_company(company_name: str, tavily_key: str) -> dict:
    """Use Tavily API to research a company and extract structured features."""
    queries = [
        f"{company_name} company overview revenue employees funding",
        f"{company_name} AI artificial intelligence machine learning features products",
        f"{company_name} technology stack cloud infrastructure API platform",
    ]

    all_content = []
    async with httpx.AsyncClient(timeout=30.0) as client:
        for query in queries:
            try:
                resp = await client.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": tavily_key,
                        "query": query,
                        "search_depth": "basic",
                        "max_results": 3,
                        "include_answer": True,
                    },
                )
                data = resp.json()
                if data.get("answer"):
                    all_content.append(data["answer"])
                for result in data.get("results", []):
                    all_content.append(result.get("content", ""))
            except Exception as e:
                logger.warning(f"Tavily search failed for '{query}': {e}")

    research_text = "\n".join(all_content)
    features = extract_features(company_name, research_text)
    features["research_summary"] = research_text[:2000]  # Keep for display
    return features


# ── Deep research (single-company mode) ─────────────────────────────────────

# Dimension-specific queries — each targets signals for specific scoring categories
DEEP_QUERIES = [
    # Company fundamentals (employee count, funding, founded year, public status)
    "{company} company overview number of employees headcount revenue funding raised valuation founded",
    # AI product features & engineering (drives ai_product_features, ai_engineering, ai_momentum)
    "{company} artificial intelligence machine learning AI features AI-powered products generative AI LLM",
    # Cloud & tech stack (drives cloud_architecture, tech_stack_modernity)
    "{company} technology stack engineering blog cloud AWS Azure GCP Kubernetes microservices architecture",
    # Data & analytics (drives data_quality, data_integration, analytics_maturity)
    "{company} data platform analytics data warehouse API integrations SDK developer platform ecosystem",
    # Leadership & talent (drives leadership_ai_vision, ai_talent_density, org_change_readiness)
    "{company} CTO CEO leadership team AI strategy hiring engineering culture talent team size",
    # Governance & compliance (drives ai_governance, regulatory_readiness)
    "{company} compliance security certifications SOC2 GDPR HIPAA ISO regulatory audit privacy",
    # Market position & differentiation (drives market_position, product_differentiation, revenue_ai_upside)
    "{company} market leader competitors market share industry position customers case studies growth",
    # Partner ecosystem (drives partner_ecosystem)
    "{company} partnerships integrations marketplace ecosystem third-party plugins extensions",
]


async def _tavily_search(client: httpx.AsyncClient, query: str, tavily_key: str) -> list[dict]:
    """Execute a single Tavily search and return results with URLs."""
    try:
        resp = await client.post(
            "https://api.tavily.com/search",
            json={
                "api_key": tavily_key,
                "query": query,
                "search_depth": "advanced",
                "max_results": 5,
                "include_answer": True,
            },
        )
        data = resp.json()
        results = []
        if data.get("answer"):
            results.append({"content": data["answer"], "url": None, "title": "AI Summary"})
        for r in data.get("results", []):
            results.append({
                "content": r.get("content", ""),
                "url": r.get("url"),
                "title": r.get("title", ""),
            })
        return results
    except Exception as e:
        logger.warning(f"Tavily search failed for '{query}': {e}")
        return []


async def _scrape_url(client: httpx.AsyncClient, url: str) -> str:
    """Scrape a URL and return clean text content. Returns empty string on failure."""
    try:
        resp = await client.get(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
            follow_redirects=True,
            timeout=15.0,
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        return "\n".join(lines)[:8000]
    except Exception as e:
        logger.debug(f"Scrape failed for {url}: {e}")
        return ""


def _pick_best_urls(all_results: list[dict], company_name: str, max_urls: int = 5) -> list[str]:
    """Select the most informative URLs from search results for follow-up scraping.

    Prioritises the company's own domain (about, careers, product pages),
    then trusted third-party sources (Crunchbase, LinkedIn, G2, etc.).
    Skips generic social media, PDFs, and video sites.
    """
    company_slug = company_name.lower().replace(" ", "").replace("-", "")
    skip_domains = {"youtube.com", "twitter.com", "x.com", "facebook.com", "instagram.com", "tiktok.com"}
    skip_extensions = {".pdf", ".png", ".jpg", ".mp4"}

    scored: list[tuple[float, str]] = []
    seen_domains = set()

    for r in all_results:
        url = r.get("url")
        if not url:
            continue
        url_lower = url.lower()

        # Skip unwanted
        if any(d in url_lower for d in skip_domains):
            continue
        if any(url_lower.endswith(ext) for ext in skip_extensions):
            continue

        # Deduplicate by domain
        try:
            domain = url_lower.split("//")[1].split("/")[0].replace("www.", "")
        except IndexError:
            continue
        if domain in seen_domains:
            continue
        seen_domains.add(domain)

        # Score the URL
        score = 0.0
        # Company's own site — highest priority
        if company_slug in domain.replace(".", "").replace("-", ""):
            score += 10.0
            if any(p in url_lower for p in ["/about", "/team", "/careers", "/jobs", "/product", "/platform", "/customers"]):
                score += 5.0
        # High-value third-party sources
        if any(src in domain for src in ["crunchbase.com", "linkedin.com", "g2.com", "pitchbook.com",
                                          "owler.com", "glassdoor.com", "stackshare.io", "builtwith.com"]):
            score += 6.0
        # Tech/engineering content
        if any(p in url_lower for p in ["/blog", "/engineering", "/tech", "/developers", "/docs", "/api"]):
            score += 3.0
        # News sources add some value
        if any(src in domain for src in ["techcrunch.com", "reuters.com", "bloomberg.com", "venturebeat.com"]):
            score += 4.0

        scored.append((score, url))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [url for _, url in scored[:max_urls]]


def _clean_text_block(text: str) -> str:
    """Remove common scrape artifacts from a text block."""
    lines = text.split("\n")
    cleaned = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Skip lines that are just navigation / UI artifacts
        if len(line) < 4:
            continue
        # Skip markdown headers that are just section labels (e.g., "## Overview", "### Website")
        if re.match(r'^#{1,4}\s*(Overview|Website|Crunchbase|LinkedIn|Industry|Company Size|'
                     r'Locations|Get Directions|Directions|Specialties|Investors|Funding|'
                     r'Founded|Key People|Similar Pages|People Also Viewed|Show more|'
                     r'See all|View all|Sign in|Join now|N/A)\s*$', line, re.IGNORECASE):
            continue
        # Skip lines that are just bullet markers or short labels
        if re.match(r'^[\•\-\→\›]\s*$', line):
            continue
        # Skip LinkedIn-style metadata lines
        if re.match(r'^\d+\s*(associated members|followers|connections)', line, re.IGNORECASE):
            continue
        cleaned.append(line)
    return " ".join(cleaned)


def _build_display_summary(all_results: list[dict], company_name: str) -> str:
    """Build a clean, readable research summary for UI display.

    Priority order:
    1. Tavily AI-generated answers (cleanest prose)
    2. High-quality search result snippets (non-LinkedIn, non-scraped)
    3. Fallback: cleaned versions of whatever we have

    Caps at 2500 chars to keep the UI concise.
    """
    ai_summaries: list[str] = []
    good_snippets: list[str] = []

    for r in all_results:
        content = r.get("content", "").strip()
        if not content or len(content) < 50:
            continue

        url = (r.get("url") or "").lower()
        title = (r.get("title") or "").strip()

        # Tier 1: Tavily AI answers — these are clean prose summaries
        if title == "AI Summary":
            cleaned = _clean_text_block(content)
            if len(cleaned) > 80:
                ai_summaries.append(cleaned)
            continue

        # Skip noisy sources for display purposes
        if any(src in url for src in ["linkedin.com", "glassdoor.com", "indeed.com"]):
            continue

        # Tier 2: Search result snippets from quality sources
        cleaned = _clean_text_block(content)
        if len(cleaned) > 80:
            good_snippets.append(cleaned)

    # Assemble display text — AI summaries first, then snippets
    parts: list[str] = []
    seen_text = set()

    for text in ai_summaries + good_snippets:
        # Basic dedup: skip if first 100 chars match something already included
        fingerprint = text[:100].lower()
        if fingerprint in seen_text:
            continue
        seen_text.add(fingerprint)
        parts.append(text)

        # Stop once we have enough
        if sum(len(p) for p in parts) > 2500:
            break

    if not parts:
        return f"Research data collected for {company_name}. Scoring based on web signals across 8 search queries."

    summary = "\n\n".join(parts)
    return summary[:2500]


async def research_company_deep(company_name: str, tavily_key: str, context_hint: str = "") -> dict:
    """Deep single-company research: 8 dimension-specific queries + URL follow-up scraping.

    Returns the same feature dict as research_company() but with significantly
    richer underlying text, leading to better feature extraction and scoring.

    Args:
        company_name: Company name to research
        tavily_key: Tavily API key
        context_hint: Optional context (e.g., "waste hauling SaaS") to append to queries
                      for disambiguating companies with generic names
    """
    hint = f" {context_hint}" if context_hint else ""
    queries = [q.format(company=company_name + hint) for q in DEEP_QUERIES]

    # Phase 1: Run all 8 Tavily searches concurrently
    async with httpx.AsyncClient(timeout=30.0) as client:
        search_tasks = [_tavily_search(client, q, tavily_key) for q in queries]
        search_results = await asyncio.gather(*search_tasks, return_exceptions=True)

    # Flatten results
    all_results: list[dict] = []
    search_content: list[str] = []
    for batch in search_results:
        if isinstance(batch, Exception):
            continue
        for r in batch:
            all_results.append(r)
            if r.get("content"):
                search_content.append(r["content"])

    logger.info(f"Deep research for '{company_name}': {len(all_results)} search results from {len(queries)} queries")

    # Phase 2: Follow-up scraping on best URLs
    best_urls = _pick_best_urls(all_results, company_name, max_urls=5)
    scraped_content: list[str] = []

    if best_urls:
        async with httpx.AsyncClient(timeout=20.0) as client:
            scrape_tasks = [_scrape_url(client, url) for url in best_urls]
            scrape_results = await asyncio.gather(*scrape_tasks, return_exceptions=True)

        for text in scrape_results:
            if isinstance(text, str) and len(text) > 100:
                scraped_content.append(text)

        logger.info(f"Deep research for '{company_name}': scraped {len(scraped_content)}/{len(best_urls)} URLs successfully")

    # Combine all text: search summaries first, then scraped pages
    research_text = "\n\n".join(search_content)
    scraped_text = "\n\n".join(scraped_content)
    combined_text = research_text + "\n\n--- SCRAPED PAGE CONTENT ---\n\n" + scraped_text

    # Extract features from the full corpus
    features = extract_features(company_name, combined_text)

    # Build a clean research summary for display
    features["research_summary"] = _build_display_summary(all_results, company_name)

    # Track data quality signals
    features["_research_meta"] = {
        "queries_sent": len(queries),
        "search_results": len(all_results),
        "urls_scraped": len(scraped_content),
        "total_text_chars": len(combined_text),
        "mode": "deep",
    }

    return features


def extract_features(company_name: str, text: str) -> dict:
    """Extract structured company features from research text using keyword heuristics.

    Designed to work with both basic (3-query) and deep (8-query + scrape) text corpora.
    More text → more keyword matches → higher-fidelity intensity scores.
    """
    text_lower = text.lower()

    # ── Employee count extraction (expanded patterns) ────────────────────────
    employee_count = None
    emp_patterns = [
        r'(\d[\d,]+)\s*(?:employees|staff|team members|people|workers)',
        r'(?:employs?|workforce of|headcount[:\s]*|team of)\s*(\d[\d,]+)',
        r'(\d[\d,]+)\+?\s*(?:employee)',
        r'(?:approximately|about|over|more than|nearly|~)\s*(\d[\d,]+)\s*(?:employees|people|staff)',
        r'(?:company size|team size)[:\s]*(\d[\d,]+)',
        r'(\d[\d,]+)\s*(?:full-time|FTE)',
    ]
    for pat in emp_patterns:
        m = re.search(pat, text_lower)
        if m:
            raw = m.group(1).replace(',', '')
            count = int(raw)
            # Sanity check: skip values that are clearly not employee counts
            if 5 <= count <= 500000:
                employee_count = count
                break

    # ── Funding extraction (expanded patterns) ───────────────────────────────
    funding = None
    fund_patterns = [
        r'\$(\d+(?:\.\d+)?)\s*(billion|million|B|M)\s*(?:in\s+)?(?:total\s+)?(?:funding|raised|capital|investment|valuation|revenue)',
        r'(?:raised|funding of|valued at|total funding|series [a-z] of)\s*\$(\d+(?:\.\d+)?)\s*(billion|million|B|M)',
        r'(?:revenue of|annual revenue|arr of)\s*\$(\d+(?:\.\d+)?)\s*(billion|million|B|M)',
        r'\$(\d+(?:\.\d+)?)(B|M)\s+(?:valuation|funding)',
    ]
    for pat in fund_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            amount = float(m.group(1))
            unit = m.group(2).lower()
            if unit in ('billion', 'b'):
                funding = amount * 1e9
            elif unit in ('million', 'm'):
                funding = amount * 1e6
            break

    # ── Founded year ─────────────────────────────────────────────────────────
    founded_year = None
    founded_patterns = [
        r'(?:founded|established|started|incorporated|launched)\s*(?:in\s+)?(\d{4})',
        r'(?:since|est\.?)\s*(\d{4})',
    ]
    for pat in founded_patterns:
        m = re.search(pat, text_lower)
        if m:
            yr = int(m.group(1))
            if 1900 <= yr <= 2026:
                founded_year = yr
                break

    # ── Boolean signals (expanded keyword lists) ─────────────────────────────
    ai_keywords = [
        'artificial intelligence', 'machine learning', 'deep learning', 'ai-powered',
        'ai features', 'neural network', 'nlp', 'natural language processing',
        'generative ai', 'llm', 'large language model', 'copilot', 'ai assistant',
        'computer vision', 'predictive model', 'recommendation engine', 'chatbot',
        'intelligent automation', 'ai/ml', 'openai', 'anthropic', 'gpt',
        'transformer model', 'fine-tuning', 'embeddings', 'vector search',
        'rag', 'retrieval augmented', 'prompt engineering',
    ]
    ai_match_count = sum(1 for kw in ai_keywords if kw in text_lower)
    has_ai_features = ai_match_count >= 1

    cloud_keywords = [
        'cloud-native', 'aws', 'amazon web services', 'azure', 'google cloud', 'gcp',
        'kubernetes', 'k8s', 'docker', 'microservices', 'saas', 'cloud platform',
        'serverless', 'lambda', 'terraform', 'infrastructure as code', 'ci/cd',
        'containerized', 'cloud-first', 'multi-cloud', 'cloudflare', 'vercel',
        'heroku', 'digital ocean', 'cloud infrastructure',
    ]
    cloud_match_count = sum(1 for kw in cloud_keywords if kw in text_lower)
    cloud_native = cloud_match_count >= 1

    public_keywords = [
        'publicly traded', 'ipo', 'nasdaq', 'nyse', 'stock price',
        'ticker', 'market cap', 'sec filing', 'annual report', '10-k',
        'quarterly earnings', 'public company', 'stock symbol', 'shareholders',
    ]
    is_public = any(kw in text_lower for kw in public_keywords)

    # ── Intensity scores (1-5) — keyword density with depth-aware scaling ────
    # With deeper text, we count actual occurrences (not just presence)
    # to differentiate "mentions AI once" from "AI is core to the product"

    api_keywords = [
        'api', 'rest api', 'graphql', 'webhook', 'integration', 'sdk',
        'developer platform', 'marketplace', 'ecosystem', 'open platform',
        'developer tools', 'api-first', 'developer experience', 'dev portal',
        'third-party', 'zapier', 'extensible', 'plugins',
    ]
    api_count = sum(1 for kw in api_keywords if kw in text_lower)
    api_ecosystem = min(5.0, 1.5 + api_count * 0.4)

    data_keywords = [
        'data platform', 'data warehouse', 'big data', 'analytics', 'dashboard',
        'data lake', 'real-time data', 'data pipeline', 'etl', 'data-driven',
        'business intelligence', 'reporting', 'data science', 'data engineering',
        'data mesh', 'data catalog', 'data governance', 'snowflake', 'databricks',
        'redshift', 'bigquery',
    ]
    data_count = sum(1 for kw in data_keywords if kw in text_lower)
    data_richness = min(5.0, 1.5 + data_count * 0.45)

    reg_keywords = [
        'compliance', 'gdpr', 'hipaa', 'sox', 'regulated', 'regulatory',
        'audit', 'certification', 'iso', 'fedramp', 'soc 2', 'soc2',
        'pci dss', 'pci compliance', 'data protection', 'privacy',
        'ccpa', 'risk management', 'governance framework',
    ]
    reg_count = sum(1 for kw in reg_keywords if kw in text_lower)
    regulatory_burden = min(5.0, 1.5 + reg_count * 0.45)

    market_keywords = [
        'market leader', 'industry leader', 'dominant', '#1', 'leading provider',
        'largest', 'top player', 'pioneer', 'category leader', 'unicorn',
        'market share', 'industry-leading', 'best-in-class', 'trusted by',
        'fortune 500', 'enterprise customers', 'thousands of customers',
        'global leader', 'award-winning',
    ]
    mkt_count = sum(1 for kw in market_keywords if kw in text_lower)
    market_position = min(5.0, 2.0 + mkt_count * 0.5)

    # ── AI depth signal: use match count for better scoring in deep mode ─────
    # Feeds into ai_product_features and ai_momentum with more nuance
    ai_intensity = min(5.0, 1.0 + ai_match_count * 0.35) if ai_match_count > 0 else 1.0
    cloud_intensity = min(5.0, 1.0 + cloud_match_count * 0.4) if cloud_match_count > 0 else 1.0

    # Vertical detection
    vertical = detect_vertical(text_lower)

    # Website extraction
    website = None
    m = re.search(r'(?:https?://)?(?:www\.)?([a-z0-9-]+\.(?:com|io|co|ai|tech|org|net))', text_lower)
    if m:
        website = f"https://{m.group(0)}"

    return {
        "vertical": vertical,
        "website": website,
        "founded_year": founded_year,
        "employee_count": employee_count,
        "funding_total_usd": funding,
        "is_public": is_public,
        "has_ai_features": has_ai_features,
        "cloud_native": cloud_native,
        "api_ecosystem_strength": round(api_ecosystem, 1),
        "data_richness": round(data_richness, 1),
        "regulatory_burden": round(regulatory_burden, 1),
        "market_position": round(market_position, 1),
        # Depth-aware intensity signals (used by estimate_dimension_scores)
        "ai_intensity": round(ai_intensity, 2),
        "cloud_intensity": round(cloud_intensity, 2),
    }


def detect_vertical(text: str) -> str:
    """Detect industry vertical from text content."""
    verticals = {
        "Healthcare/Life Sciences": ["healthcare", "health tech", "biotech", "pharmaceutical", "medical", "clinical", "patient"],
        "Financial Services": ["fintech", "banking", "financial", "insurance", "payments", "lending", "credit"],
        "E-commerce/Retail": ["e-commerce", "ecommerce", "retail", "shopping", "marketplace", "consumer"],
        "Enterprise Software": ["enterprise", "saas", "b2b software", "crm", "erp", "workflow"],
        "Cybersecurity": ["cybersecurity", "security", "infosec", "threat detection", "identity"],
        "Education": ["edtech", "education", "learning platform", "lms", "school"],
        "Real Estate/PropTech": ["real estate", "proptech", "property", "housing"],
        "HR/Workforce": ["hr tech", "human resources", "workforce", "recruiting", "talent"],
        "Marketing/AdTech": ["martech", "advertising", "marketing platform", "ad tech"],
        "Supply Chain/Logistics": ["supply chain", "logistics", "shipping", "freight", "warehouse"],
        "Construction": ["construction", "building", "contractor"],
        "Legal Tech": ["legal tech", "law firm", "legal"],
        "Data & Analytics": ["data analytics", "business intelligence", "data platform"],
        "AI/ML Platform": ["ai platform", "machine learning platform", "mlops"],
        "DevOps/Infrastructure": ["devops", "infrastructure", "cloud infrastructure", "platform engineering"],
    }
    scores = {}
    for vertical, keywords in verticals.items():
        count = sum(1 for kw in keywords if kw in text)
        if count > 0:
            scores[vertical] = count
    if scores:
        return max(scores, key=scores.get)
    return "Technology"


# ── Heuristic dimension scorer ────────────────────────────────────────────────

def estimate_dimension_scores(data: dict) -> dict[str, float]:
    """Estimate 17-dimension scores from extracted company features.

    Uses both boolean signals (has_ai, cloud) AND intensity signals
    (ai_intensity, cloud_intensity) for more nuanced scoring when
    deep research data is available.
    """
    scores = {}
    emp = data.get("employee_count") or 100
    funding = data.get("funding_total_usd") or 0
    is_public = data.get("is_public", False)
    has_ai = data.get("has_ai_features", False)
    cloud = data.get("cloud_native", False)
    api_str = data.get("api_ecosystem_strength") or 2.5
    data_rich = data.get("data_richness") or 2.5
    reg_burden = data.get("regulatory_burden") or 2.5
    mkt_pos = data.get("market_position") or 2.5

    # Intensity signals — fall back to binary thresholds for backward compatibility
    ai_int = data.get("ai_intensity") or (3.5 if has_ai else 1.0)
    cloud_int = data.get("cloud_intensity") or (3.5 if cloud else 1.0)

    funding_score = min(5.0, max(1.0, (1.0 + math.log10(max(funding, 1e6)) - 6) * 1.5)) if funding > 0 else 2.0
    size_factor = min(5.0, max(1.0, 1.0 + math.log10(max(emp, 10)) / 1.5))

    # Data & Analytics
    scores["data_quality"] = round(min(5.0, data_rich * 0.7 + size_factor * 0.3), 2)
    scores["data_integration"] = round(min(5.0, api_str * 0.6 + cloud_int * 0.4), 2)
    scores["analytics_maturity"] = round(min(5.0, (data_rich + size_factor + funding_score) / 3), 2)

    # Technology & Infrastructure — use cloud_int for gradient instead of binary
    scores["cloud_architecture"] = round(min(5.0, cloud_int * 0.6 + api_str * 0.4), 2)
    scores["tech_stack_modernity"] = round(min(5.0, cloud_int * 0.45 + funding_score * 0.3 + api_str * 0.25), 2)
    scores["ai_engineering"] = round(min(5.0, ai_int * 0.5 + size_factor * 0.25 + funding_score * 0.25), 2)

    # AI Product & Value — use ai_int for gradient instead of binary
    scores["ai_product_features"] = round(min(5.0, ai_int * 0.65 + mkt_pos * 0.35), 2)
    scores["revenue_ai_upside"] = round(min(5.0, mkt_pos * 0.4 + ai_int * 0.3 + data_rich * 0.3), 2)
    scores["margin_ai_upside"] = round(min(5.0, ai_int * 0.35 + data_rich * 0.3 + cloud_int * 0.35), 2)
    scores["product_differentiation"] = round(min(5.0, mkt_pos * 0.5 + api_str * 0.3 + data_rich * 0.2), 2)

    # Organization & Talent
    scores["ai_talent_density"] = round(min(5.0, ai_int * 0.5 + size_factor * 0.25 + funding_score * 0.25), 2)
    scores["leadership_ai_vision"] = round(min(5.0, ai_int * 0.45 + mkt_pos * 0.3 + funding_score * 0.25), 2)
    scores["org_change_readiness"] = round(min(5.0, size_factor * 0.3 + cloud_int * 0.3 + funding_score * 0.4), 2)
    scores["partner_ecosystem"] = round(min(5.0, api_str * 0.5 + mkt_pos * 0.3 + size_factor * 0.2), 2)

    # Governance & Risk
    scores["ai_governance"] = round(min(5.0, (3.5 if is_public else 2.0) * 0.4 + reg_burden * 0.3 + size_factor * 0.3), 2)
    scores["regulatory_readiness"] = round(min(5.0, (3.5 if is_public else 2.0) * 0.3 + reg_burden * 0.4 + size_factor * 0.3), 2)

    # Velocity & Momentum
    scores["ai_momentum"] = round(min(5.0, ai_int * 0.5 + funding_score * 0.25 + mkt_pos * 0.25), 2)

    return scores


# ── Request / response models ─────────────────────────────────────────────────

class SandboxScoreRequest(BaseModel):
    """User just provides a company name — we handle the rest"""
    company_name: str = Field(..., min_length=1, max_length=200)


class SandboxCompanyResponse(BaseModel):
    id: str
    name: str
    vertical: str
    website: Optional[str]
    description: Optional[str]
    employee_count: Optional[int]
    funding_total_usd: Optional[float]
    is_public: bool
    has_ai_features: bool
    cloud_native: bool
    composite_score: float
    tier: str
    wave: int
    pillar_scores: dict
    category_scores: dict
    dimension_details: list
    research_summary: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/score", response_model=SandboxCompanyResponse)
async def score_company(req: SandboxScoreRequest, db: Session = Depends(get_db)):
    """End-to-end pipeline: company name → web research → scoring → tier classification.

    1. Researches the company using Tavily web search
    2. Extracts structured features (employees, funding, AI signals, etc.)
    3. Estimates 17 AI-maturity dimension scores
    4. Computes weighted composite score and tier classification
    5. Saves to database (sandbox, not portfolio)
    """
    # Check for duplicate name first (before hitting external APIs)
    existing = db.query(Company).filter(Company.name == req.company_name).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Company '{req.company_name}' already exists. Check the Sandbox results.")

    settings = get_settings()

    # 1. Web research
    if not settings.tavily_api_key:
        raise HTTPException(status_code=503, detail="Research API not configured")

    logger.info(f"Researching company (deep mode): {req.company_name}")
    features = await research_company_deep(req.company_name, settings.tavily_api_key)
    research_meta = features.pop("_research_meta", {})
    research_summary = features.pop("research_summary", "")
    logger.info(f"Research complete for '{req.company_name}': {research_meta}")

    # 2. Create company record
    company = Company(
        name=req.company_name,
        vertical=features["vertical"],
        website=features.get("website"),
        description=research_summary[:500] if research_summary else None,
        founded_year=features.get("founded_year"),
        employee_count=features.get("employee_count"),
        funding_total_usd=features.get("funding_total_usd"),
        is_public=features.get("is_public", False),
        has_ai_features=features.get("has_ai_features", False),
        cloud_native=features.get("cloud_native", False),
        api_ecosystem_strength=features.get("api_ecosystem_strength", 2.5),
        data_richness=features.get("data_richness", 2.5),
        regulatory_burden=features.get("regulatory_burden", 2.5),
        market_position=features.get("market_position", 2.5),
        is_portfolio=False,
    )
    db.add(company)
    db.flush()

    # 3. Estimate dimension scores
    pillar_scores = estimate_dimension_scores(features)

    # 4. Save dimension scores
    for dim, score in pillar_scores.items():
        ds = DimensionScore(company_id=company.id, dimension=dim, score=score)
        db.add(ds)

    # 5. Compute composite + tier + wave
    composite = compute_composite(pillar_scores)
    tier = classify_tier(composite)
    wave = assign_wave(composite)
    cat_scores = compute_category_scores(pillar_scores)

    # 6. Save company score
    cs = CompanyScore(
        company_id=company.id,
        composite_score=composite,
        tier=tier,
        wave=wave,
        pillar_scores=pillar_scores,
        category_scores=cat_scores,
    )
    db.add(cs)
    db.commit()

    # 7. Build response
    dimension_details = []
    for dim, score in sorted(pillar_scores.items(), key=lambda x: x[1], reverse=True):
        cat = next((c for c, ds in CATEGORIES.items() if dim in ds), "Other")
        dimension_details.append({
            "dimension": dim,
            "label": DIMENSION_LABELS.get(dim, dim),
            "score": score,
            "category": cat,
            "weight": DERIVED_WEIGHTS.get(dim, 0),
        })

    return SandboxCompanyResponse(
        id=company.id,
        name=company.name,
        vertical=features["vertical"],
        website=features.get("website"),
        description=research_summary[:500] if research_summary else None,
        employee_count=features.get("employee_count"),
        funding_total_usd=features.get("funding_total_usd"),
        is_public=features.get("is_public", False),
        has_ai_features=features.get("has_ai_features", False),
        cloud_native=features.get("cloud_native", False),
        composite_score=composite,
        tier=tier,
        wave=wave,
        pillar_scores=pillar_scores,
        category_scores=cat_scores,
        dimension_details=dimension_details,
        research_summary=research_summary[:1500],
    )


@router.get("/companies")
async def list_sandbox_companies(db: Session = Depends(get_db)):
    """List all sandbox (non-portfolio) companies that were user-submitted."""
    companies = (
        db.query(Company, CompanyScore)
        .join(CompanyScore, Company.id == CompanyScore.company_id)
        .filter(Company.is_portfolio == False)
        .order_by(Company.created_at.desc())
        .all()
    )

    result = []
    for company, score in companies:
        result.append({
            "id": company.id,
            "name": company.name,
            "vertical": company.vertical,
            "website": company.website,
            "description": company.description,
            "employee_count": company.employee_count,
            "funding_total_usd": company.funding_total_usd,
            "composite_score": score.composite_score,
            "tier": score.tier,
            "wave": score.wave,
            "pillar_scores": score.pillar_scores or {},
            "category_scores": score.category_scores or {},
            "created_at": str(company.created_at),
        })
    return result


@router.delete("/companies/{company_id}")
async def delete_sandbox_company(company_id: str, db: Session = Depends(get_db)):
    """Remove a sandbox company and its scores."""
    company = db.query(Company).filter(Company.id == company_id, Company.is_portfolio == False).first()
    if not company:
        raise HTTPException(status_code=404, detail="Sandbox company not found")

    db.query(DimensionScore).filter(DimensionScore.company_id == company_id).delete()
    db.query(CompanyScore).filter(CompanyScore.company_id == company_id).delete()
    db.query(Company).filter(Company.id == company_id).delete()
    db.commit()
    return {"deleted": True, "name": company.name}
