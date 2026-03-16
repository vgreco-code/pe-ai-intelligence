"""One-time cleanup script to fix known data quality issues in portfolio_evidence.json.

Addresses:
  1. Wrong GitHub org mappings (dashpay, trackit, OG-star-tech, primate-run, etc.)
  2. Executive parsing artifacts (company names, regex fragments)
  3. Customer contamination (nav elements, self-references)
  4. AI initiative noise (non-initiative entries)
  5. Key evidence from wrong companies
  6. Narrative regeneration after cleanup

Run:  python cleanup_evidence.py
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from enrich_portfolio import _generate_narrative

EVIDENCE_PATH = os.path.join(os.path.dirname(__file__), "..", "frontend", "public", "portfolio_evidence.json")
EVIDENCE_PATH = os.path.normpath(EVIDENCE_PATH)

SCORES_PATH = os.path.join(os.path.dirname(__file__), "..", "frontend", "public", "portfolio_scores.json")
SCORES_PATH = os.path.normpath(SCORES_PATH)


def load():
    with open(EVIDENCE_PATH) as f:
        return json.load(f)


def save(data):
    with open(EVIDENCE_PATH, "w") as f:
        json.dump(data, f, indent=2)


# ── 1. GitHub org corrections ─────────────────────────────────────────────
# These orgs don't belong to the portfolio companies. They were matched by
# name similarity but are actually unrelated projects.
WRONG_GITHUB_ORGS = {
    "Dash": "dashpay",          # DashPay cryptocurrency, not Dash Financial
    "TrackIt Transit": "trackit",  # TrackIt cloud consulting, not TrackIt Transit
    "Track Star": "OG-star-tech",  # Star tracker hardware project
    "Primate": "primate-run",      # Primate web framework (open source)
    "Spokane": "spokane",          # Empty org, probably Spokane city
    "AutoTime": "AutoTimer",       # Different product (timer app)
    "SMRTR": "smrtr",             # PHP developer tools, not SMRTR business automation
    "ViaPeople": "viapeople-inc",  # Fork of DefinitelyTyped — probably not their real work
}

def fix_github(data):
    """Remove GitHub data for known wrong org mappings."""
    changes = []
    for company, wrong_org in WRONG_GITHUB_ORGS.items():
        if company in data:
            gh = data[company].get("github", {})
            if gh.get("org_login") == wrong_org:
                data[company]["github"] = {"found": False}
                # Also remove github-confirmed tech stack since it was based on wrong repos
                if "tech_stack_github_confirmed" in data[company]:
                    old = data[company]["tech_stack_github_confirmed"]
                    data[company]["tech_stack_github_confirmed"] = []
                    changes.append(f"  {company}: removed wrong GitHub @{wrong_org} (had {old})")
                else:
                    changes.append(f"  {company}: removed wrong GitHub @{wrong_org}")
    return changes


# ── 2. Executive cleanup ──────────────────────────────────────────────────

def is_valid_executive(name: str, role: str, company_name: str) -> bool:
    """Validate that an executive entry is a real person at this company."""
    name_lower = name.lower().strip()

    # Known bad patterns — company names, locations, parsing artifacts
    bad_name_patterns = [
        r'^(or|as|at|of|the|and|in|for)\s',  # Starts with preposition
        r'^(latah|vista|county|city|state)\s',  # Geographic entities
        r'\b(inc|llc|corp|ltd|county|city)\b',  # Business/gov suffixes
        r'^as\s+\w+$',   # "As DASH" etc.
        r'^or\s+\w+$',   # "or CTO" etc.
    ]
    for pat in bad_name_patterns:
        if re.search(pat, name_lower):
            return False

    # Must have at least 2 words that look like a human name
    words = name.split()
    if len(words) < 2:
        return False

    # Business/role words shouldn't be in the name
    business_words = {
        'title', 'consulting', 'solutions', 'technologies', 'software',
        'systems', 'services', 'group', 'capital', 'financial', 'industrial',
        'county', 'city', 'state', 'district', 'university',
        'executive', 'development', 'corporate', 'architect', 'engineer',
        'director', 'officer', 'manager', 'analyst', 'balance', 'sheet',
    }
    if any(w.lower() in business_words for w in words):
        return False

    # Role must contain an actual role keyword
    role_lower = role.lower()
    valid_roles = ['ceo', 'cto', 'cfo', 'coo', 'caio', 'cio', 'president', 'founder',
                   'officer', 'director', 'vp', 'vice president', 'head', 'partner']
    if not any(r in role_lower for r in valid_roles):
        return False

    return True


def fix_executives(data):
    """Remove invalid executive entries."""
    changes = []
    for company, ev in data.items():
        execs = ev.get("executives", [])
        if not execs:
            continue
        valid = [e for e in execs if is_valid_executive(e["name"], e["role"], company)]
        removed = len(execs) - len(valid)
        if removed > 0:
            bad = [e for e in execs if e not in valid]
            ev["executives"] = valid
            bad_desc = [e["name"] + " — " + e["role"] for e in bad]
            changes.append(f"  {company}: removed {removed} bad exec(s): {bad_desc}")
    return changes


# ── 3. Customer cleanup ───────────────────────────────────────────────────

def is_valid_customer(customer: str, company_name: str) -> bool:
    """Validate that a customer entry is actually a real customer name."""
    c = customer.strip()

    # Too short or too long
    if len(c) < 2 or len(c) > 60:
        return False

    # Contains HTML/newline artifacts
    if any(ch in c for ch in ['\n', '\r', '\t', '<', '>', '{', '}']):
        return False

    # Navigation/footer text patterns
    nav_patterns = [
        r'terms', r'privacy', r'policy', r'disclaimer', r'cookie',
        r'copyright', r'sign\s*up', r'log\s*in', r'contact\s*us',
        r'about\s*us', r'legal', r'sitemap', r'subscribe',
    ]
    c_lower = c.lower()
    if any(re.search(pat, c_lower) for pat in nav_patterns):
        return False

    # Self-reference: customer is the company itself
    if c_lower == company_name.lower() or company_name.lower() in c_lower:
        return False

    # Known open-source projects / CNCF tools that aren't customers
    non_customers = {
        'linkerd', 'traefik', 'sustainableit', 'istio', 'envoy',
        'prometheus', 'grafana', 'kubernetes', 'docker',
    }
    if c_lower in non_customers:
        return False

    return True


def fix_customers(data):
    """Remove invalid customer entries."""
    changes = []
    for company, ev in data.items():
        custs = ev.get("named_customers", [])
        if not custs:
            continue
        valid = [c for c in custs if is_valid_customer(c, company)]
        removed = len(custs) - len(valid)
        if removed > 0:
            bad = [c for c in custs if c not in valid]
            ev["named_customers"] = valid
            changes.append(f"  {company}: removed {removed} bad customer(s): {bad}")
    return changes


# ── 4. AI Initiative cleanup ─────────────────────────────────────────────

def is_valid_initiative(init: dict, company_name: str) -> bool:
    """Validate that an AI initiative is a real initiative, not noise."""
    text = init.get("text", "").strip()
    itype = init.get("type", "")

    if len(text) < 10:
        return False

    # Known non-initiative patterns
    bad_patterns = [
        r'^assistant\s+director',  # Job title, not an initiative
        r'^director\b',
        r'^manager\b',
        r'^vice\s+president',
        r'^senior\s+',
        r'resume\s+tips',
        r'career\s+advice',
    ]
    text_lower = text.lower()
    if any(re.search(pat, text_lower) for pat in bad_patterns):
        return False

    # Must mention AI/ML/intelligence/automation in some meaningful way
    ai_keywords = ['ai', 'artificial intelligence', 'machine learning', 'ml',
                   'intelligent', 'neural', 'nlp', 'natural language', 'deep learning',
                   'predictive', 'automation', 'automated', 'generative', 'chatbot',
                   'computer vision', 'recommendation', 'personalization']
    if not any(kw in text_lower for kw in ai_keywords):
        return False

    # Check for Tavily hallucination patterns
    if is_tavily_hallucination(text, company_name):
        return False

    return True


def fix_initiatives(data):
    """Remove invalid AI initiative entries."""
    changes = []
    for company, ev in data.items():
        inits = ev.get("ai_initiatives", [])
        if not inits:
            continue
        valid = [i for i in inits if is_valid_initiative(i, company)]
        removed = len(inits) - len(valid)
        if removed > 0:
            bad = [i for i in inits if i not in valid]
            ev["ai_initiatives"] = valid
            changes.append(f"  {company}: removed {removed} bad initiative(s): {[i['text'][:60] for i in bad]}")
    return changes


# ── 5. Key evidence cleanup ──────────────────────────────────────────────

def is_relevant_evidence(ev_item: dict, company_name: str) -> bool:
    """Check if a key evidence item is actually about this company."""
    text = ev_item.get("text", "").lower()
    source = ev_item.get("source", "").lower()
    url = (ev_item.get("url") or "").lower()

    company_lower = company_name.lower()
    company_words = [w for w in company_lower.split() if len(w) > 2]

    # For multi-word company names, require the full phrase
    if len(company_words) > 1:
        if company_lower not in text:
            return False
    else:
        # Single word: require word boundary
        if not re.search(r'\b' + re.escape(company_lower) + r'\b', text):
            return False

    # Known wrong-source domains
    wrong_sources = [
        'illumina.com',  # DNA company, not Primate
        'akbankinvestorrelations',  # Turkish bank, not NexTalk
        'viridiantherapeutics',  # Pharma, "primate" = animal testing
    ]
    if any(ws in source or ws in url for ws in wrong_sources):
        return False

    # Single-word company name collision detection
    # These short names match common English words or parts of other company names
    AMBIGUOUS_COMPANIES = {
        'dash': {
            # "Dash by LocaliQ" is a different product
            'reject_context': ['localiq', 'doordash', 'geometry dash', 'dash diet'],
        },
        'primate': {
            # "non-human primate" is about animals
            'reject_context': ['non-human primate', 'nhp', 'primate species',
                              'primate research', 'primate study', 'primate model'],
        },
        'spokane': {
            # Spokane is also a city — filter city government / unrelated Spokane businesses
            'reject_context': ['spokane city', 'spokane county', 'city of spokane',
                              'spokane fire', 'spokane police', 'spokane school',
                              'treasury4'],
        },
        'champ': {
            # "champ" is a common English word
            'reject_context': ['world champ', 'boxing champ', 'defending champ',
                              'champs platform', 'champs-elysees'],
        },
    }
    if company_lower in AMBIGUOUS_COMPANIES:
        reject_list = AMBIGUOUS_COMPANIES[company_lower]['reject_context']
        if any(r in text for r in reject_list):
            return False

    return True


def fix_evidence(data):
    """Remove key evidence items from wrong companies."""
    changes = []
    for company, ev in data.items():
        items = ev.get("key_evidence", [])
        if not items:
            continue
        valid = [e for e in items if is_relevant_evidence(e, company)]
        removed = len(items) - len(valid)
        if removed > 0:
            bad = [e for e in items if e not in valid]
            ev["key_evidence"] = valid
            changes.append(f"  {company}: removed {removed} irrelevant evidence(s) from: {[e.get('source','?')[:40] for e in bad]}")
    return changes


# ── 6. Careers cleanup ───────────────────────────────────────────────────

def fix_careers(data):
    """Clean careers data artifacts."""
    changes = []
    for company, ev in data.items():
        careers = ev.get("careers", {})
        if not careers.get("found"):
            continue

        # Clean sample_roles of HTML artifacts
        roles = careers.get("sample_roles", [])
        clean_roles = [r.strip() for r in roles if '\n' not in r and len(r.strip()) > 2 and len(r.strip()) < 60]
        if len(clean_roles) != len(roles):
            careers["sample_roles"] = clean_roles
            changes.append(f"  {company}: cleaned {len(roles) - len(clean_roles)} bad career role(s)")

    return changes


# ── 7. Tavily AI answer hallucination cleanup ────────────────────────────
# Tavily's AI answer feature appends "Financial Services" to company names
# and fabricates plausible but fictional details (funding rounds, customers,
# AI product launches). These hallucinated entries contaminate:
#   - key_evidence (no source URL = came from Tavily answer, not a real webpage)
#   - ai_initiatives (generic "launched an AI product..." phrasing)
#   - named_customers (fabricated customer names from Tavily answer)
#   - executives (fabricated or mixed with people from other companies)

def is_tavily_hallucination(text: str, company_name: str) -> bool:
    """Detect Tavily AI answer hallucinations.

    Tavily's answer synthesis commonly:
    1. Appends 'Financial Services' or vertical name to the company
    2. Generates generic AI product launch language
    3. Claims specific funding rounds, partnerships, customer names
    """
    text_lower = text.lower()
    company_lower = company_name.lower()

    # Pattern 1: "{Company} Financial Services" — Tavily's hallucination signature
    hallucination_suffixes = [
        'financial services', 'enterprise software', 'hr/workforce',
        'healthcare', 'life sciences', 'healthcare/life sciences',
    ]
    for suffix in hallucination_suffixes:
        if f"{company_lower} {suffix}" in text_lower:
            return True

    return False


def fix_hallucinated_evidence(data):
    """Remove key evidence entries that came from Tavily AI answer hallucinations."""
    changes = []
    for company, ev in data.items():
        # Key evidence: remove sourceless entries that match hallucination patterns
        items = ev.get("key_evidence", [])
        if items:
            valid = []
            for e in items:
                # Entries without a source URL came from Tavily's AI answer
                if not e.get("source") and is_tavily_hallucination(e.get("text", ""), company):
                    continue
                valid.append(e)
            removed = len(items) - len(valid)
            if removed > 0:
                ev["key_evidence"] = valid
                changes.append(f"  {company}: removed {removed} hallucinated evidence item(s)")

        # AI initiatives: remove entries that are just restated Tavily answer hallucinations
        inits = ev.get("ai_initiatives", [])
        if inits:
            valid_inits = []
            for i in inits:
                text = i.get("text", "")
                # Check if this initiative is just a generic Tavily answer restatement
                if is_tavily_hallucination(text, company):
                    continue
                valid_inits.append(i)
            removed = len(inits) - len(valid_inits)
            if removed > 0:
                ev["ai_initiatives"] = valid_inits
                changes.append(f"  {company}: removed {removed} hallucinated initiative(s)")

    return changes


# ── 8. Hiring signals quality check ──────────────────────────────────────
# Many hiring signals come from Tavily answer synthesis, not actual job postings.
# Without a careers page to verify, these are unreliable.
# We'll flag them but keep them since they may still be directionally useful.


# ── Main ──────────────────────────────────────────────────────────────────

def main():
    data = load()

    print("=" * 80)
    print("PORTFOLIO EVIDENCE CLEANUP")
    print("=" * 80)

    print("\n1. GitHub org corrections:")
    changes = fix_github(data)
    for c in changes:
        print(c)
    if not changes:
        print("  (none)")

    print("\n2. Executive validation:")
    changes = fix_executives(data)
    for c in changes:
        print(c)
    if not changes:
        print("  (none)")

    print("\n3. Customer validation:")
    changes = fix_customers(data)
    for c in changes:
        print(c)
    if not changes:
        print("  (none)")

    print("\n4. AI initiative validation:")
    changes = fix_initiatives(data)
    for c in changes:
        print(c)
    if not changes:
        print("  (none)")

    print("\n5. Key evidence validation:")
    changes = fix_evidence(data)
    for c in changes:
        print(c)
    if not changes:
        print("  (none)")

    print("\n6. Careers cleanup:")
    changes = fix_careers(data)
    for c in changes:
        print(c)
    if not changes:
        print("  (none)")

    print("\n7. Tavily hallucination cleanup:")
    changes = fix_hallucinated_evidence(data)
    for c in changes:
        print(c)
    if not changes:
        print("  (none)")

    # Regenerate narratives with clean data
    print("\n7. Regenerating narrative summaries...")
    for name, ev in data.items():
        ev["narrative_summary"] = _generate_narrative(name, ev)
        print(f"  {name}: {ev['narrative_summary'][:80]}...")

    save(data)
    print(f"\nSaved cleaned evidence to {EVIDENCE_PATH}")


if __name__ == "__main__":
    main()
