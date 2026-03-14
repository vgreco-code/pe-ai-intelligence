#!/usr/bin/env python3
"""
Real research pipeline for Solen portfolio companies.
Uses Tavily to gather real evidence for each of the 8 AI readiness pillars.
Strategy: Anchor every query on the company name + "software" to avoid contamination
from unrelated companies sharing the same name.
"""

import json
import os
import time
import re
from typing import Dict, List, Any
from tavily import TavilyClient

TAVILY_KEY = "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"
client = TavilyClient(TAVILY_KEY)

# The 14 Solen portfolio companies
# "search_anchor" = what to include in every query to nail the right company
PORTFOLIO_COMPANIES = [
    {
        "name": "Cairn Applications",
        "vertical": "Waste Hauling SaaS",
        "search_anchor": '"Cairn Applications" waste hauling software',
        "domain": "cairnapps.com",
    },
    {
        "name": "SMRTR",
        "vertical": "F&B Supply Chain Compliance",
        "search_anchor": "SMRTR supply chain compliance automation software",
        "domain": "smrtr.io",
    },
    {
        "name": "ViaPeople",
        "vertical": "HR Performance Management",
        "search_anchor": "ViaPeople performance management HR software",
        "domain": "viapeople.com",
    },
    {
        "name": "Track Star",
        "vertical": "Fleet Telematics SaaS",
        "search_anchor": "Track Star fleet telematics GPS tracking software",
        "domain": "trackstar.io",
    },
    {
        "name": "FMSI",
        "vertical": "Credit Union Staffing Analytics",
        "search_anchor": "FMSI credit union staffing analytics software",
        "domain": "fmsi.com",
    },
    {
        "name": "Champ",
        "vertical": "Aviation MRO Software",
        "search_anchor": "Champ Cargosystems aviation MRO software",
        "domain": "champcargosystems.com",
    },
    {
        "name": "TrackIt Transit",
        "vertical": "Public Transit Software",
        "search_anchor": "TrackIt Transit public transit software scheduling",
        "domain": "trackittransit.com",
    },
    {
        "name": "NexTalk",
        "vertical": "Accessibility Communications",
        "search_anchor": "NexTalk accessibility relay communications software",
        "domain": "nextalk.com",
    },
    {
        "name": "Thought Foundry",
        "vertical": "Government Decision Support",
        "search_anchor": "Thought Foundry government analytics decision support software",
        "domain": "thoughtfoundry.com",
    },
    {
        "name": "Spokane",
        "vertical": "Government ERP / Services",
        "search_anchor": "Spokane government ERP services software platform",
        "domain": "spokanecounty.org",
    },
    {
        "name": "Primate",
        "vertical": "Restaurant POS / Tech",
        "search_anchor": "Primate restaurant POS software technology",
        "domain": "primatesoftware.com",
    },
    {
        "name": "ThingTech",
        "vertical": "IoT Asset Tracking",
        "search_anchor": "ThingTech IoT asset tracking platform software",
        "domain": "thingtech.com",
    },
    {
        "name": "Dash",
        "vertical": "Field Service Management",
        "search_anchor": "Dash field service management software platform",
        "domain": "dashsoftware.com",
    },
    {
        "name": "AutoTime",
        "vertical": "Workforce Time & Attendance",
        "search_anchor": "AutoTime workforce time attendance software",
        "domain": "autotime.com",
    },
]

# Pillar queries — always combined with company's search_anchor
PILLAR_SUFFIXES = {
    "data_quality":        "data analytics reporting API integration",
    "workflow_digitization": "workflow automation digital processes",
    "infrastructure":      "cloud SaaS platform technology stack",
    "competitive_position": "market customers reviews competitors G2 Capterra",
    "revenue_upside":      "AI machine learning features product roadmap",
    "margin_upside":       "efficiency automation cost savings ROI",
    "org_readiness":       "engineering team hiring technology",
    "risk_compliance":     "security compliance certifications regulations",
}

# Also run a "general overview" search per company to pick up broad signals
OVERVIEW_QUERY = "{anchor} overview product features"
REVIEWS_QUERY  = "{name} software reviews G2 Capterra customers"

POSITIVE_SIGNALS = {
    "data_quality": [
        "api", "integration", "analytics", "dashboard", "reporting", "data platform",
        "real-time", "bi ", "intelligence", "insights", "data-driven", "export",
        "connector", "webhook", "rest api", "open api"
    ],
    "workflow_digitization": [
        "automation", "workflow", "digital", "streamline", "eliminate manual",
        "paperless", "end-to-end", "no-code", "low-code", "process automation",
        "automate", "scheduling", "dispatch", "routing", "mobile app"
    ],
    "infrastructure": [
        "cloud", "aws", "azure", "google cloud", "saas", "microservices",
        "cloud-native", "scalable", "99.9%", "uptime", "multi-tenant",
        "hosted", "web-based", "mobile", "ios", "android", "app store"
    ],
    "competitive_position": [
        "market leader", "trusted by", "customers", "clients", "users",
        "industry leading", "g2", "capterra", "award", "growing", "leading",
        "largest", "most", "best", "top rated", "recognized"
    ],
    "revenue_upside": [
        "ai", "machine learning", "predictive", "intelligent", "automated",
        "smart", "nlp", "computer vision", "recommendation", "forecast",
        "artificial intelligence", "generative", "copilot", "detection"
    ],
    "margin_upside": [
        "reduce costs", "save time", "efficiency", "roi", "payback", "automate",
        "eliminate", "optimize", "self-service", "scalable", "savings",
        "faster", "less time", "hours saved", "reduce"
    ],
    "org_readiness": [
        "engineering", "technology", "developer", "api", "integration partner",
        "platform", "ecosystem", "modern", "agile", "innovation", "tech",
        "software team", "product team", "r&d", "technical"
    ],
    "risk_compliance": [
        "soc 2", "iso 27001", "hipaa", "gdpr", "compliant", "certified",
        "security", "encryption", "data protection", "audit", "regulatory",
        "privacy", "secure", "compliance", "sox", "pci"
    ],
}

NEGATIVE_SIGNALS = {
    "infrastructure": ["on-premise", "on-prem", "installed software", "server install", "desktop only"],
    "workflow_digitization": ["paper-based", "fax", "phone-only", "manual entry"],
    "revenue_upside": ["no ai features", "rule-based only", "legacy"],
    "competitive_position": ["discontinued", "acquired", "shutting down"],
}


def run_search(query: str, max_results: int = 5) -> List[Dict]:
    """Run a Tavily search and return results."""
    try:
        response = client.search(
            query=query,
            max_results=max_results,
            include_answer=True,
            search_depth="advanced",
        )
        results = response.get("results", [])
        if response.get("answer"):
            results.append({
                "title": "Tavily AI Summary",
                "content": response["answer"],
                "url": "",
                "source": "ai_summary"
            })
        time.sleep(0.4)
        return results
    except Exception as e:
        print(f"    ⚠ Search error: {e}")
        return []


def score_from_evidence(pillar: str, all_text: str) -> Dict:
    """Score a pillar from concatenated search text."""
    text_lower = all_text.lower()

    pos_signals  = POSITIVE_SIGNALS.get(pillar, [])
    neg_signals  = NEGATIVE_SIGNALS.get(pillar, [])

    pos_hits = [s for s in pos_signals if s in text_lower]
    neg_hits = [s for s in neg_signals if s in text_lower]

    signal_ratio = len(pos_hits) / max(len(pos_signals), 1)
    base = 1.5 + (signal_ratio * 3.0) - (len(neg_hits) * 0.4)
    score = round(max(1.0, min(5.0, base)), 1)
    confidence = round(min(0.9, 0.3 + signal_ratio * 0.6), 2)

    return {
        "score": score,
        "confidence": confidence,
        "positive_signals_found": pos_hits[:5],
        "negative_signals_found": neg_hits,
    }


def extract_snippets(results: List[Dict], signals: List[str]) -> List[str]:
    """Pull the most relevant sentence snippets from results."""
    snippets = []
    for r in results:
        content = r.get("content", "")
        for sent in re.split(r'[.!?\n]', content):
            sent = sent.strip()
            if len(sent) > 40 and any(s in sent.lower() for s in signals):
                snippets.append(sent[:220])
                break
        if len(snippets) >= 3:
            break
    return snippets


def calculate_composite_score(pillars: Dict[str, float]) -> float:
    """Weighted composite using model-derived weights."""
    weights = {
        "revenue_upside":      2.86,
        "org_readiness":       2.42,
        "competitive_position":2.17,
        "infrastructure":      1.65,
        "data_quality":        1.33,
        "workflow_digitization":0.99,
        "margin_upside":       0.81,
        "risk_compliance":     0.27,
    }
    total = sum(weights.values())
    weighted = sum(pillars.get(p, 2.5) * w for p, w in weights.items())
    return round(weighted / total, 2)


def assign_tier(score: float) -> str:
    if score >= 4.0: return "AI-Ready"
    if score >= 3.2: return "AI-Buildable"
    if score >= 2.5: return "AI-Emerging"
    return "AI-Limited"


def assign_wave(score: float) -> int:
    if score >= 3.2: return 1
    if score >= 2.8: return 2
    return 3


def research_company(company: Dict) -> Dict:
    """Full research pass on a single portfolio company."""
    print(f"\n  📡  {company['name']}  ({company['vertical']})")

    # 1. Overview search — broad company profile
    overview_results = run_search(
        OVERVIEW_QUERY.format(anchor=company["search_anchor"]), max_results=5
    )
    # 2. Review search — G2/Capterra picks up feature vocabulary well
    review_results = run_search(
        REVIEWS_QUERY.format(name=company["name"]), max_results=3
    )

    base_results = overview_results + review_results
    base_text = " ".join(r.get("content", "") + " " + r.get("title", "") for r in base_results)

    pillar_scores  = {}
    pillar_evidence = {}

    for pillar, suffix in PILLAR_SUFFIXES.items():
        # Targeted pillar search
        query = f"{company['search_anchor']} {suffix}"
        pillar_results = run_search(query, max_results=3)

        # Combine base + pillar-specific text
        combined_text = base_text + " ".join(
            r.get("content", "") + " " + r.get("title", "")
            for r in pillar_results
        )

        ev = score_from_evidence(pillar, combined_text)
        snippets = extract_snippets(
            base_results + pillar_results,
            POSITIVE_SIGNALS.get(pillar, [])
        )
        sources = list({r["url"] for r in base_results + pillar_results if r.get("url")})[:4]

        pillar_scores[pillar]  = ev["score"]
        pillar_evidence[pillar] = {
            **ev,
            "evidence_snippets": snippets,
            "sources": sources,
            "query_used": query,
        }

        badge = "█" * int(ev["score"])
        print(f"    {pillar:30s} {ev['score']:.1f} {badge}  [{len(ev['positive_signals_found'])} signals]")

    composite = calculate_composite_score(pillar_scores)
    tier      = assign_tier(composite)
    wave      = assign_wave(composite)

    print(f"    {'─'*52}")
    print(f"    Composite: {composite:.2f}  │  {tier}  │  Wave {wave}")

    return {
        "name":             company["name"],
        "vertical":         company["vertical"],
        "composite_score":  composite,
        "tier":             tier,
        "wave":             wave,
        "pillar_scores":    pillar_scores,
        "research_evidence":pillar_evidence,
        "data_source":      "tavily_real_v2",
    }


def save_outputs(results: List[Dict]) -> None:
    base = "/sessions/vibrant-tender-allen/solen-ai-intelligence"
    os.makedirs(f"{base}/data/research", exist_ok=True)

    # Full research JSON
    with open(f"{base}/data/research/portfolio_research.json", "w") as f:
        json.dump(results, f, indent=2)

    # Portfolio scores (frontend format)
    portfolio_scores = [
        {
            "name":            r["name"],
            "vertical":        r["vertical"],
            "employee_count":  None,
            "composite_score": r["composite_score"],
            "tier":            r["tier"],
            "wave":            r["wave"],
            "pillar_scores":   r["pillar_scores"],
        }
        for r in results
    ]
    for path in [
        f"{base}/data/demo/portfolio_scores.json",
        f"{base}/frontend/public/portfolio_scores.json",
    ]:
        with open(path, "w") as f:
            json.dump(portfolio_scores, f, indent=2)

    # Wave sequencing
    wave_data = {"Wave 1 (Q1-Q2)": [], "Wave 2 (Q3-Q4)": [], "Wave 3 (Year 2)": []}
    for r in sorted(results, key=lambda x: x["composite_score"], reverse=True):
        entry = {"name": r["name"], "score": r["composite_score"], "tier": r["tier"]}
        key = {1: "Wave 1 (Q1-Q2)", 2: "Wave 2 (Q3-Q4)", 3: "Wave 3 (Year 2)"}[r["wave"]]
        wave_data[key].append(entry)

    for path in [
        f"{base}/data/demo/wave_sequencing.json",
        f"{base}/frontend/public/wave_sequencing.json",
    ]:
        with open(path, "w") as f:
            json.dump(wave_data, f, indent=2)

    # Tier distribution
    tier_dist = {}
    for r in results:
        tier_dist[r["tier"]] = tier_dist.get(r["tier"], 0) + 1
    for path in [
        f"{base}/data/demo/tier_distribution.json",
        f"{base}/frontend/public/tier_distribution.json",
    ]:
        with open(path, "w") as f:
            json.dump(tier_dist, f, indent=2)


def main():
    print("=" * 60)
    print("SOLEN PORTFOLIO — REAL TAVILY RESEARCH  (v2)")
    print("Targeted queries anchored to each company name")
    print("=" * 60)

    results = []
    for company in PORTFOLIO_COMPANIES:
        result = research_company(company)
        results.append(result)

    save_outputs(results)

    print("\n" + "=" * 60)
    print("FINAL PORTFOLIO SCORES (real data)")
    print("=" * 60)
    tier_counts = {}
    for r in sorted(results, key=lambda x: x["composite_score"], reverse=True):
        tier_counts[r["tier"]] = tier_counts.get(r["tier"], 0) + 1
        bar = "█" * int(r["composite_score"])
        print(f"  {r['composite_score']:.2f}  {r['tier']:18s}  W{r['wave']}  {bar}  {r['name']}")

    avg = sum(r["composite_score"] for r in results) / len(results)
    print(f"\nPortfolio avg: {avg:.2f}")

    print("\nTier distribution:")
    for tier in ["AI-Ready", "AI-Buildable", "AI-Emerging", "AI-Limited"]:
        n = tier_counts.get(tier, 0)
        print(f"  {tier:20s} {'█' * n} ({n})")

    print("\nOutputs updated in data/demo/ and frontend/public/")


if __name__ == "__main__":
    main()
