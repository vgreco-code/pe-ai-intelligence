"""Tests for core API endpoints — health, root, docs"""
import pytest


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "solen" in data["service"].lower()


def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert "endpoints" in data
    assert "/api/portfolio_scores" in data["endpoints"]
    assert "/api/model_metrics" in data["endpoints"]


def test_openapi_schema_available(client):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert "paths" in response.json()


def test_docs_available(client):
    response = client.get("/docs")
    assert response.status_code == 200


def test_unknown_route_returns_404(client):
    response = client.get("/api/nonexistent_endpoint_xyz")
    assert response.status_code in (404, 405)
