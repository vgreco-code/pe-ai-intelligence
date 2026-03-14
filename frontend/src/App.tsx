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
  composite_score: number
  tier: string
  wave: number
  pillar_scores: Record<string, number>
}

export interface ModelMetrics {
  model_version: string
  training_set_size: number
  cv_accuracy: number
  cv_std: number
  cv_folds: number
  backtest_accuracy: number
  backtest_avg_deviation: number
  backtest_results: {
    name: string
    vertical: string
    actual_tier: string
    actual_score: number
    predicted_score: number
    predicted_tier: string
    deviation: number
    correct: boolean
  }[]
  feature_importance: Record<string, number>
  derived_weights: Record<string, number>
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
  [key: string]: { name: string; score: number; tier: string }[]
}

export interface TrainingStats {
  total_companies: number
  verticals: number
  avg_score: number
  tier_distribution: Record<string, string>
  top_companies: TrainingCompany[]
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
      {/* Sidebar */}
      <aside
        className={`fixed top-0 left-0 h-screen z-50 flex flex-col border-r transition-all duration-300 ${
          collapsed ? 'w-[68px]' : 'w-[240px]'
        }`}
        style={{ background: 'var(--navy)', borderColor: 'var(--border)' }}
      >
        {/* Logo */}
        <div className="flex items-center gap-3 px-4 h-16 border-b" style={{ borderColor: 'var(--border)' }}>
          <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0" style={{ background: 'var(--teal)' }}>
            <TrendingUp className="w-4 h-4 text-white" />
          </div>
          {!collapsed && (
            <div className="overflow-hidden">
              <h1 className="text-sm font-bold text-white whitespace-nowrap">Solen AI Intelligence</h1>
              <p className="text-[10px] font-medium" style={{ color: 'var(--teal)' }}>Portfolio Analytics</p>
            </div>
          )}
        </div>

        {/* Nav Items */}
        <nav className="flex-1 py-4 px-2 space-y-1">
          {NAV_ITEMS.map(item => {
            const Icon = item.icon
            const active = page === item.id
            return (
              <button
                key={item.id}
                onClick={() => setPage(item.id)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                  active
                    ? 'nav-active text-white'
                    : 'text-[var(--text-secondary)] hover:text-white hover:bg-white/5'
                }`}
                title={collapsed ? item.label : undefined}
              >
                <Icon className={`w-5 h-5 flex-shrink-0 ${active ? 'text-[var(--teal)]' : ''}`} />
                {!collapsed && <span>{item.label}</span>}
              </button>
            )
          })}
        </nav>

        {/* Collapse Toggle */}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="mx-2 mb-4 p-2 rounded-lg text-[var(--text-muted)] hover:text-white hover:bg-white/5 transition-all flex items-center justify-center"
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </aside>

      {/* Main Content */}
      <main
        className={`flex-1 transition-all duration-300 ${collapsed ? 'ml-[68px]' : 'ml-[240px]'}`}
      >
        <div className="p-6 lg:p-8 max-w-[1600px] mx-auto">
          {page === 'dashboard' && (
            <Dashboard
              portfolio={portfolio}
              metrics={metrics}
              trainingStats={trainingStats}
              waveData={waveData}
            />
          )}
          {page === 'portfolio' && <Portfolio portfolio={portfolio} />}
          {page === 'model' && metrics && <ModelIntelligence metrics={metrics} trainingStats={trainingStats} />}
          {page === 'training' && <TrainingExplorer companies={trainingSet} />}
        </div>
      </main>
    </div>
  )
}
