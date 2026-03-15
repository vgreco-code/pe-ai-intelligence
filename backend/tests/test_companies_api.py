"""Tests for /api/companies endpoints"""
import pytest


def test_list_companies_empty(client):
    response = client.get("/api/companies")
    assert response.status_code == 200
    assert response.json() == []


def test_create_company(client, sample_company_payload):
    response = client.post("/api/companies", json=sample_company_payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Corp"
    assert data["vertical"] == "SaaS"
    assert data["employee_count"] == 50
    assert "id" in data
    assert data["id"].startswith("co_")


def test_create_company_minimal(client):
    response = client.post("/api/companies", json={"name": "Minimal Co"})
    assert response.status_code == 201
    assert response.json()["name"] == "Minimal Co"


def test_create_company_duplicate_name(client, sample_company_payload):
    client.post("/api/companies", json=sample_company_payload)
    response = client.post("/api/companies", json=sample_company_payload)
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_create_company_missing_name(client):
    response = client.post("/api/companies", json={"vertical": "SaaS"})
    assert response.status_code == 422


def test_get_company(client, sample_company_payload):
    created = client.post("/api/companies", json=sample_company_payload).json()
    response = client.get(f"/api/companies/{created['id']}")
    assert response.status_code == 200
    assert response.json()["name"] == "Test Corp"


def test_get_company_not_found(client):
    response = client.get("/api/companies/co_nonexistent")
    assert response.status_code == 404
    assert response.json()["detail"] == "Company not found"


def test_list_companies_returns_all(client, sample_company_payload):
    client.post("/api/companies", json=sample_company_payload)
    client.post("/api/companies", json={"name": "Second Corp"})
    response = client.get("/api/companies")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_list_companies_sorted_by_name(client):
    client.post("/api/companies", json={"name": "Zebra Inc"})
    client.post("/api/companies", json={"name": "Alpha Co"})
    companies = client.get("/api/companies").json()
    names = [c["name"] for c in companies]
    assert names == sorted(names)


def test_update_company(client, sample_company_payload):
    created = client.post("/api/companies", json=sample_company_payload).json()
    updated_payload = {**sample_company_payload, "employee_count": 200}
    response = client.put(f"/api/companies/{created['id']}", json=updated_payload)
    assert response.status_code == 200
    assert response.json()["employee_count"] == 200


def test_update_company_not_found(client, sample_company_payload):
    response = client.put("/api/companies/co_nonexistent", json=sample_company_payload)
    assert response.status_code == 404


def test_delete_company(client, sample_company_payload):
    created = client.post("/api/companies", json=sample_company_payload).json()
    response = client.delete(f"/api/companies/{created['id']}")
    assert response.status_code == 204
    # Confirm it's gone
    assert client.get(f"/api/companies/{created['id']}").status_code == 404


def test_delete_company_not_found(client):
    response = client.delete("/api/companies/co_nonexistent")
    assert response.status_code == 404


def test_company_response_has_timestamps(client, sample_company_payload):
    data = client.post("/api/companies", json=sample_company_payload).json()
    assert "created_at" in data
    assert "updated_at" in data
