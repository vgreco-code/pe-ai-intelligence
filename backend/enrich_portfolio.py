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


def _result_mentions_company(result: dict, company_name: str) -> bool:
    """Check if a search result actually mentions the target company."""
    content = (result.get("content", "") + " " + result.get("title", "")).lower()
    name_lower = company_name.lower()

    # Full name match
    if name_lower in content:
        return True
    # Match significant words (skip short words like "AI", "IT")
    words = [w for w in name_lower.split() if len(w) > 2]
    if words and sum(1 for w in words if w in content) >= len(words) * 0.5:
        return True
    return False


def extract_evidence(company_name: str, all_results: list[dict]) -> dict:
    """Extract structured evidence signals from enrichment search results.

    IMPORTANT: Only extracts signals from results that actually mention the
    target company, to prevent entity contamination from generic search results.
    """
    company_lower = company_name.lower()

    # ── Step 1: Split results into company-relevant vs generic ────────────
    relevant_results = []
    generic_results = []
    for r in all_results:
        if _result_mentions_company(r, company_name):
            relevant_results.append(r)
        else:
            generic_results.append(r)

    logger.info(
        f"  Evidence filter: {len(relevant_results)} relevant / "
        f"{len(generic_results)} generic of {len(all_results)} total results"
    )

    # Only use relevant results for extraction (except key_evidence which shows sources)
    relevant_text = "\n\n".join(r.get("content", "") for r in relevant_results)
    relevant_lower = relevant_text.lower()

    evidence = {
        "ai_initiatives": [],
        "named_products": [],
        "tech_stack": [],
        "named_customers": [],
        "recent_news": [],
        "executives": [],
        "hiring_signals": [],
        "key_evidence": [],
    }

    # ── AI Initiatives — strict proximity validation ─────────────────────
    # Only extract initiatives that appear within 200 chars of the company name
    # and filter out academic/generic artifacts (code paths, model names, etc.)
    ai_initiative_patterns = [
        (r'(?:launched?|introduced?|unveiled?|announced?|released?|built)\s+(?:an?\s+)?(?:AI|ML|machine learning|intelligent|smart)\s*[\w\s-]{5,60}', 'product_launch'),
        (r'(?:AI-powered|AI-driven|ML-based|intelligent)\s+[\w\s-]{5,40}', 'ai_feature'),
        (r'(?:generative AI|GenAI|LLM|copilot|assistant|chatbot)\s+[\w\s-]{3,30}', 'genai_feature'),
        (r'(?:predictive|recommendation|automation|optimization)\s+(?:engine|model|system|platform|tool)', 'ml_capability'),
    ]
    # Blocklist: patterns that indicate academic papers, code, or unrelated content
    ai_blocklist_patterns = [
        r'_dir\b', r'_ckp', r'\bcheckpoint\b', r'\.py\b', r'\.json\b',
        r'\bLLaMA\b', r'\bGPT-\d\b', r'\bBERT\b',  # model names without company context
        r'\bfigure\s+\d', r'\btable\s+\d', r'\bappendix\b',  # academic paper artifacts
        r'et\s+al\.?', r'arxiv', r'proceedings',  # citations
    ]
    seen_initiatives = set()
    for r in relevant_results:
        content = r.get("content", "")
        if not content:
            continue
        content_lower = content.lower()
        if company_lower not in content_lower:
            continue
        for pat, init_type in ai_initiative_patterns:
            for m in re.finditer(pat, content, re.IGNORECASE):
                initiative = m.group(0).strip()
                # Check proximity: initiative must be within 200 chars of company name
                match_start = m.start()
                company_positions = [i for i in range(len(content_lower)) if content_lower[i:i+len(company_lower)] == company_lower]
                near_company = any(abs(match_start - cp) < 200 for cp in company_positions)
                if not near_company:
                    continue
                # Check blocklist
                if any(re.search(bp, initiative, re.IGNORECASE) for bp in ai_blocklist_patterns):
                    continue
                fingerprint = initiative.lower()[:40]
                if fingerprint not in seen_initiatives and len(initiative) > 10:
                    seen_initiatives.add(fingerprint)
                    evidence["ai_initiatives"].append({
                        "text": initiative,
                        "type": init_type,
                    })
    evidence["ai_initiatives"] = evidence["ai_initiatives"][:6]

    # ── Named Products — require company name proximity ───────────────────
    product_patterns = [
        rf'{re.escape(company_name)}\s+([\w]+(?:\s+[\w]+)?)\s*(?:platform|product|solution|suite|module|tool|engine)',
        rf'([\w]+(?:\s+[\w]+)?)\s*(?:platform|product|solution|suite|module)\s*(?:by|from)\s*{re.escape(company_name)}',
    ]
    seen_products = set()
    for pat in product_patterns:
        for m in re.finditer(pat, relevant_text, re.IGNORECASE):
            product = m.group(1).strip() if m.group(1) else m.group(0).strip()
            if product.lower() not in seen_products and len(product) > 2 and len(product) < 50:
                seen_products.add(product.lower())
                evidence["named_products"].append(product)
    evidence["named_products"] = evidence["named_products"][:6]

    # ── Tech Stack — ONLY from company-relevant results ───────────────────
    # Additional requirement: the tech keyword must appear in a result
    # that mentions the company, not just anywhere in the search results.
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
    # Count tech mentions across company-relevant results only
    # Require at least 2 mentions to filter noise
    tech_with_counts = {}
    for tech, keywords in tech_map.items():
        mention_count = 0
        for r in relevant_results:
            r_lower = r.get("content", "").lower()
            if any(kw in r_lower for kw in keywords):
                mention_count += 1
        if mention_count >= 2:
            tech_with_counts[tech] = mention_count
    evidence["tech_stack"] = list(tech_with_counts.keys())
    evidence["_tech_mention_counts"] = tech_with_counts

    # ── Named Customers — strict validation ───────────────────────────────
    # Only accept proper nouns that look like company/org names
    customer_patterns = [
        r'(?:customers?\s+(?:include|like|such as)|trusted by|used by|works?\s+with|serves?|chosen by|partnered?\s+with)\s+([\w\s,&]+?)(?:\.|,\s*and|\band\b)',
        r'([\w\s]+?)\s+(?:uses?|chose|selected|implemented|deployed|partnered with)\s+' + re.escape(company_name),
    ]
    # Words that are not customer names
    customer_blocklist = {
        'but they', 'science', 'technology', 'the company', 'their clients',
        'customers', 'organizations', 'businesses', 'enterprises', 'users',
        'companies', 'institutions', 'agencies', 'teams', 'professionals',
        'individuals', 'financial institutions', 'credit unions', 'banks',
        'healthcare', 'hospitals', 'schools', 'universities',
    }
    seen_customers = set()
    for pat in customer_patterns:
        for m in re.finditer(pat, relevant_text, re.IGNORECASE):
            raw = m.group(1).strip()
            for cname in re.split(r',\s*|\s+and\s+', raw):
                cname = cname.strip()
                if len(cname) < 3 or len(cname) > 40:
                    continue
                if not cname[0].isupper():
                    continue
                if cname.lower() in customer_blocklist:
                    continue
                if cname.lower() in seen_customers:
                    continue
                # Must have at least one word with 3+ chars
                if not any(len(w) >= 3 for w in cname.split()):
                    continue
                # Should not be a generic phrase (all lowercase words except first)
                words = cname.split()
                if len(words) > 1 and all(w[0].islower() for w in words[1:]):
                    continue
                seen_customers.add(cname.lower())
                evidence["named_customers"].append(cname)
    evidence["named_customers"] = evidence["named_customers"][:8]

    # ── Recent News / Events — only from relevant results ─────────────────
    news_patterns = [
        r'(?:in\s+(?:20\d\d|January|February|March|April|May|June|July|August|September|October|November|December)[\w\s,]*?),?\s*' + re.escape(company_name) + r'\s+([\w\s,]+?)(?:\.|$)',
        re.escape(company_name) + r'\s+(?:announced?|launched?|raised?|acquired?|partnered?|released?|expanded?)\s+([\w\s,]+?)(?:\.|$)',
    ]
    seen_news = set()
    for pat in news_patterns:
        for m in re.finditer(pat, relevant_text, re.IGNORECASE):
            snippet = m.group(0).strip()[:150]
            fp = snippet.lower()[:60]
            if fp not in seen_news and len(snippet) > 20:
                seen_news.add(fp)
                evidence["recent_news"].append(snippet)
    evidence["recent_news"] = evidence["recent_news"][:6]

    # ── Executives — strict name validation ───────────────────────────────
    # Extract person names with C-suite/VP roles, with rigorous filtering
    ROLE_PATTERN = r'(?:CEO|CTO|CFO|COO|CAIO|Chief\s+(?:Technology|Executive|AI|Data|Operating|Financial|Information)\s+Officer|VP\s+(?:of\s+)?(?:Engineering|Product|Technology|Sales)|Head\s+of\s+(?:AI|Engineering|Product|Data)|President|Founder|Co-Founder)'
    exec_patterns = [
        # "Name, Role" or "Name, Role at Company"
        r'([A-Z][a-z]+(?:\s+[A-Z]\.?\s*)?[A-Z][a-z]+)\s*,\s*' + ROLE_PATTERN,
        # "Role Name" (e.g., "CEO John Smith")
        ROLE_PATTERN + r'\s+([A-Z][a-z]+(?:\s+[A-Z]\.?\s*)?[A-Z][a-z]+)',
        # "Name is the Role" or "Name serves as Role"
        r'([A-Z][a-z]+(?:\s+[A-Z]\.?\s*)?[A-Z][a-z]+)\s+(?:is\s+(?:the\s+)?|serves?\s+as\s+)' + ROLE_PATTERN,
    ]
    # Blocklist: things that look like names but aren't
    exec_name_blocklist = {
        'long beach', 'new york', 'san francisco', 'los angeles', 'champion health',
        'balance sheet', 'artificial intelligence', 'machine learning', 'deep learning',
        'chief technology', 'chief executive', 'vice president', 'managing director',
        'financial advisor', 'technology officer', 'of employee', 'of human',
        'of black', 'of engineering', 'of limitless',
    }
    # Single-word blocklist for first/last names that are clearly not person names
    exec_word_blocklist = {'is', 'at', 'of', 'the', 'and', 'for', 'was', 'has', 'its', 'in', 'ai', 'an'}
    seen_execs = set()
    for r in relevant_results:
        content = r.get("content", "")
        if not content or company_lower not in content.lower():
            continue
        for pat in exec_patterns:
            for m in re.finditer(pat, content, re.IGNORECASE):
                # Find the name group (first capturing group)
                name = m.group(1).strip() if m.lastindex else None
                if not name:
                    continue
                # Validate: must look like a person name (2-4 words, each capitalized)
                name_words = name.split()
                if len(name_words) < 2 or len(name_words) > 4:
                    continue
                if not all(w[0].isupper() or len(w) <= 2 for w in name_words):
                    continue
                # First word must not be a preposition/article/verb
                if name_words[0].lower() in exec_word_blocklist:
                    continue
                # Check against blocklist
                if name.lower() in exec_name_blocklist:
                    continue
                # Must not contain digits, newlines, or common non-name words
                if re.search(r'[\d\n\r]', name):
                    continue
                # Each word should be 2+ chars (no lone initials without period)
                if any(len(w) == 1 and '.' not in w for w in name_words):
                    continue
                if name.lower() not in seen_execs:
                    seen_execs.add(name.lower())
                    role_match = re.search(ROLE_PATTERN, m.group(0), re.IGNORECASE)
                    role = role_match.group(0) if role_match else "Executive"
                    evidence["executives"].append({"name": name, "role": role})
    evidence["executives"] = evidence["executives"][:5]

    # ── Hiring Signals — only from relevant results ───────────────────────
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
        if any(kw in relevant_lower for kw in keywords):
            evidence["hiring_signals"].append(role)

    # ── Key Evidence Snippets — only from relevant results ────────────────
    for r in relevant_results:
        content = r.get("content", "").strip()
        if not content or len(content) < 80:
            continue
        if company_lower in content.lower():
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
                except Exception:
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
        "relevant_results": len(relevant_results),
        "total_text_chars": len(relevant_text),
        "ai_initiatives_found": len(evidence["ai_initiatives"]),
        "tech_stack_signals": len(evidence["tech_stack"]),
        "customers_found": len(evidence["named_customers"]),
        "news_events": len(evidence["recent_news"]),
        "executives_found": len(evidence["executives"]),
        "hiring_roles_detected": len(evidence["hiring_signals"]),
        "evidence_snippets": len(evidence["key_evidence"]),
    }

    # ── Generate analytical narrative summary ──────────────────────────────
    evidence["narrative_summary"] = _generate_narrative(company_name, evidence)

    return evidence


def _generate_narrative(company_name: str, evidence: dict) -> str:
    """Generate a 2-3 sentence analytical summary of a company's AI posture.

    Uses a template-driven approach based on signal strength across dimensions.
    Tone: analytical, data-driven — suitable for a PE CAIO briefing.
    """
    ai_inits = evidence.get("ai_initiatives", [])
    tech = evidence.get("tech_stack", [])
    gh_confirmed = evidence.get("tech_stack_github_confirmed", [])
    hiring = evidence.get("hiring_signals", [])
    execs = evidence.get("executives", [])
    customers = evidence.get("named_customers", [])
    news = evidence.get("recent_news", [])
    github = evidence.get("github", {})
    careers = evidence.get("careers", {})
    stats = evidence.get("enrichment_stats", {})

    sentences = []

    # ── Sentence 1: AI activity level ──────────────────────────────────────
    ai_roles_hiring = [r for r in hiring if any(kw in r.lower() for kw in ['ai', 'ml', 'data sci', 'nlp', 'mlops', 'computer vision'])]
    has_ai_initiatives = len(ai_inits) > 0
    has_ai_hiring = len(ai_roles_hiring) > 0
    has_modern_stack = any(t in tech for t in ['TensorFlow', 'PyTorch', 'OpenAI', 'Anthropic', 'Hugging Face', 'Databricks', 'Snowflake'])

    if has_ai_initiatives and has_ai_hiring and has_modern_stack:
        # Strong signals
        init_types = set(a["type"] for a in ai_inits)
        if "product_launch" in init_types:
            sentences.append(f"{company_name} shows strong AI activity with public product launches incorporating AI/ML capabilities, active hiring for AI-focused roles ({', '.join(ai_roles_hiring[:2])}), and a modern ML-capable tech stack.")
        else:
            ml_tech = [t for t in tech if t in ['TensorFlow', 'PyTorch', 'OpenAI', 'Anthropic', 'Databricks', 'Snowflake', 'Hugging Face']][:3]
            sentences.append(f"{company_name} demonstrates meaningful AI adoption with {len(ai_inits)} identified AI-related features, active hiring across {len(ai_roles_hiring)} AI/ML disciplines, and investment in modern ML infrastructure ({', '.join(ml_tech)}).")
    elif has_ai_initiatives and (has_ai_hiring or has_modern_stack):
        # Moderate signals
        sentences.append(f"{company_name} shows moderate AI engagement with {len(ai_inits)} detected AI feature{'s' if len(ai_inits) > 1 else ''}, though evidence suggests early-stage adoption rather than mature AI product development.")
    elif has_ai_initiatives:
        # Initiatives only, no supporting infrastructure
        sentences.append(f"{company_name} references AI capabilities in public materials, but limited evidence of dedicated AI infrastructure, hiring, or ML tooling suggests these may be aspirational or vendor-integrated features.")
    elif has_ai_hiring:
        # Hiring but no visible products
        sentences.append(f"{company_name} appears to be building AI capability — hiring signals for {', '.join(ai_roles_hiring[:2])} detected, but no public AI product launches or features identified yet.")
    else:
        # Minimal signals
        relevant_pct = stats.get("relevant_results", 0) / max(stats.get("total_results", 1), 1) * 100
        if relevant_pct < 40:
            sentences.append(f"{company_name} has limited public web presence (only {stats.get('relevant_results', 0)} of {stats.get('total_results', 0)} search results were company-relevant), making AI readiness assessment difficult from public sources alone.")
        else:
            sentences.append(f"No public AI initiatives, ML tooling, or AI-specific hiring detected for {company_name} — current operations appear to rely on traditional software approaches.")

    # ── Sentence 2: Technical foundation ───────────────────────────────────
    gh_repos = github.get("total_public_repos", 0) if github.get("found") else 0
    gh_recent = github.get("recently_active_repos", 0) if github.get("found") else 0
    gh_langs = [l["language"] for l in github.get("primary_languages", [])] if github.get("found") else []

    tech_parts = []
    if gh_repos > 0:
        activity_note = f"{gh_recent} recently active" if gh_recent > 0 else "no recent activity"
        tech_parts.append(f"{gh_repos} public repos ({activity_note}) primarily in {', '.join(gh_langs[:3]) if gh_langs else 'various languages'}")
    if gh_confirmed:
        tech_parts.append(f"GitHub-confirmed stack: {', '.join(gh_confirmed[:4])}")
    elif tech:
        tech_parts.append(f"web-detected stack includes {', '.join(tech[:4])}")

    if tech_parts:
        sentences.append(f"Technical footprint: {'; '.join(tech_parts)}.")
    elif not github.get("found"):
        sentences.append("No public GitHub presence or detectable tech stack — engineering practices are opaque from external research.")

    # ── Sentence 3: Talent & investment signals ────────────────────────────
    career_openings = careers.get("total_openings", 0) if careers and careers.get("found") else 0
    career_ai = careers.get("ai_ml_openings", 0) if careers and careers.get("found") else 0

    talent_parts = []
    if career_openings > 0:
        if career_ai > 0:
            talent_parts.append(f"{career_openings} open positions ({career_ai} AI/ML-specific)")
        else:
            talent_parts.append(f"{career_openings} open positions (none AI/ML-specific)")
    if len(hiring) > 3:
        talent_parts.append(f"broad technical hiring across {len(hiring)} role categories")
    elif len(hiring) > 0:
        talent_parts.append(f"hiring signals for {', '.join(hiring[:3])}")
    if execs:
        # Only include execs whose names don't contain "at [OtherCompany]" patterns
        clean_execs = [e for e in execs if not e["name"].lower().startswith("at ") and not e["name"].lower().startswith("of ")]
        ai_execs = [e for e in clean_execs if any(kw in e["role"].lower() for kw in ['ai', 'data', 'technology'])]
        if ai_execs:
            talent_parts.append(f"identified tech leadership: {ai_execs[0]['name']} ({ai_execs[0]['role']})")
    if news:
        talent_parts.append(f"{len(news)} recent news event{'s' if len(news) > 1 else ''}")

    if talent_parts:
        sentences.append(f"Key signals: {'; '.join(talent_parts)}.")

    return " ".join(sentences)


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

    # ── Merge with existing GitHub/careers data and cross-validate ─────────
    output_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "public", "portfolio_evidence.json")
    output_path = os.path.normpath(output_path)

    # Load existing data (may contain github/careers from enrich_github_careers.py)
    existing_data = {}
    if os.path.exists(output_path):
        try:
            with open(output_path) as f:
                existing_data = json.load(f)
            logger.info(f"Loaded existing evidence data with {len(existing_data)} companies")
        except Exception:
            pass

    # Merge: keep github/careers from existing, update everything else
    for name, evidence in all_evidence.items():
        if name in existing_data:
            # Preserve github and careers data from previous enrichment
            for key in ("github", "careers"):
                if key in existing_data[name] and key not in evidence:
                    evidence[key] = existing_data[name][key]

        # Cross-validate tech stack against GitHub languages
        github_data = evidence.get("github", {})
        github_languages = set()
        if github_data.get("found"):
            for lang_entry in github_data.get("primary_languages", []):
                lang = lang_entry.get("language", "")
                if lang:
                    github_languages.add(lang.lower())

        # Map GitHub languages to tech_map names
        github_to_tech = {
            "php": "PHP", "python": "Python", "javascript": "Node.js",
            "typescript": "TypeScript", "java": "Java", "go": "Go",
            "c#": ".NET", "ruby": "Ruby", "rust": "Rust", "swift": "Swift",
            "html": "React",  # not a guarantee, but common
        }

        # Annotate tech stack with confidence
        confirmed_tech = []
        web_only_tech = []
        mention_counts = evidence.pop("_tech_mention_counts", {})

        for tech in evidence.get("tech_stack", []):
            # Check if GitHub confirms this technology
            tech_lower = tech.lower()
            github_confirmed = False
            for gl, tn in github_to_tech.items():
                if tn == tech and gl in github_languages:
                    github_confirmed = True
                    break
            # Also check direct match
            if tech_lower in github_languages:
                github_confirmed = True

            if github_confirmed:
                confirmed_tech.append(tech)
            else:
                web_only_tech.append(tech)

        # If company has GitHub data with repos, require 3+ mentions for
        # unconfirmed tech (stricter threshold without GitHub backing)
        if github_data.get("found") and github_data.get("total_public_repos", 0) > 0:
            web_only_tech = [t for t in web_only_tech if mention_counts.get(t, 0) >= 3]

        evidence["tech_stack"] = confirmed_tech + web_only_tech
        evidence["tech_stack_github_confirmed"] = confirmed_tech
        all_evidence[name] = evidence

    # Save enrichment data
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
