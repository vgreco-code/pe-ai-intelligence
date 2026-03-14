"""Job tracking schemas"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class JobResponse(BaseModel):
    """Job status response"""

    id: str
    job_type: str
    status: str
    progress: int
    total_companies: int
    completed_companies: int
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
