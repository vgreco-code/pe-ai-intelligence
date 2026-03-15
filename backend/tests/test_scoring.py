"""Tests for scoring service"""
import pytest
from services.scoring_service import (
    calculate_composite_score,
    get_tier,
    get_wave,
    build_pillar_breakdown,
    PILLARS,
    TOTAL_WEIGHT,
)


# --- calculate_composite_score ---

def test_calculate_composite_score_typical():
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


def test_calculate_composite_score_all_max():
    pillar_scores = {p: 5.0 for p in PILLARS}
    score = calculate_composite_score(pillar_scores)
    assert score == 5.0


def test_calculate_composite_score_all_zero():
    pillar_scores = {p: 0.0 for p in PILLARS}
    score = calculate_composite_score(pillar_scores)
    assert score == 0.0


def test_calculate_composite_score_clamped_above_max():
    # Scores above 5 should be clamped to 5.0
    pillar_scores = {p: 10.0 for p in PILLARS}
    score = calculate_composite_score(pillar_scores)
    assert score == 5.0


def test_calculate_composite_score_partial_pillars():
    # Only data_quality (weight 2.0) scored, rest missing
    score = calculate_composite_score({"data_quality": 4.0})
    assert score == round((4.0 * 2.0) / TOTAL_WEIGHT, 2)


def test_calculate_composite_score_unknown_pillars_ignored():
    pillar_scores = {p: 3.0 for p in PILLARS}
    pillar_scores["nonexistent_pillar"] = 5.0
    score_with_unknown = calculate_composite_score(pillar_scores)
    score_without = calculate_composite_score({p: 3.0 for p in PILLARS})
    assert score_with_unknown == score_without


def test_calculate_composite_score_returns_float():
    score = calculate_composite_score({"data_quality": 3.5})
    assert isinstance(score, float)


def test_calculate_composite_score_rounded_to_2dp():
    score = calculate_composite_score({"data_quality": 3.333})
    assert score == round(score, 2)


# --- get_tier ---

def test_get_tier_ai_ready():
    assert get_tier(4.0) == "AI-Ready"
    assert get_tier(5.0) == "AI-Ready"
    assert get_tier(4.5) == "AI-Ready"


def test_get_tier_ai_buildable():
    assert get_tier(3.2) == "AI-Buildable"
    assert get_tier(3.5) == "AI-Buildable"
    assert get_tier(3.99) == "AI-Buildable"


def test_get_tier_ai_emerging():
    assert get_tier(2.5) == "AI-Emerging"
    assert get_tier(2.8) == "AI-Emerging"
    assert get_tier(3.19) == "AI-Emerging"


def test_get_tier_ai_limited():
    assert get_tier(0.0) == "AI-Limited"
    assert get_tier(2.0) == "AI-Limited"
    assert get_tier(2.49) == "AI-Limited"


def test_get_tier_boundary_exact_4():
    assert get_tier(4.0) == "AI-Ready"


def test_get_tier_boundary_exact_3_2():
    assert get_tier(3.2) == "AI-Buildable"


def test_get_tier_boundary_exact_2_5():
    assert get_tier(2.5) == "AI-Emerging"


# --- get_wave ---

def test_get_wave_ai_ready():
    assert get_wave("AI-Ready") == 1


def test_get_wave_ai_buildable():
    assert get_wave("AI-Buildable") == 2


def test_get_wave_ai_emerging():
    assert get_wave("AI-Emerging") == 3


def test_get_wave_ai_limited():
    assert get_wave("AI-Limited") == 3


def test_get_wave_unknown_tier_defaults_to_3():
    assert get_wave("Unknown") == 3


# --- build_pillar_breakdown ---

def test_build_pillar_breakdown_structure():
    breakdown = build_pillar_breakdown({"data_quality": 4.0})
    assert "data_quality" in breakdown
    assert set(breakdown["data_quality"].keys()) == {"score", "weight", "weighted"}


def test_build_pillar_breakdown_values():
    breakdown = build_pillar_breakdown({"data_quality": 4.0})
    assert breakdown["data_quality"]["score"] == 4.0
    assert breakdown["data_quality"]["weight"] == 2.0
    assert breakdown["data_quality"]["weighted"] == 8.0


def test_build_pillar_breakdown_multiple_pillars():
    breakdown = build_pillar_breakdown({
        "data_quality": 4.0,
        "workflow_digitization": 3.5,
        "org_readiness": 2.0,
    })
    assert len(breakdown) == 3
    assert breakdown["org_readiness"]["weight"] == 1.0
    assert breakdown["org_readiness"]["weighted"] == 2.0


def test_build_pillar_breakdown_unknown_pillar_excluded():
    breakdown = build_pillar_breakdown({"fake_pillar": 5.0, "data_quality": 3.0})
    assert "fake_pillar" not in breakdown
    assert "data_quality" in breakdown


def test_build_pillar_breakdown_rounding():
    breakdown = build_pillar_breakdown({"data_quality": 3.333})
    assert breakdown["data_quality"]["score"] == round(3.333, 2)
    assert breakdown["data_quality"]["weighted"] == round(3.333 * 2.0, 2)


def test_build_pillar_breakdown_empty_input():
    breakdown = build_pillar_breakdown({})
    assert breakdown == {}


# --- PILLARS constant ---

def test_pillars_total_weight():
    total = sum(p["weight"] for p in PILLARS.values())
    assert total == TOTAL_WEIGHT


def test_pillars_has_all_eight():
    assert len(PILLARS) == 8
    expected = {
        "data_quality", "workflow_digitization", "infrastructure",
        "competitive_position", "revenue_upside", "margin_upside",
        "org_readiness", "risk_compliance",
    }
    assert set(PILLARS.keys()) == expected


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
