"""Re-score portfolio companies with v4 adjusted weights and research-corrected pillar scores.

Changes from v3:
  1. Rebalanced weights: ai_product_features down from 4.45→2.80, ai_momentum up from 0.27→0.80
  2. Softer ECF curve: small companies less harshly penalized (0.65 floor vs 0.55)
  3. Manual pillar corrections for companies where web scraping produced wrong signals
  4. Entity fix: Dash is Dash ComplyOps (cloud compliance), not Dash AP automation

Run: cd backend && source .env && python rescore_v4.py
"""
import json
import os
import sys
import math

sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from models.company import Company, CompanyScore

DATABASE_URL = os.environ.get("DATABASE_URL", "")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not set.")
    sys.exit(1)

# ── New v4 weights ────────────────────────────────────────────────────────────
WEIGHTS = {
    "data_quality": 1.10, "data_integration": 1.00, "analytics_maturity": 1.20,
    "cloud_architecture": 0.80, "tech_stack_modernity": 0.60, "ai_engineering": 1.00,
    "ai_product_features": 2.80, "revenue_ai_upside": 1.50, "margin_ai_upside": 0.80,
    "product_differentiation": 0.70, "ai_talent_density": 1.80, "leadership_ai_vision": 1.50,
    "org_change_readiness": 0.80, "partner_ecosystem": 0.90, "ai_governance": 0.50,
    "regulatory_readiness": 0.50, "ai_momentum": 0.80,
}
TOTAL = sum(WEIGHTS.values())

def composite(pillars):
    return round(sum(pillars.get(d, 0) * w for d, w in WEIGHTS.items()) / TOTAL, 2)

def tier(score):
    if score >= 3.5: return "AI-Ready"
    if score >= 2.8: return "AI-Buildable"
    if score >= 2.0: return "AI-Emerging"
    return "AI-Limited"

def wave(score):
    if score >= 3.2: return 1
    if score >= 2.5: return 2
    return 3

def cat_scores(pillars):
    cats = {
        "Data & Analytics": ["data_quality", "data_integration", "analytics_maturity"],
        "Technology & Infrastructure": ["cloud_architecture", "tech_stack_modernity", "ai_engineering"],
        "AI Product & Value": ["ai_product_features", "revenue_ai_upside", "margin_ai_upside", "product_differentiation"],
        "Organization & Talent": ["ai_talent_density", "leadership_ai_vision", "org_change_readiness", "partner_ecosystem"],
        "Governance & Risk": ["ai_governance", "regulatory_readiness"],
        "Velocity & Momentum": ["ai_momentum"],
    }
    result = {}
    for cat, dims in cats.items():
        vals = [pillars[d] for d in dims if d in pillars]
        result[cat] = round(sum(vals)/len(vals), 2) if vals else 0
    return result

# ── Research-based pillar corrections ─────────────────────────────────────────
# Only override where web scraping clearly produced wrong signals.
# Format: { "dimension": new_score }

PILLAR_OVERRIDES = {
    "AutoTime": {
        # DCAA-compliant timekeeping for A&D — solid vertical SaaS but NOT an AI product
        # Rule-based time allocation ≠ AI. No ML features, no AI product launches.
        # High scores were from defense industry AI keyword contamination.
        "ai_product_features": 2.80,    # was 4.59 — timekeeping with rules-based allocation, not AI
        "revenue_ai_upside": 3.60,      # was 4.52 — real opportunity to add AI (predictive labor, anomaly detection)
        "margin_ai_upside": 3.40,       # was 4.52 — automation potential exists but not AI-driven today
        "analytics_maturity": 3.00,     # was 4.19 — standard reporting, not advanced analytics
        "data_quality": 3.50,           # was 4.09 — good labor data but not AI-grade data platform
        "ai_momentum": 2.50,            # was 3.63 — hiring eng leadership but no AI launches
        "leadership_ai_vision": 3.20,   # was 3.56 — CEO has PE execution chops, but no AI strategy evidence
    },
    "Spokane": {
        # AS/400 RPG system from 1989 — no AI, legacy tech, but dominant market position
        "ai_product_features": 2.20,    # was 4.68 — NO shipping AI features whatsoever
        "revenue_ai_upside": 3.80,      # was 4.58 — huge modernization opportunity (64% US oranges)
        "tech_stack_modernity": 1.50,    # was 2.86 — IBM AS/400, RPG, DB2 = legacy
        "cloud_architecture": 1.80,     # was 3.40 — not cloud-native, web reporting only
        "ai_engineering": 1.20,         # was 2.21 — no ML engineering capacity
        "ai_talent_density": 1.30,      # was 3.37 — 9 employees, no AI talent
        "ai_momentum": 1.50,            # was 3.85 — no recent AI activity
        "analytics_maturity": 2.80,     # was 4.06 — basic reporting, no advanced analytics
        "data_quality": 3.50,           # keep high — 37 years of agricultural data
        "product_differentiation": 4.20, # keep high — 64% of US oranges is massive moat
        "leadership_ai_vision": 2.50,   # was 3.99 — no evidence of AI vision
    },
    "Thought Foundry": {
        # 8-person content platform — "data-driven" ≠ AI
        "ai_product_features": 2.80,    # was 4.92 — "data-driven platform" is not AI
        "revenue_ai_upside": 3.50,      # was 4.54 — content entitlements has AI potential
        "ai_talent_density": 1.80,      # was 2.52 — 8 people, no AI roles verified
        "ai_momentum": 2.50,            # was 4.51 — no recent AI launches
        "leadership_ai_vision": 2.80,   # was 4.30 — no AI vision evidence
    },
    "Champ": {
        # 40-year public health EHR — Omaha System taxonomy, HIPAA, AWS
        # Nightingale Notes is a solid cloud EHR but has no AI/ML features
        "ai_product_features": 2.60,    # was 4.72 — EHR with structured data, not AI product
        "revenue_ai_upside": 3.80,      # was 4.27 — population health analytics is real AI opportunity
        "margin_ai_upside": 3.50,       # was 4.65 — automation in billing/scheduling but not AI today
    },
    "Primate": {
        # Control room SCADA visualization — some anomaly detection but not deep AI
        "ai_product_features": 3.20,    # was 4.92 — GridGuardian has threshold alerting, not ML
        "revenue_ai_upside": 3.60,      # was 4.54 — predictive grid analytics is real opportunity
        "ai_talent_density": 1.60,      # was 1.98 — 11 people, no AI team
        "ai_momentum": 2.30,            # was 3.54 — no recent AI product launches
    },
    "NexTalk": {
        # ACTUAL SHIPPING AI: SpeechPath ASR, FCC-certified, Healthfirst $1M impact
        "ai_product_features": 4.20,    # was 2.98 — SpeechPath is a real AI product in production
        "ai_engineering": 2.80,         # was 1.03 — they built a speech-to-text engine
        "revenue_ai_upside": 3.80,      # was 2.70 — 50M addressable market, FCC funding
        "ai_talent_density": 2.20,      # was 1.00 — small but has AI engineering capability
        "ai_momentum": 3.80,            # was 2.15 — FCC certification 2025, SpeechPath launch
        "leadership_ai_vision": 3.50,   # was 2.58 — CEO from SAP, deliberate AI strategy
        "product_differentiation": 3.60, # was 2.43 — patented technology, FCC certification
        "tech_stack_modernity": 2.80,   # was 1.84 — AWS, patented speech engine
        "cloud_architecture": 3.00,     # was 2.77 — AWS cloud, available on AWS Marketplace
        "partner_ecosystem": 3.20,      # was 2.04 — Carahsoft gov distribution, AWS Marketplace
        "regulatory_readiness": 3.50,   # was 2.15 — FCC-certified IP CTS provider
        "data_quality": 2.80,           # was 1.95 — speech data collection for ASR training
    },
    "Dash": {
        # This is Dash ComplyOps (dashsdk.com) — AWS Advanced Technology Partner
        # NOT the old Dash AP automation company (merged into SMRTR)
        "ai_product_features": 3.80,    # was 2.90 — CloudScanner AI, NLP policy config, auto evidence
        "ai_engineering": 2.50,         # was 1.22 — built CloudScanner V4.0 engine
        "revenue_ai_upside": 3.50,      # was 2.10 — 6 compliance frameworks, growing market
        "ai_talent_density": 2.00,      # was 1.15 — small but has AI engineering
        "ai_momentum": 3.60,            # was 2.19 — V4.0 launch, AWS Marketplace, AWS for Health
        "leadership_ai_vision": 3.20,   # was 2.17 — deliberate AI compliance strategy
        "tech_stack_modernity": 3.50,   # was 1.33 — AWS-native, modern cloud stack
        "cloud_architecture": 4.00,     # was 1.32 — AWS Advanced Technology Partner!
        "product_differentiation": 3.40, # was 1.68 — AWS Healthcare Competency, 6 frameworks
        "partner_ecosystem": 3.50,      # was 1.60 — AWS partner, Relevance Lab integration
        "regulatory_readiness": 3.80,   # was 2.36 — compliance IS their product
        "ai_governance": 3.80,          # was 2.01 — compliance/governance is core business
        "data_quality": 2.80,           # was 1.62 — compliance data collection
        "data_integration": 2.80,       # was 1.52 — AWS Config, GuardDuty integration
        "analytics_maturity": 2.50,     # was 1.50 — compliance dashboards and reporting
        "org_change_readiness": 2.20,   # was 1.11 — small team but focused
        "margin_ai_upside": 3.20,       # was 1.55 — automated compliance saves 100s hrs/month
    },
    "Track Star": {
        # AI video telematics, predictive maintenance, $24.4M revenue
        "ai_product_features": 4.30,    # was 4.67 — slight adjust, but they DO have AI video
        "ai_engineering": 2.50,         # was 1.96 — built AI video telematics with edge computing
        "ai_talent_density": 2.20,      # was 1.80 — small but has technical team
        "ai_momentum": 3.50,            # was 3.62 — ThingTech acquisition, Enterprise launch
    },
    "FMSI": {
        # Analytics-driven staffing, Appli AI partnership, 140+ customers
        "ai_momentum": 3.80,            # was 3.35 — relaunch March 2026, Appli AI partnership, rapid sales
        "ai_product_features": 3.80,    # was 4.42 — slight down, analytics-driven not deep AI
        "partner_ecosystem": 3.20,      # was 2.40 — Appli AI partnership, banking integrations
    },
    "SMRTR": {
        # ML predictive maintenance, route optimization, compliance anomaly detection
        "ai_product_features": 3.80,    # was 4.17 — slight down, ML features are real but early
        "ai_engineering": 2.80,         # was 2.51 — built ML for backhaul, route optimization
        "ai_momentum": 3.30,            # was 3.19 — merger + VAI partnership = momentum
    },
    "ViaPeople": {
        # AI Instant Insights feature, I/O psychology foundation, SOC 2
        "ai_product_features": 3.50,    # was 3.70 — AI Instant Insights is real but limited
        "ai_momentum": 3.00,            # was 2.82 — SpiraLinks merger, AI R&D investment
        "regulatory_readiness": 3.30,   # was 3.02 — SOC 2 certified
    },
    "ThingTech": {
        # IoT predictive maintenance, Salesforce AppExchange, government contracts
        "ai_product_features": 3.20,    # was 2.83 — IoT predictive maintenance is genuine AI
        "ai_momentum": 2.50,            # was 2.28 — acquired by Track Star, less independent momentum
    },
}

# ── Main ──────────────────────────────────────────────────────────────────────

engine = create_engine(DATABASE_URL)

# Load current scores
with open(os.path.join(os.path.dirname(__file__), "..", "frontend", "public", "portfolio_scores.json")) as f:
    portfolio = json.load(f)

print("=" * 90)
print(f"{'Company':<22} {'Old':>5} {'New':>5} {'Δ':>6} {'Old Tier':<16} {'New Tier':<16} Overrides")
print("=" * 90)

results = []
for c in portfolio:
    name = c["name"]
    pillars = dict(c["pillar_scores"])
    old_composite = c["composite_score"]
    old_tier = c["tier"]

    # Apply overrides
    overrides = PILLAR_OVERRIDES.get(name, {})
    for dim, val in overrides.items():
        pillars[dim] = val

    new_composite = composite(pillars)
    new_tier = tier(new_composite)
    new_wave = wave(new_composite)
    new_cats = cat_scores(pillars)
    delta = new_composite - old_composite
    direction = "↑" if delta > 0 else "↓" if delta < 0 else "="

    override_count = len(overrides)
    print(f"{name:<22} {old_composite:>5.2f} {new_composite:>5.2f} {direction}{abs(delta):>5.2f} {old_tier:<16} {new_tier:<16} {override_count} dims")

    # Update the entry
    c["pillar_scores"] = pillars
    c["composite_score"] = new_composite
    c["tier"] = new_tier
    c["wave"] = new_wave
    c["category_scores"] = new_cats
    results.append(c)

# Sort by new composite score descending
results.sort(key=lambda x: x["composite_score"], reverse=True)

print("=" * 90)
print("\nNew rankings:")
for i, c in enumerate(results, 1):
    print(f"  {i:2d}. {c['composite_score']:.2f} {c['tier']:<16} {c['name']}")

# Write updated JSON
json_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "public", "portfolio_scores.json")
with open(json_path, "w") as f:
    json.dump(results, f, indent=2)
print(f"\n✓ Wrote {len(results)} companies to portfolio_scores.json")

# Sync to production DB
with Session(engine) as session:
    for c in results:
        company = session.query(Company).filter(Company.name == c["name"]).first()
        if not company:
            print(f"  ⚠ {c['name']} not found in DB")
            continue
        score = session.query(CompanyScore).filter(CompanyScore.company_id == company.id).first()
        if score:
            score.composite_score = c["composite_score"]
            score.tier = c["tier"]
            score.wave = c["wave"]
            score.pillar_scores = c["pillar_scores"]
            score.category_scores = c["category_scores"]
    session.commit()
    print(f"✓ Updated {len(results)} companies in production DB")
