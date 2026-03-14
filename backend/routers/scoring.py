"""Scoring pipeline endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from database import get_db
from models.company import Company
from models.research import ResearchResult
from models.score import Score
from models.job import AgentJob
from schemas.score import ScoreResponse
from schemas.job import JobResponse
from services.agent_service import AgentService
from services.scoring_service import (
    calculate_composite_score,
    get_tier,
    get_wave,
    build_pillar_breakdown,
)
from typing import Dict, List
import asyncio

router = APIRouter(prefix="/api/scoring", tags=["scoring"])


@router.post("/run", response_model=JobResponse)
async def start_scoring(
    request: Dict[str, List[str]],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Start scoring pipeline for companies"""
    company_ids = request.get("company_ids", [])

    if not company_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No companies specified")

    # Create job
    agent_service = AgentService(db)
    job = agent_service.create_job("scoring", len(company_ids))

    # Run scoring in background
    background_tasks.add_task(_run_scoring, job.id, company_ids, db)

    return job


async def _run_scoring(job_id: str, company_ids: List[str], db: Session):
    """Run scoring for companies"""
    agent_service = AgentService(db)

    try:
        for idx, company_id in enumerate(company_ids):
            # Update progress
            agent_service.update_job_progress(job_id, idx + 1, "running")

            # Get research results
            research = (
                db.query(ResearchResult)
                .filter(ResearchResult.company_id == company_id)
                .order_by(ResearchResult.created_at.desc())
                .first()
            )

            if research and research.pillar_data:
                # Extract pillar scores from research
                pillar_scores = {
                    pillar: data.get("score", 3.0)
                    for pillar, data in research.pillar_data.items()
                }
            else:
                # Use mock scores if no research exists
                pillar_scores = {
                    "data_quality": 3.5,
                    "workflow_digitization": 3.2,
                    "infrastructure": 3.0,
                    "competitive_position": 3.4,
                    "revenue_upside": 3.1,
                    "margin_upside": 3.0,
                    "org_readiness": 2.8,
                    "risk_compliance": 3.3,
                }

            # Calculate composite score
            composite_score = calculate_composite_score(pillar_scores)
            tier = get_tier(composite_score)
            wave = get_wave(tier)

            # Build breakdown
            pillar_breakdown = build_pillar_breakdown(pillar_scores)

            # Store score
            score = Score(
                company_id=company_id,
                job_id=job_id,
                composite_score=composite_score,
                tier=tier,
                wave=wave,
                pillar_scores=pillar_scores,
                pillar_breakdown=pillar_breakdown,
                model_version="1.0",
            )
            db.add(score)
            db.commit()

            await asyncio.sleep(0.3)  # Simulate work

        agent_service.complete_job(job_id)

    except Exception as e:
        agent_service.fail_job(job_id, str(e))
        raise


@router.get("/{company_id}", response_model=ScoreResponse)
async def get_company_score(company_id: str, db: Session = Depends(get_db)):
    """Get latest score for a company"""
    score = (
        db.query(Score)
        .filter(Score.company_id == company_id)
        .order_by(Score.created_at.desc())
        .first()
    )

    if not score:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No score found")

    return score
