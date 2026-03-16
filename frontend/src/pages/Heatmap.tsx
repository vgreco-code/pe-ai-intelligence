import { useState, useMemo } from 'react'
import { Grid3X3, ArrowUpDown, Eye, EyeOff, Lightbulb, TrendingUp, AlertTriangle } from 'lucide-react'
import {
  PortfolioCompany, DIMENSION_LABELS, CATEGORIES, CATEGORY_COLORS, TIER_COLORS, getTierBg,
} from '../App'

// ── Portfolio AI Investment Heatmap ─────────────────────────────────────────
// Matrix view: companies × dimensions, color-coded by score.
// Gives a CAIO an instant "where are the gaps" view across the entire portfolio.

interface Props {
  portfolio: PortfolioCompany[]
  onCompanyClick?: (name: string) => void
}

type SortMode = 'score' | 'name' | 'wave'

function scoreToColor(score: number): string {
  // Continuous gradient from red → orange → amber → teal → emerald
  if (score >= 4.0) return 'rgba(2, 195, 154, 0.85)'   // emerald/teal
  if (score >= 3.5) return 'rgba(2, 195, 154, 0.6)'
  if (score >= 3.0) return 'rgba(2, 195, 154, 0.38)'
  if (score >= 2.5) return 'rgba(245, 166, 35, 0.5)'    // amber
  if (score >= 2.0) return 'rgba(242, 78, 30, 0.4)'     // orange
  if (score >= 1.5) return 'rgba(239, 68, 68, 0.4)'     // red
  return 'rgba(239, 68, 68, 0.25)'                       // deep red
}

function scoreToTextColor(score: number): string {
  if (score >= 3.5) return '#02C39A'
  if (score >= 2.8) return '#F5A623'
  if (score >= 2.0) return '#F24E1E'
  return '#ef4444'
}

// Find portfolio-wide gaps (dimensions where average is lowest)
function getPortfolioGaps(portfolio: PortfolioCompany[]) {
  const dimAvgs: { dim: string; avg: number; label: string; cat: string }[] = []

  for (const [cat, dims] of Object.entries(CATEGORIES)) {
    for (const dim of dims) {
      const avg = portfolio.reduce((s, c) => s + (c.pillar_scores[dim] || 0), 0) / portfolio.length
      dimAvgs.push({ dim, avg, label: DIMENSION_LABELS[dim] || dim, cat })
    }
  }

  return dimAvgs.sort((a, b) => a.avg - b.avg)
}

export default function Heatmap({ portfolio, onCompanyClick }: Props) {
  const [sortBy, setSortBy] = useState<SortMode>('score')
  const [showCategories, setShowCategories] = useState(true)
  const [hoveredCell, setHoveredCell] = useState<{ company: string; dim: string } | null>(null)

  const sorted = useMemo(() => {
    return [...portfolio].sort((a, b) => {
      if (sortBy === 'score') return b.composite_score - a.composite_score
      if (sortBy === 'name') return a.name.localeCompare(b.name)
      return a.wave - b.wave
    })
  }, [portfolio, sortBy])

  const allDims = useMemo(() => {
    return Object.entries(CATEGORIES).flatMap(([cat, dims]) =>
      dims.map(d => ({ dim: d, label: DIMENSION_LABELS[d] || d, cat }))
    )
  }, [])

  const gaps = useMemo(() => getPortfolioGaps(portfolio), [portfolio])
  const topGaps = gaps.slice(0, 5)
  const topStrengths = [...gaps].sort((a, b) => b.avg - a.avg).slice(0, 5)

  // Portfolio-wide averages per dimension
  const dimAvgMap = useMemo(() => {
    const map: Record<string, number> = {}
    for (const d of allDims) {
      map[d.dim] = portfolio.reduce((s, c) => s + (c.pillar_scores[d.dim] || 0), 0) / portfolio.length
    }
    return map
  }, [portfolio, allDims])

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <div className="flex items-center gap-4 mb-2">
          <Grid3X3 className="w-8 h-8 text-teal-400" />
          <h1 className="text-4xl font-bold text-[var(--text-primary)]">AI Investment Heatmap</h1>
        </div>
        <p className="text-[var(--text-secondary)] text-lg">
          Portfolio-wide dimension analysis across {portfolio.length} companies — identify gaps and investment priorities at a glance
        </p>
      </div>

      {/* Controls */}
      <div className="flex gap-3 items-center">
        <div className="flex items-center gap-2">
          <ArrowUpDown className="w-4 h-4 text-[var(--text-muted)]" />
          <select
            value={sortBy}
            onChange={e => setSortBy(e.target.value as SortMode)}
            className="px-4 py-2 bg-slate-800/50 text-white rounded-full font-medium cursor-pointer hover:bg-slate-700/50 transition-all text-sm border border-slate-700"
          >
            <option value="score">Sort by Score</option>
            <option value="name">Sort by Name</option>
            <option value="wave">Sort by Wave</option>
          </select>
        </div>
        <button
          onClick={() => setShowCategories(!showCategories)}
          className="flex items-center gap-2 px-4 py-2 bg-slate-800/50 text-[var(--text-secondary)] rounded-full text-sm border border-slate-700 hover:bg-slate-700/50 transition-all"
        >
          {showCategories ? <Eye className="w-3.5 h-3.5" /> : <EyeOff className="w-3.5 h-3.5" />}
          Category headers
        </button>

        {/* Legend */}
        <div className="ml-auto flex items-center gap-1 text-[10px] text-[var(--text-muted)]">
          <span>Score:</span>
          {[1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5].map(s => (
            <div
              key={s}
              className="w-5 h-4 rounded-sm"
              style={{ backgroundColor: scoreToColor(s) }}
              title={s.toFixed(1)}
            />
          ))}
          <span className="ml-1">Low → High</span>
        </div>
      </div>

      {/* Heatmap Table */}
      <div className="glass-card rounded-xl border border-teal-500/20 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-xs">
            <thead>
              {/* Category header row */}
              {showCategories && (
                <tr>
                  <th className="sticky left-0 z-20 bg-slate-900/95 p-0 w-36" />
                  <th className="bg-slate-900/95 p-0 w-14" /> {/* Score column */}
                  <th className="bg-slate-900/95 p-0 w-10" /> {/* Tier column */}
                  {Object.entries(CATEGORIES).map(([cat, dims]) => (
                    <th
                      key={cat}
                      colSpan={dims.length}
                      className="text-center py-2 px-1 font-semibold border-b border-slate-700/50"
                      style={{ color: CATEGORY_COLORS[cat], borderBottom: `2px solid ${CATEGORY_COLORS[cat]}40` }}
                    >
                      {cat}
                    </th>
                  ))}
                </tr>
              )}
              {/* Dimension header row */}
              <tr className="border-b border-slate-700/50">
                <th className="sticky left-0 z-20 bg-slate-900/95 text-left p-2 font-semibold text-[var(--text-secondary)] w-36">
                  Company
                </th>
                <th className="bg-slate-900/95 text-center p-2 font-semibold text-teal-400 w-14">
                  Score
                </th>
                <th className="bg-slate-900/95 text-center p-2 font-semibold text-[var(--text-secondary)] w-10">
                  Tier
                </th>
                {allDims.map(d => (
                  <th
                    key={d.dim}
                    className="text-center p-1.5 font-medium text-[var(--text-muted)] min-w-[52px] max-w-[60px]"
                    title={d.label}
                    style={{ borderLeft: allDims.indexOf(d) > 0 && allDims[allDims.indexOf(d) - 1]?.cat !== d.cat ? `2px solid ${CATEGORY_COLORS[d.cat]}20` : undefined }}
                  >
                    <div className="truncate text-[9px] leading-tight" style={{ writingMode: 'initial' }}>
                      {d.label}
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sorted.map((company) => (
                <tr
                  key={company.name}
                  className="border-b border-slate-800/30 hover:bg-slate-800/20 transition-colors"
                >
                  <td className="sticky left-0 z-10 bg-slate-900/95 p-2">
                    <button
                      onClick={() => onCompanyClick?.(company.name)}
                      className="font-semibold text-[var(--text-primary)] hover:text-teal-400 transition-colors text-left truncate block max-w-[130px]"
                      title={company.name}
                    >
                      {company.name}
                    </button>
                    <div className="text-[9px] text-[var(--text-muted)] truncate max-w-[130px]">{company.vertical}</div>
                  </td>
                  <td className="text-center p-1">
                    <span className="font-bold text-sm" style={{ color: TIER_COLORS[company.tier] }}>
                      {company.composite_score.toFixed(2)}
                    </span>
                  </td>
                  <td className="text-center p-1">
                    <span className={`inline-block px-1.5 py-0.5 rounded text-[9px] font-bold ${getTierBg(company.tier)}`}>
                      {company.tier.replace('AI-', '')}
                    </span>
                  </td>
                  {allDims.map((d, ci) => {
                    const score = company.pillar_scores[d.dim] || 0
                    const isHovered = hoveredCell?.company === company.name && hoveredCell?.dim === d.dim
                    return (
                      <td
                        key={d.dim}
                        className="text-center p-0.5 relative"
                        style={{
                          borderLeft: ci > 0 && allDims[ci - 1]?.cat !== d.cat ? `2px solid ${CATEGORY_COLORS[d.cat]}10` : undefined,
                        }}
                        onMouseEnter={() => setHoveredCell({ company: company.name, dim: d.dim })}
                        onMouseLeave={() => setHoveredCell(null)}
                      >
                        <div
                          className="w-full h-8 rounded-sm flex items-center justify-center transition-all cursor-default"
                          style={{
                            backgroundColor: scoreToColor(score),
                            outline: isHovered ? '2px solid rgba(255,255,255,0.4)' : 'none',
                          }}
                          title={`${company.name} — ${d.label}: ${score.toFixed(1)}`}
                        >
                          <span
                            className="font-bold text-[10px]"
                            style={{ color: scoreToTextColor(score) }}
                          >
                            {score.toFixed(1)}
                          </span>
                        </div>
                      </td>
                    )
                  })}
                </tr>
              ))}

              {/* Portfolio average row */}
              <tr className="border-t-2 border-teal-500/30 bg-slate-800/30">
                <td className="sticky left-0 z-10 bg-slate-800/50 p-2">
                  <span className="font-bold text-teal-400 text-xs">Portfolio Avg</span>
                </td>
                <td className="text-center p-1">
                  <span className="font-bold text-sm text-teal-400">
                    {(portfolio.reduce((s, c) => s + c.composite_score, 0) / portfolio.length).toFixed(2)}
                  </span>
                </td>
                <td className="text-center p-1" />
                {allDims.map((d, ci) => {
                  const avg = dimAvgMap[d.dim] || 0
                  return (
                    <td
                      key={d.dim}
                      className="text-center p-0.5"
                      style={{
                        borderLeft: ci > 0 && allDims[ci - 1]?.cat !== d.cat ? `2px solid ${CATEGORY_COLORS[d.cat]}10` : undefined,
                      }}
                    >
                      <div
                        className="w-full h-8 rounded-sm flex items-center justify-center"
                        style={{ backgroundColor: scoreToColor(avg) }}
                      >
                        <span className="font-bold text-[10px]" style={{ color: scoreToTextColor(avg) }}>
                          {avg.toFixed(1)}
                        </span>
                      </div>
                    </td>
                  )
                })}
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Insights Row */}
      <div className="grid grid-cols-3 gap-6">
        {/* Portfolio Gaps */}
        <div className="glass-card rounded-xl border border-orange-500/20 p-6">
          <h2 className="text-lg font-bold text-orange-400 mb-4 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5" />
            Portfolio-Wide Gaps
          </h2>
          <p className="text-xs text-[var(--text-muted)] mb-4">
            Dimensions where the portfolio average is lowest — cross-cutting investment priorities
          </p>
          <div className="space-y-3">
            {topGaps.map((g, i) => (
              <div key={i} className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-orange-500/10 flex items-center justify-center flex-shrink-0">
                  <span className="text-xs font-bold text-orange-400">{g.avg.toFixed(1)}</span>
                </div>
                <div className="flex-1">
                  <div className="text-sm font-medium text-[var(--text-primary)]">{g.label}</div>
                  <div className="text-[10px] font-medium" style={{ color: CATEGORY_COLORS[g.cat] }}>{g.cat}</div>
                </div>
                <div className="w-16 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                  <div className="h-full bg-orange-500 rounded-full" style={{ width: `${(g.avg / 5) * 100}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Portfolio Strengths */}
        <div className="glass-card rounded-xl border border-emerald-500/20 p-6">
          <h2 className="text-lg font-bold text-emerald-400 mb-4 flex items-center gap-2">
            <TrendingUp className="w-5 h-5" />
            Portfolio Strengths
          </h2>
          <p className="text-xs text-[var(--text-muted)] mb-4">
            Dimensions where the portfolio average is highest — leverage these foundations
          </p>
          <div className="space-y-3">
            {topStrengths.map((s, i) => (
              <div key={i} className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-emerald-500/10 flex items-center justify-center flex-shrink-0">
                  <span className="text-xs font-bold text-emerald-400">{s.avg.toFixed(1)}</span>
                </div>
                <div className="flex-1">
                  <div className="text-sm font-medium text-[var(--text-primary)]">{s.label}</div>
                  <div className="text-[10px] font-medium" style={{ color: CATEGORY_COLORS[s.cat] }}>{s.cat}</div>
                </div>
                <div className="w-16 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                  <div className="h-full bg-emerald-500 rounded-full" style={{ width: `${(s.avg / 5) * 100}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Strategic Insights */}
        <div className="glass-card rounded-xl border border-purple-500/20 p-6">
          <h2 className="text-lg font-bold text-purple-400 mb-4 flex items-center gap-2">
            <Lightbulb className="w-5 h-5" />
            Strategic Insights
          </h2>
          <div className="space-y-3">
            {(() => {
              const insights: { text: string; color: string }[] = []
              const readyCount = portfolio.filter(c => c.tier === 'AI-Ready' || c.tier === 'AI-Buildable').length
              const w1Count = portfolio.filter(c => c.wave === 1).length

              // Gap-based insight
              if (topGaps[0]?.avg < 2.0) {
                insights.push({
                  text: `"${topGaps[0].label}" is the portfolio's biggest gap at ${topGaps[0].avg.toFixed(1)} avg. A cross-portfolio program here would lift ${portfolio.filter(c => (c.pillar_scores[topGaps[0].dim] || 0) < 2.0).length} companies.`,
                  color: '#F24E1E',
                })
              }

              // Ready companies insight
              insights.push({
                text: `${readyCount} of ${portfolio.length} companies (${Math.round(readyCount / portfolio.length * 100)}%) are AI-Buildable or higher — these should receive priority AI investment dollars.`,
                color: '#02C39A',
              })

              // Wave insight
              if (w1Count > 0) {
                insights.push({
                  text: `${w1Count} Wave 1 companies can begin AI deployment immediately. Focus on revenue-generating AI features first for fastest ROI.`,
                  color: '#F5A623',
                })
              }

              // Strength insight
              insights.push({
                text: `"${topStrengths[0]?.label}" is the strongest dimension portfolio-wide (${topStrengths[0]?.avg.toFixed(1)} avg) — leverage this as the foundation for more advanced AI capabilities.`,
                color: '#8b5cf6',
              })

              // Scale insight
              if (portfolio.filter(c => c.employee_count < 50).length > portfolio.length / 2) {
                insights.push({
                  text: `Most portfolio companies are small (<50 employees). AI strategy should emphasize embedded AI tools and managed services over building internal ML teams.`,
                  color: '#06b6d4',
                })
              }

              return insights.slice(0, 4).map((ins, i) => (
                <div key={i} className="flex items-start gap-3 p-3 bg-slate-800/30 rounded-lg border border-slate-700/30">
                  <div className="w-1 h-full min-h-[40px] rounded-full flex-shrink-0" style={{ backgroundColor: ins.color }} />
                  <p className="text-xs text-[var(--text-secondary)] leading-relaxed">{ins.text}</p>
                </div>
              ))
            })()}
          </div>
        </div>
      </div>
    </div>
  )
}
