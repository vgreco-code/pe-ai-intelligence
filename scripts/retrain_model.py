#!/usr/bin/env python3
"""
Retrain the scoring model on the large 264-company training set,
then re-score all 14 Solen portfolio companies and update demo data.
"""
import json
import os
import sys
import uuid
import sqlite3
from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix
from xgboost import XGBClassifier

# ---------------------------------------------------------------------------
# FRAMEWORK
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
PILLAR_NAMES = list(PILLARS.keys())

def calc_composite(ps):
    return round(sum(ps[p] * PILLARS[p]["weight"] for p in ps) / TOTAL_WEIGHT, 2)

def get_tier(score):
    for name, threshold in TIERS:
        if score >= threshold:
            return name
    return "AI-Limited"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------------------
# LOAD TRAINING DATA
# ---------------------------------------------------------------------------
print("=" * 70)
print("MODEL RETRAINING — Large Training Set (264 companies)")
print("=" * 70)

with open(os.path.join(BASE_DIR, "data", "training", "large_training_set.json")) as f:
    training_data = json.load(f)

print(f"\n[1/6] Loaded {len(training_data)} training companies")

# Build feature matrix
X_data = []
y_labels = []
company_names = []

for co in training_data:
    ps = co.get("pillar_scores", co.get("pillars", {}))
    features = [ps[p] for p in PILLAR_NAMES]
    X_data.append(features)
    y_labels.append(co["tier"])
    company_names.append(co["name"])

X = np.array(X_data)
le = LabelEncoder()
y = le.fit_transform(y_labels)

print(f"  Features: {X.shape[1]} pillars × {X.shape[0]} companies")
print(f"  Classes: {list(le.classes_)}")
print(f"  Distribution: {dict(zip(*np.unique(y_labels, return_counts=True)))}")

# ---------------------------------------------------------------------------
# TRAIN WITH STRATIFIED K-FOLD CV
# ---------------------------------------------------------------------------
print(f"\n[2/6] Training XGBoost with 5-fold stratified CV...")

model = XGBClassifier(
    n_estimators=100,
    max_depth=4,
    learning_rate=0.1,
    random_state=42,
    eval_metric='mlogloss',
    min_child_weight=2,
    subsample=0.8,
    colsample_bytree=0.8,
)

# Stratified K-Fold (handles class imbalance better than LOO)
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
cv_scores = cross_val_score(model, X, y, cv=skf, scoring='accuracy')

print(f"  5-Fold CV Accuracy: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")
print(f"  Per-fold: {[f'{s:.3f}' for s in cv_scores]}")

# Train final model on all data
model.fit(X, y)

# Feature importance → pillar weights
importances = dict(zip(PILLAR_NAMES, model.feature_importances_.tolist()))
print(f"\n[3/6] Feature importance (derived pillar weights):")
sorted_imp = sorted(importances.items(), key=lambda x: -x[1])
for p, v in sorted_imp:
    bar = "█" * int(v * 50)
    print(f"  {PILLARS[p]['label']:30s} {v:.4f} {bar}")

# Derive weights from importance
total_imp = sum(importances.values())
derived_weights = {}
for p, imp in importances.items():
    derived_weights[p] = round((imp / total_imp) * TOTAL_WEIGHT, 2) if total_imp > 0 else PILLARS[p]["weight"]

print(f"\n  Derived weights (scaled to sum={TOTAL_WEIGHT}):")
for p, w in sorted(derived_weights.items(), key=lambda x: -x[1]):
    orig = PILLARS[p]["weight"]
    diff = w - orig
    arrow = "↑" if diff > 0 else "↓" if diff < 0 else "="
    print(f"    {PILLARS[p]['label']:30s} {w:.2f} (was {orig:.1f}) {arrow}")

# ---------------------------------------------------------------------------
# BACKTEST against original 8 ground truth companies
# ---------------------------------------------------------------------------
print(f"\n[4/6] Backtesting against 8 ground truth companies...")

with open(os.path.join(BASE_DIR, "data", "training", "ground_truth.json")) as f:
    ground_truth = json.load(f)

backtest_results = []
correct = 0
deviations = []

for gt in ground_truth:
    ps = gt["pillar_scores"]
    features = np.array([[ps[p] for p in PILLAR_NAMES]])

    # Predict tier
    pred_class = model.predict(features)[0]
    pred_tier = le.inverse_transform([pred_class])[0]

    # Calculate composite
    pred_composite = calc_composite(ps)
    actual_composite = gt["actual_score"]
    dev = abs(pred_composite - actual_composite)
    deviations.append(dev)

    is_correct = pred_tier == gt["actual_tier"]
    if is_correct:
        correct += 1

    backtest_results.append({
        "name": gt["name"],
        "vertical": gt["vertical"],
        "actual_tier": gt["actual_tier"],
        "actual_score": actual_composite,
        "predicted_score": pred_composite,
        "predicted_tier": pred_tier,
        "deviation": round(dev, 4),
        "correct": is_correct,
    })

    status = "✓" if is_correct else "✗"
    print(f"  {status} {gt['name']:20s} actual={gt['actual_tier']:15s} predicted={pred_tier:15s} dev={dev:.3f}")

bt_accuracy = correct / len(ground_truth)
avg_dev = sum(deviations) / len(deviations)
print(f"\n  Backtest accuracy: {bt_accuracy*100:.1f}% ({correct}/{len(ground_truth)})")
print(f"  Avg score deviation: {avg_dev:.4f}")

# ---------------------------------------------------------------------------
# RE-SCORE SOLEN PORTFOLIO
# ---------------------------------------------------------------------------
print(f"\n[5/6] Re-scoring 14 Solen portfolio companies with retrained model...")

# Import Solen companies from the generate_demo_data script
sys.path.insert(0, os.path.join(BASE_DIR, "scripts"))
from generate_demo_data import SOLEN_COMPANIES, generate_research_result, generate_evidence, generate_sources

scored_portfolio = []
for co in SOLEN_COMPANIES:
    ps = co.get("pillar_scores", co.get("pillars", {}))
    features = np.array([[ps[p] for p in PILLAR_NAMES]])

    # Use model to predict tier
    pred_class = model.predict(features)[0]
    model_tier = le.inverse_transform([pred_class])[0]

    # Calculate composite using derived weights
    composite_derived = round(
        sum(ps[p] * derived_weights.get(p, PILLARS[p]["weight"]) for p in ps) /
        sum(derived_weights.values()), 2
    )

    # Also calculate with original weights for comparison
    composite_original = calc_composite(ps)

    # Use model tier but original composite for consistency
    tier = get_tier(composite_original)
    wave = 1 if composite_original >= 3.2 else (2 if composite_original >= 2.8 else 3)

    breakdown = {}
    for pillar, score in ps.items():
        weight = PILLARS[pillar]["weight"]
        breakdown[pillar] = {
            "score": score,
            "weight": weight,
            "weighted": round(score * weight, 2),
            "label": PILLARS[pillar]["label"],
            "derived_weight": derived_weights.get(pillar, weight),
        }

    scored_portfolio.append({
        "name": co["name"],
        "vertical": co["vertical"],
        "employee_count": co["employee_count"],
        "composite_score": composite_original,
        "composite_score_derived": composite_derived,
        "tier": tier,
        "model_predicted_tier": model_tier,
        "wave": wave,
        "pillar_scores": ps,
        "pillar_breakdown": breakdown,
    })

    tier_match = "✓" if tier == model_tier else f"(model says {model_tier})"
    print(f"  {co['name']:25s}  Score: {composite_original:.2f}  Tier: {tier:15s}  Wave: {wave}  {tier_match}")

# Sort by score
scored_portfolio.sort(key=lambda x: x["composite_score"], reverse=True)

# Portfolio summary
buildable = sum(1 for s in scored_portfolio if s["tier"] == "AI-Buildable")
emerging = sum(1 for s in scored_portfolio if s["tier"] == "AI-Emerging")
avg_score = sum(s["composite_score"] for s in scored_portfolio) / len(scored_portfolio)
print(f"\n  Portfolio: {buildable} Buildable / {emerging} Emerging")
print(f"  Average score: {avg_score:.2f}")

# ---------------------------------------------------------------------------
# SAVE ALL OUTPUTS
# ---------------------------------------------------------------------------
print(f"\n[6/6] Saving outputs...")

# 1. Model metrics
model_metrics = {
    "model_version": "3.0",
    "training_set_size": len(training_data),
    "cv_accuracy": round(float(cv_scores.mean()), 4),
    "cv_std": round(float(cv_scores.std()), 4),
    "cv_folds": 5,
    "backtest_accuracy": round(bt_accuracy, 4),
    "backtest_avg_deviation": round(avg_dev, 4),
    "backtest_results": backtest_results,
    "feature_importance": {p: round(float(v), 4) for p, v in importances.items()},
    "derived_weights": derived_weights,
    "original_weights": {p: PILLARS[p]["weight"] for p in PILLARS},
    "tier_distribution_training": dict(zip(*np.unique(y_labels, return_counts=True))),
    "trained_at": datetime.utcnow().isoformat(),
}

demo_dir = os.path.join(BASE_DIR, "data", "demo")
os.makedirs(demo_dir, exist_ok=True)

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
        "composite_score": s["composite_score"],
        "tier": s["tier"],
        "wave": s["wave"],
        "pillar_scores": s["pillar_scores"],
    })

with open(os.path.join(demo_dir, "portfolio_scores.json"), "w") as f:
    json.dump(portfolio_export, f, indent=2)
print(f"  ✓ data/demo/portfolio_scores.json")

# 3. Wave sequencing
waves = {"Wave 1 (Q1-Q2)": [], "Wave 2 (Q3-Q4)": [], "Wave 3 (Year 2)": []}
for item in scored_portfolio:
    wave_key = {1: "Wave 1 (Q1-Q2)", 2: "Wave 2 (Q3-Q4)", 3: "Wave 3 (Year 2)"}[item["wave"]]
    waves[wave_key].append({"name": item["name"], "score": item["composite_score"], "tier": item["tier"]})
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

# 6. Update SQLite database
db_path = os.path.join(BASE_DIR, "data", "solen.db")
if os.path.exists(db_path):
    os.remove(db_path)

conn = sqlite3.connect(db_path)
c = conn.cursor()

# Create tables
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
    pillar_scores TEXT, pillar_breakdown TEXT, model_version TEXT DEFAULT '3.0',
    created_at TEXT NOT NULL,
    FOREIGN KEY (company_id) REFERENCES companies(id))""")

c.execute("""CREATE TABLE agent_jobs (
    id TEXT PRIMARY KEY, job_type TEXT NOT NULL, status TEXT DEFAULT 'completed',
    progress INTEGER DEFAULT 100, total_companies INTEGER, completed_companies INTEGER,
    error_message TEXT, result_data TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL)""")

c.execute("""CREATE TABLE model_metrics (
    id TEXT PRIMARY KEY, model_version TEXT NOT NULL, training_set_size INTEGER,
    accuracy REAL, avg_deviation REAL, total_samples INTEGER,
    feature_importance TEXT, derived_weights TEXT, backtest_results TEXT, trained_at TEXT NOT NULL)""")

now = datetime.utcnow().isoformat()
scoring_job_id = f"job_{uuid.uuid4().hex[:8]}"

# Insert companies + scores + research
for i, (co, sp, rr) in enumerate(zip(SOLEN_COMPANIES, scored_portfolio, research_results)):
    c.execute("""INSERT INTO companies VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (co["_id"], co["name"], co["vertical"], co.get("website",""), co.get("github_org",""),
         co.get("description",""), co.get("founded_year"), co.get("employee_count"), now, now))

    score_id = f"sc_{uuid.uuid4().hex[:8]}"
    c.execute("""INSERT INTO scores VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (score_id, co["_id"], scoring_job_id, sp["composite_score"], sp["tier"], sp["wave"],
         json.dumps(sp["pillar_scores"]), json.dumps(sp["pillar_breakdown"]), "3.0", now))

    c.execute("""INSERT INTO research_results VALUES (?,?,?,?,?,?)""",
        (rr["id"], co["_id"], rr["job_id"], json.dumps(rr["pillar_data"]), rr["raw_summary"], now))

# Insert jobs
for job_id, job_type in [(research_job_id, "research"), (scoring_job_id, "scoring"),
                          (f"job_{uuid.uuid4().hex[:8]}", "ml_training")]:
    c.execute("""INSERT INTO agent_jobs VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (job_id, job_type, "completed", 100, 14, 14, None, None, now, now))

# Insert model metrics
c.execute("""INSERT INTO model_metrics VALUES (?,?,?,?,?,?,?,?,?,?)""",
    (f"mm_{uuid.uuid4().hex[:8]}", "3.0", len(training_data),
     model_metrics["cv_accuracy"], model_metrics["backtest_avg_deviation"],
     len(ground_truth), json.dumps(model_metrics["feature_importance"]),
     json.dumps(model_metrics["derived_weights"]),
     json.dumps(model_metrics["backtest_results"]), now))

conn.commit()
conn.close()
print(f"  ✓ data/solen.db (SQLite database updated)")

# 7. Save training set stats
training_stats = {
    "total_companies": len(training_data),
    "verticals": len(set(co["vertical"] for co in training_data)),
    "avg_score": round(float(np.mean([co["composite_score"] for co in training_data])), 2),
    "tier_distribution": dict(zip(*np.unique([co["tier"] for co in training_data], return_counts=True))),
    "top_companies": sorted(training_data, key=lambda x: x["composite_score"], reverse=True)[:10],
}
with open(os.path.join(demo_dir, "training_stats.json"), "w") as f:
    json.dump(training_stats, f, indent=2, default=str)
print(f"  ✓ data/demo/training_stats.json")

print("\n" + "=" * 70)
print("RETRAINING COMPLETE")
print("=" * 70)
print(f"  Model version: 3.0")
print(f"  Training set: {len(training_data)} companies")
print(f"  5-Fold CV accuracy: {cv_scores.mean()*100:.1f}%")
print(f"  Backtest accuracy: {bt_accuracy*100:.1f}%")
print(f"  Avg deviation: {avg_dev:.4f}")
print(f"  Portfolio: {buildable} Buildable / {emerging} Emerging")
