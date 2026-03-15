# PE AI Intelligence Platform

A private equity AI readiness assessment platform that scores portfolio companies across an 8-pillar framework, classifies them into investment tiers, and provides a rich interactive dashboard for analysis.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Environment Setup](#environment-setup)
  - [Running Locally](#running-locally)
  - [Running with Docker](#running-with-docker)
- [Project Structure](#project-structure)
- [AI Readiness Framework](#ai-readiness-framework)
- [API Reference](#api-reference)
- [Frontend Pages](#frontend-pages)
- [Testing](#testing)
- [CI/CD](#cicd)
- [Configuration](#configuration)

---

## Overview

PE AI Intelligence evaluates portfolio companies on their readiness to adopt and benefit from AI. Each company is scored across 8 pillars using a weighted framework, assigned to one of 4 tiers, and prioritized into 3 investment waves. The platform includes:

- **Research Pipeline** — automated data gathering via web scraping, Crunchbase, SEC EDGAR, and GitHub
- **Scoring Engine** — weighted 8-pillar composite scoring with tier classification
- **ML Model** — XGBoost classifier trained on 500+ enterprise software companies
- **Interactive Dashboard** — React frontend with charts, comparisons, and model intelligence views

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    React Frontend (Vite)                 │
│           http://localhost:3000                         │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP / WebSocket
┌──────────────────────▼──────────────────────────────────┐
│                  FastAPI Backend                         │
│           http://localhost:8000                         │
│  /api/companies  /api/research  /api/scoring            │
│  /api/jobs       /api/models                            │
└──────────┬──────────────────────┬───────────────────────┘
           │                      │
┌──────────▼──────────┐  ┌───────▼────────────────────────┐
│   SQLite / Postgres │  │     FastMCP Server              │
│   (data/solen.db)   │  │   http://localhost:8001         │
└─────────────────────┘  │  web_search, scrape_webpage     │
                         │  crunchbase, sec_edgar, github  │
                         └────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, Recharts |
| Backend | FastAPI, SQLAlchemy, Pydantic, Uvicorn |
| Database | SQLite (dev) / PostgreSQL (prod) |
| ML | XGBoost, scikit-learn |
| Research | Anthropic Claude, Tavily, Crunchbase, SEC EDGAR |
| MCP Server | FastMCP |
| Containerization | Docker, Docker Compose |

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- npm 9+
- (Optional) Docker & Docker Compose

### Environment Setup

```bash
cp .env.example .env
```

Edit `.env` and fill in your API keys:

```env
ANTHROPIC_API_KEY=sk-ant-...      # Required for AI research agent
TAVILY_API_KEY=tvly-...           # Required for web search
CRUNCHBASE_API_KEY=               # Optional — enables Crunchbase enrichment
GITHUB_TOKEN=                     # Optional — enables GitHub analysis
```

### Running Locally

**Install dependencies:**

```bash
make install
# or manually:
cd backend && pip install -r requirements.txt
cd frontend && npm install
```

**Start each service in a separate terminal:**

```bash
# Terminal 1 — Backend API
make backend-dev
# → http://localhost:8000
# → Swagger UI: http://localhost:8000/docs

# Terminal 2 — MCP Server
make mcp-dev
# → http://localhost:8001

# Terminal 3 — Frontend
make frontend-dev
# → http://localhost:3000
```

### Running with Docker

```bash
# Development (with hot reload)
make dev

# Production
make prod

# Stop all services
make down
```

---

## Project Structure

```
pe-ai-intelligence/
├── backend/                  # FastAPI application
│   ├── main.py               # App entry point, CORS, router registration
│   ├── config.py             # Pydantic settings (loaded from .env)
│   ├── database.py           # SQLAlchemy engine, session, DB init & seed
│   ├── models/               # SQLAlchemy ORM models
│   │   ├── company.py        # Company table
│   │   ├── score.py          # AI readiness score table
│   │   ├── research.py       # Research results table
│   │   └── job.py            # Agent job tracking table
│   ├── schemas/              # Pydantic request/response schemas
│   ├── routers/              # API endpoint handlers
│   │   ├── companies.py      # CRUD for companies
│   │   ├── research.py       # Research pipeline endpoints
│   │   ├── scoring.py        # Scoring pipeline endpoints
│   │   ├── jobs.py           # Job status + WebSocket
│   │   └── models.py         # Model performance metrics
│   ├── services/
│   │   ├── scoring_service.py # 8-pillar weighted scoring logic
│   │   └── agent_service.py  # Background job lifecycle management
│   └── tests/                # pytest test suite
│       ├── conftest.py       # Shared fixtures (in-memory DB, TestClient)
│       ├── test_scoring.py   # Unit tests for scoring service
│       ├── test_companies_api.py # API tests for /api/companies
│       └── test_api.py       # Health, root, and error endpoint tests
│
├── frontend/                 # React + TypeScript app
│   ├── src/
│   │   ├── App.tsx           # Root component, routing, data loading
│   │   ├── api/client.ts     # Axios API client + TypeScript types
│   │   ├── pages/            # Full-page view components
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Portfolio.tsx
│   │   │   ├── CompanyDetail.tsx
│   │   │   ├── CompareCompanies.tsx
│   │   │   ├── CompetitiveBenchmarks.tsx
│   │   │   ├── ModelIntelligence.tsx
│   │   │   ├── TrainingExplorer.tsx
│   │   │   └── PipelineArchitecture.tsx
│   │   ├── components/       # Reusable UI components
│   │   │   ├── TierBadge.tsx
│   │   │   ├── ScoreRadar.tsx
│   │   │   ├── WaveChart.tsx
│   │   │   ├── JobStatus.tsx
│   │   │   └── Layout.tsx
│   │   └── __tests__/        # Vitest test suite
│   │       ├── setup.ts
│   │       ├── components/TierBadge.test.tsx
│   │       └── api/client.test.ts
│   ├── public/               # Static JSON data files (served directly)
│   └── package.json
│
├── agents/                   # AI research & ML agents
│   ├── base_agent.py         # Base class with MCP + Claude client
│   ├── research/
│   │   ├── research_agent.py # 8-pillar Claude-powered research
│   │   └── orchestrator.py   # Job orchestration
│   └── ml/
│       ├── model_trainer.py  # XGBoost classifier training
│       ├── feature_engineer.py
│       ├── backtester.py     # Leave-One-Out cross-validation
│       └── weight_deriver.py # Feature importance → pillar weights
│
├── mcp_server/               # FastMCP tool server
│   ├── server.py             # MCP server (port 8001)
│   └── tools/
│       ├── web_search.py     # Tavily web search
│       ├── web_scraper.py    # Webpage content extraction
│       ├── crunchbase.py     # Crunchbase company data
│       ├── sec_edgar.py      # SEC EDGAR filings
│       └── github_analyzer.py # GitHub org analysis
│
├── data/
│   ├── training/             # Ground truth + training set JSON
│   ├── research/             # Portfolio research results
│   ├── demo/                 # Demo data for frontend
│   └── solen.db              # SQLite database
│
├── scripts/                  # Data pipeline scripts
├── .github/workflows/ci.yml  # GitHub Actions CI
├── docker-compose.yml
├── Makefile
└── .env.example
```

---

## AI Readiness Framework

Companies are scored across **8 pillars** using a weighted composite model:

| Pillar | Weight | Description |
|---|---|---|
| Data Quality & Availability | 2.0 | Richness, accessibility, and structure of company data |
| Workflow Digitization | 2.0 | Degree to which core workflows are digitized and automatable |
| Competitive Position | 2.0 | AI adoption relative to market peers |
| Infrastructure Readiness | 1.5 | Cloud architecture, APIs, and technical foundation |
| Revenue Upside | 1.5 | Potential revenue growth from AI-enabled features |
| Margin Upside | 1.5 | Potential margin improvement through AI automation |
| Org Readiness | 1.0 | Leadership vision, talent, and change management capability |
| Risk & Compliance | 1.0 | Regulatory environment and data governance posture |

**Composite Score** = Σ(pillar_score × weight) / 12.5 — scaled to 0–5.

### Tier Classification

| Tier | Score Range | Wave |
|---|---|---|
| AI-Ready | ≥ 4.0 | Wave 1 — immediate investment priority |
| AI-Buildable | ≥ 3.2 | Wave 2 — 6–12 month horizon |
| AI-Emerging | ≥ 2.5 | Wave 3 — 12–24 month horizon |
| AI-Limited | < 2.5 | Wave 3 — longer-term potential |

---

## API Reference

All endpoints are prefixed with `/api`. Interactive docs available at `http://localhost:8000/docs`.

### Companies

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/companies` | List all portfolio companies |
| `POST` | `/api/companies` | Create a new company |
| `GET` | `/api/companies/{id}` | Get a company by ID |
| `PUT` | `/api/companies/{id}` | Update a company |
| `DELETE` | `/api/companies/{id}` | Delete a company |

### Research

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/research/run` | Start research pipeline `{ company_ids: [] }` |
| `GET` | `/api/research/{company_id}` | Get latest research results |

### Scoring

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/scoring/run` | Start scoring pipeline `{ company_ids: [] }` |
| `GET` | `/api/scoring/{company_id}` | Get latest score |

### Jobs

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/jobs` | List all jobs |
| `GET` | `/api/jobs/{job_id}` | Get job status |
| `WS` | `/api/jobs/ws/{job_id}` | Real-time job progress stream |

### Models

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/models/performance` | Model accuracy, feature importance, backtest results |

---

## Frontend Pages

| Page | Description |
|---|---|
| Dashboard | Portfolio KPIs, tier distribution, feature importance, wave timing |
| Portfolio | Grid/list view of all companies with tier and score filters |
| Company Detail | Deep dive: pillar scores, radar chart, research findings |
| Compare | Side-by-side multi-company pillar comparison |
| Benchmarks | Competitive positioning vs. market peers |
| Model Intelligence | CV accuracy, feature importance rankings, backtest results |
| Training Explorer | Browse and filter the 500+ company training set |
| Pipeline Architecture | System architecture diagram and data flow |

---

## Testing

### Backend (pytest)

```bash
cd backend
pytest tests/ -v

# With coverage report
pytest tests/ -v --cov=. --cov-report=html
```

| Test File | What It Covers | Tests |
|---|---|---|
| `tests/test_scoring.py` | Composite score calculation, tier/wave assignment, pillar breakdown, edge cases | 28 |
| `tests/test_companies_api.py` | Full CRUD for `/api/companies` including validation and 404/409 errors | 14 |
| `tests/test_api.py` | Health check, root endpoint, OpenAPI schema, error responses | 11 |

### Frontend (Vitest + Testing Library)

```bash
cd frontend
npm test           # Single run
npm run test:watch # Watch mode
```

| Test File | What It Covers | Tests |
|---|---|---|
| `src/__tests__/components/TierBadge.test.tsx` | Renders all 4 tiers, correct CSS classes, className forwarding | 9 |
| `src/__tests__/api/client.test.ts` | All API methods call correct HTTP methods and endpoint paths | 13 |

---

## CI/CD

GitHub Actions workflow at [`.github/workflows/ci.yml`](.github/workflows/ci.yml) runs on every push and PR to `main` or `develop`:

| Job | Steps |
|---|---|
| `backend-lint` | Python 3.11 → install deps → pylint |
| `frontend-lint` | Node 18 → `npm ci` → `npm run build` |
| `docker-build` | Build Docker images for backend, frontend, and mcp-server |

---

## Configuration

All configuration is via environment variables. See [`.env.example`](.env.example) for the full list.

| Variable | Default | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | — | Claude API key (required for research agent) |
| `TAVILY_API_KEY` | — | Web search API key |
| `CRUNCHBASE_API_KEY` | — | Crunchbase enrichment (optional) |
| `GITHUB_TOKEN` | — | GitHub API access (optional) |
| `DATABASE_URL` | `sqlite:///./data/solen.db` | Database connection string |
| `MCP_SERVER_URL` | `http://mcp-server:8001` | MCP tool server URL |
| `CORS_ORIGINS` | `http://localhost:3000` | Allowed frontend origins |
| `ENVIRONMENT` | `development` | `development` or `production` |
| `VITE_API_URL` | `http://localhost:8000` | Backend URL for the frontend |
