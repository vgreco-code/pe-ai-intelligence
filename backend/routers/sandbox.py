"""Sandbox endpoint — score a user-submitted company through the full pipeline.

Flow: company name → Tavily web research → feature extraction → 17-dimension scoring → tier classification
"""
import math
import json
import re
import logging
import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
from database import get_db
from config import get_settings
from models.company import Company, DimensionScore, CompanyScore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sandbox", tags=["sandbox"])

# ── Scoring engine constants ──────────────────────────────────────────────────

DERIVED_WEIGHTS = {
    "data_quality": 0.997, "data_integration": 0.913, "analytics_maturity": 1.126,
    "cloud_architecture": 0.559, "tech_stack_modernity": 0.297, "ai_engineering": 0.519,
    "ai_product_features": 4.447, "revenue_ai_upside": 2.019, "margin_ai_upside": 0.644,
    "product_differentiation": 0.481, "ai_talent_density": 2.346, "leadership_ai_vision": 1.432,
    "org_change_readiness": 0.534, "partner_ecosystem": 0.972, "ai_governance": 0.422,
    "regulatory_readiness": 0.32, "ai_momentum": 0.272,
}
TOTAL_WEIGHT = sum(DERIVED_WEIGHTS.values())

CATEGORIES = {
    "Data & Analytics": ["data_quality", "data_integration", "analytics_maturity"],
    "Technology & Infrastructure": ["cloud_architecture", "tech_stack_modernity", "ai_engineering"],
    "AI Product & Value": ["ai_product_features", "revenue_ai_upside", "margin_ai_upside", "product_differentiation"],
    "Organization & Talent": ["ai_talent_density", "leadership_ai_vision", "org_change_readiness", "partner_ecosystem"],
    "Governance & Risk": ["ai_governance", "regulatory_readiness"],
    "Velocity & Momentum": ["ai_momentum"],
}

DIMENSION_LABELS = {
    "data_quality": "Data Quality & Availability", "data_integration": "Data Integration & APIs",
    "analytics_maturity": "Analytics Maturity", "cloud_architecture": "Cloud Architecture",
    "tech_stack_modernity": "Tech Stack Modernity", "ai_engineering": "AI/ML Engineering",
    "ai_product_features": "AI Product Features", "revenue_ai_upside": "Revenue AI Upside",
    "margin_ai_upside": "Margin AI Upside", "product_differentiation": "Product Differentiation",
    "ai_talent_density": "AI Talent Density", "leadership_ai_vision": "Leadership AI Vision",
    "org_change_readiness": "Org Change Readiness", "partner_ecosystem": "Partner Ecosystem",
    "ai_governance": "AI Governance", "regulatory_readiness": "Regulatory Readiness",
    "ai_momentum": "AI Momentum",
}


# ── Scoring functions ─────────────────────────────────────────────────────────

def classify_tier(score: float) -> str:
    if score >= 4.0:
        return "AI-Ready"
    if score >= 3.2:
        return "AI-Buildable"
    if score >= 2.5:
        return "AI-Emerging"
    return "AI-Limited"


def assign_wave(score: float) -> int:
    if score >= 3.5:
        return 1
    if score >= 2.8:
        return 2
    return 3


def compute_composite(pillar_scores: dict[str, float]) -> float:
    weighted = sum(pillar_scores.get(d, 0) * w for d, w in DERIVED_WEIGHTS.items())
    return round(weighted / TOTAL_WEIGHT, 2)


def compute_category_scores(pillar_scores: dict[str, float]) -> dict[str, float]:
    result = {}
    for cat, dims in CATEGORIES.items():
        vals = [pillar_scores[d] for d in dims if d in pillar_scores]
        result[cat] = round(sum(vals) / len(vals), 2) if vals else 0.0
    return result


# ── Web research → feature extraction ─────────────────────────────────────────

async def research_company(company_name: str, tavily_key: str) -> dict:
    """Use Tavily API to research a company and extract structured features."""
    queries = [
        f"{company_name} company overview revenue employees funding",
        f"{company_name} AI artificial intelligence machine learning features products",
        f"{company_name} technology stack cloud infrastructure API platform",
    ]

    all_content = []
    async with httpx.AsyncClient(timeout=30.0) as client:
        for query in queries:
            try:
                resp = await client.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": tavily_key,
                        "query": query,
                        "search_depth": "basic",
                        "max_results": 3,
                        "include_answer": True,
                    },
                )
                data = resp.json()
                if data.get("answer"):
                    all_content.append(data["answer"])
                for result in data.get("results", []):
                    all_content.append(result.get("content", ""))
            except Exception as e:
                logger.warning(f"Tavily search failed for '{query}': {e}")

    research_text = "\n".join(all_content)
    features = extract_features(company_name, research_text)
    features["research_summary"] = research_text[:2000]  # Keep for display
    return features


def extract_features(company_name: str, text: str) -> dict:
    """Extract structured company features from research text using keyword heuristics."""
    text_lower = text.lower()

    # Employee count extraction
    employee_count = None
    emp_patterns = [
        r'(\d[\d,]+)\s*(?:employees|staff|team members|people)',
        r'(?:employs?|workforce of|headcount[:\s])\s*(\d[\d,]+)',
        r'(\d[\d,]+)\+?\s*(?:employee)',
    ]
    for pat in emp_patterns:
        m = re.search(pat, text_lower)
        if m:
            employee_count = int(m.group(1).replace(',', ''))
            break

    # Funding extraction
    funding = None
    fund_patterns = [
        r'\$(\d+(?:\.\d+)?)\s*(billion|million|B|M)\s*(?:in\s+)?(?:funding|raised|valuation|revenue)',
        r'(?:raised|funding of|valued at)\s*\$(\d+(?:\.\d+)?)\s*(billion|million|B|M)',
    ]
    for pat in fund_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            amount = float(m.group(1))
            unit = m.group(2).lower()
            if unit in ('billion', 'b'):
                funding = amount * 1e9
            elif unit in ('million', 'm'):
                funding = amount * 1e6
            break

    # Founded year
    founded_year = None
    m = re.search(r'(?:founded|established|started)\s*(?:in\s+)?(\d{4})', text_lower)
    if m:
        yr = int(m.group(1))
        if 1900 <= yr <= 2026:
            founded_year = yr

    # Boolean signals
    ai_keywords = ['artificial intelligence', 'machine learning', 'deep learning', 'ai-powered',
                    'ai features', 'neural network', 'nlp', 'natural language processing',
                    'generative ai', 'llm', 'large language model', 'copilot', 'ai assistant']
    has_ai_features = any(kw in text_lower for kw in ai_keywords)

    cloud_keywords = ['cloud-native', 'aws', 'azure', 'google cloud', 'gcp', 'kubernetes',
                      'docker', 'microservices', 'saas', 'cloud platform', 'serverless']
    cloud_native = any(kw in text_lower for kw in cloud_keywords)

    public_keywords = ['publicly traded', 'ipo', 'nasdaq', 'nyse', 'stock price',
                       'ticker', 'market cap', 'sec filing']
    is_public = any(kw in text_lower for kw in public_keywords)

    # Intensity scores (1-5) based on keyword density
    api_keywords = ['api', 'rest api', 'graphql', 'webhook', 'integration', 'sdk',
                    'developer platform', 'marketplace', 'ecosystem', 'open platform']
    api_count = sum(1 for kw in api_keywords if kw in text_lower)
    api_ecosystem = min(5.0, 1.5 + api_count * 0.5)

    data_keywords = ['data platform', 'data warehouse', 'big data', 'analytics',
                     'data lake', 'real-time data', 'data pipeline', 'etl', 'data-driven']
    data_count = sum(1 for kw in data_keywords if kw in text_lower)
    data_richness = min(5.0, 1.5 + data_count * 0.6)

    reg_keywords = ['compliance', 'gdpr', 'hipaa', 'sox', 'regulated', 'regulatory',
                    'audit', 'certification', 'iso', 'fedramp']
    reg_count = sum(1 for kw in reg_keywords if kw in text_lower)
    regulatory_burden = min(5.0, 1.5 + reg_count * 0.6)

    market_keywords = ['market leader', 'industry leader', 'dominant', '#1', 'leading provider',
                       'largest', 'top player', 'pioneer', 'category leader', 'unicorn']
    mkt_count = sum(1 for kw in market_keywords if kw in text_lower)
    market_position = min(5.0, 2.0 + mkt_count * 0.7)

    # Vertical detection
    vertical = detect_vertical(text_lower)

    # Website extraction
    website = None
    m = re.search(r'(?:https?://)?(?:www\.)?([a-z0-9-]+\.(?:com|io|co|ai|tech|org|net))', text_lower)
    if m:
        website = f"https://{m.group(0)}"

    return {
        "vertical": vertical,
        "website": website,
        "founded_year": founded_year,
        "employee_count": employee_count,
        "funding_total_usd": funding,
        "is_public": is_public,
        "has_ai_features": has_ai_features,
        "cloud_native": cloud_native,
        "api_ecosystem_strength": round(api_ecosystem, 1),
        "data_richness": round(data_richness, 1),
        "regulatory_burden": round(regulatory_burden, 1),
        "market_position": round(market_position, 1),
    }


def detect_vertical(text: str) -> str:
    """Detect industry vertical from text content."""
    verticals = {
        "Healthcare/Life Sciences": ["healthcare", "health tech", "biotech", "pharmaceutical", "medical", "clinical", "patient"],
        "Financial Services": ["fintech", "banking", "financial", "insurance", "payments", "lending", "credit"],
        "E-commerce/Retail": ["e-commerce", "ecommerce", "retail", "shopping", "marketplace", "consumer"],
        "Enterprise Software": ["enterprise", "saas", "b2b software", "crm", "erp", "workflow"],
        "Cybersecurity": ["cybersecurity", "security", "infosec", "threat detection", "identity"],
        "Education": ["edtech", "education", "learning platform", "lms", "school"],
        "Real Estate/PropTech": ["real estate", "proptech", "property", "housing"],
        "HR/Workforce": ["hr tech", "human resources", "workforce", "recruiting", "talent"],
        "Marketing/AdTech": ["martech", "advertising", "marketing platform", "ad tech"],
        "Supply Chain/Logistics": ["supply chain", "logistics", "shipping", "freight", "warehouse"],
        "Construction": ["construction", "building", "contractor"],
        "Legal Tech": ["legal tech", "law firm", "legal"],
        "Data & Analytics": ["data analytics", "business intelligence", "data platform"],
        "AI/ML Platform": ["ai platform", "machine learning platform", "mlops"],
        "DevOps/Infrastructure": ["devops", "infrastructure", "cloud infrastructure", "platform engineering"],
    }
    scores = {}
    for vertical, keywords in verticals.items():
        count = sum(1 for kw in keywords if kw in text)
        if count > 0:
            scores[vertical] = count
    if scores:
        return max(scores, key=scores.get)
    return "Technology"


# ── Heuristic dimension scorer ────────────────────────────────────────────────

def estimate_dimension_scores(data: dict) -> dict[str, float]:
    """Estimate 17-dimension scores from extracted company features."""
    scores = {}
    emp = data.get("employee_count") or 100
    funding = data.get("funding_total_usd") or 0
    is_public = data.get("is_public", False)
    has_ai = data.get("has_ai_features", False)
    cloud = data.get("cloud_native", False)
    api_str = data.get("api_ecosystem_strength") or 2.5
    data_rich = data.get("data_richness") or 2.5
    reg_burden = data.get("regulatory_burden") or 2.5
    mkt_pos = data.get("market_position") or 2.5

    funding_score = min(5.0, max(1.0, (1.0 + math.log10(max(funding, 1e6)) - 6) * 1.5)) if funding > 0 else 2.0
    size_factor = min(5.0, max(1.0, 1.0 + math.log10(max(emp, 10)) / 1.5))

    # Data & Analytics
    scores["data_quality"] = round(min(5.0, data_rich * 0.7 + size_factor * 0.3), 2)
    scores["data_integration"] = round(min(5.0, api_str * 0.6 + (4.0 if cloud else 2.5) * 0.4), 2)
    scores["analytics_maturity"] = round(min(5.0, (data_rich + size_factor + funding_score) / 3), 2)

    # Technology & Infrastructure
    scores["cloud_architecture"] = round(min(5.0, (4.5 if cloud else 2.0) * 0.6 + api_str * 0.4), 2)
    scores["tech_stack_modernity"] = round(min(5.0, (4.0 if cloud else 2.5) * 0.5 + funding_score * 0.3 + api_str * 0.2), 2)
    scores["ai_engineering"] = round(min(5.0, (4.5 if has_ai else 1.5) * 0.5 + size_factor * 0.25 + funding_score * 0.25), 2)

    # AI Product & Value
    scores["ai_product_features"] = round(min(5.0, (4.5 if has_ai else 1.2) * 0.7 + mkt_pos * 0.3), 2)
    scores["revenue_ai_upside"] = round(min(5.0, mkt_pos * 0.4 + (3.5 if has_ai else 2.0) * 0.3 + data_rich * 0.3), 2)
    scores["margin_ai_upside"] = round(min(5.0, (3.5 if has_ai else 2.5) * 0.4 + data_rich * 0.3 + (3.0 if cloud else 2.0) * 0.3), 2)
    scores["product_differentiation"] = round(min(5.0, mkt_pos * 0.5 + api_str * 0.3 + data_rich * 0.2), 2)

    # Organization & Talent
    scores["ai_talent_density"] = round(min(5.0, (4.0 if has_ai else 1.5) * 0.5 + size_factor * 0.25 + funding_score * 0.25), 2)
    scores["leadership_ai_vision"] = round(min(5.0, (4.0 if has_ai else 2.0) * 0.5 + mkt_pos * 0.3 + funding_score * 0.2), 2)
    scores["org_change_readiness"] = round(min(5.0, size_factor * 0.3 + (3.5 if cloud else 2.0) * 0.3 + funding_score * 0.4), 2)
    scores["partner_ecosystem"] = round(min(5.0, api_str * 0.5 + mkt_pos * 0.3 + size_factor * 0.2), 2)

    # Governance & Risk
    scores["ai_governance"] = round(min(5.0, (3.5 if is_public else 2.0) * 0.4 + reg_burden * 0.3 + size_factor * 0.3), 2)
    scores["regulatory_readiness"] = round(min(5.0, (3.5 if is_public else 2.0) * 0.3 + reg_burden * 0.4 + size_factor * 0.3), 2)

    # Velocity & Momentum
    scores["ai_momentum"] = round(min(5.0, (4.0 if has_ai else 1.5) * 0.5 + funding_score * 0.25 + mkt_pos * 0.25), 2)

    return scores


# ── Request / response models ─────────────────────────────────────────────────

class SandboxScoreRequest(BaseModel):
    """User just provides a company name — we handle the rest"""
    company_name: str = Field(..., min_length=1, max_length=200)


class SandboxCompanyResponse(BaseModel):
    id: str
    name: str
    vertical: str
    website: Optional[str]
    description: Optional[str]
    employee_count: Optional[int]
    funding_total_usd: Optional[float]
    is_public: bool
    has_ai_features: bool
    cloud_native: bool
    composite_score: float
    tier: str
    wave: int
    pillar_scores: dict
    category_scores: dict
    dimension_details: list
    research_summary: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/score", response_model=SandboxCompanyResponse)
async def score_company(req: SandboxScoreRequest, db: Session = Depends(get_db)):
    """End-to-end pipeline: company name → web research → scoring → tier classification.

    1. Researches the company using Tavily web search
    2. Extracts structured features (employees, funding, AI signals, etc.)
    3. Estimates 17 AI-maturity dimension scores
    4. Computes weighted composite score and tier classification
    5. Saves to database (sandbox, not portfolio)
    """
    # Check for duplicate name first (before hitting external APIs)
    existing = db.query(Company).filter(Company.name == req.company_name).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Company '{req.company_name}' already exists. Check the Sandbox results.")

    settings = get_settings()

    # 1. Web research
    if not settings.tavily_api_key:
        raise HTTPException(status_code=503, detail="Research API not configured")

    logger.info(f"Researching company: {req.company_name}")
    features = await research_company(req.company_name, settings.tavily_api_key)
    research_summary = features.pop("research_summary", "")

    # 2. Create company record
    company = Company(
        name=req.company_name,
        vertical=features["vertical"],
        website=features.get("website"),
        description=research_summary[:500] if research_summary else None,
        founded_year=features.get("founded_year"),
        employee_count=features.get("employee_count"),
        funding_total_usd=features.get("funding_total_usd"),
        is_public=features.get("is_public", False),
        has_ai_features=features.get("has_ai_features", False),
        cloud_native=features.get("cloud_native", False),
        api_ecosystem_strength=features.get("api_ecosystem_strength", 2.5),
        data_richness=features.get("data_richness", 2.5),
        regulatory_burden=features.get("regulatory_burden", 2.5),
        market_position=features.get("market_position", 2.5),
        is_portfolio=False,
    )
    db.add(company)
    db.flush()

    # 3. Estimate dimension scores
    pillar_scores = estimate_dimension_scores(features)

    # 4. Save dimension scores
    for dim, score in pillar_scores.items():
        ds = DimensionScore(company_id=company.id, dimension=dim, score=score)
        db.add(ds)

    # 5. Compute composite + tier + wave
    composite = compute_composite(pillar_scores)
    tier = classify_tier(composite)
    wave = assign_wave(composite)
    cat_scores = compute_category_scores(pillar_scores)

    # 6. Save company score
    cs = CompanyScore(
        company_id=company.id,
        composite_score=composite,
        tier=tier,
        wave=wave,
        pillar_scores=pillar_scores,
        category_scores=cat_scores,
    )
    db.add(cs)
    db.commit()

    # 7. Build response
    dimension_details = []
    for dim, score in sorted(pillar_scores.items(), key=lambda x: x[1], reverse=True):
        cat = next((c for c, ds in CATEGORIES.items() if dim in ds), "Other")
        dimension_details.append({
            "dimension": dim,
            "label": DIMENSION_LABELS.get(dim, dim),
            "score": score,
            "category": cat,
            "weight": DERIVED_WEIGHTS.get(dim, 0),
        })

    return SandboxCompanyResponse(
        id=company.id,
        name=company.name,
        vertical=features["vertical"],
        website=features.get("website"),
        description=research_summary[:500] if research_summary else None,
        employee_count=features.get("employee_count"),
        funding_total_usd=features.get("funding_total_usd"),
        is_public=features.get("is_public", False),
        has_ai_features=features.get("has_ai_features", False),
        cloud_native=features.get("cloud_native", False),
        composite_score=composite,
        tier=tier,
        wave=wave,
        pillar_scores=pillar_scores,
        category_scores=cat_scores,
        dimension_details=dimension_details,
        research_summary=research_summary[:1500],
    )


@router.get("/companies")
async def list_sandbox_companies(db: Session = Depends(get_db)):
    """List all sandbox (non-portfolio) companies that were user-submitted."""
    companies = (
        db.query(Company, CompanyScore)
        .join(CompanyScore, Company.id == CompanyScore.company_id)
        .filter(Company.is_portfolio == False)
        .order_by(Company.created_at.desc())
        .all()
    )

    result = []
    for company, score in companies:
        result.append({
            "id": company.id,
            "name": company.name,
            "vertical": company.vertical,
            "website": company.website,
            "description": company.description,
            "employee_count": company.employee_count,
            "funding_total_usd": company.funding_total_usd,
            "composite_score": score.composite_score,
            "tier": score.tier,
            "wave": score.wave,
            "pillar_scores": score.pillar_scores or {},
            "category_scores": score.category_scores or {},
            "created_at": str(company.created_at),
        })
    return result


@router.delete("/companies/{company_id}")
async def delete_sandbox_company(company_id: str, db: Session = Depends(get_db)):
    """Remove a sandbox company and its scores."""
    company = db.query(Company).filter(Company.id == company_id, Company.is_portfolio == False).first()
    if not company:
        raise HTTPException(status_code=404, detail="Sandbox company not found")

    db.query(DimensionScore).filter(DimensionScore.company_id == company_id).delete()
    db.query(CompanyScore).filter(CompanyScore.company_id == company_id).delete()
    db.query(Company).filter(Company.id == company_id).delete()
    db.commit()
    return {"deleted": True, "name": company.name}
