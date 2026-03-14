"""Web scraper tool for extracting page content"""
import os
from typing import Any
import httpx
from bs4 import BeautifulSoup


async def scrape_url(url: str) -> dict[str, Any]:
    """
    Scrape a webpage and extract text content.

    Args:
        url: URL to scrape

    Returns:
        Dictionary with extracted content
    """
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                },
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            # Get text
            text = soup.get_text(separator="\n", strip=True)
            lines = [line.strip() for line in text.split("\n") if line.strip()]
            clean_text = "\n".join(lines)

            # Get title
            title = soup.find("title")
            title_text = title.string if title else url

            return {
                "url": url,
                "title": title_text,
                "content": clean_text[:5000],  # Limit to 5000 chars
                "content_length": len(clean_text),
                "status": "success",
            }

    except Exception as e:
        return {
            "url": url,
            "error": str(e),
            "status": "error",
            "content": _mock_page_content(url),
        }


def _mock_page_content(url: str) -> str:
    """Generate mock page content for fallback"""
    domain = url.replace("https://", "").replace("http://", "").split("/")[0]
    return f"""
    Company: {domain}

    Mock Website Content

    This is mock content extracted from {url}.
    The company appears to have a modern web presence with
    information about their products and services.

    Key sections typically include:
    - About Us: Company mission and values
    - Products: Service offerings and features
    - Customers: Case studies and testimonials
    - Blog: Industry insights and updates
    - Contact: Ways to get in touch

    Mock content serves as fallback when actual scraping fails.
    """
