"""Migrate JSON data files into Postgres database"""
import json
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.company import Base, Company, DimensionScore, CompanyScore, Benchmark, ModelMetrics, TrainingSignal

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend", "public")


def load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


def migrate(database_url: str):
    engine = create_engine(database_url, pool_pre_ping=True)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        # Check if already migrated
        if db.query(Company).count() > 0:
            print("Database already has data. Skipping migration.")
            print(f"  Companies: {db.query(Company).count()}")
            print(f"  Scores: {db.query(CompanyScore).count()}")
            print(f"  Benchmarks: {db.query(Benchmark).count()}")
            return

        # 1. Load portfolio companies
        print("Loading portfolio companies...")
        portfolio = load_json("portfolio_scores.json")
        portfolio_ids = {}
        for p in portfolio:
            company = Company(
                name=p["name"],
                vertical=p.get("vertical"),
                website=p.get("website"),
                description=p.get("description"),
                founded_year=p.get("founded_year"),
                employee_count=p.get("employee_count"),
                is_portfolio=True,
            )
            db.add(company)
            db.flush()
            portfolio_ids[p["name"]] = company.id

            # Company score
            score = CompanyScore(
                company_id=company.id,
                composite_score=p["composite_score"],
                tier=p["tier"],
                wave=p.get("wave"),
                pillar_scores=p.get("pillar_scores"),
                category_scores=p.get("category_scores"),
            )
            db.add(score)

            # Individual dimension scores
            for dim, val in (p.get("pillar_scores") or {}).items():
                ds = DimensionScore(
                    company_id=company.id,
                    dimension=dim,
                    score=val,
                )
                db.add(ds)

        print(f"  Loaded {len(portfolio)} portfolio companies")

        # 2. Load training set
        print("Loading training set...")
        training = load_json("large_training_set.json")
        training_ids = {}
        for t in training:
            # Skip if already added as portfolio company
            if t["name"] in portfolio_ids:
                training_ids[t["name"]] = portfolio_ids[t["name"]]
                continue

            company = Company(
                name=t["name"],
                vertical=t.get("vertical"),
                founded_year=t.get("founded_year"),
                employee_count=t.get("employee_count"),
                funding_total_usd=t.get("funding_total_usd"),
                is_public=t.get("is_public", False),
                has_ai_features=t.get("has_ai_features", False),
                cloud_native=t.get("cloud_native", False),
                api_ecosystem_strength=t.get("api_ecosystem_strength"),
                data_richness=t.get("data_richness"),
                regulatory_burden=t.get("regulatory_burden"),
                market_position=t.get("market_position"),
                is_portfolio=False,
            )
            db.add(company)
            db.flush()
            training_ids[t["name"]] = company.id

            # Company score
            score = CompanyScore(
                company_id=company.id,
                composite_score=t.get("composite_score", 0),
                tier=t.get("tier", "AI-Limited"),
                pillar_scores=t.get("pillars"),
            )
            db.add(score)

            # Dimension scores
            for dim, val in (t.get("pillars") or {}).items():
                ds = DimensionScore(
                    company_id=company.id,
                    dimension=dim,
                    score=val,
                )
                db.add(ds)

            # Training signals
            signal = TrainingSignal(
                company_id=company.id,
                text_chars=t.get("text_chars"),
                signal_count=t.get("signal_count"),
                ai_hiring_signals=t.get("ai_hiring_signals"),
                recent_ai_signals=t.get("recent_ai_signals"),
                stagnation_signals=t.get("stagnation_signals"),
            )
            db.add(signal)

        print(f"  Loaded {len(training)} training companies")

        # 3. Load benchmarks
        print("Loading competitive benchmarks...")
        benchmarks_data = load_json("competitive_benchmarks.json")
        benchmarks_list = benchmarks_data.get("portfolio_benchmarks", [])
        for b in benchmarks_list:
            # Find company id - check portfolio first, then training
            company_name = b["name"]
            company_id = portfolio_ids.get(company_name) or training_ids.get(company_name)
            if not company_id:
                # Create a stub company for benchmark-only entries
                stub = Company(name=company_name, is_portfolio=False)
                db.add(stub)
                db.flush()
                company_id = stub.id

            benchmark = Benchmark(
                company_id=company_id,
                score=b.get("score", 0),
                tier=b.get("tier", ""),
                wave=b.get("wave"),
                peer_verticals=b.get("peer_verticals"),
                peer_count=b.get("peer_count"),
                vertical_rank=b.get("vertical_rank"),
                vertical_percentile=b.get("vertical_percentile"),
                vertical_avg=b.get("vertical_avg"),
                vertical_max=b.get("vertical_max"),
                vertical_min=b.get("vertical_min"),
                nearest_peers=b.get("nearest_peers"),
            )
            db.add(benchmark)

        print(f"  Loaded {len(benchmarks_list)} benchmarks")

        # 4. Load model metrics
        print("Loading model metrics...")
        metrics = load_json("model_metrics.json")
        mm = ModelMetrics(
            model_version=metrics.get("model_version", "1.0"),
            framework=metrics.get("framework", "XGBoost"),
            training_set_size=metrics.get("training_set_size"),
            num_dimensions=metrics.get("num_dimensions", 17),
            cv_accuracy=metrics.get("cv_accuracy"),
            cv_std=metrics.get("cv_std"),
            cv_folds=metrics.get("cv_folds", 5),
            backtest_accuracy=metrics.get("backtest_accuracy"),
            backtest_adjacent_accuracy=metrics.get("backtest_adjacent_accuracy"),
            backtest_avg_deviation=metrics.get("backtest_avg_deviation"),
            backtest_count=metrics.get("backtest_count"),
            feature_importance=metrics.get("feature_importance"),
            derived_weights=metrics.get("derived_weights"),
            original_weights=metrics.get("original_weights"),
            categories=metrics.get("categories"),
            dimension_labels=metrics.get("dimension_labels"),
            tier_distribution_training=metrics.get("tier_distribution_training"),
            backtest_results=metrics.get("backtest_results"),
            trained_at=metrics.get("trained_at"),
        )
        db.add(mm)
        print("  Loaded model metrics")

        db.commit()
        print("\nMigration complete!")
        print(f"  Companies: {db.query(Company).count()}")
        print(f"  Dimension scores: {db.query(DimensionScore).count()}")
        print(f"  Company scores: {db.query(CompanyScore).count()}")
        print(f"  Benchmarks: {db.query(Benchmark).count()}")
        print(f"  Model metrics: {db.query(ModelMetrics).count()}")
        print(f"  Training signals: {db.query(TrainingSignal).count()}")

    except Exception as e:
        db.rollback()
        print(f"Migration failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        db_url = sys.argv[1]
    else:
        db_url = os.environ.get("DATABASE_URL", "sqlite:///./data/solen.db")

    print(f"Migrating to: {db_url[:30]}...")
    migrate(db_url)
