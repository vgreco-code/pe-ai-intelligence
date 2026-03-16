"""Export portfolio scores and benchmarks from DB to frontend JSON files."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.company import Company, CompanyScore, Benchmark

database_url = os.environ.get("DATABASE_URL")
if not database_url:
    print("DATABASE_URL not set")
    sys.exit(1)

engine = create_engine(database_url, pool_pre_ping=True)
Session = sessionmaker(bind=engine)
db = Session()

# Export portfolio scores
companies = (
    db.query(Company, CompanyScore)
    .join(CompanyScore, Company.id == CompanyScore.company_id)
    .filter(Company.is_portfolio == True)
    .all()
)

portfolio = []
for c, s in companies:
    portfolio.append({
        "name": c.name,
        "vertical": c.vertical,
        "employee_count": c.employee_count or 50,
        "description": c.description or "",
        "website": c.website or "",
        "founded_year": c.founded_year or 0,
        "composite_score": round(s.composite_score, 2),
        "tier": s.tier,
        "wave": s.wave,
        "pillar_scores": s.pillar_scores or {},
        "category_scores": s.category_scores or {},
        "confidence_score": round(s.confidence_score, 1) if s.confidence_score else None,
        "confidence_breakdown": s.confidence_breakdown or {},
    })

portfolio.sort(key=lambda x: x["composite_score"], reverse=True)

out_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "public", "portfolio_scores.json")
out_path = os.path.normpath(out_path)
with open(out_path, "w") as f:
    json.dump(portfolio, f, indent=2)
print(f"Exported {len(portfolio)} portfolio companies to {out_path}")

# Export competitive benchmarks
benchmarks = db.query(Benchmark).all()
portfolio_benchmarks = []

for b in benchmarks:
    c = db.query(Company).filter(Company.id == b.company_id).first()
    if not c or not c.is_portfolio:
        continue
    s = db.query(CompanyScore).filter(CompanyScore.company_id == c.id).first()
    if not s:
        continue

    # Get peers in same vertical
    peer_data = (
        db.query(Company, CompanyScore)
        .join(CompanyScore, Company.id == CompanyScore.company_id)
        .filter(Company.vertical == c.vertical)
        .all()
    )
    peer_scores = [ps.composite_score for pc, ps in peer_data]
    peer_scores.sort()

    rank = len([x for x in peer_scores if x > s.composite_score]) + 1
    percentile = ((len(peer_scores) - rank) / max(len(peer_scores) - 1, 1)) * 100

    nearest = []
    for pc, ps in sorted(peer_data, key=lambda x: abs(x[1].composite_score - s.composite_score)):
        if pc.id != c.id:
            nearest.append({
                "name": pc.name,
                "score": round(ps.composite_score, 2),
                "tier": ps.tier,
                "vertical": pc.vertical,
            })

    portfolio_benchmarks.append({
        "name": c.name,
        "score": round(s.composite_score, 2),
        "tier": s.tier,
        "wave": s.wave,
        "peer_verticals": list(set(pc.vertical for pc, ps in peer_data if pc.id != c.id))[:5],
        "peer_vertical": c.vertical,
        "peer_count": len(peer_scores),
        "vertical_rank": rank,
        "vertical_percentile": round(percentile, 1),
        "vertical_avg": round(sum(peer_scores) / len(peer_scores), 2),
        "vertical_max": round(max(peer_scores), 2),
        "vertical_min": round(min(peer_scores), 2),
        "nearest_peers": nearest[:5],
    })

bench_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "public", "competitive_benchmarks.json")
bench_path = os.path.normpath(bench_path)
with open(bench_path, "w") as f:
    json.dump({"portfolio_benchmarks": portfolio_benchmarks}, f, indent=2)
print(f"Exported {len(portfolio_benchmarks)} benchmark entries to {bench_path}")

db.close()
