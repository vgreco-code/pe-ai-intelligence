import { useState, useEffect } from 'react'
import {
  LayoutDashboard, Building2, Brain, Database, ChevronLeft, ChevronRight,
  Zap, TrendingUp, BarChart3, GitCompareArrows, Workflow, Github
} from 'lucide-react'
import Dashboard from './pages/Dashboard'
import Portfolio from './pages/Portfolio'
import ModelIntelligence from './pages/ModelIntelligence'
import TrainingExplorer from './pages/TrainingExplorer'
import CompetitiveBenchmarks from './pages/CompetitiveBenchmarks'
import CompanyDetail from './pages/CompanyDetail'
import CompareCompanies from './pages/CompareCompanies'
import PipelineArchitecture from './pages/PipelineArchitecture'
import type { BenchmarkCompany } from './pages/CompetitiveBenchmarks'

// Types
export interface PortfolioCompany {
  name: string
  vertical: string
  employee_count: number
  description: string
  website: string
  founded_year: number
  composite_score: number
  tier: string
  wave: number
  pillar_scores: Record<string, number>
  category_scores?: Record<string, number>
}

export interface BacktestResult {
  name: string
  vertical: string
  actual_tier: string
  actual_score: number
  predicted_score: number
  predicted_tier: string
  deviation: number
  correct: boolean
  adjacent_correct?: boolean
}

export interface ModelMetrics {
  model_version: string
  framework?: string
  training_set_size: number
  num_dimensions?: number
  cv_accuracy: number
  cv_std: number
  cv_folds: number
  backtest_accuracy: number
  backtest_adjacent_accuracy?: number
  backtest_avg_deviation: number
  backtest_count?: number
  backtest_results: BacktestResult[]
  feature_importance: Record<string, number>
  derived_weights: Record<string, number>
  original_weights?: Record<string, number>
  categories?: Record<string, string[]>
  dimension_labels?: Record<string, string>
}

export interface TrainingCompany {
  name: string
  vertical: string
  founded_year: number
  employee_count: number
  funding_total_usd: number
  is_public: boolean
  has_ai_features: boolean
  cloud_native: boolean
  api_ecosystem_strength: number
  data_richness: number
  regulatory_burden: number
  market_position: number
  pillars: Record<string, number>
  composite_score: number
  tier: string
}

export interface WaveData {
  [key: string]: { name: string; score: number; tier: string; top_category?: string }[]
}

export interface TrainingStats {
  total_companies: number
  num_dimensions?: number
  verticals: number
  avg_score: number
  tier_distribution: Record<string, number>
  dimension_stats?: Record<string, { label: string; category: string; mean: number; std: number; min: number; max: number }>
  top_companies: TrainingCompany[]
}

export const DIMENSION_LABELS: Record<string, string> = {
  data_quality: 'Data Quality',
  data_integration: 'Data Integration',
  analytics_maturity: 'Analytics Maturity',
  cloud_architecture: 'Cloud Architecture',
  tech_stack_modernity: 'Tech Stack',
  ai_engineering: 'AI Engineering',
  ai_product_features: 'AI Products',
  revenue_ai_upside: 'Revenue Upside',
  margin_ai_upside: 'Margin Upside',
  product_differentiation: 'Differentiation',
  ai_talent_density: 'AI Talent',
  leadership_ai_vision: 'Leadership Vision',
  org_change_readiness: 'Org Readiness',
  partner_ecosystem: 'Partners',
  ai_governance: 'AI Governance',
  regulatory_readiness: 'Regulatory',
  ai_momentum: 'AI Momentum',
}

export const DIMENSION_SHORT: Record<string, string> = {
  data_quality: 'DQ', data_integration: 'DI', analytics_maturity: 'AM',
  cloud_architecture: 'CA', tech_stack_modernity: 'TS', ai_engineering: 'AE',
  ai_product_features: 'AP', revenue_ai_upside: 'RU', margin_ai_upside: 'MU',
  product_differentiation: 'PD', ai_talent_density: 'AT', leadership_ai_vision: 'LV',
  org_change_readiness: 'OR', partner_ecosystem: 'PE', ai_governance: 'AG',
  regulatory_readiness: 'RR', ai_momentum: 'MO',
}

export const CATEGORIES: Record<string, string[]> = {
  'Data & Analytics': ['data_quality', 'data_integration', 'analytics_maturity'],
  'Technology & Infra': ['cloud_architecture', 'tech_stack_modernity', 'ai_engineering'],
  'AI Product & Value': ['ai_product_features', 'revenue_ai_upside', 'margin_ai_upside', 'product_differentiation'],
  'Organization & Talent': ['ai_talent_density', 'leadership_ai_vision', 'org_change_readiness', 'partner_ecosystem'],
  'Governance & Risk': ['ai_governance', 'regulatory_readiness'],
  'Velocity & Momentum': ['ai_momentum'],
}

export const CATEGORY_COLORS: Record<string, string> = {
  'Data & Analytics': '#06b6d4',
  'Technology & Infra': '#8b5cf6',
  'AI Product & Value': '#02C39A',
  'Organization & Talent': '#F5A623',
  'Governance & Risk': '#ec4899',
  'Velocity & Momentum': '#1ABCFE',
}

export const TIER_COLORS: Record<string, string> = {
  'AI-Ready': '#02C39A',
  'AI-Buildable': '#F5A623',
  'AI-Emerging': '#F24E1E',
  'AI-Limited': '#ef4444',
}

export const getTierBg = (tier: string): string => {
  switch (tier) {
    case 'AI-Ready': return 'bg-emerald-500/20 text-emerald-400'
    case 'AI-Buildable': return 'bg-amber-500/20 text-amber-400'
    case 'AI-Emerging': return 'bg-orange-500/20 text-orange-400'
    case 'AI-Limited': return 'bg-red-500/20 text-red-400'
    default: return 'bg-gray-500/20 text-gray-400'
  }
}

export const getScoreColor = (score: number): string => {
  if (score >= 4.0) return '#02C39A'
  if (score >= 3.2) return '#F5A623'
  if (score >= 2.5) return '#F24E1E'
  return '#ef4444'
}

type Page = 'dashboard' | 'portfolio' | 'compare' | 'benchmarks' | 'pipeline' | 'model' | 'training' | 'company-detail'

const NAV_ITEMS: { id: Page; label: string; icon: typeof LayoutDashboard }[] = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'portfolio', label: 'Portfolio', icon: Building2 },
  { id: 'compare', label: 'Compare', icon: GitCompareArrows },
  { id: 'benchmarks', label: 'Benchmarks', icon: BarChart3 },
  { id: 'pipeline', label: 'Pipeline', icon: Workflow },
  { id: 'model', label: 'Model Intelligence', icon: Brain },
  { id: 'training', label: 'Training Explorer', icon: Database },
]

export default function App() {
  const [page, setPage] = useState<Page>('dashboard')
  const [collapsed, setCollapsed] = useState(false)
  const [portfolio, setPortfolio] = useState<PortfolioCompany[]>([])
  const [metrics, setMetrics] = useState<ModelMetrics | null>(null)
  const [trainingStats, setTrainingStats] = useState<TrainingStats | null>(null)
  const [waveData, setWaveData] = useState<WaveData>({})
  const [trainingSet, setTrainingSet] = useState<TrainingCompany[]>([])
  const [benchmarkData, setBenchmarkData] = useState<BenchmarkCompany[]>([])
  const [selectedCompany, setSelectedCompany] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      fetch('/portfolio_scores.json').then(r => r.json()),
      fetch('/model_metrics.json').then(r => r.json()),
      fetch('/training_stats.json').then(r => r.json()),
      fetch('/wave_sequencing.json').then(r => r.json()),
      fetch('/large_training_set.json').then(r => r.json()),
      fetch('/competitive_benchmarks.json').then(r => r.json()).catch(() => ({ portfolio_benchmarks: [] })),
    ]).then(([p, m, ts, w, t, cb]) => {
      setPortfolio(p)
      setMetrics(m)
      setTrainingStats(ts)
      setWaveData(w)
      setTrainingSet(t)
      setBenchmarkData(cb.portfolio_benchmarks || [])
      setLoading(false)
    }).catch(err => {
      console.error('Failed to load data:', err)
      setLoading(false)
    })
  }, [])

  const navigateToCompany = (companyName: string) => {
    setSelectedCompany(companyName)
    setPage('company-detail')
  }

  const selectedPortfolioCompany = portfolio.find(c => c.name === selectedCompany)
  const selectedBenchmark = benchmarkData.find(b => b.name === selectedCompany)

  if (loading) {
    return (
      <div className="min-h-screen bg-mesh flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="relative">
            <Zap className="w-12 h-12 text-teal-400 animate-pulse" />
            <div className="absolute inset-0 w-12 h-12 bg-teal-400/20 rounded-full blur-xl animate-pulse" />
          </div>
          <p className="text-[var(--text-secondary)] text-sm font-medium">Loading AI Intelligence Platform...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-mesh flex">
      <aside
        className={`fixed top-0 left-0 h-screen z-50 flex flex-col border-r transition-all duration-300 ${
          collapsed ? 'w-[68px]' : 'w-[240px]'
        }`}
        style={{ background: 'var(--navy)', borderColor: 'var(--border)' }}
      >
        <div className="flex items-center gap-3 px-4 h-16 border-b" style={{ borderColor: 'var(--border)' }}>
          <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0" style={{ background: 'var(--teal)' }}>
            <TrendingUp className="w-4 h-4 text-white" />
          </div>
          {!collapsed && (
            <div className="overflow-hidden">
              <h1 className="text-sm font-bold text-white whitespace-nowrap">PE AI Intelligence</h1>
              <p className="text-[10px] font-medium" style={{ color: 'var(--teal)' }}>Model v1.0</p>
            </div>
          )}
        </div>
        <nav className="flex-1 py-4 px-2 space-y-1">
          {NAV_ITEMS.map(item => {
            const Icon = item.icon
            const active = page === item.id || (page === 'company-detail' && item.id === 'portfolio')
            return (
              <button
                key={item.id}
                onClick={() => {
                  if (item.id === 'portfolio') setSelectedCompany(null)
                  setPage(item.id)
                }}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                  active ? 'nav-active text-white' : 'text-[var(--text-secondary)] hover:text-white hover:bg-white/5'
                }`}
                title={collapsed ? item.label : undefined}
              >
                <Icon className={`w-5 h-5 flex-shrink-0 ${active ? 'text-[var(--teal)]' : ''}`} />
                {!collapsed && <span>{item.label}</span>}
              </button>
            )
          })}
        </nav>
        {!collapsed && (
          <div className="mx-3 mb-3 px-2 py-2 rounded-lg bg-white/[0.03] border border-white/[0.06]">
            <div className="text-[9px] font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1.5">Tech Stack</div>
            <div className="flex flex-wrap gap-1">
              {['React', 'TypeScript', 'Vite', 'XGBoost', 'Python'].map(t => (
                <span key={t} className="text-[9px] font-medium px-1.5 py-0.5 rounded bg-white/[0.06] text-[var(--text-muted)]">{t}</span>
              ))}
            </div>
          </div>
        )}
        <a
          href="https://github.com/vgreco-code/pe-ai-intelligence"
          target="_blank"
          rel="noopener noreferrer"
          className="mx-2 mb-2 p-2 rounded-lg text-[var(--text-muted)] hover:text-white hover:bg-white/5 transition-all flex items-center gap-3"
          title="View source on GitHub"
        >
          <Github className="w-5 h-5 flex-shrink-0" />
          {!collapsed && <span className="text-xs font-medium">View on GitHub</span>}
        </a>
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="mx-2 mb-4 p-2 rounded-lg text-[var(--text-muted)] hover:text-white hover:bg-white/5 transition-all flex items-center justify-center"
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </aside>

      <main className={`flex-1 transition-all duration-300 ${collapsed ? 'ml-[68px]' : 'ml-[240px]'}`}>
        <div className="p-6 lg:p-8 max-w-[1600px] mx-auto">
          {page === 'dashboard' && (
            <Dashboard
              portfolio={portfolio}
              metrics={metrics}
              trainingStats={trainingStats}
              waveData={waveData}
              onCompanyClick={navigateToCompany}
            />
          )}
          {page === 'portfolio' && (
            <Portfolio
              portfolio={portfolio}
              onCompanyClick={navigateToCompany}
            />
          )}
          {page === 'compare' && (
            <CompareCompanies portfolio={portfolio} />
          )}
          {page === 'benchmarks' && (
            <CompetitiveBenchmarks benchmarks={benchmarkData} />
          )}
          {page === 'pipeline' && (
            <PipelineArchitecture metrics={metrics} trainingStats={trainingStats} />
          )}
          {page === 'company-detail' && selectedPortfolioCompany && (
            <CompanyDetail
              company={selectedPortfolioCompany}
              benchmark={selectedBenchmark}
              onBack={() => setPage('portfolio')}
            />
          )}
          {page === 'model' && metrics && <ModelIntelligence metrics={metrics} trainingStats={trainingStats} />}
          {page === 'training' && <TrainingExplorer companies={trainingSet} />}
        </div>
      </main>
    </div>
  )
}
