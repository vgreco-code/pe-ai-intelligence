#!/usr/bin/env python3
"""
Real research pipeline for Solen portfolio companies — v3.
Three data source layers:
  1. Direct website scraping (homepage + product pages)
  2. Tavily search (targeted per-pillar + reviews + job postings)
  3. SEC EDGAR (free, for any public companies)
"""

import json
import os
import time
import re
from typing import Dict, List, Any
import httpx
from bs4 import BeautifulSoup
from tavily import TavilyClient

TAVILY_KEY = "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"
tavily = TavilyClient(TAVILY_KEY)

# ─── Portfolio companies ────────────────────────────────────────
PORTFOLIO_COMPANIES = [
    {
        "name": "Cairn Applications",
        "vertical": "Waste Hauling SaaS",
        "anchor": '"Cairn Applications" waste hauling software',
        "urls": ["https://cairnapps.com", "https://www.cairnsoftware.com"],
    },
    {
        "name": "SMRTR",
        "vertical": "F&B Supply Chain Compliance",
        "anchor": "SMRTR supply chain compliance automation software food beverage",
        "urls": ["https://smrtr.io", "https://www.smrtr.com"],
    },
    {
        "name": "ViaPeople",
        "vertical": "HR Performance Management",
        "anchor": "ViaPeople performance management HR software",
        "urls": ["https://www.viapeople.com"],
    },
    {
        "name": "Track Star",
        "vertical": "Fleet Telematics SaaS",
        "anchor": "Track Star fleet telematics GPS tracking software",
        "urls": ["https://www.trackstarinternational.com"],
    },
    {
        "name": "FMSI",
        "vertical": "Credit Union Staffing Analytics",
        "anchor": "FMSI credit union staffing analytics software",
        "urls": ["https://www.fmsi.com"],
    },
    {
        "name": "Champ",
        "vertical": "Aviation MRO Software",
        "anchor": "CHAMP Cargosystems aviation cargo software",
        "urls": ["https://www.champ.aero"],
    },
    {
        "name": "TrackIt Transit",
        "vertical": "Public Transit Software",
        "anchor": "TrackIt Transit public transit fleet software",
        "urls": ["https://www.intueor.com"],
    },
    {
        "name": "NexTalk",
        "vertical": "Accessibility Communications",
        "anchor": "NexTalk accessibility relay interpreting software",
        "urls": ["https://www.nextalk.com"],
    },
    {
        "name": "Thought Foundry",
        "vertical": "Government Decision Support",
        "anchor": "Thought Foundry government analytics decision support",
        "urls": ["https://www.thoughtfoundry.com"],
    },
    {
        "name": "Spokane",
        "vertical": "Government ERP / Services",
        "anchor": "Spokane government ERP services software",
        "urls": ["https://www.spokanecounty.org"],
    },
    {
        "name": "Primate",
        "vertical": "Restaurant POS / Tech",
        "anchor": "Primate restaurant POS technology software",
        "urls": ["https://www.primatesoftware.com"],
    },
    {
        "name": "ThingTech",
        "vertical": "IoT Asset Tracking",
        "anchor": "ThingTech IoT asset tracking platform",
        "urls": ["https://www.thingtech.com"],
    },
    {
        "name": "Dash",
        "vertical": "Field Service Management",
        "anchor": "Dash field service management software dispatch",
        "urls": ["https://www.dashsoftware.com"],
    },
    {
        "name": "AutoTime",
        "vertical": "Workforce Time & Attendance",
        "anchor": "AutoTime workforce time attendance tracking software",
        "urls": ["https://www.autotime.com"],
    },
]

# ─── Keyword signal dictionaries ────────────────────────────────
POSITIVE_SIGNALS = {
    "data_quality": [
        "api", "integration", "analytics", "dashboard", "reporting", "data platform",
        "real-time", "bi ", "intelligence", "insights", "data-driven", "export",
        "connector", "webhook", "rest api", "open api", "data warehouse",
        "import", "sync", "third-party", "partner integration", "marketplace",
    ],
    "workflow_digitization": [
        "automation", "workflow", "digital", "streamline", "eliminate manual",
        "paperless", "end-to-end", "no-code", "low-code", "process automation",
        "automate", "scheduling", "dispatch", "routing", "mobile app",
        "electronic", "instant", "real-time", "online portal", "self-service",
    ],
    "infrastructure": [
        "cloud", "aws", "azure", "google cloud", "saas", "microservices",
        "cloud-native", "scalable", "99.9%", "uptime", "multi-tenant",
        "hosted", "web-based", "mobile", "ios", "android", "app store",
        "docker", "kubernetes", "serverless", "cdn", "ssl", "https",
    ],
    "competitive_position": [
        "market leader", "trusted by", "customers", "clients", "users",
        "industry leading", "g2", "capterra", "award", "growing", "leading",
        "largest", "best", "top rated", "recognized", "featured",
        "case study", "testimonial", "review", "years of experience",
    ],
    "revenue_upside": [
        "ai", "machine learning", "predictive", "intelligent", "automated",
        "smart", "nlp", "computer vision", "recommendation", "forecast",
        "artificial intelligence", "generative", "copilot", "detection",
        "model", "algorithm", "neural", "deep learning", "optimization",
    ],
    "margin_upside": [
        "reduce costs", "save time", "efficiency", "roi", "payback", "automate",
        "eliminate", "optimize", "self-service", "scalable", "savings",
        "faster", "less time", "hours saved", "reduce", "productivity",
        "streamline", "fewer errors", "accuracy", "lower cost",
    ],
    "org_readiness": [
        "engineering", "technology", "developer", "api", "integration partner",
        "platform", "ecosystem", "modern", "agile", "innovation", "tech",
        "software team", "product team", "r&d", "technical", "startup",
        "data scientist", "ml engineer", "ai team", "hiring", "engineers",
    ],
    "risk_compliance": [
        "soc 2", "soc2", "iso 27001", "hipaa", "gdpr", "compliant", "certified",
        "security", "encryption", "data protection", "audit", "regulatory",
        "privacy", "secure", "compliance", "sox", "pci", "fedramp",
        "penetration test", "vulnerability", "backup", "disaster recovery",
    ],
}

NEGATIVE_SIGNALS = {
    "infrastructure": ["on-premise", "on-prem", "installed software", "server install", "desktop only", "windows only"],
    "workflow_digitization": ["paper-based", "fax", "phone-only", "manual entry", "spreadsheet"],
    "revenue_upside": ["no ai", "rule-based only"],
    "competitive_position": ["discontinued", "shutting down"],
}


# ─── Data collection functions ──────────────────────────────────

def scrape_website(url: str) -> str:
    """Directly scrape a company website and return its text content."""
    try:
        r = httpx.get(
            url,
            timeout=15.0,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"},
        )
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        return text[:8000]  # first 8k chars
    except Exception as e:
        return ""


def tavily_search(query: str, max_results: int = 5, depth: str = "advanced") -> List[Dict]:
    """Run a Tavily search, return list of {title, content, url}."""
    try:
        resp = tavily.search(query=query, max_results=max_results,
                             include_answer=True, search_depth=depth)
        results = resp.get("results", [])
        if resp.get("answer"):
            results.append({"title": "AI Summary", "content": resp["answer"], "url": ""})
        time.sleep(0.35)
        return results
    except Exception as e:
        print(f"      ⚠ Tavily error: {e}")
        return []


def search_sec_edgar(company_name: str) -> str:
    """Search SEC EDGAR EFTS for company mentions — free, no key."""
    try:
        r = httpx.get(
            "https://efts.sec.gov/LATEST/search-index",
            params={"q": f'"{company_name}"', "dateRange": "custom",
                    "startdt": "2023-01-01", "enddt": "2026-03-14", "forms": "10-K,10-Q,8-K"},
            headers={"User-Agent": "Solen AI Research vincent.greco@gmail.com"},
            timeout=15.0,
        )
        if r.status_code == 200:
            return r.text[:3000]
    except:
        pass
    return ""


def search_job_postings(company: Dict) -> str:
    """Search for company job postings to gauge org_readiness and tech stack."""
    results = tavily_search(
        f'{company["name"]} software company jobs hiring engineering data science',
        max_results=3,
        depth="basic",
    )
    return " ".join(r.get("content", "") for r in results)


# ─── Scoring logic ──────────────────────────────────────────────

def score_pillar(pillar: str, text: str) -> Dict:
    """Score one pillar from accumulated text evidence."""
    text_lower = text.lower()
    pos = POSITIVE_SIGNALS.get(pillar, [])
    neg = NEGATIVE_SIGNALS.get(pillar, [])
    pos_hits = [s for s in pos if s in text_lower]
    neg_hits = [s for s in neg if s in text_lower]

    ratio = len(pos_hits) / max(len(pos), 1)
    base = 1.5 + (ratio * 3.5) - (len(neg_hits) * 0.4)
    score = round(max(1.0, min(5.0, base)), 1)
    confidence = round(min(0.95, 0.25 + ratio * 0.7), 2)

    return {
        "score": score,
        "confidence": confidence,
        "positive_signals": pos_hits[:6],
        "negative_signals": neg_hits,
        "signal_count": len(pos_hits),
    }


def extract_evidence_snippets(text: str, signals: List[str], n: int = 3) -> List[str]:
    """Pull the best evidence sentences from text."""
    snippets = []
    for sent in re.split(r'[.!?\n]', text):
        sent = sent.strip()
        if 40 < len(sent) < 300 and any(s in sent.lower() for s in signals):
            snippets.append(sent)
            if len(snippets) >= n:
                break
    return snippets


def composite_score(pillars: Dict[str, float]) -> float:
    """Weighted composite using model-derived weights from XGBoost v3."""
    w = {
        "revenue_upside": 2.86, "org_readiness": 2.42,
        "competitive_position": 2.17, "infrastructure": 1.65,
        "data_quality": 1.33, "workflow_digitization": 0.99,
        "margin_upside": 0.81, "risk_compliance": 0.27,
    }
    return round(sum(pillars.get(p, 2.5) * v for p, v in w.items()) / sum(w.values()), 2)


def tier(score: float) -> str:
    if score >= 4.0: return "AI-Ready"
    if score >= 3.2: return "AI-Buildable"
    if score >= 2.5: return "AI-Emerging"
    return "AI-Limited"


def wave(score: float) -> int:
    if score >= 3.2: return 1
    if score >= 2.8: return 2
    return 3


# ─── Main research loop ────────────────────────────────────────

def research_company(company: Dict) -> Dict:
    name = company["name"]
    print(f"\n  {'─'*56}")
    print(f"  📡  {name}  ({company['vertical']})")

    # ── Layer 1: Direct website scrape ──
    website_text = ""
    for url in company.get("urls", []):
        print(f"      🌐 Scraping {url}...")
        page_text = scrape_website(url)
        if page_text:
            website_text += " " + page_text
            print(f"         ✓ {len(page_text)} chars")
        else:
            print(f"         ✗ failed or empty")

    # ── Layer 2: Tavily overview + reviews ──
    print(f"      🔍 Tavily overview search...")
    overview = tavily_search(f'{company["anchor"]} product features overview', max_results=5)
    overview_text = " ".join(r.get("content", "") + " " + r.get("title", "") for r in overview)

    print(f"      🔍 Tavily reviews search...")
    reviews = tavily_search(f'{name} software reviews G2 Capterra customers', max_results=3, depth="basic")
    review_text = " ".join(r.get("content", "") + " " + r.get("title", "") for r in reviews)

    # ── Layer 3: Job postings (for org_readiness + infrastructure) ──
    print(f"      🔍 Job postings search...")
    jobs_text = search_job_postings(company)

    # ── Layer 4: SEC EDGAR (for public companies, compliance) ──
    print(f"      🔍 SEC EDGAR search...")
    sec_text = search_sec_edgar(name)

    # ── Combine all text ──
    # Website text gets 2× weight because it's the most trustworthy source
    base_corpus = f"{website_text} {website_text} {overview_text} {review_text}"
    full_corpus = f"{base_corpus} {jobs_text} {sec_text}"

    # ── Score each pillar ──
    pillar_scores = {}
    pillar_evidence = {}
    pillar_keys = [
        "data_quality", "workflow_digitization", "infrastructure", "competitive_position",
        "revenue_upside", "margin_upside", "org_readiness", "risk_compliance"
    ]

    # Per-pillar targeted searches for the weakest signals
    for pillar in pillar_keys:
        pillar_suffix = {
            "data_quality":        "data analytics API reporting integration",
            "workflow_digitization":"workflow automation digital process",
            "infrastructure":      "cloud SaaS technology platform hosting",
            "competitive_position":"market customers reviews award leader",
            "revenue_upside":      "AI machine learning predictive features",
            "margin_upside":       "efficiency cost savings automation ROI",
            "org_readiness":       "engineering team technology hiring developers",
            "risk_compliance":     "security compliance SOC2 HIPAA certification",
        }[pillar]

        # Use org_readiness text corpus = base + job postings
        if pillar == "org_readiness":
            pillar_corpus = f"{full_corpus}"
        elif pillar == "risk_compliance":
            pillar_corpus = f"{full_corpus}"
        else:
            pillar_corpus = base_corpus

        # For pillars with weak signals, run an additional targeted search
        quick_check = score_pillar(pillar, pillar_corpus)
        if quick_check["signal_count"] < 4:
            extra = tavily_search(f'{company["anchor"]} {pillar_suffix}', max_results=3, depth="basic")
            extra_text = " ".join(r.get("content", "") for r in extra)
            pillar_corpus += " " + extra_text

        ev = score_pillar(pillar, pillar_corpus)
        snippets = extract_evidence_snippets(pillar_corpus, POSITIVE_SIGNALS.get(pillar, []))
        all_sources = list({r.get("url", "") for r in overview + reviews if r.get("url")})[:4]

        pillar_scores[pillar] = ev["score"]
        pillar_evidence[pillar] = {
            **ev,
            "evidence_snippets": snippets[:2],
            "sources": all_sources,
        }

        bar = "█" * int(ev["score"]) + "░" * (5 - int(ev["score"]))
        print(f"      {pillar:30s} {ev['score']:.1f} {bar}  [{ev['signal_count']:2d} signals]")

    comp = composite_score(pillar_scores)
    t = tier(comp)
    w = wave(comp)
    print(f"      {'─'*48}")
    print(f"      ⚡ Composite: {comp:.2f}  │  {t}  │  Wave {w}")

    return {
        "name": name,
        "vertical": company["vertical"],
        "composite_score": comp,
        "tier": t,
        "wave": w,
        "pillar_scores": pillar_scores,
        "research_evidence": pillar_evidence,
        "data_sources": {
            "website_chars": len(website_text),
            "tavily_results": len(overview) + len(reviews),
            "jobs_chars": len(jobs_text),
            "sec_chars": len(sec_text),
        },
    }


def save_outputs(results: List[Dict]):
    base = "/sessions/vibrant-tender-allen/solen-ai-intelligence"
    os.makedirs(f"{base}/data/research", exist_ok=True)

    with open(f"{base}/data/research/portfolio_research.json", "w") as f:
        json.dump(results, f, indent=2)

    scores = [{
        "name": r["name"], "vertical": r["vertical"], "employee_count": None,
        "composite_score": r["composite_score"], "tier": r["tier"],
        "wave": r["wave"], "pillar_scores": r["pillar_scores"],
    } for r in results]

    for path in [f"{base}/data/demo/portfolio_scores.json",
                 f"{base}/frontend/public/portfolio_scores.json"]:
        with open(path, "w") as f:
            json.dump(scores, f, indent=2)

    wave_data = {"Wave 1 (Q1-Q2)": [], "Wave 2 (Q3-Q4)": [], "Wave 3 (Year 2)": []}
    for r in sorted(results, key=lambda x: x["composite_score"], reverse=True):
        entry = {"name": r["name"], "score": r["composite_score"], "tier": r["tier"]}
        wave_data[{1: "Wave 1 (Q1-Q2)", 2: "Wave 2 (Q3-Q4)", 3: "Wave 3 (Year 2)"}[r["wave"]]].append(entry)

    for path in [f"{base}/data/demo/wave_sequencing.json",
                 f"{base}/frontend/public/wave_sequencing.json"]:
        with open(path, "w") as f:
            json.dump(wave_data, f, indent=2)

    tier_dist = {}
    for r in results:
        tier_dist[r["tier"]] = tier_dist.get(r["tier"], 0) + 1
    for path in [f"{base}/data/demo/tier_distribution.json",
                 f"{base}/frontend/public/tier_distribution.json"]:
        with open(path, "w") as f:
            json.dump(tier_dist, f, indent=2)


def main():
    print("=" * 60)
    print("SOLEN PORTFOLIO RESEARCH  v3")
    print("Sources: Website scrape + Tavily + Job postings + SEC EDGAR")
    print("=" * 60)

    results = []
    for co in PORTFOLIO_COMPANIES:
        results.append(research_company(co))

    save_outputs(results)

    print("\n" + "=" * 60)
    print("FINAL PORTFOLIO SCORES")
    print("=" * 60)

    for r in sorted(results, key=lambda x: x["composite_score"], reverse=True):
        bar = "█" * int(r["composite_score"] * 2)
        src = r["data_sources"]
        print(f"  {r['composite_score']:.2f}  {r['tier']:18s} W{r['wave']}  {bar:12s}  {r['name']}")
        print(f"        web={src['website_chars']:5d}ch  tavily={src['tavily_results']}res  jobs={src['jobs_chars']:4d}ch")

    avg = sum(r["composite_score"] for r in results) / len(results)
    print(f"\n  Portfolio avg: {avg:.2f}")
    tiers = {}
    for r in results:
        tiers[r["tier"]] = tiers.get(r["tier"], 0) + 1
    for t in ["AI-Ready", "AI-Buildable", "AI-Emerging", "AI-Limited"]:
        print(f"  {t:20s} {'█' * tiers.get(t, 0)} ({tiers.get(t, 0)})")


if __name__ == "__main__":
    main()
