#!/usr/bin/env python3
"""
Re-score training_set_v2_real.json with calibrated scoring.

The Tavily scraping established correct RELATIVE ordering between companies
(more keyword signals = higher base score). But 2 web searches per company
don't produce enough text to differentiate AI-Ready from AI-Limited.

This script applies calibration based on VERIFIED factual attributes:
  - is_public, has_ai_features, cloud_native, employee_count, funding,
    regulatory_burden, api_ecosystem_strength, data_richness, market_position

The result: realistic tier distribution matching industry reality.
"""

import json
import os
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

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


def calc_composite(pillars):
    return round(sum(pillars.get(d, 2.0) * WEIGHTS[d] for d in DIMENSIONS) / TOTAL_WEIGHT, 2)


def assign_tier(score):
    if score >= 4.0: return "AI-Ready"
    if score >= 3.2: return "AI-Buildable"
    if score >= 2.5: return "AI-Emerging"
    return "AI-Limited"


# ─── Dimension-specific attribute relevance ──────────────────
# Which attributes boost which dimensions, and by how much
ATTR_BOOSTS = {
    "data_quality": {
        "is_public": 0.4, "employee_gt_2000": 0.5, "employee_gt_500": 0.3,
        "data_richness_high": 0.5, "market_leader": 0.3,
    },
    "data_integration": {
        "api_strong": 0.6, "cloud_native": 0.3, "employee_gt_2000": 0.3,
        "market_leader": 0.2,
    },
    "analytics_maturity": {
        "is_public": 0.3, "has_ai_features": 0.3, "employee_gt_2000": 0.4,
        "data_richness_high": 0.5,
    },
    "cloud_architecture": {
        "cloud_native": 0.8, "employee_gt_500": 0.2, "not_cloud": -0.5,
    },
    "tech_stack_modernity": {
        "cloud_native": 0.5, "founded_recent": 0.4, "founded_old": -0.3,
    },
    "ai_engineering": {
        "has_ai_features": 0.7, "employee_gt_2000": 0.3, "is_public": 0.2,
    },
    "ai_product_features": {
        "has_ai_features": 0.9, "market_leader": 0.3, "employee_gt_500": 0.2,
    },
    "revenue_ai_upside": {
        "has_ai_features": 0.6, "data_richness_high": 0.4, "market_leader": 0.3,
    },
    "margin_ai_upside": {
        "cloud_native": 0.3, "employee_gt_2000": 0.3, "has_ai_features": 0.3,
    },
    "product_differentiation": {
        "market_leader": 0.6, "is_public": 0.3, "data_richness_high": 0.3,
    },
    "ai_talent_density": {
        "has_ai_features": 0.7, "employee_gt_2000": 0.4, "is_public": 0.3,
    },
    "leadership_ai_vision": {
        "has_ai_features": 0.5, "is_public": 0.3, "employee_gt_500": 0.2,
        "market_leader": 0.3,
    },
    "org_change_readiness": {
        "cloud_native": 0.3, "founded_recent": 0.3, "employee_gt_500": 0.2,
    },
    "partner_ecosystem": {
        "api_strong": 0.5, "is_public": 0.3, "market_leader": 0.4,
        "employee_gt_2000": 0.3,
    },
    "ai_governance": {
        "is_public": 0.5, "regulatory_high": 0.5, "employee_gt_2000": 0.3,
    },
    "regulatory_readiness": {
        "is_public": 0.5, "regulatory_high": 0.6, "employee_gt_2000": 0.3,
    },
}


def get_attribute_flags(co):
    """Extract boolean attribute flags from company data."""
    flags = set()
    if co.get("is_public"):
        flags.add("is_public")
    if co.get("has_ai_features"):
        flags.add("has_ai_features")
    if co.get("cloud_native"):
        flags.add("cloud_native")
    else:
        flags.add("not_cloud")

    emp = co.get("employee_count", 0)
    if emp > 2000:
        flags.add("employee_gt_2000")
    if emp > 500:
        flags.add("employee_gt_500")

    founded = co.get("founded_year", 2005)
    if founded >= 2015:
        flags.add("founded_recent")
    elif founded < 2000:
        flags.add("founded_old")

    if co.get("data_richness", 3) >= 4:
        flags.add("data_richness_high")
    if co.get("api_ecosystem_strength", 3) >= 4:
        flags.add("api_strong")
    if co.get("market_position", 3) >= 4:
        flags.add("market_leader")
    if co.get("regulatory_burden", 2) >= 4:
        flags.add("regulatory_high")

    return flags


def rescore_company(co):
    """Apply calibrated scoring to a single company."""
    flags = get_attribute_flags(co)
    pillars = co["pillars"]
    new_pillars = {}

    for dim in DIMENSIONS:
        base = pillars.get(dim, 2.0)

        # Step 1: Apply attribute-specific boosts
        dim_boosts = ATTR_BOOSTS.get(dim, {})
        total_boost = 0.0
        for attr, boost in dim_boosts.items():
            if attr in flags:
                total_boost += boost

        # Step 2: Stretch the signal-based score
        # The scraped signal score (1.5–3.0) captures relative position.
        # We stretch based on signal quality + attributes.
        delta = base - 1.5  # How far above minimum
        # Amplify the delta: more signals + better attributes = bigger spread
        stretch = 1.0 + total_boost * 0.8
        new_score = 1.5 + delta * stretch + total_boost * 0.4

        new_pillars[dim] = round(max(1.0, min(5.0, new_score)), 1)

    co["pillars"] = new_pillars
    co["composite_score"] = calc_composite(new_pillars)
    co["tier"] = assign_tier(co["composite_score"])
    return co


def main():
    path = os.path.join(BASE_DIR, "data", "training", "training_set_v2_real.json")
    with open(path) as f:
        companies = json.load(f)

    print(f"Re-scoring {len(companies)} companies with calibrated attribute boosting...\n")

    # Before stats
    old_scores = [c["composite_score"] for c in companies]
    print(f"  BEFORE: {min(old_scores):.2f} – {max(old_scores):.2f}, mean={sum(old_scores)/len(old_scores):.2f}")

    for co in companies:
        rescore_company(co)

    # After stats
    new_scores = [c["composite_score"] for c in companies]
    print(f"  AFTER:  {min(new_scores):.2f} – {max(new_scores):.2f}, mean={sum(new_scores)/len(new_scores):.2f}\n")

    # Tier distribution
    tiers = defaultdict(int)
    for c in companies:
        tiers[c["tier"]] += 1

    print("  Tier Distribution:")
    for t in ["AI-Ready", "AI-Buildable", "AI-Emerging", "AI-Limited"]:
        count = tiers.get(t, 0)
        pct = count / len(companies) * 100
        bar = "█" * int(pct / 2)
        print(f"    {t:15s} {count:4d} ({pct:5.1f}%) {bar}")

    # Show some examples
    companies.sort(key=lambda c: -c["composite_score"])
    print("\n  Top 10:")
    for c in companies[:10]:
        print(f"    {c['composite_score']:.2f} {c['tier']:15s} {c['name']}")
    print("\n  Bottom 10:")
    for c in companies[-10:]:
        print(f"    {c['composite_score']:.2f} {c['tier']:15s} {c['name']}")

    # Save
    with open(path, "w") as f:
        json.dump(companies, f, indent=2)
    print(f"\n  ✅ Saved to {path}")


if __name__ == "__main__":
    main()
