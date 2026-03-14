"""Company model"""
from sqlalchemy import Column, String, Integer, DateTime, Text, func
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Company(Base):
    """Company entity"""

    __tablename__ = "companies"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    vertical = Column(String, nullable=True)
    website = Column(String, nullable=True)
    github_org = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    founded_year = Column(Integer, nullable=True)
    employee_count = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __init__(self, **kwargs):
        """Initialize with auto-generated ID if not provided"""
        if "id" not in kwargs:
            kwargs["id"] = self._generate_id(kwargs.get("name", ""))
        super().__init__(**kwargs)

    @staticmethod
    def _generate_id(name: str) -> str:
        """Generate ID from company name"""
        import uuid

        return f"co_{uuid.uuid4().hex[:8]}"
