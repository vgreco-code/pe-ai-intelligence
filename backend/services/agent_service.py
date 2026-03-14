"""Agent service for managing research and scoring jobs"""
import asyncio
from typing import Callable, Optional
from sqlalchemy.orm import Session
from models.job import AgentJob


class AgentService:
    """Service for managing agent job execution"""

    def __init__(self, db: Session):
        self.db = db

    def create_job(self, job_type: str, total_companies: int) -> AgentJob:
        """Create a new agent job"""
        job = AgentJob(
            job_type=job_type,
            status="pending",
            progress=0,
            total_companies=total_companies,
            completed_companies=0,
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def update_job_progress(
        self, job_id: str, completed: int, status: str = "running", error: Optional[str] = None
    ) -> AgentJob:
        """Update job progress"""
        job = self.db.query(AgentJob).filter(AgentJob.id == job_id).first()
        if job:
            job.completed_companies = completed
            job.status = status
            if error:
                job.error_message = error
            job.progress = int((completed / job.total_companies) * 100) if job.total_companies > 0 else 0
            self.db.commit()
            self.db.refresh(job)
        return job

    def complete_job(self, job_id: str) -> AgentJob:
        """Mark job as completed"""
        from datetime import datetime

        job = self.db.query(AgentJob).filter(AgentJob.id == job_id).first()
        if job:
            job.status = "completed"
            job.progress = 100
            job.completed_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(job)
        return job

    def fail_job(self, job_id: str, error: str) -> AgentJob:
        """Mark job as failed"""
        from datetime import datetime

        job = self.db.query(AgentJob).filter(AgentJob.id == job_id).first()
        if job:
            job.status = "failed"
            job.error_message = error
            job.completed_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(job)
        return job

    def get_job(self, job_id: str) -> Optional[AgentJob]:
        """Get job by ID"""
        return self.db.query(AgentJob).filter(AgentJob.id == job_id).first()
