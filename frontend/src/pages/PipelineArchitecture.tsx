import { useState } from 'react'
import { Workflow, Globe, Cpu, BarChart3, Brain, Layers, Database, Zap, CheckCircle2, Server, Cloud, FlaskConical, Github } from 'lucide-react'
import { ModelMetrics, TrainingStats } from '../App'

interface Props {
  metrics: ModelMetrics | null
  trainingStats: TrainingStats | null
}

interface PipelineStage {
  id: string
  title: string
  subtitle: string
  icon: typeof Globe
  color: string
  description: string
  details: string[]
  techStack: string[]
  inputs: string[]
  outputs: string[]
}

const PIPELINE_STAGES: PipelineStage[] = [
  {
    id: 'scrape',
    title: 'Web Intelligence',
    subtitle: 'Tavily Search API',
    icon: Globe,
    color: '#1ABCFE',
    description: 'Multi-query web research system that autonomously researches each company across 6 data layers: website content, company overview, customer reviews, job postings, SEC filings, and AI/ML technology signals.',
    details: [
      'Tavily API with domain-specific search queries per dimension',
      'Checkpoint/resume pattern for fault tolerance (saves every 25 companies)',
      '6 parallel search queries per company for comprehensive coverage',
      'Rate-limited to respect API quotas with exponential backoff',
    ],
    techStack: ['Tavily API', 'Python', 'JSON checkpointing'],
    inputs: ['Company name', 'Website URL', 'Vertical classification'],
    outputs: ['Raw text corpus per company', 'Source URLs', 'Confidence scores'],
  },
  {
    id: 'signal',
    title: 'Signal Detection',
    subtitle: 'Keyword & NLP Scoring',
    icon: Cpu,
    color: '#A259FF',
    description: 'Domain-specific keyword signal scoring across 17 dimensions. Each dimension has curated positive and negative keyword lists that are matched against the scraped text corpus to produce raw signal scores.',
    details: [
      '17 dimension-specific keyword dictionaries (200+ keywords total)',
      'Positive and negative signal weighting',
      'Factual attribute modifiers (is_public, has_ai_features, cloud_native, etc.)',
      'Signal count normalization and confidence scoring',
    ],
    techStack: ['Python', 'Regex matching', 'Statistical scoring'],
    inputs: ['Raw text corpus', 'Company attributes'],
    outputs: ['Raw 17-dimension signal scores (1.0-5.0)', 'Evidence snippets', 'Signal counts'],
  },
  {
    id: 'calibrate',
    title: 'Attribute Calibration',
    subtitle: 'Score Normalization',
    icon: BarChart3,
    color: '#F5A623',
    description: 'Raw keyword scores are compressed (1.5-3.0 range). The calibration engine stretches scores using verified company attributes (employee count, funding, cloud-native status, etc.) to produce realistic tier-distributed scores matching real-world observations.',
    details: [
      'Per-dimension attribute boost matrices (16 attributes x 17 dimensions)',
      'Stretch factor: score = 1.5 + delta * stretch + boost * 0.4',
      'Expands score range from 1.5-3.0 to 1.0-5.0',
      'Portfolio scores: 35% calibrated research + 65% domain-expert heuristic',
    ],
    techStack: ['Python', 'NumPy', 'Statistical normalization'],
    inputs: ['Raw signal scores', 'Company attributes', 'Attribute boost matrices'],
    outputs: ['Calibrated 17-dimension scores', 'Composite score', 'Preliminary tier'],
  },
  {
    id: 'velocity',
    title: 'Velocity Signals',
    subtitle: 'AI Momentum Detection',
    icon: Zap,
    color: '#0ACF83',
    description: 'Separate scraping pass that detects AI adoption velocity through two signals: AI-related job postings (hiring momentum) and recent AI news/announcements (strategic momentum). Produces the 17th dimension: AI Momentum.',
    details: [
      'AI job posting search: hiring signals, role types, seniority',
      'Recent AI news search: product launches, partnerships, investments',
      'Stagnation detection: legacy indicators that reduce momentum score',
      'Weighted formula: 40% hiring + 60% news, with attribute modifiers',
    ],
    techStack: ['Tavily API', 'Python', 'Temporal analysis'],
    inputs: ['Company name', 'Company attributes'],
    outputs: ['AI Momentum score (1.0-5.0)', 'Hiring signal count', 'News signal count'],
  },
  {
    id: 'classify',
    title: 'ML Classification',
    subtitle: 'XGBoost Multi-Class',
    icon: Brain,
    color: '#02C39A',
    description: 'Gradient-boosted tree classifier trained on 515 enterprise software companies. Predicts AI readiness tier and derives feature importance weights that reveal which dimensions matter most for AI maturity classification.',
    details: [
      'XGBoost with 150 estimators, max_depth=5, learning_rate=0.08',
      '5-fold stratified cross-validation for robust accuracy estimation',
      'Derived dimension weights from feature importance (replaces static weights)',
      '58-company backtest against manually verified ground truth',
    ],
    techStack: ['XGBoost', 'scikit-learn', 'NumPy', 'Pandas'],
    inputs: ['17-dimension feature vectors for all companies'],
    outputs: ['Tier predictions', 'Derived weights', 'Feature importance', 'Model metrics'],
  },
  {
    id: 'benchmark',
    title: 'Competitive Benchmarking',
    subtitle: 'Vertical Peer Ranking',
    icon: Layers,
    color: '#F24E1E',
    description: 'Each portfolio company is benchmarked against peer companies in their vertical(s) from the 515-company training set. Multi-vertical pooling ensures sufficient comparison depth even for niche verticals.',
    details: [
      'Explicit multi-vertical mapping (3 verticals per portfolio company)',
      'Percentile rank calculation within pooled peer set',
      'Nearest-peer identification for competitive context',
      'Vertical statistics: avg, min, max, distribution',
    ],
    techStack: ['Python', 'Statistical percentile ranking'],
    inputs: ['Portfolio scores', 'Training set scores', 'Vertical mappings'],
    outputs: ['Percentile ranks', 'Peer comparisons', 'Vertical statistics'],
  },
  {
    id: 'sandbox',
    title: 'Sandbox Pipeline',
    subtitle: 'Real-Time Scoring',
    icon: FlaskConical,
    color: '#A259FF',
    description: 'End-to-end scoring pipeline exposed as a REST API. Users submit a company name; the system researches it via Tavily, extracts structured features, scores all 17 dimensions using heuristic models with XGBoost-derived weights, and classifies the tier — all in real time.',
    details: [
      '3 targeted Tavily queries per company (overview, AI signals, tech stack)',
      'Regex + keyword heuristic feature extraction (employees, funding, AI, cloud)',
      '17-dimension scoring using model-derived weights (same as production)',
      'Results saved to Postgres with is_portfolio=false (sandbox isolation)',
    ],
    techStack: ['FastAPI', 'Tavily API', 'httpx', 'SQLAlchemy'],
    inputs: ['Company name (single string)'],
    outputs: ['Composite score', '17 dimension scores', 'Tier + Wave', 'Research context'],
  },
]

// Architecture layer cards
const ARCH_LAYERS = [
  {
    title: 'Frontend',
    subtitle: 'React + TypeScript',
    icon: Globe,
    color: '#1ABCFE',
    tech: ['React 18', 'TypeScript', 'Vite', 'Tailwind CSS', 'Recharts'],
    details: '8 interactive pages — Dashboard, Portfolio, Compare, Benchmarks, Sandbox, Pipeline, Model Intelligence, Training Explorer. Deployed on Vercel with static JSON fallback.',
  },
  {
    title: 'API Layer',
    subtitle: 'FastAPI + Pydantic',
    icon: Server,
    color: '#02C39A',
    tech: ['FastAPI', 'Pydantic', 'SQLAlchemy ORM', 'Uvicorn'],
    details: '10 REST endpoints serving portfolio scores, benchmarks, model metrics, training data, and the Sandbox scoring pipeline. Auto-generated OpenAPI docs at /docs.',
  },
  {
    title: 'Database',
    subtitle: 'Neon Postgres',
    icon: Database,
    color: '#F5A623',
    tech: ['Neon Postgres', 'SQLAlchemy', 'Alembic'],
    details: '6 models: Company, DimensionScore, CompanyScore, Benchmark, ModelMetrics, TrainingSignal. 529 companies, 8,993 dimension scores. Idempotent migration from JSON.',
  },
  {
    title: 'Research',
    subtitle: 'Tavily Web Search',
    icon: Cloud,
    color: '#F24E1E',
    tech: ['Tavily API', 'httpx', 'Regex extraction'],
    details: 'Powers the Sandbox scoring pipeline. 3 targeted queries per company, extracts employees, funding, AI signals, cloud-native, market position, regulatory burden.',
  },
]

export default function PipelineArchitecture({ metrics, trainingStats }: Props) {
  const [activeStage, setActiveStage] = useState<string>('scrape')

  const active = PIPELINE_STAGES.find(s => s.id === activeStage) || PIPELINE_STAGES[0]
  const ActiveIcon = active.icon

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <div className="flex items-center gap-4 mb-2">
          <Workflow className="w-8 h-8 text-teal-400" />
          <h1 className="text-4xl font-bold text-[var(--text-primary)]">Pipeline Architecture</h1>
        </div>
        <p className="text-[var(--text-secondary)] text-lg">
          Full-stack platform: from raw web data to investment-grade intelligence
        </p>
      </div>

      {/* System Architecture Overview */}
      <div className="glass-card rounded-2xl border border-slate-700/50 p-8">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-[var(--text-primary)]">System Architecture</h2>
          <a
            href="https://github.com/vgreco-code/pe-ai-intelligence"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 text-xs text-[var(--text-muted)] hover:text-white transition-colors"
          >
            <Github className="w-3.5 h-3.5" />
            <span>View Source</span>
          </a>
        </div>

        <div className="grid grid-cols-4 gap-4 mb-6">
          {ARCH_LAYERS.map(layer => {
            const Icon = layer.icon
            return (
              <div
                key={layer.title}
                className="rounded-xl p-5 border transition-all hover:scale-[1.02]"
                style={{
                  backgroundColor: `${layer.color}08`,
                  borderColor: `${layer.color}20`,
                }}
              >
                <div className="flex items-center gap-3 mb-3">
                  <div
                    className="w-9 h-9 rounded-lg flex items-center justify-center"
                    style={{ backgroundColor: `${layer.color}18` }}
                  >
                    <Icon className="w-4.5 h-4.5" style={{ color: layer.color }} />
                  </div>
                  <div>
                    <div className="text-sm font-bold text-[var(--text-primary)]">{layer.title}</div>
                    <div className="text-[10px] font-medium" style={{ color: layer.color }}>{layer.subtitle}</div>
                  </div>
                </div>
                <p className="text-[11px] text-[var(--text-secondary)] leading-relaxed mb-3">
                  {layer.details}
                </p>
                <div className="flex flex-wrap gap-1">
                  {layer.tech.map(t => (
                    <span
                      key={t}
                      className="text-[9px] font-medium px-1.5 py-0.5 rounded"
                      style={{ backgroundColor: `${layer.color}10`, color: `${layer.color}cc` }}
                    >
                      {t}
                    </span>
                  ))}
                </div>
              </div>
            )
          })}
        </div>

        {/* Data flow arrows */}
        <div className="flex items-center justify-center gap-3 py-2">
          <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-800/40 border border-slate-700/30">
            <div className="w-2 h-2 rounded-full bg-[#1ABCFE]" />
            <span className="text-[10px] text-[var(--text-muted)]">React SPA</span>
          </div>
          <div className="flex items-center">
            <div className="w-10 h-px bg-slate-600" />
            <span className="text-[9px] text-[var(--text-muted)] px-1">REST</span>
            <div className="w-10 h-px bg-slate-600" />
          </div>
          <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-800/40 border border-slate-700/30">
            <div className="w-2 h-2 rounded-full bg-[#02C39A]" />
            <span className="text-[10px] text-[var(--text-muted)]">FastAPI</span>
          </div>
          <div className="flex items-center">
            <div className="w-10 h-px bg-slate-600" />
            <span className="text-[9px] text-[var(--text-muted)] px-1">SQL</span>
            <div className="w-10 h-px bg-slate-600" />
          </div>
          <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-800/40 border border-slate-700/30">
            <div className="w-2 h-2 rounded-full bg-[#F5A623]" />
            <span className="text-[10px] text-[var(--text-muted)]">Neon Postgres</span>
          </div>
          <div className="flex items-center">
            <div className="w-6 h-px bg-slate-600" />
          </div>
          <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-800/40 border border-slate-700/30">
            <div className="w-2 h-2 rounded-full bg-[#F24E1E]" />
            <span className="text-[10px] text-[var(--text-muted)]">Tavily API</span>
          </div>
        </div>
      </div>

      {/* Pipeline Flow Diagram */}
      <div className="glass-card rounded-2xl border border-slate-700/50 p-8">
        <div className="flex items-center justify-between mb-8">
          <h2 className="text-xl font-bold text-[var(--text-primary)]">Scoring Pipeline</h2>
          <div className="flex items-center gap-2 text-xs text-[var(--text-muted)]">
            <Database className="w-4 h-4" />
            <span>{trainingStats?.total_companies || 515} companies processed</span>
          </div>
        </div>

        {/* Flow visualization */}
        <div className="flex items-center gap-2 mb-8 overflow-x-auto pb-2">
          {PIPELINE_STAGES.map((stage, i) => {
            const Icon = stage.icon
            const isActive = stage.id === activeStage
            return (
              <div key={stage.id} className="flex items-center flex-shrink-0">
                <button
                  onClick={() => setActiveStage(stage.id)}
                  className={`relative flex flex-col items-center gap-2 p-4 rounded-xl border transition-all min-w-[120px] ${
                    isActive
                      ? 'border-opacity-50 scale-105 shadow-lg'
                      : 'border-slate-700/30 hover:border-opacity-30'
                  }`}
                  style={{
                    backgroundColor: isActive ? `${stage.color}15` : 'rgba(30,41,59,0.3)',
                    borderColor: isActive ? stage.color : undefined,
                  }}
                >
                  <div
                    className="w-10 h-10 rounded-lg flex items-center justify-center"
                    style={{ backgroundColor: `${stage.color}20` }}
                  >
                    <Icon className="w-5 h-5" style={{ color: stage.color }} />
                  </div>
                  <span className={`text-xs font-semibold text-center ${isActive ? 'text-[var(--text-primary)]' : 'text-[var(--text-muted)]'}`}>
                    {stage.title}
                  </span>
                  <span className="text-[9px] text-[var(--text-muted)] text-center">{stage.subtitle}</span>
                  {isActive && (
                    <div className="absolute -bottom-2 left-1/2 -translate-x-1/2 w-2 h-2 rounded-full" style={{ backgroundColor: stage.color }} />
                  )}
                </button>
                {i < PIPELINE_STAGES.length - 1 && (
                  <div className="flex items-center px-1 flex-shrink-0">
                    <div className="w-6 h-0.5 bg-slate-700" />
                    <div className="w-0 h-0 border-t-4 border-b-4 border-l-6 border-t-transparent border-b-transparent border-l-slate-700" />
                  </div>
                )}
              </div>
            )
          })}
        </div>

        {/* Active stage detail */}
        <div className="border-t border-slate-700/30 pt-8">
          <div className="flex items-start gap-6">
            <div
              className="w-16 h-16 rounded-2xl flex items-center justify-center flex-shrink-0"
              style={{ backgroundColor: `${active.color}15`, border: `1px solid ${active.color}30` }}
            >
              <ActiveIcon className="w-8 h-8" style={{ color: active.color }} />
            </div>
            <div className="flex-1">
              <h3 className="text-2xl font-bold text-[var(--text-primary)] mb-1">{active.title}</h3>
              <p className="text-sm font-medium mb-4" style={{ color: active.color }}>{active.subtitle}</p>
              <p className="text-[var(--text-secondary)] leading-relaxed mb-6">{active.description}</p>

              <div className="grid grid-cols-2 gap-6">
                {/* How it works */}
                <div>
                  <h4 className="text-sm font-semibold text-[var(--text-primary)] mb-3">How It Works</h4>
                  <div className="space-y-2">
                    {active.details.map((detail, i) => (
                      <div key={i} className="flex items-start gap-2">
                        <CheckCircle2 className="w-4 h-4 flex-shrink-0 mt-0.5" style={{ color: active.color }} />
                        <span className="text-sm text-[var(--text-secondary)]">{detail}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* I/O and Tech */}
                <div className="space-y-4">
                  <div>
                    <h4 className="text-sm font-semibold text-[var(--text-primary)] mb-2">Inputs</h4>
                    <div className="flex flex-wrap gap-2">
                      {active.inputs.map((input, i) => (
                        <span key={i} className="bg-slate-800/50 text-[var(--text-secondary)] rounded-full px-3 py-1 text-xs border border-slate-700/30">
                          {input}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold text-[var(--text-primary)] mb-2">Outputs</h4>
                    <div className="flex flex-wrap gap-2">
                      {active.outputs.map((output, i) => (
                        <span key={i} className="rounded-full px-3 py-1 text-xs border" style={{
                          backgroundColor: `${active.color}10`,
                          borderColor: `${active.color}30`,
                          color: active.color,
                        }}>
                          {output}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold text-[var(--text-primary)] mb-2">Tech Stack</h4>
                    <div className="flex flex-wrap gap-2">
                      {active.techStack.map((tech, i) => (
                        <span key={i} className="bg-slate-800/50 text-[var(--text-muted)] rounded px-2 py-0.5 text-xs font-mono">
                          {tech}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* API Endpoints */}
      <div className="glass-card rounded-2xl border border-slate-700/50 p-8">
        <h2 className="text-xl font-bold text-[var(--text-primary)] mb-6">API Endpoints</h2>
        <div className="grid grid-cols-2 gap-x-8 gap-y-2">
          {[
            { method: 'GET', path: '/api/portfolio_scores', desc: 'Portfolio with 17-dimension scores', group: 'portfolio' },
            { method: 'GET', path: '/api/competitive_benchmarks', desc: 'Peer benchmarking data', group: 'portfolio' },
            { method: 'GET', path: '/api/wave_sequencing', desc: 'Investment wave groupings', group: 'portfolio' },
            { method: 'GET', path: '/api/tier_distribution', desc: 'Tier counts across portfolio', group: 'portfolio' },
            { method: 'GET', path: '/api/model_metrics', desc: 'XGBoost accuracy & weights', group: 'training' },
            { method: 'GET', path: '/api/training_stats', desc: 'Dimension stats & top companies', group: 'training' },
            { method: 'GET', path: '/api/large_training_set', desc: 'Full 515-company dataset', group: 'training' },
            { method: 'POST', path: '/api/sandbox/score', desc: 'Score any company (web research)', group: 'sandbox' },
            { method: 'GET', path: '/api/sandbox/companies', desc: 'List sandbox results', group: 'sandbox' },
            { method: 'CRUD', path: '/api/companies', desc: 'Company management', group: 'companies' },
          ].map(ep => (
            <div key={ep.path} className="flex items-center gap-3 py-1.5 border-b border-slate-700/20">
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded font-mono ${
                ep.method === 'POST' ? 'bg-purple-500/15 text-purple-400' :
                ep.method === 'CRUD' ? 'bg-amber-500/15 text-amber-400' :
                'bg-teal-500/15 text-teal-400'
              }`}>
                {ep.method}
              </span>
              <span className="text-xs font-mono text-[var(--text-primary)]">{ep.path}</span>
              <span className="text-[10px] text-[var(--text-muted)] ml-auto">{ep.desc}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Model Performance Summary */}
      <div className="grid grid-cols-3 gap-6">
        <div className="glass-card rounded-xl border border-teal-500/20 p-6">
          <h3 className="text-lg font-bold text-[var(--text-primary)] mb-4">Training Data</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-sm text-[var(--text-muted)]">Companies</span>
              <span className="text-sm font-bold text-[var(--text-primary)]">{trainingStats?.total_companies || 515}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-[var(--text-muted)]">Verticals</span>
              <span className="text-sm font-bold text-[var(--text-primary)]">{trainingStats?.verticals || 332}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-[var(--text-muted)]">Dimensions</span>
              <span className="text-sm font-bold text-[var(--text-primary)]">17</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-[var(--text-muted)]">Dimension Scores</span>
              <span className="text-sm font-bold text-[var(--text-primary)]">8,993</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-[var(--text-muted)]">Ground Truth</span>
              <span className="text-sm font-bold text-[var(--text-primary)]">{metrics?.backtest_count || 58} verified</span>
            </div>
          </div>
        </div>

        <div className="glass-card rounded-xl border border-teal-500/20 p-6">
          <h3 className="text-lg font-bold text-[var(--text-primary)] mb-4">Model Performance</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-sm text-[var(--text-muted)]">CV Accuracy</span>
              <span className="text-sm font-bold text-emerald-400">{metrics ? (metrics.cv_accuracy * 100).toFixed(1) : '89.3'}%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-[var(--text-muted)]">Adjacent Accuracy</span>
              <span className="text-sm font-bold text-emerald-400">{metrics?.backtest_adjacent_accuracy ? (metrics.backtest_adjacent_accuracy * 100).toFixed(1) : '93.1'}%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-[var(--text-muted)]">Exact Backtest</span>
              <span className="text-sm font-bold text-amber-400">{metrics ? (metrics.backtest_accuracy * 100).toFixed(1) : '43.1'}%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-[var(--text-muted)]">Avg Deviation</span>
              <span className="text-sm font-bold text-[var(--text-primary)]">{metrics?.backtest_avg_deviation?.toFixed(3) || '0.366'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-[var(--text-muted)]">Algorithm</span>
              <span className="text-sm font-bold text-[var(--text-primary)]">XGBoost</span>
            </div>
          </div>
        </div>

        <div className="glass-card rounded-xl border border-teal-500/20 p-6">
          <h3 className="text-lg font-bold text-[var(--text-primary)] mb-4">Platform</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-sm text-[var(--text-muted)]">Tests Passing</span>
              <span className="text-sm font-bold text-emerald-400">92</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-[var(--text-muted)]">API Endpoints</span>
              <span className="text-sm font-bold text-[var(--text-primary)]">10</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-[var(--text-muted)]">Frontend Pages</span>
              <span className="text-sm font-bold text-[var(--text-primary)]">8</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-[var(--text-muted)]">DB Models</span>
              <span className="text-sm font-bold text-[var(--text-primary)]">6</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-[var(--text-muted)]">Deployment</span>
              <span className="text-sm font-bold text-[var(--text-primary)]">Vercel + Neon</span>
            </div>
          </div>
        </div>
      </div>

      {/* Architecture Philosophy */}
      <div className="glass-card rounded-2xl border border-slate-700/50 p-8">
        <h2 className="text-xl font-bold text-[var(--text-primary)] mb-6">Design Principles</h2>
        <div className="grid grid-cols-4 gap-4">
          {[
            {
              title: 'Evidence-Based',
              desc: 'Every score is backed by scraped web evidence with source URLs and confidence scores — no black-box assessments.',
              color: '#1ABCFE',
            },
            {
              title: 'Calibrated',
              desc: 'Raw signals are normalized against 515-company training set with attribute-based calibration for realistic score distributions.',
              color: '#02C39A',
            },
            {
              title: 'Full-Stack',
              desc: 'React frontend → FastAPI → Neon Postgres. Same scoring weights in production pipeline and real-time Sandbox. 92 tests across 4 test suites.',
              color: '#F5A623',
            },
            {
              title: 'Reproducible',
              desc: 'Deterministic scoring with versioned models, fixed random seeds, and auditable evidence chains from raw data to final tier.',
              color: '#A259FF',
            },
          ].map(principle => (
            <div key={principle.title} className="bg-slate-800/30 rounded-xl p-5 border border-slate-700/30">
              <div className="w-1 h-8 rounded-full mb-3" style={{ backgroundColor: principle.color }} />
              <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-2">{principle.title}</h3>
              <p className="text-xs text-[var(--text-secondary)] leading-relaxed">{principle.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
