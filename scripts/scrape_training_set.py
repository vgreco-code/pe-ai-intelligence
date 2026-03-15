#!/usr/bin/env python3
"""
Scrape real data for ALL 515 training companies and re-score on 16 dimensions.

Strategy (lean, 2-3 API calls per company):
  1. Tavily search: "{company} {vertical} software product features AI cloud"
  2. Tavily search: "{company} software reviews compliance security hiring"
  3. Score 16 dimensions from combined text using keyword signal matching

~1,100 Tavily calls total. Estimated runtime: 15-20 minutes.
"""

import json
import os
import sys
import time
import re
import traceback
from typing import Dict, List
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

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

WEIGHTS = {
    "data_quality": 1.5, "data_integration": 1.0, "analytics_maturity": 1.0,
    "cloud_architecture": 1.0, "tech_stack_modernity": 0.8, "ai_engineering": 1.5,
    "ai_product_features": 1.5, "revenue_ai_upside": 1.5, "margin_ai_upside": 1.0,
    "product_differentiation": 1.2, "ai_talent_density": 1.2, "leadership_ai_vision": 1.0,
    "org_change_readiness": 0.8, "partner_ecosystem": 0.8, "ai_governance": 0.6,
    "regulatory_readiness": 0.6,
}
TOTAL_WEIGHT = sum(WEIGHTS.values())

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
    "cloud_architecture": ["on-premise", "on-prem", "desktop only", "installed software"],
    "tech_stack_modernity": ["legacy", "cobol", "vb6", "classic asp", "foxpro"],
    "ai_product_features": ["no ai", "rule-based only"],
    "ai_engineering": ["no ml", "spreadsheet-based"],
}


# ─── Scoring ───────────────────────────────────────────────────

def score_dimension(dim: str, text: str, co: dict = None) -> dict:
    """Score a dimension using keyword signals + factual company attributes.

    The keyword signals come from real scraped data.
    The attribute modifiers come from verified company facts
    (public/private, has AI features, cloud-native, employee count).
    """
    text_lower = text.lower()
    pos = POSITIVE_SIGNALS.get(dim, [])
    neg = NEGATIVE_SIGNALS.get(dim, [])
    pos_hits = [s for s in pos if s in text_lower]
    neg_hits = [s for s in neg if s in text_lower]

    # More generous base: each signal worth more since we have limited text
    n_hits = len(pos_hits)
    if n_hits == 0:
        base = 1.5
    elif n_hits <= 2:
        base = 2.0 + n_hits * 0.25
    elif n_hits <= 5:
        base = 2.5 + (n_hits - 2) * 0.3
    elif n_hits <= 8:
        base = 3.4 + (n_hits - 5) * 0.2
    else:
        base = 4.0 + min((n_hits - 8) * 0.15, 0.8)

    base -= len(neg_hits) * 0.3

    # Apply factual attribute modifiers (these are real data, not heuristic)
    if co:
        # AI dimensions get a boost from verified AI capabilities
        if dim in ("ai_product_features", "ai_engineering", "revenue_ai_upside", "ai_talent_density"):
            if co.get("has_ai_features"):
                base += 0.4
        # Cloud dimensions boosted by verified cloud-native status
        if dim in ("cloud_architecture", "tech_stack_modernity"):
            if co.get("cloud_native"):
                base += 0.4
            else:
                base -= 0.2
        # Governance dimensions boosted by public company status
        if dim in ("ai_governance", "regulatory_readiness"):
            if co.get("is_public"):
                base += 0.4
            if co.get("regulatory_burden", 2) >= 4:
                base += 0.2
        # Scale/maturity boost for larger companies
        if co.get("employee_count", 0) > 2000:
            if dim in ("data_quality", "data_integration", "analytics_maturity", "partner_ecosystem"):
                base += 0.3
        if co.get("employee_count", 0) > 500:
            if dim in ("org_change_readiness", "leadership_ai_vision"):
                base += 0.15

    score = round(max(1.0, min(5.0, base)), 1)
    return {"score": score, "signals": n_hits, "neg": len(neg_hits)}


def calc_composite(pillars: Dict[str, float]) -> float:
    return round(sum(pillars.get(d, 2.0) * WEIGHTS[d] for d in DIMENSIONS) / TOTAL_WEIGHT, 2)


def assign_tier(score: float) -> str:
    if score >= 4.0: return "AI-Ready"
    if score >= 3.2: return "AI-Buildable"
    if score >= 2.5: return "AI-Emerging"
    return "AI-Limited"


# ─── Tavily search ─────────────────────────────────────────────

def tavily_search(query: str, max_results: int = 5) -> str:
    """Run Tavily search, return combined text."""
    try:
        resp = tavily.search(
            query=query,
            max_results=max_results,
            include_answer=True,
            search_depth="basic",
        )
        parts = []
        for r in resp.get("results", []):
            parts.append(r.get("content", ""))
            parts.append(r.get("title", ""))
        if resp.get("answer"):
            parts.append(resp["answer"])
        time.sleep(0.3)  # Rate limit
        return " ".join(parts)
    except Exception as e:
        time.sleep(1.0)
        return ""


# ─── Per-company research ──────────────────────────────────────

def research_company(co: dict, index: int, total: int) -> dict:
    """Scrape real data for one company, score 16 dimensions."""
    name = co["name"]
    vertical = co["vertical"]
    anchor = f'"{name}" {vertical} software'

    # Search 1: Product + AI + Technology
    text1 = tavily_search(f'{anchor} product features AI cloud technology platform', max_results=5)

    # Search 2: Reviews + Compliance + Hiring
    text2 = tavily_search(f'{anchor} reviews compliance security hiring engineering', max_results=5)

    combined = f"{text1} {text2}"
    text_len = len(combined)

    # Score all 16 dimensions
    pillar_scores = {}
    total_signals = 0
    for dim in DIMENSIONS:
        result = score_dimension(dim, combined, co)
        pillar_scores[dim] = result["score"]
        total_signals += result["signals"]

    composite = calc_composite(pillar_scores)
    tier = assign_tier(composite)

    # Progress indicator
    bar = "█" * int(composite * 2) + "░" * (10 - int(composite * 2))
    print(f"  [{index+1:3d}/{total}] {composite:.2f} {tier:15s} {bar} {name[:35]:35s} ({text_len:5d}ch, {total_signals:2d}sig)")

    return {
        "name": name,
        "vertical": vertical,
        "founded_year": co.get("founded_year", 0),
        "employee_count": co.get("employee_count", 0),
        "funding_total_usd": co.get("funding_total_usd", 0),
        "is_public": co.get("is_public", False),
        "has_ai_features": co.get("has_ai_features", False),
        "cloud_native": co.get("cloud_native", False),
        "api_ecosystem_strength": co.get("api_ecosystem_strength", 3),
        "data_richness": co.get("data_richness", 3),
        "regulatory_burden": co.get("regulatory_burden", 2),
        "market_position": co.get("market_position", 3),
        "pillars": pillar_scores,
        "composite_score": composite,
        "tier": tier,
        "text_chars": text_len,
        "signal_count": total_signals,
    }


# ─── Main ──────────────────────────────────────────────────────

def main():
    # Load existing training set
    with open(os.path.join(BASE_DIR, "data", "training", "training_set_v2.json")) as f:
        companies = json.load(f)

    total = len(companies)
    print("=" * 75)
    print(f"SCRAPING REAL DATA FOR {total} TRAINING COMPANIES")
    print(f"Strategy: 2 Tavily searches per company → ~{total * 2} API calls")
    print(f"Estimated time: ~{total * 2 * 0.5 / 60:.0f} minutes")
    print("=" * 75)

    # Check for checkpoint (resume support)
    checkpoint_path = os.path.join(BASE_DIR, "data", "training", "_scrape_checkpoint.json")
    results = []
    start_idx = 0

    if os.path.exists(checkpoint_path):
        with open(checkpoint_path) as f:
            checkpoint = json.load(f)
        results = checkpoint.get("results", [])
        start_idx = len(results)
        print(f"\n  ⚡ Resuming from checkpoint: {start_idx}/{total} already done\n")

    try:
        for i in range(start_idx, total):
            co = companies[i]
            result = research_company(co, i, total)
            results.append(result)

            # Save checkpoint every 25 companies
            if (i + 1) % 25 == 0:
                with open(checkpoint_path, "w") as f:
                    json.dump({"results": results}, f)
                print(f"  💾 Checkpoint saved ({i+1}/{total})")

    except KeyboardInterrupt:
        print(f"\n\n  ⚠ Interrupted at {len(results)}/{total}. Saving checkpoint...")
        with open(checkpoint_path, "w") as f:
            json.dump({"results": results}, f)
        print(f"  💾 Checkpoint saved. Re-run to resume.")
        sys.exit(1)

    except Exception as e:
        print(f"\n\n  ⚠ Error at company {len(results)}: {e}")
        traceback.print_exc()
        with open(checkpoint_path, "w") as f:
            json.dump({"results": results}, f)
        print(f"  💾 Checkpoint saved at {len(results)}/{total}. Re-run to resume.")
        sys.exit(1)

    # ─── Save final output ─────────────────────────────────────
    out_path = os.path.join(BASE_DIR, "data", "training", "training_set_v2_real.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)

    # Clean up checkpoint
    if os.path.exists(checkpoint_path):
        os.remove(checkpoint_path)

    # ─── Stats ─────────────────────────────────────────────────
    tiers = defaultdict(int)
    scores = []
    low_signal = 0
    for r in results:
        tiers[r["tier"]] += 1
        scores.append(r["composite_score"])
        if r["signal_count"] < 5:
            low_signal += 1

    print(f"\n{'='*75}")
    print(f"SCRAPING COMPLETE — {len(results)} companies")
    print(f"{'='*75}")
    print(f"  Output: {out_path}")
    print(f"\n  Tier Distribution:")
    for t in ["AI-Ready", "AI-Buildable", "AI-Emerging", "AI-Limited"]:
        count = tiers.get(t, 0)
        pct = count / len(results) * 100
        bar = "█" * int(pct / 2)
        print(f"    {t:15s} {count:4d} ({pct:5.1f}%) {bar}")
    print(f"\n  Score Stats:")
    print(f"    Mean:   {sum(scores)/len(scores):.2f}")
    print(f"    Min:    {min(scores):.2f}")
    print(f"    Max:    {max(scores):.2f}")
    print(f"    Median: {sorted(scores)[len(scores)//2]:.2f}")
    print(f"\n  Data Quality:")
    print(f"    Low-signal companies (<5 signals): {low_signal} ({low_signal/len(results)*100:.1f}%)")
    avg_chars = sum(r["text_chars"] for r in results) / len(results)
    print(f"    Avg text per company: {avg_chars:.0f} chars")


if __name__ == "__main__":
    main()
