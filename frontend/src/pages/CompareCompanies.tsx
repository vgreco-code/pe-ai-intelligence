import { useState, useMemo } from 'react'
import { GitCompareArrows, Plus, X, ArrowUp, ArrowDown, Minus } from 'lucide-react'
import {
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, Tooltip, Legend,
} from 'recharts'
import {
  PortfolioCompany, DIMENSION_LABELS, CATEGORIES, CATEGORY_COLORS,
  getTierBg, getScoreColor,
} from '../App'

interface Props {
  portfolio: PortfolioCompany[]
}

const COMPARE_COLORS = ['#02C39A', '#1ABCFE', '#F5A623', '#A259FF']

export default function CompareCompanies({ portfolio }: Props) {
  const [selected, setSelected] = useState<string[]>(
    portfolio.length >= 2
      ? [portfolio.sort((a, b) => b.composite_score - a.composite_score)[0].name, portfolio.sort((a, b) => b.composite_score - a.composite_score)[1].name]
      : []
  )
  const [dropdownOpen, setDropdownOpen] = useState(false)

  const companies = useMemo(
    () => selected.map(name => portfolio.find(c => c.name === name)!).filter(Boolean),
    [selected, portfolio]
  )

  const addCompany = (name: string) => {
    if (selected.length < 4 && !selected.includes(name)) {
      setSelected([...selected, name])
    }
    setDropdownOpen(false)
  }

  const removeCompany = (name: string) => {
    setSelected(selected.filter(n => n !== name))
  }

  const available = portfolio.filter(c => !selected.includes(c.name))

  // Radar data — all companies overlaid
  const radarData = useMemo(() => {
    const dims = Object.keys(DIMENSION_LABELS)
    return dims.map(dim => {
      const entry: Record<string, string | number> = { dimension: DIMENSION_LABELS[dim] }
      companies.forEach(c => {
        entry[c.name] = c.pillar_scores[dim] || 0
      })
      return entry
    })
  }, [companies])

  // Category comparison
  const categoryCompareData = useMemo(() => {
    return Object.entries(CATEGORIES).map(([cat, dims]) => {
      const entry: Record<string, string | number> = { category: cat }
      companies.forEach(c => {
        const avg = dims.reduce((s, d) => s + (c.pillar_scores[d] || 0), 0) / dims.length
        entry[c.name] = parseFloat(avg.toFixed(2))
      })
      return entry
    })
  }, [companies])

  // Gap analysis: dimension-level differences (only for 2 companies)
  const gapAnalysis = useMemo(() => {
    if (companies.length !== 2) return []
    const [a, b] = companies
    return Object.keys(DIMENSION_LABELS)
      .map(dim => ({
        dimension: DIMENSION_LABELS[dim],
        dim,
        scoreA: a.pillar_scores[dim] || 0,
        scoreB: b.pillar_scores[dim] || 0,
        diff: parseFloat(((a.pillar_scores[dim] || 0) - (b.pillar_scores[dim] || 0)).toFixed(1)),
      }))
      .sort((a, b) => Math.abs(b.diff) - Math.abs(a.diff))
  }, [companies])

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <div className="flex items-center gap-4 mb-2">
          <GitCompareArrows className="w-8 h-8 text-teal-400" />
          <h1 className="text-4xl font-bold text-[var(--text-primary)]">Compare Companies</h1>
        </div>
        <p className="text-[var(--text-secondary)] text-lg">
          Select up to 4 portfolio companies for side-by-side analysis
        </p>
      </div>

      {/* Selection Bar */}
      <div className="glass-card rounded-xl border border-teal-500/20 p-6">
        <div className="flex items-center gap-3 flex-wrap">
          {selected.map((name, i) => {
            const co = portfolio.find(c => c.name === name)
            return (
              <div
                key={name}
                className="flex items-center gap-2 px-4 py-2 rounded-full border"
                style={{
                  backgroundColor: `${COMPARE_COLORS[i]}15`,
                  borderColor: `${COMPARE_COLORS[i]}40`,
                }}
              >
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: COMPARE_COLORS[i] }} />
                <span className="text-sm font-medium text-[var(--text-primary)]">{name}</span>
                {co && (
                  <span className="text-xs font-bold" style={{ color: COMPARE_COLORS[i] }}>
                    {co.composite_score.toFixed(2)}
                  </span>
                )}
                <button
                  onClick={() => removeCompany(name)}
                  className="ml-1 text-[var(--text-muted)] hover:text-red-400 transition-colors"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
            )
          })}

          {selected.length < 4 && (
            <div className="relative">
              <button
                onClick={() => setDropdownOpen(!dropdownOpen)}
                className="flex items-center gap-2 px-4 py-2 rounded-full border border-dashed border-slate-600 text-[var(--text-muted)] hover:border-teal-500 hover:text-teal-400 transition-all text-sm"
              >
                <Plus className="w-4 h-4" />
                Add Company
              </button>
              {dropdownOpen && (
                <div className="absolute top-full mt-2 left-0 z-10 glass-card rounded-xl border border-slate-700/50 p-2 min-w-[200px] max-h-60 overflow-y-auto">
                  {available.map(co => (
                    <button
                      key={co.name}
                      onClick={() => addCompany(co.name)}
                      className="w-full text-left px-3 py-2 rounded-lg text-sm hover:bg-slate-800/50 transition-colors flex items-center justify-between"
                    >
                      <span className="text-[var(--text-primary)]">{co.name}</span>
                      <span className="text-xs" style={{ color: getScoreColor(co.composite_score) }}>
                        {co.composite_score.toFixed(2)}
                      </span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {companies.length < 2 && (
        <div className="text-center py-20">
          <GitCompareArrows className="w-16 h-16 text-slate-700 mx-auto mb-4" />
          <p className="text-[var(--text-muted)] text-lg">Select at least 2 companies to compare</p>
        </div>
      )}

      {companies.length >= 2 && (
        <>
          {/* Score Summary Cards */}
          <div className={`grid gap-6`} style={{ gridTemplateColumns: `repeat(${companies.length}, 1fr)` }}>
            {companies.map((co, i) => (
              <div
                key={co.name}
                className="glass-card rounded-xl p-6 border"
                style={{ borderColor: `${COMPARE_COLORS[i]}30` }}
              >
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-4 h-4 rounded-full" style={{ backgroundColor: COMPARE_COLORS[i] }} />
                  <h3 className="text-lg font-bold text-[var(--text-primary)]">{co.name}</h3>
                </div>
                <div className="text-3xl font-bold mb-2" style={{ color: COMPARE_COLORS[i] }}>
                  {co.composite_score.toFixed(2)}
                </div>
                <div className="flex items-center gap-2 mb-3">
                  <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${getTierBg(co.tier)}`}>
                    {co.tier}
                  </span>
                  <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-slate-700/50 text-slate-300">
                    Wave {co.wave}
                  </span>
                </div>
                <p className="text-xs text-[var(--text-muted)]">{co.vertical}</p>
                <p className="text-xs text-[var(--text-muted)]">{co.employee_count} employees</p>
              </div>
            ))}
          </div>

          {/* Overlaid Radar Chart */}
          <div className="glass-card rounded-xl border border-slate-700/50 p-8">
            <h2 className="text-xl font-bold text-[var(--text-primary)] mb-6">Dimension Profile Overlay</h2>
            <div style={{ height: '450px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart data={radarData}>
                  <PolarGrid stroke="rgba(255,255,255,0.08)" />
                  <PolarAngleAxis dataKey="dimension" tick={{ fill: '#94a3b8', fontSize: 10 }} />
                  <PolarRadiusAxis angle={90} domain={[0, 5]} tick={false} />
                  {companies.map((co, i) => (
                    <Radar
                      key={co.name}
                      name={co.name}
                      dataKey={co.name}
                      stroke={COMPARE_COLORS[i]}
                      fill={COMPARE_COLORS[i]}
                      fillOpacity={0.08}
                      strokeWidth={2}
                    />
                  ))}
                  <Legend
                    wrapperStyle={{ paddingTop: 20 }}
                    formatter={(value: string) => (
                      <span style={{ color: '#94a3b8', fontSize: 12 }}>{value}</span>
                    )}
                  />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Category Comparison */}
          <div className="glass-card rounded-xl border border-slate-700/50 p-8">
            <h2 className="text-xl font-bold text-[var(--text-primary)] mb-6">Category Comparison</h2>
            <div style={{ height: '320px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={categoryCompareData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                  <XAxis
                    dataKey="category"
                    stroke="rgba(107,114,128,0.6)"
                    tick={{ fontSize: 11, fill: 'rgba(148,163,184,0.8)' }}
                  />
                  <YAxis
                    domain={[0, 5]}
                    stroke="rgba(107,114,128,0.6)"
                    tick={{ fontSize: 11, fill: 'rgba(148,163,184,0.8)' }}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'rgba(15, 23, 42, 0.95)',
                      border: '1px solid rgba(20, 184, 166, 0.2)',
                      borderRadius: '8px',
                    }}
                  />
                  <Legend
                    formatter={(value: string) => (
                      <span style={{ color: '#94a3b8', fontSize: 12 }}>{value}</span>
                    )}
                  />
                  {companies.map((co, i) => (
                    <Bar
                      key={co.name}
                      dataKey={co.name}
                      fill={COMPARE_COLORS[i]}
                      fillOpacity={0.85}
                      radius={[4, 4, 0, 0]}
                    />
                  ))}
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Gap Analysis (only for exactly 2 companies) */}
          {companies.length === 2 && gapAnalysis.length > 0 && (
            <div className="glass-card rounded-xl border border-slate-700/50 p-8">
              <h2 className="text-xl font-bold text-[var(--text-primary)] mb-2">Gap Analysis</h2>
              <p className="text-sm text-[var(--text-muted)] mb-6">
                Dimension-level differences between {companies[0].name} and {companies[1].name}, sorted by largest gap
              </p>
              <div className="space-y-3">
                {gapAnalysis.map(gap => {
                  const barWidth = Math.abs(gap.diff) / 3 * 100 // scale: max diff ~3 = full width
                  const isPositive = gap.diff > 0
                  const isNeutral = Math.abs(gap.diff) < 0.2
                  return (
                    <div key={gap.dim} className="flex items-center gap-4">
                      <div className="w-32 text-right">
                        <span className="text-sm text-[var(--text-secondary)]">{gap.dimension}</span>
                      </div>
                      <div className="w-12 text-right">
                        <span className="text-xs font-bold" style={{ color: COMPARE_COLORS[0] }}>
                          {gap.scoreA.toFixed(1)}
                        </span>
                      </div>
                      {/* Diverging bar */}
                      <div className="flex-1 flex items-center">
                        <div className="w-full flex items-center relative h-6">
                          {/* Center line */}
                          <div className="absolute left-1/2 top-0 bottom-0 w-px bg-slate-600" />
                          {isPositive ? (
                            <div className="absolute right-1/2 h-4 rounded-l flex items-center" style={{
                              width: `${Math.min(barWidth, 50)}%`,
                              backgroundColor: `${COMPARE_COLORS[0]}40`,
                              borderLeft: `2px solid ${COMPARE_COLORS[0]}`,
                              transform: 'translateX(0)',
                              right: '50%',
                            }}>
                              <span className="absolute -left-1 top-1/2 -translate-y-1/2">
                                {!isNeutral && <ArrowUp className="w-3 h-3" style={{ color: COMPARE_COLORS[0] }} />}
                              </span>
                            </div>
                          ) : gap.diff < 0 ? (
                            <div className="absolute left-1/2 h-4 rounded-r flex items-center justify-end" style={{
                              width: `${Math.min(barWidth, 50)}%`,
                              backgroundColor: `${COMPARE_COLORS[1]}40`,
                              borderRight: `2px solid ${COMPARE_COLORS[1]}`,
                            }}>
                              <span className="absolute -right-1 top-1/2 -translate-y-1/2">
                                {!isNeutral && <ArrowDown className="w-3 h-3" style={{ color: COMPARE_COLORS[1] }} />}
                              </span>
                            </div>
                          ) : null}
                          {isNeutral && (
                            <div className="absolute left-1/2 -translate-x-1/2 top-1/2 -translate-y-1/2">
                              <Minus className="w-3 h-3 text-slate-500" />
                            </div>
                          )}
                        </div>
                      </div>
                      <div className="w-12">
                        <span className="text-xs font-bold" style={{ color: COMPARE_COLORS[1] }}>
                          {gap.scoreB.toFixed(1)}
                        </span>
                      </div>
                      <div className="w-16 text-right">
                        <span className={`text-xs font-bold ${
                          isNeutral ? 'text-slate-500' : isPositive ? 'text-emerald-400' : 'text-blue-400'
                        }`}>
                          {gap.diff > 0 ? '+' : ''}{gap.diff.toFixed(1)}
                        </span>
                      </div>
                    </div>
                  )
                })}
              </div>

              {/* Summary */}
              <div className="mt-6 pt-6 border-t border-slate-700/30 grid grid-cols-3 gap-4">
                <div className="bg-slate-800/30 rounded-xl p-4 text-center">
                  <div className="text-sm text-[var(--text-muted)] mb-1">{companies[0].name} leads in</div>
                  <div className="text-2xl font-bold" style={{ color: COMPARE_COLORS[0] }}>
                    {gapAnalysis.filter(g => g.diff > 0.2).length}
                  </div>
                  <div className="text-xs text-[var(--text-muted)]">dimensions</div>
                </div>
                <div className="bg-slate-800/30 rounded-xl p-4 text-center">
                  <div className="text-sm text-[var(--text-muted)] mb-1">Within 0.2 pts</div>
                  <div className="text-2xl font-bold text-slate-400">
                    {gapAnalysis.filter(g => Math.abs(g.diff) <= 0.2).length}
                  </div>
                  <div className="text-xs text-[var(--text-muted)]">dimensions</div>
                </div>
                <div className="bg-slate-800/30 rounded-xl p-4 text-center">
                  <div className="text-sm text-[var(--text-muted)] mb-1">{companies[1].name} leads in</div>
                  <div className="text-2xl font-bold" style={{ color: COMPARE_COLORS[1] }}>
                    {gapAnalysis.filter(g => g.diff < -0.2).length}
                  </div>
                  <div className="text-xs text-[var(--text-muted)]">dimensions</div>
                </div>
              </div>
            </div>
          )}

          {/* Dimension-by-Dimension Table */}
          <div className="glass-card rounded-xl border border-slate-700/50 p-8">
            <h2 className="text-xl font-bold text-[var(--text-primary)] mb-6">Full Dimension Breakdown</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-700/50">
                    <th className="text-left py-3 px-4 text-[var(--text-muted)] font-medium">Category</th>
                    <th className="text-left py-3 px-4 text-[var(--text-muted)] font-medium">Dimension</th>
                    {companies.map((co, i) => (
                      <th key={co.name} className="text-center py-3 px-4 font-medium" style={{ color: COMPARE_COLORS[i] }}>
                        {co.name}
                      </th>
                    ))}
                    {companies.length === 2 && (
                      <th className="text-center py-3 px-4 text-[var(--text-muted)] font-medium">Delta</th>
                    )}
                    <th className="text-center py-3 px-4 text-[var(--text-muted)] font-medium">Leader</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(CATEGORIES).map(([cat, dims]) => (
                    dims.map((dim, di) => {
                      const scores = companies.map(c => c.pillar_scores[dim] || 0)
                      const maxScore = Math.max(...scores)
                      const leaderIdx = scores.indexOf(maxScore)
                      const allSame = scores.every(s => Math.abs(s - scores[0]) < 0.1)
                      return (
                        <tr key={dim} className="border-b border-slate-800/30 hover:bg-slate-800/20 transition-colors">
                          {di === 0 ? (
                            <td
                              className="py-2.5 px-4 text-xs font-semibold align-top"
                              rowSpan={dims.length}
                              style={{ color: CATEGORY_COLORS[cat] }}
                            >
                              {cat}
                            </td>
                          ) : null}
                          <td className="py-2.5 px-4 text-[var(--text-secondary)]">
                            {DIMENSION_LABELS[dim]}
                          </td>
                          {companies.map((co, i) => {
                            const score = co.pillar_scores[dim] || 0
                            const isMax = score === maxScore && !allSame
                            return (
                              <td key={co.name} className="py-2.5 px-4 text-center">
                                <span
                                  className={`font-bold ${isMax ? '' : 'opacity-70'}`}
                                  style={{ color: isMax ? COMPARE_COLORS[i] : 'var(--text-secondary)' }}
                                >
                                  {score.toFixed(1)}
                                </span>
                              </td>
                            )
                          })}
                          {companies.length === 2 && (
                            <td className="py-2.5 px-4 text-center">
                              <span className={`text-xs font-bold ${
                                Math.abs(scores[0] - scores[1]) < 0.2
                                  ? 'text-slate-500'
                                  : scores[0] > scores[1] ? 'text-emerald-400' : 'text-blue-400'
                              }`}>
                                {scores[0] > scores[1] ? '+' : ''}{(scores[0] - scores[1]).toFixed(1)}
                              </span>
                            </td>
                          )}
                          <td className="py-2.5 px-4 text-center">
                            {allSame ? (
                              <span className="text-xs text-slate-500">Tied</span>
                            ) : (
                              <div className="w-3 h-3 rounded-full mx-auto" style={{ backgroundColor: COMPARE_COLORS[leaderIdx] }} />
                            )}
                          </td>
                        </tr>
                      )
                    })
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
