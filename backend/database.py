"""Database configuration and initialization"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import os
from config import get_settings

settings = get_settings()

# Create engine based on database URL
if settings.database_url.startswith("sqlite"):
    # SQLite with StaticPool for better async support
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=settings.database_echo,
    )
else:
    # PostgreSQL or other databases
    engine = create_engine(
        settings.database_url,
        echo=settings.database_echo,
        pool_pre_ping=True,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database - create all tables"""
    from models.company import Base as CompanyBase
    from models.research import Base as ResearchBase
    from models.score import Base as ScoreBase
    from models.job import Base as JobBase

    # Create all tables
    for base in [CompanyBase, ResearchBase, ScoreBase, JobBase]:
        base.metadata.create_all(bind=engine)

    # Seed with initial data
    _seed_initial_data()


def _seed_initial_data():
    """Seed database with initial company data"""
    from models.company import Company

    db = SessionLocal()

    # Check if already seeded
    if db.query(Company).count() > 0:
        db.close()
        return

    # Solen portfolio companies
    companies = [
        {
            "name": "Cairn Applications",
            "vertical": "Waste Hauling SaaS",
            "website": "cairnapp.com",
            "employee_count": 45,
            "description": "Software platform for waste hauling and fleet management",
        },
        {
            "name": "SMRTR",
            "vertical": "F&B Supply Chain",
            "website": "smrtr.io",
            "employee_count": 120,
            "description": "Supply chain solutions for food and beverage industry",
        },
        {
            "name": "ViaPeople",
            "vertical": "Talent Management",
            "website": "viapeople.com",
            "employee_count": 65,
            "description": "Talent management and workforce optimization platform",
        },
        {
            "name": "Track Star",
            "vertical": "Fleet & Asset Mgmt",
            "website": "trackstar.com",
            "employee_count": 200,
            "description": "Fleet tracking and asset management solutions",
        },
        {
            "name": "FMSI",
            "vertical": "Banking Operations",
            "website": "fmsi.com",
            "employee_count": 85,
            "description": "Financial management and banking operations software",
        },
        {
            "name": "Champ",
            "vertical": "Public Health EHR",
            "website": "champsoftware.com",
            "employee_count": 150,
            "description": "Electronic health records system for public health agencies",
        },
        {
            "name": "TrackIt Transit",
            "vertical": "Transit Operations",
            "website": "trackittransit.com",
            "employee_count": 30,
            "description": "Transit operations and scheduling platform",
        },
        {
            "name": "NexTalk",
            "vertical": "ADA Communications",
            "website": "nextalk.com",
            "employee_count": 40,
            "description": "Communications platform for ADA compliance and accessibility",
        },
        {
            "name": "Thought Foundry",
            "vertical": "Entertainment PaaS",
            "website": "thoughtfoundry.com",
            "employee_count": 55,
            "description": "Platform as a Service for entertainment and media",
        },
        {
            "name": "Spokane",
            "vertical": "Produce ERP",
            "website": "spokane.com",
            "employee_count": 70,
            "description": "Enterprise resource planning for produce distribution",
        },
        {
            "name": "Primate",
            "vertical": "Energy Control Room",
            "website": "primate.com",
            "employee_count": 90,
            "description": "Energy management and control room operations software",
        },
        {
            "name": "ThingTech",
            "vertical": "IoT Asset Tracking",
            "website": "thingtech.com",
            "employee_count": 110,
            "description": "IoT solutions for asset tracking and monitoring",
        },
        {
            "name": "Dash",
            "vertical": "AP & Doc Automation",
            "website": "dash.com",
            "employee_count": 60,
            "description": "Accounts payable and document automation platform",
        },
        {
            "name": "AutoTime",
            "vertical": "A&D Payroll",
            "website": "autotime.com",
            "employee_count": 75,
            "description": "Architecture and design payroll management system",
        },
    ]

    try:
        for company_data in companies:
            company = Company(**company_data)
            db.add(company)

        db.commit()
        print(f"Seeded {len(companies)} companies")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()
