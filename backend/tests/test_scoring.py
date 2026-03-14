"""Tests for scoring service"""
import pytest
from services.scoring_service import (
    calculate_composite_score,
    get_tier,
    get_wave,
    build_pillar_breakdown,
    TOTAL_WEIGHT,
)


def test_calculate_composite_score():
    """Test composite score calculation"""
    pillar_scores = {
        "data_quality": 4.0,
        "workflow_digitization": 4.0,
        "infrastructure": 3.5,
        "competitive_position": 3.5,
        "revenue_upside": 3.8,
        "margin_upside": 3.5,
        "org_readiness": 3.0,
        "risk_compliance": 4.0,
    }

    score = calculate_composite_score(pillar_scores)
    assert 3.5 < score < 4.0
    assert score <= 5.0


def test_get_tier():
    """Test tier assignment"""
    assert get_tier(4.5) == "AI-Ready"
    assert get_tier(3.5) == "AI-Buildable"
    assert get_tier(2.8) == "AI-Emerging"
    assert get_tier(2.0) == "AI-Limited"


def test_get_wave():
    """Test wave assignment"""
    assert get_wave("AI-Ready") == 1
    assert get_wave("AI-Buildable") == 2
    assert get_wave("AI-Emerging") == 3
    assert get_wave("AI-Limited") == 3


def test_build_pillar_breakdown():
    """Test pillar breakdown calculation"""
    pillar_scores = {
        "data_quality": 4.0,
        "workflow_digitization": 3.5,
    }

    breakdown = build_pillar_breakdown(pillar_scores)

    assert "data_quality" in breakdown
    assert breakdown["data_quality"]["score"] == 4.0
    assert breakdown["data_quality"]["weight"] == 2.0
    assert breakdown["data_quality"]["weighted"] == 8.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
