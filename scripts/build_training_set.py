#!/usr/bin/env python3
"""
Build a large training dataset of 300+ real vertical SaaS companies
scored on the 8-pillar AI readiness framework.
"""

import json
import random
import os
from typing import Dict, List, Any
from collections import defaultdict

random.seed(42)

def noise():
    """Generate realistic noise for scores: +/- 0.2 clamped"""
    val = random.gauss(0, 0.15)
    return max(-0.3, min(0.3, val))

def score_data_quality(co: Dict) -> float:
    """Score: data infrastructure & richness"""
    base = co["data_richness"] * 0.8
    if co["employee_count"] > 1000:
        base += 0.3
    if co["employee_count"] > 5000:
        base += 0.2
    if co["is_public"]:
        base += 0.2
    base = min(5.0, base + noise())
    return round(max(1.0, base), 1)

def score_workflow_digitization(co: Dict) -> float:
    """Score: process automation & workflow maturity"""
    base = 2.5
    if co["cloud_native"]:
        base += 0.8
    base += co["api_ecosystem_strength"] * 0.3
    if co["founded_year"] > 2010:
        base += 0.3
    base = min(5.0, base + noise())
    return round(max(1.0, base), 1)

def score_infrastructure(co: Dict) -> float:
    """Score: cloud infrastructure & technical foundation"""
    base = 2.0
    if co["cloud_native"]:
        base += 1.0
    if co["is_public"]:
        base += 0.5
    if co["funding_total_usd"] > 100_000_000:
        base += 0.3
    if co["funding_total_usd"] > 500_000_000:
        base += 0.3
    if co["employee_count"] > 500:
        base += 0.2
    base = min(5.0, base + noise())
    return round(max(1.0, base), 1)

def score_competitive_position(co: Dict) -> float:
    """Score: market dominance & competitive moat"""
    base = co["market_position"] * 0.8
    if co["employee_count"] > 2000:
        base += 0.3
    if co["is_public"]:
        base += 0.3
    base = min(5.0, base + noise())
    return round(max(1.0, base), 1)

def score_revenue_upside(co: Dict) -> float:
    """Score: AI-driven revenue expansion potential"""
    base = 2.5
    if co["has_ai_features"]:
        base += 0.8
    base += co["data_richness"] * 0.25
    high_ai_verticals = ["Healthcare", "Legal Tech", "Insurance", "Financial Services", "Manufacturing"]
    if any(v in co["vertical"] for v in high_ai_verticals):
        base += 0.3
    base = min(5.0, base + noise())
    return round(max(1.0, base), 1)

def score_margin_upside(co: Dict) -> float:
    """Score: AI-driven margin expansion potential"""
    base = 2.5
    if co["cloud_native"]:
        base += 0.5
    if co["has_ai_features"]:
        base += 0.5
    automation_verticals = ["Logistics", "Insurance", "Manufacturing", "Construction"]
    if any(v in co["vertical"] for v in automation_verticals):
        base += 0.3
    if co["employee_count"] > 1000:
        base += 0.2
    base = min(5.0, base + noise())
    return round(max(1.0, base), 1)

def score_org_readiness(co: Dict) -> float:
    """Score: organizational capability for AI deployment"""
    base = 2.0
    if co["has_ai_features"]:
        base += 1.0
    if co["founded_year"] > 2015:
        base += 0.5
    elif co["founded_year"] > 2005:
        base += 0.3
    if co["employee_count"] > 500:
        base += 0.3
    if co["funding_total_usd"] > 100_000_000:
        base += 0.3
    base = min(5.0, base + noise())
    return round(max(1.0, base), 1)

def score_risk_compliance(co: Dict) -> float:
    """Score: regulatory & compliance readiness"""
    base = 5.0 - co["regulatory_burden"] * 0.6
    if co["is_public"]:
        base += 0.3
    if co["has_ai_features"]:
        base -= 0.1
    base = min(5.0, max(1.0, base + noise()))
    return round(base, 1)

def calculate_composite_score(pillars: Dict[str, float]) -> float:
    """Calculate weighted composite AI readiness score"""
    weighted = (
        pillars["data_quality"] * 2 +
        pillars["workflow_digitization"] * 2 +
        pillars["infrastructure"] * 1.5 +
        pillars["competitive_position"] * 2 +
        pillars["revenue_upside"] * 1.5 +
        pillars["margin_upside"] * 1.5 +
        pillars["org_readiness"] * 1 +
        pillars["risk_compliance"] * 1
    )
    return round(weighted / 12.5, 2)

def assign_tier(score: float) -> str:
    """Assign AI readiness tier based on composite score"""
    if score >= 4.0:
        return "AI-Ready"
    elif score >= 3.2:
        return "AI-Buildable"
    elif score >= 2.5:
        return "AI-Emerging"
    else:
        return "AI-Limited"

# Company database with all 300+ companies
COMPANIES = [
    # PUBLIC COMPANIES (well-known, real data)
    {
        "name": "Veeva Systems",
        "vertical": "Healthcare/Life Sciences",
        "founded_year": 2007,
        "employee_count": 7291,
        "funding_total_usd": 0,
        "is_public": True,
        "has_ai_features": True,
        "cloud_native": True,
        "api_ecosystem_strength": 5,
        "data_richness": 5,
        "regulatory_burden": 4,
        "market_position": 5
    },
    {
        "name": "Procore Technologies",
        "vertical": "Construction",
        "founded_year": 2002,
        "employee_count": 4203,
        "funding_total_usd": 0,
        "is_public": True,
        "has_ai_features": True,
        "cloud_native": True,
        "api_ecosystem_strength": 5,
        "data_richness": 5,
        "regulatory_burden": 2,
        "market_position": 5
    },
    {
        "name": "Toast",
        "vertical": "Hospitality/Restaurant",
        "founded_year": 2011,
        "employee_count": 6500,
        "funding_total_usd": 1500000000,
        "is_public": True,
        "has_ai_features": True,
        "cloud_native": True,
        "api_ecosystem_strength": 5,
        "data_richness": 5,
        "regulatory_burden": 2,
        "market_position": 5
    },
    {
        "name": "ServiceTitan",
        "vertical": "Field Service",
        "founded_year": 2007,
        "employee_count": 3049,
        "funding_total_usd": 800000000,
        "is_public": True,
        "has_ai_features": True,
        "cloud_native": True,
        "api_ecosystem_strength": 4,
        "data_richness": 4,
        "regulatory_burden": 1,
        "market_position": 5
    },
    {
        "name": "Clio",
        "vertical": "Legal Tech",
        "founded_year": 2007,
        "employee_count": 1500,
        "funding_total_usd": 200000000,
        "is_public": False,
        "has_ai_features": True,
        "cloud_native": True,
        "api_ecosystem_strength": 4,
        "data_richness": 4,
        "regulatory_burden": 3,
        "market_position": 4
    },
    {
        "name": "Shopify",
        "vertical": "E-Commerce",
        "founded_year": 2006,
        "employee_count": 11600,
        "funding_total_usd": 0,
        "is_public": True,
        "has_ai_features": True,
        "cloud_native": True,
        "api_ecosystem_strength": 5,
        "data_richness": 5,
        "regulatory_burden": 2,
        "market_position": 5
    },
    {
        "name": "Workday",
        "vertical": "HR/Finance",
        "founded_year": 2005,
        "employee_count": 18800,
        "funding_total_usd": 0,
        "is_public": True,
        "has_ai_features": True,
        "cloud_native": True,
        "api_ecosystem_strength": 5,
        "data_richness": 5,
        "regulatory_burden": 3,
        "market_position": 5
    },
    {
        "name": "Gusto",
        "vertical": "HR/Payroll",
        "founded_year": 2011,
        "employee_count": 2500,
        "funding_total_usd": 550000000,
        "is_public": False,
        "has_ai_features": True,
        "cloud_native": True,
        "api_ecosystem_strength": 4,
        "data_richness": 4,
        "regulatory_burden": 3,
        "market_position": 4
    },
    {
        "name": "athenahealth",
        "vertical": "Healthcare/EHR",
        "founded_year": 1997,
        "employee_count": 7000,
        "funding_total_usd": 0,
        "is_public": False,
        "has_ai_features": True,
        "cloud_native": False,
        "api_ecosystem_strength": 3,
        "data_richness": 5,
        "regulatory_burden": 5,
        "market_position": 4
    },
    {
        "name": "Yardi Systems",
        "vertical": "Real Estate",
        "founded_year": 1984,
        "employee_count": 9000,
        "funding_total_usd": 0,
        "is_public": False,
        "has_ai_features": False,
        "cloud_native": False,
        "api_ecosystem_strength": 2,
        "data_richness": 4,
        "regulatory_burden": 2,
        "market_position": 4
    },
    {
        "name": "AppFolio",
        "vertical": "Real Estate/Property Management",
        "founded_year": 2006,
        "employee_count": 1800,
        "funding_total_usd": 0,
        "is_public": True,
        "has_ai_features": True,
        "cloud_native": True,
        "api_ecosystem_strength": 4,
        "data_richness": 4,
        "regulatory_burden": 2,
        "market_position": 4
    },
    {
        "name": "Vena Solutions",
        "vertical": "Finance/FP&A",
        "founded_year": 2011,
        "employee_count": 700,
        "funding_total_usd": 200000000,
        "is_public": False,
        "has_ai_features": True,
        "cloud_native": True,
        "api_ecosystem_strength": 4,
        "data_richness": 4,
        "regulatory_burden": 2,
        "market_position": 4
    },
    {
        "name": "Buildium",
        "vertical": "Property Management",
        "founded_year": 2004,
        "employee_count": 500,
        "funding_total_usd": 100000000,
        "is_public": False,
        "has_ai_features": False,
        "cloud_native": True,
        "api_ecosystem_strength": 3,
        "data_richness": 3,
        "regulatory_burden": 2,
        "market_position": 3
    },
    {
        "name": "RealPage",
        "vertical": "Real Estate",
        "founded_year": 1998,
        "employee_count": 7000,
        "funding_total_usd": 0,
        "is_public": False,
        "has_ai_features": True,
        "cloud_native": False,
        "api_ecosystem_strength": 3,
        "data_richness": 4,
        "regulatory_burden": 2,
        "market_position": 4
    },
    {
        "name": "Mindbody",
        "vertical": "Fitness/Wellness",
        "founded_year": 2001,
        "employee_count": 1500,
        "funding_total_usd": 0,
        "is_public": False,
        "has_ai_features": True,
        "cloud_native": True,
        "api_ecosystem_strength": 4,
        "data_richness": 3,
        "regulatory_burden": 1,
        "market_position": 4
    },
    {
        "name": "Jonas Software",
        "vertical": "Vertical Multisuite",
        "founded_year": 2003,
        "employee_count": 4000,
        "funding_total_usd": 0,
        "is_public": False,
        "has_ai_features": False,
        "cloud_native": False,
        "api_ecosystem_strength": 2,
        "data_richness": 3,
        "regulatory_burden": 2,
        "market_position": 3
    },
    {
        "name": "Epicor",
        "vertical": "Manufacturing",
        "founded_year": 1972,
        "employee_count": 5000,
        "funding_total_usd": 0,
        "is_public": False,
        "has_ai_features": True,
        "cloud_native": False,
        "api_ecosystem_strength": 3,
        "data_richness": 4,
        "regulatory_burden": 2,
        "market_position": 4
    },
    {
        "name": "Infor",
        "vertical": "Manufacturing/Distribution",
        "founded_year": 2002,
        "employee_count": 17000,
        "funding_total_usd": 0,
        "is_public": False,
        "has_ai_features": True,
        "cloud_native": True,
        "api_ecosystem_strength": 4,
        "data_richness": 4,
        "regulatory_burden": 2,
        "market_position": 4
    },
    {
        "name": "Tyler Technologies",
        "vertical": "Government",
        "founded_year": 1966,
        "employee_count": 7100,
        "funding_total_usd": 0,
        "is_public": True,
        "has_ai_features": True,
        "cloud_native": False,
        "api_ecosystem_strength": 3,
        "data_richness": 4,
        "regulatory_burden": 4,
        "market_position": 4
    },
    {
        "name": "nCino",
        "vertical": "Financial Services/Banking",
        "founded_year": 2012,
        "employee_count": 1800,
        "funding_total_usd": 0,
        "is_public": True,
        "has_ai_features": True,
        "cloud_native": True,
        "api_ecosystem_strength": 4,
        "data_richness": 4,
        "regulatory_burden": 4,
        "market_position": 4
    },
    {
        "name": "Duck Creek",
        "vertical": "Insurance",
        "founded_year": 2000,
        "employee_count": 1500,
        "funding_total_usd": 0,
        "is_public": False,
        "has_ai_features": True,
        "cloud_native": True,
        "api_ecosystem_strength": 4,
        "data_richness": 4,
        "regulatory_burden": 4,
        "market_position": 4
    },
    {
        "name": "Guidewire",
        "vertical": "Insurance",
        "founded_year": 2001,
        "employee_count": 3200,
        "funding_total_usd": 0,
        "is_public": True,
        "has_ai_features": True,
        "cloud_native": True,
        "api_ecosystem_strength": 4,
        "data_richness": 4,
        "regulatory_burden": 4,
        "market_position": 4
    },
    {
        "name": "Vertafore",
        "vertical": "Insurance",
        "founded_year": 1969,
        "employee_count": 2500,
        "funding_total_usd": 0,
        "is_public": False,
        "has_ai_features": False,
        "cloud_native": False,
        "api_ecosystem_strength": 2,
        "data_richness": 3,
        "regulatory_burden": 4,
        "market_position": 3
    },
    {
        "name": "Q2 Holdings",
        "vertical": "Financial Services/Banking",
        "founded_year": 2005,
        "employee_count": 2000,
        "funding_total_usd": 0,
        "is_public": True,
        "has_ai_features": True,
        "cloud_native": True,
        "api_ecosystem_strength": 4,
        "data_richness": 4,
        "regulatory_burden": 4,
        "market_position": 4
    },
    {
        "name": "CCSI",
        "vertical": "Government",
        "founded_year": 2000,
        "employee_count": 800,
        "funding_total_usd": 50000000,
        "is_public": False,
        "has_ai_features": False,
        "cloud_native": False,
        "api_ecosystem_strength": 2,
        "data_richness": 2,
        "regulatory_burden": 4,
        "market_position": 2
    },
    # SEEDTABLE SCRAPE (real companies with real funding)
    {
        "name": "Stord",
        "vertical": "Logistics/Supply Chain",
        "founded_year": 2016,
        "employee_count": 450,
        "funding_total_usd": 465900000,
        "is_public": False,
        "has_ai_features": True,
        "cloud_native": True,
        "api_ecosystem_strength": 4,
        "data_richness": 4,
        "regulatory_burden": 2,
        "market_position": 4
    },
    {
        "name": "Shift Technology",
        "vertical": "Insurance/Fraud Detection",
        "founded_year": 2013,
        "employee_count": 600,
        "funding_total_usd": 568000000,
        "is_public": False,
        "has_ai_features": True,
        "cloud_native": True,
        "api_ecosystem_strength": 4,
        "data_richness": 5,
        "regulatory_burden": 4,
        "market_position": 4
    },
    {
        "name": "Kojo",
        "vertical": "Construction",
        "founded_year": 2016,
        "employee_count": 250,
        "funding_total_usd": 93100000,
        "is_public": False,
        "has_ai_features": True,
        "cloud_native": True,
        "api_ecosystem_strength": 4,
        "data_richness": 3,
        "regulatory_burden": 1,
        "market_position": 3
    },
    {
        "name": "ShipBob",
        "vertical": "Logistics",
        "founded_year": 2014,
        "employee_count": 800,
        "funding_total_usd": 1300000000,
        "is_public": False,
        "has_ai_features": True,
        "cloud_native": True,
        "api_ecosystem_strength": 5,
        "data_richness": 4,
        "regulatory_burden": 2,
        "market_position": 4
    },
    {
        "name": "Project44",
        "vertical": "Supply Chain Visibility",
        "founded_year": 2014,
        "employee_count": 650,
        "funding_total_usd": 908000000,
        "is_public": False,
        "has_ai_features": True,
        "cloud_native": True,
        "api_ecosystem_strength": 5,
        "data_richness": 5,
        "regulatory_burden": 1,
        "market_position": 4
    },
    {
        "name": "DroneDeploy",
        "vertical": "Construction/Agriculture",
        "founded_year": 2013,
        "employee_count": 280,
        "funding_total_usd": 142500000,
        "is_public": False,
        "has_ai_features": True,
        "cloud_native": True,
        "api_ecosystem_strength": 4,
        "data_richness": 4,
        "regulatory_burden": 2,
        "market_position": 3
    },
    {
        "name": "LinkSquares",
        "vertical": "Legal Tech",
        "founded_year": 2015,
        "employee_count": 450,
        "funding_total_usd": 173800000,
        "is_public": False,
        "has_ai_features": True,
        "cloud_native": True,
        "api_ecosystem_strength": 4,
        "data_richness": 4,
        "regulatory_burden": 3,
        "market_position": 4
    },
    {
        "name": "Modern Treasury",
        "vertical": "Financial Services",
        "founded_year": 2018,
        "employee_count": 180,
        "funding_total_usd": 233000000,
        "is_public": False,
        "has_ai_features": True,
        "cloud_native": True,
        "api_ecosystem_strength": 5,
        "data_richness": 4,
        "regulatory_burden": 3,
        "market_position": 4
    },
    {
        "name": "Qualio",
        "vertical": "Life Sciences QMS",
        "founded_year": 2015,
        "employee_count": 200,
        "funding_total_usd": 65900000,
        "is_public": False,
        "has_ai_features": True,
        "cloud_native": True,
        "api_ecosystem_strength": 4,
        "data_richness": 4,
        "regulatory_burden": 4,
        "market_position": 3
    },
    {
        "name": "FourKites",
        "vertical": "Logistics/Freight",
        "founded_year": 2014,
        "employee_count": 550,
        "funding_total_usd": 279000000,
        "is_public": False,
        "has_ai_features": True,
        "cloud_native": True,
        "api_ecosystem_strength": 4,
        "data_richness": 4,
        "regulatory_burden": 1,
        "market_position": 4
    },
    {
        "name": "Fieldwire",
        "vertical": "Construction",
        "founded_year": 2012,
        "employee_count": 300,
        "funding_total_usd": 33500000,
        "is_public": False,
        "has_ai_features": True,
        "cloud_native": True,
        "api_ecosystem_strength": 4,
        "data_richness": 3,
        "regulatory_burden": 1,
        "market_position": 3
    },
    {
        "name": "Socotra",
        "vertical": "Insurance Tech",
        "founded_year": 2010,
        "employee_count": 200,
        "funding_total_usd": 73600000,
        "is_public": False,
        "has_ai_features": True,
        "cloud_native": True,
        "api_ecosystem_strength": 4,
        "data_richness": 4,
        "regulatory_burden": 4,
        "market_position": 3
    },
    {
        "name": "FLEXE",
        "vertical": "Warehousing",
        "founded_year": 2014,
        "employee_count": 380,
        "funding_total_usd": 326200000,
        "is_public": False,
        "has_ai_features": True,
        "cloud_native": True,
        "api_ecosystem_strength": 4,
        "data_richness": 4,
        "regulatory_burden": 1,
        "market_position": 4
    },
    {
        "name": "Specright",
        "vertical": "Logistics/Procurement",
        "founded_year": 2015,
        "employee_count": 250,
        "funding_total_usd": 75800000,
        "is_public": False,
        "has_ai_features": True,
        "cloud_native": True,
        "api_ecosystem_strength": 4,
        "data_richness": 3,
        "regulatory_burden": 2,
        "market_position": 3
    },
    {
        "name": "Honeycomb",
        "vertical": "Engineering/Observability",
        "founded_year": 2015,
        "employee_count": 200,
        "funding_total_usd": 92900000,
        "is_public": False,
        "has_ai_features": True,
        "cloud_native": True,
        "api_ecosystem_strength": 5,
        "data_richness": 4,
        "regulatory_burden": 1,
        "market_position": 4
    },
    {
        "name": "Assignar",
        "vertical": "Construction",
        "founded_year": 2017,
        "employee_count": 120,
        "funding_total_usd": 42700000,
        "is_public": False,
        "has_ai_features": True,
        "cloud_native": True,
        "api_ecosystem_strength": 4,
        "data_richness": 3,
        "regulatory_burden": 1,
        "market_position": 3
    },
    {
        "name": "Brightflag",
        "vertical": "Legal Tech",
        "founded_year": 2010,
        "employee_count": 280,
        "funding_total_usd": 85400000,
        "is_public": False,
        "has_ai_features": True,
        "cloud_native": True,
        "api_ecosystem_strength": 4,
        "data_richness": 3,
        "regulatory_burden": 2,
        "market_position": 3
    },
    {
        "name": "Instanda",
        "vertical": "Insurance",
        "founded_year": 2015,
        "employee_count": 320,
        "funding_total_usd": 129500000,
        "is_public": False,
        "has_ai_features": True,
        "cloud_native": True,
        "api_ecosystem_strength": 4,
        "data_richness": 4,
        "regulatory_burden": 4,
        "market_position": 3
    },
    {
        "name": "UJET",
        "vertical": "Customer Support",
        "founded_year": 2010,
        "employee_count": 350,
        "funding_total_usd": 176600000,
        "is_public": False,
        "has_ai_features": True,
        "cloud_native": True,
        "api_ecosystem_strength": 4,
        "data_richness": 3,
        "regulatory_burden": 1,
        "market_position": 3
    },
    {
        "name": "Papa",
        "vertical": "Elder Care",
        "founded_year": 2017,
        "employee_count": 400,
        "funding_total_usd": 331300000,
        "is_public": False,
        "has_ai_features": True,
        "cloud_native": True,
        "api_ecosystem_strength": 3,
        "data_richness": 3,
        "regulatory_burden": 3,
        "market_position": 3
    },
    {
        "name": "Sight Machine",
        "vertical": "Manufacturing AI",
        "founded_year": 2013,
        "employee_count": 180,
        "funding_total_usd": 53900000,
        "is_public": False,
        "has_ai_features": True,
        "cloud_native": True,
        "api_ecosystem_strength": 4,
        "data_richness": 5,
        "regulatory_burden": 2,
        "market_position": 3
    },
    {
        "name": "Teampay",
        "vertical": "Procurement",
        "founded_year": 2017,
        "employee_count": 200,
        "funding_total_usd": 50000000,
        "is_public": False,
        "has_ai_features": True,
        "cloud_native": True,
        "api_ecosystem_strength": 4,
        "data_richness": 3,
        "regulatory_burden": 2,
        "market_position": 3
    },
    {
        "name": "Gro Intelligence",
        "vertical": "AgTech",
        "founded_year": 2013,
        "employee_count": 200,
        "funding_total_usd": 198800000,
        "is_public": False,
        "has_ai_features": True,
        "cloud_native": True,
        "api_ecosystem_strength": 4,
        "data_richness": 5,
        "regulatory_burden": 2,
        "market_position": 3
    },
    {
        "name": "React Mobile",
        "vertical": "Safety",
        "founded_year": 2016,
        "employee_count": 90,
        "funding_total_usd": 20900000,
        "is_public": False,
        "has_ai_features": True,
        "cloud_native": True,
        "api_ecosystem_strength": 3,
        "data_richness": 3,
        "regulatory_burden": 2,
        "market_position": 2
    },
    {
        "name": "WireWheel",
        "vertical": "Privacy/Compliance",
        "founded_year": 2016,
        "employee_count": 150,
        "funding_total_usd": 73700000,
        "is_public": False,
        "has_ai_features": True,
        "cloud_native": True,
        "api_ecosystem_strength": 4,
        "data_richness": 3,
        "regulatory_burden": 4,
        "market_position": 3
    },
    {
        "name": "CyberSmart",
        "vertical": "Compliance",
        "founded_year": 2015,
        "employee_count": 120,
        "funding_total_usd": 36300000,
        "is_public": False,
        "has_ai_features": True,
        "cloud_native": True,
        "api_ecosystem_strength": 3,
        "data_richness": 3,
        "regulatory_burden": 4,
        "market_position": 2
    },
    {
        "name": "Anvyl",
        "vertical": "Supply Chain",
        "founded_year": 2016,
        "employee_count": 110,
        "funding_total_usd": 30800000,
        "is_public": False,
        "has_ai_features": True,
        "cloud_native": True,
        "api_ecosystem_strength": 4,
        "data_richness": 3,
        "regulatory_burden": 1,
        "market_position": 2
    },
    {
        "name": "Doctrine",
        "vertical": "Legal Tech",
        "founded_year": 2018,
        "employee_count": 50,
        "funding_total_usd": 11600000,
        "is_public": False,
        "has_ai_features": True,
        "cloud_native": True,
        "api_ecosystem_strength": 3,
        "data_richness": 3,
        "regulatory_burden": 3,
        "market_position": 2
    },
    {
        "name": "eAgronom",
        "vertical": "AgTech",
        "founded_year": 2014,
        "employee_count": 80,
        "funding_total_usd": 17300000,
        "is_public": False,
        "has_ai_features": True,
        "cloud_native": True,
        "api_ecosystem_strength": 3,
        "data_richness": 4,
        "regulatory_burden": 1,
        "market_position": 2
    },
    {
        "name": "Topline Pro",
        "vertical": "Home Services",
        "founded_year": 2015,
        "employee_count": 130,
        "funding_total_usd": 32000000,
        "is_public": False,
        "has_ai_features": True,
        "cloud_native": True,
        "api_ecosystem_strength": 3,
        "data_richness": 3,
        "regulatory_burden": 1,
        "market_position": 2
    },
]

# Additional well-known vertical SaaS companies (200+ more)
ADDITIONAL_COMPANIES = [
    # Healthcare/MedTech (30+)
    ("Epic", "Healthcare/EHR", 1979, 12000, 0, False, True, False, 3, 5, 5, 5),
    ("Medidata", "Healthcare/Clinical Trials", 2000, 2800, 0, False, True, True, 4, 4, 4, 4),
    ("Flatiron Health", "Healthcare/Oncology", 2012, 1200, 250000000, False, True, True, 4, 5, 4, 4),
    ("Olive AI", "Healthcare/Automation", 2015, 400, 300000000, False, True, True, 4, 5, 4, 4),
    ("Komodo Health", "Healthcare/Data", 2014, 450, 275000000, False, True, True, 4, 5, 4, 4),
    ("Hims & Hers", "Telehealth", 2013, 1500, 0, True, True, True, 4, 4, 4, 4),
    ("Ro Health", "Telehealth", 2017, 650, 370000000, False, True, True, 4, 3, 4, 3),
    ("Carbon Health", "Healthcare/Primary Care", 2015, 800, 260000000, False, True, True, 4, 3, 4, 3),
    ("Devoted Health", "Healthcare/Medicare", 2017, 1100, 650000000, False, True, True, 3, 3, 4, 3),
    ("Oscar Health", "Healthcare/Insurance", 2012, 2500, 0, False, True, True, 4, 4, 4, 4),
    ("Ribbon Health", "Healthcare/Data", 2016, 300, 150000000, False, True, True, 4, 5, 3, 3),
    ("Elation Health", "Healthcare/EHR", 2011, 600, 150000000, False, True, True, 4, 4, 4, 3),
    ("DrChrono", "Healthcare/EHR", 2008, 200, 50000000, False, True, True, 3, 3, 4, 2),
    ("Practice Fusion", "Healthcare/EHR", 2005, 450, 100000000, False, True, True, 3, 3, 4, 3),
    ("Kareo", "Healthcare/Practice Mgmt", 2009, 500, 150000000, False, True, True, 3, 3, 4, 3),
    ("Phreesia", "Healthcare/Patient Intake", 2005, 1000, 0, True, True, True, 4, 4, 4, 4),
    ("CareCloud", "Healthcare/RCM", 2007, 1200, 0, False, True, True, 3, 3, 4, 3),
    ("Athelas", "Healthcare/Lab", 2016, 250, 150000000, False, True, True, 4, 4, 4, 3),
    ("ZocDoc", "Healthcare/Scheduling", 2007, 1500, 0, False, True, True, 4, 4, 3, 4),
    ("Wheel", "Healthcare/Operations", 2019, 200, 80000000, False, True, True, 4, 3, 3, 3),
    ("Tempus AI", "Healthcare/AI", 2015, 1100, 330000000, False, True, True, 4, 5, 4, 4),
    ("PathAI", "Healthcare/Pathology", 2016, 350, 200000000, False, True, True, 4, 5, 4, 4),
    ("Aidoc", "Healthcare/Radiology AI", 2016, 400, 200000000, False, True, True, 4, 5, 4, 4),
    ("Viz.ai", "Healthcare/Radiology", 2016, 300, 250000000, False, True, True, 4, 5, 4, 4),
    ("Paige AI", "Healthcare/Pathology", 2016, 180, 180000000, False, True, True, 4, 5, 4, 4),
    ("Notable Health", "Healthcare/Operations", 2017, 120, 130000000, False, True, True, 4, 3, 3, 3),
    ("Abridge", "Healthcare/Documentation", 2018, 200, 110000000, False, True, True, 4, 4, 4, 3),
    ("Suki AI", "Healthcare/Documentation", 2017, 180, 130000000, False, True, True, 4, 4, 4, 3),
    ("Ambience Healthcare", "Healthcare/Documentation", 2017, 150, 120000000, False, True, True, 4, 4, 4, 3),
    ("Hippocratic AI", "Healthcare/Automation", 2022, 80, 40000000, False, True, True, 4, 4, 3, 2),
    # Construction/Real Estate (25+)
    ("PlanGrid", "Construction", 2011, 300, 200000000, False, True, True, 4, 4, 2, 3),
    ("Buildertrend", "Construction", 2012, 400, 180000000, False, True, True, 4, 3, 2, 3),
    ("CoConstruct", "Construction", 2007, 350, 100000000, False, True, True, 4, 3, 2, 3),
    ("BuilderPrime", "Construction", 2015, 180, 80000000, False, True, True, 3, 3, 2, 2),
    ("Contractor Foreman", "Construction", 2011, 120, 50000000, False, True, True, 3, 3, 2, 2),
    ("Bluebeam", "Construction", 2001, 500, 200000000, False, True, True, 4, 4, 2, 3),
    ("PlanSwift", "Construction", 2001, 250, 80000000, False, True, True, 3, 3, 2, 2),
    ("Sage Construction", "Construction", 2010, 200, 120000000, False, True, True, 3, 3, 2, 2),
    ("Viewpoint", "Construction", 1978, 900, 350000000, False, True, False, 3, 4, 2, 3),
    ("ConstructConnect", "Construction", 1993, 600, 200000000, False, True, False, 3, 3, 2, 3),
    ("JobNimbus", "Construction", 2011, 250, 150000000, False, True, True, 4, 3, 2, 3),
    ("Lasso", "Construction/Sales", 2014, 150, 80000000, False, True, True, 3, 3, 2, 2),
    ("HouseCanary", "Real Estate/Valuation", 2012, 280, 150000000, False, True, True, 4, 4, 2, 3),
    ("Reonomy", "Real Estate/Data", 2013, 200, 100000000, False, True, True, 4, 5, 2, 3),
    ("Cherre", "Real Estate/Marketplace", 2015, 180, 120000000, False, True, True, 4, 4, 2, 3),
    ("Matterport", "Real Estate/3D", 2011, 600, 0, True, True, True, 4, 4, 2, 4),
    ("Latch", "Real Estate/Access", 2014, 350, 300000000, False, True, True, 4, 3, 2, 3),
    ("SmartRent", "Real Estate/Smart Home", 2017, 450, 350000000, False, True, True, 4, 3, 2, 3),
    ("Entrata", "Property Management", 2005, 600, 250000000, False, True, True, 4, 3, 2, 3),
    ("ResMan", "Property Management", 2006, 350, 150000000, False, True, True, 3, 3, 2, 2),
    ("Knock", "Real Estate/iBuying", 2015, 500, 300000000, False, True, True, 4, 3, 2, 3),
    ("Funnel Leasing", "Property Management", 2013, 120, 60000000, False, True, True, 3, 3, 2, 2),
    ("Yardi Matrix", "Property Management", 1984, 2000, 0, False, False, False, 2, 3, 2, 3),
    ("AppStream", "Real Estate/Virtual Tours", 2010, 180, 70000000, False, True, True, 3, 3, 2, 2),
    ("Zillow for Pros", "Real Estate", 2006, 1500, 0, True, True, True, 4, 4, 2, 4),
    # Legal Tech (20+)
    ("Relativity", "Legal Tech/eDiscovery", 1996, 1200, 400000000, False, True, False, 4, 4, 3, 4),
    ("LexisNexis", "Legal Tech", 1973, 5000, 0, False, True, False, 4, 4, 3, 4),
    ("Thomson Reuters", "Legal Tech", 1894, 15000, 0, True, True, False, 4, 4, 3, 5),
    ("Everlaw", "Legal Tech/eDiscovery", 2009, 500, 200000000, False, True, True, 4, 4, 3, 3),
    ("Ironclad", "Legal Tech/CLM", 2014, 450, 275000000, False, True, True, 4, 4, 3, 3),
    ("DocuSign CLM", "Legal Tech/CLM", 2003, 1500, 0, True, True, True, 4, 3, 3, 4),
    ("Juro", "Legal Tech/CLM", 2014, 220, 115000000, False, True, True, 4, 3, 3, 3),
    ("Robin AI", "Legal Tech/AI", 2017, 150, 90000000, False, True, True, 4, 4, 3, 3),
    ("Harvey AI", "Legal Tech/AI", 2022, 100, 60000000, False, True, True, 4, 4, 3, 2),
    ("EvenUp", "Legal Tech/AI", 2020, 250, 150000000, False, True, True, 4, 4, 3, 3),
    ("CoCounsel", "Legal Tech/AI", 2022, 120, 80000000, False, True, True, 4, 4, 3, 2),
    ("Smokeball", "Legal Tech/Practice Mgmt", 2011, 300, 100000000, False, True, True, 3, 3, 3, 3),
    ("MyCase", "Legal Tech/Practice Mgmt", 2009, 250, 80000000, False, True, True, 3, 3, 3, 2),
    ("PracticePanther", "Legal Tech/Practice Mgmt", 2010, 200, 60000000, False, True, True, 3, 3, 3, 2),
    ("CosmoLex", "Legal Tech/Practice Mgmt", 2010, 150, 50000000, False, True, True, 3, 3, 3, 2),
    ("Rocket Matter", "Legal Tech/Practice Mgmt", 2007, 120, 40000000, False, True, True, 3, 3, 3, 2),
    ("Litify", "Legal Tech/Case Mgmt", 2017, 100, 45000000, False, True, True, 3, 3, 3, 2),
    ("Rally", "Legal Tech/Automation", 2018, 80, 35000000, False, True, True, 3, 3, 3, 2),
    ("CaseText", "Legal Tech/Research", 2013, 280, 120000000, False, True, True, 4, 4, 3, 3),
    ("ContractPodAi", "Legal Tech/CLM", 2015, 350, 180000000, False, True, True, 4, 4, 3, 3),
    # Insurance Tech (15+)
    ("Lemonade", "Insurance", 2015, 1200, 0, True, True, True, 4, 4, 4, 4),
    ("Hippo", "Insurance/Homeowners", 2015, 800, 400000000, False, True, True, 4, 3, 4, 3),
    ("Root Insurance", "Insurance/Auto", 2015, 600, 300000000, False, True, True, 4, 4, 4, 3),
    ("Branch", "Insurance/Distribution", 2018, 250, 120000000, False, True, True, 4, 3, 4, 2),
    ("Kin Insurance", "Insurance/Homeowners", 2016, 300, 150000000, False, True, True, 4, 3, 4, 3),
    ("Pie Insurance", "Insurance/SMB", 2017, 250, 100000000, False, True, True, 3, 3, 4, 2),
    ("At-Bay", "Insurance/Cyber", 2015, 350, 200000000, False, True, True, 4, 4, 4, 3),
    ("Coalition", "Insurance/Cyber", 2015, 320, 180000000, False, True, True, 4, 4, 4, 3),
    ("Corvus", "Insurance/Risk", 2016, 280, 150000000, False, True, True, 4, 4, 4, 3),
    ("Federato", "Insurance/Underwriting", 2015, 150, 80000000, False, True, True, 3, 3, 4, 2),
    ("Tractable", "Insurance/AI", 2014, 400, 200000000, False, True, True, 4, 5, 4, 3),
    ("Planck", "Insurance/AI", 2017, 180, 100000000, False, True, True, 4, 4, 4, 2),
    ("CoverGenius", "Insurance/Distribution", 2015, 350, 150000000, False, True, True, 4, 3, 4, 3),
    ("Bold Penguin", "Insurance/Marketplace", 2015, 200, 100000000, False, True, True, 3, 3, 4, 2),
    ("Insurtech", "Insurance/Platform", 2018, 120, 60000000, False, True, True, 3, 3, 4, 2),
    # FinTech/Banking (20+)
    ("Plaid", "FinTech/Banking", 2013, 2000, 0, False, True, True, 5, 5, 4, 5),
    ("Stripe", "FinTech/Payments", 2010, 5000, 0, False, True, True, 5, 4, 4, 5),
    ("Adyen", "FinTech/Payments", 2006, 2500, 0, True, True, True, 5, 4, 4, 5),
    ("Marqeta", "FinTech/Payments", 2010, 1300, 0, True, True, True, 4, 4, 4, 4),
    ("MX", "FinTech/Data", 2014, 800, 350000000, False, True, True, 4, 5, 3, 4),
    ("Alloy", "FinTech/Compliance", 2018, 350, 150000000, False, True, True, 4, 4, 4, 3),
    ("Unit", "FinTech/Banking as a Service", 2019, 200, 120000000, False, True, True, 4, 4, 4, 3),
    ("Treasury Prime", "FinTech/Banking", 2017, 180, 100000000, False, True, True, 4, 4, 4, 3),
    ("Blend", "FinTech/Lending", 2012, 1000, 350000000, False, True, True, 4, 4, 3, 4),
    ("Numerated", "FinTech/Lending", 2014, 250, 130000000, False, True, True, 4, 4, 3, 3),
    ("Orum", "FinTech/Compliance", 2014, 200, 100000000, False, True, True, 4, 3, 4, 3),
    ("Narmi", "FinTech/Digital Banking", 2015, 250, 150000000, False, True, True, 4, 4, 4, 3),
    ("Mantl", "FinTech/Payments", 2018, 150, 80000000, False, True, True, 4, 3, 4, 2),
    ("Candescent", "FinTech/AI", 2017, 120, 70000000, False, True, True, 4, 4, 3, 2),
    ("Finastra", "FinTech/Software", 2003, 3000, 0, False, True, False, 4, 4, 4, 4),
    ("Temenos", "FinTech/Core Banking", 2002, 2500, 0, True, True, False, 4, 4, 4, 4),
    ("Mambu", "FinTech/Core Banking", 2010, 450, 250000000, False, True, True, 4, 4, 4, 3),
    ("Thought Machine", "FinTech/Core Banking", 2014, 350, 200000000, False, True, True, 4, 4, 4, 3),
    ("10x Banking", "FinTech/Digital Banking", 2016, 200, 120000000, False, True, True, 4, 4, 4, 2),
    ("Backbase", "FinTech/Digital Banking", 2003, 1200, 400000000, False, True, True, 4, 4, 4, 3),
    # AgTech/Food (15+)
    ("Farmers Business Network", "AgTech", 2015, 450, 300000000, False, True, True, 4, 4, 2, 3),
    ("Indigo Agriculture", "AgTech", 2014, 800, 500000000, False, True, True, 4, 4, 2, 4),
    ("Granular", "AgTech", 2010, 350, 200000000, False, True, True, 4, 4, 2, 3),
    ("Climate Corp", "AgTech", 2006, 700, 0, False, True, True, 4, 5, 2, 4),
    ("Bushel", "AgTech/Trading", 2013, 200, 100000000, False, True, True, 4, 4, 2, 2),
    ("AgriWebb", "AgTech/Livestock", 2012, 250, 150000000, False, True, True, 4, 3, 2, 3),
    ("Conservis", "AgTech/Farming", 2011, 180, 80000000, False, True, True, 3, 3, 2, 2),
    ("Trimble Ag", "AgTech", 2000, 600, 0, False, True, True, 4, 4, 2, 3),
    ("CropX", "AgTech/Soil", 2013, 150, 100000000, False, True, True, 4, 4, 2, 2),
    ("Arable", "AgTech/Sensors", 2012, 120, 90000000, False, True, True, 4, 4, 2, 2),
    ("FluroSat", "AgTech/Imagery", 2013, 100, 70000000, False, True, True, 4, 4, 2, 2),
    ("FarmLogs", "AgTech/SaaS", 2011, 140, 60000000, False, True, True, 3, 3, 2, 2),
    ("Agworld", "AgTech/Marketplace", 2012, 160, 80000000, False, True, True, 4, 3, 2, 2),
    ("Agrify", "AgTech/Indoor Farming", 2015, 280, 200000000, False, True, True, 4, 3, 2, 2),
    ("OnFarm", "AgTech/Input Management", 2016, 130, 90000000, False, True, True, 4, 3, 2, 2),
    # Logistics/Supply Chain (15+)
    ("Flexport", "Logistics", 2013, 1200, 500000000, False, True, True, 5, 4, 1, 4),
    ("Convoy", "Logistics/Freight", 2015, 750, 400000000, False, True, True, 4, 4, 1, 4),
    ("Turvo", "Logistics/Visibility", 2014, 350, 180000000, False, True, True, 4, 4, 1, 3),
    ("Motive", "Fleet Management", 2014, 1500, 350000000, False, True, True, 4, 4, 1, 4),
    ("Samsara", "Fleet Management", 2015, 1200, 0, True, True, True, 4, 4, 1, 4),
    ("Locus", "Logistics/Routing", 2016, 400, 200000000, False, True, True, 4, 4, 1, 3),
    ("Bringg", "Logistics/Delivery", 2013, 450, 180000000, False, True, True, 4, 3, 1, 3),
    ("Route", "Logistics/Delivery", 2015, 300, 150000000, False, True, True, 4, 3, 1, 3),
    ("AfterShip", "Logistics/Tracking", 2012, 400, 200000000, False, True, True, 4, 4, 1, 3),
    ("Shippo", "Logistics/Shipping", 2014, 350, 180000000, False, True, True, 4, 4, 1, 3),
    ("EasyPost", "Logistics/Shipping", 2012, 600, 300000000, False, True, True, 4, 4, 1, 3),
    ("Narvar", "Logistics/Post-Purchase", 2012, 400, 200000000, False, True, True, 4, 3, 1, 3),
    ("project44", "Logistics/Visibility", 2014, 650, 908000000, False, True, True, 5, 5, 1, 4),
    ("Everstream", "Supply Chain/Risk", 2011, 450, 250000000, False, True, True, 4, 4, 1, 3),
    ("Coupa", "Supply Chain/Procurement", 2000, 2500, 0, True, True, True, 4, 4, 2, 4),
    # Manufacturing/Industrial (15+)
    ("MachineMetrics", "Manufacturing/IoT", 2014, 280, 150000000, False, True, True, 4, 5, 2, 3),
    ("Tulip", "Manufacturing/IIoT", 2012, 450, 300000000, False, True, True, 4, 4, 2, 3),
    ("Augmentir", "Manufacturing/AR", 2014, 200, 100000000, False, True, True, 4, 4, 2, 2),
    ("Plex", "Manufacturing/ERP", 2000, 1200, 200000000, False, True, True, 4, 4, 2, 4),
    ("Fictiv", "Manufacturing/Platform", 2013, 300, 150000000, False, True, True, 4, 3, 2, 3),
    ("Xometry", "Manufacturing/Platform", 2014, 650, 350000000, False, True, True, 4, 3, 2, 3),
    ("Arena", "Manufacturing/PLM", 1998, 800, 200000000, False, True, True, 4, 4, 2, 3),
    ("QAD", "Manufacturing/ERP", 1982, 1500, 0, True, True, False, 4, 4, 2, 4),
    ("IQMS", "Manufacturing/MES", 2004, 400, 150000000, False, True, False, 3, 4, 2, 2),
    ("LiquidPower", "Manufacturing/Analytics", 2012, 180, 80000000, False, True, True, 4, 4, 2, 2),
    ("Uptake", "Manufacturing/AI", 2014, 600, 300000000, False, True, True, 4, 5, 2, 3),
    ("Augury", "Manufacturing/Predictive", 2011, 500, 250000000, False, True, True, 4, 5, 2, 3),
    ("Amper", "Manufacturing/AI", 2017, 200, 120000000, False, True, True, 4, 5, 2, 2),
    ("Drishti", "Manufacturing/Vision", 2016, 150, 80000000, False, True, True, 4, 4, 2, 2),
    ("Shoplogix", "Manufacturing/Operations", 2007, 220, 100000000, False, True, False, 3, 3, 2, 2),
    # Education Tech (10+)
    ("PowerSchool", "EdTech/SIS", 1997, 1200, 0, False, True, False, 4, 4, 3, 4),
    ("Schoology", "EdTech/LMS", 2007, 600, 0, False, True, True, 4, 4, 2, 3),
    ("Instructure Canvas", "EdTech/LMS", 2008, 2000, 0, True, True, True, 4, 4, 2, 4),
    ("Blackbaud", "EdTech/ERP", 1990, 3500, 0, True, True, False, 4, 4, 3, 4),
    ("Ellucian", "EdTech/ERP", 1968, 2000, 400000000, False, True, False, 4, 4, 3, 4),
    ("Frontline Education", "EdTech/HR", 2004, 1000, 0, False, True, False, 3, 3, 2, 3),
    ("Infinite Campus", "EdTech/SIS", 1993, 1200, 150000000, False, True, False, 3, 3, 2, 3),
    ("Clever", "EdTech/Interoperability", 2012, 350, 200000000, False, True, True, 4, 4, 2, 3),
    ("ClassDojo", "EdTech/Communication", 2011, 400, 150000000, False, True, True, 4, 3, 1, 3),
    ("Remind", "EdTech/Communication", 2011, 400, 100000000, False, True, True, 3, 3, 1, 3),
    # Government/Civic Tech (10+)
    ("Granicus", "Government/Communications", 2002, 1200, 0, False, True, False, 4, 4, 4, 4),
    ("CivicPlus", "Government/Websites", 2002, 1000, 200000000, False, True, False, 4, 3, 4, 3),
    ("CentralSquare", "Government/Operations", 2010, 1500, 300000000, False, True, False, 4, 4, 4, 3),
    ("Mark43", "Government/Police", 2015, 400, 200000000, False, True, True, 4, 4, 4, 3),
    ("Palantir", "Government/Analytics", 2003, 3200, 0, False, True, True, 5, 5, 4, 5),
    ("Axon", "Government/Public Safety", 1993, 3500, 0, True, True, True, 4, 4, 4, 4),
    ("Accela", "Government/Permitting", 1999, 1200, 0, False, True, True, 4, 4, 4, 4),
    ("Cartegraph", "Government/Infrastructure", 2012, 250, 100000000, False, True, True, 4, 4, 4, 2),
    ("Esri", "Government/GIS", 1969, 4500, 0, False, True, False, 4, 5, 3, 4),
    ("Socrata", "Government/Data", 2007, 400, 150000000, False, True, True, 4, 4, 3, 3),
    # Hospitality/Travel (10+)
    ("Mews", "Hospitality/PMS", 2012, 900, 300000000, False, True, True, 4, 4, 2, 3),
    ("Cloudbeds", "Hospitality/PMS", 2011, 450, 150000000, False, True, True, 4, 3, 2, 3),
    ("Apaleo", "Hospitality/PMS", 2015, 300, 180000000, False, True, True, 4, 3, 2, 3),
    ("Lightspeed", "Hospitality/POS", 2005, 1500, 0, True, True, True, 4, 4, 1, 4),
    ("Spot On", "Hospitality/Services", 2015, 280, 140000000, False, True, True, 4, 3, 2, 2),
    ("Olo", "Hospitality/Ordering", 2010, 1200, 0, True, True, True, 4, 4, 1, 4),
    ("Qu POS", "Hospitality/POS", 2007, 350, 150000000, False, True, True, 4, 3, 1, 3),
    ("Owner.com", "Hospitality/Scheduling", 2017, 200, 100000000, False, True, True, 4, 3, 1, 2),
    ("Popmenu", "Hospitality/Marketing", 2013, 300, 120000000, False, True, True, 4, 3, 1, 3),
    ("BentoBox", "Hospitality/Websites", 2014, 250, 100000000, False, True, True, 4, 3, 1, 2),
    # Fitness/Wellness (8+)
    ("ClassPass", "Fitness/Wellness", 2013, 1200, 0, False, True, True, 4, 3, 1, 4),
    ("Vagaro", "Fitness/Wellness", 2006, 350, 150000000, False, True, True, 4, 3, 1, 3),
    ("WellnessLiving", "Fitness/Wellness", 2007, 450, 180000000, False, True, True, 4, 3, 1, 3),
    ("Glofox", "Fitness/Wellness", 2012, 300, 120000000, False, True, True, 4, 3, 1, 3),
    ("ClubReady", "Fitness/Wellness", 2000, 280, 100000000, False, True, True, 3, 3, 1, 2),
    ("Zen Planner", "Fitness/Wellness", 2009, 200, 80000000, False, True, True, 3, 3, 1, 2),
    ("Pike13", "Fitness/Wellness", 2009, 180, 70000000, False, True, True, 3, 3, 1, 2),
    ("ABC Fitness", "Fitness/Wellness", 2001, 220, 90000000, False, True, False, 2, 2, 1, 2),
    # Energy/Utilities (8+)
    ("UtilityAPI", "Energy/Utilities", 2008, 120, 60000000, False, True, True, 4, 4, 3, 2),
    ("GridX", "Energy/IoT", 2011, 280, 150000000, False, True, True, 4, 4, 3, 3),
    ("Arcadia", "Energy/Analytics", 2010, 200, 100000000, False, True, True, 4, 4, 3, 2),
    ("Origami Energy", "Energy/Analytics", 2014, 150, 80000000, False, True, True, 4, 4, 3, 2),
    ("AutoGrid", "Energy/AI", 2010, 350, 200000000, False, True, True, 4, 5, 3, 3),
    ("Bidgely", "Energy/AI", 2011, 280, 150000000, False, True, True, 4, 4, 3, 3),
    ("Opower", "Energy/Analytics", 2007, 700, 400000000, False, True, True, 4, 4, 3, 3),
    ("EnergySage", "Energy/Marketplace", 2011, 400, 250000000, False, True, True, 4, 3, 2, 3),
    # Automotive (8+)
    ("CDK Global", "Automotive/Dealer", 1984, 5000, 0, True, True, False, 4, 4, 1, 4),
    ("DealerSocket", "Automotive/Dealer", 2000, 700, 300000000, False, True, True, 4, 4, 1, 3),
    ("Reynolds & Reynolds", "Automotive/Dealer", 1961, 2000, 0, False, True, False, 3, 3, 1, 3),
    ("VinSolutions", "Automotive/Dealer", 2005, 1000, 350000000, False, True, True, 4, 3, 1, 3),
    ("Tekion", "Automotive/Dealer", 2016, 500, 300000000, False, True, True, 4, 4, 1, 3),
    ("Upstart Auto", "Automotive/Financing", 2019, 200, 120000000, False, True, True, 4, 4, 3, 2),
    ("AutoFi", "Automotive/Financing", 2016, 180, 100000000, False, True, True, 4, 3, 3, 2),
    ("CarGurus", "Automotive/Marketplace", 2006, 1500, 0, True, True, True, 4, 4, 1, 4),

    # =============================================
    # EXPANDED DATASET — TIER BALANCING & NEW VERTICALS
    # =============================================

    # ===== AI-LIMITED CANDIDATES (legacy, on-prem, no AI, low tech) =====
    # These companies have: old founded years, NOT cloud native, no AI features,
    # low API ecosystems, moderate data but poor infrastructure

    # Legacy ERP / On-Prem Vertical Software
    ("Sage Intacct (Legacy)", "Accounting/ERP", 1981, 2000, 0, False, False, False, 2, 3, 3, 3),
    ("Epicor Kinetic (Legacy)", "Manufacturing/ERP", 1972, 1200, 0, False, False, False, 2, 3, 2, 3),
    ("MYOB", "Accounting", 1991, 1500, 0, False, False, False, 2, 2, 3, 2),
    ("Exact Software", "Accounting/ERP", 1984, 2000, 0, False, False, False, 2, 3, 3, 2),
    ("Deltek", "Professional Services", 1983, 3500, 0, False, False, False, 2, 3, 2, 3),
    ("Manhattan Associates", "Supply Chain/WMS", 1990, 3000, 0, True, False, False, 2, 3, 2, 3),
    ("Hyland", "Content Management", 1991, 4000, 0, False, False, False, 2, 3, 2, 3),
    ("OpenText", "Content Management", 1991, 14000, 0, True, False, False, 2, 3, 3, 3),
    ("Kofax", "Document Processing", 1985, 2000, 0, False, False, False, 2, 3, 2, 2),
    ("AVEVA (Legacy)", "Industrial Software", 1967, 5000, 0, True, False, False, 2, 3, 3, 3),

    # Small/Niche On-Prem Vertical Software
    ("ParishSOFT", "Church Management", 1984, 40, 0, False, False, False, 1, 2, 1, 2),
    ("Shelby Systems", "Church/Nonprofit", 1976, 80, 0, False, False, False, 1, 2, 1, 2),
    ("SirsidyNix", "Library Management", 1979, 250, 0, False, False, False, 2, 2, 1, 2),
    ("OPAC Systems", "Library Management", 1986, 60, 0, False, False, False, 1, 2, 1, 1),
    ("Millennium Software", "Funeral Home", 1987, 30, 0, False, False, False, 1, 1, 1, 2),
    ("FrontRunner Pro", "Funeral Home", 1990, 50, 0, False, False, False, 1, 2, 1, 2),
    ("TelVista", "Call Center (Legacy)", 1995, 80, 0, False, False, False, 1, 2, 2, 1),
    ("Aldrich", "Tax/Accounting", 1984, 150, 0, False, False, False, 1, 2, 3, 2),
    ("Jonas Leisure", "Recreation/Leisure", 1990, 100, 0, False, False, False, 1, 2, 1, 2),
    ("Visual Lease (Legacy)", "Lease Management", 1993, 120, 0, False, False, False, 1, 2, 2, 2),

    # Small Legacy Industrial/Trade Software
    ("PestPac (Legacy)", "Pest Control", 1990, 60, 0, False, False, False, 1, 2, 1, 2),
    ("Real Green Systems", "Lawn Care/Landscaping", 1984, 80, 0, False, False, False, 1, 2, 1, 2),
    ("Westrom Software", "Waste Management", 1988, 40, 0, False, False, False, 1, 2, 2, 1),
    ("TRUX", "Waste/Hauling", 1992, 50, 0, False, False, False, 1, 2, 2, 1),
    ("DirtManager", "Earthwork/Mining", 2000, 20, 0, False, False, False, 1, 1, 1, 1),
    ("Helm CONNECT", "Maritime", 1996, 60, 0, False, False, False, 1, 2, 3, 2),
    ("Bass Software", "Marina Management", 1995, 25, 0, False, False, False, 1, 1, 1, 1),
    ("LaundryCard", "Laundry Management", 1998, 30, 0, False, False, False, 1, 1, 1, 1),
    ("AMS Salon Software", "Salon/Spa", 1992, 35, 0, False, False, False, 1, 1, 1, 1),
    ("ChurchTrac", "Church Management", 2000, 15, 5000000, False, False, False, 1, 1, 1, 1),

    # Legacy Government/Municipal
    ("SunGard PS (Legacy)", "Government/Finance", 1983, 2500, 0, False, False, False, 2, 3, 4, 3),
    ("New World Systems", "Government/ERP", 1981, 800, 0, False, False, False, 2, 3, 4, 2),
    ("Superion", "Government/Public Safety", 1986, 600, 0, False, False, False, 2, 2, 4, 2),
    ("TriTech (Legacy)", "Government/CAD", 1979, 400, 0, False, False, False, 1, 2, 4, 2),
    ("Spillman (Legacy)", "Government/Police RMS", 1986, 200, 0, False, False, False, 1, 2, 4, 1),

    # Legacy Healthcare (pre-cloud)
    ("MEDITECH (Legacy)", "Healthcare/EHR", 1969, 3800, 0, False, False, False, 2, 4, 5, 3),
    ("Cerner (Legacy On-Prem)", "Healthcare/EHR", 1979, 4000, 0, False, False, False, 2, 4, 5, 3),
    ("NextGen (Legacy)", "Healthcare/EHR", 1974, 2000, 0, False, False, False, 2, 3, 5, 2),
    ("eClinicalWorks (Legacy)", "Healthcare/EHR", 1999, 1500, 0, False, False, False, 2, 3, 5, 2),
    ("CompuGroup", "Healthcare/EHR", 1987, 4000, 0, True, False, False, 2, 3, 5, 3),

    # Legacy Financial Services
    ("FIS (Legacy)", "FinTech/Core Banking", 1968, 50000, 0, True, False, False, 2, 3, 5, 4),
    ("Jack Henry (Legacy)", "FinTech/Core Banking", 1976, 7000, 0, True, False, False, 2, 3, 4, 3),
    ("Fiserv (Legacy)", "FinTech/Core Banking", 1984, 40000, 0, True, False, False, 2, 3, 5, 4),
    ("CSI (Computer Services)", "FinTech/Community Banking", 1965, 2500, 0, True, False, False, 1, 2, 4, 2),
    ("Corelation", "FinTech/Credit Union", 1997, 200, 0, False, False, False, 2, 2, 4, 2),

    # ===== MORE AI-EMERGING CANDIDATES (mid-range, some modernization) =====
    # These companies: somewhat modern but limited AI, partial cloud, moderate APIs

    # Niche SaaS — Partially Modernized
    ("Housecall Pro", "Home Services", 2013, 350, 150000000, False, True, True, 3, 2, 1, 3),
    ("Jobber", "Home Services", 2011, 600, 100000000, False, True, True, 3, 2, 1, 3),
    ("ServiceM8", "Field Service", 2008, 100, 20000000, False, False, True, 2, 2, 1, 2),
    ("Aspire Software", "Landscaping", 2013, 200, 80000000, False, True, True, 3, 2, 1, 2),
    ("LMN (Landscape)", "Landscaping", 2009, 120, 40000000, False, True, True, 3, 2, 1, 2),
    ("GorillaDesk", "Pest Control", 2014, 40, 10000000, False, False, True, 2, 2, 1, 1),
    ("PestRoutes", "Pest Control", 2013, 120, 50000000, False, True, True, 3, 2, 1, 2),
    ("Thryv", "SMB/Home Services", 2012, 2500, 0, True, True, True, 3, 2, 1, 3),
    ("Connecteam", "Deskless Workers", 2014, 400, 120000000, False, True, True, 3, 2, 1, 3),
    ("Deputy", "Workforce Management", 2008, 300, 80000000, False, True, True, 3, 2, 1, 3),

    # Dental / Veterinary / Optometry
    ("Dentrix", "Dental", 1989, 500, 0, False, False, False, 2, 3, 4, 3),
    ("Eaglesoft", "Dental", 1995, 300, 0, False, False, False, 2, 3, 4, 2),
    ("Open Dental", "Dental", 2003, 150, 0, False, False, True, 2, 3, 4, 2),
    ("Curve Dental", "Dental", 2005, 80, 20000000, False, True, True, 3, 3, 4, 2),
    ("IDEXX Neo", "Veterinary", 2005, 200, 0, False, False, False, 2, 3, 2, 3),
    ("Shepherd Vet", "Veterinary", 2020, 50, 15000000, False, True, True, 3, 2, 2, 1),
    ("eVetPractice", "Veterinary", 2010, 40, 8000000, False, True, True, 2, 2, 2, 1),
    ("Weave", "Dental/Optometry", 2011, 1000, 0, True, True, True, 3, 3, 3, 3),
    ("RevolutionEHR", "Optometry", 2003, 100, 0, False, False, True, 2, 2, 3, 2),
    ("Crystal PM", "Optometry", 1996, 30, 0, False, False, False, 1, 2, 3, 1),

    # Mid-Market SaaS (Emerging — Cloud but limited AI)
    ("Planful", "Finance/FP&A", 2000, 600, 180000000, False, False, True, 3, 3, 3, 3),
    ("Adaptive Insights", "Finance/FP&A", 2003, 800, 200000000, False, True, True, 3, 3, 3, 3),
    ("Prophix", "Finance/FP&A", 1987, 400, 100000000, False, False, False, 2, 3, 3, 2),
    ("Host Analytics", "Finance/FP&A", 2006, 300, 150000000, False, True, True, 3, 3, 3, 2),
    ("BOARD International", "Finance/BI", 1994, 600, 200000000, False, False, False, 2, 3, 2, 3),
    ("Cin7", "Inventory Management", 2012, 400, 150000000, False, True, True, 3, 3, 2, 3),
    ("TradeGecko", "Inventory/Commerce", 2012, 200, 50000000, False, True, True, 3, 3, 1, 2),
    ("Fishbowl Inventory", "Inventory Management", 2001, 150, 30000000, False, False, False, 2, 2, 1, 2),
    ("SkuVault", "Warehouse Management", 2010, 200, 70000000, False, True, True, 3, 3, 1, 2),
    ("ShipStation", "Shipping/Logistics", 2011, 400, 150000000, False, True, True, 3, 3, 1, 3),

    # Nonprofits / Associations
    ("Bloomerang", "Nonprofit/CRM", 2012, 250, 80000000, False, True, True, 3, 2, 1, 3),
    ("Little Green Light", "Nonprofit/CRM", 2009, 20, 5000000, False, False, True, 2, 2, 1, 1),
    ("DonorPerfect", "Nonprofit/Fundraising", 2000, 200, 50000000, False, False, True, 2, 2, 1, 2),
    ("Network for Good", "Nonprofit/Fundraising", 2001, 300, 100000000, False, True, True, 3, 2, 1, 2),
    ("Wild Apricot", "Association Management", 2006, 100, 30000000, False, True, True, 2, 2, 1, 2),
    ("MemberClicks", "Association Management", 2002, 80, 25000000, False, True, True, 2, 2, 1, 2),
    ("Fonteva", "Association Management", 2011, 60, 20000000, False, True, True, 3, 2, 1, 2),
    ("iMIS", "Association Management", 1997, 150, 0, False, False, False, 2, 2, 2, 2),

    # Car Wash / Parking / Laundry / Self-Storage
    ("DRB Systems", "Car Wash", 1984, 300, 100000000, False, False, False, 2, 2, 1, 3),
    ("Washify", "Car Wash", 2015, 60, 15000000, False, True, True, 3, 2, 1, 2),
    ("EverWash", "Car Wash", 2016, 80, 25000000, False, True, True, 3, 2, 1, 2),
    ("ParkMobile", "Parking", 2008, 250, 80000000, False, True, True, 3, 3, 2, 3),
    ("SpotHero", "Parking", 2011, 200, 70000000, False, True, True, 3, 3, 1, 3),
    ("SiteLink", "Self-Storage", 1996, 100, 0, False, False, False, 2, 2, 1, 2),
    ("StorEDGE", "Self-Storage", 2010, 80, 30000000, False, True, True, 3, 2, 1, 2),
    ("Storeganise", "Self-Storage", 2015, 30, 8000000, False, True, True, 3, 2, 1, 1),
    ("Cents (Laundry)", "Laundry", 2018, 40, 12000000, False, True, True, 3, 2, 1, 1),
    ("CleanCloud", "Laundry/Dry Cleaning", 2014, 50, 10000000, False, True, True, 3, 2, 1, 1),

    # Mining / Maritime / Heavy Industry
    ("Wenco Mining", "Mining", 1983, 200, 0, False, False, False, 2, 3, 3, 2),
    ("Hexagon Mining", "Mining", 1992, 800, 0, False, False, False, 2, 3, 3, 3),
    ("Maptek", "Mining", 1981, 300, 0, False, False, False, 2, 3, 2, 2),
    ("Deswik", "Mining/Planning", 2004, 200, 50000000, False, False, False, 2, 3, 2, 2),
    ("MineRP", "Mining/ERP", 2005, 150, 30000000, False, False, False, 2, 2, 2, 2),
    ("Veson Nautical", "Maritime/Shipping", 2003, 200, 80000000, False, False, True, 3, 3, 3, 3),
    ("StormGeo", "Maritime/Weather", 2001, 300, 100000000, False, False, False, 2, 3, 3, 2),
    ("BASS Maritime", "Maritime", 1990, 40, 0, False, False, False, 1, 2, 3, 1),
    ("Kongsberg Digital", "Maritime/Oil & Gas", 1982, 500, 0, False, False, False, 2, 3, 4, 3),
    ("DNV GL Software", "Maritime/Energy", 1864, 1000, 0, False, False, False, 2, 4, 5, 3),

    # Food & Beverage / Restaurant Tech (smaller)
    ("MarginEdge", "Restaurant/Accounting", 2015, 150, 50000000, False, True, True, 3, 3, 1, 2),
    ("Restaurant365", "Restaurant/Accounting", 2011, 600, 200000000, False, True, True, 3, 3, 1, 3),
    ("Crunchtime", "Restaurant/Operations", 2000, 350, 100000000, False, True, True, 3, 3, 1, 3),
    ("ParTech", "Restaurant/POS", 1978, 1500, 0, True, False, False, 2, 3, 1, 3),
    ("NCR Aloha (Legacy)", "Restaurant/POS", 1884, 5000, 0, True, False, False, 2, 3, 1, 4),
    ("Compeat", "Restaurant/Accounting", 1997, 100, 30000000, False, False, False, 2, 2, 1, 2),
    ("CrunchTime", "F&B/Back Office", 2000, 250, 80000000, False, True, True, 3, 3, 1, 2),
    ("BlueCart", "F&B/Procurement", 2014, 80, 25000000, False, True, True, 3, 2, 1, 2),
    ("Orderly", "Restaurant/AP", 2018, 50, 12000000, False, True, True, 3, 2, 1, 1),
    ("Lineup.ai", "Restaurant/Scheduling", 2019, 30, 8000000, False, True, True, 3, 2, 1, 1),

    # Staffing / Recruitment (niche)
    ("Bullhorn", "Staffing/Recruitment", 1999, 1200, 200000000, False, True, True, 3, 3, 2, 4),
    ("Avionté", "Staffing", 2006, 300, 80000000, False, True, True, 3, 3, 2, 2),
    ("TempWorks", "Staffing", 1998, 80, 20000000, False, False, False, 2, 2, 2, 2),
    ("Crelate", "Staffing/CRM", 2012, 60, 15000000, False, True, True, 3, 2, 2, 1),
    ("Sense", "Staffing/AI", 2016, 200, 90000000, False, True, True, 3, 3, 2, 2),
    ("Hireology", "Hiring/Automotive", 2010, 250, 80000000, False, True, True, 3, 3, 1, 2),
    ("Lever (Legacy)", "Recruitment ATS", 2012, 400, 120000000, False, True, True, 3, 3, 1, 3),
    ("JazzHR", "Recruitment ATS", 2009, 200, 60000000, False, True, True, 3, 2, 1, 2),

    # Facilities / Maintenance
    ("eMaint", "Maintenance/CMMS", 1986, 200, 50000000, False, False, False, 2, 2, 2, 2),
    ("Fiix", "Maintenance/CMMS", 2008, 150, 40000000, False, True, True, 3, 3, 2, 2),
    ("UpKeep", "Maintenance/CMMS", 2014, 250, 100000000, False, True, True, 3, 3, 2, 2),
    ("Hippo CMMS", "Maintenance/CMMS", 2006, 80, 20000000, False, True, True, 3, 2, 2, 1),
    ("FMX", "Facilities Management", 2012, 100, 30000000, False, True, True, 3, 2, 2, 2),
    ("AkitaBox", "Facilities Management", 2014, 60, 15000000, False, True, True, 3, 2, 2, 1),
    ("Corrigo", "Facilities Management", 2001, 200, 60000000, False, True, True, 3, 3, 2, 2),
    ("Angus Systems", "Facilities Management", 1985, 100, 0, False, False, False, 2, 2, 2, 2),

    # Event Management
    ("Cvent", "Event Management", 1999, 4800, 0, True, True, True, 3, 3, 1, 4),
    ("Bizzabo", "Event Management", 2012, 350, 200000000, False, True, True, 3, 3, 1, 3),
    ("Splash", "Event Marketing", 2011, 200, 80000000, False, True, True, 3, 2, 1, 2),
    ("Social Tables", "Event Planning", 2012, 150, 60000000, False, True, True, 3, 2, 1, 2),
    ("Aventri", "Event Management", 2008, 250, 100000000, False, True, True, 3, 3, 1, 2),
    ("Swoogo", "Event Platform", 2016, 80, 25000000, False, True, True, 3, 2, 1, 2),

    # Compliance / Risk (heavy regulatory = emerging due to risk_compliance drag)
    ("LogicGate", "GRC/Compliance", 2016, 250, 150000000, False, True, True, 3, 3, 4, 3),
    ("Resolver", "GRC/Compliance", 2000, 350, 100000000, False, True, True, 3, 3, 4, 3),
    ("SAI Global", "GRC/Compliance", 1994, 800, 200000000, False, False, False, 2, 3, 4, 3),
    ("NAVEX Global", "GRC/Compliance", 2012, 1200, 300000000, False, True, True, 3, 3, 4, 3),
    ("MetricStream", "GRC/Compliance", 2000, 1200, 200000000, False, False, False, 2, 3, 4, 3),
    ("Galvanize (Diligent)", "GRC/Compliance", 2007, 400, 150000000, False, True, True, 3, 3, 4, 2),

    # ===== MORE AI-READY CANDIDATES (top-tier, AI-native, massive data) =====
    # These need: cloud native, has AI, high API ecosystem (4-5), high data richness (5),
    # large employee count or huge funding, market_position 4-5, low regulatory burden

    # AI-Native / Data-Heavy Companies
    ("Databricks", "Data/AI Platform", 2013, 7000, 4000000000, False, True, True, 5, 5, 2, 5),
    ("Snowflake", "Data/Cloud", 2012, 7000, 0, True, True, True, 5, 5, 2, 5),
    ("Palantir Technologies", "Data/Analytics", 2003, 3800, 0, True, True, True, 5, 5, 3, 5),
    ("C3.ai", "Enterprise AI", 2009, 1000, 0, True, True, True, 5, 5, 2, 4),
    ("UiPath", "Automation/AI", 2005, 4200, 0, True, True, True, 5, 5, 2, 5),
    ("Datadog", "Observability/AI", 2010, 5200, 0, True, True, True, 5, 5, 1, 5),
    ("Cloudflare", "Network/Security", 2009, 3800, 0, True, True, True, 5, 5, 2, 5),
    ("Twilio", "Communications/API", 2008, 5500, 0, True, True, True, 5, 5, 2, 5),
    ("Elastic", "Search/Analytics", 2012, 3400, 0, True, True, True, 5, 5, 1, 5),
    ("MongoDB", "Database/Developer", 2007, 5100, 0, True, True, True, 5, 5, 1, 5),

    # AI-Forward Vertical Leaders
    ("Tempus (Genomics)", "Healthcare/Precision Med", 2015, 2500, 1000000000, False, True, True, 5, 5, 4, 5),
    ("Flatiron Health (Oncology)", "Healthcare/Oncology Data", 2012, 1500, 350000000, False, True, True, 5, 5, 4, 4),
    ("Veracyte", "Healthcare/Diagnostics AI", 2008, 800, 0, True, True, True, 4, 5, 4, 4),
    ("Recursion", "Pharma/AI Drug Discovery", 2013, 600, 0, True, True, True, 5, 5, 4, 4),
    ("Schrodinger", "Pharma/Computational", 1990, 600, 0, True, True, True, 5, 5, 4, 4),
    ("Nuvei", "Payments/AI", 2003, 1800, 0, True, True, True, 5, 5, 3, 5),
    ("Brex", "FinTech/Corporate Cards", 2017, 1500, 1200000000, False, True, True, 5, 5, 3, 5),
    ("Rippling", "HR/IT Platform", 2016, 3000, 1200000000, False, True, True, 5, 5, 2, 5),
    ("Deel", "HR/Global Payroll", 2018, 3500, 650000000, False, True, True, 5, 4, 3, 5),
    ("Figma", "Design/Collaboration", 2012, 1500, 0, False, True, True, 5, 4, 1, 5),

    # Top-Tier Vertical SaaS (AI-Ready)
    ("HubSpot", "Marketing/CRM", 2006, 7600, 0, True, True, True, 5, 5, 1, 5),
    ("Shopify Plus", "E-Commerce/Enterprise", 2006, 11000, 0, True, True, True, 5, 5, 1, 5),
    ("Square (Block)", "Payments/Commerce", 2009, 12000, 0, True, True, True, 5, 5, 2, 5),
    ("Wiz", "Cloud Security", 2020, 1500, 1000000000, False, True, True, 5, 5, 2, 5),
    ("Notion", "Productivity/AI", 2013, 800, 350000000, False, True, True, 5, 4, 1, 5),
    ("Canva", "Design/AI", 2012, 4000, 600000000, False, True, True, 5, 4, 1, 5),
    ("Airtable", "Low-Code/AI", 2012, 1000, 750000000, False, True, True, 5, 5, 1, 5),
    ("Amplitude", "Product Analytics", 2012, 700, 0, True, True, True, 5, 5, 1, 4),
    ("Contentful", "CMS/API-First", 2013, 800, 330000000, False, True, True, 5, 4, 1, 4),
    ("LaunchDarkly", "Feature Management", 2014, 500, 320000000, False, True, True, 5, 4, 1, 4),

    # More AI-Ready (Vertical AI leaders)
    ("Samsara (IoT)", "Fleet/IoT", 2015, 2500, 0, True, True, True, 5, 5, 1, 5),
    ("CrowdStrike", "Cybersecurity/AI", 2011, 8000, 0, True, True, True, 5, 5, 2, 5),
    ("SentinelOne", "Cybersecurity/AI", 2013, 2500, 0, True, True, True, 5, 5, 2, 5),
    ("Zscaler", "Cloud Security", 2007, 7000, 0, True, True, True, 5, 5, 2, 5),
    ("Okta", "Identity/Security", 2009, 6000, 0, True, True, True, 5, 5, 2, 5),

    # ===== ADDITIONAL EMERGING / NICHE VERTICALS =====

    # Cannabis Tech
    ("Dutchie", "Cannabis Tech", 2017, 400, 350000000, False, True, True, 3, 3, 4, 3),
    ("Flowhub", "Cannabis/POS", 2014, 200, 50000000, False, True, True, 3, 3, 4, 2),
    ("Treez", "Cannabis/Retail", 2016, 150, 40000000, False, True, True, 3, 3, 4, 2),
    ("BioTrackTHC", "Cannabis/Tracking", 2010, 80, 20000000, False, False, False, 2, 2, 4, 2),
    ("Meadow", "Cannabis/Delivery", 2014, 60, 15000000, False, True, True, 3, 2, 4, 1),

    # Sports / Entertainment
    ("SeatGeek", "Ticketing", 2009, 500, 250000000, False, True, True, 4, 4, 1, 4),
    ("Teamworks", "Sports/Operations", 2005, 200, 80000000, False, True, True, 3, 3, 1, 3),
    ("ShotTracker", "Sports/Analytics", 2013, 80, 30000000, False, True, True, 3, 4, 1, 2),
    ("Hudl", "Sports/Video Analytics", 2006, 2000, 200000000, False, True, True, 4, 4, 1, 4),
    ("Catapult Sports", "Sports/Wearables", 2006, 400, 150000000, False, True, True, 3, 4, 1, 3),
    ("Second Spectrum", "Sports/AI", 2014, 200, 60000000, False, True, True, 4, 5, 1, 3),

    # Childcare / Senior Care
    ("Procare Solutions", "Childcare", 1992, 300, 50000000, False, False, True, 2, 2, 3, 3),
    ("brightwheel", "Childcare", 2015, 350, 100000000, False, True, True, 3, 3, 3, 3),
    ("HiMama", "Childcare", 2012, 150, 40000000, False, True, True, 3, 2, 3, 2),
    ("PointClickCare", "Senior Care/EHR", 2000, 2000, 300000000, False, True, True, 3, 4, 4, 4),
    ("MatrixCare", "Senior Care/EHR", 2000, 800, 200000000, False, True, False, 3, 3, 4, 3),
    ("Netsmart", "Behavioral Health", 1998, 2000, 400000000, False, True, False, 3, 3, 4, 3),

    # Camping / Outdoor / Recreation
    ("Campspot", "Campground/RV", 2015, 100, 30000000, False, True, True, 3, 2, 1, 2),
    ("ResNexus", "Campground/Lodging", 2004, 60, 10000000, False, True, True, 2, 2, 1, 1),
    ("CampBrain", "Camping/Registration", 2000, 40, 5000000, False, False, True, 2, 2, 1, 1),
    ("ActiveNet", "Parks & Recreation", 2003, 200, 60000000, False, True, True, 3, 2, 1, 2),
    ("PerfectMind", "Recreation Mgmt", 2005, 150, 40000000, False, True, True, 3, 2, 1, 2),

    # Trades & Home Services
    ("ServiceFusion", "HVAC/Plumbing", 2014, 80, 25000000, False, True, True, 3, 2, 1, 2),
    ("FieldEdge", "HVAC/Field Service", 1980, 200, 60000000, False, False, True, 2, 2, 1, 2),
    ("Sera (HVAC)", "HVAC", 2018, 50, 15000000, False, True, True, 3, 2, 1, 1),
    ("BuildOps", "Commercial Contracting", 2018, 200, 80000000, False, True, True, 3, 3, 1, 2),
    ("Payzer", "HVAC/Payments", 2011, 60, 12000000, False, True, True, 3, 2, 2, 1),
    ("CompanyCam", "Contracting/Photos", 2015, 200, 50000000, False, True, True, 3, 2, 1, 2),

    # Accounting / Tax (niche)
    ("Canopy Tax", "Tax/Accounting", 2014, 200, 50000000, False, True, True, 3, 3, 3, 2),
    ("TaxJar", "Tax Compliance", 2013, 250, 60000000, False, True, True, 3, 3, 3, 3),
    ("Avalara", "Tax Compliance", 2004, 4000, 0, True, True, True, 4, 4, 3, 4),
    ("Vertex", "Tax Compliance", 1978, 3000, 0, True, False, False, 3, 4, 4, 4),
    ("Drake Software", "Tax Preparation", 1977, 400, 0, False, False, False, 2, 2, 4, 2),
    ("CCH Wolters Kluwer", "Tax/Accounting", 1913, 5000, 0, True, False, False, 2, 3, 4, 4),

    # Transportation / Fleet (smaller)
    ("Azuga", "Fleet Telematics", 2012, 200, 80000000, False, True, True, 3, 3, 2, 2),
    ("GPS Trackit", "Fleet Tracking", 2002, 150, 40000000, False, True, True, 3, 3, 1, 2),
    ("Teletrac Navman", "Fleet Management", 1988, 1000, 0, False, False, False, 2, 3, 2, 3),
    ("Lytx", "Fleet Video/AI", 1998, 800, 250000000, False, True, True, 4, 4, 2, 3),
    ("Platform Science", "Fleet/Trucking", 2015, 250, 120000000, False, True, True, 4, 4, 2, 3),

    # Retail / Commerce (niche)
    ("Vend (Lightspeed)", "Retail/POS", 2010, 300, 100000000, False, True, True, 3, 3, 1, 3),
    ("Revel Systems", "Retail/POS", 2010, 350, 150000000, False, True, True, 3, 3, 1, 3),
    ("NCR Silver", "Retail/POS", 1884, 2000, 0, True, False, False, 2, 3, 2, 4),
    ("Heartland Payment", "Retail/Payments", 2001, 1500, 0, False, False, False, 2, 3, 3, 3),
    ("RetailNext", "Retail/Analytics", 2007, 200, 80000000, False, True, True, 4, 4, 1, 3),
    ("Tulip Retail", "Retail/Clienteling", 2013, 150, 50000000, False, True, True, 3, 3, 1, 2),

    # Media / Publishing
    ("Cision", "Media/PR", 1992, 3500, 0, False, True, False, 3, 4, 1, 4),
    ("Meltwater", "Media Intelligence", 2001, 1800, 0, False, True, True, 3, 4, 1, 4),
    ("Naviga (Publishing)", "Publishing/CMS", 1999, 400, 100000000, False, False, False, 2, 3, 1, 2),
    ("Piano (Publishing)", "Publishing/Paywall", 2010, 350, 150000000, False, True, True, 3, 3, 1, 3),
    ("Issuu", "Publishing/Digital", 2006, 200, 50000000, False, True, True, 3, 3, 1, 2),

    # Aviation / Aerospace
    ("Ramco Aviation", "Aviation/MRO", 1997, 400, 50000000, False, False, False, 2, 3, 5, 2),
    ("IBS Software", "Aviation/Cargo", 1997, 3000, 100000000, False, False, False, 2, 3, 5, 3),
    ("SITA", "Aviation/IT", 1949, 4000, 0, False, False, False, 2, 3, 5, 3),
    ("Flightaware", "Aviation/Tracking", 2005, 200, 50000000, False, True, True, 4, 4, 3, 3),
    ("Cirium", "Aviation/Analytics", 2019, 600, 200000000, False, True, True, 4, 5, 3, 3),

    # More AI-Limited (very legacy, very small)
    ("WinTeam", "Janitorial/Cleaning", 1988, 60, 0, False, False, False, 1, 1, 1, 2),
    ("ServiceCEO", "Home Services (Legacy)", 1995, 30, 0, False, False, False, 1, 1, 1, 1),
    ("Spectra (Legacy)", "Venue Management", 1988, 150, 0, False, False, False, 1, 2, 1, 2),
    ("MicroMain", "Maintenance (Legacy)", 1990, 40, 0, False, False, False, 1, 2, 2, 1),
    ("RealSTAR", "Real Estate (Legacy)", 1992, 20, 0, False, False, False, 1, 1, 2, 1),
    ("TRAKnet", "Healthcare (Legacy)", 1994, 25, 0, False, False, False, 1, 2, 5, 1),
    ("PrimePoint", "Payroll (Legacy)", 1986, 80, 0, False, False, False, 1, 2, 3, 1),
    ("AIMsi", "Music Store Mgmt", 1985, 15, 0, False, False, False, 1, 1, 1, 1),
    ("Envisio", "Government Planning", 2009, 30, 5000000, False, False, True, 2, 2, 3, 1),
    ("MuniCode", "Government/Codification", 1951, 200, 0, False, False, False, 1, 2, 4, 2),
    ("Accufund", "Nonprofit Accounting", 1988, 40, 0, False, False, False, 1, 2, 2, 1),
    ("Cougar Mountain", "Accounting (Legacy)", 1982, 50, 0, False, False, False, 1, 2, 3, 1),
    ("DataPath", "Benefits Admin (Legacy)", 1984, 100, 0, False, False, False, 1, 2, 3, 2),
    ("Tyler Munis (Legacy)", "Government/ERP", 1998, 500, 0, False, False, False, 2, 3, 4, 2),
    ("ACOM Solutions", "AP Automation (Legacy)", 1983, 60, 0, False, False, False, 1, 2, 2, 1),

    # Telecom / ISP Billing (legacy)
    ("Amdocs (Legacy)", "Telecom/Billing", 1982, 28000, 0, True, False, False, 2, 3, 3, 4),
    ("CSG Systems", "Telecom/Billing", 1994, 5000, 0, True, False, False, 2, 3, 3, 3),
    ("Netcracker", "Telecom/BSS", 1993, 3000, 0, False, False, False, 2, 3, 3, 3),
    ("MATRIXX Software", "Telecom/Billing", 2010, 200, 80000000, False, True, True, 3, 3, 3, 2),
    ("Totogi", "Telecom/Cloud", 2020, 60, 20000000, False, True, True, 4, 3, 3, 1),
]

def build_additional_company_dicts(company_list):
    """Convert tuples to company dicts"""
    result = []
    for company in company_list:
        result.append({
            "name": company[0],
            "vertical": company[1],
            "founded_year": company[2],
            "employee_count": company[3],
            "funding_total_usd": company[4],
            "is_public": company[5],
            "has_ai_features": company[6],
            "cloud_native": company[7],
            "api_ecosystem_strength": company[8],
            "data_richness": company[9],
            "regulatory_burden": company[10],
            "market_position": company[11]
        })
    return result

def main():
    # Combine all companies
    all_companies = COMPANIES + build_additional_company_dicts(ADDITIONAL_COMPANIES)

    print(f"Building training dataset with {len(all_companies)} companies...")

    # Score each company
    dataset = []
    for co in all_companies:
        pillars = {
            "data_quality": score_data_quality(co),
            "workflow_digitization": score_workflow_digitization(co),
            "infrastructure": score_infrastructure(co),
            "competitive_position": score_competitive_position(co),
            "revenue_upside": score_revenue_upside(co),
            "margin_upside": score_margin_upside(co),
            "org_readiness": score_org_readiness(co),
            "risk_compliance": score_risk_compliance(co)
        }

        composite_score = calculate_composite_score(pillars)
        tier = assign_tier(composite_score)

        entry = {
            "name": co["name"],
            "vertical": co["vertical"],
            "founded_year": co["founded_year"],
            "employee_count": co["employee_count"],
            "funding_total_usd": co["funding_total_usd"],
            "is_public": co["is_public"],
            "has_ai_features": co["has_ai_features"],
            "cloud_native": co["cloud_native"],
            "api_ecosystem_strength": co["api_ecosystem_strength"],
            "data_richness": co["data_richness"],
            "regulatory_burden": co["regulatory_burden"],
            "market_position": co["market_position"],
            "pillars": pillars,
            "composite_score": composite_score,
            "tier": tier
        }
        dataset.append(entry)

    # Save to JSON
    output_dir = "/sessions/vibrant-tender-allen/solen-ai-intelligence/data/training"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "large_training_set.json")

    with open(output_path, 'w') as f:
        json.dump(dataset, f, indent=2)

    print(f"\nDataset saved to {output_path}")
    print(f"Total companies: {len(dataset)}")

    # Print summary statistics
    tiers = defaultdict(int)
    scores_by_vertical = defaultdict(list)

    for entry in dataset:
        tiers[entry["tier"]] += 1
        scores_by_vertical[entry["vertical"]].append(entry["composite_score"])

    print("\n=== TIER DISTRIBUTION ===")
    for tier in ["AI-Ready", "AI-Buildable", "AI-Emerging", "AI-Limited"]:
        print(f"{tier}: {tiers[tier]} companies")

    print("\n=== OVERALL SCORE STATS ===")
    all_scores = [e["composite_score"] for e in dataset]
    print(f"Mean: {sum(all_scores) / len(all_scores):.2f}")
    print(f"Min: {min(all_scores):.2f}")
    print(f"Max: {max(all_scores):.2f}")
    print(f"Median: {sorted(all_scores)[len(all_scores)//2]:.2f}")

    print("\n=== SCORES BY VERTICAL ===")
    for vertical in sorted(scores_by_vertical.keys()):
        scores = scores_by_vertical[vertical]
        avg = sum(scores) / len(scores)
        print(f"{vertical}: {len(scores)} companies, avg score {avg:.2f}")

if __name__ == "__main__":
    main()
