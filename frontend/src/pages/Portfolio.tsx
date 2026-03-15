import { useState, useMemo } from 'react'
import { Building2, Users, Filter, ArrowUpDown, Calendar } from 'lucide-react'
import {
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer,
} from 'recharts'
import {
  PortfolioCompany, TIER_COLORS, DIMENSION_LABELS, DIMENSION_SHORT,
  CATEGORIES, CATEGORY_COLORS, getScoreColor,
} from '../App'

type TierFilter = 'AI-Ready' | 'AI-Buildable' | 'AI-Emerging' | 'AI-Limited' | 'All'
type SortType = 'score' | 'name' | 'wave'

interface Props {
  portfolio: PortfolioCompany[]
  onCompanyClick?: (name: string) => void
}

const getRecommendation = (tier: string): string => {
  switch (tier) {
    case 'AI-Ready': return 'High priority for immediate AI implementation. Strong fundamentals across all dimensions.'
    case 'AI-Buildable': return 'Strong candidate for targeted AI deployment. Address key gaps in specific categories.'
    case 'AI-Emerging': return 'Moderate potential with significant development needed. Plan phased AI integration.'
    case 'AI-Limited': return 'Requires foundational work before AI deployment. Focus on core infrastructure.'
    default: return ''
  }
}

export default function Portfolio({ portfolio, onCompanyClick }: Props) {
  const [activeFilter, setActiveFilter] = useState<TierFilter>('All')
  const [sortBy, setSortBy] = useState<SortType>('score')
  const [expandedCard, setExpandedCard] = useState<string | null>(null)

  const handleCardClick = (companyName: string) => {
    if (onCompanyClick) {
      onCompanyClick(companyName)
    } else {
      setExpandedCard(expandedCard === companyName ? null : companyName)
    }
  }

  const filteredAndSorted = useMemo(() => {
    let filtered = activeFilter === 'All' ? portfolio : portfolio.filter(c => c.tier === activeFilter)
    return [...filtered].sort((a, b) => {
      if (sortBy === 'score') return b.composite_score - a.composite_score
      if (sortBy === 'name') return a.name.localeCompare(b.name)
      return a.wave - b.wave
    })
  }, [portfolio, activeFilter, sortBy])

  const radarData = (company: PortfolioCompany) =>
    Object.entries(company.pillar_scores).map(([key, value]) => ({
      name: DIMENSION_SHORT[key] || key,
      value,
      fullName: DIMENSION_LABELS[key] || key,
    }))

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <div className="flex items-center gap-4 mb-2">
          <Building2 className="w-8 h-8 text-teal-400" />
          <h1 className="text-4xl font-bold text-[var(--text-primary)]">Portfolio Companies</h1>
          <span className="ml-2 bg-teal-900/50 text-teal-200 rounded-full px-4 py-1 text-lg font-semibold border border-teal-500/30">
            {filteredAndSorted.length}
          </span>
        </div>
        <p className="text-[var(--text-secondary)] text-lg">
          16-dimension AI readiness analysis across {portfolio.length} portfolio companies
        </p>
      </div>

      {/* Filter Bar */}
      <div className="flex flex-wrap gap-4 items-center">
        <div className="flex gap-2 items-center">
          <Filter className="w-5 h-5 text-[var(--text-muted)]" />
          {(['All', 'AI-Ready', 'AI-Buildable', 'AI-Emerging', 'AI-Limited'] as TierFilter[]).map(tier => (
            <button
              key={tier}
              onClick={() => setActiveFilter(tier)}
              className={`px-4 py-2 rounded-full font-medium transition-all text-sm ${
                activeFilter === tier
                  ? 'text-white'
                  : 'bg-slate-800/50 text-[var(--text-secondary)] hover:bg-slate-700/50'
              }`}
              style={activeFilter === tier ? { backgroundColor: tier === 'All' ? 'var(--teal)' : TIER_COLORS[tier] } : {}}
            >
              {tier}
            </button>
          ))}
        </div>
        <div className="ml-auto flex gap-2 items-center">
          <ArrowUpDown className="w-4 h-4 text-[var(--text-muted)]" />
          <select
            value={sortBy}
            onChange={e => setSortBy(e.target.value as SortType)}
            className="px-4 py-2 bg-slate-800/50 text-white rounded-full font-medium cursor-pointer hover:bg-slate-700/50 transition-all text-sm border border-slate-700"
          >
            <option value="score">By Score</option>
            <option value="name">By Name</option>
            <option value="wave">By Wave</option>
          </select>
        </div>
      </div>

      {/* Company Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredAndSorted.map(company => (
          <div key={company.name}>
            {expandedCard === company.name ? (
              <div className="glass-card rounded-2xl p-8 border border-slate-700/50">
                <button onClick={() => setExpandedCard(null)} className="mb-4 text-[var(--text-muted)] hover:text-white transition-colors underline text-sm">
                  ← Back to Grid
                </button>
                <div className="mb-6">
                  <h2 className="text-2xl font-bold text-[var(--text-primary)] mb-1">{company.name}</h2>
                  <span className="inline-block bg-slate-800 text-[var(--text-secondary)] rounded-full px-3 py-1 text-sm mb-2">{company.vertical}</span>
                  {company.description && <p className="text-xs text-[var(--text-muted)] mb-4">{company.description}</p>}

                  <div className="grid grid-cols-3 gap-3 mb-6">
                    <div className="bg-slate-800/50 rounded-lg p-3">
                      <p className="text-[var(--text-muted)] text-xs">Score</p>
                      <p className="text-xl font-bold" style={{ color: TIER_COLORS[company.tier] }}>{company.composite_score.toFixed(2)}</p>
                    </div>
                    <div className="bg-slate-800/50 rounded-lg p-3">
                      <p className="text-[var(--text-muted)] text-xs">Employees</p>
                      <p className="text-xl font-bold text-[var(--text-primary)]">{company.employee_count}</p>
                    </div>
                    <div className="bg-slate-800/50 rounded-lg p-3">
                      <p className="text-[var(--text-muted)] text-xs">Wave</p>
                      <p className="text-xl font-bold text-teal-400">{company.wave}</p>
                    </div>
                  </div>
                </div>

                {/* Category Breakdown */}
                <h3 className="text-lg font-bold mb-4 text-[var(--text-primary)]">Category Analysis</h3>
                {Object.entries(CATEGORIES).map(([cat, dims]) => {
                  const catAvg = dims.reduce((s, d) => s + (company.pillar_scores[d] || 0), 0) / dims.length
                  return (
                    <div key={cat} className="mb-4">
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-sm font-semibold" style={{ color: CATEGORY_COLORS[cat] }}>{cat}</span>
                        <span className="text-sm font-bold text-[var(--text-primary)]">{catAvg.toFixed(1)}</span>
                      </div>
                      <div className="space-y-2">
                        {dims.map(d => (
                          <div key={d}>
                            <div className="flex justify-between mb-1">
                              <span className="text-xs text-[var(--text-secondary)]">{DIMENSION_LABELS[d]}</span>
                              <span className="text-xs font-semibold" style={{ color: getScoreColor(company.pillar_scores[d] || 0) }}>
                                {(company.pillar_scores[d] || 0).toFixed(1)}
                              </span>
                            </div>
                            <div className="w-full bg-slate-800 rounded-full h-1.5">
                              <div className="h-full rounded-full" style={{ width: `${((company.pillar_scores[d] || 0) / 5) * 100}%`, backgroundColor: getScoreColor(company.pillar_scores[d] || 0) }} />
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )
                })}

                <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700/50 mt-4">
                  <p className="text-sm text-[var(--text-secondary)]">
                    <span className="font-semibold text-teal-400">Recommendation: </span>
                    {getRecommendation(company.tier)}
                  </p>
                </div>
              </div>
            ) : (
              <button
                onClick={() => handleCardClick(company.name)}
                className="glass-card rounded-2xl p-6 border border-slate-700/50 w-full text-left hover:border-teal-500/50 transition-all cursor-pointer group h-full"
              >
                <div className="mb-3">
                  <h3 className="text-xl font-bold text-[var(--text-primary)] mb-1 group-hover:text-teal-400 transition-colors">{company.name}</h3>
                  <span className="inline-block bg-slate-800 text-[var(--text-muted)] rounded-full px-3 py-1 text-xs">{company.vertical}</span>
                </div>

                <div className="flex items-center gap-4 mb-3 text-xs text-[var(--text-muted)]">
                  <span className="flex items-center gap-1"><Users className="w-3 h-3" />{company.employee_count}</span>
                  {company.founded_year > 0 && <span className="flex items-center gap-1"><Calendar className="w-3 h-3" />{company.founded_year}</span>}
                </div>

                <div className="mb-3">
                  <p className="text-4xl font-bold" style={{ color: TIER_COLORS[company.tier] }}>{company.composite_score.toFixed(2)}</p>
                </div>

                <div className="flex gap-2 mb-4">
                  <span className="rounded-full px-3 py-1 text-xs font-bold text-white" style={{ backgroundColor: TIER_COLORS[company.tier] }}>
                    {company.tier.replace('AI-', '')}
                  </span>
                  <span className="bg-slate-800 text-slate-300 rounded-full px-3 py-1 text-xs font-bold">Wave {company.wave}</span>
                </div>

                {/* Radar Chart */}
                <div className="mb-4 bg-slate-800/30 rounded-lg p-2 relative">
                  <ResponsiveContainer width="100%" height={180}>
                    <RadarChart data={radarData(company)}>
                      <PolarGrid stroke="#334155" />
                      <PolarAngleAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 8 }} />
                      <PolarRadiusAxis angle={90} domain={[0, 5]} tick={false} />
                      <Radar name="Score" dataKey="value" stroke="#02C39A" fill="#02C39A" fillOpacity={0.2} />
                    </RadarChart>
                  </ResponsiveContainer>
                  {/* Centered composite score overlay */}
                  <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                    <div className="text-center">
                      <div className="text-2xl font-bold" style={{ color: TIER_COLORS[company.tier], textShadow: '0 0 12px rgba(0,0,0,0.8)' }}>
                        {company.composite_score.toFixed(1)}
                      </div>
                      <div className="text-[9px] font-medium text-slate-400" style={{ textShadow: '0 0 8px rgba(0,0,0,0.8)' }}>/ 5.0</div>
                    </div>
                  </div>
                </div>

                {/* Category Bars */}
                <div className="space-y-2">
                  {Object.entries(CATEGORIES).map(([cat, dims]) => {
                    const catAvg = dims.reduce((s, d) => s + (company.pillar_scores[d] || 0), 0) / dims.length
                    return (
                      <div key={cat}>
                        <div className="flex justify-between items-center mb-1">
                          <span className="text-[10px] font-semibold" style={{ color: CATEGORY_COLORS[cat] }}>{cat}</span>
                          <span className="text-[10px] font-bold text-[var(--text-secondary)]">{catAvg.toFixed(1)}</span>
                        </div>
                        <div className="w-full bg-slate-800 rounded-full h-1.5">
                          <div className="h-full rounded-full" style={{ width: `${(catAvg / 5) * 100}%`, backgroundColor: CATEGORY_COLORS[cat] }} />
                        </div>
                      </div>
                    )
                  })}
                </div>

                <div className="mt-4 text-center">
                  <p className="text-xs text-[var(--text-muted)] group-hover:text-teal-400 transition-colors">
                    {onCompanyClick ? 'Click for deep-dive' : 'Click to expand'}
                  </p>
                </div>
              </button>
            )}
          </div>
        ))}
      </div>

      {filteredAndSorted.length === 0 && (
        <div className="text-center py-16">
          <Building2 className="w-16 h-16 text-slate-700 mx-auto mb-4" />
          <p className="text-[var(--text-muted)] text-lg">No companies found.</p>
        </div>
      )}
    </div>
  )
}
