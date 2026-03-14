"""Research pipeline endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from database import get_db
from models.company import Company
from models.job import AgentJob
from models.research import ResearchResult
from schemas.job import JobResponse
from services.agent_service import AgentService
from typing import Dict, List
import asyncio
import json

router = APIRouter(prefix="/api/research", tags=["research"])


@router.post("/run", response_model=JobResponse)
async def start_research(
    request: Dict[str, List[str]],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Start research pipeline for companies"""
    company_ids = request.get("company_ids", [])

    if not company_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No companies specified")

    # Create job
    agent_service = AgentService(db)
    job = agent_service.create_job("research", len(company_ids))

    # Run research in background
    background_tasks.add_task(_run_research, job.id, company_ids, db)

    return job


async def _run_research(job_id: str, company_ids: List[str], db: Session):
    """Run research for companies"""
    agent_service = AgentService(db)

    try:
        for idx, company_id in enumerate(company_ids):
            # Update progress
            agent_service.update_job_progress(job_id, idx + 1, "running")

            # Get company
            company = db.query(Company).filter(Company.id == company_id).first()
            if not company:
                continue

            # Generate mock research data
            pillar_scores = {
                "data_quality": 3.5 + (idx * 0.1),
                "workflow_digitization": 3.2 + (idx * 0.15),
                "infrastructure": 3.0 + (idx * 0.12),
                "competitive_position": 3.4 + (idx * 0.11),
                "revenue_upside": 3.1 + (idx * 0.13),
                "margin_upside": 3.0 + (idx * 0.14),
                "org_readiness": 2.8 + (idx * 0.1),
                "risk_compliance": 3.3 + (idx * 0.09),
            }

            # Store research result
            research = ResearchResult(
                company_id=company_id,
                job_id=job_id,
                pillar_data={
                    pillar: {
                        "score": score,
                        "confidence": 0.75 + (idx * 0.02),
                        "evidence": [
                            f"Mock evidence point {i + 1} for {pillar}" for i in range(2)
                        ],
                        "sources": ["https://example.com", "https://research.com"],
                    }
                    for pillar, score in pillar_scores.items()
                },
                raw_summary=f"Mock research summary for {company.name}. Comprehensive analysis across all 8 pillars.",
            )
            db.add(research)
            db.commit()

            await asyncio.sleep(0.5)  # Simulate work

        agent_service.complete_job(job_id)

    except Exception as e:
        agent_service.fail_job(job_id, str(e))
        raise


@router.get("/{company_id}")
async def get_research(company_id: str, db: Session = Depends(get_db)):
    """Get research results for a company"""
    research = (
        db.query(ResearchResult)
        .filter(ResearchResult.company_id == company_id)
        .order_by(ResearchResult.created_at.desc())
        .first()
    )

    if not research:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No research found")

    return {
        "id": research.id,
        "company_id": research.company_id,
        "pillar_data": research.pillar_data,
        "raw_summary": research.raw_summary,
        "created_at": research.created_at,
    }
