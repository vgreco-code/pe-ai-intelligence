"""Agent job model for tracking research and scoring runs"""
from sqlalchemy import Column, String, Integer, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()


class AgentJob(Base):
    """Tracks research and scoring job execution"""

    __tablename__ = "agent_jobs"

    id = Column(String, primary_key=True, index=True, default=lambda: f"job_{uuid.uuid4().hex[:8]}")
    job_type = Column(String, nullable=False)  # research, scoring, ml_training
    status = Column(String, default="pending", nullable=False)  # pending, running, completed, failed
    progress = Column(Integer, default=0, nullable=False)  # 0-100
    total_companies = Column(Integer, default=0, nullable=False)
    completed_companies = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
