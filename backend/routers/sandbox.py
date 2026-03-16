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
    # ── Data & Analytics ───────────────────────────────────────────────────────
    "data_quality": 1.10,           # ↑ from 0.997 — data foundation matters
    "data_integration": 1.00,       # ↑ from 0.913 — API/integration maturity
    "analytics_maturity": 1.20,     # ↑ from 1.126 — can they actually use data?
    # ── Technology & Infrastructure ────────────────────────────────────────────
    "cloud_architecture": 0.80,     # ↑ from 0.559 — cloud-native = AI-ready infra
    "tech_stack_modernity": 0.60,   # ↑ from 0.297 — legacy tech is a real barrier
    "ai_engineering": 1.00,         # ↑↑ from 0.519 — can they build/deploy AI?
    # ── AI Product & Value ─────────────────────────────────────────────────────
    "ai_product_features": 2.80,    # ↓↓ from 4.447 — was too dominant, inflated by keyword noise
    "revenue_ai_upside": 1.50,      # ↓ from 2.019 — opportunity ≠ readiness
    "margin_ai_upside": 0.80,       # ↑ from 0.644 — automation potential matters
    "product_differentiation": 0.70, # ↑ from 0.481 — moat strength
    # ── Organization & Talent ──────────────────────────────────────────────────
    "ai_talent_density": 1.80,      # ↓ from 2.346 — important but ECF over-penalizes small cos
    "leadership_ai_vision": 1.50,   # ↑ from 1.432 — leadership drives AI adoption
    "org_change_readiness": 0.80,   # ↑ from 0.534 — ability to transform matters
    "partner_ecosystem": 0.90,      # ~ from 0.972
    # ── Governance & Risk ──────────────────────────────────────────────────────
    "ai_governance": 0.50,          # ↑ from 0.422
    "regulatory_readiness": 0.50,   # ↑ from 0.32 — regulated verticals need this
    # ── Velocity & Momentum ────────────────────────────────────────────────────
    "ai_momentum": 0.80,            # ↑↑ from 0.272 — recent activity signals future trajectory
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
    """Classify company into AI maturity tier.

    Thresholds calibrated for PE portfolio realism (v3 model):
      AI-Ready (≥3.5):    Has AI in-product, data infra, and team to execute
      AI-Buildable (≥2.8): Foundation exists, AI buildable with investment
      AI-Emerging (≥2.0):  Early-stage, some signals but needs significant work
      AI-Limited (<2.0):   Major gaps across data, tech, and talent
    """
    if score >= 3.5:
        return "AI-Ready"
    if score >= 2.8:
        return "AI-Buildable"
    if score >= 2.0:
        return "AI-Emerging"
    return "AI-Limited"


def assign_wave(score: float) -> int:
    """Assign implementation wave for AI rollout sequencing.

    Wave 1: Deploy AI immediately (strong foundation)
    Wave 2: Build foundation first, then deploy (6-12 months)
    Wave 3: Significant investment needed (12-24 months)
    """
    if score >= 3.2:
        return 1
    if score >= 2.5:
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


# ── Confidence score ─────────────────────────────────────────────────────────

def compute_confidence_score(features: dict, research_meta: dict) -> dict:
    """Compute a 0-100 research confidence score with a detailed breakdown.

    Measures how much evidence the pipeline gathered — NOT whether the
    company is good, but whether we trust the scoring.

    Five components:
      1. Search Coverage (0-25):  How many search results came back
      2. Scrape Depth (0-20):     How many URLs were successfully scraped
      3. Corpus Volume (0-15):    Total text size of the research corpus
      4. Structured Extraction (0-25): Whether key facts were extracted
                                       (employees, funding, year, website, own domain)
      5. Signal Richness (0-15):  Non-default intensity scores (AI, cloud, API, data)
    """
    breakdown = {}

    # 1. Search coverage: 120 results is perfect (20 queries × 6 results each)
    search_results = research_meta.get("search_results", 0)
    search_pct = min(search_results / 100, 1.0)  # 100+ results = full marks
    breakdown["search_coverage"] = round(search_pct * 25, 1)

    # 2. Scrape depth: 5 URLs is perfect
    urls_scraped = research_meta.get("urls_scraped", 0)
    scrape_pct = min(urls_scraped / 4, 1.0)  # 4+ URLs = full marks
    breakdown["scrape_depth"] = round(scrape_pct * 20, 1)

    # 3. Corpus volume: 180K+ chars of research text is excellent (20 queries + scrapes)
    total_chars = research_meta.get("total_text_chars", 0)
    corpus_pct = min(total_chars / 180000, 1.0)
    breakdown["corpus_volume"] = round(corpus_pct * 15, 1)

    # 4. Structured extraction: 5 points each for key facts found
    struct_score = 0
    if features.get("employee_count"):
        struct_score += 5
    if features.get("funding_total_usd"):
        struct_score += 5
    if features.get("founded_year"):
        struct_score += 5
    if features.get("website"):
        struct_score += 5
    if research_meta.get("own_domain_found"):
        struct_score += 5  # Strong relevance signal — we found the actual company
    breakdown["structured_extraction"] = min(struct_score, 25)

    # 5. Signal richness: non-default AI/cloud/API/data signals
    signal_score = 0
    ai_int = features.get("ai_intensity", 1.0)
    cloud_int = features.get("cloud_intensity", 1.0)
    api_str = features.get("api_ecosystem_strength", 1.5)
    data_rich = features.get("data_richness", 1.5)
    # Each signal that exceeds its default contributes
    if ai_int > 1.0:
        signal_score += min((ai_int - 1.0) / 3.0, 1.0) * 4
    if cloud_int > 1.0:
        signal_score += min((cloud_int - 1.0) / 3.0, 1.0) * 4
    if api_str > 1.5:
        signal_score += min((api_str - 1.5) / 2.5, 1.0) * 3.5
    if data_rich > 1.5:
        signal_score += min((data_rich - 1.5) / 2.5, 1.0) * 3.5
    breakdown["signal_richness"] = round(min(signal_score, 15), 1)

    total = sum(breakdown.values())
    return {
        "total": round(min(total, 100), 0),
        "breakdown": breakdown,
    }


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
    # ── Core scoring queries (8) ────────────────────────────────────────────
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
    # ── Enrichment queries (6) — deeper signal extraction ───────────────────
    # Named AI initiatives & product launches
    '"{company}" AI product features launch announcement OR "AI-powered" OR "machine learning" OR "intelligent"',
    # Customer case studies & testimonials
    '"{company}" customer case study testimonial OR "uses {company}" OR "powered by {company}" OR "customer success"',
    # Recent news, funding, acquisitions, partnerships
    '"{company}" news 2024 2025 OR announcement OR partnership OR acquisition OR funding round OR product launch',
    # Job postings — AI/ML hiring signals
    '"{company}" hiring jobs "machine learning" OR "AI engineer" OR "data scientist" OR "ML engineer" OR "AI product"',
    # Executive team & AI leadership
    '"{company}" CEO CTO leadership team OR "chief technology" OR "chief AI" OR "VP engineering" OR "head of AI"',
    # Technology stack from job postings and tech blogs
    '"{company}" engineering blog OR tech stack OR "we use" OR "built with" OR Python OR React OR Kubernetes OR AWS',
    # ── Dimension-targeted queries (6) — break score clustering ───────────
    # Governance & compliance deep dive (breaks ai_governance + regulatory_readiness clustering)
    '"{company}" SOC2 OR SOC OR GDPR OR HIPAA OR "data privacy" OR "security audit" OR "compliance certification" OR "ISO 27001" OR "data protection officer" OR "privacy policy"',
    # Analytics & BI maturity (breaks analytics_maturity clustering)
    '"{company}" analytics OR dashboard OR "business intelligence" OR Tableau OR PowerBI OR Looker OR "data visualization" OR "reporting platform" OR metrics OR KPI OR "data-driven decisions"',
    # Organizational change & digital transformation (breaks org_change_readiness clustering)
    '"{company}" "digital transformation" OR "agile" OR "organizational change" OR "company culture" OR "innovation" OR "modernization" OR "cloud migration" OR "process automation" OR "change management"',
    # AI/ML team & talent specifics (breaks ai_talent_density clustering)
    '"{company}" "machine learning team" OR "AI team" OR "data science team" OR "ML infrastructure" OR "model training" OR "MLOps" OR "AI research" OR "AI hiring" OR "data engineer" OR "ML platform"',
    # Modern engineering practices (breaks tech_stack_modernity + ai_engineering clustering)
    '"{company}" "CI/CD" OR "continuous integration" OR DevOps OR "code review" OR "automated testing" OR monitoring OR observability OR Datadog OR "feature flags" OR "infrastructure as code" OR microservices',
    # Partnership & integration ecosystem (breaks partner_ecosystem clustering)
    '"{company}" integration OR marketplace OR "app store" OR partner OR "third-party" OR Zapier OR "API partner" OR "technology partner" OR connector OR plugin OR "integration partner" OR ecosystem',
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


# ── Entity-match validation ──────────────────────────────────────────────────

def build_identity_markers(
    company_name: str,
    website: str = None,
    vertical: str = None,
    description: str = None,
) -> dict:
    """Build an identity fingerprint from known company data.

    Used to validate that web research results actually match the target
    company rather than a different entity with the same name.
    """
    markers = {"company_name": company_name.lower()}

    # Extract domain from website (e.g., "nextalk.com" from "https://www.nextalk.com/")
    if website:
        try:
            domain = website.lower().split("//")[-1].split("/")[0].replace("www.", "")
            if domain and "." in domain:
                markers["domain"] = domain
        except Exception:
            pass

    # Vertical keywords (skip short words)
    if vertical:
        stop = {"and", "the", "for", "of"}
        markers["vertical_keywords"] = [
            w.lower() for w in re.split(r'[\s/&]+', vertical) if len(w) > 2 and w.lower() not in stop
        ]

    # Extract meaningful keywords from description
    if description:
        stop_words = {
            "the", "and", "for", "with", "has", "was", "are", "that", "this",
            "from", "been", "have", "will", "its", "they", "their", "which",
            "about", "into", "over", "more", "than", "also", "other", "some",
            "company", "founded", "employees", "revenue", "provides", "based",
        }
        words = [w.lower().strip(".,;:()\"'") for w in description.split()]
        keywords = [w for w in words if len(w) > 3 and w not in stop_words]
        # Take up to 15 unique keywords
        seen = set()
        unique = []
        for w in keywords:
            if w not in seen:
                seen.add(w)
                unique.append(w)
            if len(unique) >= 15:
                break
        markers["desc_keywords"] = unique

    return markers


def _score_result_relevance(
    result: dict,
    company_name: str,
    markers: dict,
) -> float:
    """Score how likely a search result is about the target company (0.0-1.0).

    Uses multiple signals:
      - Company name in text/title (strong)
      - Known website domain in URL (very strong)
      - Vertical keywords in text (moderate)
      - Description keywords in text (moderate)

    Returns 0.5 (neutral) when no identity markers are available.
    """
    content = (result.get("content") or "").lower()
    title = (result.get("title") or "").lower()
    url = (result.get("url") or "").lower()
    text = content + " " + title

    score = 0.0
    max_score = 0.0

    # 1. Company name appears in text/title (weight: 3)
    name_lower = markers.get("company_name", company_name.lower())
    # Try full name and individual significant words
    name_words = [w for w in name_lower.split() if len(w) > 2]
    if name_lower in text:
        score += 3.0
    elif any(w in text for w in name_words):
        score += 1.5  # Partial name match
    max_score += 3.0

    # 2. Website domain in URL or text (weight: 4 — strongest signal)
    domain = markers.get("domain")
    if domain:
        # Check both URL and text content
        domain_root = domain.split(".")[0]  # e.g., "nextalk" from "nextalk.com"
        if domain in url:
            score += 4.0
        elif domain in text:
            score += 3.0
        elif domain_root in url or domain_root in text:
            score += 2.0
        max_score += 4.0

    # 3. Vertical keyword match (weight: 2)
    vertical_kws = markers.get("vertical_keywords", [])
    if vertical_kws:
        matches = sum(1 for kw in vertical_kws if kw in text)
        score += min(matches / max(len(vertical_kws), 1), 1.0) * 2.0
        max_score += 2.0

    # 4. Description keyword match (weight: 2)
    desc_kws = markers.get("desc_keywords", [])
    if desc_kws:
        matches = sum(1 for kw in desc_kws if kw in text)
        score += min(matches / max(len(desc_kws), 1), 1.0) * 2.0
        max_score += 2.0

    # AI Summary results (no URL) get a slight boost — Tavily AI answers
    # are usually synthesized about the queried company
    if result.get("title") == "AI Summary":
        score += 1.0
        max_score += 1.0

    return score / max_score if max_score > 0 else 0.5


def _filter_by_relevance(
    all_results: list[dict],
    company_name: str,
    markers: dict,
    threshold: float = 0.15,
) -> tuple[list[dict], dict]:
    """Filter search results to only those that likely match the target company.

    Returns:
        (filtered_results, stats) where stats has counts of kept/dropped results.
    """
    if not markers or len(markers) <= 1:
        # No identity markers beyond company name — skip validation
        return all_results, {"kept": len(all_results), "dropped": 0, "mode": "unvalidated"}

    kept = []
    dropped = 0

    for r in all_results:
        relevance = _score_result_relevance(r, company_name, markers)
        if relevance >= threshold:
            kept.append(r)
        else:
            dropped += 1
            title = (r.get("title") or "")[:60]
            logger.debug(f"  Dropped irrelevant result (relevance={relevance:.2f}): {title}")

    logger.info(
        f"  Relevance filter: kept {len(kept)}/{len(all_results)} results "
        f"(dropped {dropped} below {threshold} threshold)"
    )

    return kept, {"kept": len(kept), "dropped": dropped, "mode": "validated"}


def _filter_scraped_by_relevance(
    scraped_texts: list[str],
    urls: list[str],
    company_name: str,
    markers: dict,
    threshold: float = 0.10,
) -> list[str]:
    """Filter scraped page content by relevance to the target company.

    More lenient than search result filtering since scraped content is longer
    and more likely to contain some relevant signal even if noisy.
    """
    if not markers or len(markers) <= 1:
        return scraped_texts

    filtered = []
    name_lower = company_name.lower()
    domain = markers.get("domain", "")
    desc_kws = markers.get("desc_keywords", [])
    vert_kws = markers.get("vertical_keywords", [])
    all_kws = desc_kws + vert_kws

    for text, url in zip(scraped_texts, urls):
        text_lower = text.lower()
        url_lower = url.lower()

        # Always keep content from the company's own domain
        if domain and domain in url_lower:
            filtered.append(text)
            continue

        # Check for company name or keyword matches
        name_found = name_lower in text_lower or any(
            w in text_lower for w in name_lower.split() if len(w) > 2
        )
        kw_matches = sum(1 for kw in all_kws if kw in text_lower) if all_kws else 0
        kw_ratio = kw_matches / max(len(all_kws), 1)

        if name_found or kw_ratio >= threshold:
            filtered.append(text)
        else:
            logger.debug(f"  Dropped irrelevant scraped page: {url[:80]}")

    if len(filtered) < len(scraped_texts):
        logger.info(
            f"  Scraped content filter: kept {len(filtered)}/{len(scraped_texts)} pages"
        )

    return filtered


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
        return f"Research data collected for {company_name}. Scoring based on web signals across 14 search queries."

    summary = "\n\n".join(parts)
    return summary[:2500]


async def research_company_deep(
    company_name: str,
    tavily_key: str,
    context_hint: str = "",
    identity_markers: dict = None,
) -> dict:
    """Deep single-company research: 20 targeted queries + URL follow-up scraping.

    Returns the same feature dict as research_company() but with significantly
    richer underlying text, leading to better feature extraction and scoring.

    Args:
        company_name: Company name to research
        tavily_key: Tavily API key
        context_hint: Optional context (e.g., "waste hauling SaaS") to append to queries
                      for disambiguating companies with generic names
        identity_markers: Optional dict from build_identity_markers() for entity-match
                          validation. When provided, search results and scraped pages
                          are filtered to discard content about different companies.
    """
    hint = f" {context_hint}" if context_hint else ""
    queries = [q.format(company=company_name + hint) for q in DEEP_QUERIES]

    # Phase 1: Run all 8 Tavily searches concurrently
    async with httpx.AsyncClient(timeout=30.0) as client:
        search_tasks = [_tavily_search(client, q, tavily_key) for q in queries]
        search_results = await asyncio.gather(*search_tasks, return_exceptions=True)

    # Flatten results
    all_results: list[dict] = []
    for batch in search_results:
        if isinstance(batch, Exception):
            continue
        for r in batch:
            all_results.append(r)

    raw_result_count = len(all_results)
    logger.info(f"Deep research for '{company_name}': {raw_result_count} search results from {len(queries)} queries")

    # Phase 1b: Entity-match validation — filter results about the wrong company
    relevance_stats = {"kept": raw_result_count, "dropped": 0, "mode": "unvalidated"}
    if identity_markers:
        all_results, relevance_stats = _filter_by_relevance(
            all_results, company_name, identity_markers, threshold=0.15
        )

    # Build search content from validated results only
    search_content: list[str] = [r["content"] for r in all_results if r.get("content")]

    # Phase 2: Follow-up scraping on best URLs (from validated results)
    best_urls = _pick_best_urls(all_results, company_name, max_urls=5)
    scraped_content: list[str] = []
    scraped_urls: list[str] = []

    if best_urls:
        async with httpx.AsyncClient(timeout=20.0) as client:
            scrape_tasks = [_scrape_url(client, url) for url in best_urls]
            scrape_results = await asyncio.gather(*scrape_tasks, return_exceptions=True)

        for text, url in zip(scrape_results, best_urls):
            if isinstance(text, str) and len(text) > 100:
                scraped_content.append(text)
                scraped_urls.append(url)

        logger.info(f"Deep research for '{company_name}': scraped {len(scraped_content)}/{len(best_urls)} URLs successfully")

        # Phase 2b: Filter scraped pages by relevance
        if identity_markers and scraped_content:
            scraped_content = _filter_scraped_by_relevance(
                scraped_content, scraped_urls, company_name, identity_markers
            )

    # Combine all text: search summaries first, then scraped pages
    research_text = "\n\n".join(search_content)
    scraped_text = "\n\n".join(scraped_content)
    combined_text = research_text + "\n\n--- SCRAPED PAGE CONTENT ---\n\n" + scraped_text

    # Extract features from the validated corpus
    features = extract_features(company_name, combined_text)

    # Build a clean research summary for display (from validated results)
    features["research_summary"] = _build_display_summary(all_results, company_name)

    # Check if company's own domain was found among scraped URLs
    company_slug = company_name.lower().replace(" ", "").replace("-", "")
    own_domain_scraped = any(
        company_slug in url.lower().replace(".", "").replace("-", "")
        for url in best_urls
    ) if best_urls else False

    # Track data quality signals
    features["_research_meta"] = {
        "queries_sent": len(queries),
        "search_results": raw_result_count,
        "validated_results": relevance_stats["kept"],
        "results_dropped": relevance_stats["dropped"],
        "validation_mode": relevance_stats["mode"],
        "urls_scraped": len(scraped_content),
        "total_text_chars": len(combined_text),
        "own_domain_found": own_domain_scraped,
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

    # ── AI signal extraction — split into STRONG (company-specific) vs GENERIC ─
    # Strong evidence = the company itself builds/ships AI features
    # Generic evidence = AI mentioned in industry context (common in any research)
    ai_strong_keywords = [
        'ai-powered', 'ai features', 'ai assistant', 'copilot', 'chatbot',
        'recommendation engine', 'predictive model', 'intelligent automation',
        'ai/ml pipeline', 'ml model', 'ai-driven', 'ai-enabled',
        'ai product', 'ai solution', 'ai platform',
    ]
    ai_generic_keywords = [
        'artificial intelligence', 'machine learning', 'deep learning',
        'neural network', 'nlp', 'natural language processing',
        'generative ai', 'llm', 'large language model', 'openai', 'anthropic',
        'gpt', 'transformer model', 'fine-tuning', 'embeddings', 'vector search',
        'rag', 'retrieval augmented', 'prompt engineering', 'computer vision',
    ]
    ai_strong_count = sum(1 for kw in ai_strong_keywords if kw in text_lower)
    ai_generic_count = sum(1 for kw in ai_generic_keywords if kw in text_lower)
    ai_match_count = ai_strong_count + ai_generic_count
    has_ai_features = ai_strong_count >= 2 or ai_match_count >= 4  # Stricter: need real evidence

    cloud_keywords = [
        'cloud-native', 'aws', 'amazon web services', 'azure', 'google cloud', 'gcp',
        'kubernetes', 'k8s', 'docker', 'microservices', 'saas', 'cloud platform',
        'serverless', 'lambda', 'terraform', 'infrastructure as code', 'ci/cd',
        'containerized', 'cloud-first', 'multi-cloud', 'cloudflare', 'vercel',
        'heroku', 'digital ocean', 'cloud infrastructure',
    ]
    cloud_match_count = sum(1 for kw in cloud_keywords if kw in text_lower)
    cloud_native = cloud_match_count >= 2  # Stricter: need multiple cloud signals

    public_keywords = [
        'publicly traded', 'ipo', 'nasdaq', 'nyse', 'stock price',
        'ticker', 'market cap', 'sec filing', 'annual report', '10-k',
        'quarterly earnings', 'public company', 'stock symbol', 'shareholders',
    ]
    is_public = any(kw in text_lower for kw in public_keywords)

    # ── Intensity scores (1-5) — recalibrated for PE portco realism ──────────
    # Old model: any 10 keyword matches → 4.5/5.0 (way too generous)
    # New model: strong evidence counts 2x, generic counts 0.5x, with log scaling

    api_keywords = [
        'api', 'rest api', 'graphql', 'webhook', 'integration', 'sdk',
        'developer platform', 'marketplace', 'ecosystem', 'open platform',
        'developer tools', 'api-first', 'developer experience', 'dev portal',
        'third-party', 'zapier', 'extensible', 'plugins',
    ]
    api_count = sum(1 for kw in api_keywords if kw in text_lower)
    api_ecosystem = min(5.0, 1.0 + api_count * 0.3)

    data_keywords = [
        'data platform', 'data warehouse', 'big data', 'analytics', 'dashboard',
        'data lake', 'real-time data', 'data pipeline', 'etl', 'data-driven',
        'business intelligence', 'reporting', 'data science', 'data engineering',
        'data mesh', 'data catalog', 'data governance', 'snowflake', 'databricks',
        'redshift', 'bigquery',
    ]
    data_count = sum(1 for kw in data_keywords if kw in text_lower)
    data_richness = min(5.0, 1.0 + data_count * 0.35)

    reg_keywords = [
        'compliance', 'gdpr', 'hipaa', 'sox', 'regulated', 'regulatory',
        'audit', 'certification', 'iso', 'fedramp', 'soc 2', 'soc2',
        'pci dss', 'pci compliance', 'data protection', 'privacy',
        'ccpa', 'risk management', 'governance framework',
    ]
    reg_count = sum(1 for kw in reg_keywords if kw in text_lower)
    regulatory_burden = min(5.0, 1.0 + reg_count * 0.35)

    market_keywords = [
        'market leader', 'industry leader', 'dominant', '#1', 'leading provider',
        'largest', 'top player', 'pioneer', 'category leader', 'unicorn',
        'market share', 'industry-leading', 'best-in-class', 'trusted by',
        'fortune 500', 'enterprise customers', 'thousands of customers',
        'global leader', 'award-winning',
    ]
    mkt_count = sum(1 for kw in market_keywords if kw in text_lower)
    market_position = min(5.0, 1.5 + mkt_count * 0.4)

    # ── NEW: Governance & compliance depth (breaks ai_governance + regulatory clustering)
    governance_keywords = [
        'soc 2', 'soc2', 'soc 1', 'iso 27001', 'iso 9001', 'fedramp',
        'data protection officer', 'dpo', 'privacy officer', 'chief security officer',
        'security audit', 'penetration testing', 'pen test', 'vulnerability assessment',
        'security operations center', 'soc report', 'aicpa', 'trust services',
        'data processing agreement', 'dpa', 'incident response plan',
        'security framework', 'nist', 'zero trust', 'encryption at rest',
        'access control', 'mfa', 'multi-factor', 'single sign-on', 'sso',
        'data retention policy', 'breach notification', 'privacy impact assessment',
    ]
    gov_count = sum(1 for kw in governance_keywords if kw in text_lower)
    governance_depth = min(5.0, 1.0 + gov_count * 0.4)

    # ── NEW: Analytics maturity depth (breaks analytics_maturity clustering)
    analytics_keywords = [
        'tableau', 'power bi', 'powerbi', 'looker', 'metabase', 'superset',
        'data visualization', 'dashboards', 'self-service analytics', 'ad hoc reporting',
        'data warehouse', 'snowflake', 'databricks', 'redshift', 'bigquery',
        'etl pipeline', 'data pipeline', 'dbt', 'airflow', 'fivetran',
        'data catalog', 'data dictionary', 'data lineage', 'data quality',
        'a/b testing', 'experimentation platform', 'cohort analysis',
        'predictive analytics', 'customer analytics', 'product analytics',
        'mixpanel', 'amplitude', 'heap', 'segment', 'customer data platform',
        'data team', 'data engineering', 'data mesh', 'data lakehouse',
    ]
    analytics_count = sum(1 for kw in analytics_keywords if kw in text_lower)
    analytics_depth = min(5.0, 1.0 + analytics_count * 0.35)

    # ── NEW: Organizational change readiness (breaks org_change_readiness clustering)
    org_change_keywords = [
        'digital transformation', 'cloud migration', 'modernization',
        'agile methodology', 'agile development', 'scrum', 'kanban',
        'devops culture', 'continuous improvement', 'lean', 'six sigma',
        'change management', 'transformation roadmap', 'innovation lab',
        'hackathon', 'r&d', 'research and development', 'skunkworks',
        'process automation', 'workflow automation', 'rpa',
        'cross-functional', 'product-led', 'data-driven culture',
        'upskilling', 'training program', 'learning and development',
        'center of excellence', 'coe', 'ai council', 'innovation team',
    ]
    org_change_count = sum(1 for kw in org_change_keywords if kw in text_lower)
    org_change_depth = min(5.0, 1.0 + org_change_count * 0.4)

    # ── NEW: AI talent signals (breaks ai_talent_density clustering)
    ai_talent_keywords = [
        'machine learning engineer', 'ml engineer', 'ai engineer',
        'data scientist', 'data science team', 'ml team', 'ai team',
        'chief ai officer', 'caio', 'vp of ai', 'head of ai', 'head of ml',
        'director of data science', 'ml infrastructure', 'ml platform',
        'model training', 'model deployment', 'model serving', 'mlops',
        'feature store', 'experiment tracking', 'ml pipeline',
        'ai research', 'research scientist', 'phd', 'computer science',
        'deep learning', 'pytorch', 'tensorflow', 'hugging face',
        'ai intern', 'ml intern', 'ai residency',
    ]
    ai_talent_count = sum(1 for kw in ai_talent_keywords if kw in text_lower)
    ai_talent_depth = min(5.0, 1.0 + ai_talent_count * 0.35)

    # ── NEW: Engineering practices maturity (breaks tech_stack_modernity + ai_engineering)
    eng_practice_keywords = [
        'ci/cd', 'continuous integration', 'continuous deployment', 'continuous delivery',
        'github actions', 'gitlab ci', 'jenkins', 'circleci', 'buildkite',
        'automated testing', 'unit tests', 'integration tests', 'e2e tests',
        'code review', 'pull request', 'peer review', 'pair programming',
        'infrastructure as code', 'terraform', 'pulumi', 'cloudformation',
        'monitoring', 'observability', 'datadog', 'new relic', 'grafana', 'prometheus',
        'feature flags', 'launchdarkly', 'split.io', 'canary deployment',
        'blue-green deployment', 'rolling deployment', 'service mesh', 'istio',
        'api gateway', 'load balancing', 'auto-scaling', 'chaos engineering',
        'sre', 'site reliability', 'incident management', 'pagerduty', 'opsgenie',
    ]
    eng_practice_count = sum(1 for kw in eng_practice_keywords if kw in text_lower)
    eng_practice_depth = min(5.0, 1.0 + eng_practice_count * 0.3)

    # ── NEW: Partnership & integration ecosystem depth (breaks partner_ecosystem)
    partnership_keywords = [
        'integration partner', 'technology partner', 'strategic partner',
        'partner program', 'partner portal', 'reseller', 'channel partner',
        'marketplace listing', 'app marketplace', 'app store',
        'zapier integration', 'make.com', 'workato', 'tray.io',
        'pre-built integration', 'native integration', 'bidirectional sync',
        'open api', 'developer ecosystem', 'partner ecosystem',
        'implementation partner', 'consulting partner', 'si partner',
        'technology alliance', 'certified partner', 'platinum partner',
        'integration catalog', 'connector', 'app directory',
    ]
    partnership_count = sum(1 for kw in partnership_keywords if kw in text_lower)
    partnership_depth = min(5.0, 1.0 + partnership_count * 0.4)

    # ── AI intensity: strong evidence counts double, generic counts half ──────
    # This separates "company actually builds AI" from "article mentions AI"
    ai_weighted = ai_strong_count * 2.0 + ai_generic_count * 0.5
    ai_intensity = min(5.0, 1.0 + ai_weighted * 0.2) if ai_match_count > 0 else 1.0
    cloud_intensity = min(5.0, 1.0 + cloud_match_count * 0.3) if cloud_match_count > 0 else 1.0

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
        # Evidence quality breakdown (strong = company-specific, generic = industry)
        "ai_strong_evidence_count": ai_strong_count,
        "ai_generic_evidence_count": ai_generic_count,
        # ── NEW granular signals for clustered dimensions ─────────────────
        "governance_depth": round(governance_depth, 2),
        "analytics_depth": round(analytics_depth, 2),
        "org_change_depth": round(org_change_depth, 2),
        "ai_talent_depth": round(ai_talent_depth, 2),
        "eng_practice_depth": round(eng_practice_depth, 2),
        "partnership_depth": round(partnership_depth, 2),
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


# ── Plausibility validator ─────────────────────────────────────────────────────

def validate_plausibility(
    features: dict,
    is_pe_portfolio: bool = True,
) -> dict:
    """Cross-check extracted features for plausibility and apply corrections.

    Problem: Companies with generic names (e.g., "Thought Foundry", "Dash",
    "Primate") pull in web results from unrelated entities with the same name.
    This causes wildly inflated funding, employee counts, and intensity scores.

    This validator applies three layers of correction:

    1. PE portfolio reality check:
       - PE portcos are NOT publicly traded (override is_public)
       - Cap funding relative to employee count (a 50-person company
         doesn't have $300M in funding)
       - Cap employee count (PE software portcos are typically <500)

    2. Intensity ceiling by company size:
       - A 10-person company cannot realistically score 5.0 on governance,
         analytics maturity, AI talent, and engineering practices simultaneously
       - Apply a size-aware ceiling to prevent small companies from maxing out

    3. Contamination detection:
       - If too many intensity signals hit 5.0, the data is likely contaminated
       - Apply a broad discount proportional to how many signals are maxed

    Returns a corrected copy of features with a _plausibility_adjustments log.
    """
    data = dict(features)  # Work on a copy
    adjustments = []
    emp = data.get("employee_count") or 50
    funding = data.get("funding_total_usd") or 0

    # ── 1. PE portfolio reality check ─────────────────────────────────────
    if is_pe_portfolio:
        # PE portfolio companies are not publicly traded
        if data.get("is_public"):
            data["is_public"] = False
            adjustments.append("is_public: overridden to False (PE portfolio company)")

        # Funding plausibility: cap at reasonable levels for company size
        # Rule of thumb: funding rarely exceeds ~$500K per employee for PE portcos
        # (most PE software companies are acquired for $20-200M total)
        if funding > 0:
            max_plausible_funding = max(emp * 500_000, 10_000_000)  # At least $10M floor
            if is_pe_portfolio:
                max_plausible_funding = min(max_plausible_funding, 200_000_000)  # Hard cap $200M for PE
            if funding > max_plausible_funding:
                old_funding = funding
                data["funding_total_usd"] = max_plausible_funding
                funding = max_plausible_funding
                adjustments.append(
                    f"funding: ${old_funding/1e6:.0f}M → ${max_plausible_funding/1e6:.0f}M "
                    f"(capped for {emp}-person PE company)"
                )

        # Employee count plausibility: PE software portcos are typically <1000
        if emp > 1000:
            old_emp = emp
            emp = min(emp, 500)
            data["employee_count"] = emp
            adjustments.append(f"employee_count: {old_emp} → {emp} (capped for PE portfolio)")

    # ── 2. Size-aware intensity ceiling ───────────────────────────────────
    # Small companies (< 50 people) can't realistically max out on
    # governance, analytics, AI talent, engineering practices, etc.
    # These capabilities require dedicated teams and budget.
    if emp <= 15:
        intensity_ceiling = 3.0
    elif emp <= 30:
        intensity_ceiling = 3.5
    elif emp <= 75:
        intensity_ceiling = 4.0
    elif emp <= 150:
        intensity_ceiling = 4.5
    else:
        intensity_ceiling = 5.0

    # Apply ceiling to execution-dependent signals
    # (AI intensity and market position are exempt — small companies can
    #  genuinely be AI-focused or market leaders in a niche)
    ceiling_fields = [
        "governance_depth", "analytics_depth", "org_change_depth",
        "ai_talent_depth", "eng_practice_depth", "partnership_depth",
        "data_richness", "regulatory_burden",
    ]
    for field in ceiling_fields:
        val = data.get(field, 0)
        if val > intensity_ceiling:
            data[field] = intensity_ceiling
            adjustments.append(f"{field}: {val:.1f} → {intensity_ceiling:.1f} (size ceiling, {emp} emp)")

    # ── 3. Contamination detection ────────────────────────────────────────
    # If too many signals are at or near their max, the data is likely
    # pulling from multiple unrelated entities. Apply a broad discount.
    intensity_fields = [
        "ai_intensity", "cloud_intensity", "data_richness", "regulatory_burden",
        "market_position", "governance_depth", "analytics_depth", "org_change_depth",
        "ai_talent_depth", "eng_practice_depth", "partnership_depth",
    ]
    near_max_count = sum(1 for f in intensity_fields if data.get(f, 0) >= 4.5)
    total_fields = len(intensity_fields)

    # If more than 60% of signals are near-maxed, likely contamination
    contamination_ratio = near_max_count / total_fields
    if contamination_ratio > 0.6:
        discount = 0.7 + (1.0 - contamination_ratio) * 0.75  # 0.70-0.85 range
        adjustments.append(
            f"contamination_discount: {discount:.2f} applied "
            f"({near_max_count}/{total_fields} signals near-maxed)"
        )
        for field in intensity_fields:
            val = data.get(field, 0)
            if val > 2.0:
                data[field] = round(max(2.0, val * discount), 2)
    elif contamination_ratio > 0.4:
        # Mild contamination — apply lighter discount
        discount = 0.85 + (1.0 - contamination_ratio) * 0.25
        adjustments.append(
            f"mild_contamination_discount: {discount:.2f} applied "
            f"({near_max_count}/{total_fields} signals near-maxed)"
        )
        for field in intensity_fields:
            val = data.get(field, 0)
            if val > 3.0:
                data[field] = round(max(2.5, val * discount), 2)

    data["_plausibility_adjustments"] = adjustments
    if adjustments:
        logger.info(f"  Plausibility adjustments ({len(adjustments)}):")
        for adj in adjustments:
            logger.info(f"    → {adj}")

    return data


# ── Heuristic dimension scorer ────────────────────────────────────────────────

def estimate_dimension_scores(data: dict) -> dict[str, float]:
    """Estimate 17-dimension scores from extracted company features.

    v3 scoring model — calibrated for PE portfolio realism:
    - Execution capacity factor penalizes resource-constrained companies
      on dimensions that require headcount/budget to execute
    - AI evidence quality distinguishes "company ships AI" from "industry has AI"
    - Tighter intensity curves require stronger evidence for high scores
    - Starting-point awareness: small teams get credit for agility but
      discounted on execution-heavy dimensions
    """
    scores = {}
    emp = data.get("employee_count") or 50  # Default 50 (typical PE portco)
    funding = data.get("funding_total_usd") or 0
    is_public = data.get("is_public", False)
    has_ai = data.get("has_ai_features", False)
    cloud = data.get("cloud_native", False)
    api_str = data.get("api_ecosystem_strength") or 2.0
    data_rich = data.get("data_richness") or 2.0
    reg_burden = data.get("regulatory_burden") or 2.0
    mkt_pos = data.get("market_position") or 2.0

    # Intensity signals — fall back to binary thresholds for backward compatibility
    ai_int = data.get("ai_intensity") or (2.5 if has_ai else 1.0)
    cloud_int = data.get("cloud_intensity") or (2.5 if cloud else 1.0)

    # NEW: Granular dimension signals (default to base values for backward compat)
    gov_depth = data.get("governance_depth") or reg_burden
    analytics_depth = data.get("analytics_depth") or data_rich
    org_change = data.get("org_change_depth") or 1.5
    ai_talent = data.get("ai_talent_depth") or ai_int
    eng_practice = data.get("eng_practice_depth") or cloud_int
    partner_depth = data.get("partnership_depth") or api_str

    # ── Execution Capacity Factor (ECF) ──────────────────────────────────────
    # Measures whether the company has the resources to actually execute on AI.
    # Small PE portcos can leverage Solen shared services + external AI vendors,
    # so the penalty for small size should be moderate, not crushing.
    #
    # ECF range: 0.65 (very small) → 1.0 (large enough to execute)
    #   <15 employees:  0.65  — micro team, but can still adopt AI via vendors
    #   15-30:          0.72  — can hire 1-2 ML roles with PE support
    #   30-75:          0.80  — small AI team feasible
    #   75-150:         0.88  — reasonable execution capacity
    #   150-500:        0.94  — solid execution capacity
    #   500+:           1.0   — full execution capacity
    if emp < 15:
        exec_capacity = 0.65
    elif emp < 30:
        exec_capacity = 0.65 + (emp - 15) * 0.0047  # 0.65 → 0.72
    elif emp < 75:
        exec_capacity = 0.72 + (emp - 30) * 0.0018  # 0.72 → 0.80
    elif emp < 150:
        exec_capacity = 0.80 + (emp - 75) * 0.0011  # 0.80 → 0.88
    elif emp < 500:
        exec_capacity = 0.88 + (emp - 150) * 0.00017  # 0.88 → 0.94
    else:
        exec_capacity = min(1.0, 0.94 + (emp - 500) * 0.00012)  # 0.94 → 1.0

    # Funding also contributes to execution capacity (can hire/buy AI talent)
    funding_boost = 0.0
    if funding > 0:
        if funding >= 50e6:
            funding_boost = 0.08
        elif funding >= 10e6:
            funding_boost = 0.05
        elif funding >= 2e6:
            funding_boost = 0.03
    exec_capacity = min(1.0, exec_capacity + funding_boost)

    # ── Base factors ─────────────────────────────────────────────────────────
    funding_score = min(4.5, max(1.0, (1.0 + math.log10(max(funding, 1e6)) - 6) * 1.3)) if funding > 0 else 1.5
    size_factor = min(4.0, max(1.0, 1.0 + math.log10(max(emp, 10)) / 2.0))

    # ── Data & Analytics ─────────────────────────────────────────────────────
    scores["data_quality"] = round(min(5.0, data_rich * 0.5 + analytics_depth * 0.3 + size_factor * 0.2), 2)
    scores["data_integration"] = round(min(5.0, api_str * 0.45 + cloud_int * 0.3 + partner_depth * 0.25), 2)
    # analytics_maturity: now uses dedicated analytics_depth signal
    scores["analytics_maturity"] = round(min(5.0, analytics_depth * 0.45 + data_rich * 0.25 + eng_practice * 0.15 + size_factor * 0.15), 2)

    # ── Technology & Infrastructure ──────────────────────────────────────────
    scores["cloud_architecture"] = round(min(5.0, cloud_int * 0.5 + eng_practice * 0.3 + api_str * 0.2), 2)
    # tech_stack_modernity: now uses engineering practice depth
    scores["tech_stack_modernity"] = round(min(5.0, eng_practice * 0.35 + cloud_int * 0.30 + api_str * 0.20 + funding_score * 0.15), 2)
    # AI engineering: now uses dedicated AI talent + engineering practice signals
    scores["ai_engineering"] = round(min(5.0, (ai_int * 0.30 + ai_talent * 0.25 + eng_practice * 0.25 + size_factor * 0.20) * exec_capacity), 2)

    # ── AI Product & Value ───────────────────────────────────────────────────
    scores["ai_product_features"] = round(min(5.0, ai_int * 0.6 + mkt_pos * 0.25 + (1.0 if has_ai else 0.0) * 0.15 * 5), 2)
    scores["revenue_ai_upside"] = round(min(5.0, mkt_pos * 0.35 + ai_int * 0.3 + data_rich * 0.35), 2)
    scores["margin_ai_upside"] = round(min(5.0, ai_int * 0.3 + data_rich * 0.35 + cloud_int * 0.35), 2)
    scores["product_differentiation"] = round(min(5.0, mkt_pos * 0.45 + partner_depth * 0.30 + data_rich * 0.25), 2)

    # ── Organization & Talent — heavily gated by execution capacity ──────────
    # ai_talent_density: now uses dedicated AI talent depth signal
    scores["ai_talent_density"] = round(min(5.0, (ai_talent * 0.40 + ai_int * 0.20 + size_factor * 0.20 + funding_score * 0.20) * exec_capacity), 2)
    # leadership_ai_vision: now uses org_change signal as indicator of strategic vision
    scores["leadership_ai_vision"] = round(min(5.0, ai_int * 0.30 + org_change * 0.25 + mkt_pos * 0.25 + funding_score * 0.20), 2)
    # org_change_readiness: now uses dedicated org change depth signal
    scores["org_change_readiness"] = round(min(5.0, (org_change * 0.35 + eng_practice * 0.25 + cloud_int * 0.20 + funding_score * 0.20) * exec_capacity), 2)
    # partner_ecosystem: now uses dedicated partnership depth signal
    scores["partner_ecosystem"] = round(min(5.0, partner_depth * 0.40 + api_str * 0.30 + mkt_pos * 0.20 + size_factor * 0.10), 2)

    # ── Governance & Risk ────────────────────────────────────────────────────
    # Now uses dedicated governance depth signal
    scores["ai_governance"] = round(min(5.0, gov_depth * 0.40 + (3.0 if is_public else 1.5) * 0.20 + reg_burden * 0.20 + size_factor * 0.20), 2)
    scores["regulatory_readiness"] = round(min(5.0, gov_depth * 0.35 + reg_burden * 0.30 + (3.0 if is_public else 1.5) * 0.15 + size_factor * 0.20), 2)

    # ── Velocity & Momentum ──────────────────────────────────────────────────
    scores["ai_momentum"] = round(min(5.0, ai_int * 0.35 + org_change * 0.20 + funding_score * 0.20 + mkt_pos * 0.25), 2)

    return scores


# ── Request / response models ─────────────────────────────────────────────────

class SandboxScoreRequest(BaseModel):
    """User provides a company name, plus optional context for entity validation"""
    company_name: str = Field(..., min_length=1, max_length=200)
    website: Optional[str] = Field(None, description="Company website URL for entity-match validation")
    description: Optional[str] = Field(None, max_length=500, description="Brief company description for disambiguation")


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
    confidence_score: Optional[float] = None
    confidence_breakdown: Optional[dict] = None


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

    # 1. Web research with entity-match validation
    if not settings.tavily_api_key:
        raise HTTPException(status_code=503, detail="Research API not configured")

    # Build context hint and identity markers from user-provided context
    context_parts = []
    if req.description:
        context_parts.append(req.description[:60].strip())
    context_hint = " ".join(context_parts) if context_parts else ""

    identity_markers = build_identity_markers(
        company_name=req.company_name,
        website=req.website,
        description=req.description,
    )
    logger.info(
        f"Researching company (deep mode): {req.company_name} | "
        f"markers: domain={identity_markers.get('domain', 'N/A')}, "
        f"desc_kw={identity_markers.get('desc_keywords', [])[:3]}"
    )

    features = await research_company_deep(
        req.company_name, settings.tavily_api_key,
        context_hint=context_hint,
        identity_markers=identity_markers,
    )
    research_meta = features.pop("_research_meta", {})
    research_summary = features.pop("research_summary", "")
    logger.info(
        f"Research complete for '{req.company_name}': {research_meta.get('search_results', 0)} results "
        f"({research_meta.get('validated_results', 'N/A')} validated, "
        f"{research_meta.get('results_dropped', 0)} dropped)"
    )

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

    # 3. Plausibility check + dimension scoring
    features = validate_plausibility(features, is_pe_portfolio=True)
    pillar_scores = estimate_dimension_scores(features)

    # 4. Save dimension scores
    for dim, score in pillar_scores.items():
        ds = DimensionScore(company_id=company.id, dimension=dim, score=score)
        db.add(ds)

    # 5. Compute composite + tier + wave + confidence
    composite = compute_composite(pillar_scores)
    tier = classify_tier(composite)
    wave = assign_wave(composite)
    cat_scores = compute_category_scores(pillar_scores)
    confidence = compute_confidence_score(features, research_meta)

    # 6. Save company score
    cs = CompanyScore(
        company_id=company.id,
        composite_score=composite,
        tier=tier,
        wave=wave,
        pillar_scores=pillar_scores,
        category_scores=cat_scores,
        confidence_score=confidence["total"],
        confidence_breakdown=confidence["breakdown"],
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
        confidence_score=confidence["total"],
        confidence_breakdown=confidence["breakdown"],
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
