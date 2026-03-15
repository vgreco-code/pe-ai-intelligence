"""Shared test fixtures for backend tests"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models.company import Base, Company, CompanyScore, DimensionScore, Benchmark, ModelMetrics, TrainingSignal

TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def db():
    """Provide a clean database session for each test."""
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client():
    """Test client backed by an isolated in-memory database."""
    Base.metadata.create_all(bind=test_engine)

    from main import app
    from database import get_db
    app.dependency_overrides[get_db] = override_get_db

    from fastapi.testclient import TestClient
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def seeded_client(client):
    """Test client with sample data pre-loaded."""
    db = TestingSessionLocal()

    # Create portfolio companies
    companies = [
        Company(id="co_test1", name="Cairn Applications", vertical="Waste Hauling SaaS",
                employee_count=45, founded_year=2008, website="cairnapp.com",
                description="Waste hauling platform", is_portfolio=True),
        Company(id="co_test2", name="SMRTR", vertical="F&B Supply Chain",
                employee_count=120, founded_year=2015, website="smrtr.io",
                description="Supply chain solutions", is_portfolio=True),
        Company(id="co_test3", name="AutoTime", vertical="A&D Payroll",
                employee_count=75, founded_year=2010, website="autotime.com",
                description="Payroll system", is_portfolio=True),
    ]
    for c in companies:
        db.add(c)

    # Training company (non-portfolio)
    training_co = Company(id="co_train1", name="Salesforce", vertical="CRM",
                          employee_count=70000, is_portfolio=False, is_public=True,
                          has_ai_features=True, cloud_native=True,
                          api_ecosystem_strength=4.5, data_richness=4.2)
    db.add(training_co)

    # Scores for portfolio companies
    pillar_scores_1 = {
        "data_quality": 3.6, "data_integration": 3.3, "analytics_maturity": 3.7,
        "cloud_architecture": 2.3, "tech_stack_modernity": 3.1, "ai_engineering": 2.8,
        "ai_product_features": 3.5, "revenue_ai_upside": 3.8, "margin_ai_upside": 3.2,
        "product_differentiation": 3.6, "ai_talent_density": 2.9, "leadership_ai_vision": 3.4,
        "org_change_readiness": 3.1, "partner_ecosystem": 2.7, "ai_governance": 2.5,
        "regulatory_readiness": 2.8, "ai_momentum": 3.3,
    }
    category_scores_1 = {"Data & Analytics": 3.5, "Technology & Infra": 2.7,
                         "AI Product & Value": 3.5, "Organization & Talent": 3.0,
                         "Governance & Risk": 2.7, "Velocity & Momentum": 3.3}

    db.add(CompanyScore(company_id="co_test1", composite_score=3.30, tier="AI-Buildable",
                        wave=1, pillar_scores=pillar_scores_1, category_scores=category_scores_1))
    db.add(CompanyScore(company_id="co_test2", composite_score=3.15, tier="AI-Buildable",
                        wave=1, pillar_scores={"data_quality": 3.2, "ai_engineering": 3.0},
                        category_scores={"Data & Analytics": 3.2}))
    db.add(CompanyScore(company_id="co_test3", composite_score=2.10, tier="AI-Limited",
                        wave=3, pillar_scores={"data_quality": 2.0, "ai_engineering": 1.8},
                        category_scores={"Data & Analytics": 2.0}))
    db.add(CompanyScore(company_id="co_train1", composite_score=4.50, tier="AI-Ready",
                        pillar_scores={"data_quality": 4.8, "ai_engineering": 4.5}))

    # Dimension scores for Cairn
    for dim, val in pillar_scores_1.items():
        db.add(DimensionScore(company_id="co_test1", dimension=dim, score=val))

    # Benchmark for Cairn
    db.add(Benchmark(
        company_id="co_test1", score=3.30, tier="AI-Buildable", wave=1,
        peer_verticals=["Waste Management", "Fleet Tech"],
        peer_count=25, vertical_rank=6, vertical_percentile=76.0,
        vertical_avg=2.85, vertical_max=4.20, vertical_min=1.50,
        nearest_peers=[{"name": "PeerCo", "score": 3.25, "tier": "AI-Buildable", "vertical": "Waste Mgmt"}],
    ))

    # Model metrics
    db.add(ModelMetrics(
        model_version="4.1", framework="XGBoost", training_set_size=515,
        num_dimensions=17, cv_accuracy=0.8932, cv_std=0.03, cv_folds=5,
        backtest_accuracy=0.431, backtest_adjacent_accuracy=0.931,
        backtest_avg_deviation=0.09, backtest_count=58,
        feature_importance={"data_quality": 0.12, "ai_engineering": 0.15},
        derived_weights={"data_quality": 0.11}, original_weights={"data_quality": 0.10},
        categories={"Data & Analytics": ["data_quality", "data_integration", "analytics_maturity"]},
        dimension_labels={"data_quality": "Data Quality", "ai_engineering": "AI Engineering"},
        tier_distribution_training={"AI-Ready": 9, "AI-Buildable": 89, "AI-Emerging": 241, "AI-Limited": 190},
        backtest_results=[{"name": "TestCo", "actual_tier": "AI-Ready", "predicted_tier": "AI-Ready", "correct": True}],
    ))

    # Training signal
    db.add(TrainingSignal(company_id="co_train1", text_chars=15000, signal_count=42,
                          ai_hiring_signals=8, recent_ai_signals=5, stagnation_signals=0))

    db.commit()
    db.close()

    yield client


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
