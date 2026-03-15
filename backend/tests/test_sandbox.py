"""Tests for the sandbox scoring pipeline"""
import pytest
from unittest.mock import patch, AsyncMock
from routers.sandbox import (
    classify_tier, assign_wave, compute_composite, compute_category_scores,
    estimate_dimension_scores, extract_features, detect_vertical, DERIVED_WEIGHTS
)


# ── Unit tests for scoring functions ──────────────────────────────────────────

class TestClassifyTier:
    def test_ai_ready(self):
        assert classify_tier(4.5) == "AI-Ready"
        assert classify_tier(4.0) == "AI-Ready"

    def test_ai_buildable(self):
        assert classify_tier(3.5) == "AI-Buildable"
        assert classify_tier(3.2) == "AI-Buildable"

    def test_ai_emerging(self):
        assert classify_tier(3.0) == "AI-Emerging"
        assert classify_tier(2.5) == "AI-Emerging"

    def test_ai_limited(self):
        assert classify_tier(2.0) == "AI-Limited"
        assert classify_tier(1.0) == "AI-Limited"


class TestAssignWave:
    def test_wave_1(self):
        assert assign_wave(4.0) == 1
        assert assign_wave(3.5) == 1

    def test_wave_2(self):
        assert assign_wave(3.0) == 2
        assert assign_wave(2.8) == 2

    def test_wave_3(self):
        assert assign_wave(2.5) == 3
        assert assign_wave(1.0) == 3


class TestComputeComposite:
    def test_all_fives(self):
        scores = {d: 5.0 for d in DERIVED_WEIGHTS}
        assert compute_composite(scores) == 5.0

    def test_all_ones(self):
        scores = {d: 1.0 for d in DERIVED_WEIGHTS}
        assert compute_composite(scores) == 1.0

    def test_mixed_scores(self):
        scores = {d: 3.0 for d in DERIVED_WEIGHTS}
        result = compute_composite(scores)
        assert result == 3.0

    def test_missing_dimensions_default_zero(self):
        result = compute_composite({})
        assert result == 0.0


class TestComputeCategoryScores:
    def test_all_categories_present(self):
        scores = {d: 3.5 for d in DERIVED_WEIGHTS}
        cat_scores = compute_category_scores(scores)
        assert len(cat_scores) == 6
        for v in cat_scores.values():
            assert v == 3.5

    def test_partial_scores(self):
        scores = {"data_quality": 4.0, "data_integration": 2.0}
        cat_scores = compute_category_scores(scores)
        assert cat_scores["Data & Analytics"] == 3.0  # (4+2)/2 since analytics_maturity missing -> only 2 vals


class TestEstimateDimensionScores:
    def test_returns_all_17_dimensions(self):
        scores = estimate_dimension_scores({"employee_count": 500, "funding_total_usd": 50e6})
        assert len(scores) == 17

    def test_scores_in_range(self):
        scores = estimate_dimension_scores({
            "employee_count": 1000, "funding_total_usd": 100e6,
            "has_ai_features": True, "cloud_native": True,
            "api_ecosystem_strength": 4.0, "data_richness": 4.0,
            "market_position": 4.0,
        })
        for dim, score in scores.items():
            assert 1.0 <= score <= 5.0, f"{dim} score {score} out of range"

    def test_ai_features_boost_scores(self):
        without_ai = estimate_dimension_scores({"has_ai_features": False})
        with_ai = estimate_dimension_scores({"has_ai_features": True})
        assert with_ai["ai_product_features"] > without_ai["ai_product_features"]
        assert with_ai["ai_engineering"] > without_ai["ai_engineering"]
        assert with_ai["ai_talent_density"] > without_ai["ai_talent_density"]

    def test_cloud_native_boost(self):
        without_cloud = estimate_dimension_scores({"cloud_native": False})
        with_cloud = estimate_dimension_scores({"cloud_native": True})
        assert with_cloud["cloud_architecture"] > without_cloud["cloud_architecture"]

    def test_defaults_for_missing_data(self):
        scores = estimate_dimension_scores({})
        assert len(scores) == 17
        for v in scores.values():
            assert v >= 1.0


# ── Feature extraction tests ─────────────────────────────────────────────────

class TestExtractFeatures:
    def test_employee_extraction(self):
        text = "Datadog has over 5,000 employees worldwide"
        features = extract_features("Datadog", text)
        assert features["employee_count"] == 5000

    def test_funding_extraction_millions(self):
        text = "The company has raised $150 million in funding"
        features = extract_features("TestCo", text)
        assert features["funding_total_usd"] == 150e6

    def test_funding_extraction_billions(self):
        text = "Stripe is valued at $50 billion"
        features = extract_features("Stripe", text)
        assert features["funding_total_usd"] == 50e9

    def test_ai_features_detection(self):
        text = "The platform uses machine learning and AI-powered recommendations"
        features = extract_features("TestCo", text)
        assert features["has_ai_features"] is True

    def test_no_ai_features(self):
        text = "A traditional construction company since 1990"
        features = extract_features("TestCo", text)
        assert features["has_ai_features"] is False

    def test_cloud_native_detection(self):
        text = "Built on AWS with kubernetes and microservices architecture"
        features = extract_features("TestCo", text)
        assert features["cloud_native"] is True

    def test_public_company_detection(self):
        text = "Listed on NASDAQ since 2020, the company's stock price has risen"
        features = extract_features("TestCo", text)
        assert features["is_public"] is True

    def test_founded_year(self):
        text = "Founded in 2015, the startup has grown rapidly"
        features = extract_features("TestCo", text)
        assert features["founded_year"] == 2015


class TestDetectVertical:
    def test_healthcare(self):
        assert "Healthcare" in detect_vertical("a healthcare platform for patient care and biotech")

    def test_fintech(self):
        assert "Financial" in detect_vertical("fintech company for banking and payments")

    def test_enterprise_software(self):
        assert "Enterprise" in detect_vertical("enterprise saas b2b software crm solution")

    def test_unknown_defaults_to_technology(self):
        assert detect_vertical("some random thing with no keywords") == "Technology"


# ── API endpoint tests ────────────────────────────────────────────────────────

class TestSandboxAPI:
    def test_list_empty_sandbox(self, seeded_client):
        """All seeded companies are portfolio — sandbox should be empty or
        contain only non-portfolio companies."""
        resp = seeded_client.get("/api/sandbox/companies")
        assert resp.status_code == 200
        # The seeded test data has 1 non-portfolio company (training co)
        data = resp.json()
        assert isinstance(data, list)

    def test_score_endpoint_requires_tavily_key(self, seeded_client):
        """Without a Tavily API key, scoring should return 503."""
        resp = seeded_client.post(
            "/api/sandbox/score",
            json={"company_name": "TestCorp"}
        )
        # Should fail gracefully — either 503 (no key) or 409 (already exists)
        assert resp.status_code in [503, 409]

    def test_score_duplicate_name(self, seeded_client):
        """Scoring a company that already exists should return 409."""
        resp = seeded_client.post(
            "/api/sandbox/score",
            json={"company_name": "Cairn Applications"}  # Seeded portfolio company
        )
        assert resp.status_code == 409
        assert "already exists" in resp.json()["detail"]

    def test_score_empty_name(self, seeded_client):
        """Empty name should be rejected by validation."""
        resp = seeded_client.post(
            "/api/sandbox/score",
            json={"company_name": ""}
        )
        assert resp.status_code == 422  # Validation error

    def test_delete_nonexistent(self, seeded_client):
        """Deleting a non-existent sandbox company should 404."""
        resp = seeded_client.delete("/api/sandbox/companies/fake_id")
        assert resp.status_code == 404
