"""Third-pass enrichment: GitHub presence + careers page scraping.

Enriches portfolio companies with:
  1. GitHub org/repos — languages, stars, recent commits, open-source activity
  2. Careers page — scraped open job listings with titles and departments

Usage:
    python enrich_github_careers.py                      # Enrich all companies
    python enrich_github_careers.py "Cairn Applications"  # One company
    python enrich_github_careers.py --dry-run             # Preview only

No API keys required (GitHub public API has 60 req/hr unauthenticated).
"""
import asyncio
import json
import os
import re
import sys
import logging
from urllib.parse import urlparse

import httpx

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-5s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

DELAY_BETWEEN_COMPANIES = 2.0

# Known GitHub org overrides (when the org name doesn't match the company name)
GITHUB_ORG_OVERRIDES: dict[str, str | None] = {
    # Add known mappings: "Company Name": "github-org-name"
    # Set to None to skip GitHub lookup entirely
}

# Careers page URL patterns to try
CAREERS_PATHS = [
    "/careers",
    "/jobs",
    "/about/careers",
    "/company/careers",
    "/join-us",
    "/work-with-us",
    "/open-positions",
    "/about-us/careers",
    "/careers/open-positions",
    "/career",
    "/hiring",
]


# ── GitHub Enrichment ────────────────────────────────────────────────────────

async def search_github_org(client: httpx.AsyncClient, company_name: str) -> dict | None:
    """Search GitHub for an organization matching the company name."""
    # Try search API
    try:
        resp = await client.get(
            "https://api.github.com/search/users",
            params={"q": f"{company_name} type:org", "per_page": 5},
            headers={"Accept": "application/vnd.github+json", "User-Agent": "PE-AI-Intelligence"},
        )
        if resp.status_code == 200:
            data = resp.json()
            items = data.get("items", [])
            if items:
                # Score matches by similarity to company name
                company_lower = company_name.lower().replace(" ", "")
                best = None
                best_score = 0
                for item in items:
                    login = item.get("login", "").lower()
                    # Simple fuzzy match
                    score = 0
                    if company_lower in login or login in company_lower:
                        score = 3
                    elif any(word.lower() in login for word in company_name.split()):
                        score = 2
                    elif login.startswith(company_lower[:4]):
                        score = 1
                    if score > best_score:
                        best_score = score
                        best = item
                if best and best_score >= 2:
                    return {"login": best["login"], "url": best["html_url"], "avatar": best.get("avatar_url", "")}
        elif resp.status_code == 403:
            logger.warning("GitHub rate limit reached")
            return None
    except Exception as e:
        logger.warning(f"GitHub search failed for {company_name}: {e}")
    return None


async def get_org_repos(client: httpx.AsyncClient, org_login: str) -> list[dict]:
    """Fetch public repos for a GitHub org."""
    try:
        resp = await client.get(
            f"https://api.github.com/orgs/{org_login}/repos",
            params={"sort": "updated", "per_page": 30, "type": "public"},
            headers={"Accept": "application/vnd.github+json", "User-Agent": "PE-AI-Intelligence"},
        )
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        logger.warning(f"Failed to fetch repos for {org_login}: {e}")
    return []


def analyze_github_repos(repos: list[dict]) -> dict:
    """Analyze repo data for engineering signals."""
    if not repos:
        return {}

    languages = {}
    total_stars = 0
    total_forks = 0
    repo_summaries = []
    recent_activity = 0

    for repo in repos:
        lang = repo.get("language")
        if lang:
            languages[lang] = languages.get(lang, 0) + 1
        total_stars += repo.get("stargazers_count", 0)
        total_forks += repo.get("forks_count", 0)

        # Check recent activity (updated in last 6 months)
        updated = repo.get("updated_at", "")
        if updated and updated >= "2025-09-01":
            recent_activity += 1

        # Keep summary of notable repos
        if repo.get("stargazers_count", 0) >= 5 or repo.get("description"):
            repo_summaries.append({
                "name": repo.get("name", ""),
                "description": (repo.get("description") or "")[:120],
                "language": lang,
                "stars": repo.get("stargazers_count", 0),
                "forks": repo.get("forks_count", 0),
                "updated": updated[:10] if updated else "",
            })

    # Sort languages by frequency
    sorted_langs = sorted(languages.items(), key=lambda x: x[1], reverse=True)

    return {
        "total_public_repos": len(repos),
        "total_stars": total_stars,
        "total_forks": total_forks,
        "recently_active_repos": recent_activity,
        "primary_languages": [{"language": lang, "repo_count": count} for lang, count in sorted_langs[:8]],
        "top_repos": sorted(repo_summaries, key=lambda r: r["stars"], reverse=True)[:6],
    }


async def enrich_github(client: httpx.AsyncClient, company_name: str) -> dict:
    """Full GitHub enrichment for a company."""
    # Check overrides
    if company_name in GITHUB_ORG_OVERRIDES:
        override = GITHUB_ORG_OVERRIDES[company_name]
        if override is None:
            return {"found": False, "reason": "skipped_by_override"}
        org_login = override
        org_info = {"login": override, "url": f"https://github.com/{override}"}
    else:
        org_info = await search_github_org(client, company_name)
        if not org_info:
            # Try with common variations
            variations = [
                company_name.replace(" ", ""),
                company_name.replace(" ", "-").lower(),
                company_name.split()[0].lower() if " " in company_name else None,
            ]
            for var in variations:
                if var:
                    try:
                        resp = await client.get(
                            f"https://api.github.com/orgs/{var}",
                            headers={"Accept": "application/vnd.github+json", "User-Agent": "PE-AI-Intelligence"},
                        )
                        if resp.status_code == 200:
                            data = resp.json()
                            org_info = {"login": data["login"], "url": data.get("html_url", "")}
                            break
                    except:
                        pass
            if not org_info:
                return {"found": False, "reason": "no_matching_org"}
        org_login = org_info["login"]

    # Fetch repos
    repos = await get_org_repos(client, org_login)
    analysis = analyze_github_repos(repos)

    return {
        "found": True,
        "org_login": org_login,
        "org_url": org_info.get("url", f"https://github.com/{org_login}"),
        **analysis,
    }


# ── Careers Page Scraping ─────────────────────────────────────────────────────

def extract_jobs_from_text(text: str, company_name: str) -> list[dict]:
    """Extract job listings from scraped careers page text."""
    if not text or len(text) < 50:
        return []

    jobs = []
    seen_titles = set()

    # Common job title patterns
    job_patterns = [
        # "Senior Software Engineer" style titles
        r'(?:^|\n)\s*(?:Senior |Lead |Staff |Principal |Junior |Associate |Head of |Director of |VP of |Manager[,] )?'
        r'(?:Software|Frontend|Backend|Full[- ]Stack|DevOps|Data|ML|Machine Learning|AI|Cloud|Platform|'
        r'Infrastructure|Security|QA|Quality|Product|Engineering|Solutions|Mobile|iOS|Android|'
        r'Site Reliability|SRE|Systems?|Network|Database|Analytics|Business|Sales|Marketing|'
        r'Customer|Account|Finance|HR|Human Resources|Operations|Design|UX|UI)'
        r'(?:\s+(?:Engineer|Developer|Scientist|Analyst|Architect|Manager|Lead|Director|Specialist|'
        r'Consultant|Administrator|Coordinator|Designer|Researcher|Strategist|Representative))?'
        r'(?:\s+(?:I{1,3}|[1-3]|Sr|Jr))?',
    ]

    for pat in job_patterns:
        for m in re.finditer(pat, text, re.IGNORECASE | re.MULTILINE):
            title = m.group(0).strip()
            if len(title) < 8 or len(title) > 80:
                continue
            title_lower = title.lower()
            if title_lower in seen_titles:
                continue
            # Filter out common false positives
            skip_words = ['the ', 'our ', 'your ', 'this ', 'that ', 'about ', 'with ']
            if any(title_lower.startswith(w) for w in skip_words):
                continue
            seen_titles.add(title_lower)

            # Detect department/category
            dept = "Engineering"
            if any(w in title_lower for w in ["data", "analytics", "ml", "machine learning", "ai"]):
                dept = "Data & AI"
            elif any(w in title_lower for w in ["product", "design", "ux", "ui"]):
                dept = "Product & Design"
            elif any(w in title_lower for w in ["sales", "account", "business"]):
                dept = "Sales & Business"
            elif any(w in title_lower for w in ["marketing", "content"]):
                dept = "Marketing"
            elif any(w in title_lower for w in ["devops", "sre", "infrastructure", "cloud", "platform"]):
                dept = "Infrastructure"
            elif any(w in title_lower for w in ["security"]):
                dept = "Security"
            elif any(w in title_lower for w in ["hr", "human", "people"]):
                dept = "People"
            elif any(w in title_lower for w in ["finance", "operations"]):
                dept = "Operations"

            # Check if it's AI-related
            is_ai = any(w in title_lower for w in [
                "ai", "ml", "machine learning", "data scien", "deep learning",
                "nlp", "computer vision", "generative",
            ])

            jobs.append({
                "title": title,
                "department": dept,
                "is_ai_related": is_ai,
            })

    return jobs[:25]  # Cap at 25 jobs


def _clean_html(text: str) -> str:
    """Strip HTML to plain text for job extraction."""
    clean = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
    clean = re.sub(r'<style[^>]*>.*?</style>', '', clean, flags=re.DOTALL)
    clean = re.sub(r'<[^>]+>', '\n', clean)
    clean = re.sub(r'\n{3,}', '\n\n', clean)
    clean = re.sub(r'[ \t]+', ' ', clean)
    return clean


def _build_careers_result(jobs: list[dict], url: str) -> dict:
    """Build a careers result dict from extracted jobs."""
    ai_jobs = [j for j in jobs if j["is_ai_related"]]
    depts: dict[str, int] = {}
    for j in jobs:
        depts[j["department"]] = depts.get(j["department"], 0) + 1
    return {
        "found": True,
        "careers_url": url,
        "total_openings": len(jobs),
        "ai_ml_openings": len(ai_jobs),
        "departments": depts,
        "sample_roles": [j["title"] for j in jobs[:12]],
        "ai_roles": [j["title"] for j in ai_jobs[:8]],
    }


async def _try_url(client: httpx.AsyncClient, url: str, company_name: str, require_jobs: bool = True) -> dict | None:
    """Try to scrape a URL for careers content. Returns result dict or None."""
    try:
        resp = await client.get(
            url,
            follow_redirects=True,
            timeout=15.0,
            headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"},
        )
        if resp.status_code != 200:
            return None
        text = resp.text
        text_lower = text.lower()

        # Check if page has careers-related content
        careers_keywords = ["career", "job opening", "open position", "we're hiring", "join our team", "apply now"]
        if not any(kw in text_lower for kw in careers_keywords):
            return None

        # IMPORTANT: Validate this page actually belongs to the target company.
        # Without this, we get false positives from platform marketing pages
        # (e.g., BambooHR testimonials, Greenhouse homepage).
        company_lower = company_name.lower()
        company_words = [w for w in company_lower.split() if len(w) > 2]
        page_mentions_company = (
            company_lower in text_lower
            or (company_words and sum(1 for w in company_words if w in text_lower) >= len(company_words) * 0.5)
        )
        # Also check if the URL itself contains the company name
        url_lower = url.lower()
        url_has_company = any(w in url_lower for w in company_words) if company_words else company_lower.replace(" ", "") in url_lower

        if not page_mentions_company and not url_has_company:
            logger.debug(f"  Skipping {url} — page doesn't mention {company_name}")
            return None

        clean_text = _clean_html(text)
        jobs = extract_jobs_from_text(clean_text, company_name)

        if not jobs:
            return None

        return _build_careers_result(jobs, url)
    except Exception as e:
        logger.debug(f"  Failed {url}: {e}")
        return None


async def scrape_careers_page(client: httpx.AsyncClient, website: str, company_name: str, tavily_key: str = "") -> dict:
    """Try to find and scrape a company's careers page.

    Strategy:
      1. Try common /careers paths on the company website
      2. Try jobs.{domain} subdomain
      3. Try Greenhouse / Lever / Ashby job boards
      4. Fallback: Tavily search for "{company} careers jobs"
    """
    if not website or "stackoverflow.com" in website or "bakersfield.com" in website:
        # Skip obviously wrong websites, but still try job boards + Tavily
        pass
    else:
        # ── Strategy 1: Direct paths on company website ─────────────────────
        parsed = urlparse(website)
        base_url = f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme else f"https://{parsed.netloc or website}"

        for path in CAREERS_PATHS:
            result = await _try_url(client, f"{base_url}{path}", company_name)
            if result and result.get("total_openings", 0) > 0:
                return result

        # ── Strategy 2: jobs.{domain} subdomain ────────────────────────────
        domain = parsed.netloc.replace("www.", "")
        jobs_subdomain = f"https://jobs.{domain}"
        result = await _try_url(client, jobs_subdomain, company_name)
        if result and result.get("total_openings", 0) > 0:
            return result

    # ── Strategy 3: Job board platforms ────────────────────────────────────
    slugs = [
        company_name.lower().replace(" ", ""),
        company_name.lower().replace(" ", "-"),
        company_name.lower().replace(" ", "").replace(".", ""),
    ]
    # Add first-word-only slug for multi-word names
    if " " in company_name:
        slugs.append(company_name.split()[0].lower())

    job_board_urls = []
    for slug in slugs:
        job_board_urls.extend([
            f"https://boards.greenhouse.io/{slug}",
            f"https://jobs.lever.co/{slug}",
            f"https://jobs.ashbyhq.com/{slug}",
            f"https://apply.workable.com/{slug}",
            f"https://{slug}.bamboohr.com/careers",
        ])

    for url in job_board_urls:
        result = await _try_url(client, url, company_name)
        if result and result.get("total_openings", 0) > 0:
            return result

    # ── Strategy 4: Tavily search for company careers page URL ─────────
    if tavily_key:
        try:
            # Search specifically for the company's own careers page
            resp = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": tavily_key,
                    "query": f'"{company_name}" careers page jobs hiring',
                    "search_depth": "basic",
                    "max_results": 5,
                },
                timeout=15.0,
            )
            data = resp.json()
            for r in data.get("results", []):
                url = r.get("url", "")
                content = r.get("content", "").lower()
                # Only follow URLs that look like actual careers pages
                # AND whose content mentions the company (not just any careers page)
                company_in_content = company_name.lower() in content
                is_careers_url = any(kw in url.lower() for kw in ["career", "jobs", "hiring", "lever.co", "greenhouse.io", "ashby", "workable"])
                # Exclude job aggregator sites (LinkedIn, Indeed, Glassdoor) — these are
                # generic and match many unrelated companies
                is_aggregator = any(site in url.lower() for site in ["linkedin.com", "indeed.com", "glassdoor.com", "ziprecruiter.com", "monster.com"])

                if is_careers_url and company_in_content and not is_aggregator:
                    result = await _try_url(client, url, company_name)
                    if result and result.get("total_openings", 0) > 0:
                        return result
        except Exception as e:
            logger.debug(f"  Tavily careers search failed: {e}")

    return {"found": False, "reason": "no_careers_page_found"}


# ── Main Pipeline ─────────────────────────────────────────────────────────────

async def enrich_company(client: httpx.AsyncClient, company: dict, tavily_key: str = "") -> dict:
    """Run GitHub + careers enrichment for a single company."""
    name = company["name"]
    website = company.get("website", "")

    logger.info(f"  GitHub search...")
    github_data = await enrich_github(client, name)
    if github_data.get("found"):
        logger.info(f"  → GitHub: {github_data['org_login']} — {github_data.get('total_public_repos', 0)} repos, {github_data.get('total_stars', 0)} stars")
    else:
        logger.info(f"  → GitHub: not found ({github_data.get('reason', 'unknown')})")

    logger.info(f"  Careers page scrape ({website})...")
    careers_data = await scrape_careers_page(client, website, name, tavily_key=tavily_key)
    if careers_data.get("found"):
        logger.info(f"  → Careers: {careers_data['total_openings']} openings ({careers_data['ai_ml_openings']} AI/ML) at {careers_data['careers_url']}")
    else:
        logger.info(f"  → Careers: not found ({careers_data.get('reason', 'unknown')})")

    return {
        "github": github_data,
        "careers": careers_data,
    }


async def main():
    # Load portfolio
    json_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "public", "portfolio_scores.json")
    json_path = os.path.normpath(json_path)
    with open(json_path) as f:
        portfolio = json.load(f)

    # Filter / flags
    target = None
    dry_run = False
    for arg in sys.argv[1:]:
        if arg == "--dry-run":
            dry_run = True
        else:
            target = arg

    if target:
        portfolio = [c for c in portfolio if c["name"].lower() == target.lower()]
        if not portfolio:
            logger.error(f"Company '{target}' not found")
            sys.exit(1)

    tavily_key = os.environ.get("TAVILY_API_KEY", "")
    if tavily_key:
        logger.info("Tavily API key found — will use for careers page discovery")

    logger.info(f"GitHub + Careers enrichment for {len(portfolio)} companies")

    if dry_run:
        for c in portfolio:
            print(f"  {c['name']:22s} | {c.get('website', 'N/A')}")
        return

    # Load existing evidence to merge into
    evidence_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "public", "portfolio_evidence.json")
    evidence_path = os.path.normpath(evidence_path)
    if os.path.exists(evidence_path):
        with open(evidence_path) as f:
            all_evidence = json.load(f)
    else:
        all_evidence = {}

    async with httpx.AsyncClient(timeout=20.0) as client:
        for i, company in enumerate(portfolio):
            name = company["name"]
            logger.info(f"[{i+1}/{len(portfolio)}] {name}")

            result = await enrich_company(client, company, tavily_key=tavily_key)

            # Merge into existing evidence — only overwrite if new data is better
            if name not in all_evidence:
                all_evidence[name] = {}

            # GitHub: only overwrite if new result found, or no previous data existed
            new_gh = result["github"]
            old_gh = all_evidence[name].get("github", {})
            if new_gh.get("found"):
                all_evidence[name]["github"] = new_gh
            elif not old_gh.get("found"):
                all_evidence[name]["github"] = new_gh  # both empty, use new
            else:
                logger.info(f"  Keeping existing GitHub data for {name}")

            # Careers: only overwrite if new result found, or no previous data existed
            new_cr = result["careers"]
            old_cr = all_evidence[name].get("careers", {})
            if new_cr.get("found"):
                all_evidence[name]["careers"] = new_cr
            elif not old_cr.get("found"):
                all_evidence[name]["careers"] = new_cr  # both empty, use new
            else:
                logger.info(f"  Keeping existing careers data for {name}")

            if i < len(portfolio) - 1:
                await asyncio.sleep(DELAY_BETWEEN_COMPANIES)

    # Save merged evidence
    with open(evidence_path, "w") as f:
        json.dump(all_evidence, f, indent=2)
    logger.info(f"\nSaved merged evidence to {evidence_path}")

    # Summary table
    print("\n" + "=" * 100)
    print("GITHUB + CAREERS ENRICHMENT SUMMARY")
    print("=" * 100)
    print(f"{'Company':<22} {'GitHub Org':<18} {'Repos':>6} {'Stars':>6} {'Langs':>6} {'Careers URL':<30} {'Jobs':>5} {'AI':>4}")
    print("-" * 100)
    for c in portfolio:
        name = c["name"]
        ev = all_evidence.get(name, {})
        gh = ev.get("github", {})
        cr = ev.get("careers", {})
        gh_org = gh.get("org_login", "—") if gh.get("found") else "—"
        repos = gh.get("total_public_repos", 0) if gh.get("found") else 0
        stars = gh.get("total_stars", 0) if gh.get("found") else 0
        langs = len(gh.get("primary_languages", [])) if gh.get("found") else 0
        cr_url = cr.get("careers_url", "—")[:28] if cr.get("found") else "—"
        jobs = cr.get("total_openings", 0) if cr.get("found") else 0
        ai_jobs = cr.get("ai_ml_openings", 0) if cr.get("found") else 0
        print(f"{name:<22} {gh_org:<18} {repos:>6} {stars:>6} {langs:>6} {cr_url:<30} {jobs:>5} {ai_jobs:>4}")


if __name__ == "__main__":
    asyncio.run(main())
