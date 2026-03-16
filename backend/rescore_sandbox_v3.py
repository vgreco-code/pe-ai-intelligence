"""Re-score all sandbox (non-portfolio) companies with the v3 scoring model.

No API calls — uses stored features. Updates CompanyScore + Benchmark only.
"""
import os, sys, logging
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.company import Company, CompanyScore, Benchmark
from routers.sandbox import (
    estimate_dimension_scores, compute_composite,
    classify_tier, assign_wave, compute_category_scores,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger(__name__)


def main():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL required"); sys.exit(1)

    dry_run = "--dry-run" in sys.argv
    engine = create_engine(database_url, pool_pre_ping=True)
    db = sessionmaker(bind=engine)()

    companies = (
        db.query(Company, CompanyScore)
        .join(CompanyScore, Company.id == CompanyScore.company_id)
        .filter(Company.is_portfolio == False)
        .all()
    )

    logger.info(f"Re-scoring {len(companies)} sandbox companies {'(DRY RUN)' if dry_run else ''}")

    tier_counts_old = {}
    tier_counts_new = {}
    changes = {"up": 0, "down": 0, "same": 0}

    for i, (co, sc) in enumerate(companies):
        features = {
            "employee_count": co.employee_count,
            "funding_total_usd": co.funding_total_usd or 0,
            "is_public": co.is_public or False,
            "has_ai_features": co.has_ai_features or False,
            "cloud_native": co.cloud_native or False,
            "api_ecosystem_strength": co.api_ecosystem_strength,
            "data_richness": co.data_richness,
            "regulatory_burden": co.regulatory_burden,
            "market_position": co.market_position,
        }

        pillars = estimate_dimension_scores(features)
        composite = compute_composite(pillars)
        tier = classify_tier(composite)
        wave = assign_wave(composite)
        cats = compute_category_scores(pillars)

        tier_counts_old[sc.tier] = tier_counts_old.get(sc.tier, 0) + 1
        tier_counts_new[tier] = tier_counts_new.get(tier, 0) + 1

        t_order = ["AI-Limited", "AI-Emerging", "AI-Buildable", "AI-Ready"]
        oi = t_order.index(sc.tier) if sc.tier in t_order else 0
        ni = t_order.index(tier) if tier in t_order else 0
        changes["up" if ni > oi else "down" if ni < oi else "same"] += 1

        if not dry_run:
            sc.composite_score = composite
            sc.tier = tier
            sc.wave = wave
            sc.pillar_scores = pillars
            sc.category_scores = cats
            sc.model_version = "3.0"

        if not dry_run and (i + 1) % 100 == 0:
            db.commit()
            logger.info(f"  {i+1}/{len(companies)} committed")

    if not dry_run:
        # Also update benchmarks in bulk
        for co, sc in companies:
            bm = db.query(Benchmark).filter(Benchmark.company_id == co.id).first()
            if bm:
                bm.score = sc.composite_score
                bm.tier = sc.tier
                bm.wave = sc.wave
        db.commit()

    logger.info(f"\nDone. {len(companies)} companies re-scored.")
    logger.info(f"Tier changes: {changes['up']} up, {changes['down']} down, {changes['same']} same")
    logger.info(f"\nOld: {dict(sorted(tier_counts_old.items()))}")
    logger.info(f"New: {dict(sorted(tier_counts_new.items()))}")
    db.close()


if __name__ == "__main__":
    main()
