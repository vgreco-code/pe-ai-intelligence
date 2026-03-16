"""Fourth-pass enrichment: LinkedIn talent analysis via Tavily search.

Enriches portfolio companies with:
  1. Tech leadership identification — CTO, VP Eng, Head of AI, etc.
  2. Engineering team composition — languages, specialties, seniority
  3. AI/ML talent signals — data scientists, ML engineers, AI researchers
  4. Team size & growth indicators — headcount estimates, hiring velocity

Uses Tavily search to discover LinkedIn profiles and team pages.
Does NOT scrape LinkedIn directly — all data comes from Tavily's index.

Usage:
    python enrich_talent.py                      # Enrich all companies
    python enrich_talent.py "Cairn Applications"  # One company
    python enrich_talent.py --dry-run             # Preview queries

Requires: TAVILY_API_KEY
"""
import asyncio
import json
import os
import re
import sys
import logging

import httpx

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-5s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

DELAY_BETWEEN_COMPANIES = 2.5


# ── Talent Queries ──────────────────────────────────────────────────────────
# 4 targeted queries per company to map technical talent from LinkedIn

TALENT_QUERIES = [
    # Q1: Tech leadership — CTO, VP Eng, Head of AI
    '"{company}" CTO OR "VP of engineering" OR "head of AI" OR "chief technology" OR "VP engineering" OR "head of data" site:linkedin.com',
    # Q2: AI/ML talent — data scientists, ML engineers
    '"{company}" "machine learning" OR "data scientist" OR "AI engineer" OR "ML engineer" OR "deep learning" OR "NLP" site:linkedin.com',
    # Q3: Engineering team breadth — developers, architects, SREs
    '"{company}" "software engineer" OR "senior engineer" OR "architect" OR "DevOps" OR "SRE" OR "platform engineer" site:linkedin.com',
    # Q4: Team size & company context (not limited to LinkedIn)
    '"{company}" engineering team size employees technology department OR "tech team" OR "development team"',
]


async def tavily_search(client: httpx.AsyncClient, query: str, tavily_key: str) -> dict:
    """Execute a Tavily search and return structured results."""
    try:
        resp = await client.post(
            "https://api.tavily.com/search",
            json={
                "api_key": tavily_key,
                "query": query,
                "search_depth": "advanced",
                "max_results": 5,
                "include_answer": True,
            },
            timeout=20.0,
        )
        data = resp.json()
        if "error" in data:
            logger.warning(f"Tavily error: {data['error']}")
            return {"answer": "", "results": []}
        return {
            "answer": data.get("answer", ""),
            "results": data.get("results", []),
        }
    except Exception as e:
        logger.warning(f"Search failed: {e}")
        return {"answer": "", "results": []}


def _extract_people(text: str, company_name: str) -> list[dict]:
    """Extract person-role pairs from text that mention the target company."""
    people = []
    seen = set()
    company_lower = company_name.lower()

    # Pattern: "Name - Title at Company" or "Name | Title | Company"
    # Also: "Name, Title at Company"
    role_keywords = (
        r'(?:CTO|CEO|CFO|COO|CAIO|VP|Vice President|Director|Head|Lead|'
        r'Chief\s+(?:Technology|AI|Data|Information|Engineering)\s+Officer|'
        r'(?:Senior\s+)?(?:Software|Data|ML|AI|Platform|Backend|Frontend|Full.Stack)\s+'
        r'(?:Engineer|Developer|Scientist|Architect|Manager|Lead)|'
        r'(?:Engineering|Product|Data|AI|ML)\s+(?:Manager|Director|Lead|Head)|'
        r'Scrum\s+Master|Tech\s+Lead|Staff\s+Engineer|Principal\s+Engineer|'
        r'Data\s+(?:Analyst|Architect|Engineer)|Solutions?\s+Architect)'
    )

    # "Name - Role" or "Name, Role" patterns from LinkedIn results
    patterns = [
        # "Name - Role at/| Company"  (LinkedIn title format)
        r'([A-Z][a-z]+(?:\s+[A-Z]\.?\s*)?[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*[-–|]\s*(' + role_keywords + r'[^|\n]{0,60})',
        # "Role: Name" patterns
        r'(' + role_keywords + r')\s+(?:is\s+)?([A-Z][a-z]+(?:\s+[A-Z]\.?\s*)?[A-Z][a-z]+)',
    ]

    text_lower = text.lower()
    # Only extract from text that mentions the company
    if company_lower not in text_lower:
        # Check partial matches
        words = [w for w in company_lower.split() if len(w) > 2]
        if not words or sum(1 for w in words if w in text_lower) < len(words) * 0.5:
            return []

    for pat in patterns:
        for m in re.finditer(pat, text, re.IGNORECASE):
            groups = m.groups()
            if len(groups) >= 2:
                # Determine which group is the name vs role
                g1, g2 = groups[0].strip(), groups[1].strip()
                # If first group looks like a role keyword, swap
                if re.match(role_keywords, g1, re.IGNORECASE):
                    name, role = g2, g1
                else:
                    name, role = g1, g2

                # Validate name
                name = name.strip(' -–|,')
                name_words = name.split()
                if len(name_words) < 2 or len(name_words) > 4:
                    continue
                if not all(w[0].isupper() or len(w) <= 2 for w in name_words):
                    continue
                if name_words[0].lower() in {'is', 'at', 'of', 'the', 'and', 'for', 'in', 'as'}:
                    continue
                if re.search(r'[\d\n\r]', name):
                    continue

                # Clean role
                role = role.strip(' -–|,')[:80]
                role = re.sub(r'\s+at\s+.*$', '', role, flags=re.IGNORECASE)
                role = re.sub(r'\s*\|.*$', '', role)

                fingerprint = name.lower()
                if fingerprint not in seen:
                    seen.add(fingerprint)

                    # Classify the role
                    role_lower = role.lower()
                    if any(kw in role_lower for kw in ['cto', 'chief technology', 'vp of eng', 'vp engineering', 'head of eng']):
                        category = 'leadership'
                    elif any(kw in role_lower for kw in ['ai', 'ml', 'machine learning', 'data scien', 'nlp', 'deep learning']):
                        category = 'ai_ml'
                    elif any(kw in role_lower for kw in ['architect', 'principal', 'staff', 'lead']):
                        category = 'senior_eng'
                    elif any(kw in role_lower for kw in ['engineer', 'developer', 'devops', 'sre']):
                        category = 'engineering'
                    elif any(kw in role_lower for kw in ['director', 'head', 'manager', 'vp']):
                        category = 'management'
                    else:
                        category = 'other'

                    people.append({
                        "name": name,
                        "role": role,
                        "category": category,
                    })

    return people


def _estimate_team_size(answers: list[str], results: list[dict], company_name: str) -> dict:
    """Estimate engineering team size from search results."""
    company_lower = company_name.lower()
    all_text = " ".join(answers) + " " + " ".join(r.get("content", "") for r in results)
    all_lower = all_text.lower()

    # Look for explicit size mentions
    size_patterns = [
        r'(\d+)[\s-]+(?:employees?|people|staff|team members?)',
        r'(?:team of|team size|headcount)\s*(?:of\s*)?(\d+)',
        r'(\d+)[\s-]+(?:engineers?|developers?)',
        r'(?:about|approximately|roughly|around)\s+(\d+)\s+(?:employees?|people|engineers?)',
    ]

    sizes = []
    for pat in size_patterns:
        for m in re.finditer(pat, all_lower):
            try:
                n = int(m.group(1))
                if 2 <= n <= 10000:  # reasonable range
                    sizes.append(n)
            except:
                pass

    # LinkedIn company page ranges
    linkedin_ranges = {
        '1-10': 5, '2-10': 5, '11-50': 30, '51-200': 100,
        '201-500': 300, '501-1000': 700, '1001-5000': 2000,
    }
    for rng, estimate in linkedin_ranges.items():
        if rng in all_text:
            sizes.append(estimate)

    result = {}
    if sizes:
        result["estimated_total_employees"] = max(sizes)
        # Rough engineering ratio for software companies: 30-50%
        result["estimated_eng_team"] = max(1, int(max(sizes) * 0.35))

    return result


def extract_talent_signals(company_name: str, query_results: list[dict]) -> dict:
    """Extract talent signals from search results."""
    company_lower = company_name.lower()

    all_people = []
    all_answers = []
    all_results = []

    for qr in query_results:
        answer = qr.get("answer", "")
        results = qr.get("results", [])
        all_answers.append(answer)
        all_results.extend(results)

        # Extract people from answer
        if answer:
            all_people.extend(_extract_people(answer, company_name))

        # Extract people from search results
        for r in results:
            content = r.get("content", "")
            title = r.get("title", "")
            combined = f"{title}\n{content}"
            all_people.extend(_extract_people(combined, company_name))

    # Deduplicate people by name
    seen_names = set()
    unique_people = []
    for p in all_people:
        if p["name"].lower() not in seen_names:
            seen_names.add(p["name"].lower())
            unique_people.append(p)

    # Categorize
    leadership = [p for p in unique_people if p["category"] == "leadership"]
    ai_ml = [p for p in unique_people if p["category"] == "ai_ml"]
    senior_eng = [p for p in unique_people if p["category"] == "senior_eng"]
    engineering = [p for p in unique_people if p["category"] == "engineering"]
    management = [p for p in unique_people if p["category"] == "management"]

    # LinkedIn profile URLs found
    linkedin_urls = set()
    for r in all_results:
        url = r.get("url", "")
        if "linkedin.com/in/" in url:
            linkedin_urls.add(url)

    # Team size estimate
    size_est = _estimate_team_size(all_answers, all_results, company_name)

    # Aggregate skills/tech mentions from profiles
    tech_skills = set()
    skill_keywords = {
        'python', 'java', 'javascript', 'typescript', 'react', 'node.js',
        'aws', 'azure', 'gcp', 'kubernetes', 'docker', 'terraform',
        'tensorflow', 'pytorch', 'machine learning', 'deep learning',
        'sql', 'postgresql', 'mongodb', 'redis', 'elasticsearch',
        'spark', 'hadoop', 'snowflake', 'databricks', 'airflow',
        'ci/cd', 'jenkins', 'github actions', 'agile', 'scrum',
    }
    all_text_lower = " ".join(all_answers).lower() + " " + " ".join(r.get("content", "").lower() for r in all_results)
    for skill in skill_keywords:
        if skill in all_text_lower:
            tech_skills.add(skill)

    return {
        "found": len(unique_people) > 0,
        "total_profiles_found": len(unique_people),
        "linkedin_profiles_discovered": len(linkedin_urls),
        "leadership": [{"name": p["name"], "role": p["role"]} for p in leadership[:5]],
        "ai_ml_talent": [{"name": p["name"], "role": p["role"]} for p in ai_ml[:8]],
        "senior_engineers": [{"name": p["name"], "role": p["role"]} for p in senior_eng[:8]],
        "engineering_team": [{"name": p["name"], "role": p["role"]} for p in engineering[:8]],
        "management": [{"name": p["name"], "role": p["role"]} for p in management[:5]],
        "team_skills": sorted(list(tech_skills)),
        **size_est,
        "talent_summary": {
            "has_cto": any("cto" in p["role"].lower() or "chief technology" in p["role"].lower() for p in unique_people),
            "has_vp_eng": any("vp" in p["role"].lower() and "eng" in p["role"].lower() for p in unique_people),
            "has_ai_leadership": any(
                p["category"] in ("leadership", "management") and
                any(kw in p["role"].lower() for kw in ["ai", "ml", "data", "machine learning"])
                for p in unique_people
            ),
            "ai_ml_headcount": len(ai_ml),
            "eng_headcount_discovered": len(engineering) + len(senior_eng),
            "leadership_headcount": len(leadership) + len(management),
            "total_discovered": len(unique_people),
        },
    }


async def enrich_company_talent(
    client: httpx.AsyncClient,
    company: dict,
    tavily_key: str,
) -> dict:
    """Run talent queries for a single company."""
    name = company["name"]
    vertical = company.get("vertical", "")
    hint = f" {vertical}" if vertical else ""

    queries = [q.format(company=name + hint) for q in TALENT_QUERIES]

    # Run all queries concurrently
    tasks = [tavily_search(client, q, tavily_key) for q in queries]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    query_results = []
    for r in results:
        if isinstance(r, Exception):
            logger.warning(f"  Query failed: {r}")
            query_results.append({"answer": "", "results": []})
        else:
            query_results.append(r)

    total_results = sum(len(qr.get("results", [])) for qr in query_results)
    logger.info(f"  {name}: {total_results} results from {len(queries)} talent queries")

    talent = extract_talent_signals(name, query_results)
    return talent


async def main():
    tavily_key = os.environ.get("TAVILY_API_KEY")
    if not tavily_key:
        logger.error("TAVILY_API_KEY not set")
        sys.exit(1)

    # Load portfolio
    json_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "public", "portfolio_scores.json")
    json_path = os.path.normpath(json_path)
    with open(json_path) as f:
        portfolio = json.load(f)

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

    logger.info(f"LinkedIn talent enrichment for {len(portfolio)} companies")

    if dry_run:
        for c in portfolio:
            hint = f" {c.get('vertical', '')}" if c.get('vertical') else ""
            for q in TALENT_QUERIES:
                print(f"  {c['name']}: {q.format(company=c['name'] + hint)}")
        return

    # Load existing evidence
    evidence_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "public", "portfolio_evidence.json")
    evidence_path = os.path.normpath(evidence_path)
    if os.path.exists(evidence_path):
        with open(evidence_path) as f:
            all_evidence = json.load(f)
    else:
        all_evidence = {}

    async with httpx.AsyncClient(timeout=30.0) as client:
        for i, company in enumerate(portfolio):
            name = company["name"]
            logger.info(f"[{i+1}/{len(portfolio)}] Talent analysis: {name}")

            talent = await enrich_company_talent(client, company, tavily_key)

            if name not in all_evidence:
                all_evidence[name] = {}
            all_evidence[name]["talent"] = talent

            summary = talent["talent_summary"]
            logger.info(
                f"  → {summary['total_discovered']} people found: "
                f"{summary['leadership_headcount']} leadership, "
                f"{summary['ai_ml_headcount']} AI/ML, "
                f"{summary['eng_headcount_discovered']} engineering"
            )
            if talent.get("estimated_total_employees"):
                logger.info(f"  → Est. {talent['estimated_total_employees']} total employees, ~{talent['estimated_eng_team']} engineering")

            if i < len(portfolio) - 1:
                await asyncio.sleep(DELAY_BETWEEN_COMPANIES)

    # Save
    with open(evidence_path, "w") as f:
        json.dump(all_evidence, f, indent=2)
    logger.info(f"\nSaved talent data to {evidence_path}")

    # Summary table
    print("\n" + "=" * 110)
    print("TALENT ENRICHMENT SUMMARY")
    print("=" * 110)
    print(f"{'Company':<22} {'People':>7} {'Leaders':>8} {'AI/ML':>6} {'Sr Eng':>7} {'Eng':>5} {'CTO':>4} {'VP Eng':>7} {'AI Lead':>8} {'Skills':>7}")
    print("-" * 110)
    for c in portfolio:
        name = c["name"]
        t = all_evidence.get(name, {}).get("talent", {})
        s = t.get("talent_summary", {})
        print(
            f"{name:<22} "
            f"{s.get('total_discovered', 0):>7} "
            f"{s.get('leadership_headcount', 0):>8} "
            f"{s.get('ai_ml_headcount', 0):>6} "
            f"{len(t.get('senior_engineers', [])):>7} "
            f"{len(t.get('engineering_team', [])):>5} "
            f"{'✓' if s.get('has_cto') else '—':>4} "
            f"{'✓' if s.get('has_vp_eng') else '—':>7} "
            f"{'✓' if s.get('has_ai_leadership') else '—':>8} "
            f"{len(t.get('team_skills', [])):>7}"
        )


if __name__ == "__main__":
    asyncio.run(main())
