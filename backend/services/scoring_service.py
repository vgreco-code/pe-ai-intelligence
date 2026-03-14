"""Scoring service for AI readiness evaluation"""
from typing import Dict, Any


# 8-Pillar Framework Definition
PILLARS = {
    "data_quality": {"weight": 2.0, "label": "Data Quality & Availability"},
    "workflow_digitization": {"weight": 2.0, "label": "Workflow Digitization"},
    "infrastructure": {"weight": 1.5, "label": "Infrastructure Readiness"},
    "competitive_position": {"weight": 2.0, "label": "Competitive Position"},
    "revenue_upside": {"weight": 1.5, "label": "Revenue Upside"},
    "margin_upside": {"weight": 1.5, "label": "Margin Upside"},
    "org_readiness": {"weight": 1.0, "label": "Org Readiness"},
    "risk_compliance": {"weight": 1.0, "label": "Risk & Compliance"},
}

TOTAL_WEIGHT = 12.5
TIERS = [("AI-Ready", 4.0), ("AI-Buildable", 3.2), ("AI-Emerging", 2.5), ("AI-Limited", 0)]


def calculate_composite_score(pillar_scores: Dict[str, float]) -> float:
    """
    Calculate composite score from pillar scores using weighted average.

    Args:
        pillar_scores: Dictionary of pillar names to scores

    Returns:
        Weighted composite score (0-5)
    """
    total_weighted = 0.0

    for pillar, score in pillar_scores.items():
        if pillar in PILLARS:
            weight = PILLARS[pillar]["weight"]
            total_weighted += score * weight

    composite = total_weighted / TOTAL_WEIGHT
    return round(min(5.0, max(0.0, composite)), 2)


def get_tier(composite_score: float) -> str:
    """
    Determine tier based on composite score.

    Args:
        composite_score: Weighted composite score

    Returns:
        Tier name
    """
    for tier_name, min_score in TIERS:
        if composite_score >= min_score:
            return tier_name

    return "AI-Limited"


def get_wave(tier: str) -> int:
    """
    Assign wave number based on tier.

    Args:
        tier: Tier name

    Returns:
        Wave number (1, 2, or 3)
    """
    wave_mapping = {
        "AI-Ready": 1,
        "AI-Buildable": 2,
        "AI-Emerging": 3,
        "AI-Limited": 3,
    }
    return wave_mapping.get(tier, 3)


def build_pillar_breakdown(pillar_scores: Dict[str, float]) -> Dict[str, Dict[str, Any]]:
    """
    Build detailed breakdown of pillar scores with weights.

    Args:
        pillar_scores: Dictionary of pillar scores

    Returns:
        Detailed breakdown with weights and weighted scores
    """
    breakdown = {}

    for pillar, score in pillar_scores.items():
        if pillar in PILLARS:
            weight = PILLARS[pillar]["weight"]
            weighted = score * weight

            breakdown[pillar] = {
                "score": round(score, 2),
                "weight": weight,
                "weighted": round(weighted, 2),
            }

    return breakdown
