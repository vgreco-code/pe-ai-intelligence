#!/usr/bin/env python3
"""
Scrape velocity/momentum signals for all 515 training companies.

Adds 2 additional Tavily searches per company:
  1. AI job postings: "{company} AI machine learning engineer jobs hiring 2025 2026"
  2. Recent AI news: "{company} AI launch announcement partnership 2025 2026"

Computes:
  - ai_hiring_signals: count of AI/ML hiring keywords in job search results
  - recent_ai_signals: count of AI activity keywords in recent news results
  - ai_momentum: composite momentum score (1.0-5.0) derived from velocity signals

Checkpoint/resume support: saves every 25 companies.
"""

import json
import os
import sys
import time
from typing import Dict, List
from collections import defaultdict

from tavily import TavilyClient

TAVILY_KEY = os.getenv("TAVILY_API_KEY", "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")
tavily = TavilyClient(TAVILY_KEY)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRAINING_PATH = os.path.join(BASE_DIR, "data", "training", "training_set_v2_real.json")
CHECKPOINT_PATH = os.path.join(BASE_DIR, "data", "training", "_velocity_checkpoint.json")

# ─── Velocity signal keywords ────────────────────────────────

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

# Signals indicating stagnation or legacy approach
STAGNATION_SIGNALS = [
    "shutting down", "laying off", "pivot away", "end of life",
    "deprecated", "sunset", "no longer", "acquired by",
    "merged with", "bankruptcy", "struggling",
]


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
        time.sleep(0.3)
        return " ".join(parts)
    except Exception as e:
        time.sleep(1.0)
        return ""


def count_signals(text: str, keywords: List[str]) -> int:
    """Count how many keywords appear in text."""
    text_lower = text.lower()
    return sum(1 for kw in keywords if kw in text_lower)


def compute_momentum_score(job_signals: int, news_signals: int, stagnation: int, co: dict) -> float:
    """
    Compute AI Momentum score (1.0-5.0) from velocity signals.

    This measures how actively a company is INVESTING in AI right now,
    independent of their current maturity level.
    """
    # Job posting signals (0-25 range typically)
    if job_signals == 0:
        job_score = 1.0
    elif job_signals <= 2:
        job_score = 1.5 + job_signals * 0.5
    elif job_signals <= 5:
        job_score = 2.5 + (job_signals - 2) * 0.4
    elif job_signals <= 10:
        job_score = 3.7 + (job_signals - 5) * 0.2
    else:
        job_score = 4.7 + min((job_signals - 10) * 0.05, 0.3)

    # Recent AI news signals (0-30 range typically)
    if news_signals == 0:
        news_score = 1.0
    elif news_signals <= 3:
        news_score = 1.5 + news_signals * 0.4
    elif news_signals <= 7:
        news_score = 2.7 + (news_signals - 3) * 0.3
    elif news_signals <= 12:
        news_score = 3.9 + (news_signals - 7) * 0.15
    else:
        news_score = 4.65 + min((news_signals - 12) * 0.05, 0.35)

    # Weighted combination: news slightly more important (it's action, not just intent)
    raw = job_score * 0.4 + news_score * 0.6

    # Stagnation penalty
    raw -= stagnation * 0.4

    # Company attribute modifiers for momentum
    if co.get("has_ai_features"):
        raw += 0.3  # Already has AI = more likely to be actively developing more
    if co.get("is_public"):
        raw += 0.15  # Public companies have more visible AI announcements
    if co.get("employee_count", 0) > 1000:
        raw += 0.2  # Larger companies have more AI hiring activity

    # Founded recently = likely more momentum
    founded = co.get("founded_year", 2005)
    if founded >= 2018:
        raw += 0.2
    elif founded < 1995:
        raw -= 0.15

    return round(max(1.0, min(5.0, raw)), 1)


def research_velocity(co: dict, index: int, total: int) -> dict:
    """Scrape velocity signals for one company."""
    name = co["name"]
    vertical = co.get("vertical", "software")
    anchor = f'"{name}"'

    # Search 1: AI job postings
    job_text = tavily_search(
        f'{anchor} {vertical} AI machine learning engineer jobs hiring 2025 2026',
        max_results=5
    )

    # Search 2: Recent AI news/announcements
    news_text = tavily_search(
        f'{anchor} AI launch announcement partnership product update 2025 2026',
        max_results=5
    )

    combined = f"{job_text} {news_text}"

    job_sigs = count_signals(job_text, AI_JOB_SIGNALS)
    news_sigs = count_signals(news_text, RECENT_AI_SIGNALS)
    stag_sigs = count_signals(combined, STAGNATION_SIGNALS)

    momentum = compute_momentum_score(job_sigs, news_sigs, stag_sigs, co)

    # Progress
    bar = "█" * int(momentum * 2) + "░" * (10 - int(momentum * 2))
    total_sigs = job_sigs + news_sigs
    print(f"  [{index+1:3d}/{total}] mom={momentum:.1f} {bar} {name[:35]:35s} (jobs={job_sigs:2d} news={news_sigs:2d} stag={stag_sigs})")

    return {
        "ai_hiring_signals": job_sigs,
        "recent_ai_signals": news_sigs,
        "stagnation_signals": stag_sigs,
        "ai_momentum": momentum,
        "velocity_text_chars": len(combined),
    }


def main():
    with open(TRAINING_PATH) as f:
        companies = json.load(f)

    total = len(companies)

    # Load checkpoint if exists
    completed = {}
    if os.path.exists(CHECKPOINT_PATH):
        with open(CHECKPOINT_PATH) as f:
            checkpoint = json.load(f)
            completed = {c["name"]: c for c in checkpoint.get("completed", [])}
        print(f"\n  ⚡ Resuming from checkpoint: {len(completed)}/{total} already done\n")

    print("=" * 75)
    print(f"SCRAPING VELOCITY SIGNALS FOR {total} COMPANIES")
    print(f"Strategy: 2 Tavily searches per company (AI jobs + recent AI news)")
    print(f"Estimated time: ~{(total - len(completed)) * 1.2 / 60:.0f} minutes")
    print("=" * 75)

    results = list(completed.values())  # Start with checkpointed results

    for i, co in enumerate(companies):
        # Skip already-completed
        if co["name"] in completed:
            continue

        try:
            velocity = research_velocity(co, i, total)
            results.append({"name": co["name"], **velocity})
        except Exception as e:
            print(f"  ✗ Error on {co['name']}: {e}")
            results.append({
                "name": co["name"],
                "ai_hiring_signals": 0,
                "recent_ai_signals": 0,
                "stagnation_signals": 0,
                "ai_momentum": 1.5,
                "velocity_text_chars": 0,
            })

        # Checkpoint every 25
        if (len(results)) % 25 == 0:
            with open(CHECKPOINT_PATH, "w") as f:
                json.dump({"completed": results}, f)
            print(f"  💾 Checkpoint saved ({len(results)}/{total})")

    # Build lookup
    velocity_lookup = {r["name"]: r for r in results}

    # Merge velocity data into training set
    for co in companies:
        v = velocity_lookup.get(co["name"], {})
        co["ai_hiring_signals"] = v.get("ai_hiring_signals", 0)
        co["recent_ai_signals"] = v.get("recent_ai_signals", 0)
        co["stagnation_signals"] = v.get("stagnation_signals", 0)
        co["pillars"]["ai_momentum"] = v.get("ai_momentum", 1.5)

    # Save enriched training set
    with open(TRAINING_PATH, "w") as f:
        json.dump(companies, f, indent=2)

    # Clean up checkpoint
    if os.path.exists(CHECKPOINT_PATH):
        os.remove(CHECKPOINT_PATH)

    # Stats
    momentums = [co["pillars"]["ai_momentum"] for co in companies]
    print(f"\n{'=' * 75}")
    print(f"VELOCITY SCRAPING COMPLETE — {total} companies")
    print(f"{'=' * 75}")
    print(f"  Output: {TRAINING_PATH}")
    print(f"\n  Momentum Stats:")
    print(f"    Mean:   {sum(momentums)/len(momentums):.2f}")
    print(f"    Min:    {min(momentums):.2f}")
    print(f"    Max:    {max(momentums):.2f}")
    print(f"    Median: {sorted(momentums)[len(momentums)//2]:.2f}")

    # Momentum tiers
    high = sum(1 for m in momentums if m >= 4.0)
    med_high = sum(1 for m in momentums if 3.0 <= m < 4.0)
    med = sum(1 for m in momentums if 2.0 <= m < 3.0)
    low = sum(1 for m in momentums if m < 2.0)
    print(f"\n  Momentum Distribution:")
    print(f"    High (≥4.0):      {high:4d} ({high/total*100:.1f}%)")
    print(f"    Med-High (3-4):   {med_high:4d} ({med_high/total*100:.1f}%)")
    print(f"    Medium (2-3):     {med:4d} ({med/total*100:.1f}%)")
    print(f"    Low (<2.0):       {low:4d} ({low/total*100:.1f}%)")

    # Top and bottom
    companies.sort(key=lambda c: -c["pillars"]["ai_momentum"])
    print(f"\n  Top 10 Momentum:")
    for c in companies[:10]:
        print(f"    {c['pillars']['ai_momentum']:.1f}  {c['name']:35s} (jobs={c['ai_hiring_signals']:2d} news={c['recent_ai_signals']:2d})")
    print(f"\n  Bottom 10 Momentum:")
    for c in companies[-10:]:
        print(f"    {c['pillars']['ai_momentum']:.1f}  {c['name']:35s} (jobs={c['ai_hiring_signals']:2d} news={c['recent_ai_signals']:2d})")


if __name__ == "__main__":
    main()
