"""FastMCP Server for Solen AI Intelligence Platform"""
import os
import json
from typing import Any
from fastmcp import FastMCP
from tools.web_search import web_search
from tools.web_scraper import scrape_url
from tools.crunchbase import search_crunchbase
from tools.sec_edgar import search_sec_edgar
from tools.github_analyzer import analyze_github

# Initialize FastMCP server
mcp = FastMCP("solen-intelligence")


@mcp.tool()
async def web_search_tool(query: str, max_results: int = 5) -> dict[str, Any]:
    """
    Search the web for company intelligence.

    Args:
        query: Search query string
        max_results: Maximum number of results to return

    Returns:
        Search results with titles, URLs, and content
    """
    return await web_search(query, max_results)


@mcp.tool()
async def scrape_webpage(url: str) -> dict[str, Any]:
    """
    Scrape a webpage and extract text content.

    Args:
        url: URL to scrape

    Returns:
        Extracted page content and metadata
    """
    return await scrape_url(url)


@mcp.tool()
async def crunchbase_search(company_name: str) -> dict[str, Any]:
    """
    Get company funding, employee count, and description from Crunchbase.

    Args:
        company_name: Name of the company to search for

    Returns:
        Company information including funding, stage, and headcount
    """
    return await search_crunchbase(company_name)


@mcp.tool()
async def sec_edgar_search(company_name: str) -> dict[str, Any]:
    """
    Search SEC EDGAR for company filings.

    Args:
        company_name: Name of the company to search for

    Returns:
        SEC filing information and CIK numbers
    """
    return await search_sec_edgar(company_name)


@mcp.tool()
async def analyze_github_org(company_name: str, org_name: str = "") -> dict[str, Any]:
    """
    Analyze company GitHub organization for AI tooling and tech stack.

    Args:
        company_name: Name of the company
        org_name: GitHub organization name (optional)

    Returns:
        GitHub organization analysis including repos and activity
    """
    return await analyze_github(company_name, org_name)


@mcp.tool()
async def store_research_data(
    company_id: str, pillar: str, evidence: dict[str, Any]
) -> dict[str, Any]:
    """
    Store research findings to the backend database.

    Args:
        company_id: ID of the company
        pillar: Pillar name (e.g., "data_quality")
        evidence: Evidence dictionary with score, confidence, sources

    Returns:
        Confirmation of storage
    """
    # This is a placeholder that acknowledges the data
    # Real implementation would call backend API
    return {
        "status": "acknowledged",
        "company_id": company_id,
        "pillar": pillar,
        "evidence": evidence,
        "timestamp": "2024-01-01T00:00:00Z",
    }


@mcp.tool()
async def get_research_results(company_id: str) -> dict[str, Any]:
    """
    Retrieve all research findings for a company.

    Args:
        company_id: ID of the company

    Returns:
        All research results for the company
    """
    # Placeholder implementation
    return {
        "company_id": company_id,
        "status": "no_research",
        "pillars": {},
    }


async def health_check() -> dict[str, str]:
    """Health check endpoint"""
    return {"status": "healthy", "service": "solen-mcp"}


if __name__ == "__main__":
    import uvicorn

    # Configure FastMCP with health endpoint
    app = mcp.asgi_app

    # Mount health check
    @app.get("/health")
    async def _health():
        return await health_check()

    # Run the server
    uvicorn.run(app, host="0.0.0.0", port=8001)
