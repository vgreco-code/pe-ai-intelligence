#!/usr/bin/env python3
"""
Retrain the scoring model on the 16-dimension v2 training set (515 companies),
backtest against 28 ground truth companies, re-score the 14 Solen portfolio
companies, and update all demo data outputs.

Model version: 4.0
Framework: 16 dimensions × 5 supercategories
"""
import json
import os
import sys
import uuid
import sqlite3
from datetime import datetime
from collections import defaultdict

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix
from xgboost import XGBClassifier

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------------------
# 17-DIMENSION FRAMEWORK (16 maturity + 1 velocity)
# ---------------------------------------------------------------------------
DIMENSIONS = {
    # DATA & ANALYTICS FOUNDATION
    "data_quality":          {"weight": 1.5, "label": "Data Quality & Availability",  "category": "Data & Analytics"},
    "data_integration":      {"weight": 1.0, "label": "Data Integration & APIs",      "category": "Data & Analytics"},
    "analytics_maturity":    {"weight": 1.0, "label": "Analytics Maturity",            "category": "Data & Analytics"},
    # TECHNOLOGY & INFRASTRUCTURE
    "cloud_architecture":    {"weight": 1.0, "label": "Cloud Architecture",            "category": "Technology & Infrastructure"},
    "tech_stack_modernity":  {"weight": 0.8, "label": "Tech Stack Modernity",          "category": "Technology & Infrastructure"},
    "ai_engineering":        {"weight": 1.5, "label": "AI/ML Engineering",             "category": "Technology & Infrastructure"},
    # AI PRODUCT & VALUE CREATION
    "ai_product_features":   {"weight": 1.5, "label": "AI Product Features",           "category": "AI Product & Value"},
    "revenue_ai_upside":     {"weight": 1.5, "label": "Revenue AI Upside",             "category": "AI Product & Value"},
    "margin_ai_upside":      {"weight": 1.0, "label": "Margin AI Upside",              "category": "AI Product & Value"},
    "product_differentiation":{"weight": 1.2, "label": "Product Differentiation",      "category": "AI Product & Value"},
    # ORGANIZATION & TALENT
    "ai_talent_density":     {"weight": 1.2, "label": "AI Talent Density",             "category": "Organization & Talent"},
    "leadership_ai_vision":  {"weight": 1.0, "label": "Leadership AI Vision",          "category": "Organization & Talent"},
    "org_change_readiness":  {"weight": 0.8, "label": "Org Change Readiness",          "category": "Organization & Talent"},
    "partner_ecosystem":     {"weight": 0.8, "label": "Partner Ecosystem",             "category": "Organization & Talent"},
    # GOVERNANCE & RISK
    "ai_governance":         {"weight": 0.6, "label": "AI Governance",                 "category": "Governance & Risk"},
    "regulatory_readiness":  {"weight": 0.6, "label": "Regulatory Readiness",          "category": "Governance & Risk"},
    # VELOCITY & MOMENTUM
    "ai_momentum":           {"weight": 1.3, "label": "AI Momentum",                   "category": "Velocity & Momentum"},
}

DIMENSION_NAMES = list(DIMENSIONS.keys())
TOTAL_WEIGHT = sum(d["weight"] for d in DIMENSIONS.values())
TIERS = [("AI-Ready", 4.0), ("AI-Buildable", 3.2), ("AI-Emerging", 2.5), ("AI-Limited", 0)]

CATEGORIES = {
    "Data & Analytics": ["data_quality", "data_integration", "analytics_maturity"],
    "Technology & Infrastructure": ["cloud_architecture", "tech_stack_modernity", "ai_engineering"],
    "AI Product & Value": ["ai_product_features", "revenue_ai_upside", "margin_ai_upside", "product_differentiation"],
    "Organization & Talent": ["ai_talent_density", "leadership_ai_vision", "org_change_readiness", "partner_ecosystem"],
    "Governance & Risk": ["ai_governance", "regulatory_readiness"],
    "Velocity & Momentum": ["ai_momentum"],
}


def calc_composite(pillars, weights=None):
    w = weights or {d: DIMENSIONS[d]["weight"] for d in DIMENSION_NAMES}
    tw = sum(w.values())
    return round(sum(pillars[d] * w[d] for d in DIMENSION_NAMES) / tw, 2)


def get_tier(score):
    for name, threshold in TIERS:
        if score >= threshold:
            return name
    return "AI-Limited"


# ---------------------------------------------------------------------------
# MAP 8-PILLAR PORTFOLIO SCORES → 16 DIMENSIONS
# ---------------------------------------------------------------------------
def map_8_to_16(ps8, company_info=None):
    """Convert legacy 8-pillar scores to 16-dimension scores."""
    co = company_info or {}
    emp = co.get("employee_count", 100)
    founded = co.get("founded_year", 2005)

    return {
        "data_quality":          ps8["data_quality"],
        "data_integration":      round(ps8["data_quality"] * 0.6 + ps8["infrastructure"] * 0.4, 1),
        "analytics_maturity":    round(ps8["data_quality"] * 0.5 + ps8["workflow_digitization"] * 0.3 + ps8["revenue_upside"] * 0.2, 1),
        "cloud_architecture":    round(ps8["infrastructure"] * 0.8 + (0.3 if founded > 2010 else 0), 1),
        "tech_stack_modernity":  round(ps8["infrastructure"] * 0.7 + ps8["workflow_digitization"] * 0.3, 1),
        "ai_engineering":        round(ps8["infrastructure"] * 0.4 + ps8["data_quality"] * 0.3 + (0.5 if ps8.get("data_quality", 0) > 3.5 else 0), 1),
        "ai_product_features":   round(ps8["workflow_digitization"] * 0.4 + ps8["data_quality"] * 0.3 + ps8["revenue_upside"] * 0.3, 1),
        "revenue_ai_upside":     ps8["revenue_upside"],
        "margin_ai_upside":      ps8["margin_upside"],
        "product_differentiation": round(ps8["competitive_position"] * 0.7 + ps8["data_quality"] * 0.3, 1),
        "ai_talent_density":     round(ps8["org_readiness"] * 0.5 + ps8["infrastructure"] * 0.3 + (0.3 if emp > 100 else 0), 1),
        "leadership_ai_vision":  round(ps8["org_readiness"] * 0.6 + ps8["competitive_position"] * 0.4, 1),
        "org_change_readiness":  ps8["org_readiness"],
        "partner_ecosystem":     round(ps8["competitive_position"] * 0.5 + ps8["workflow_digitization"] * 0.3 + ps8["infrastructure"] * 0.2, 1),
        "ai_governance":         round(ps8["risk_compliance"] * 0.6 + ps8["org_readiness"] * 0.4, 1),
        "regulatory_readiness":  ps8["risk_compliance"],
        "ai_momentum":           round(ps8.get("workflow_digitization", 2.5) * 0.4 + ps8.get("data_quality", 2.5) * 0.3 + (0.5 if founded > 2015 else 0.0) + (0.3 if emp > 50 else 0.0), 1),
    }


# ---------------------------------------------------------------------------
# LOAD TRAINING DATA
# ---------------------------------------------------------------------------
print("=" * 70)
print("MODEL RETRAINING v4.1 — 17-Dimension Framework (16 maturity + velocity)")
print("=" * 70)

with open(os.path.join(BASE_DIR, "data", "training", "training_set_v2_real.json")) as f:
    training_data = json.load(f)

print(f"\n[1/7] Loaded {len(training_data)} training companies (16 dimensions)")

# Build feature matrix
X_data = []
y_labels = []
company_names = []
company_lookup = {}

for co in training_data:
    ps = co["pillars"]
    features = [ps[d] for d in DIMENSION_NAMES]
    X_data.append(features)
    y_labels.append(co["tier"])
    company_names.append(co["name"])
    company_lookup[co["name"]] = co

X = np.array(X_data)
le = LabelEncoder()
y = le.fit_transform(y_labels)

print(f"  Features: {X.shape[1]} dimensions × {X.shape[0]} companies")
print(f"  Classes: {list(le.classes_)}")
tier_dist = {}
for t in y_labels:
    tier_dist[t] = tier_dist.get(t, 0) + 1
print(f"  Distribution: {tier_dist}")

# ---------------------------------------------------------------------------
# TRAIN WITH STRATIFIED K-FOLD CV
# ---------------------------------------------------------------------------
print(f"\n[2/7] Training XGBoost with 5-fold stratified CV...")

model = XGBClassifier(
    n_estimators=150,
    max_depth=5,
    learning_rate=0.08,
    random_state=42,
    eval_metric='mlogloss',
    min_child_weight=2,
    subsample=0.85,
    colsample_bytree=0.85,
    gamma=0.1,
    reg_alpha=0.1,
    reg_lambda=1.0,
)

skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
cv_scores = cross_val_score(model, X, y, cv=skf, scoring='accuracy')

print(f"  5-Fold CV Accuracy: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")
print(f"  Per-fold: {[f'{s:.3f}' for s in cv_scores]}")

# Train final model on all data
model.fit(X, y)

# Feature importance → dimension weights
importances = dict(zip(DIMENSION_NAMES, model.feature_importances_.tolist()))
print(f"\n[3/7] Feature importance (derived dimension weights):")
sorted_imp = sorted(importances.items(), key=lambda x: -x[1])
for d, v in sorted_imp:
    bar = "█" * int(v * 60)
    print(f"  {DIMENSIONS[d]['label']:35s} {v:.4f} {bar}")

# Derive weights from importance
total_imp = sum(importances.values())
derived_weights = {}
for d, imp in importances.items():
    derived_weights[d] = round((imp / total_imp) * TOTAL_WEIGHT, 3) if total_imp > 0 else DIMENSIONS[d]["weight"]

print(f"\n  Derived weights (scaled to sum={TOTAL_WEIGHT}):")
for d, w in sorted(derived_weights.items(), key=lambda x: -x[1]):
    orig = DIMENSIONS[d]["weight"]
    diff = w - orig
    arrow = "↑" if diff > 0.05 else "↓" if diff < -0.05 else "≈"
    print(f"    {DIMENSIONS[d]['label']:35s} {w:.3f} (was {orig:.1f}) {arrow}")

# Category-level importance
print(f"\n  Category importance:")
for cat, dims in CATEGORIES.items():
    cat_imp = sum(importances.get(d, 0) for d in dims)
    bar = "█" * int(cat_imp * 40)
    print(f"    {cat:35s} {cat_imp:.4f} {bar}")

# ---------------------------------------------------------------------------
# BACKTEST against 28 ground truth companies
# ---------------------------------------------------------------------------
print(f"\n[4/7] Backtesting against expanded ground truth...")

with open(os.path.join(BASE_DIR, "data", "training", "ground_truth_v2.json")) as f:
    ground_truth = json.load(f)

backtest_results = []
correct = 0
adjacent_correct = 0
deviations = []
tier_order = ["AI-Limited", "AI-Emerging", "AI-Buildable", "AI-Ready"]

for gt in ground_truth:
    name = gt["name"]

    # Try to find in training set (has 16-dim scores)
    if name in company_lookup:
        co = company_lookup[name]
        ps = co["pillars"]
    elif name.replace(" (Legacy)", "") in company_lookup:
        co = company_lookup[name.replace(" (Legacy)", "")]
        ps = co["pillars"]
    else:
        # For companies not in training set, check if they have 8-pillar scores
        # in the v1 ground truth, and map them
        v1_gt_path = os.path.join(BASE_DIR, "data", "training", "ground_truth.json")
        with open(v1_gt_path) as f:
            v1_gt = json.load(f)
        v1_match = next((g for g in v1_gt if g["name"] == name or g["name"] in name), None)
        if v1_match and "pillar_scores" in v1_match:
            ps = map_8_to_16(v1_match["pillar_scores"])
        else:
            print(f"  ⚠ Skipping {name} — no pillar scores available")
            continue

    features = np.array([[ps[d] for d in DIMENSION_NAMES]])

    # Predict tier
    pred_class = model.predict(features)[0]
    pred_tier = le.inverse_transform([pred_class])[0]

    # Calculate composite with derived weights
    pred_composite = calc_composite(ps, derived_weights)
    actual_score = gt["actual_score"]
    dev = abs(pred_composite - actual_score)
    deviations.append(dev)

    is_correct = pred_tier == gt["actual_tier"]
    if is_correct:
        correct += 1

    # Adjacent tier accuracy (within 1 tier)
    pred_idx = tier_order.index(pred_tier) if pred_tier in tier_order else -1
    actual_idx = tier_order.index(gt["actual_tier"]) if gt["actual_tier"] in tier_order else -1
    is_adjacent = abs(pred_idx - actual_idx) <= 1
    if is_adjacent:
        adjacent_correct += 1

    backtest_results.append({
        "name": name,
        "vertical": gt["vertical"],
        "actual_tier": gt["actual_tier"],
        "actual_score": actual_score,
        "predicted_score": pred_composite,
        "predicted_tier": pred_tier,
        "deviation": round(dev, 4),
        "correct": is_correct,
        "adjacent_correct": is_adjacent,
    })

    status = "✓" if is_correct else ("~" if is_adjacent else "✗")
    print(f"  {status} {name:25s} actual={gt['actual_tier']:15s} predicted={pred_tier:15s} dev={dev:.3f}")

n_tested = len(backtest_results)
bt_accuracy = correct / n_tested if n_tested > 0 else 0
adj_accuracy = adjacent_correct / n_tested if n_tested > 0 else 0
avg_dev = sum(deviations) / len(deviations) if deviations else 0

print(f"\n  Exact accuracy:    {bt_accuracy*100:.1f}% ({correct}/{n_tested})")
print(f"  Adjacent accuracy: {adj_accuracy*100:.1f}% ({adjacent_correct}/{n_tested})")
print(f"  Avg score deviation: {avg_dev:.4f}")

# Confusion matrix
actual_tiers_bt = [r["actual_tier"] for r in backtest_results]
pred_tiers_bt = [r["predicted_tier"] for r in backtest_results]
if actual_tiers_bt:
    print(f"\n  Confusion matrix:")
    labels = sorted(set(actual_tiers_bt + pred_tiers_bt))
    cm = confusion_matrix(actual_tiers_bt, pred_tiers_bt, labels=labels)
    print(f"  {'':15s} " + " ".join(f"{l:15s}" for l in labels))
    for i, row in enumerate(cm):
        print(f"  {labels[i]:15s} " + " ".join(f"{v:15d}" for v in row))

# ---------------------------------------------------------------------------
# RE-SCORE SOLEN PORTFOLIO with 16 dimensions
# ---------------------------------------------------------------------------
print(f"\n[5/7] Re-scoring 14 Solen portfolio companies with 17-dimension model...")

sys.path.insert(0, os.path.join(BASE_DIR, "scripts"))
from generate_demo_data import SOLEN_COMPANIES, generate_research_result, generate_evidence, generate_sources

# Load portfolio velocity data if available
portfolio_velocity_path = os.path.join(BASE_DIR, "data", "research", "portfolio_velocity.json")
portfolio_velocity = {}
if os.path.exists(portfolio_velocity_path):
    with open(portfolio_velocity_path) as f:
        portfolio_velocity = json.load(f)
    print(f"  Loaded velocity data for {len(portfolio_velocity)} portfolio companies")

scored_portfolio = []
for co in SOLEN_COMPANIES:
    ps8 = co.get("pillar_scores", {})
    ps16 = map_8_to_16(ps8, co)

    # Inject real momentum score from velocity scraping
    vel = portfolio_velocity.get(co["name"], {})
    if vel.get("ai_momentum"):
        ps16["ai_momentum"] = vel["ai_momentum"]

    features = np.array([[ps16[d] for d in DIMENSION_NAMES]])

    # Model prediction
    pred_class = model.predict(features)[0]
    model_tier = le.inverse_transform([pred_class])[0]

    # Composite scores
    composite_original = calc_composite(ps16)
    composite_derived = calc_composite(ps16, derived_weights)

    # Use composite-based tier (more stable than model prediction for edge cases)
    tier = get_tier(composite_original)
    wave = 1 if composite_original >= 3.2 else (2 if composite_original >= 2.8 else 3)

    # Category averages
    category_scores = {}
    for cat, dims in CATEGORIES.items():
        cat_scores = [ps16[d] for d in dims]
        category_scores[cat] = round(sum(cat_scores) / len(cat_scores), 2)

    # Dimension breakdown
    breakdown = {}
    for dim, score in ps16.items():
        weight = DIMENSIONS[dim]["weight"]
        breakdown[dim] = {
            "score": score,
            "weight": weight,
            "weighted": round(score * weight, 2),
            "label": DIMENSIONS[dim]["label"],
            "category": DIMENSIONS[dim]["category"],
            "derived_weight": derived_weights.get(dim, weight),
        }

    scored_portfolio.append({
        "name": co["name"],
        "vertical": co["vertical"],
        "employee_count": co.get("employee_count", 0),
        "description": co.get("description", ""),
        "website": co.get("website", ""),
        "founded_year": co.get("founded_year", 0),
        "composite_score": composite_original,
        "composite_score_derived": composite_derived,
        "tier": tier,
        "model_predicted_tier": model_tier,
        "wave": wave,
        "pillar_scores": ps16,
        "pillar_breakdown": breakdown,
        "category_scores": category_scores,
        "legacy_8_pillar": ps8,
        "ai_hiring_signals": vel.get("ai_hiring_signals", 0),
        "recent_ai_signals": vel.get("recent_ai_signals", 0),
    })

    tier_match = "✓" if tier == model_tier else f"(model: {model_tier})"
    print(f"  {co['name']:25s}  Score: {composite_original:.2f}  Tier: {tier:15s}  Wave: {wave}  {tier_match}")

# Sort by score
scored_portfolio.sort(key=lambda x: x["composite_score"], reverse=True)

# Portfolio summary
tier_counts = defaultdict(int)
for s in scored_portfolio:
    tier_counts[s["tier"]] += 1
avg_score = sum(s["composite_score"] for s in scored_portfolio) / len(scored_portfolio)
print(f"\n  Portfolio summary: {dict(tier_counts)}")
print(f"  Average score: {avg_score:.2f}")

# ---------------------------------------------------------------------------
# SAVE ALL OUTPUTS
# ---------------------------------------------------------------------------
print(f"\n[6/7] Saving outputs...")

demo_dir = os.path.join(BASE_DIR, "data", "demo")
os.makedirs(demo_dir, exist_ok=True)

# 1. Model metrics
model_metrics = {
    "model_version": "4.1",
    "framework": "17-dimension (16 maturity + velocity)",
    "training_set_size": len(training_data),
    "num_dimensions": 17,
    "cv_accuracy": round(float(cv_scores.mean()), 4),
    "cv_std": round(float(cv_scores.std()), 4),
    "cv_folds": 5,
    "backtest_accuracy": round(bt_accuracy, 4),
    "backtest_adjacent_accuracy": round(adj_accuracy, 4),
    "backtest_avg_deviation": round(avg_dev, 4),
    "backtest_count": n_tested,
    "backtest_results": backtest_results,
    "feature_importance": {d: round(float(v), 4) for d, v in importances.items()},
    "derived_weights": derived_weights,
    "original_weights": {d: DIMENSIONS[d]["weight"] for d in DIMENSIONS},
    "categories": {cat: dims for cat, dims in CATEGORIES.items()},
    "dimension_labels": {d: DIMENSIONS[d]["label"] for d in DIMENSIONS},
    "tier_distribution_training": tier_dist,
    "trained_at": datetime.utcnow().isoformat(),
}

with open(os.path.join(demo_dir, "model_metrics.json"), "w") as f:
    json.dump(model_metrics, f, indent=2, default=str)
print(f"  ✓ data/demo/model_metrics.json")

# 2. Portfolio scores
portfolio_export = []
for s in scored_portfolio:
    portfolio_export.append({
        "name": s["name"],
        "vertical": s["vertical"],
        "employee_count": s["employee_count"],
        "description": s["description"],
        "website": s["website"],
        "founded_year": s["founded_year"],
        "composite_score": s["composite_score"],
        "tier": s["tier"],
        "wave": s["wave"],
        "pillar_scores": s["pillar_scores"],
        "category_scores": s["category_scores"],
    })

with open(os.path.join(demo_dir, "portfolio_scores.json"), "w") as f:
    json.dump(portfolio_export, f, indent=2)
print(f"  ✓ data/demo/portfolio_scores.json")

# 3. Wave sequencing
waves = {"Wave 1 (Q1-Q2)": [], "Wave 2 (Q3-Q4)": [], "Wave 3 (Year 2)": []}
for item in scored_portfolio:
    wave_key = {1: "Wave 1 (Q1-Q2)", 2: "Wave 2 (Q3-Q4)", 3: "Wave 3 (Year 2)"}[item["wave"]]
    waves[wave_key].append({
        "name": item["name"],
        "score": item["composite_score"],
        "tier": item["tier"],
        "top_category": max(item["category_scores"].items(), key=lambda x: x[1])[0],
    })
with open(os.path.join(demo_dir, "wave_sequencing.json"), "w") as f:
    json.dump(waves, f, indent=2)
print(f"  ✓ data/demo/wave_sequencing.json")

# 4. Tier distribution
distribution = {}
for item in scored_portfolio:
    distribution[item["tier"]] = distribution.get(item["tier"], 0) + 1
with open(os.path.join(demo_dir, "tier_distribution.json"), "w") as f:
    json.dump(distribution, f, indent=2)
print(f"  ✓ data/demo/tier_distribution.json")

# 5. Generate research results for all 14 companies
research_job_id = f"job_{uuid.uuid4().hex[:8]}"
for co in SOLEN_COMPANIES:
    co["_id"] = f"co_{uuid.uuid4().hex[:8]}"

research_results = [generate_research_result(co, research_job_id) for co in SOLEN_COMPANIES]
with open(os.path.join(demo_dir, "research_results.json"), "w") as f:
    json.dump(research_results, f, indent=2)
print(f"  ✓ data/demo/research_results.json")

# 6. Training stats
training_stats = {
    "total_companies": len(training_data),
    "num_dimensions": 16,
    "framework_version": "v2",
    "verticals": len(set(co["vertical"] for co in training_data)),
    "avg_score": round(float(np.mean([co["composite_score"] for co in training_data])), 2),
    "tier_distribution": tier_dist,
    "dimension_stats": {},
    "top_companies": sorted(training_data, key=lambda x: x["composite_score"], reverse=True)[:10],
}

for d in DIMENSION_NAMES:
    vals = [co["pillars"][d] for co in training_data]
    training_stats["dimension_stats"][d] = {
        "label": DIMENSIONS[d]["label"],
        "category": DIMENSIONS[d]["category"],
        "mean": round(float(np.mean(vals)), 2),
        "std": round(float(np.std(vals)), 2),
        "min": round(float(np.min(vals)), 1),
        "max": round(float(np.max(vals)), 1),
    }

with open(os.path.join(demo_dir, "training_stats.json"), "w") as f:
    json.dump(training_stats, f, indent=2, default=str)
print(f"  ✓ data/demo/training_stats.json")

# 7. Update SQLite database
print(f"\n[7/7] Updating SQLite database...")

db_path = os.path.join(BASE_DIR, "data", "solen.db")
if os.path.exists(db_path):
    os.remove(db_path)

conn = sqlite3.connect(db_path)
c = conn.cursor()

c.execute("""CREATE TABLE companies (
    id TEXT PRIMARY KEY, name TEXT UNIQUE NOT NULL, vertical TEXT, website TEXT,
    github_org TEXT, description TEXT, founded_year INTEGER, employee_count INTEGER,
    created_at TEXT NOT NULL, updated_at TEXT NOT NULL)""")

c.execute("""CREATE TABLE research_results (
    id TEXT PRIMARY KEY, company_id TEXT NOT NULL, job_id TEXT,
    pillar_data TEXT, raw_summary TEXT, created_at TEXT NOT NULL,
    FOREIGN KEY (company_id) REFERENCES companies(id))""")

c.execute("""CREATE TABLE scores (
    id TEXT PRIMARY KEY, company_id TEXT NOT NULL, job_id TEXT,
    composite_score REAL NOT NULL, tier TEXT NOT NULL, wave INTEGER,
    pillar_scores TEXT, pillar_breakdown TEXT, category_scores TEXT,
    model_version TEXT DEFAULT '4.0',
    created_at TEXT NOT NULL,
    FOREIGN KEY (company_id) REFERENCES companies(id))""")

c.execute("""CREATE TABLE agent_jobs (
    id TEXT PRIMARY KEY, job_type TEXT NOT NULL, status TEXT DEFAULT 'completed',
    progress INTEGER DEFAULT 100, total_companies INTEGER, completed_companies INTEGER,
    error_message TEXT, result_data TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL)""")

c.execute("""CREATE TABLE model_metrics (
    id TEXT PRIMARY KEY, model_version TEXT NOT NULL, framework TEXT,
    training_set_size INTEGER, num_dimensions INTEGER,
    accuracy REAL, adjacent_accuracy REAL, avg_deviation REAL,
    total_samples INTEGER, feature_importance TEXT, derived_weights TEXT,
    backtest_results TEXT, trained_at TEXT NOT NULL)""")

now = datetime.utcnow().isoformat()
scoring_job_id = f"job_{uuid.uuid4().hex[:8]}"

for co, sp, rr in zip(SOLEN_COMPANIES, scored_portfolio, research_results):
    c.execute("INSERT INTO companies VALUES (?,?,?,?,?,?,?,?,?,?)",
        (co["_id"], co["name"], co["vertical"], co.get("website",""),
         co.get("github_org",""), co.get("description",""),
         co.get("founded_year"), co.get("employee_count"), now, now))

    score_id = f"sc_{uuid.uuid4().hex[:8]}"
    c.execute("INSERT INTO scores VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (score_id, co["_id"], scoring_job_id, sp["composite_score"],
         sp["tier"], sp["wave"], json.dumps(sp["pillar_scores"]),
         json.dumps(sp["pillar_breakdown"]),
         json.dumps(sp.get("category_scores", {})), "4.0", now))

    c.execute("INSERT INTO research_results VALUES (?,?,?,?,?,?)",
        (rr["id"], co["_id"], rr["job_id"],
         json.dumps(rr["pillar_data"]), rr["raw_summary"], now))

for job_id, job_type in [(research_job_id, "research"), (scoring_job_id, "scoring"),
                          (f"job_{uuid.uuid4().hex[:8]}", "ml_training")]:
    c.execute("INSERT INTO agent_jobs VALUES (?,?,?,?,?,?,?,?,?,?)",
        (job_id, job_type, "completed", 100, 14, 14, None, None, now, now))

c.execute("INSERT INTO model_metrics VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
    (f"mm_{uuid.uuid4().hex[:8]}", "4.0", "16-dimension",
     len(training_data), 16,
     model_metrics["cv_accuracy"], model_metrics["backtest_adjacent_accuracy"],
     model_metrics["backtest_avg_deviation"], n_tested,
     json.dumps(model_metrics["feature_importance"]),
     json.dumps(model_metrics["derived_weights"]),
     json.dumps(model_metrics["backtest_results"]), now))

conn.commit()
conn.close()
print(f"  ✓ data/solen.db")

# 8. Copy to frontend public/
frontend_public = os.path.join(BASE_DIR, "frontend", "public")
os.makedirs(frontend_public, exist_ok=True)

import shutil
for fname in ["model_metrics.json", "portfolio_scores.json", "wave_sequencing.json",
              "tier_distribution.json", "training_stats.json"]:
    src = os.path.join(demo_dir, fname)
    dst = os.path.join(frontend_public, fname)
    shutil.copy2(src, dst)
    print(f"  ✓ frontend/public/{fname}")

# Copy v2 training set for training explorer
shutil.copy2(
    os.path.join(BASE_DIR, "data", "training", "training_set_v2_real.json"),
    os.path.join(frontend_public, "large_training_set.json"),
)
print(f"  ✓ frontend/public/large_training_set.json")

# ---------------------------------------------------------------------------
# SUMMARY
# ---------------------------------------------------------------------------
print("\n" + "=" * 70)
print("RETRAINING COMPLETE — v4.1 (17-Dimension Framework + Velocity)")
print("=" * 70)
print(f"  Model version:      4.1")
print(f"  Dimensions:         17 (in 6 categories, incl. AI Momentum)")
print(f"  Training set:       {len(training_data)} companies")
print(f"  5-Fold CV accuracy: {cv_scores.mean()*100:.1f}%")
print(f"  Backtest accuracy:  {bt_accuracy*100:.1f}% exact / {adj_accuracy*100:.1f}% adjacent")
print(f"  Avg deviation:      {avg_dev:.4f}")
print(f"  Portfolio:          {dict(tier_counts)}")
print(f"  Avg portfolio score:{avg_score:.2f}")
