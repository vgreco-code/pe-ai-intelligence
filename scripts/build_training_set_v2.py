#!/usr/bin/env python3
"""
Build training dataset v2 — expanded 16-dimension AI maturity framework.

Draws from:
  - MITRE AI Maturity Model (6 pillars, 20 dimensions)
  - Gartner AI Maturity (7 areas: strategy, product, governance, engineering, data, ops, culture)
  - McKinsey AI Readiness Index (strategy, data, technology, organization, capabilities)
  - Deloitte PE AI Levers (talent, revenue growth, margin expansion, product differentiation, asset protection)
  - RSM PE AI Due Diligence (data quality → culture, EBITDA line-of-sight)
  - Our original 8-pillar framework

New framework: 16 dimensions in 5 supercategories

  DATA & ANALYTICS FOUNDATION
    1. data_quality          – Data volume, cleanliness, structure, accessibility
    2. data_integration      – API ecosystem, third-party connectors, interoperability
    3. analytics_maturity    – BI dashboards, reporting depth, self-service analytics

  TECHNOLOGY & INFRASTRUCTURE
    4. cloud_architecture    – Cloud-native, multi-tenant, containerized, CI/CD
    5. tech_stack_modernity  – Modern frameworks, microservices vs monolith, devops
    6. ai_engineering        – ML pipelines, model serving, MLOps, feature stores

  AI PRODUCT & VALUE CREATION
    7. ai_product_features   – Existing AI features, NLP, predictions, automation
    8. revenue_ai_upside     – Unrealized AI revenue opportunity, pricing power
    9. margin_ai_upside      – Cost reduction, automation ROI, efficiency gains
   10. product_differentiation – AI as competitive moat, switching costs

  ORGANIZATION & TALENT
   11. ai_talent_density      – ML engineers, data scientists per headcount
   12. leadership_ai_vision   – C-suite AI strategy, AI budget allocation
   13. org_change_readiness   – Culture, training, adoption propensity
   14. partner_ecosystem      – AI/ML vendor relationships, integration partners

  GOVERNANCE & RISK
   15. ai_governance          – Responsible AI policies, model monitoring, ethics
   16. regulatory_readiness   – Industry compliance, data privacy, security posture
"""

import json
import random
import os
from typing import Dict, List, Any
from collections import defaultdict

random.seed(42)

def noise(std=0.15):
    return max(-0.3, min(0.3, random.gauss(0, std)))


# ─── Scoring heuristics for the 16 dimensions ──────────────────
# Each company dict has: name, vertical, founded_year, employee_count,
# funding_total_usd, is_public, has_ai_features, cloud_native,
# api_ecosystem_strength(1-5), data_richness(1-5), regulatory_burden(1-5),
# market_position(1-5)
# NEW FIELDS: ai_talent_pct(0-1), has_ml_pipeline(bool), leadership_ai_score(1-5)

def s_data_quality(co):
    base = co["data_richness"] * 0.8
    if co["employee_count"] > 1000: base += 0.3
    if co["employee_count"] > 5000: base += 0.2
    if co["is_public"]: base += 0.2
    return round(max(1.0, min(5.0, base + noise())), 1)

def s_data_integration(co):
    base = co["api_ecosystem_strength"] * 0.7 + 0.5
    if co["cloud_native"]: base += 0.5
    if co["employee_count"] > 500: base += 0.2
    if co.get("has_ml_pipeline"): base += 0.3
    return round(max(1.0, min(5.0, base + noise())), 1)

def s_analytics_maturity(co):
    base = co["data_richness"] * 0.5 + co["api_ecosystem_strength"] * 0.3
    if co["has_ai_features"]: base += 0.6
    if co["is_public"]: base += 0.3
    if co["employee_count"] > 2000: base += 0.3
    return round(max(1.0, min(5.0, base + noise())), 1)

def s_cloud_architecture(co):
    base = 2.0
    if co["cloud_native"]: base += 1.2
    if co["is_public"]: base += 0.4
    if co["funding_total_usd"] > 100_000_000: base += 0.3
    if co["founded_year"] > 2010: base += 0.5
    elif co["founded_year"] > 2000: base += 0.2
    return round(max(1.0, min(5.0, base + noise())), 1)

def s_tech_stack_modernity(co):
    base = 1.8
    if co["cloud_native"]: base += 1.0
    if co["founded_year"] > 2012: base += 0.7
    elif co["founded_year"] > 2005: base += 0.3
    if co["api_ecosystem_strength"] >= 4: base += 0.5
    if co.get("has_ml_pipeline"): base += 0.4
    return round(max(1.0, min(5.0, base + noise())), 1)

def s_ai_engineering(co):
    base = 1.2
    if co["has_ai_features"]: base += 1.5
    if co.get("has_ml_pipeline"): base += 1.0
    if co.get("ai_talent_pct", 0) > 0.05: base += 0.5
    if co["cloud_native"]: base += 0.3
    if co["employee_count"] > 1000: base += 0.2
    return round(max(1.0, min(5.0, base + noise())), 1)

def s_ai_product_features(co):
    base = 1.5
    if co["has_ai_features"]: base += 1.8
    if co.get("has_ml_pipeline"): base += 0.8
    if co["data_richness"] >= 4: base += 0.4
    if co["funding_total_usd"] > 200_000_000: base += 0.2
    return round(max(1.0, min(5.0, base + noise())), 1)

def s_revenue_ai_upside(co):
    base = 2.0
    if co["has_ai_features"]: base += 0.8
    if co["market_position"] >= 4: base += 0.5
    if co["data_richness"] >= 4: base += 0.5
    if co["cloud_native"]: base += 0.3
    if co["employee_count"] > 500: base += 0.2
    return round(max(1.0, min(5.0, base + noise())), 1)

def s_margin_ai_upside(co):
    base = 2.0
    if co["has_ai_features"]: base += 0.6
    if co["cloud_native"]: base += 0.5
    if co["api_ecosystem_strength"] >= 4: base += 0.4
    if co["data_richness"] >= 3: base += 0.3
    if co["employee_count"] > 500: base += 0.2
    return round(max(1.0, min(5.0, base + noise())), 1)

def s_product_differentiation(co):
    base = co["market_position"] * 0.7
    if co["has_ai_features"]: base += 0.8
    if co["data_richness"] >= 4: base += 0.3
    if co["is_public"]: base += 0.2
    return round(max(1.0, min(5.0, base + noise())), 1)

def s_ai_talent_density(co):
    pct = co.get("ai_talent_pct", 0)
    base = 1.2 + pct * 25  # 0.04 → 2.2, 0.10 → 3.7
    if co["has_ai_features"]: base += 0.5
    if co["employee_count"] > 2000: base += 0.2
    return round(max(1.0, min(5.0, base + noise())), 1)

def s_leadership_ai_vision(co):
    base = co.get("leadership_ai_score", 2.5) * 0.7 + 0.5
    if co["has_ai_features"]: base += 0.5
    if co["is_public"]: base += 0.3
    if co["funding_total_usd"] > 200_000_000: base += 0.3
    return round(max(1.0, min(5.0, base + noise())), 1)

def s_org_change_readiness(co):
    base = 2.5
    if co["cloud_native"]: base += 0.6
    if co["founded_year"] > 2010: base += 0.5
    elif co["founded_year"] > 2000: base += 0.2
    if co["employee_count"] > 500: base += 0.2
    if co["has_ai_features"]: base += 0.3
    return round(max(1.0, min(5.0, base + noise())), 1)

def s_partner_ecosystem(co):
    base = co["api_ecosystem_strength"] * 0.6 + 0.5
    if co["is_public"]: base += 0.4
    if co["market_position"] >= 4: base += 0.4
    if co["employee_count"] > 1000: base += 0.3
    return round(max(1.0, min(5.0, base + noise())), 1)

def s_ai_governance(co):
    base = 1.5
    if co["is_public"]: base += 0.8
    if co["regulatory_burden"] >= 3: base += 0.5
    if co["has_ai_features"]: base += 0.5
    if co["employee_count"] > 2000: base += 0.4
    if co.get("has_ml_pipeline"): base += 0.3
    return round(max(1.0, min(5.0, base + noise())), 1)

def s_regulatory_readiness(co):
    # High regulatory burden → more compliance investment, so score depends on both
    base = 3.0
    if co["regulatory_burden"] >= 4: base += 0.3  # They must handle it
    if co["is_public"]: base += 0.5
    if co["employee_count"] > 2000: base += 0.3
    if not co["cloud_native"]: base -= 0.4  # legacy = harder to secure
    if co["regulatory_burden"] <= 1: base -= 0.3  # no compliance culture
    return round(max(1.0, min(5.0, base + noise())), 1)


SCORE_FNS = {
    "data_quality": s_data_quality,
    "data_integration": s_data_integration,
    "analytics_maturity": s_analytics_maturity,
    "cloud_architecture": s_cloud_architecture,
    "tech_stack_modernity": s_tech_stack_modernity,
    "ai_engineering": s_ai_engineering,
    "ai_product_features": s_ai_product_features,
    "revenue_ai_upside": s_revenue_ai_upside,
    "margin_ai_upside": s_margin_ai_upside,
    "product_differentiation": s_product_differentiation,
    "ai_talent_density": s_ai_talent_density,
    "leadership_ai_vision": s_leadership_ai_vision,
    "org_change_readiness": s_org_change_readiness,
    "partner_ecosystem": s_partner_ecosystem,
    "ai_governance": s_ai_governance,
    "regulatory_readiness": s_regulatory_readiness,
}

DIMENSION_NAMES = list(SCORE_FNS.keys())

# Weights (initial — the model will derive its own)
WEIGHTS = {
    "data_quality": 1.5, "data_integration": 1.0, "analytics_maturity": 1.0,
    "cloud_architecture": 1.0, "tech_stack_modernity": 0.8, "ai_engineering": 1.5,
    "ai_product_features": 1.5, "revenue_ai_upside": 1.5, "margin_ai_upside": 1.0,
    "product_differentiation": 1.2, "ai_talent_density": 1.2, "leadership_ai_vision": 1.0,
    "org_change_readiness": 0.8, "partner_ecosystem": 0.8, "ai_governance": 0.6,
    "regulatory_readiness": 0.6,
}
TOTAL_WEIGHT = sum(WEIGHTS.values())

def calc_composite(pillars):
    weighted = sum(pillars[d] * WEIGHTS[d] for d in DIMENSION_NAMES)
    return round(weighted / TOTAL_WEIGHT, 2)

def assign_tier(score):
    if score >= 4.0: return "AI-Ready"
    if score >= 3.2: return "AI-Buildable"
    if score >= 2.5: return "AI-Emerging"
    return "AI-Limited"


# ─── Helper: add new fields to legacy company dicts ─────────────
def enrich_company(co):
    """Add ai_talent_pct, has_ml_pipeline, leadership_ai_score based on existing fields."""
    co.setdefault("ai_talent_pct", 0)
    co.setdefault("has_ml_pipeline", False)
    co.setdefault("leadership_ai_score", 2.5)

    # Infer from existing attributes
    if co["has_ai_features"]:
        co["ai_talent_pct"] = max(co["ai_talent_pct"], random.uniform(0.02, 0.08))
        co["has_ml_pipeline"] = random.random() < 0.7
        co["leadership_ai_score"] = max(co["leadership_ai_score"], random.uniform(3.0, 4.5))
    else:
        co["ai_talent_pct"] = max(co["ai_talent_pct"], random.uniform(0, 0.02))
        co["has_ml_pipeline"] = random.random() < 0.1
        co["leadership_ai_score"] = max(co["leadership_ai_score"], random.uniform(1.5, 3.0))

    # Public companies / large companies have more governance
    if co["is_public"]:
        co["leadership_ai_score"] = min(5.0, co["leadership_ai_score"] + 0.5)
    if co["employee_count"] > 3000:
        co["ai_talent_pct"] = max(co["ai_talent_pct"], random.uniform(0.01, 0.04))

    return co


# ─── Load the existing v1 training set and enrich ───────────────
def load_v1_companies():
    v1_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "data", "training", "large_training_set.json")
    with open(v1_path) as f:
        companies = json.load(f)

    # v1 already has pillar scores — extract the base attributes
    enriched = []
    for co in companies:
        base = {
            "name": co["name"],
            "vertical": co["vertical"],
            "founded_year": co["founded_year"],
            "employee_count": co["employee_count"],
            "funding_total_usd": co["funding_total_usd"],
            "is_public": co["is_public"],
            "has_ai_features": co["has_ai_features"],
            "cloud_native": co["cloud_native"],
            "api_ecosystem_strength": co["api_ecosystem_strength"],
            "data_richness": co["data_richness"],
            "regulatory_burden": co["regulatory_burden"],
            "market_position": co["market_position"],
        }
        enriched.append(enrich_company(base))
    return enriched


# ─── Main ───────────────────────────────────────────────────────
def main():
    companies = load_v1_companies()
    print(f"Loaded {len(companies)} companies from v1 training set")

    dataset = []
    for co in companies:
        dims = {d: fn(co) for d, fn in SCORE_FNS.items()}
        composite = calc_composite(dims)
        tier = assign_tier(composite)

        entry = {
            "name": co["name"],
            "vertical": co["vertical"],
            "founded_year": co["founded_year"],
            "employee_count": co["employee_count"],
            "funding_total_usd": co["funding_total_usd"],
            "is_public": co["is_public"],
            "has_ai_features": co["has_ai_features"],
            "cloud_native": co["cloud_native"],
            "api_ecosystem_strength": co["api_ecosystem_strength"],
            "data_richness": co["data_richness"],
            "regulatory_burden": co["regulatory_burden"],
            "market_position": co["market_position"],
            "ai_talent_pct": round(co["ai_talent_pct"], 4),
            "has_ml_pipeline": co["has_ml_pipeline"],
            "leadership_ai_score": round(co["leadership_ai_score"], 1),
            "pillars": dims,
            "composite_score": composite,
            "tier": tier,
        }
        dataset.append(entry)

    # Save
    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "data", "training")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "training_set_v2.json")
    with open(out_path, "w") as f:
        json.dump(dataset, f, indent=2)

    print(f"\nSaved {len(dataset)} companies to {out_path}")

    # Stats
    tiers = defaultdict(int)
    for e in dataset:
        tiers[e["tier"]] += 1

    print("\n=== TIER DISTRIBUTION ===")
    for t in ["AI-Ready", "AI-Buildable", "AI-Emerging", "AI-Limited"]:
        print(f"  {t:20s} {tiers[t]:4d}")

    scores = [e["composite_score"] for e in dataset]
    print(f"\n=== SCORE STATS ===")
    print(f"  Mean:   {sum(scores)/len(scores):.2f}")
    print(f"  Min:    {min(scores):.2f}")
    print(f"  Max:    {max(scores):.2f}")
    print(f"  Median: {sorted(scores)[len(scores)//2]:.2f}")
    print(f"\n=== DIMENSIONS ({len(DIMENSION_NAMES)}) ===")
    for d in DIMENSION_NAMES:
        vals = [e["pillars"][d] for e in dataset]
        print(f"  {d:30s}  mean={sum(vals)/len(vals):.2f}  min={min(vals):.1f}  max={max(vals):.1f}")


if __name__ == "__main__":
    main()
