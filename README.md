# PE AI Intelligence Platform

An AI-readiness assessment platform for private equity portfolio companies. Scores companies across a **17-dimension maturity framework**, classifies them into investment tiers, and provides an interactive dashboard for analysis — plus a **Sandbox** that lets you score any company in real time via web research.

**[Live Demo →](https://pe-ai-intelligence.vercel.app)**

---

## Overview

PE AI Intelligence evaluates software companies on their readiness to adopt and benefit from AI. Each company is scored across 17 dimensions using XGBoost-derived weights, assigned to one of 4 tiers, and prioritized into 3 investment waves. The platform includes:

- **17-Dimension Scoring Engine** — weighted composite scoring with model-derived weights trained on 515 companies
- **XGBoost Classifier** — 89.3% cross-validation accuracy with 5-fold CV and leave-one-out backtesting
- **Competitive Benchmarking** — peer comparison across 58 industry benchmarks with vertical percentile rankings
- **AI Scoring Sandbox** — enter any company name and get a full maturity assessment via live web research (Tavily API)
- **Interactive Dashboard** — React frontend with radar charts, dimension breakdowns, and portfolio analytics

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                  React Frontend (Vite + TypeScript)           │
│                  pe-ai-intelligence.vercel.app                │
│  Dashboard · Portfolio · Compare · Benchmarks · Sandbox       │
│  Pipeline · Model Intelligence · Training Explorer            │
└──────────────────────┬───────────────────────────────────────┘
                       │ REST API
┌──────────────────────▼───────────────────────────────────────┐
│                    FastAPI Backend                             │
│                    localhost:8000                              │
│                                                               │
│  /api/portfolio_scores        /api/sandbox/score (POST)       │
│  /api/competitive_benchmarks  /api/sandbox/companies          │
│  /api/wave_sequencing         /api/model_metrics              │
│  /api/tier_distribution       /api/training_stats             │
│  /api/large_training_set      /api/companies (CRUD)           │
└──────────────────────┬───────────────────────────────────────┘
                       │
          ┌────────────┴────────────┐
          │                         │
┌─────────▼──────────┐   ┌────────▼──────────────────┐
│   Neon Postgres     │   │   Tavily Web Search API   │
│   (serverless)      │   │   (Sandbox pipeline)      │
│                     │   │                            │
│  529 companies      │   │  3 targeted queries per    │
│  8,993 dim scores   │   │  company → feature         │
│  14 benchmarks      │   │  extraction → scoring      │
│  515 training sigs  │   │                            │
└─────────────────────┘   └───────────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, Recharts |
| Backend | FastAPI, SQLAlchemy, Pydantic, Uvicorn |
| Database | Neon Postgres (serverless) / SQLite (tests) |
| ML | XGBoost, scikit-learn (model training) |
| Research | Tavily API (web search for Sandbox scoring) |
| Deployment | Vercel (frontend), Neon (database) |

---

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- npm 9+

### Environment Setup

Create a `.env` file in the `backend/` directory:

```env
DATABASE_URL=postgresql://...          # Neon Postgres connection string
TAVILY_API_KEY=tvly-...                # Required for Sandbox scoring
```

### Running Locally

```bash
# Backend
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

The frontend uses `VITE_API_URL` to switch between static JSON (production) and the API backend (development). The dev config at `frontend/.env.development` sets this to `http://localhost:8000` automatically.

### Database Migration

To populate a fresh Postgres database from the static JSON files:

```bash
cd backend
python migrate.py
```

This loads all 7 JSON files (portfolio scores, benchmarks, training set, etc.) into the database. The migration is idempotent — it skips if data already exists.

---

## Project Structure

```
pe-ai-intelligence/
├── backend/
│   ├── main.py               # FastAPI app, CORS, router registration
│   ├── config.py             # Pydantic settings (loaded from .env)
│   ├── database.py           # SQLAlchemy engine + session factory
│   ├── migrate.py            # JSON → Postgres data migration
│   ├── models/
│   │   └── company.py        # All models: Company, DimensionScore,
│   │                         # CompanyScore, Benchmark, ModelMetrics,
│   │                         # TrainingSignal
│   ├── schemas/
│   │   ├── company.py        # Company request/response schemas
│   │   ├── score.py          # Score schemas
│   │   └── job.py            # Job schemas
│   ├── routers/
│   │   ├── portfolio.py      # Portfolio scores, benchmarks, waves, tiers
│   │   ├── training.py       # Training set, model metrics, training stats
│   │   ├── companies.py      # CRUD for companies
│   │   └── sandbox.py        # Sandbox scoring pipeline (web research → score)
│   └── tests/
│       ├── conftest.py       # Shared fixtures (in-memory SQLite, seeded data)
│       ├── test_api.py       # Health, root, OpenAPI endpoint tests
│       ├── test_companies_api.py  # CRUD endpoint tests
│       ├── test_scoring.py   # Portfolio, benchmark, training endpoint tests
│       └── test_sandbox.py   # Sandbox pipeline + scoring function tests
│
├── frontend/
│   ├── src/
│   │   ├── App.tsx           # Root: routing, sidebar, data loading, types
│   │   └── pages/
│   │       ├── Dashboard.tsx         # KPIs, tier distribution, scoreboard
│   │       ├── Portfolio.tsx         # Company cards with radar charts
│   │       ├── CompanyDetail.tsx     # Deep-dive dimension breakdown
│   │       ├── CompareCompanies.tsx  # Side-by-side comparison
│   │       ├── CompetitiveBenchmarks.tsx  # Peer benchmarking
│   │       ├── Sandbox.tsx           # Score any company via web research
│   │       ├── PipelineArchitecture.tsx   # System architecture diagram
│   │       ├── ModelIntelligence.tsx      # Model accuracy + feature importance
│   │       └── TrainingExplorer.tsx       # Browse 515-company training set
│   ├── public/               # Static JSON data (production fallback)
│   └── .env.development      # VITE_API_URL=http://localhost:8000
│
└── README.md
```

---

## AI Readiness Framework

Companies are scored across **17 dimensions** organized into **6 categories**, using weights derived from XGBoost feature importance:

| Category | Dimensions | Top Weights |
|---|---|---|
| **Data & Analytics** | Data Quality, Data Integration, Analytics Maturity | 0.997, 0.913, 1.126 |
| **Technology & Infra** | Cloud Architecture, Tech Stack Modernity, AI Engineering | 0.559, 0.297, 0.519 |
| **AI Product & Value** | AI Product Features, Revenue Upside, Margin Upside, Differentiation | **4.447**, 2.019, 0.644, 0.481 |
| **Organization & Talent** | AI Talent Density, Leadership Vision, Org Readiness, Partners | **2.346**, 1.432, 0.534, 0.972 |
| **Governance & Risk** | AI Governance, Regulatory Readiness | 0.422, 0.320 |
| **Velocity & Momentum** | AI Momentum | 0.272 |

**Composite Score** = Σ(dimension_score × derived_weight) / Σ(derived_weights) — scaled 1.0–5.0

### Tier Classification

| Tier | Score Range | Wave | Investment Horizon |
|---|---|---|---|
| AI-Ready | ≥ 4.0 | Wave 1 | Immediate (Q1–Q2) |
| AI-Buildable | ≥ 3.2 | Wave 2 | Near-term (Q3–Q4) |
| AI-Emerging | ≥ 2.5 | Wave 3 | Medium-term (Year 2) |
| AI-Limited | < 2.5 | Wave 3 | Longer-term |

### Sandbox Scoring Pipeline

The Sandbox lets you score any company by name through an end-to-end pipeline:

1. **Web Research** — 3 targeted Tavily queries (overview, AI/ML features, technology stack)
2. **Feature Extraction** — regex + keyword heuristics extract employees, funding, AI signals, cloud-native status, market position, etc.
3. **Dimension Scoring** — heuristic model estimates all 17 dimensions from extracted features
4. **Composite Scoring** — weighted composite using the same model-derived weights
5. **Tier Classification** — assigns tier and investment wave
6. **Persistence** — saves to Postgres with `is_portfolio=False` (sandbox-only, separate from curated portfolio)

---

## API Reference

All endpoints prefixed with `/api`. Interactive docs at `http://localhost:8000/docs`.

### Portfolio

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/portfolio_scores` | Portfolio companies with composite + pillar scores |
| `GET` | `/api/competitive_benchmarks` | Peer benchmarking with vertical percentiles |
| `GET` | `/api/wave_sequencing` | Companies grouped by investment wave |
| `GET` | `/api/tier_distribution` | Tier counts across portfolio |

### Training & Model

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/large_training_set` | Full 515-company training dataset |
| `GET` | `/api/model_metrics` | XGBoost model accuracy, weights, backtest results |
| `GET` | `/api/training_stats` | Aggregated stats: dimension means, tier distribution |

### Sandbox

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/sandbox/score` | Score a company by name (triggers web research pipeline) |
| `GET` | `/api/sandbox/companies` | List all sandbox-scored companies |
| `DELETE` | `/api/sandbox/companies/{id}` | Remove a sandbox entry |

### Companies (CRUD)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/companies` | List all companies |
| `POST` | `/api/companies` | Create a company |
| `GET` | `/api/companies/{id}` | Get company by ID |
| `PUT` | `/api/companies/{id}` | Update a company |
| `DELETE` | `/api/companies/{id}` | Delete a company |

---

## Frontend Pages

| Page | Description |
|---|---|
| **Dashboard** | Portfolio KPIs, avg AI score (/ 5), tier distribution chart, top scoreboard |
| **Portfolio** | Company cards with radar charts and centered composite scores |
| **Company Detail** | 17-dimension bar chart with score labels, category breakdown |
| **Compare** | Side-by-side multi-company dimension comparison |
| **Benchmarks** | Competitive positioning vs. 58 market peers with vertical percentiles |
| **Sandbox** | Score any company by name — live web research → full 17-dimension analysis |
| **Pipeline** | System architecture diagram and data flow visualization |
| **Model Intelligence** | CV accuracy (89.3%), feature importance rankings, backtest results |
| **Training Explorer** | Browse and filter the 515-company training dataset |

---

## Testing

```bash
cd backend
python -m pytest tests/ -v
```

| Test File | Coverage | Tests |
|---|---|---|
| `test_scoring.py` | Portfolio scores, benchmarks, waves, tiers, model metrics, training stats, training set, ORM models | 38 |
| `test_sandbox.py` | Scoring functions, feature extraction, vertical detection, API endpoints | 35 |
| `test_companies_api.py` | Full CRUD for `/api/companies` including validation and error cases | 14 |
| `test_api.py` | Health check, root endpoint, OpenAPI schema, error handling | 5 |
| **Total** | | **92** |

Tests use an in-memory SQLite database with seeded fixtures. The `stddev()` computation in training stats uses Python (not SQL) for cross-database compatibility.

---

## Configuration

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | Yes | Postgres connection string (Neon recommended) |
| `TAVILY_API_KEY` | For Sandbox | Web search API key for company research |
| `VITE_API_URL` | Dev only | Backend URL for frontend (set in `.env.development`) |
| `ENVIRONMENT` | No | `development` (default) or `production` |
| `CORS_ORIGINS` | No | Allowed frontend origins (defaults include localhost + Vercel) |
