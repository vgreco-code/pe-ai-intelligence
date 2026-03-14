"""Research result model"""
from sqlalchemy import Column, String, DateTime, Text, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()


class ResearchResult(Base):
    """Research findings for a company"""

    __tablename__ = "research_results"

    id = Column(String, primary_key=True, index=True, default=lambda: f"res_{uuid.uuid4().hex[:8]}")
    company_id = Column(String, ForeignKey("companies.id"), nullable=False, index=True)
    job_id = Column(String, ForeignKey("agent_jobs.id"), nullable=True, index=True)
    pillar_data = Column(JSON, nullable=True)  # {pillar: {score, confidence, evidence, sources}}
    raw_summary = Column(Text, nullable=True)
    research_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
