"""Crunchbase API tool for company data"""
import os
from typing import Any
import httpx


async def search_crunchbase(company_name: str) -> dict[str, Any]:
    """
    Get company funding, employee count, and description from Crunchbase.
    Uses Crunchbase API if CRUNCHBASE_API_KEY is set, otherwise returns mock data.

    Args:
        company_name: Name of the company to search for

    Returns:
        Dictionary with company information
    """
    crunchbase_key = os.getenv("CRUNCHBASE_API_KEY", "").strip()

    if not crunchbase_key:
        return _mock_crunchbase_data(company_name)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"https://api.crunchbase.com/api/v4/searches/organizations",
                headers={"X-Cb-User-Key": crunchbase_key},
                json={
                    "query": {
                        "type": "full_text",
                        "query": company_name,
                    },
                    "limit": 1,
                },
            )
            response.raise_for_status()
            data = response.json()

            if data.get("entities"):
                entity = data["entities"][0]["properties"]
                return {
                    "name": entity.get("name", company_name),
                    "description": entity.get("short_description", ""),
                    "headquarters": entity.get("headquarters", {}).get("location_identifiers", {}).get("name", ""),
                    "employee_count": entity.get("employee_count", ""),
                    "founded_year": entity.get("founded_year", ""),
                    "total_funding": entity.get("total_funding_usd", 0),
                    "stage": entity.get("last_funding_stage", ""),
                    "status": "success",
                }
            else:
                return _mock_crunchbase_data(company_name)

    except Exception as e:
        return {
            "error": str(e),
            "status": "error",
            **_mock_crunchbase_data(company_name),
        }


def _mock_crunchbase_data(company_name: str) -> dict[str, Any]:
    """Generate mock Crunchbase data for testing"""
    return {
        "name": company_name,
        "description": f"Mock data for {company_name}. Leading software platform in enterprise solutions.",
        "headquarters": "San Francisco, CA",
        "employee_count": 250,
        "founded_year": 2015,
        "total_funding": 50000000,
        "stage": "Series C",
        "status": "mock",
    }
