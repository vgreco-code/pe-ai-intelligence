"""SEC EDGAR tool for accessing company filings"""
import os
from typing import Any
import httpx


async def search_sec_edgar(company_name: str) -> dict[str, Any]:
    """
    Search SEC EDGAR for company filings.
    Uses SEC EDGAR full-text search API (free, no key required).

    Args:
        company_name: Name of the company to search for

    Returns:
        Dictionary with filing information
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # SEC EDGAR API endpoint
            response = await client.get(
                "https://data.sec.gov/submissions/CIK0000000000/company_tickers.json",
                headers={"User-Agent": "Solen AI"},
            )

            # Also try the full-text search
            search_response = await client.get(
                f"https://www.sec.gov/cgi-bin/browse-edgar",
                params={
                    "company": company_name,
                    "action": "getcompany",
                    "output": "json",
                },
                headers={"User-Agent": "Solen AI"},
            )

            if search_response.status_code == 200:
                data = search_response.json()
                if data.get("CIK"):
                    return {
                        "cik": data.get("CIK"),
                        "company_name": data.get("name", company_name),
                        "filings": _extract_filings(data.get("filings", [])),
                        "status": "success",
                    }

        return _mock_sec_data(company_name)

    except Exception as e:
        return {
            "error": str(e),
            "status": "error",
            **_mock_sec_data(company_name),
        }


def _extract_filings(filings_data: list) -> list[dict[str, Any]]:
    """Extract relevant filing information"""
    relevant_filings = []
    for filing in filings_data[:5]:  # Get most recent 5
        if isinstance(filing, dict):
            relevant_filings.append(
                {
                    "form": filing.get("form", ""),
                    "date": filing.get("date", ""),
                    "accession": filing.get("accession_number", ""),
                }
            )
    return relevant_filings


def _mock_sec_data(company_name: str) -> dict[str, Any]:
    """Generate mock SEC data for testing"""
    return {
        "company_name": company_name,
        "cik": "0000000000",
        "filings": [
            {
                "form": "10-K",
                "date": "2024-01-15",
                "accession": "0000000000-24-000001",
            },
            {
                "form": "10-Q",
                "date": "2023-11-10",
                "accession": "0000000000-23-000045",
            },
            {
                "form": "8-K",
                "date": "2023-09-20",
                "accession": "0000000000-23-000032",
            },
        ],
        "status": "mock",
    }
