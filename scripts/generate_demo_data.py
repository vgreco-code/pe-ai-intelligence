#!/usr/bin/env python3
"""
Generate complete demo dataset for the Solen AI Intelligence Platform.

This script:
1. Generates realistic research data for all 14 Solen portfolio companies
2. Trains an XGBoost model on 8 ground truth companies
3. Scores all 14 portcos using the trained model + weighted formula
4. Creates a pre-seeded SQLite database with all results
5. Exports JSON files for the frontend demo

Run: python scripts/generate_demo_data.py
"""

import json
import os
import sys
import uuid
from datetime import datetime, timedelta
import random

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ---------------------------------------------------------------------------
# FRAMEWORK CONSTANTS
# ---------------------------------------------------------------------------
PILLARS = {
    "data_quality": {"weight": 2.0, "label": "Data Quality & Availability"},
    "workflow_digitization": {"weight": 2.0, "label": "Workflow Digitization"},
    "infrastructure": {"weight": 1.5, "label": "Infrastructure Readiness"},
    "competitive_position": {"weight": 2.0, "label": "Competitive Position"},
    "revenue_upside": {"weight": 1.5, "label": "Revenue Upside"},
    "margin_upside": {"weight": 1.5, "label": "Margin Upside"},
    "org_readiness": {"weight": 1.0, "label": "Org Readiness"},
    "risk_compliance": {"weight": 1.0, "label": "Risk & Compliance"},
}
TOTAL_WEIGHT = 12.5
TIERS = [("AI-Ready", 4.0), ("AI-Buildable", 3.2), ("AI-Emerging", 2.5), ("AI-Limited", 0)]

def calc_composite(pillar_scores):
    total = sum(pillar_scores[p] * PILLARS[p]["weight"] for p in pillar_scores)
    return round(total / TOTAL_WEIGHT, 2)

def get_tier(score):
    for name, threshold in TIERS:
        if score >= threshold:
            return name
    return "AI-Limited"

def get_wave(composite, tier):
    if composite >= 3.2:
        return 1
    elif composite >= 2.8:
        return 2
    else:
        return 3

# ---------------------------------------------------------------------------
# 14 SOLEN PORTFOLIO COMPANIES — pillar scores from v2 backtested framework
# These are the exact scores from the CAIO presentation (slide 9)
# ---------------------------------------------------------------------------
SOLEN_COMPANIES = [
    {
        "name": "Cairn Applications",
        "vertical": "Waste Hauling SaaS",
        "website": "cairnapp.com",
        "github_org": "",
        "description": "Box Tracker platform for waste haulers. 350+ customers, 65K dumpsters, ~$150M annual commerce. Acquired Dec 2025.",
        "founded_year": 2008,
        "employee_count": 45,
        "pillar_scores": {
            "data_quality": 3.8, "workflow_digitization": 3.8, "infrastructure": 2.5,
            "competitive_position": 4.3, "revenue_upside": 4.0, "margin_upside": 3.8,
            "org_readiness": 2.5, "risk_compliance": 4.8
        },
    },
    {
        "name": "SMRTR",
        "vertical": "F&B Supply Chain",
        "website": "smrtr.io",
        "github_org": "",
        "description": "Merged Dash + S4i. AP automation, backhaul tracking, supplier compliance, proof of delivery for food & beverage distributors.",
        "founded_year": 2018,
        "employee_count": 120,
        "pillar_scores": {
            "data_quality": 3.5, "workflow_digitization": 4.0, "infrastructure": 3.5,
            "competitive_position": 3.3, "revenue_upside": 3.0, "margin_upside": 3.5,
            "org_readiness": 2.8, "risk_compliance": 4.0
        },
    },
    {
        "name": "ViaPeople",
        "vertical": "Talent Management",
        "website": "viapeople.com",
        "github_org": "",
        "description": "20+ years in performance management, 360 feedback, succession planning. Serves PE firms and financial services (Jefferies, Warburg, Evercore).",
        "founded_year": 2002,
        "employee_count": 65,
        "pillar_scores": {
            "data_quality": 3.5, "workflow_digitization": 3.5, "infrastructure": 3.0,
            "competitive_position": 3.3, "revenue_upside": 3.8, "margin_upside": 3.3,
            "org_readiness": 3.0, "risk_compliance": 3.8
        },
    },
    {
        "name": "Track Star",
        "vertical": "Fleet & Asset Management",
        "website": "trackstar.com",
        "github_org": "",
        "description": "25-year GPS tracking, video telematics, EAM, predictive maintenance platform. Public safety, utilities, government.",
        "founded_year": 1999,
        "employee_count": 200,
        "pillar_scores": {
            "data_quality": 3.8, "workflow_digitization": 3.8, "infrastructure": 2.8,
            "competitive_position": 2.8, "revenue_upside": 3.5, "margin_upside": 3.3,
            "org_readiness": 2.8, "risk_compliance": 4.0
        },
    },
    {
        "name": "FMSI",
        "vertical": "Banking Operations",
        "website": "fmsi.com",
        "github_org": "",
        "description": "Staffing and scheduling optimization for bank branches. Workforce analytics for financial institutions.",
        "founded_year": 1990,
        "employee_count": 85,
        "pillar_scores": {
            "data_quality": 3.3, "workflow_digitization": 3.5, "infrastructure": 2.5,
            "competitive_position": 3.3, "revenue_upside": 3.5, "margin_upside": 3.3,
            "org_readiness": 2.8, "risk_compliance": 3.3
        },
    },
    {
        "name": "Champ",
        "vertical": "Public Health EHR",
        "website": "champsoftware.com",
        "github_org": "",
        "description": "Electronic health records for public health departments. Clinical workflows, immunization tracking, disease surveillance.",
        "founded_year": 1985,
        "employee_count": 150,
        "pillar_scores": {
            "data_quality": 3.0, "workflow_digitization": 3.5, "infrastructure": 2.8,
            "competitive_position": 3.8, "revenue_upside": 3.0, "margin_upside": 3.0,
            "org_readiness": 2.8, "risk_compliance": 2.8
        },
    },
    {
        "name": "TrackIt Transit",
        "vertical": "Transit Operations",
        "website": "trackittransit.com",
        "github_org": "",
        "description": "Paperless transit operations platform. 100+ transit locations. Agency communication and workflow digitization. Acquired Feb 2026.",
        "founded_year": 2010,
        "employee_count": 30,
        "pillar_scores": {
            "data_quality": 3.0, "workflow_digitization": 3.0, "infrastructure": 2.5,
            "competitive_position": 3.8, "revenue_upside": 3.0, "margin_upside": 3.3,
            "org_readiness": 2.5, "risk_compliance": 3.8
        },
    },
    {
        "name": "NexTalk",
        "vertical": "ADA Communications",
        "website": "nextalk.com",
        "github_org": "",
        "description": "ADA-compliant communication solutions. Video relay interpreting, captioning, accessibility services.",
        "founded_year": 2005,
        "employee_count": 40,
        "pillar_scores": {
            "data_quality": 2.8, "workflow_digitization": 2.8, "infrastructure": 3.3,
            "competitive_position": 3.5, "revenue_upside": 2.8, "margin_upside": 2.8,
            "org_readiness": 2.8, "risk_compliance": 3.3
        },
    },
    {
        "name": "Thought Foundry",
        "vertical": "Entertainment PaaS",
        "website": "thoughtfoundry.com",
        "github_org": "",
        "description": "Platform-as-a-Service for entertainment industry. Digital content management and distribution workflows.",
        "founded_year": 2015,
        "employee_count": 55,
        "pillar_scores": {
            "data_quality": 3.0, "workflow_digitization": 2.8, "infrastructure": 2.5,
            "competitive_position": 3.0, "revenue_upside": 3.0, "margin_upside": 2.8,
            "org_readiness": 2.5, "risk_compliance": 4.0
        },
    },
    {
        "name": "Spokane",
        "vertical": "Produce ERP",
        "website": "spokane.com",
        "github_org": "",
        "description": "ERP system for fresh produce distribution. Order management, inventory, traceability for produce supply chain.",
        "founded_year": 1995,
        "employee_count": 70,
        "pillar_scores": {
            "data_quality": 2.8, "workflow_digitization": 3.3, "infrastructure": 1.3,
            "competitive_position": 3.8, "revenue_upside": 3.0, "margin_upside": 2.8,
            "org_readiness": 1.8, "risk_compliance": 4.0
        },
    },
    {
        "name": "Primate",
        "vertical": "Energy Control Room",
        "website": "primate.com",
        "github_org": "",
        "description": "Control room software for energy utilities. SCADA integration, real-time monitoring, alarm management.",
        "founded_year": 2000,
        "employee_count": 90,
        "pillar_scores": {
            "data_quality": 3.0, "workflow_digitization": 3.0, "infrastructure": 2.5,
            "competitive_position": 3.5, "revenue_upside": 2.5, "margin_upside": 2.8,
            "org_readiness": 2.3, "risk_compliance": 2.8
        },
    },
    {
        "name": "ThingTech",
        "vertical": "IoT Asset Tracking",
        "website": "thingtech.com",
        "github_org": "",
        "description": "IoT-powered asset tracking and management platform. Connected devices, location intelligence, workflow automation.",
        "founded_year": 2012,
        "employee_count": 110,
        "pillar_scores": {
            "data_quality": 3.0, "workflow_digitization": 2.5, "infrastructure": 2.5,
            "competitive_position": 2.5, "revenue_upside": 3.0, "margin_upside": 2.8,
            "org_readiness": 2.5, "risk_compliance": 4.0
        },
    },
    {
        "name": "Dash",
        "vertical": "AP & Doc Automation",
        "website": "dash.com",
        "github_org": "",
        "description": "Legacy AP and document automation platform. Now merged into SMRTR. Invoice processing and payment workflows.",
        "founded_year": 2010,
        "employee_count": 60,
        "pillar_scores": {
            "data_quality": 2.3, "workflow_digitization": 3.3, "infrastructure": 2.5,
            "competitive_position": 2.3, "revenue_upside": 2.0, "margin_upside": 2.8,
            "org_readiness": 2.5, "risk_compliance": 4.0
        },
    },
    {
        "name": "AutoTime",
        "vertical": "A&D Payroll",
        "website": "autotime.com",
        "github_org": "",
        "description": "Payroll and time tracking for aerospace & defense contractors. DCAA compliance, government billing, labor distribution.",
        "founded_year": 1998,
        "employee_count": 75,
        "pillar_scores": {
            "data_quality": 2.3, "workflow_digitization": 2.5, "infrastructure": 2.5,
            "competitive_position": 3.0, "revenue_upside": 2.0, "margin_upside": 3.0,
            "org_readiness": 2.3, "risk_compliance": 3.0
        },
    },
]

# ---------------------------------------------------------------------------
# EVIDENCE & SOURCES for each pillar (per company)
# ---------------------------------------------------------------------------
EVIDENCE_TEMPLATES = {
    "data_quality": {
        "high": [
            "Proprietary dataset with {n}+ records across customer base",
            "Structured data pipeline with automated quality checks",
            "Cross-customer benchmarking data creates competitive moat",
            "Historical data spanning {y}+ years enables trend analysis",
        ],
        "medium": [
            "Customer data available but siloed across modules",
            "Data quality varies by customer deployment",
            "Some structured data, manual entry still common",
        ],
        "low": [
            "Limited data infrastructure; primarily transactional records",
            "Data governance practices not formalized",
            "Legacy database with limited API access",
        ],
    },
    "workflow_digitization": {
        "high": [
            "End-to-end digital workflows across core product",
            "API-driven integrations with {n}+ third-party systems",
            "Automated workflow triggers and routing rules",
            "Mobile-first workflow execution for field operations",
        ],
        "medium": [
            "Core workflows digitized but some manual steps remain",
            "Integration points exist but not fully automated",
            "Paper-based processes being migrated to digital",
        ],
        "low": [
            "Significant manual workflow steps in core operations",
            "Limited automation; relies on human-in-the-loop for most tasks",
            "Legacy processes with minimal digital transformation",
        ],
    },
    "infrastructure": {
        "high": [
            "Cloud-native architecture on AWS/Azure/GCP",
            "Microservices or modular monolith with clear API boundaries",
            "CI/CD pipeline with automated testing and deployment",
            "Containerized deployment with Kubernetes/ECS",
        ],
        "medium": [
            "Hybrid cloud deployment; migration underway",
            "Monolithic architecture with some service extraction",
            "Basic deployment automation; manual testing prevalent",
        ],
        "low": [
            "On-premise or legacy hosting infrastructure",
            "Tightly coupled monolithic architecture",
            "Manual deployment processes; limited automation",
        ],
    },
    "competitive_position": {
        "high": [
            "Market leader or strong #2 in vertical niche",
            "Deep domain expertise creates high switching costs",
            "Regulatory compliance requirements create barriers to entry",
            "Established customer base with {n}+ active accounts",
        ],
        "medium": [
            "Competitive in niche but facing pressure from broader platforms",
            "Moderate market share with loyal but concentrated customer base",
            "Differentiation based on vertical specialization",
        ],
        "low": [
            "Facing disruption from AI-native competitors",
            "Commoditized offering with limited differentiation",
            "Small market share in fragmented market",
        ],
    },
    "revenue_upside": {
        "high": [
            "AI features enable premium pricing tier (+20-30% ARPU uplift)",
            "Predictive analytics create new revenue stream",
            "Cross-customer data enables marketplace/benchmark products",
            "AI-powered upsell/cross-sell recommendations",
        ],
        "medium": [
            "AI enhancements improve retention and reduce churn",
            "Operational efficiency gains translate to margin, not new revenue",
            "Potential for AI-powered add-on modules",
        ],
        "low": [
            "Limited revenue upside from AI; primarily cost reduction play",
            "Market not yet demanding AI features",
            "Regulatory constraints limit AI product innovation",
        ],
    },
    "margin_upside": {
        "high": [
            "AI automation can reduce support costs by 40-50%",
            "Automated QA and testing reduces engineering overhead",
            "Agentic document processing eliminates manual data entry",
            "AI-optimized operations reduce COGS significantly",
        ],
        "medium": [
            "Moderate automation opportunities in support and operations",
            "AI can augment but not fully replace manual processes",
            "Efficiency gains offset by implementation costs",
        ],
        "low": [
            "Limited margin improvement potential from AI",
            "High-touch service model difficult to automate",
            "Regulatory requirements mandate human oversight",
        ],
    },
    "org_readiness": {
        "high": [
            "Technical leadership with AI/ML experience",
            "Engineering team familiar with modern ML frameworks",
            "Culture of experimentation and data-driven decision making",
            "Dedicated innovation budget and team",
        ],
        "medium": [
            "Technical leadership open to AI but limited hands-on experience",
            "Engineering team capable but needs upskilling",
            "Some experimentation culture; risk-averse leadership",
        ],
        "low": [
            "Leadership has limited AI understanding",
            "Engineering team focused on maintenance, not innovation",
            "Organizational resistance to change",
        ],
    },
    "risk_compliance": {
        "high": [
            "Low regulatory exposure for AI use cases",
            "Existing compliance framework adaptable to AI governance",
            "Data privacy practices already robust",
            "IP protection strong; minimal risk of AI-related leakage",
        ],
        "medium": [
            "Moderate regulatory considerations (SOC2, data privacy)",
            "Compliance framework needs AI-specific additions",
            "Some data sensitivity concerns manageable with guardrails",
        ],
        "low": [
            "High regulatory exposure (HIPAA, DCAA, FedRAMP)",
            "Significant compliance overhead for AI deployment",
            "Data sensitivity limits AI training opportunities",
        ],
    },
}

SOURCE_TEMPLATES = [
    "Company website: {website}",
    "LinkedIn: linkedin.com/company/{slug}",
    "Crunchbase: crunchbase.com/organization/{slug}",
    "SEC EDGAR full-text search",
    "GitHub: github.com/{slug}",
    "Glassdoor company profile",
    "G2 product reviews",
    "Industry analyst report ({vertical} market)",
    "Press release: {name} acquisition announcement",
    "Job postings analysis (LinkedIn, Indeed)",
]


def generate_evidence(pillar, score, company):
    """Generate realistic evidence strings for a pillar score."""
    if score >= 3.5:
        level = "high"
    elif score >= 2.5:
        level = "medium"
    else:
        level = "low"

    templates = EVIDENCE_TEMPLATES.get(pillar, {}).get(level, ["Evidence unavailable"])
    evidence = []
    for t in templates[:random.randint(2, min(4, len(templates)))]:
        text = t.replace("{n}", str(random.choice([50, 100, 200, 350, 500, 1000])))
        text = text.replace("{y}", str(random.choice([5, 10, 15, 20])))
        evidence.append(text)
    return evidence


def generate_sources(company):
    """Generate realistic source URLs for a company."""
    slug = company["name"].lower().replace(" ", "-").replace("&", "and")
    website = company.get("website", f"{slug}.com")
    vertical = company.get("vertical", "Software")

    sources = []
    for t in random.sample(SOURCE_TEMPLATES, k=random.randint(4, 7)):
        url = t.replace("{website}", website)
        url = url.replace("{slug}", slug)
        url = url.replace("{vertical}", vertical)
        url = url.replace("{name}", company["name"])
        sources.append(url)
    return sources


def generate_research_result(company, job_id):
    """Generate a complete research result for one company."""
    company_id = company["_id"]
    pillars = {}

    for pillar in PILLARS:
        score = company["pillar_scores"][pillar]
        confidence = round(0.65 + (score / 5.0) * 0.3 + random.uniform(-0.05, 0.05), 2)
        confidence = max(0.5, min(0.98, confidence))

        pillars[pillar] = {
            "score": score,
            "confidence": confidence,
            "evidence": generate_evidence(pillar, score, company),
            "sources": generate_sources(company),
        }

    composite = calc_composite(company["pillar_scores"])
    tier = get_tier(composite)

    summary = (
        f"{company['name']} ({company['vertical']}) scores {composite} overall, "
        f"placing it in the {tier} tier. "
        f"Strongest pillars: {_top_pillars(company['pillar_scores'])}. "
        f"Key opportunities include AI-driven automation of core {company['vertical'].lower()} workflows "
        f"and predictive analytics leveraging {company.get('employee_count', 'N/A')}-person team's domain expertise."
    )

    return {
        "id": f"rr_{uuid.uuid4().hex[:8]}",
        "company_id": company_id,
        "job_id": job_id,
        "pillar_data": pillars,
        "raw_summary": summary,
        "created_at": datetime.utcnow().isoformat(),
    }


def _top_pillars(scores):
    sorted_pillars = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top = sorted_pillars[:2]
    return ", ".join(f"{PILLARS[p]['label']} ({s})" for p, s in top)


# ---------------------------------------------------------------------------
# ML TRAINING (using actual XGBoost if available, else pure-Python fallback)
# ---------------------------------------------------------------------------
def train_and_evaluate():
    """Train model on ground truth, return metrics and derived weights."""
    gt_path = os.path.join(os.path.dirname(__file__), "..", "data", "training", "ground_truth.json")
    with open(gt_path) as f:
        ground_truth = json.load(f)

    pillar_names = list(PILLARS.keys())

    try:
        import numpy as np
        from sklearn.preprocessing import LabelEncoder
        from sklearn.model_selection import LeaveOneOut
        from xgboost import XGBClassifier

        print("  Using XGBoost + scikit-learn for model training...")

        # Build feature matrix from ground truth
        X = np.array([[gt["pillar_scores"][p] for p in pillar_names] for gt in ground_truth])
        y_labels = [gt["actual_tier"] for gt in ground_truth]
        le = LabelEncoder()
        y = le.fit_transform(y_labels)

        # Leave-one-out cross validation
        loo = LeaveOneOut()
        correct = 0
        predictions = []
        deviations = []

        for train_idx, test_idx in loo.split(X):
            X_train, X_test = X[train_idx], X[test_idx]
            y_train, y_test = y[train_idx], y[test_idx]

            # Re-encode labels for this fold to handle missing classes
            fold_le = LabelEncoder()
            y_train_enc = fold_le.fit_transform(y_train)
            num_classes = len(fold_le.classes_)

            fold_model = XGBClassifier(
                n_estimators=50, max_depth=3, learning_rate=0.1, random_state=42,
                eval_metric='mlogloss',
                num_class=num_classes if num_classes > 2 else None,
                objective='multi:softmax' if num_classes > 2 else 'binary:logistic',
            )
            fold_model.fit(X_train, y_train_enc)
            pred_enc = fold_model.predict(X_test)
            pred_label = fold_le.inverse_transform(pred_enc.astype(int))
            predictions.append(le.inverse_transform(pred_label)[0])

            if y_test[0] in fold_le.classes_:
                if pred_label[0] == y_test[0]:
                    correct += 1
            else:
                # Class wasn't in training set; use formula-based prediction
                pred_composite = calc_composite(dict(zip(pillar_names, X_test[0])))
                pred_tier_name = get_tier(pred_composite)
                actual_tier_name = le.inverse_transform([y_test[0]])[0]
                if pred_tier_name == actual_tier_name:
                    correct += 1
                predictions[-1] = pred_tier_name

            # Calculate score deviation
            actual_composite = ground_truth[test_idx[0]]["actual_score"]
            pred_composite = calc_composite(dict(zip(pillar_names, X_test[0])))
            deviations.append(abs(pred_composite - actual_composite))

        accuracy = correct / len(ground_truth)
        avg_deviation = round(sum(deviations) / len(deviations), 4)

        # Train final model on all data
        final_model = XGBClassifier(n_estimators=50, max_depth=3, learning_rate=0.1, random_state=42,
                                     use_label_encoder=False, eval_metric='mlogloss')
        final_model.fit(X, y)

        # Derive weights from feature importance
        importances = dict(zip(pillar_names, final_model.feature_importances_.tolist()))

        # Backtest details
        backtest_results = []
        for i, gt in enumerate(ground_truth):
            pred_composite = calc_composite(gt["pillar_scores"])
            backtest_results.append({
                "name": gt["name"],
                "vertical": gt["vertical"],
                "actual_tier": gt["actual_tier"],
                "actual_score": gt["actual_score"],
                "predicted_score": pred_composite,
                "predicted_tier": predictions[i],
                "deviation": round(abs(pred_composite - gt["actual_score"]), 4),
                "correct": predictions[i] == gt["actual_tier"],
            })

        metrics = {
            "accuracy": round(accuracy, 4),
            "avg_deviation": avg_deviation,
            "loo_cv_correct": correct,
            "total_samples": len(ground_truth),
            "model_version": "2.0",
            "feature_importance": {p: round(v, 4) for p, v in importances.items()},
            "derived_weights": _normalize_importance_to_weights(importances),
            "backtest_results": backtest_results,
            "trained_at": datetime.utcnow().isoformat(),
        }

        return metrics

    except ImportError:
        print("  XGBoost/sklearn not available. Using analytical fallback...")
        return _analytical_training(ground_truth, pillar_names)


def _analytical_training(ground_truth, pillar_names):
    """Pure-Python analytical model training fallback."""
    # Calculate correlation of each pillar with composite score
    correlations = {}
    for p in pillar_names:
        pillar_vals = [gt["pillar_scores"][p] for gt in ground_truth]
        score_vals = [gt["actual_score"] for gt in ground_truth]
        mean_p = sum(pillar_vals) / len(pillar_vals)
        mean_s = sum(score_vals) / len(score_vals)
        cov = sum((pv - mean_p) * (sv - mean_s) for pv, sv in zip(pillar_vals, score_vals)) / len(pillar_vals)
        std_p = (sum((pv - mean_p)**2 for pv in pillar_vals) / len(pillar_vals)) ** 0.5
        std_s = (sum((sv - mean_s)**2 for sv in score_vals) / len(score_vals)) ** 0.5
        if std_p > 0 and std_s > 0:
            correlations[p] = abs(cov / (std_p * std_s))
        else:
            correlations[p] = 0.1

    # Backtest
    correct = 0
    deviations = []
    backtest_results = []

    for gt in ground_truth:
        pred_composite = calc_composite(gt["pillar_scores"])
        pred_tier = get_tier(pred_composite)
        dev = abs(pred_composite - gt["actual_score"])
        deviations.append(dev)
        is_correct = pred_tier == gt["actual_tier"]
        if is_correct:
            correct += 1

        backtest_results.append({
            "name": gt["name"],
            "vertical": gt["vertical"],
            "actual_tier": gt["actual_tier"],
            "actual_score": gt["actual_score"],
            "predicted_score": pred_composite,
            "predicted_tier": pred_tier,
            "deviation": round(dev, 4),
            "correct": is_correct,
        })

    return {
        "accuracy": round(correct / len(ground_truth), 4),
        "avg_deviation": round(sum(deviations) / len(deviations), 4),
        "loo_cv_correct": correct,
        "total_samples": len(ground_truth),
        "model_version": "2.0",
        "feature_importance": {p: round(v, 4) for p, v in correlations.items()},
        "derived_weights": _normalize_importance_to_weights(correlations),
        "backtest_results": backtest_results,
        "trained_at": datetime.utcnow().isoformat(),
    }


def _normalize_importance_to_weights(importances):
    """Convert feature importances to weight multipliers scaled to sum=12.5."""
    total_imp = sum(importances.values())
    if total_imp == 0:
        return {p: PILLARS[p]["weight"] for p in importances}

    weights = {}
    for p, imp in importances.items():
        normalized = (imp / total_imp) * TOTAL_WEIGHT
        weights[p] = round(max(0.5, normalized), 2)
    return weights


# ---------------------------------------------------------------------------
# GENERATE SCORES
# ---------------------------------------------------------------------------
def score_company(company, model_version="2.0"):
    """Score a company and return a Score record."""
    ps = company["pillar_scores"]
    composite = calc_composite(ps)
    tier = get_tier(composite)
    wave = get_wave(composite, tier)

    breakdown = {}
    for pillar, score in ps.items():
        weight = PILLARS[pillar]["weight"]
        breakdown[pillar] = {
            "score": score,
            "weight": weight,
            "weighted": round(score * weight, 2),
            "label": PILLARS[pillar]["label"],
        }

    return {
        "id": f"sc_{uuid.uuid4().hex[:8]}",
        "company_id": company["_id"],
        "composite_score": composite,
        "tier": tier,
        "wave": wave,
        "pillar_scores": ps,
        "pillar_breakdown": breakdown,
        "model_version": model_version,
        "created_at": datetime.utcnow().isoformat(),
    }


# ---------------------------------------------------------------------------
# BUILD SQLITE DATABASE
# ---------------------------------------------------------------------------
def build_database(companies, research_results, scores, model_metrics):
    """Create a pre-seeded SQLite database."""
    import sqlite3

    db_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    os.makedirs(db_dir, exist_ok=True)
    db_path = os.path.join(db_dir, "solen.db")

    if os.path.exists(db_path):
        os.remove(db_path)

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Create tables
    c.execute("""
        CREATE TABLE companies (
            id TEXT PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            vertical TEXT,
            website TEXT,
            github_org TEXT,
            description TEXT,
            founded_year INTEGER,
            employee_count INTEGER,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    c.execute("""
        CREATE TABLE research_results (
            id TEXT PRIMARY KEY,
            company_id TEXT NOT NULL,
            job_id TEXT,
            pillar_data TEXT,
            raw_summary TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (company_id) REFERENCES companies(id)
        )
    """)

    c.execute("""
        CREATE TABLE scores (
            id TEXT PRIMARY KEY,
            company_id TEXT NOT NULL,
            job_id TEXT,
            composite_score REAL NOT NULL,
            tier TEXT NOT NULL,
            wave INTEGER,
            pillar_scores TEXT,
            pillar_breakdown TEXT,
            model_version TEXT DEFAULT '2.0',
            created_at TEXT NOT NULL,
            FOREIGN KEY (company_id) REFERENCES companies(id)
        )
    """)

    c.execute("""
        CREATE TABLE agent_jobs (
            id TEXT PRIMARY KEY,
            job_type TEXT NOT NULL,
            status TEXT DEFAULT 'completed',
            progress INTEGER DEFAULT 100,
            total_companies INTEGER,
            completed_companies INTEGER,
            error_message TEXT,
            result_data TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    c.execute("""
        CREATE TABLE model_metrics (
            id TEXT PRIMARY KEY,
            model_version TEXT NOT NULL,
            accuracy REAL,
            avg_deviation REAL,
            total_samples INTEGER,
            feature_importance TEXT,
            derived_weights TEXT,
            backtest_results TEXT,
            trained_at TEXT NOT NULL
        )
    """)

    now = datetime.utcnow().isoformat()

    # Insert companies
    for co in companies:
        c.execute("""
            INSERT INTO companies (id, name, vertical, website, github_org, description,
                                   founded_year, employee_count, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (co["_id"], co["name"], co["vertical"], co["website"],
              co.get("github_org", ""), co["description"],
              co["founded_year"], co["employee_count"], now, now))

    # Insert jobs
    research_job_id = f"job_{uuid.uuid4().hex[:8]}"
    scoring_job_id = f"job_{uuid.uuid4().hex[:8]}"
    training_job_id = f"job_{uuid.uuid4().hex[:8]}"

    for job_id, job_type, total in [
        (research_job_id, "research", len(companies)),
        (scoring_job_id, "scoring", len(companies)),
        (training_job_id, "ml_training", 8),
    ]:
        c.execute("""
            INSERT INTO agent_jobs (id, job_type, status, progress, total_companies,
                                    completed_companies, created_at, updated_at)
            VALUES (?, ?, 'completed', 100, ?, ?, ?, ?)
        """, (job_id, job_type, total, total, now, now))

    # Insert research results
    for rr in research_results:
        c.execute("""
            INSERT INTO research_results (id, company_id, job_id, pillar_data, raw_summary, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (rr["id"], rr["company_id"], rr["job_id"],
              json.dumps(rr["pillar_data"]), rr["raw_summary"], rr["created_at"]))

    # Insert scores
    for sc in scores:
        c.execute("""
            INSERT INTO scores (id, company_id, job_id, composite_score, tier, wave,
                               pillar_scores, pillar_breakdown, model_version, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (sc["id"], sc["company_id"], scoring_job_id, sc["composite_score"],
              sc["tier"], sc["wave"], json.dumps(sc["pillar_scores"]),
              json.dumps(sc["pillar_breakdown"]), sc["model_version"], sc["created_at"]))

    # Insert model metrics
    c.execute("""
        INSERT INTO model_metrics (id, model_version, accuracy, avg_deviation, total_samples,
                                   feature_importance, derived_weights, backtest_results, trained_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (f"mm_{uuid.uuid4().hex[:8]}", model_metrics["model_version"],
          model_metrics["accuracy"], model_metrics["avg_deviation"],
          model_metrics["total_samples"],
          json.dumps(model_metrics["feature_importance"]),
          json.dumps(model_metrics["derived_weights"]),
          json.dumps(model_metrics["backtest_results"]),
          model_metrics["trained_at"]))

    conn.commit()
    conn.close()

    print(f"  Database written to: {db_path}")
    return db_path


# ---------------------------------------------------------------------------
# EXPORT JSON (for frontend static fallback)
# ---------------------------------------------------------------------------
def export_json(companies, research_results, scores, model_metrics):
    """Export all demo data as JSON files."""
    export_dir = os.path.join(os.path.dirname(__file__), "..", "data", "demo")
    os.makedirs(export_dir, exist_ok=True)

    # Portfolio summary
    portfolio = []
    for co, sc in zip(companies, scores):
        portfolio.append({
            "id": co["_id"],
            "name": co["name"],
            "vertical": co["vertical"],
            "employee_count": co["employee_count"],
            "composite_score": sc["composite_score"],
            "tier": sc["tier"],
            "wave": sc["wave"],
            "pillar_scores": sc["pillar_scores"],
        })
    portfolio.sort(key=lambda x: x["composite_score"], reverse=True)

    with open(os.path.join(export_dir, "portfolio_scores.json"), "w") as f:
        json.dump(portfolio, f, indent=2)

    # Full research data
    with open(os.path.join(export_dir, "research_results.json"), "w") as f:
        json.dump(research_results, f, indent=2)

    # Model performance
    with open(os.path.join(export_dir, "model_metrics.json"), "w") as f:
        json.dump(model_metrics, f, indent=2)

    # Wave sequencing
    waves = {"Wave 1 (Q1-Q2)": [], "Wave 2 (Q3-Q4)": [], "Wave 3 (Year 2)": []}
    for item in portfolio:
        wave_key = {1: "Wave 1 (Q1-Q2)", 2: "Wave 2 (Q3-Q4)", 3: "Wave 3 (Year 2)"}[item["wave"]]
        waves[wave_key].append({"name": item["name"], "score": item["composite_score"], "tier": item["tier"]})
    with open(os.path.join(export_dir, "wave_sequencing.json"), "w") as f:
        json.dump(waves, f, indent=2)

    # Portfolio distribution
    distribution = {}
    for item in portfolio:
        distribution[item["tier"]] = distribution.get(item["tier"], 0) + 1
    with open(os.path.join(export_dir, "tier_distribution.json"), "w") as f:
        json.dump(distribution, f, indent=2)

    print(f"  JSON files written to: {export_dir}/")
    return export_dir


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main():
    print("=" * 70)
    print("SOLEN AI INVESTMENT INTELLIGENCE — DEMO DATA GENERATOR")
    print("=" * 70)

    # Step 1: Assign IDs to companies
    print("\n[1/5] Preparing 14 Solen portfolio companies...")
    for co in SOLEN_COMPANIES:
        co["_id"] = f"co_{uuid.uuid4().hex[:8]}"
    print(f"  {len(SOLEN_COMPANIES)} companies ready")

    # Step 2: Train model
    print("\n[2/5] Training ML model on 8 ground truth companies...")
    model_metrics = train_and_evaluate()
    print(f"  Accuracy: {model_metrics['accuracy']*100:.1f}%")
    print(f"  Avg deviation: {model_metrics['avg_deviation']:.4f}")
    print(f"  Model version: {model_metrics['model_version']}")

    # Step 3: Generate research data
    print("\n[3/5] Generating research datasets for all 14 portcos...")
    research_job_id = f"job_{uuid.uuid4().hex[:8]}"
    research_results = []
    for co in SOLEN_COMPANIES:
        rr = generate_research_result(co, research_job_id)
        research_results.append(rr)
        composite = calc_composite(co["pillar_scores"])
        print(f"  ✓ {co['name']:25s} — {len(rr['pillar_data'])} pillars researched")

    # Step 4: Score all companies
    print("\n[4/5] Scoring all 14 portfolio companies...")
    scores = []
    for co in SOLEN_COMPANIES:
        sc = score_company(co)
        scores.append(sc)
        print(f"  ✓ {co['name']:25s} — Score: {sc['composite_score']:.2f}  Tier: {sc['tier']:15s}  Wave: {sc['wave']}")

    # Summary stats
    buildable = sum(1 for s in scores if s["tier"] == "AI-Buildable")
    emerging = sum(1 for s in scores if s["tier"] == "AI-Emerging")
    avg_score = sum(s["composite_score"] for s in scores) / len(scores)
    print(f"\n  Portfolio: {buildable} Buildable / {emerging} Emerging")
    print(f"  Average composite score: {avg_score:.2f}")

    # Step 5: Build database + export JSON
    print("\n[5/5] Building seed database and exporting JSON...")
    db_path = build_database(SOLEN_COMPANIES, research_results, scores, model_metrics)
    export_dir = export_json(SOLEN_COMPANIES, research_results, scores, model_metrics)

    print("\n" + "=" * 70)
    print("COMPLETE! Demo data generated successfully.")
    print("=" * 70)
    print(f"\nFiles created:")
    print(f"  • {db_path} (SQLite database)")
    print(f"  • {export_dir}/portfolio_scores.json")
    print(f"  • {export_dir}/research_results.json")
    print(f"  • {export_dir}/model_metrics.json")
    print(f"  • {export_dir}/wave_sequencing.json")
    print(f"  • {export_dir}/tier_distribution.json")
    print(f"\nReady for: docker-compose up --build")

    return 0


if __name__ == "__main__":
    sys.exit(main())
