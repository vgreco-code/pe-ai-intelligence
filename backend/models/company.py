"""SQLAlchemy models for the AI Intelligence platform"""
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, JSON
from sqlalchemy.orm import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()


class Company(Base):
    """Company — both portfolio and training set companies"""
    __tablename__ = "companies"

    id = Column(String, primary_key=True, default=lambda: f"co_{uuid.uuid4().hex[:8]}")
    name = Column(String, unique=True, index=True, nullable=False)
    vertical = Column(String, nullable=True)
    website = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    founded_year = Column(Integer, nullable=True)
    employee_count = Column(Integer, nullable=True)
    funding_total_usd = Column(Float, nullable=True)
    is_public = Column(Boolean, default=False)
    has_ai_features = Column(Boolean, default=False)
    cloud_native = Column(Boolean, default=False)
    api_ecosystem_strength = Column(Float, nullable=True)
    data_richness = Column(Float, nullable=True)
    regulatory_burden = Column(Float, nullable=True)
    market_position = Column(Float, nullable=True)
    is_portfolio = Column(Boolean, default=False, index=True)  # True for Solen portfolio companies
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DimensionScore(Base):
    """Individual dimension scores for a company"""
    __tablename__ = "dimension_scores"

    id = Column(String, primary_key=True, default=lambda: f"ds_{uuid.uuid4().hex[:8]}")
    company_id = Column(String, index=True, nullable=False)
    dimension = Column(String, nullable=False)  # e.g., 'data_quality', 'ai_engineering'
    score = Column(Float, nullable=False)  # 0.0 to 5.0
    model_version = Column(String, default="1.0")
    created_at = Column(DateTime, default=datetime.utcnow)


class CompanyScore(Base):
    """Composite score and tier classification for a company"""
    __tablename__ = "company_scores"

    id = Column(String, primary_key=True, default=lambda: f"cs_{uuid.uuid4().hex[:8]}")
    company_id = Column(String, index=True, nullable=False)
    composite_score = Column(Float, nullable=False)
    tier = Column(String, nullable=False)  # AI-Ready, AI-Buildable, AI-Emerging, AI-Limited
    wave = Column(Integer, nullable=True)
    pillar_scores = Column(JSON, nullable=True)  # {dimension: score}
    category_scores = Column(JSON, nullable=True)  # {category: avg_score}
    confidence_score = Column(Float, nullable=True)  # 0-100 research confidence
    confidence_breakdown = Column(JSON, nullable=True)  # {component: score}
    model_version = Column(String, default="1.0")
    created_at = Column(DateTime, default=datetime.utcnow)


class Benchmark(Base):
    """Competitive benchmark data for a company"""
    __tablename__ = "benchmarks"

    id = Column(String, primary_key=True, default=lambda: f"bm_{uuid.uuid4().hex[:8]}")
    company_id = Column(String, index=True, nullable=False)
    score = Column(Float, nullable=False)
    tier = Column(String, nullable=False)
    wave = Column(Integer, nullable=True)
    peer_verticals = Column(JSON, nullable=True)  # list of strings
    peer_count = Column(Integer, nullable=True)
    vertical_rank = Column(Integer, nullable=True)
    vertical_percentile = Column(Float, nullable=True)
    vertical_avg = Column(Float, nullable=True)
    vertical_max = Column(Float, nullable=True)
    vertical_min = Column(Float, nullable=True)
    nearest_peers = Column(JSON, nullable=True)  # list of {name, score, tier, vertical}
    created_at = Column(DateTime, default=datetime.utcnow)


class ModelMetrics(Base):
    """Model performance metrics and configuration"""
    __tablename__ = "model_metrics"

    id = Column(String, primary_key=True, default=lambda: f"mm_{uuid.uuid4().hex[:8]}")
    model_version = Column(String, nullable=False)
    framework = Column(String, default="XGBoost")
    training_set_size = Column(Integer, nullable=True)
    num_dimensions = Column(Integer, default=17)
    cv_accuracy = Column(Float, nullable=True)
    cv_std = Column(Float, nullable=True)
    cv_folds = Column(Integer, default=5)
    backtest_accuracy = Column(Float, nullable=True)
    backtest_adjacent_accuracy = Column(Float, nullable=True)
    backtest_avg_deviation = Column(Float, nullable=True)
    backtest_count = Column(Integer, nullable=True)
    feature_importance = Column(JSON, nullable=True)  # {dimension: weight}
    derived_weights = Column(JSON, nullable=True)
    original_weights = Column(JSON, nullable=True)
    categories = Column(JSON, nullable=True)
    dimension_labels = Column(JSON, nullable=True)
    tier_distribution_training = Column(JSON, nullable=True)
    backtest_results = Column(JSON, nullable=True)  # list of backtest entries
    trained_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class PortfolioEvidence(Base):
    """Research evidence for portfolio companies — executives, customers, AI initiatives, etc."""
    __tablename__ = "portfolio_evidence"

    id = Column(String, primary_key=True, default=lambda: f"pe_{uuid.uuid4().hex[:8]}")
    company_id = Column(String, index=True, nullable=False)
    executives = Column(JSON, nullable=True)       # [{name, role}]
    customers = Column(JSON, nullable=True)         # [str]
    ai_initiatives = Column(JSON, nullable=True)    # [{text, type}]
    tech_stack = Column(JSON, nullable=True)        # [str]
    github = Column(JSON, nullable=True)            # {org, public_repos, top_languages}
    careers = Column(JSON, nullable=True)           # {ai_roles, total_roles, titles}
    talent = Column(JSON, nullable=True)            # {leadership, team_skills, talent_summary}
    news = Column(JSON, nullable=True)              # [{title, url, date, summary}]
    evidence = Column(JSON, nullable=True)          # [{title, content, url, source}]
    narrative = Column(Text, nullable=True)         # Generated summary
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TrainingSignal(Base):
    """Signal/metadata for training set companies"""
    __tablename__ = "training_signals"

    id = Column(String, primary_key=True, default=lambda: f"ts_{uuid.uuid4().hex[:8]}")
    company_id = Column(String, index=True, nullable=False)
    text_chars = Column(Integer, nullable=True)
    signal_count = Column(Integer, nullable=True)
    ai_hiring_signals = Column(Integer, nullable=True)
    recent_ai_signals = Column(Integer, nullable=True)
    stagnation_signals = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
