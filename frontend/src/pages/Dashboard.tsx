import { Building2, TrendingUp, Brain, Database, Layers, Zap } from 'lucide-react'
import {
  PieChart, Pie, Cell, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid,
} from 'recharts'
import {
  PortfolioCompany, ModelMetrics, TrainingStats, WaveData,
  TIER_COLORS, getTierBg, DIMENSION_LABELS, CATEGORIES, CATEGORY_COLORS,
} from '../App'

interface Props {
  portfolio: PortfolioCompany[]
  metrics: ModelMetrics | null
  trainingStats: TrainingStats | null
  waveData: WaveData
}

export default function Dashboard({ portfolio, metrics, trainingStats, waveData }: Props) {
  const portfolioCount = portfolio.length
  const avgAIScore = portfolio.length > 0
    ? (portfolio.reduce((sum, c) => sum + c.composite_score, 0) / portfolio.length).toFixed(2)
    : '0.00'
  const modelAccuracy = metrics ? (metrics.cv_accuracy * 100).toFixed(1) : '0.0'
  const trainingSetCount = trainingStats?.total_companies || 0
  const sortedPortfolio = [...portfolio].sort((a, b) => b.composite_score - a.composite_score)

  const tierDistribution = portfolio.reduce((acc, company) => {
    const existing = acc.find(t => t.name === company.tier)
    if (existing) existing.value += 1
    else acc.push({ name: company.tier, value: 1 })
    return acc
  }, [] as { name: string; value: number }[])

  // Feature importance data from object
  const featureImportanceData = metrics
    ? Object.entries(metrics.feature_importance)
        .map(([key, value]) => ({
          name: DIMENSION_LABELS[key] || key.replace(/_/g, ' '),
          value: parseFloat((value * 100).toFixed(1)),
          key,
        }))
        .sort((a, b) => b.value - a.value)
        .slice(0, 10) // Top 10 for dashboard
    : []

  // Category importance
  const categoryData = metrics
    ? Object.entries(CATEGORIES).map(([cat, dims]) => ({
        name: cat,
        value: parseFloat((dims.reduce((s, d) => s + (metrics.feature_importance[d] || 0), 0) * 100).toFixed(1)),
        fill: CATEGORY_COLORS[cat] || '#6B7280',
      }))
    : []

  // Wave data from JSON structure
  const waveEntries = Object.entries(waveData)
  const waveTimingData = waveEntries.map(([label, companies]) => ({
    name: label,
    companies: companies.length,
    names: companies.map(c => c.name).join(', '),
  }))

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-5xl font-bold text-[var(--text-primary)] mb-2">AI Investment Intelligence</h1>
          <p className="text-xl text-[var(--text-secondary)]">Solen Software Group — Portfolio AI Readiness Platform</p>
        </div>
        <div className="glass-card px-4 py-2 rounded-lg text-sm text-teal-400 border border-teal-500/30">
          Model v4.0 • 16 dimensions • {trainingSetCount} companies trained
        </div>
      </div>

      {/* KPI Row */}
      <div className="grid grid-cols-4 gap-6">
        <div className="glass-card p-6 rounded-xl border border-teal-500/20 hover:border-teal-500/40 transition-all">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-[var(--text-secondary)] text-sm font-medium">Portfolio Companies</h3>
            <Building2 className="w-5 h-5 text-teal-400" />
          </div>
          <div className="text-4xl font-bold text-[var(--text-primary)]">{portfolioCount}</div>
          <p className="text-xs text-[var(--text-secondary)] mt-2">Active investments</p>
        </div>
        <div className="glass-card p-6 rounded-xl border border-teal-500/20 hover:border-teal-500/40 transition-all">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-[var(--text-secondary)] text-sm font-medium">Avg AI Score</h3>
            <TrendingUp className="w-5 h-5 text-teal-400" />
          </div>
          <div className="text-4xl font-bold text-[var(--text-primary)]">{avgAIScore}</div>
          <div className="mt-3 h-2 bg-slate-700 rounded-full overflow-hidden">
            <div className="h-full bg-gradient-to-r from-teal-500 to-emerald-400" style={{ width: `${parseFloat(avgAIScore) * 20}%` }} />
          </div>
        </div>
        <div className="glass-card p-6 rounded-xl border border-teal-500/20 hover:border-teal-500/40 transition-all">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-[var(--text-secondary)] text-sm font-medium">Model Accuracy</h3>
            <Brain className="w-5 h-5 text-teal-400" />
          </div>
          <div className="text-4xl font-bold text-[var(--text-primary)]">{modelAccuracy}%</div>
          <p className="text-xs text-[var(--text-secondary)] mt-2">5-fold cross-validation</p>
        </div>
        <div className="glass-card p-6 rounded-xl border border-teal-500/20 hover:border-teal-500/40 transition-all">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-[var(--text-secondary)] text-sm font-medium">Dimensions</h3>
            <Database className="w-5 h-5 text-teal-400" />
          </div>
          <div className="text-4xl font-bold text-[var(--text-primary)]">16</div>
          <p className="text-xs text-[var(--text-secondary)] mt-2">5 supercategories</p>
        </div>
      </div>

      {/* Two-Column Layout */}
      <div className="grid grid-cols-3 gap-6">
        {/* Portfolio Scoreboard */}
        <div className="col-span-2 glass-card rounded-xl border border-teal-500/20 p-6">
          <h2 className="text-xl font-bold text-[var(--text-primary)] mb-4 flex items-center gap-2">
            <Layers className="w-5 h-5 text-teal-400" />
            Portfolio Scoreboard
          </h2>
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {sortedPortfolio.map((company, index) => (
              <div key={company.name} className="flex items-center gap-4 p-3 hover:bg-slate-800/30 rounded-lg transition-colors">
                <div className="text-sm font-bold text-teal-400 w-6">{index + 1}</div>
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-[var(--text-primary)] truncate">{company.name}</div>
                  <div className="text-xs text-[var(--text-secondary)]">{company.vertical}</div>
                </div>
                <div className="flex-1">
                  <div className="relative h-2 bg-slate-700 rounded-full overflow-hidden">
                    <div
                      className="h-full transition-all"
                      style={{ width: `${(company.composite_score / 5) * 100}%`, backgroundColor: TIER_COLORS[company.tier] || '#6B7280' }}
                    />
                  </div>
                </div>
                <div className="w-16 text-right">
                  <span className="text-sm font-bold text-[var(--text-primary)]">{company.composite_score.toFixed(2)}</span>
                </div>
                <div className={`px-3 py-1 rounded-full text-xs font-medium ${getTierBg(company.tier)}`}>
                  {company.tier}
                </div>
                <div className="px-3 py-1 rounded-full text-xs font-medium bg-slate-700/50 text-slate-300">
                  W{company.wave}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right Column */}
        <div className="space-y-6">
          {/* Tier Distribution */}
          <div className="glass-card rounded-xl border border-teal-500/20 p-6">
            <h2 className="text-lg font-bold text-[var(--text-primary)] mb-4 flex items-center gap-2">
              <Zap className="w-5 h-5 text-teal-400" />
              Tier Distribution
            </h2>
            <div style={{ height: '200px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={tierDistribution} cx="50%" cy="50%" innerRadius={60} outerRadius={90} paddingAngle={2} dataKey="value">
                    {tierDistribution.map((entry, i) => (
                      <Cell key={i} fill={TIER_COLORS[entry.name] || '#6B7280'} />
                    ))}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-4 space-y-2 text-sm">
              {tierDistribution.map(tier => (
                <div key={tier.name} className="flex justify-between items-center">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: TIER_COLORS[tier.name] }} />
                    <span className="text-[var(--text-secondary)]">{tier.name}</span>
                  </div>
                  <span className="font-bold text-[var(--text-primary)]">{tier.value}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Wave Sequencing */}
          <div className="glass-card rounded-xl border border-teal-500/20 p-6">
            <h2 className="text-lg font-bold text-[var(--text-primary)] mb-4 flex items-center gap-2">
              <Layers className="w-5 h-5 text-teal-400" />
              Wave Sequencing
            </h2>
            <div className="space-y-3">
              {waveTimingData.map(wave => (
                <div key={wave.name} className="space-y-1">
                  <div className="flex justify-between items-center text-sm">
                    <span className="font-medium text-[var(--text-primary)]">{wave.name}</span>
                    <span className="text-teal-400 font-bold">{wave.companies}</span>
                  </div>
                  <div className="text-xs text-[var(--text-secondary)] truncate">{wave.names}</div>
                  <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                    <div className="h-full bg-gradient-to-r from-teal-500 to-emerald-400" style={{ width: `${(wave.companies / portfolioCount) * 100}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Category & Feature Importance */}
      <div className="grid grid-cols-2 gap-6">
        {/* Category Importance */}
        <div className="glass-card rounded-xl border border-teal-500/20 p-8">
          <h2 className="text-xl font-bold text-[var(--text-primary)] mb-6 flex items-center gap-2">
            <Brain className="w-5 h-5 text-teal-400" />
            Category Importance
          </h2>
          <div style={{ height: '250px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={categoryData} layout="vertical" margin={{ top: 5, right: 30, left: 160, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(15, 23, 42, 0.5)" />
                <XAxis type="number" stroke="rgba(107, 114, 128, 0.6)" />
                <YAxis dataKey="name" type="category" width={155} stroke="rgba(107, 114, 128, 0.6)" tick={{ fontSize: 12, fill: 'rgba(148, 163, 184, 0.8)' }} />
                <Tooltip contentStyle={{ backgroundColor: 'rgba(15, 23, 42, 0.95)', border: '1px solid rgba(20, 184, 166, 0.2)', borderRadius: '8px' }} formatter={(v: number) => [`${v.toFixed(1)}%`, 'Weight']} />
                <Bar dataKey="value" radius={[0, 8, 8, 0]}>
                  {categoryData.map((entry, i) => (
                    <Cell key={i} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Top 10 Feature Importance */}
        <div className="glass-card rounded-xl border border-teal-500/20 p-8">
          <h2 className="text-xl font-bold text-[var(--text-primary)] mb-6 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-teal-400" />
            Top 10 Dimensions
          </h2>
          <div style={{ height: '250px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={featureImportanceData} layout="vertical" margin={{ top: 5, right: 30, left: 130, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(15, 23, 42, 0.5)" />
                <XAxis type="number" stroke="rgba(107, 114, 128, 0.6)" />
                <YAxis dataKey="name" type="category" width={125} stroke="rgba(107, 114, 128, 0.6)" tick={{ fontSize: 11, fill: 'rgba(148, 163, 184, 0.8)' }} />
                <Tooltip contentStyle={{ backgroundColor: 'rgba(15, 23, 42, 0.95)', border: '1px solid rgba(20, 184, 166, 0.2)', borderRadius: '8px' }} formatter={(v: number) => [`${v.toFixed(1)}%`, 'Importance']} />
                <Bar dataKey="value" fill="url(#tealGrad)" radius={[0, 8, 8, 0]}>
                  <defs>
                    <linearGradient id="tealGrad" x1="0" y1="0" x2="1" y2="0">
                      <stop offset="0%" stopColor="#14b8a6" />
                      <stop offset="100%" stopColor="#06b6d4" />
                    </linearGradient>
                  </defs>
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  )
}
