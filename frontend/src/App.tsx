import { useState, useEffect } from 'react'
import {
  LayoutDashboard, Building2, Brain, Database, ChevronLeft, ChevronRight,
  Zap, TrendingUp
} from 'lucide-react'
import Dashboard from './pages/Dashboard'
import Portfolio from './pages/Portfolio'
import ModelIntelligence from './pages/ModelIntelligence'
import TrainingExplorer from './pages/TrainingExplorer'

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
}

export const DIMENSION_SHORT: Record<string, string> = {
  data_quality: 'DQ', data_integration: 'DI', analytics_maturity: 'AM',
  cloud_architecture: 'CA', tech_stack_modernity: 'TS', ai_engineering: 'AE',
  ai_product_features: 'AP', revenue_ai_upside: 'RU', margin_ai_upside: 'MU',
  product_differentiation: 'PD', ai_talent_density: 'AT', leadership_ai_vision: 'LV',
  org_change_readiness: 'OR', partner_ecosystem: 'PE', ai_governance: 'AG',
  regulatory_readiness: 'RR',
}

export const CATEGORIES: Record<string, string[]> = {
  'Data & Analytics': ['data_quality', 'data_integration', 'analytics_maturity'],
  'Technology & Infra': ['cloud_architecture', 'tech_stack_modernity', 'ai_engineering'],
  'AI Product & Value': ['ai_product_features', 'revenue_ai_upside', 'margin_ai_upside', 'product_differentiation'],
  'Organization & Talent': ['ai_talent_density', 'leadership_ai_vision', 'org_change_readiness', 'partner_ecosystem'],
  'Governance & Risk': ['ai_governance', 'regulatory_readiness'],
}

export const CATEGORY_COLORS: Record<string, string> = {
  'Data & Analytics': '#06b6d4',
  'Technology & Infra': '#8b5cf6',
  'AI Product & Value': '#02C39A',
  'Organization & Talent': '#F5A623',
  'Governance & Risk': '#ec4899',
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

type Page = 'dashboard' | 'portfolio' | 'model' | 'training'

const NAV_ITEMS: { id: Page; label: string; icon: typeof LayoutDashboard }[] = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'portfolio', label: 'Portfolio', icon: Building2 },
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
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      fetch('/portfolio_scores.json').then(r => r.json()),
      fetch('/model_metrics.json').then(r => r.json()),
      fetch('/training_stats.json').then(r => r.json()),
      fetch('/wave_sequencing.json').then(r => r.json()),
      fetch('/large_training_set.json').then(r => r.json()),
    ]).then(([p, m, ts, w, t]) => {
      setPortfolio(p)
      setMetrics(m)
      setTrainingStats(ts)
      setWaveData(w)
      setTrainingSet(t)
      setLoading(false)
    }).catch(err => {
      console.error('Failed to load data:', err)
      setLoading(false)
    })
  }, [])

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
              <h1 className="text-sm font-bold text-white whitespace-nowrap">Solen AI Intelligence</h1>
              <p className="text-[10px] font-medium" style={{ color: 'var(--teal)' }}>Portfolio Analytics v4.0</p>
            </div>
          )}
        </div>
        <nav className="flex-1 py-4 px-2 space-y-1">
          {NAV_ITEMS.map(item => {
            const Icon = item.icon
            const active = page === item.id
            return (
              <button
                key={item.id}
                onClick={() => setPage(item.id)}
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
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="mx-2 mb-4 p-2 rounded-lg text-[var(--text-muted)] hover:text-white hover:bg-white/5 transition-all flex items-center justify-center"
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </aside>

      <main className={`flex-1 transition-all duration-300 ${collapsed ? 'ml-[68px]' : 'ml-[240px]'}`}>
        <div className="p-6 lg:p-8 max-w-[1600px] mx-auto">
          {page === 'dashboard' && <Dashboard portfolio={portfolio} metrics={metrics} trainingStats={trainingStats} waveData={waveData} />}
          {page === 'portfolio' && <Portfolio portfolio={portfolio} />}
          {page === 'model' && metrics && <ModelIntelligence metrics={metrics} trainingStats={trainingStats} />}
          {page === 'training' && <TrainingExplorer companies={trainingSet} />}
        </div>
      </main>
    </div>
  )
}
