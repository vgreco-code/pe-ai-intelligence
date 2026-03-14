"""Derive pillar weights from model feature importance"""
from typing import Dict, Any


def derive_weights(
    feature_importance: Dict[str, float], feature_names: list
) -> Dict[str, float]:
    """
    Extract pillar weights from XGBoost feature importances.

    Args:
        feature_importance: Feature importance dictionary from trained model
        feature_names: List of feature names

    Returns:
        Dictionary mapping pillars to derived weights
    """
    pillar_names = [
        "data_quality",
        "workflow_digitization",
        "infrastructure",
        "competitive_position",
        "revenue_upside",
        "margin_upside",
        "org_readiness",
        "risk_compliance",
    ]

    pillar_weights = {}

    # Extract importance for score features (confidence features have minimal importance)
    for pillar in pillar_names:
        score_key = f"{pillar}_score"
        importance = feature_importance.get(score_key, 0.0)
        pillar_weights[pillar] = importance

    # Normalize to sum to 1.0
    total = sum(pillar_weights.values())
    if total > 0:
        pillar_weights = {k: v / total for k, v in pillar_weights.items()}

    # Scale to match original framework weights if needed
    return pillar_weights
