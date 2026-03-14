# Solen AI Investment Intelligence Platform

A production-grade AI-powered investment intelligence platform that evaluates AI-readiness of portfolio companies using the 8-Pillar Readiness Framework.

## Overview

The platform combines AI research agents, machine learning classification, and a full-stack web application to score companies across:
- Data Quality & Availability
- Workflow Digitization
- Infrastructure Readiness
- Competitive Position
- Revenue Upside
- Margin Upside
- Org Readiness
- Risk & Compliance

## Tech Stack

- **LLM**: Anthropic Claude (claude-sonnet-4-6)
- **MCP Server**: Python FastMCP for tool integration
- **Backend**: FastAPI + SQLAlchemy + SQLite/PostgreSQL
- **ML**: scikit-learn + XGBoost + pandas + numpy
- **Frontend**: React 18 + TypeScript + Vite + Tailwind CSS
- **Orchestration**: Docker Compose

## Architecture

```
┌─────────────┐
│   Frontend  │ (React + TypeScript)
│  (Port 3000)│
└──────┬──────┘
       │
┌──────▼──────────────────────────┐
│   FastAPI Backend (Port 8000)    │
│  - Companies CRUD               │
│  - Job orchestration            │
│  - Real-time WebSocket streams  │
└──────┬──────────────────────────┘
       │
    ┌──┴────────────────┐
    │                   │
┌───▼────────┐   ┌──────▼──────────┐
│    MCP     │   │  SQLite / DB    │
│  Server    │   └─────────────────┘
│ (Port 8001)│
└─────┬──────┘
      │
  ┌───┴─────────────────────────────────┐
  │  Research + ML Agents (Async)       │
  │  - ResearchAgent (per-company)      │
  │  - Feature Engineering               │
  │  - Model Training & Backtesting     │
  └─────────────────────────────────────┘
```

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Node.js 18+
- Anthropic API key

### Setup

1. Clone and configure:
```bash
cd solen-ai-intelligence
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

2. Start with Docker:
```bash
docker-compose up --build
```

3. Access:
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs
- MCP Server: http://mcp-server:8001

### Local Development

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**MCP Server:**
```bash
cd mcp_server
pip install -r requirements.txt
python server.py
```

## Usage

### 1. Add Companies
Navigate to Companies page → "Add Company" modal → Enter company details

### 2. Run Research Pipeline
- Companies page → "Run Research" button
- Agents research each company across 8 pillars using Claude + MCP tools
- Real-time progress via WebSocket

### 3. Score Companies
- Run Scoring pipeline to classify companies using trained ML model
- View results: composite score (0-5), tier (AI-Ready/AI-Buildable/AI-Emerging/AI-Limited)

### 4. Review Results
- Dashboard: portfolio overview, tier distribution
- Company Detail: radar chart of 8 pillars, evidence sources
- Models page: backtest results, pillar weights

## 8-Pillar Scoring Framework

| Pillar | Weight | Description |
|--------|--------|-------------|
| Data Quality & Availability | 2.0 | Data maturity, accessibility, quality |
| Workflow Digitization | 2.0 | Process digitization, automation |
| Infrastructure Readiness | 1.5 | Tech stack, scalability, AI-ready infra |
| Competitive Position | 2.0 | Market fit, differentiation potential |
| Revenue Upside | 1.5 | TAM expansion, new product opportunities |
| Margin Upside | 1.5 | Automation potential, cost reduction |
| Org Readiness | 1.0 | Team capability, change management |
| Risk & Compliance | 1.0 | Regulatory, data privacy, governance |

**Composite Score Formula:**
```
weighted_score = Σ(pillar_score × weight) / 12.5

Tiers:
- AI-Ready: 4.0+
- AI-Buildable: 3.2-3.99
- AI-Emerging: 2.5-3.19
- AI-Limited: <2.5
```

## API Reference

### Companies
- `GET /api/companies` - List all companies
- `POST /api/companies` - Add company
- `GET /api/companies/{id}` - Get company detail
- `DELETE /api/companies/{id}` - Remove company

### Research & Scoring
- `POST /api/research/run` - Start research pipeline
- `GET /api/research/{company_id}` - Get research results
- `POST /api/scoring/run` - Start scoring pipeline
- `GET /api/scoring/{company_id}` - Get company scores

### Jobs & Real-time
- `GET /api/jobs` - List all jobs
- `GET /api/jobs/{job_id}` - Get job status
- `WS /ws/jobs/{job_id}` - WebSocket live stream

### Models
- `GET /api/models/performance` - Backtest results & weights

## File Structure

```
solen-ai-intelligence/
├── mcp_server/          # MCP tools server
├── agents/              # Research & ML agents
├── backend/             # FastAPI application
├── frontend/            # React TypeScript SPA
├── data/                # Training data & models
├── docker-compose.yml
├── Makefile
└── README.md
```

## Development

### Running Tests
```bash
cd backend && pytest tests/
```

### Building Docker Images
```bash
docker-compose build
```

### Database Initialization
The backend automatically creates and seeds the database on startup with 14 Solen portfolio companies.

## Color Palette (Solen)

```css
--navy: #0D1B3E
--teal: #02C39A
--orange: #F24E1E
--blue: #1ABCFE
--green: #0ACF83
--purple: #A259FF
--gold: #F5A623
```

## ML Model Details

**Architecture:** XGBoost Classifier
- Input: 8 pillar scores + confidence values (16 features)
- Output: Tier classification (4 classes)
- Training: 8 ground-truth companies with leave-one-out CV

**Backtest Results:**
- Overall Accuracy: ~88%
- Avg Tier Deviation: ±0.09
- Pillar weights derived from feature importances

## Security & Environment

- All API keys are optional; tools degrade gracefully without them
- Database supports SQLite (dev) and PostgreSQL (prod)
- WebSocket connections include job_id validation
- CORS configured via environment variables
- HTTPS recommended for production

## Contributing

1. Create feature branch
2. Follow PEP 8 (Python) and TypeScript strict mode
3. Add tests
4. Submit PR with description

## License

Proprietary - Solen Software

## Support

For issues, contact: dev@solen.ai
