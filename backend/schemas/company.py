"""Company schemas"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class CompanyCreate(BaseModel):
    """Schema for creating a company"""

    name: str
    vertical: Optional[str] = None
    website: Optional[str] = None
    github_org: Optional[str] = None
    description: Optional[str] = None
    founded_year: Optional[int] = None
    employee_count: Optional[int] = None


class CompanyResponse(BaseModel):
    """Schema for company response"""

    id: str
    name: str
    vertical: Optional[str] = None
    website: Optional[str] = None
    github_org: Optional[str] = None
    description: Optional[str] = None
    founded_year: Optional[int] = None
    employee_count: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
