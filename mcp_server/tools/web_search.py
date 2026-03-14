"""Web search tool using Tavily API or mock data"""
import os
import json
from typing import Any
import httpx


async def web_search(query: str, max_results: int = 5) -> dict[str, Any]:
    """
    Search the web for company intelligence.
    Uses Tavily API if TAVILY_API_KEY is set, otherwise returns mock data.

    Args:
        query: Search query string
        max_results: Maximum number of results to return

    Returns:
        Dictionary with search results
    """
    tavily_key = os.getenv("TAVILY_API_KEY", "").strip()

    if not tavily_key:
        # Return mock data when API key is not available
        return _mock_search_results(query, max_results)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": tavily_key,
                    "query": query,
                    "max_results": max_results,
                    "include_answer": True,
                },
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        # Fall back to mock data on error
        return {
            "error": str(e),
            "results": _mock_search_results(query, max_results)["results"],
        }


def _mock_search_results(query: str, max_results: int) -> dict[str, Any]:
    """Generate mock search results for testing"""
    mock_results = [
        {
            "title": f"Company Intelligence Report - {query}",
            "url": f"https://example.com/report/{query.lower().replace(' ', '-')}",
            "content": f"Mock research data for {query}. This company operates in the technology sector with strong growth indicators.",
            "source": "example.com",
        },
        {
            "title": f"{query} Funding Round",
            "url": f"https://example.com/funding/{query.lower().replace(' ', '-')}",
            "content": f"Mock funding information for {query}. Recent investments show strong investor confidence.",
            "source": "example.com",
        },
        {
            "title": f"{query} Market Analysis",
            "url": f"https://example.com/analysis/{query.lower().replace(' ', '-')}",
            "content": f"Mock market data for {query}. The company holds a competitive position in its vertical.",
            "source": "example.com",
        },
    ]

    return {
        "results": mock_results[:max_results],
        "answer": f"Mock summary about {query}",
        "source": "mock_data",
    }
