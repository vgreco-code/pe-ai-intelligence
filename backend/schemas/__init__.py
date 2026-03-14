"""Pydantic schemas for request/response validation"""
from .company import CompanyCreate, CompanyResponse
from .score import ScoreResponse, ScoringRequest
from .job import JobResponse

__all__ = [
    "CompanyCreate",
    "CompanyResponse",
    "ScoreResponse",
    "ScoringRequest",
    "JobResponse",
]
