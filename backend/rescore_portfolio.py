"""Batch re-score portfolio companies using the deep research pipeline.

Runs research_company_deep() for each Solen portfolio company, then updates
their Company, DimensionScore, and CompanyScore records in Postgres.

Usage:
    python rescore_portfolio.py                    # Re-score all portfolio companies
    python rescore_portfolio.py "Cairn Applications"  # Re-score one company
    python rescore_portfolio.py --dry-run          # Preview without writing to DB

Requires env vars:
    DATABASE_URL   — Neon Postgres connection string
    TAVILY_API_KEY — Tavily API key for web research
"""
import asyncio
import json
import os
import sys
import time
import logging
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.company import Base, Company, DimensionScore, CompanyScore, Benchmark
from routers.sandbox import (
    research_company_deep,
    estimate_dimension_scores,
    validate_plausibility,
    compute_composite,
    compute_confidence_score,
    classify_tier,
    assign_wave,
    compute_category_scores,
    build_identity_markers,
    CATEGORIES,
    DERIVED_WEIGHTS,
    DIMENSION_LABELS,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-5s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# Rate limiting: pause between companies to avoid Tavily rate limits
DELAY_BETWEEN_COMPANIES = 3.0  # seconds


def get_db_session(database_url: str):
    engine = create_engine(database_url, pool_pre_ping=True)
    Session = sessionmaker(bind=engine)
    return Session()


async def rescore_company(
    db,
    company: Company,
    tavily_key: str,
    dry_run: bool = False,
) -> dict:
    """Re-score a single portfolio company using deep research.

    Returns a summary dict with old vs new scores.
    """
    company_name = company.name
    logger.info(f"Researching: {company_name}")

    # Get current score for comparison
    old_score_row = db.query(CompanyScore).filter(
        CompanyScore.company_id == company.id
    ).first()
    old_composite = old_score_row.composite_score if old_score_row else None
    old_tier = old_score_row.tier if old_score_row else None
    old_pillars = old_score_row.pillar_scores if old_score_row else {}

    # Build context hint from known company data for better search targeting
    # This helps disambiguate generic names like "AutoTime" or "Dash"
    context_parts = []
    if company.vertical:
        context_parts.append(company.vertical)
    if company.description:
        # Take first ~60 chars of description as extra context
        context_parts.append(company.description[:60].strip())
    context_hint = " ".join(context_parts) if context_parts else ""

    # Build identity markers for entity-match validation
    # This filters out search results for wrong companies with similar names
    identity_markers = build_identity_markers(
        company_name=company_name,
        website=company.website,
        vertical=company.vertical,
        description=company.description,
    )
    logger.info(
        f"  Identity markers: domain={identity_markers.get('domain', 'N/A')}, "
        f"vertical_kw={identity_markers.get('vertical_keywords', [])[:3]}, "
        f"desc_kw={identity_markers.get('desc_keywords', [])[:3]}"
    )

    # Run deep research with context hint + entity validation
    features = await research_company_deep(
        company_name, tavily_key,
        context_hint=context_hint,
        identity_markers=identity_markers,
    )
    research_meta = features.pop("_research_meta", {})
    research_summary = features.pop("research_summary", "")

    validated = research_meta.get("validated_results", research_meta.get("search_results", 0))
    dropped = research_meta.get("results_dropped", 0)
    logger.info(
        f"  Research complete: {research_meta.get('search_results', 0)} results "
        f"({validated} validated, {dropped} dropped), "
        f"{research_meta.get('urls_scraped', 0)} URLs scraped, "
        f"{research_meta.get('total_text_chars', 0)} chars"
    )

    # Plausibility check + compute new scores
    features = validate_plausibility(features, is_pe_portfolio=True)
    pillar_scores = estimate_dimension_scores(features)
    composite = compute_composite(pillar_scores)
    tier = classify_tier(composite)
    wave = assign_wave(composite)
    cat_scores = compute_category_scores(pillar_scores)
    confidence = compute_confidence_score(features, research_meta)

    delta = composite - old_composite if old_composite else 0
    direction = "+" if delta > 0 else ""
    logger.info(
        f"  Score: {old_composite} -> {composite} ({direction}{delta:.2f}) | "
        f"Tier: {old_tier} -> {tier} | Confidence: {confidence['total']}%"
    )

    summary = {
        "name": company_name,
        "old_composite": old_composite,
        "new_composite": composite,
        "delta": round(delta, 2),
        "old_tier": old_tier,
        "new_tier": tier,
        "wave": wave,
        "confidence": confidence["total"],
        "confidence_breakdown": confidence["breakdown"],
        "research_results": research_meta.get("search_results", 0),
        "validated_results": research_meta.get("validated_results", research_meta.get("search_results", 0)),
        "results_dropped": research_meta.get("results_dropped", 0),
        "urls_scraped": research_meta.get("urls_scraped", 0),
        "features": features,
        "pillar_scores": pillar_scores,
    }

    if dry_run:
        logger.info("  [DRY RUN] Skipping database update")
        return summary

    # Update Company record with enriched features
    company.vertical = features.get("vertical") or company.vertical
    company.website = features.get("website") or company.website
    company.description = research_summary[:500] if research_summary else company.description
    company.founded_year = features.get("founded_year") or company.founded_year
    company.employee_count = features.get("employee_count") or company.employee_count
    company.funding_total_usd = features.get("funding_total_usd") or company.funding_total_usd
    company.is_public = features.get("is_public", company.is_public)
    company.has_ai_features = features.get("has_ai_features", company.has_ai_features)
    company.cloud_native = features.get("cloud_native", company.cloud_native)
    company.api_ecosystem_strength = features.get("api_ecosystem_strength", company.api_ecosystem_strength)
    company.data_richness = features.get("data_richness", company.data_richness)
    company.regulatory_burden = features.get("regulatory_burden", company.regulatory_burden)
    company.market_position = features.get("market_position", company.market_position)
    company.updated_at = datetime.utcnow()

    # Update or create DimensionScore records
    existing_dims = db.query(DimensionScore).filter(
        DimensionScore.company_id == company.id
    ).all()
    dim_map = {d.dimension: d for d in existing_dims}

    for dim, score in pillar_scores.items():
        if dim in dim_map:
            dim_map[dim].score = score
            dim_map[dim].model_version = "2.0-deep"
        else:
            ds = DimensionScore(
                company_id=company.id,
                dimension=dim,
                score=score,
                model_version="2.0-deep",
            )
            db.add(ds)

    # Update or create CompanyScore record
    if old_score_row:
        old_score_row.composite_score = composite
        old_score_row.tier = tier
        old_score_row.wave = wave
        old_score_row.pillar_scores = pillar_scores
        old_score_row.category_scores = cat_scores
        old_score_row.confidence_score = confidence["total"]
        old_score_row.confidence_breakdown = confidence["breakdown"]
        old_score_row.model_version = "2.0-deep"
    else:
        cs = CompanyScore(
            company_id=company.id,
            composite_score=composite,
            tier=tier,
            wave=wave,
            pillar_scores=pillar_scores,
            category_scores=cat_scores,
            confidence_score=confidence["total"],
            confidence_breakdown=confidence["breakdown"],
            model_version="2.0-deep",
        )
        db.add(cs)

    # Update Benchmark record if it exists
    benchmark = db.query(Benchmark).filter(
        Benchmark.company_id == company.id
    ).first()
    if benchmark:
        benchmark.score = composite
        benchmark.tier = tier
        benchmark.wave = wave

    db.commit()
    logger.info(f"  Database updated successfully")
    return summary


async def rescore_all(
    database_url: str,
    tavily_key: str,
    target_company: str = None,
    dry_run: bool = False,
):
    """Re-score all (or one specific) portfolio companies."""
    db = get_db_session(database_url)

    try:
        # Query portfolio companies
        query = db.query(Company).filter(Company.is_portfolio == True)
        if target_company:
            query = query.filter(Company.name == target_company)

        companies = query.order_by(Company.name).all()

        if not companies:
            if target_company:
                logger.error(f"Company '{target_company}' not found in portfolio")
            else:
                logger.error("No portfolio companies found in database")
            return

        logger.info(f"{'=' * 60}")
        logger.info(f"PORTFOLIO RE-SCORING {'(DRY RUN)' if dry_run else ''}")
        logger.info(f"Companies to process: {len(companies)}")
        logger.info(f"Estimated Tavily calls: {len(companies) * 8}")
        logger.info(f"{'=' * 60}")

        results = []
        for i, company in enumerate(companies, 1):
            logger.info(f"\n[{i}/{len(companies)}] Processing {company.name}")
            logger.info(f"-" * 40)

            try:
                summary = await rescore_company(db, company, tavily_key, dry_run)
                results.append(summary)
            except Exception as e:
                logger.error(f"  FAILED: {e}")
                results.append({
                    "name": company.name,
                    "error": str(e),
                })

            # Rate limit between companies
            if i < len(companies):
                logger.info(f"  Waiting {DELAY_BETWEEN_COMPANIES}s before next company...")
                await asyncio.sleep(DELAY_BETWEEN_COMPANIES)

        # Print summary report
        print_report(results, dry_run)

        # Save results to JSON for reference
        output_path = os.path.join(os.path.dirname(__file__), "rescore_results.json")
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2, default=str)
        logger.info(f"\nDetailed results saved to: {output_path}")

    finally:
        db.close()


def print_report(results: list[dict], dry_run: bool):
    """Print a summary report of all re-scored companies."""
    logger.info(f"\n{'=' * 60}")
    logger.info(f"RE-SCORING REPORT {'(DRY RUN)' if dry_run else ''}")
    logger.info(f"{'=' * 60}")

    successes = [r for r in results if "error" not in r]
    failures = [r for r in results if "error" in r]

    if successes:
        logger.info(f"\n{'Company':<30s} {'Old':>6s} {'New':>6s} {'Delta':>7s} {'Conf':>5s} {'Drop':>5s} {'Old Tier':<15s} {'New Tier':<15s}")
        logger.info(f"{'-'*30} {'-'*6} {'-'*6} {'-'*7} {'-'*5} {'-'*5} {'-'*15} {'-'*15}")

        for r in sorted(successes, key=lambda x: x.get("new_composite", 0), reverse=True):
            delta_str = f"{'+' if r['delta'] > 0 else ''}{r['delta']:.2f}"
            conf_str = f"{r.get('confidence', 0):.0f}%"
            drop_str = f"{r.get('results_dropped', 0)}"
            logger.info(
                f"{r['name']:<30s} {r.get('old_composite', 0):>6.2f} {r['new_composite']:>6.2f} "
                f"{delta_str:>7s} {conf_str:>5s} {drop_str:>5s} {r.get('old_tier', 'N/A'):<15s} {r['new_tier']:<15s}"
            )

        # Tier distribution
        tier_counts = {}
        for r in successes:
            t = r["new_tier"]
            tier_counts[t] = tier_counts.get(t, 0) + 1

        logger.info(f"\nNew Tier Distribution:")
        for tier in ["AI-Ready", "AI-Buildable", "AI-Emerging", "AI-Limited"]:
            count = tier_counts.get(tier, 0)
            logger.info(f"  {tier:<15s}: {count}")

        avg_delta = sum(r["delta"] for r in successes) / len(successes)
        avg_new = sum(r["new_composite"] for r in successes) / len(successes)
        logger.info(f"\nAverage composite score: {avg_new:.2f}")
        logger.info(f"Average score change: {'+' if avg_delta > 0 else ''}{avg_delta:.2f}")

    if failures:
        logger.info(f"\nFailed ({len(failures)}):")
        for r in failures:
            logger.info(f"  {r['name']}: {r['error']}")

    logger.info(f"\nTotal: {len(successes)} succeeded, {len(failures)} failed")


def main():
    # Get config from env vars
    database_url = os.environ.get("DATABASE_URL")
    tavily_key = os.environ.get("TAVILY_API_KEY")

    if not database_url:
        logger.error("DATABASE_URL env var is required")
        sys.exit(1)
    if not tavily_key:
        logger.error("TAVILY_API_KEY env var is required")
        sys.exit(1)

    # Parse CLI args
    dry_run = "--dry-run" in sys.argv
    target_company = None

    for arg in sys.argv[1:]:
        if arg == "--dry-run":
            continue
        target_company = arg

    asyncio.run(rescore_all(database_url, tavily_key, target_company, dry_run))


if __name__ == "__main__":
    main()
