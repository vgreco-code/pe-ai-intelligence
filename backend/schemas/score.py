"""Score and scoring schemas"""
from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime


class ScoringRequest(BaseModel):
    """Request to score companies"""

    company_ids: List[str]


class PillarBreakdown(BaseModel):
    """Breakdown of a single pillar score"""

    score: float
    weight: float
    weighted: float
    confidence: Optional[float] = None
    evidence: Optional[List[str]] = None


class ScoreResponse(BaseModel):
    """Score response schema"""

    id: str
    company_id: str
    composite_score: float
    tier: str
    wave: Optional[int] = None
    pillar_scores: Optional[Dict[str, float]] = None
    pillar_breakdown: Optional[Dict[str, PillarBreakdown]] = None
    model_version: str
    created_at: datetime

    class Config:
        from_attributes = True
