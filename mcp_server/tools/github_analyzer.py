"""GitHub analyzer tool for company repository analysis"""
import os
from typing import Any
import httpx


async def analyze_github(company_name: str, org_name: str = "") -> dict[str, Any]:
    """
    Analyze company GitHub org for AI tooling, repo activity, tech stack.
    Uses GitHub API if GITHUB_TOKEN is set, otherwise returns mock data.

    Args:
        company_name: Name of the company
        org_name: GitHub organization name (optional, defaults to company_name)

    Returns:
        Dictionary with GitHub analysis
    """
    github_token = os.getenv("GITHUB_TOKEN", "").strip()
    org = org_name or company_name.lower().replace(" ", "-")

    if not github_token:
        return _mock_github_data(company_name, org)

    try:
        headers = {"Authorization": f"token {github_token}"}

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Get org info
            org_response = await client.get(
                f"https://api.github.com/orgs/{org}",
                headers=headers,
            )

            if org_response.status_code != 200:
                return _mock_github_data(company_name, org)

            org_data = org_response.json()

            # Get repos
            repos_response = await client.get(
                f"https://api.github.com/orgs/{org}/repos",
                params={"sort": "updated", "per_page": 10},
                headers=headers,
            )

            repos = repos_response.json() if repos_response.status_code == 200 else []

            return {
                "org_name": org_data.get("name", org),
                "url": org_data.get("blog", ""),
                "public_repos": org_data.get("public_repos", 0),
                "followers": org_data.get("followers", 0),
                "repos": [
                    {
                        "name": repo.get("name"),
                        "stars": repo.get("stargazers_count", 0),
                        "language": repo.get("language", "Unknown"),
                        "updated": repo.get("updated_at"),
                        "description": repo.get("description", ""),
                    }
                    for repo in repos
                ],
                "status": "success",
            }

    except Exception as e:
        return {
            "error": str(e),
            "status": "error",
            **_mock_github_data(company_name, org),
        }


def _mock_github_data(company_name: str, org_name: str) -> dict[str, Any]:
    """Generate mock GitHub data for testing"""
    return {
        "org_name": company_name,
        "url": f"https://github.com/{org_name}",
        "public_repos": 15,
        "followers": 250,
        "repos": [
            {
                "name": "platform-core",
                "stars": 450,
                "language": "Python",
                "updated": "2024-01-10",
                "description": "Main platform repository with AI integration",
            },
            {
                "name": "api-service",
                "stars": 180,
                "language": "TypeScript",
                "updated": "2024-01-08",
                "description": "REST API service for company platform",
            },
            {
                "name": "ml-models",
                "stars": 320,
                "language": "Python",
                "updated": "2024-01-05",
                "description": "Machine learning model implementations",
            },
            {
                "name": "frontend-app",
                "stars": 200,
                "language": "TypeScript",
                "updated": "2024-01-12",
                "description": "React-based web application",
            },
        ],
        "status": "mock",
    }
