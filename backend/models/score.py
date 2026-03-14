"""Score model"""
from sqlalchemy import Column, String, Float, Integer, DateTime, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()


class Score(Base):
    """AI readiness score for a company"""

    __tablename__ = "scores"

    id = Column(String, primary_key=True, index=True, default=lambda: f"sc_{uuid.uuid4().hex[:8]}")
    company_id = Column(String, ForeignKey("companies.id"), nullable=False, index=True)
    job_id = Column(String, ForeignKey("agent_jobs.id"), nullable=True, index=True)
    composite_score = Column(Float, nullable=False)
    tier = Column(String, nullable=False)  # AI-Ready, AI-Buildable, AI-Emerging, AI-Limited
    wave = Column(Integer, nullable=True)  # 1, 2, or 3
    pillar_scores = Column(JSON, nullable=True)  # {pillar: weighted_score}
    pillar_breakdown = Column(JSON, nullable=True)  # {pillar: {score, weight, weighted}}
    model_version = Column(String, default="1.0", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
