"""Feature engineering for ML model training"""
from typing import Dict, List, Any
import json


def extract_features(research_results: List[Dict[str, Any]]) -> Dict[str, List[float]]:
    """
    Convert research results into ML feature matrix.

    Args:
        research_results: List of research result dictionaries

    Returns:
        Dictionary with feature names as keys and value lists as values
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

    features = {f"{pillar}_score": [] for pillar in pillar_names}
    features.update({f"{pillar}_confidence": [] for pillar in pillar_names})
    features["source_count"] = []
    features["evidence_count"] = []

    for result in research_results:
        pillars = result.get("pillars", {})

        # Extract pillar scores and confidence
        for pillar in pillar_names:
            pillar_data = pillars.get(pillar, {})
            features[f"{pillar}_score"].append(pillar_data.get("score", 3.0))
            features[f"{pillar}_confidence"].append(pillar_data.get("confidence", 0.5))

        # Count sources and evidence
        total_sources = sum(
            len(pillar.get("sources", [])) for pillar in pillars.values()
        )
        total_evidence = sum(
            len(pillar.get("evidence", [])) for pillar in pillars.values()
        )

        features["source_count"].append(total_sources)
        features["evidence_count"].append(total_evidence)

    return features


def load_ground_truth(file_path: str) -> tuple[Dict[str, List[float]], List[str]]:
    """
    Load ground truth data for training.

    Args:
        file_path: Path to ground_truth.json

    Returns:
        Tuple of (features dict, tier labels list)
    """
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
    except Exception:
        return {}, []

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

    features = {f"{pillar}_score": [] for pillar in pillar_names}
    features.update({f"{pillar}_confidence": [] for pillar in pillar_names})
    features["source_count"] = []
    features["evidence_count"] = []

    tiers = []

    for item in data:
        pillar_scores = item.get("pillar_scores", {})

        # Extract pillar scores
        for pillar in pillar_names:
            score = pillar_scores.get(pillar, 3.0)
            features[f"{pillar}_score"].append(score)
            features[f"{pillar}_confidence"].append(0.8)  # Assume high confidence for ground truth

        # Estimate sources and evidence
        features["source_count"].append(5)
        features["evidence_count"].append(8)

        # Add tier label
        tiers.append(item.get("actual_tier", "AI-Emerging"))

    return features, tiers
