#!/usr/bin/env python3
"""
Three data enhancements in one script:
  1. Portfolio velocity: scrape AI momentum for 14 Solen companies
  2. Expanded ground truth: add 30+ well-known companies (total ~58)
  3. Competitive benchmarking: vertical percentile ranks for every company

Run AFTER scrape_training_set.py, scrape_velocity.py, and rescore_training_set.py.
"""

import json
import os
import time
from typing import Dict, List
from collections import defaultdict

from tavily import TavilyClient

TAVILY_KEY = os.getenv("TAVILY_API_KEY", "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")
tavily = TavilyClient(TAVILY_KEY)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DIMENSIONS = [
    "data_quality", "data_integration", "analytics_maturity",
    "cloud_architecture", "tech_stack_modernity", "ai_engineering",
    "ai_product_features", "revenue_ai_upside", "margin_ai_upside", "product_differentiation",
    "ai_talent_density", "leadership_ai_vision", "org_change_readiness", "partner_ecosystem",
    "ai_governance", "regulatory_readiness", "ai_momentum",
]

# ─── Velocity signals (same as scrape_velocity.py) ────────────

AI_JOB_SIGNALS = [
    "machine learning engineer", "ml engineer", "data scientist",
    "ai engineer", "ai researcher", "deep learning", "nlp engineer",
    "computer vision", "mlops", "ai/ml", "llm", "generative ai",
    "prompt engineer", "ai architect", "head of ai", "vp ai",
    "chief ai", "ai team lead", "applied scientist", "research scientist",
    "ai product manager", "ml platform", "ai infrastructure",
    "model training", "reinforcement learning", "ai ops",
]

RECENT_AI_SIGNALS = [
    "ai launch", "ai-powered", "launches ai", "introduces ai",
    "ai feature", "ai product", "generative ai", "copilot",
    "ai partnership", "ai integration", "ai acquisition",
    "machine learning", "ai strategy", "ai investment",
    "ai roadmap", "artificial intelligence", "gpt", "llm",
    "ai assistant", "ai automation", "ai analytics",
    "predictive", "recommendation engine", "intelligent",
    "ai update", "ai release", "neural", "foundation model",
    "ai-first", "ai transformation", "ai initiative",
]

STAGNATION_SIGNALS = [
    "shutting down", "laying off", "pivot away", "end of life",
    "deprecated", "sunset", "no longer", "acquired by",
    "merged with", "bankruptcy", "struggling",
]


def tavily_search(query, max_results=5):
    try:
        resp = tavily.search(query=query, max_results=max_results, include_answer=True, search_depth="basic")
        parts = []
        for r in resp.get("results", []):
            parts.append(r.get("content", ""))
            parts.append(r.get("title", ""))
        if resp.get("answer"):
            parts.append(resp["answer"])
        time.sleep(0.3)
        return " ".join(parts)
    except:
        time.sleep(1.0)
        return ""


def count_signals(text, keywords):
    text_lower = text.lower()
    return sum(1 for kw in keywords if kw in text_lower)


def compute_momentum(job_sigs, news_sigs, stag_sigs, co):
    if job_sigs == 0:
        job_score = 1.0
    elif job_sigs <= 2:
        job_score = 1.5 + job_sigs * 0.5
    elif job_sigs <= 5:
        job_score = 2.5 + (job_sigs - 2) * 0.4
    elif job_sigs <= 10:
        job_score = 3.7 + (job_sigs - 5) * 0.2
    else:
        job_score = 4.7 + min((job_sigs - 10) * 0.05, 0.3)

    if news_sigs == 0:
        news_score = 1.0
    elif news_sigs <= 3:
        news_score = 1.5 + news_sigs * 0.4
    elif news_sigs <= 7:
        news_score = 2.7 + (news_sigs - 3) * 0.3
    elif news_sigs <= 12:
        news_score = 3.9 + (news_sigs - 7) * 0.15
    else:
        news_score = 4.65 + min((news_sigs - 12) * 0.05, 0.35)

    raw = job_score * 0.4 + news_score * 0.6
    raw -= stag_sigs * 0.4

    if co.get("has_ai_features"):
        raw += 0.3
    emp = co.get("employee_count", 50)
    if emp > 1000:
        raw += 0.2
    founded = co.get("founded_year", 2005)
    if founded >= 2018:
        raw += 0.2
    elif founded < 1995:
        raw -= 0.15

    return round(max(1.0, min(5.0, raw)), 1)


# ─── Portfolio companies (must match retrain_model_v2 / generate_demo_data) ──

PORTFOLIO = [
    {"name": "Cairn Applications", "vertical": "Waste Hauling SaaS", "employee_count": 45},
    {"name": "SMRTR", "vertical": "F&B Supply Chain Compliance", "employee_count": 120},
    {"name": "ViaPeople", "vertical": "HR Performance Management", "employee_count": 65},
    {"name": "Track Star", "vertical": "Fleet Telematics SaaS", "employee_count": 200},
    {"name": "FMSI", "vertical": "Credit Union Staffing Analytics", "employee_count": 85},
    {"name": "Champ", "vertical": "Public Health EHR", "employee_count": 150},
    {"name": "TrackIt Transit", "vertical": "Public Transit Software", "employee_count": 30},
    {"name": "NexTalk", "vertical": "Accessibility Communications", "employee_count": 40},
    {"name": "Thought Foundry", "vertical": "Entertainment PaaS", "employee_count": 55},
    {"name": "Spokane", "vertical": "Produce ERP", "employee_count": 70},
    {"name": "Primate", "vertical": "Energy Control Room", "employee_count": 90},
    {"name": "ThingTech", "vertical": "IoT Asset Tracking", "employee_count": 110},
    {"name": "Dash", "vertical": "AP & Doc Automation", "employee_count": 60},
    {"name": "AutoTime", "vertical": "A&D Payroll", "employee_count": 75},
]


# ═══════════════════════════════════════════════════════════════
# PART 1: Portfolio Velocity
# ═══════════════════════════════════════════════════════════════

def scrape_portfolio_velocity():
    print("=" * 70)
    print("PART 1: Scraping velocity signals for 14 Solen portfolio companies")
    print("=" * 70)

    results = {}
    for i, co in enumerate(PORTFOLIO):
        name = co["name"]
        vertical = co["vertical"]
        anchor = f'"{name}"'

        job_text = tavily_search(f'{anchor} {vertical} AI machine learning engineer jobs hiring 2025 2026')
        news_text = tavily_search(f'{anchor} AI launch announcement partnership product update 2025 2026')

        combined = f"{job_text} {news_text}"
        job_sigs = count_signals(job_text, AI_JOB_SIGNALS)
        news_sigs = count_signals(news_text, RECENT_AI_SIGNALS)
        stag_sigs = count_signals(combined, STAGNATION_SIGNALS)

        momentum = compute_momentum(job_sigs, news_sigs, stag_sigs, co)
        results[name] = {
            "ai_momentum": momentum,
            "ai_hiring_signals": job_sigs,
            "recent_ai_signals": news_sigs,
            "stagnation_signals": stag_sigs,
        }

        bar = "█" * int(momentum * 2) + "░" * (10 - int(momentum * 2))
        print(f"  [{i+1:2d}/14] mom={momentum:.1f} {bar} {name:25s} (jobs={job_sigs:2d} news={news_sigs:2d})")

    # Save
    out_path = os.path.join(BASE_DIR, "data", "research", "portfolio_velocity.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n  ✅ Saved to {out_path}")
    return results


# ═══════════════════════════════════════════════════════════════
# PART 2: Expanded Ground Truth (28 → ~58 companies)
# ═══════════════════════════════════════════════════════════════

def expand_ground_truth():
    print(f"\n{'=' * 70}")
    print("PART 2: Expanding ground truth from 28 to ~58 companies")
    print("=" * 70)

    gt_path = os.path.join(BASE_DIR, "data", "training", "ground_truth_v2.json")
    with open(gt_path) as f:
        existing = json.load(f)

    existing_names = {g["name"] for g in existing}
    print(f"  Existing: {len(existing)} companies")

    # New ground truth companies with well-known tier assignments
    new_gt = [
        # AI-Ready (obvious leaders)
        {"name": "Datadog", "vertical": "DevOps/Observability", "actual_tier": "AI-Ready", "actual_score": 4.3,
         "rationale": "AI-powered observability, Watchdog AI, massive telemetry data, 5000+ employees, public"},
        {"name": "Elastic", "vertical": "Search/Analytics", "actual_tier": "AI-Ready", "actual_score": 4.1,
         "rationale": "Elasticsearch AI, ESRE, vector search, ML-native platform, public"},
        {"name": "MongoDB", "vertical": "Database/AI", "actual_tier": "AI-Ready", "actual_score": 4.2,
         "rationale": "Atlas Vector Search, AI app framework, massive developer ecosystem, public"},
        {"name": "Twilio", "vertical": "Communications", "actual_tier": "AI-Ready", "actual_score": 4.0,
         "rationale": "CustomerAI, massive communications data, AI-powered personalization, 6000+ employees"},
        {"name": "Figma", "vertical": "Design", "actual_tier": "AI-Ready", "actual_score": 4.0,
         "rationale": "AI-powered design features, massive design data, acquired by Adobe then independent, strong engineering"},
        {"name": "Stripe", "vertical": "Payments/FinTech", "actual_tier": "AI-Ready", "actual_score": 4.3,
         "rationale": "Radar AI fraud detection, massive payment data, 8000+ employees, AI-native infrastructure"},
        {"name": "Notion", "vertical": "Productivity", "actual_tier": "AI-Ready", "actual_score": 4.0,
         "rationale": "Notion AI assistant, strong data platform, cloud-native, strong engineering culture"},

        # AI-Buildable (strong companies with AI potential)
        {"name": "Canva", "vertical": "Design", "actual_tier": "AI-Buildable", "actual_score": 3.8,
         "rationale": "Magic Design AI, image generation, strong data, 4000+ employees but AI still developing"},
        {"name": "Airtable", "vertical": "Low-Code/Database", "actual_tier": "AI-Buildable", "actual_score": 3.4,
         "rationale": "AI blocks, strong data platform, cloud-native, but limited ML engineering depth"},
        {"name": "Brex", "vertical": "FinTech/Corporate Cards", "actual_tier": "AI-Buildable", "actual_score": 3.5,
         "rationale": "AI-powered spend management, Empower AI, strong data, cloud-native"},
        {"name": "nCino", "vertical": "Banking Software", "actual_tier": "AI-Buildable", "actual_score": 3.3,
         "rationale": "Bank operating system, nCino Mortgage Suite, cloud-native on Salesforce, public"},
        {"name": "Duck Creek", "vertical": "Insurance", "actual_tier": "AI-Buildable", "actual_score": 3.4,
         "rationale": "Insurance SaaS platform, SaaS migration, AI claims processing, good data"},
        {"name": "Flatiron Health", "vertical": "Oncology/Health Data", "actual_tier": "AI-Buildable", "actual_score": 3.8,
         "rationale": "Oncology data platform, real-world evidence, Roche-backed, strong data science team"},
        {"name": "EvenUp", "vertical": "Legal Tech/AI", "actual_tier": "AI-Buildable", "actual_score": 3.6,
         "rationale": "AI demand letters for personal injury, NLP-heavy, growing fast, AI-native product"},
        {"name": "Ironclad", "vertical": "Contract Management", "actual_tier": "AI-Buildable", "actual_score": 3.5,
         "rationale": "AI-powered CLM, AI Assist, strong data from contracts, cloud-native"},
        {"name": "Suki AI", "vertical": "Healthcare/Voice AI", "actual_tier": "AI-Buildable", "actual_score": 3.7,
         "rationale": "AI medical scribe, voice AI for clinicians, AI-native product, strong clinical data"},

        # AI-Emerging (some capabilities but gaps)
        {"name": "Blackbaud", "vertical": "Nonprofit Software", "actual_tier": "AI-Emerging", "actual_score": 2.8,
         "rationale": "Nonprofit CRM/Finance, some AI features, large but legacy platform, slow cloud migration"},
        {"name": "Ellucian", "vertical": "Higher Ed ERP", "actual_tier": "AI-Emerging", "actual_score": 2.7,
         "rationale": "Higher ed admin software, legacy on-prem, some cloud, limited AI, large install base"},
        {"name": "Deltek", "vertical": "Project-Based ERP", "actual_tier": "AI-Emerging", "actual_score": 2.8,
         "rationale": "Project ERP for GovCon, decent data, some cloud migration, limited AI"},
        {"name": "PowerSchool", "vertical": "K-12 Education", "actual_tier": "AI-Emerging", "actual_score": 2.6,
         "rationale": "K-12 SIS/LMS, massive student data, public, but limited AI and slow modernization"},
        {"name": "RealPage", "vertical": "Property Management", "actual_tier": "AI-Emerging", "actual_score": 2.9,
         "rationale": "Revenue management AI, property data, but antitrust issues, mixed cloud migration"},
        {"name": "Elation Health", "vertical": "Primary Care EHR", "actual_tier": "AI-Emerging", "actual_score": 2.7,
         "rationale": "Modern EHR, cloud-native, decent data, but limited AI features, small team"},
        {"name": "Jobber", "vertical": "Field Service", "actual_tier": "AI-Emerging", "actual_score": 2.7,
         "rationale": "Field service mgmt for SMBs, cloud-native, growing, limited AI but modern stack"},
        {"name": "Buildertrend", "vertical": "Construction", "actual_tier": "AI-Emerging", "actual_score": 2.6,
         "rationale": "Residential construction management, cloud-native, limited AI, decent market position"},

        # AI-Limited (minimal AI / legacy)
        {"name": "Open Dental", "vertical": "Dental Practice Mgmt", "actual_tier": "AI-Limited", "actual_score": 2.0,
         "rationale": "Open-source dental PM, desktop-focused, minimal cloud, no AI, small team"},
        {"name": "SiteLink", "vertical": "Self-Storage Mgmt", "actual_tier": "AI-Limited", "actual_score": 2.1,
         "rationale": "Self-storage management, legacy on-prem, limited cloud, no AI, niche market"},
        {"name": "DRB Systems", "vertical": "Car Wash Tech", "actual_tier": "AI-Limited", "actual_score": 2.0,
         "rationale": "Car wash point-of-sale and tunnel controls, hardware-focused, minimal software AI"},
        {"name": "Compeat", "vertical": "Restaurant Back Office", "actual_tier": "AI-Limited", "actual_score": 1.9,
         "rationale": "Restaurant accounting/back-office, legacy, limited cloud, no AI, acquired by Restaurant365"},
        {"name": "FrontRunner Pro", "vertical": "Funeral Home", "actual_tier": "AI-Limited", "actual_score": 1.7,
         "rationale": "Funeral home websites/marketing, minimal tech, no cloud, no AI"},
        {"name": "Shelby Systems", "vertical": "Church Management", "actual_tier": "AI-Limited", "actual_score": 1.5,
         "rationale": "Church management software, legacy desktop, minimal cloud, no AI whatsoever"},
    ]

    added = 0
    for gt in new_gt:
        if gt["name"] not in existing_names:
            existing.append(gt)
            existing_names.add(gt["name"])
            added += 1

    # Save
    with open(gt_path, "w") as f:
        json.dump(existing, f, indent=2)

    # Stats
    tiers = defaultdict(int)
    for g in existing:
        tiers[g["actual_tier"]] += 1
    print(f"  Added: {added} new companies")
    print(f"  Total: {len(existing)} ground truth companies")
    print(f"  Distribution: {dict(tiers)}")
    print(f"  ✅ Saved to {gt_path}")
    return existing


# ═══════════════════════════════════════════════════════════════
# PART 3: Competitive Benchmarking (vertical percentile ranks)
# ═══════════════════════════════════════════════════════════════

def build_competitive_benchmarks():
    print(f"\n{'=' * 70}")
    print("PART 3: Building competitive benchmarks by vertical")
    print("=" * 70)

    # Load training set
    train_path = os.path.join(BASE_DIR, "data", "training", "training_set_v2_real.json")
    with open(train_path) as f:
        training = json.load(f)

    # Group by vertical
    by_vertical = defaultdict(list)
    for co in training:
        by_vertical[co["vertical"]].append(co)

    print(f"  {len(training)} companies across {len(by_vertical)} verticals")

    # Compute percentile rank for each company within its vertical
    benchmarks = {}
    for vertical, companies in by_vertical.items():
        scores = sorted([c["composite_score"] for c in companies])
        n = len(scores)
        for co in companies:
            rank = sorted(scores).index(co["composite_score"]) + 1
            percentile = round(rank / n * 100, 1)
            benchmarks[co["name"]] = {
                "vertical": vertical,
                "rank": rank,
                "of": n,
                "percentile": percentile,
                "vertical_avg": round(sum(scores) / n, 2),
                "vertical_max": max(scores),
                "vertical_min": min(scores),
                "score": co["composite_score"],
                "tier": co["tier"],
                "momentum": co["pillars"].get("ai_momentum", 0),
            }

    # Also compute portfolio company benchmarks against their CLOSEST verticals
    # Since portfolio companies aren't in the training set, we map them to similar verticals
    portfolio_vertical_map = {
        "Cairn Applications": "Waste Hauling SaaS",
        "SMRTR": "Supply Chain/Logistics",
        "ViaPeople": "HR/Workforce Management",
        "Track Star": "Fleet/IoT",
        "FMSI": "FinTech/Core Banking",
        "Champ": "Healthcare IT",
        "TrackIt Transit": "Fleet/IoT",
        "NexTalk": "Communications/Telecom",
        "Thought Foundry": "Entertainment/Media",
        "Spokane": "Agriculture/Food Tech",
        "Primate": "Energy/Utilities",
        "ThingTech": "Fleet/IoT",
        "Dash": "AP Automation",
        "AutoTime": "HR/Workforce Management",
    }

    # Load portfolio scores
    portfolio_path = os.path.join(BASE_DIR, "data", "demo", "portfolio_scores.json")
    with open(portfolio_path) as f:
        portfolio = json.load(f)

    portfolio_benchmarks = []
    for co in portfolio:
        mapped_vertical = portfolio_vertical_map.get(co["name"], "")

        # Find best-matching vertical in training data
        best_match = None
        best_count = 0
        for vert, companies in by_vertical.items():
            # Simple keyword matching
            keywords = set(mapped_vertical.lower().replace("/", " ").split())
            vert_keywords = set(vert.lower().replace("/", " ").split())
            overlap = len(keywords & vert_keywords)
            if overlap > best_count:
                best_count = overlap
                best_match = vert

        if not best_match:
            # Fallback: use the vertical with the closest average score
            best_match = min(by_vertical.keys(),
                           key=lambda v: abs(sum(c["composite_score"] for c in by_vertical[v]) / len(by_vertical[v]) - co["composite_score"]))

        peers = by_vertical[best_match]
        peer_scores = sorted([c["composite_score"] for c in peers])
        n = len(peer_scores)

        # Where does this portfolio company rank?
        rank = sum(1 for s in peer_scores if s <= co["composite_score"]) + 1
        percentile = round(rank / (n + 1) * 100, 1)

        # Find nearest peers
        peers_sorted = sorted(peers, key=lambda c: abs(c["composite_score"] - co["composite_score"]))
        nearest = [{"name": p["name"], "score": p["composite_score"], "tier": p["tier"]} for p in peers_sorted[:5]]

        portfolio_benchmarks.append({
            "name": co["name"],
            "score": co["composite_score"],
            "tier": co["tier"],
            "wave": co["wave"],
            "peer_vertical": best_match,
            "peer_count": n,
            "vertical_rank": rank,
            "vertical_percentile": percentile,
            "vertical_avg": round(sum(peer_scores) / n, 2),
            "vertical_max": max(peer_scores),
            "vertical_min": min(peer_scores),
            "nearest_peers": nearest,
        })

        rank_bar = "█" * int(percentile / 10) + "░" * (10 - int(percentile / 10))
        print(f"  {co['name']:25s} {co['composite_score']:.2f}  P{percentile:5.1f} {rank_bar} rank {rank:2d}/{n:2d}  vs {best_match}")

    # Save
    bench_path = os.path.join(BASE_DIR, "data", "demo", "competitive_benchmarks.json")
    with open(bench_path, "w") as f:
        json.dump({
            "portfolio_benchmarks": portfolio_benchmarks,
            "training_set_benchmarks": benchmarks,
        }, f, indent=2)

    # Also copy to frontend
    frontend_path = os.path.join(BASE_DIR, "frontend", "public", "competitive_benchmarks.json")
    with open(frontend_path, "w") as f:
        json.dump({
            "portfolio_benchmarks": portfolio_benchmarks,
            "training_set_benchmarks": benchmarks,
        }, f, indent=2)

    print(f"\n  ✅ Saved to {bench_path}")
    print(f"  ✅ Copied to {frontend_path}")
    return portfolio_benchmarks


# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Part 1: Portfolio velocity
    velocity = scrape_portfolio_velocity()

    # Part 2: Expanded ground truth
    ground_truth = expand_ground_truth()

    # Part 3: Competitive benchmarks
    benchmarks = build_competitive_benchmarks()

    print(f"\n{'=' * 70}")
    print("ALL THREE ENHANCEMENTS COMPLETE")
    print("=" * 70)
    print(f"  1. Portfolio velocity: {len(velocity)} companies with momentum scores")
    print(f"  2. Ground truth: {len(ground_truth)} companies (expanded)")
    print(f"  3. Competitive benchmarks: {len(benchmarks)} portfolio companies benchmarked")
    print(f"\n  Next: run retrain_model_v2.py to incorporate all changes")
