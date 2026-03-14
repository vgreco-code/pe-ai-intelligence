#!/usr/bin/env python3
"""
Real research pipeline v4 — 16-dimension scoring.
Data sources: Website scrape + Tavily search + Job postings + SEC EDGAR
"""

import json
import os
import time
import re
from typing import Dict, List, Any
import httpx
from bs4 import BeautifulSoup
from tavily import TavilyClient

TAVILY_KEY = os.getenv("TAVILY_API_KEY", "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")
tavily = TavilyClient(TAVILY_KEY)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ─── 16 Dimensions ─────────────────────────────────────────────
DIMENSIONS = [
    "data_quality", "data_integration", "analytics_maturity",
    "cloud_architecture", "tech_stack_modernity", "ai_engineering",
    "ai_product_features", "revenue_ai_upside", "margin_ai_upside", "product_differentiation",
    "ai_talent_density", "leadership_ai_vision", "org_change_readiness", "partner_ecosystem",
    "ai_governance", "regulatory_readiness",
]

DIMENSION_LABELS = {
    "data_quality": "Data Quality", "data_integration": "Data Integration",
    "analytics_maturity": "Analytics Maturity", "cloud_architecture": "Cloud Architecture",
    "tech_stack_modernity": "Tech Stack Modernity", "ai_engineering": "AI Engineering",
    "ai_product_features": "AI Product Features", "revenue_ai_upside": "Revenue AI Upside",
    "margin_ai_upside": "Margin AI Upside", "product_differentiation": "Product Differentiation",
    "ai_talent_density": "AI Talent Density", "leadership_ai_vision": "Leadership AI Vision",
    "org_change_readiness": "Org Change Readiness", "partner_ecosystem": "Partner Ecosystem",
    "ai_governance": "AI Governance", "regulatory_readiness": "Regulatory Readiness",
}

WEIGHTS = {
    "data_quality": 1.5, "data_integration": 1.0, "analytics_maturity": 1.0,
    "cloud_architecture": 1.0, "tech_stack_modernity": 0.8, "ai_engineering": 1.5,
    "ai_product_features": 1.5, "revenue_ai_upside": 1.5, "margin_ai_upside": 1.0,
    "product_differentiation": 1.2, "ai_talent_density": 1.2, "leadership_ai_vision": 1.0,
    "org_change_readiness": 0.8, "partner_ecosystem": 0.8, "ai_governance": 0.6,
    "regulatory_readiness": 0.6,
}
TOTAL_WEIGHT = sum(WEIGHTS.values())

# ─── Portfolio companies ────────────────────────────────────────
PORTFOLIO_COMPANIES = [
    {"name": "Cairn Applications", "vertical": "Waste Hauling SaaS", "employee_count": 45,
     "anchor": '"Cairn Applications" waste hauling software', "urls": ["https://cairnapps.com", "https://www.cairnsoftware.com"]},
    {"name": "SMRTR", "vertical": "F&B Supply Chain Compliance", "employee_count": 120,
     "anchor": "SMRTR supply chain compliance automation software food beverage", "urls": ["https://smrtr.io", "https://www.smrtr.com"]},
    {"name": "ViaPeople", "vertical": "HR Performance Management", "employee_count": 65,
     "anchor": "ViaPeople performance management HR software", "urls": ["https://www.viapeople.com"]},
    {"name": "Track Star", "vertical": "Fleet Telematics SaaS", "employee_count": 200,
     "anchor": "Track Star fleet telematics GPS tracking software", "urls": ["https://www.trackstarinternational.com"]},
    {"name": "FMSI", "vertical": "Credit Union Staffing Analytics", "employee_count": 85,
     "anchor": "FMSI credit union staffing analytics software", "urls": ["https://www.fmsi.com"]},
    {"name": "Champ", "vertical": "Public Health EHR", "employee_count": 150,
     "anchor": "CHAMP software public health EHR", "urls": ["https://www.champsoftware.com"]},
    {"name": "TrackIt Transit", "vertical": "Public Transit Software", "employee_count": 30,
     "anchor": "TrackIt Transit public transit fleet software", "urls": ["https://www.intueor.com"]},
    {"name": "NexTalk", "vertical": "Accessibility Communications", "employee_count": 40,
     "anchor": "NexTalk accessibility relay interpreting software", "urls": ["https://www.nextalk.com"]},
    {"name": "Thought Foundry", "vertical": "Entertainment PaaS", "employee_count": 55,
     "anchor": "Thought Foundry entertainment platform software", "urls": ["https://www.thoughtfoundry.com"]},
    {"name": "Spokane", "vertical": "Produce ERP", "employee_count": 70,
     "anchor": "Spokane produce ERP distribution software", "urls": ["https://www.spokane.com"]},
    {"name": "Primate", "vertical": "Energy Control Room", "employee_count": 90,
     "anchor": "Primate energy control room SCADA software", "urls": ["https://www.primatesoftware.com"]},
    {"name": "ThingTech", "vertical": "IoT Asset Tracking", "employee_count": 110,
     "anchor": "ThingTech IoT asset tracking platform", "urls": ["https://www.thingtech.com"]},
    {"name": "Dash", "vertical": "AP & Doc Automation", "employee_count": 60,
     "anchor": "Dash AP document automation software", "urls": ["https://www.dashsoftware.com"]},
    {"name": "AutoTime", "vertical": "A&D Payroll", "employee_count": 75,
     "anchor": "AutoTime workforce time attendance aerospace defense", "urls": ["https://www.autotime.com"]},
]

# ─── Keyword signal dictionaries for 16 dimensions ─────────────
POSITIVE_SIGNALS = {
    "data_quality": [
        "data platform", "data-driven", "proprietary data", "structured data",
        "data warehouse", "data lake", "clean data", "data quality", "data governance",
        "real-time data", "time-series", "historical data", "reporting", "export",
    ],
    "data_integration": [
        "api", "rest api", "graphql", "webhook", "integration", "connector",
        "third-party", "marketplace", "open api", "sdk", "import", "export",
        "sync", "partner integration", "zapier", "interoperability",
    ],
    "analytics_maturity": [
        "analytics", "dashboard", "reporting", "bi ", "business intelligence",
        "insights", "benchmarking", "kpi", "metrics", "visualization",
        "self-service analytics", "drill-down", "data exploration",
    ],
    "cloud_architecture": [
        "cloud", "aws", "azure", "google cloud", "saas", "cloud-native",
        "multi-tenant", "containerized", "docker", "kubernetes", "serverless",
        "microservices", "ci/cd", "99.9%", "uptime", "scalable",
    ],
    "tech_stack_modernity": [
        "react", "typescript", "python", "node.js", "golang", "rust",
        "microservices", "graphql", "kubernetes", "terraform", "devops",
        "modern stack", "spa", "progressive web", "mobile-first",
    ],
    "ai_engineering": [
        "machine learning", "ml pipeline", "model training", "feature store",
        "mlops", "model serving", "tensorflow", "pytorch", "scikit",
        "model monitoring", "a/b testing", "experiment tracking", "ml platform",
    ],
    "ai_product_features": [
        "ai", "artificial intelligence", "machine learning", "predictive",
        "intelligent", "smart", "nlp", "computer vision", "recommendation",
        "generative", "copilot", "chatbot", "automated detection", "classification",
    ],
    "revenue_ai_upside": [
        "ai-powered", "predictive analytics", "optimization", "forecast",
        "recommendation engine", "personalization", "automated insights",
        "intelligent routing", "anomaly detection", "premium tier",
    ],
    "margin_ai_upside": [
        "automate", "automation", "reduce costs", "efficiency", "roi",
        "eliminate manual", "savings", "productivity", "streamline",
        "self-service", "fewer errors", "time saved", "optimize",
    ],
    "product_differentiation": [
        "market leader", "only solution", "unique", "proprietary",
        "patent", "competitive advantage", "moat", "switching cost",
        "industry-specific", "purpose-built", "specialized", "dominant",
    ],
    "ai_talent_density": [
        "data scientist", "ml engineer", "ai team", "machine learning engineer",
        "ai researcher", "deep learning", "nlp engineer", "computer vision engineer",
        "data engineering", "ai hiring", "ai talent",
    ],
    "leadership_ai_vision": [
        "ai strategy", "ai vision", "digital transformation", "innovation",
        "ai roadmap", "chief data officer", "chief ai officer", "ai-first",
        "ai investment", "r&d", "technology leadership",
    ],
    "org_change_readiness": [
        "agile", "modern", "startup culture", "innovation", "growth",
        "training", "upskill", "adoption", "change management",
        "digital culture", "remote-first", "tech-forward",
    ],
    "partner_ecosystem": [
        "partner", "ecosystem", "marketplace", "integration partner",
        "technology partner", "reseller", "channel partner", "alliance",
        "app store", "plugin", "extension", "third-party ecosystem",
    ],
    "ai_governance": [
        "responsible ai", "ai ethics", "model monitoring", "bias detection",
        "explainability", "model governance", "ai risk", "transparency",
        "audit trail", "model validation", "fairness",
    ],
    "regulatory_readiness": [
        "soc 2", "soc2", "iso 27001", "hipaa", "gdpr", "compliant", "certified",
        "security", "encryption", "data protection", "audit", "regulatory",
        "privacy", "pci", "fedramp", "penetration test", "disaster recovery",
    ],
}

NEGATIVE_SIGNALS = {
    "cloud_architecture": ["on-premise", "on-prem", "desktop only", "installed software", "server install"],
    "tech_stack_modernity": ["legacy", "cobol", "vb6", "classic asp", "foxpro"],
    "ai_product_features": ["no ai", "rule-based only", "manual process"],
    "ai_engineering": ["no ml", "spreadsheet-based"],
}

PILLAR_SEARCH_SUFFIX = {
    "data_quality": "data analytics platform reporting",
    "data_integration": "API integration connector third-party",
    "analytics_maturity": "analytics dashboard business intelligence",
    "cloud_architecture": "cloud SaaS platform hosting infrastructure",
    "tech_stack_modernity": "technology stack engineering modern",
    "ai_engineering": "machine learning AI pipeline MLOps",
    "ai_product_features": "AI features machine learning predictive",
    "revenue_ai_upside": "AI revenue growth opportunity product",
    "margin_ai_upside": "automation efficiency cost reduction ROI",
    "product_differentiation": "market leader competitive advantage unique",
    "ai_talent_density": "hiring engineer data scientist ML team",
    "leadership_ai_vision": "AI strategy digital transformation innovation",
    "org_change_readiness": "culture innovation agile growth",
    "partner_ecosystem": "partner ecosystem integration marketplace",
    "ai_governance": "responsible AI governance ethics compliance",
    "regulatory_readiness": "security compliance SOC2 certification HIPAA",
}


# ─── Data collection ───────────────────────────────────────────

def scrape_website(url: str) -> str:
    try:
        r = httpx.get(url, timeout=15.0, follow_redirects=True,
                      headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"})
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        return soup.get_text(separator=" ", strip=True)[:8000]
    except:
        return ""


def tavily_search(query: str, max_results: int = 5, depth: str = "advanced") -> List[Dict]:
    try:
        resp = tavily.search(query=query, max_results=max_results, include_answer=True, search_depth=depth)
        results = resp.get("results", [])
        if resp.get("answer"):
            results.append({"title": "AI Summary", "content": resp["answer"], "url": ""})
        time.sleep(0.35)
        return results
    except Exception as e:
        print(f"      ⚠ Tavily error: {e}")
        return []


def search_sec_edgar(company_name: str) -> str:
    try:
        r = httpx.get("https://efts.sec.gov/LATEST/search-index",
            params={"q": f'"{company_name}"', "dateRange": "custom", "startdt": "2023-01-01", "enddt": "2026-03-14", "forms": "10-K,10-Q,8-K"},
            headers={"User-Agent": "Solen AI Research vincent.greco@gmail.com"}, timeout=15.0)
        if r.status_code == 200:
            return r.text[:3000]
    except:
        pass
    return ""


def search_job_postings(company: Dict) -> str:
    results = tavily_search(f'{company["name"]} software company jobs hiring engineering data science AI', max_results=3, depth="basic")
    return " ".join(r.get("content", "") for r in results)


# ─── Scoring ───────────────────────────────────────────────────

def score_dimension(dim: str, text: str) -> Dict:
    text_lower = text.lower()
    pos = POSITIVE_SIGNALS.get(dim, [])
    neg = NEGATIVE_SIGNALS.get(dim, [])
    pos_hits = [s for s in pos if s in text_lower]
    neg_hits = [s for s in neg if s in text_lower]
    ratio = len(pos_hits) / max(len(pos), 1)
    base = 1.5 + (ratio * 3.5) - (len(neg_hits) * 0.4)
    score = round(max(1.0, min(5.0, base)), 1)
    confidence = round(min(0.95, 0.25 + ratio * 0.7), 2)
    return {"score": score, "confidence": confidence, "positive_signals": pos_hits[:6],
            "negative_signals": neg_hits, "signal_count": len(pos_hits)}


def extract_evidence(text: str, signals: List[str], n: int = 3) -> List[str]:
    snippets = []
    for sent in re.split(r'[.!?\n]', text):
        sent = sent.strip()
        if 40 < len(sent) < 300 and any(s in sent.lower() for s in signals):
            snippets.append(sent)
            if len(snippets) >= n:
                break
    return snippets


def calc_composite(pillars: Dict[str, float]) -> float:
    return round(sum(pillars.get(d, 2.5) * WEIGHTS[d] for d in DIMENSIONS) / TOTAL_WEIGHT, 2)


def get_tier(score: float) -> str:
    if score >= 4.0: return "AI-Ready"
    if score >= 3.2: return "AI-Buildable"
    if score >= 2.5: return "AI-Emerging"
    return "AI-Limited"


# ─── Research ──────────────────────────────────────────────────

def research_company(company: Dict) -> Dict:
    name = company["name"]
    print(f"\n  {'─'*56}")
    print(f"  📡  {name}  ({company['vertical']})")

    # Layer 1: Website scrape
    website_text = ""
    for url in company.get("urls", []):
        print(f"      🌐 Scraping {url}...")
        page = scrape_website(url)
        if page:
            website_text += " " + page
            print(f"         ✓ {len(page)} chars")
        else:
            print(f"         ✗ failed")

    # Layer 2: Tavily overview + reviews
    print(f"      🔍 Tavily overview...")
    overview = tavily_search(f'{company["anchor"]} product features overview', max_results=5)
    overview_text = " ".join(r.get("content", "") + " " + r.get("title", "") for r in overview)

    print(f"      🔍 Tavily reviews...")
    reviews = tavily_search(f'{name} software reviews G2 Capterra', max_results=3, depth="basic")
    review_text = " ".join(r.get("content", "") for r in reviews)

    # Layer 3: Job postings
    print(f"      🔍 Job postings...")
    jobs_text = search_job_postings(company)

    # Layer 4: SEC EDGAR
    print(f"      🔍 SEC EDGAR...")
    sec_text = search_sec_edgar(name)

    # Layer 5: AI/ML specific search
    print(f"      🔍 AI/ML capabilities...")
    ai_results = tavily_search(f'{company["anchor"]} artificial intelligence machine learning features', max_results=3, depth="basic")
    ai_text = " ".join(r.get("content", "") for r in ai_results)

    # Layer 6: Technology stack search
    print(f"      🔍 Tech stack...")
    tech_results = tavily_search(f'{name} software technology stack cloud architecture', max_results=3, depth="basic")
    tech_text = " ".join(r.get("content", "") for r in tech_results)

    # Combine (website 2× weight)
    base_corpus = f"{website_text} {website_text} {overview_text} {review_text}"
    full_corpus = f"{base_corpus} {jobs_text} {sec_text} {ai_text} {tech_text}"

    # Score each dimension
    pillar_scores = {}
    pillar_evidence = {}
    all_sources = list({r.get("url", "") for r in overview + reviews + ai_results + tech_results if r.get("url")})[:6]

    for dim in DIMENSIONS:
        # Choose the best corpus per dimension
        if dim in ("ai_talent_density", "org_change_readiness", "leadership_ai_vision"):
            corpus = f"{full_corpus} {jobs_text}"
        elif dim in ("ai_governance", "regulatory_readiness"):
            corpus = f"{full_corpus} {sec_text}"
        elif dim in ("ai_engineering", "ai_product_features"):
            corpus = f"{full_corpus} {ai_text}"
        elif dim in ("cloud_architecture", "tech_stack_modernity"):
            corpus = f"{full_corpus} {tech_text}"
        else:
            corpus = full_corpus

        quick = score_dimension(dim, corpus)
        if quick["signal_count"] < 3:
            extra = tavily_search(f'{company["anchor"]} {PILLAR_SEARCH_SUFFIX.get(dim, "")}', max_results=2, depth="basic")
            corpus += " " + " ".join(r.get("content", "") for r in extra)

        ev = score_dimension(dim, corpus)
        snippets = extract_evidence(corpus, POSITIVE_SIGNALS.get(dim, []))

        pillar_scores[dim] = ev["score"]
        pillar_evidence[dim] = {
            **ev,
            "evidence_snippets": snippets[:2],
            "sources": all_sources[:3],
        }

        bar = "█" * int(ev["score"]) + "░" * (5 - int(ev["score"]))
        print(f"      {DIMENSION_LABELS.get(dim, dim):30s} {ev['score']:.1f} {bar}  [{ev['signal_count']:2d}]")

    comp = calc_composite(pillar_scores)
    t = get_tier(comp)
    w = 1 if comp >= 3.2 else (2 if comp >= 2.8 else 3)

    # Category averages
    from collections import defaultdict
    CATEGORIES = {
        "Data & Analytics": ["data_quality", "data_integration", "analytics_maturity"],
        "Technology & Infra": ["cloud_architecture", "tech_stack_modernity", "ai_engineering"],
        "AI Product & Value": ["ai_product_features", "revenue_ai_upside", "margin_ai_upside", "product_differentiation"],
        "Organization & Talent": ["ai_talent_density", "leadership_ai_vision", "org_change_readiness", "partner_ecosystem"],
        "Governance & Risk": ["ai_governance", "regulatory_readiness"],
    }
    category_scores = {}
    for cat, dims in CATEGORIES.items():
        cat_vals = [pillar_scores.get(d, 2.5) for d in dims]
        category_scores[cat] = round(sum(cat_vals) / len(cat_vals), 2)

    print(f"      {'─'*48}")
    print(f"      ⚡ Composite: {comp:.2f}  │  {t}  │  Wave {w}")

    return {
        "name": name,
        "vertical": company["vertical"],
        "employee_count": company.get("employee_count", 0),
        "composite_score": comp,
        "tier": t,
        "wave": w,
        "pillar_scores": pillar_scores,
        "category_scores": category_scores,
        "research_evidence": pillar_evidence,
        "data_sources": {
            "website_chars": len(website_text),
            "tavily_results": len(overview) + len(reviews) + len(ai_results) + len(tech_results),
            "jobs_chars": len(jobs_text),
            "sec_chars": len(sec_text),
        },
    }


def save_outputs(results: List[Dict]):
    os.makedirs(os.path.join(BASE_DIR, "data", "research"), exist_ok=True)

    with open(os.path.join(BASE_DIR, "data", "research", "portfolio_research_v2.json"), "w") as f:
        json.dump(results, f, indent=2)

    scores = [{
        "name": r["name"], "vertical": r["vertical"],
        "employee_count": r.get("employee_count", 0),
        "description": "", "website": "", "founded_year": 0,
        "composite_score": r["composite_score"], "tier": r["tier"],
        "wave": r["wave"], "pillar_scores": r["pillar_scores"],
        "category_scores": r.get("category_scores", {}),
    } for r in results]

    for path in [os.path.join(BASE_DIR, "data", "demo", "portfolio_scores.json"),
                 os.path.join(BASE_DIR, "frontend", "public", "portfolio_scores.json")]:
        with open(path, "w") as f:
            json.dump(scores, f, indent=2)

    waves = {"Wave 1 (Q1-Q2)": [], "Wave 2 (Q3-Q4)": [], "Wave 3 (Year 2)": []}
    for r in sorted(results, key=lambda x: x["composite_score"], reverse=True):
        entry = {"name": r["name"], "score": r["composite_score"], "tier": r["tier"]}
        waves[{1: "Wave 1 (Q1-Q2)", 2: "Wave 2 (Q3-Q4)", 3: "Wave 3 (Year 2)"}[r["wave"]]].append(entry)

    tiers = {}
    for r in results:
        tiers[r["tier"]] = tiers.get(r["tier"], 0) + 1

    for fname, data in [("wave_sequencing.json", waves), ("tier_distribution.json", tiers)]:
        for path in [os.path.join(BASE_DIR, "data", "demo", fname),
                     os.path.join(BASE_DIR, "frontend", "public", fname)]:
            with open(path, "w") as f:
                json.dump(data, f, indent=2)

    print(f"\n  ✓ Saved all outputs")


def main():
    print("=" * 60)
    print("SOLEN PORTFOLIO RESEARCH  v4 (16 dimensions)")
    print("Sources: Website + Tavily + Jobs + SEC EDGAR + AI/Tech search")
    print("=" * 60)

    results = []
    for co in PORTFOLIO_COMPANIES:
        results.append(research_company(co))

    save_outputs(results)

    print("\n" + "=" * 60)
    print("FINAL PORTFOLIO SCORES (16 dimensions)")
    print("=" * 60)

    for r in sorted(results, key=lambda x: x["composite_score"], reverse=True):
        bar = "█" * int(r["composite_score"] * 2)
        src = r["data_sources"]
        print(f"  {r['composite_score']:.2f}  {r['tier']:18s} W{r['wave']}  {bar:12s}  {r['name']}")
        print(f"        web={src['website_chars']:5d}ch  tavily={src['tavily_results']}res  jobs={src['jobs_chars']:4d}ch")

    avg = sum(r["composite_score"] for r in results) / len(results)
    print(f"\n  Portfolio avg: {avg:.2f}")


if __name__ == "__main__":
    main()
