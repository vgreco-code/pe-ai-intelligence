"""Shared test fixtures for backend tests"""
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Import all model classes to ensure they are registered
from models.company import Company
from models.job import AgentJob
from models.research import ResearchResult
from models.score import Score

TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def _create_all_tables():
    """Create tables in dependency order using raw DDL to bypass cross-metadata FK checks."""
    with test_engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS companies (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                vertical TEXT,
                website TEXT,
                github_org TEXT,
                description TEXT,
                founded_year INTEGER,
                employee_count INTEGER,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS agent_jobs (
                id TEXT PRIMARY KEY,
                job_type TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                progress INTEGER DEFAULT 0,
                total_companies INTEGER DEFAULT 0,
                completed_companies INTEGER DEFAULT 0,
                error_message TEXT,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                completed_at DATETIME
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS research_results (
                id TEXT PRIMARY KEY,
                company_id TEXT NOT NULL,
                job_id TEXT,
                pillar_data JSON,
                raw_summary TEXT,
                research_timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (company_id) REFERENCES companies(id),
                FOREIGN KEY (job_id) REFERENCES agent_jobs(id)
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS scores (
                id TEXT PRIMARY KEY,
                company_id TEXT NOT NULL,
                job_id TEXT,
                composite_score REAL NOT NULL,
                tier TEXT NOT NULL,
                wave INTEGER,
                pillar_scores JSON,
                pillar_breakdown JSON,
                model_version TEXT,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (company_id) REFERENCES companies(id),
                FOREIGN KEY (job_id) REFERENCES agent_jobs(id)
            )
        """))
        conn.commit()


def _drop_all_tables():
    with test_engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS scores"))
        conn.execute(text("DROP TABLE IF EXISTS research_results"))
        conn.execute(text("DROP TABLE IF EXISTS agent_jobs"))
        conn.execute(text("DROP TABLE IF EXISTS companies"))
        conn.commit()


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def client():
    """Test client backed by an isolated in-memory database."""
    _create_all_tables()

    from main import app
    from database import get_db
    app.dependency_overrides[get_db] = override_get_db

    from fastapi.testclient import TestClient
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c

    app.dependency_overrides.clear()
    _drop_all_tables()


@pytest.fixture
def sample_company_payload():
    return {
        "name": "Test Corp",
        "vertical": "SaaS",
        "website": "https://testcorp.com",
        "description": "A test company",
        "founded_year": 2015,
        "employee_count": 50,
    }
