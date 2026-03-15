"""Training data and model metrics endpoints"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models.company import Company, CompanyScore, ModelMetrics, TrainingSignal, DimensionScore

router = APIRouter(prefix="/api", tags=["training"])


@router.get("/large_training_set")
async def get_training_set(db: Session = Depends(get_db)):
    """Returns full training set — matches large_training_set.json shape"""
    companies = (
        db.query(Company, CompanyScore)
        .join(CompanyScore, Company.id == CompanyScore.company_id)
        .all()
    )

    # Get training signals indexed by company_id
    signals = {s.company_id: s for s in db.query(TrainingSignal).all()}

    result = []
    for company, score in companies:
        sig = signals.get(company.id)
        entry = {
            "name": company.name,
            "vertical": company.vertical,
            "founded_year": company.founded_year,
            "employee_count": company.employee_count,
            "funding_total_usd": company.funding_total_usd,
            "is_public": company.is_public,
            "has_ai_features": company.has_ai_features,
            "cloud_native": company.cloud_native,
            "api_ecosystem_strength": company.api_ecosystem_strength,
            "data_richness": company.data_richness,
            "regulatory_burden": company.regulatory_burden,
            "market_position": company.market_position,
            "pillars": score.pillar_scores or {},
            "composite_score": score.composite_score,
            "tier": score.tier,
        }
        if sig:
            entry.update({
                "text_chars": sig.text_chars,
                "signal_count": sig.signal_count,
                "ai_hiring_signals": sig.ai_hiring_signals,
                "recent_ai_signals": sig.recent_ai_signals,
                "stagnation_signals": sig.stagnation_signals,
            })
        result.append(entry)

    return result


@router.get("/model_metrics")
async def get_model_metrics(db: Session = Depends(get_db)):
    """Returns model metrics — matches model_metrics.json shape"""
    mm = db.query(ModelMetrics).order_by(ModelMetrics.created_at.desc()).first()
    if not mm:
        return {}

    return {
        "model_version": mm.model_version,
        "framework": mm.framework,
        "training_set_size": mm.training_set_size,
        "num_dimensions": mm.num_dimensions,
        "cv_accuracy": mm.cv_accuracy,
        "cv_std": mm.cv_std,
        "cv_folds": mm.cv_folds,
        "backtest_accuracy": mm.backtest_accuracy,
        "backtest_adjacent_accuracy": mm.backtest_adjacent_accuracy,
        "backtest_avg_deviation": mm.backtest_avg_deviation,
        "backtest_count": mm.backtest_count,
        "feature_importance": mm.feature_importance or {},
        "derived_weights": mm.derived_weights or {},
        "original_weights": mm.original_weights or {},
        "categories": mm.categories or {},
        "dimension_labels": mm.dimension_labels or {},
        "tier_distribution_training": mm.tier_distribution_training or {},
        "backtest_results": mm.backtest_results or [],
        "trained_at": str(mm.trained_at) if mm.trained_at else None,
    }


@router.get("/training_stats")
async def get_training_stats(db: Session = Depends(get_db)):
    """Returns training stats — matches training_stats.json shape"""
    total = db.query(Company).count()

    # Tier distribution
    tier_counts = (
        db.query(CompanyScore.tier, func.count(CompanyScore.id))
        .group_by(CompanyScore.tier)
        .all()
    )
    tier_distribution = {tier: count for tier, count in tier_counts}

    # Avg composite score
    avg_score = db.query(func.avg(CompanyScore.composite_score)).scalar() or 0

    # Unique verticals
    verticals = db.query(func.count(func.distinct(Company.vertical))).scalar() or 0

    # Dimension stats
    dimension_stats = {}
    dims = db.query(DimensionScore.dimension).distinct().all()
    mm = db.query(ModelMetrics).first()
    dim_labels = (mm.dimension_labels or {}) if mm else {}
    categories = (mm.categories or {}) if mm else {}

    # Invert categories: dimension -> category
    dim_to_cat = {}
    for cat, dim_list in categories.items():
        for d in dim_list:
            dim_to_cat[d] = cat

    for (dim,) in dims:
        stats = db.query(
            func.avg(DimensionScore.score),
            func.stddev(DimensionScore.score),
            func.min(DimensionScore.score),
            func.max(DimensionScore.score),
        ).filter(DimensionScore.dimension == dim).first()

        dimension_stats[dim] = {
            "label": dim_labels.get(dim, dim.replace("_", " ").title()),
            "category": dim_to_cat.get(dim, "Other"),
            "mean": round(float(stats[0] or 0), 2),
            "std": round(float(stats[1] or 0), 2),
            "min": round(float(stats[2] or 0), 2),
            "max": round(float(stats[3] or 0), 2),
        }

    # Top companies
    top = (
        db.query(Company, CompanyScore)
        .join(CompanyScore, Company.id == CompanyScore.company_id)
        .order_by(CompanyScore.composite_score.desc())
        .limit(10)
        .all()
    )
    top_companies = []
    for company, score in top:
        top_companies.append({
            "name": company.name,
            "vertical": company.vertical,
            "composite_score": score.composite_score,
            "tier": score.tier,
            "pillar_scores": score.pillar_scores or {},
        })

    return {
        "total_companies": total,
        "num_dimensions": len(dimension_stats),
        "framework_version": "v2",
        "verticals": verticals,
        "avg_score": round(float(avg_score), 2),
        "tier_distribution": tier_distribution,
        "dimension_stats": dimension_stats,
        "top_companies": top_companies,
    }
