"""Second-pass enrichment for portfolio companies — targeted Tavily queries
to extract concrete, named evidence beyond the scoring pipeline's 8 queries.

Extracts:
  - Key AI initiatives & named products
  - Specific technology stack (named tools/platforms)
  - Named customers & case studies
  - Recent news, funding events, partnerships
  - Executive team & AI leadership
  - Job posting signals (AI/ML hiring activity)

Usage:
    python enrich_portfolio.py                      # Enrich all portfolio companies
    python enrich_portfolio.py "Cairn Applications"  # Enrich one company
    python enrich_portfolio.py --dry-run             # Preview queries without running

Requires env vars:
    TAVILY_API_KEY — Tavily API key
"""
import asyncio
import json
import os
import re
import sys
import time
import logging

import httpx

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-5s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

DELAY_BETWEEN_COMPANIES = 2.5  # seconds between companies to avoid rate limits

# ── Enrichment query templates ──────────────────────────────────────────────
# These are designed to NOT overlap with the scoring pipeline's 8 queries.
# Focus: concrete named entities and recent events.
ENRICHMENT_QUERIES = [
    # 1. Named AI initiatives, specific product features
    '"{company}" AI product features launch announcement OR "AI-powered" OR "machine learning" OR "intelligent"',
    # 2. Customer case studies, named customers, testimonials
    '"{company}" customer case study testimonial OR "uses {company}" OR "powered by {company}" OR "customer success"',
    # 3. Recent news, funding, acquisitions, partnerships (last 2 years)
    '"{company}" news 2024 2025 OR announcement OR partnership OR acquisition OR funding round OR product launch',
    # 4. Job postings — AI/ML hiring signals
    '"{company}" hiring jobs "machine learning" OR "AI engineer" OR "data scientist" OR "ML engineer" OR "AI product"',
    # 5. Executive team, leadership, CTO, CAIO, AI leadership
    '"{company}" CEO CTO leadership team OR "chief technology" OR "chief AI" OR "VP engineering" OR "head of AI"',
    # 6. Technology stack deep dive from job postings and tech blogs
    '"{company}" engineering blog OR tech stack OR "we use" OR "built with" OR Python OR React OR Kubernetes OR AWS',
]


async def tavily_search(client: httpx.AsyncClient, query: str, tavily_key: str) -> list[dict]:
    """Execute a single Tavily search."""
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
        )
        data = resp.json()
        if "error" in data:
            logger.warning(f"Tavily error: {data['error']}")
            return []
        results = []
        if data.get("answer"):
            results.append({"content": data["answer"], "url": None, "title": "AI Summary", "source": "tavily_answer"})
        for r in data.get("results", []):
            results.append({
                "content": r.get("content", ""),
                "url": r.get("url", ""),
                "title": r.get("title", ""),
                "source": "search_result",
            })
        return results
    except Exception as e:
        logger.warning(f"Search failed: {e}")
        return []


def extract_evidence(company_name: str, all_results: list[dict]) -> dict:
    """Extract structured evidence signals from enrichment search results."""
    combined_text = "\n\n".join(r.get("content", "") for r in all_results)
    text_lower = combined_text.lower()
    company_lower = company_name.lower()

    evidence = {
        "ai_initiatives": [],
        "named_products": [],
        "tech_stack": [],
        "named_customers": [],
        "recent_news": [],
        "executives": [],
        "hiring_signals": [],
        "key_evidence": [],  # Top evidence snippets for display
    }

    # ── AI Initiatives ──────────────────────────────────────────────────────
    ai_initiative_patterns = [
        (r'(?:launched?|introduced?|unveiled?|announced?|released?|built)\s+(?:an?\s+)?(?:AI|ML|machine learning|intelligent|smart)\s*[\w\s-]{5,60}', 'product_launch'),
        (r'(?:AI-powered|AI-driven|ML-based|intelligent)\s+[\w\s-]{5,40}', 'ai_feature'),
        (r'(?:generative AI|GenAI|LLM|copilot|assistant|chatbot)\s*[\w\s-]{3,30}', 'genai_feature'),
        (r'(?:predictive|recommendation|automation|optimization)\s+(?:engine|model|system|platform|tool)', 'ml_capability'),
    ]
    seen_initiatives = set()
    for pat, init_type in ai_initiative_patterns:
        for m in re.finditer(pat, combined_text, re.IGNORECASE):
            initiative = m.group(0).strip()
            # Only keep if it seems related to the company
            fingerprint = initiative.lower()[:40]
            if fingerprint not in seen_initiatives and len(initiative) > 10:
                seen_initiatives.add(fingerprint)
                evidence["ai_initiatives"].append({
                    "text": initiative,
                    "type": init_type,
                })
    evidence["ai_initiatives"] = evidence["ai_initiatives"][:8]

    # ── Named Products ──────────────────────────────────────────────────────
    product_patterns = [
        rf'{re.escape(company_name)}\s+([\w]+(?:\s+[\w]+)?)\s*(?:platform|product|solution|suite|module|tool|engine)',
        rf'([\w]+(?:\s+[\w]+)?)\s*(?:platform|product|solution|suite|module)\s*(?:by|from)\s*{re.escape(company_name)}',
    ]
    seen_products = set()
    for pat in product_patterns:
        for m in re.finditer(pat, combined_text, re.IGNORECASE):
            product = m.group(1).strip() if m.group(1) else m.group(0).strip()
            if product.lower() not in seen_products and len(product) > 2 and len(product) < 50:
                seen_products.add(product.lower())
                evidence["named_products"].append(product)
    evidence["named_products"] = evidence["named_products"][:6]

    # ── Tech Stack (specific named technologies) ────────────────────────────
    tech_map = {
        # Cloud
        'AWS': ['aws', 'amazon web services', 'ec2', 's3 bucket', 'lambda'],
        'Azure': ['azure', 'microsoft cloud'],
        'GCP': ['google cloud', 'gcp', 'bigquery'],
        # Containers & orchestration
        'Kubernetes': ['kubernetes', 'k8s', 'eks', 'aks', 'gke'],
        'Docker': ['docker', 'containerized'],
        # Languages & frameworks
        'Python': ['python', 'django', 'fastapi', 'flask'],
        'TypeScript': ['typescript', 'nextjs', 'next.js'],
        'React': ['react', 'react.js', 'reactjs'],
        'Node.js': ['node.js', 'nodejs', 'express.js'],
        'Java': ['java ', 'spring boot', 'jvm'],
        '.NET': ['.net', 'c#', 'asp.net'],
        'Go': ['golang', 'go language'],
        # Data
        'PostgreSQL': ['postgresql', 'postgres'],
        'MongoDB': ['mongodb', 'mongo'],
        'Redis': ['redis'],
        'Elasticsearch': ['elasticsearch', 'elastic search', 'opensearch'],
        'Snowflake': ['snowflake'],
        'Databricks': ['databricks'],
        # AI/ML
        'TensorFlow': ['tensorflow'],
        'PyTorch': ['pytorch'],
        'OpenAI': ['openai', 'gpt-4', 'gpt-3', 'chatgpt'],
        'Anthropic': ['anthropic', 'claude'],
        'Hugging Face': ['hugging face', 'huggingface'],
        # DevOps
        'Terraform': ['terraform'],
        'GitHub Actions': ['github actions'],
        'Jenkins': ['jenkins'],
        'Datadog': ['datadog'],
        # Other
        'Salesforce': ['salesforce', 'sfdc'],
        'Stripe': ['stripe'],
        'Twilio': ['twilio'],
        'Segment': ['segment'],
    }
    for tech, keywords in tech_map.items():
        if any(kw in text_lower for kw in keywords):
            evidence["tech_stack"].append(tech)

    # ── Named Customers ─────────────────────────────────────────────────────
    customer_patterns = [
        r'(?:customers?\s+(?:include|like|such as)|trusted by|used by|works? with|serves?|chosen by)\s+([\w\s,&]+?)(?:\.|,\s*and|\band\b)',
        r'([\w\s]+?)\s+(?:uses?|chose|selected|implemented|deployed|partnered with)\s+' + re.escape(company_name),
    ]
    seen_customers = set()
    for pat in customer_patterns:
        for m in re.finditer(pat, combined_text, re.IGNORECASE):
            raw = m.group(1).strip()
            # Split by comma or "and"
            for name in re.split(r',\s*|\s+and\s+', raw):
                name = name.strip()
                if 2 < len(name) < 40 and name.lower() not in seen_customers and name[0].isupper():
                    seen_customers.add(name.lower())
                    evidence["named_customers"].append(name)
    evidence["named_customers"] = evidence["named_customers"][:8]

    # ── Recent News / Events ────────────────────────────────────────────────
    news_patterns = [
        r'(?:in\s+(?:20\d\d|January|February|March|April|May|June|July|August|September|October|November|December)[\w\s,]*?),?\s*' + re.escape(company_name) + r'\s+([\w\s,]+?)(?:\.|$)',
        re.escape(company_name) + r'\s+(?:announced?|launched?|raised?|acquired?|partnered?|released?|expanded?)\s+([\w\s,]+?)(?:\.|$)',
    ]
    seen_news = set()
    for pat in news_patterns:
        for m in re.finditer(pat, combined_text, re.IGNORECASE):
            snippet = m.group(0).strip()[:150]
            fp = snippet.lower()[:60]
            if fp not in seen_news and len(snippet) > 20:
                seen_news.add(fp)
                evidence["recent_news"].append(snippet)
    evidence["recent_news"] = evidence["recent_news"][:6]

    # ── Executives ──────────────────────────────────────────────────────────
    exec_patterns = [
        r'(?:CEO|CTO|CFO|COO|CAIO|Chief\s+(?:Technology|Executive|AI|Data|Operating|Financial)\s+Officer|VP\s+(?:of\s+)?Engineering|Head of AI|President)\s*(?:,?\s*)([\w\s.]+?)(?:,|\.|said|stated|noted|explained|at\s)',
        r'([\w\s.]+?),?\s*(?:CEO|CTO|CFO|COO|CAIO|Chief\s+(?:Technology|Executive|AI|Data)\s+Officer|VP\s+Engineering|Head of AI)\s*(?:of|at)\s*' + re.escape(company_name),
    ]
    seen_execs = set()
    for pat in exec_patterns:
        for m in re.finditer(pat, combined_text, re.IGNORECASE):
            name = m.group(1).strip() if m.lastindex else m.group(0).strip()
            name = re.sub(r'^(CEO|CTO|CFO|COO|CAIO|Chief\s+\w+\s+Officer)\s*,?\s*', '', name).strip()
            if 3 < len(name) < 40 and name[0].isupper() and name.lower() not in seen_execs:
                seen_execs.add(name.lower())
                role_match = re.search(r'(CEO|CTO|CFO|COO|CAIO|Chief\s+\w+\s+Officer|VP\s+\w+|Head of \w+)', m.group(0))
                role = role_match.group(0) if role_match else "Executive"
                evidence["executives"].append({"name": name, "role": role})
    evidence["executives"] = evidence["executives"][:5]

    # ── Hiring Signals ──────────────────────────────────────────────────────
    hiring_roles = {
        'AI/ML Engineer': ['machine learning engineer', 'ml engineer', 'ai engineer'],
        'Data Scientist': ['data scientist', 'senior data scientist'],
        'AI Product Manager': ['ai product manager', 'ml product manager'],
        'Data Engineer': ['data engineer', 'data engineering'],
        'NLP Engineer': ['nlp engineer', 'natural language'],
        'Computer Vision': ['computer vision engineer', 'cv engineer'],
        'MLOps': ['mlops', 'ml ops', 'ml infrastructure'],
        'AI Researcher': ['ai researcher', 'research scientist'],
        'Full Stack': ['full stack', 'full-stack'],
        'DevOps/SRE': ['devops', 'site reliability', 'sre'],
        'Backend Engineer': ['backend engineer', 'backend developer'],
        'Frontend Engineer': ['frontend engineer', 'frontend developer'],
    }
    for role, keywords in hiring_roles.items():
        if any(kw in text_lower for kw in keywords):
            evidence["hiring_signals"].append(role)

    # ── Key Evidence Snippets (best snippets for display) ───────────────────
    # Pick the most informative result snippets that mention the company
    for r in all_results:
        content = r.get("content", "").strip()
        if not content or len(content) < 80:
            continue
        if company_lower in content.lower():
            # Truncate to ~200 chars at a sentence boundary
            snippet = content[:250]
            last_period = snippet.rfind('.')
            if last_period > 100:
                snippet = snippet[:last_period + 1]
            source_url = r.get("url", "")
            source_name = ""
            if source_url:
                try:
                    from urllib.parse import urlparse
                    source_name = urlparse(source_url).netloc.replace("www.", "")
                except:
                    source_name = source_url[:40]
            evidence["key_evidence"].append({
                "text": snippet,
                "source": source_name,
                "url": source_url,
            })
    evidence["key_evidence"] = evidence["key_evidence"][:8]

    # Summary stats
    evidence["enrichment_stats"] = {
        "total_results": len(all_results),
        "total_text_chars": len(combined_text),
        "ai_initiatives_found": len(evidence["ai_initiatives"]),
        "tech_stack_signals": len(evidence["tech_stack"]),
        "customers_found": len(evidence["named_customers"]),
        "news_events": len(evidence["recent_news"]),
        "executives_found": len(evidence["executives"]),
        "hiring_roles_detected": len(evidence["hiring_signals"]),
        "evidence_snippets": len(evidence["key_evidence"]),
    }

    return evidence


async def enrich_company(
    client: httpx.AsyncClient,
    company: dict,
    tavily_key: str,
) -> dict:
    """Run enrichment queries for a single company and extract evidence."""
    name = company["name"]
    vertical = company.get("vertical", "")
    hint = f" {vertical}" if vertical else ""

    queries = [q.format(company=name + hint) for q in ENRICHMENT_QUERIES]

    # Run all 6 queries concurrently
    tasks = [tavily_search(client, q, tavily_key) for q in queries]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    all_results = []
    for batch in results:
        if isinstance(batch, Exception):
            logger.warning(f"  Query failed: {batch}")
            continue
        all_results.extend(batch)

    logger.info(f"  {name}: {len(all_results)} results from {len(queries)} enrichment queries")

    # Extract structured evidence
    evidence = extract_evidence(name, all_results)
    return evidence


async def main():
    tavily_key = os.environ.get("TAVILY_API_KEY")
    if not tavily_key:
        logger.error("TAVILY_API_KEY not set")
        sys.exit(1)

    # Load portfolio from JSON
    json_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "public", "portfolio_scores.json")
    json_path = os.path.normpath(json_path)
    with open(json_path) as f:
        portfolio = json.load(f)

    # Filter to specific company if provided
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
            logger.error(f"Company '{target}' not found in portfolio")
            sys.exit(1)

    logger.info(f"Enriching {len(portfolio)} portfolio companies")
    if dry_run:
        logger.info("[DRY RUN] Will show queries but not execute them")
        for c in portfolio:
            hint = f" {c.get('vertical', '')}" if c.get('vertical') else ""
            for q in ENRICHMENT_QUERIES:
                print(f"  {c['name']}: {q.format(company=c['name'] + hint)}")
        return

    all_evidence = {}
    async with httpx.AsyncClient(timeout=30.0) as client:
        for i, company in enumerate(portfolio):
            name = company["name"]
            logger.info(f"[{i+1}/{len(portfolio)}] Enriching: {name}")

            evidence = await enrich_company(client, company, tavily_key)
            all_evidence[name] = evidence

            stats = evidence["enrichment_stats"]
            logger.info(
                f"  → {stats['ai_initiatives_found']} AI initiatives, "
                f"{stats['tech_stack_signals']} tech signals, "
                f"{stats['customers_found']} customers, "
                f"{stats['news_events']} news events, "
                f"{stats['executives_found']} executives, "
                f"{stats['hiring_roles_detected']} hiring roles, "
                f"{stats['evidence_snippets']} evidence snippets"
            )

            if i < len(portfolio) - 1:
                logger.info(f"  Waiting {DELAY_BETWEEN_COMPANIES}s...")
                await asyncio.sleep(DELAY_BETWEEN_COMPANIES)

    # Save enrichment data
    output_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "public", "portfolio_evidence.json")
    output_path = os.path.normpath(output_path)
    with open(output_path, "w") as f:
        json.dump(all_evidence, f, indent=2)
    logger.info(f"\nSaved enrichment data to {output_path}")

    # Print summary
    print("\n" + "="*80)
    print("ENRICHMENT SUMMARY")
    print("="*80)
    print(f"{'Company':<22} {'AI Init':>8} {'Tech':>6} {'Cust':>6} {'News':>6} {'Execs':>6} {'Hiring':>7} {'Evidence':>9}")
    print("-"*80)
    for name, ev in all_evidence.items():
        s = ev["enrichment_stats"]
        print(
            f"{name:<22} {s['ai_initiatives_found']:>8} {s['tech_stack_signals']:>6} "
            f"{s['customers_found']:>6} {s['news_events']:>6} {s['executives_found']:>6} "
            f"{s['hiring_roles_detected']:>7} {s['evidence_snippets']:>9}"
        )


if __name__ == "__main__":
    asyncio.run(main())
