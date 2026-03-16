"""Portfolio endpoints — serves data matching frontend JSON shapes"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.company import Company, CompanyScore, Benchmark, PortfolioEvidence

router = APIRouter(prefix="/api", tags=["portfolio"])


@router.get("/portfolio_scores")
async def get_portfolio_scores(db: Session = Depends(get_db)):
    """Returns portfolio companies with scores — matches portfolio_scores.json shape"""
    companies = (
        db.query(Company, CompanyScore)
        .join(CompanyScore, Company.id == CompanyScore.company_id)
        .filter(Company.is_portfolio == True)
        .order_by(CompanyScore.composite_score.desc())
        .all()
    )

    result = []
    for company, score in companies:
        result.append({
            "name": company.name,
            "vertical": company.vertical,
            "employee_count": company.employee_count,
            "description": company.description,
            "website": company.website,
            "founded_year": company.founded_year,
            "composite_score": score.composite_score,
            "tier": score.tier,
            "wave": score.wave,
            "pillar_scores": score.pillar_scores or {},
            "category_scores": score.category_scores or {},
            "confidence_score": score.confidence_score,
            "confidence_breakdown": score.confidence_breakdown,
        })
    return result


@router.get("/competitive_benchmarks")
async def get_competitive_benchmarks(db: Session = Depends(get_db)):
    """Returns benchmark data — matches competitive_benchmarks.json shape"""
    benchmarks = (
        db.query(Company, Benchmark)
        .join(Benchmark, Company.id == Benchmark.company_id)
        .all()
    )

    portfolio_benchmarks = []
    for company, bm in benchmarks:
        portfolio_benchmarks.append({
            "name": company.name,
            "score": bm.score,
            "tier": bm.tier,
            "wave": bm.wave,
            "peer_verticals": bm.peer_verticals or [],
            "peer_vertical": ", ".join(bm.peer_verticals or []),
            "peer_count": bm.peer_count,
            "vertical_rank": bm.vertical_rank,
            "vertical_percentile": bm.vertical_percentile,
            "vertical_avg": bm.vertical_avg,
            "vertical_max": bm.vertical_max,
            "vertical_min": bm.vertical_min,
            "nearest_peers": bm.nearest_peers or [],
        })

    return {"portfolio_benchmarks": portfolio_benchmarks}


@router.get("/wave_sequencing")
async def get_wave_sequencing(db: Session = Depends(get_db)):
    """Returns wave groupings — matches wave_sequencing.json shape"""
    companies = (
        db.query(Company, CompanyScore)
        .join(CompanyScore, Company.id == CompanyScore.company_id)
        .filter(Company.is_portfolio == True)
        .all()
    )

    waves = {
        "Wave 1 (Deploy Now)": [],
        "Wave 2 (Build Foundation)": [],
        "Wave 3 (Groundwork)": [],
    }
    wave_labels = {1: "Wave 1 (Deploy Now)", 2: "Wave 2 (Build Foundation)", 3: "Wave 3 (Groundwork)"}

    for company, score in companies:
        wave_key = wave_labels.get(score.wave, "Wave 3 (Year 2)")
        # Find top category
        cat_scores = score.category_scores or {}
        top_cat = max(cat_scores, key=cat_scores.get) if cat_scores else "N/A"
        waves[wave_key].append({
            "name": company.name,
            "score": score.composite_score,
            "tier": score.tier,
            "top_category": top_cat,
        })

    return waves


@router.get("/portfolio_evidence")
async def get_portfolio_evidence(db: Session = Depends(get_db)):
    """Returns evidence data for all portfolio companies — matches portfolio_evidence.json shape"""
    rows = (
        db.query(Company, PortfolioEvidence)
        .join(PortfolioEvidence, Company.id == PortfolioEvidence.company_id)
        .filter(Company.is_portfolio == True)
        .all()
    )

    result = {}
    for company, ev in rows:
        result[company.name] = {
            "executives": ev.executives or [],
            "named_customers": ev.customers or [],
            "ai_initiatives": ev.ai_initiatives or [],
            "tech_stack": ev.tech_stack or [],
            "github": ev.github or {},
            "careers": ev.careers or {},
            "talent": ev.talent or {},
            "recent_news": ev.news or [],
            "key_evidence": [
                {**item, "text": item.pop("content", item.get("text", ""))}
                for item in (ev.evidence or [])
            ],
            "narrative_summary": ev.narrative or "",
        }
    return result


@router.get("/tier_distribution")
async def get_tier_distribution(db: Session = Depends(get_db)):
    """Returns tier counts — matches tier_distribution.json shape"""
    companies = (
        db.query(CompanyScore)
        .join(Company, Company.id == CompanyScore.company_id)
        .filter(Company.is_portfolio == True)
        .all()
    )

    distribution = {}
    for score in companies:
        distribution[score.tier] = distribution.get(score.tier, 0) + 1
    return distribution
