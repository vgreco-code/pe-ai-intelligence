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


def _is_valid_person_name(name: str, company_name: str) -> bool:
    """Strict validation that a string is actually a person's name, not a company/role/artifact."""
    name_words = name.split()
    if len(name_words) < 2 or len(name_words) > 4:
        return False

    # Every word must start with uppercase (except short connectors like "de", "van")
    for w in name_words:
        if len(w) <= 2:
            continue
        if not w[0].isupper():
            return False

    # Blocklist: prepositions, articles, common junk as first word
    first_word_blocklist = {
        'is', 'at', 'of', 'the', 'and', 'for', 'in', 'as', 'to', 'by',
        'view', 'click', 'see', 'more', 'read', 'about', 'our', 'this',
        'new', 'top', 'best', 'all', 'get', 'how',
    }
    if name_words[0].lower() in first_word_blocklist:
        return False

    # Blocklist: any word that's a company suffix or business term
    business_words = {
        'inc', 'llc', 'corp', 'ltd', 'consulting', 'solutions', 'technologies',
        'technology', 'software', 'systems', 'services', 'group', 'partners',
        'capital', 'ventures', 'financial', 'industrial', 'healthcare',
        'robotics', 'foundry', 'analytics', 'labs', 'global', 'international',
        'executive', 'development', 'corporate', 'architect', 'engineer',
        'engineering', 'scientist', 'science', 'manager', 'director', 'lead',
        'senior', 'junior', 'principal', 'staff', 'post', 'power', 'energy',
        'data', 'cloud', 'platform', 'product', 'marketing', 'sales',
        'operations', 'research', 'design', 'infrastructure', 'security',
    }
    if any(w.lower() in business_words for w in name_words):
        return False

    # Must not contain digits or special chars
    if re.search(r'[\d\n\r@#$%&*(){}[\]]', name):
        return False

    # Must not be the company name itself or a close variant
    company_words = set(w.lower() for w in company_name.split() if len(w) > 2)
    name_lower_words = set(w.lower() for w in name_words if len(w) > 2)
    if company_words and name_lower_words.issubset(company_words):
        return False

    # Known non-person patterns (product names, LinkedIn artifacts)
    known_non_persons = [
        'view post', 'read more', 'see all', 'learn more', 'sign in',
        'palantir', 'doordash', 'healthcare', 'bamboo',
    ]
    name_lower = name.lower()
    if any(bad in name_lower for bad in known_non_persons):
        return False

    # Each name word should look like a human name (2+ chars, no all-caps unless 2-3 letter initials)
    for w in name_words:
        if len(w) > 3 and w.isupper():
            return False  # Likely an acronym, not a name

    return True


def _result_mentions_company_strict(result: dict, company_name: str) -> bool:
    """Check if a search result is specifically about the target company.

    Stricter than the portfolio enrichment version: requires exact company name
    match to avoid DoorDash→Dash, Palantir Foundry→Thought Foundry contamination.
    """
    company_lower = company_name.lower().strip()
    # For multi-word company names, require the full phrase
    # For single-word names, require word-boundary match to avoid substring false positives
    text = f"{result.get('title', '')} {result.get('content', '')}".lower()
    url = result.get("url", "").lower()

    if len(company_lower.split()) > 1:
        # Multi-word: require exact phrase
        return company_lower in text or company_lower.replace(" ", "") in url
    else:
        # Single-word: require word boundary match to prevent "Dash" matching "DoorDash"
        pattern = r'\b' + re.escape(company_lower) + r'\b'
        return bool(re.search(pattern, text))


def _extract_people_from_result(result: dict, company_name: str) -> list[dict]:
    """Extract person-role pairs from a SINGLE search result that is confirmed
    to be about the target company.

    Key difference from old approach: we require BOTH that the result is about
    the company AND that the person-role extraction is proximate to company mentions.
    """
    people = []
    company_lower = company_name.lower()

    title = result.get("title", "")
    content = result.get("content", "")
    url = result.get("url", "").lower()
    text = f"{title}\n{content}"

    # Is this a LinkedIn profile page for someone AT this company?
    is_linkedin_profile = "linkedin.com/in/" in url
    # Is this a LinkedIn company page?
    is_linkedin_company = "linkedin.com/company/" in url

    role_keywords = (
        r'(?:CTO|CEO|CFO|COO|CAIO|VP|Vice President|Director|Head|Lead|'
        r'Chief\s+(?:Technology|AI|Data|Information|Engineering)\s+Officer|'
        r'(?:Senior\s+)?(?:Software|Data|ML|AI|Platform|Backend|Frontend|Full.Stack)\s+'
        r'(?:Engineer|Developer|Scientist|Architect|Manager|Lead)|'
        r'(?:Engineering|Product|Data|AI|ML)\s+(?:Manager|Director|Lead|Head)|'
        r'Scrum\s+Master|Tech\s+Lead|Staff\s+Engineer|Principal\s+Engineer|'
        r'Data\s+(?:Analyst|Architect|Engineer)|Solutions?\s+Architect)'
    )

    # Primary pattern: "Name - Role" (LinkedIn title format)
    pattern = r'([A-Z][a-z]+(?:\s+[A-Z]\.?\s*)?[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*[-–|]\s*(' + role_keywords + r'[^|\n]{0,60})'

    for m in re.finditer(pattern, text, re.IGNORECASE):
        name = m.group(1).strip(' -–|,')
        role = m.group(2).strip(' -–|,')[:80]

        # Clean role: remove "at Company" suffix
        role = re.sub(r'\s+at\s+.*$', '', role, flags=re.IGNORECASE)
        role = re.sub(r'\s*\|.*$', '', role)
        role = re.sub(r'\s*-\s*LinkedIn.*$', '', role, flags=re.IGNORECASE)

        if not _is_valid_person_name(name, company_name):
            continue

        # CRITICAL: Verify this person is associated with THIS company
        # For LinkedIn profiles, check if the company is mentioned near the person's entry
        match_pos = m.start()
        context_window = text[max(0, match_pos - 150):match_pos + len(m.group(0)) + 150].lower()

        # The company name must appear in proximity to this person
        if len(company_lower.split()) > 1:
            company_in_context = company_lower in context_window
        else:
            company_in_context = bool(re.search(r'\b' + re.escape(company_lower) + r'\b', context_window))

        # For LinkedIn profile pages, also accept if the URL or page title has the company
        if is_linkedin_profile:
            company_in_context = company_in_context or (
                company_lower in title.lower()
            )

        if not company_in_context:
            continue

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
    """Extract talent signals from search results with strict company validation.

    Key principles:
    1. Only process results that are specifically about the target company
    2. Require person-company proximity (name near company mention)
    3. Strict person-name validation to reject companies/roles/artifacts as names
    4. Only count skills from company-relevant results
    """
    company_lower = company_name.lower()

    all_people = []
    all_answers = []
    relevant_results = []
    total_results = 0

    for qr in query_results:
        answer = qr.get("answer", "")
        results = qr.get("results", [])
        all_answers.append(answer)
        total_results += len(results)

        # Filter results: only process ones that are clearly about this company
        for r in results:
            if _result_mentions_company_strict(r, company_name):
                relevant_results.append(r)
                all_people.extend(_extract_people_from_result(r, company_name))

        # Extract from Tavily answer too (with answer wrapped as a pseudo-result)
        if answer:
            answer_result = {"title": "", "content": answer, "url": ""}
            if _result_mentions_company_strict(answer_result, company_name):
                all_people.extend(_extract_people_from_result(answer_result, company_name))

    logger.info(f"  {company_name}: {len(relevant_results)}/{total_results} results were company-relevant")

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

    # LinkedIn profile URLs found (only from relevant results)
    linkedin_urls = set()
    for r in relevant_results:
        url = r.get("url", "")
        if "linkedin.com/in/" in url:
            linkedin_urls.add(url)

    # Team size estimate (only from relevant results)
    size_est = _estimate_team_size(all_answers, relevant_results, company_name)

    # Aggregate skills/tech mentions ONLY from company-relevant results
    tech_skills = set()
    skill_keywords = {
        'python', 'java', 'javascript', 'typescript', 'react', 'node.js',
        'aws', 'azure', 'gcp', 'kubernetes', 'docker', 'terraform',
        'tensorflow', 'pytorch', 'machine learning', 'deep learning',
        'sql', 'postgresql', 'mongodb', 'redis', 'elasticsearch',
        'spark', 'hadoop', 'snowflake', 'databricks', 'airflow',
        'ci/cd', 'jenkins', 'github actions', 'agile', 'scrum',
    }
    relevant_text = " ".join(r.get("content", "").lower() for r in relevant_results)
    for skill in skill_keywords:
        if skill in relevant_text:
            tech_skills.add(skill)

    return {
        "found": len(unique_people) > 0,
        "total_profiles_found": len(unique_people),
        "linkedin_profiles_discovered": len(linkedin_urls),
        "relevant_results": len(relevant_results),
        "total_results": total_results,
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
