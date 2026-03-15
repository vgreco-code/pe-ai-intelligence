"""Tests for core API endpoints (health, root, error handling)"""
import pytest


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "solen-backend"


def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert data["docs"] == "/docs"


def test_openapi_schema_available(client):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert "paths" in response.json()


def test_docs_available(client):
    response = client.get("/docs")
    assert response.status_code == 200


def test_unknown_route_returns_404(client):
    response = client.get("/api/nonexistent")
    assert response.status_code == 404


def test_scoring_run_no_companies(client):
    response = client.post("/api/scoring/run", json={"company_ids": []})
    assert response.status_code == 400
    assert "No companies specified" in response.json()["detail"]


def test_scoring_run_missing_body(client):
    response = client.post("/api/scoring/run", json={})
    assert response.status_code == 400


def test_scoring_get_nonexistent(client):
    response = client.get("/api/scoring/co_nonexistent")
    assert response.status_code == 404
    assert "No score found" in response.json()["detail"]


def test_research_get_nonexistent(client):
    response = client.get("/api/research/co_nonexistent")
    assert response.status_code == 404


def test_jobs_list_empty(client):
    response = client.get("/api/jobs")
    assert response.status_code == 200
    assert response.json() == []


def test_jobs_get_nonexistent(client):
    response = client.get("/api/jobs/job_nonexistent")
    assert response.status_code == 404
