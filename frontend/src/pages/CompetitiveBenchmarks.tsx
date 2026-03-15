import { useState, useMemo } from 'react'
import { BarChart3, Target, TrendingUp, Users, ChevronDown, ChevronUp } from 'lucide-react'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, ReferenceLine,
} from 'recharts'
import { getTierBg, getScoreColor } from '../App'

export interface BenchmarkCompany {
  name: string
  score: number
  tier: string
  wave: number
  peer_verticals: string[]
  peer_vertical: string
  peer_count: number
  vertical_rank: number
  vertical_percentile: number
  vertical_avg: number
  vertical_max: number
  vertical_min: number
  nearest_peers: { name: string; score: number; tier: string; vertical: string }[]
}

interface Props {
  benchmarks: BenchmarkCompany[]
}

export default function CompetitiveBenchmarks({ benchmarks }: Props) {
  const [expandedCompany, setExpandedCompany] = useState<string | null>(null)
  const [sortBy, setSortBy] = useState<'percentile' | 'score' | 'name'>('percentile')

  const sorted = useMemo(() => {
    return [...benchmarks].sort((a, b) => {
      if (sortBy === 'percentile') return b.vertical_percentile - a.vertical_percentile
      if (sortBy === 'score') return b.score - a.score
      return a.name.localeCompare(b.name)
    })
  }, [benchmarks, sortBy])

  const avgPercentile = benchmarks.length > 0
    ? (benchmarks.reduce((s, b) => s + b.vertical_percentile, 0) / benchmarks.length)
    : 0

  const aboveAvg = benchmarks.filter(b => b.score > b.vertical_avg).length
  const topQuartile = benchmarks.filter(b => b.vertical_percentile >= 75).length

  const getPercentileColor = (p: number) => {
    if (p >= 75) return '#02C39A'
    if (p >= 50) return '#F5A623'
    if (p >= 25) return '#F24E1E'
    return '#ef4444'
  }

  const getPercentileLabel = (p: number) => {
    if (p >= 75) return 'Top Quartile'
    if (p >= 50) return 'Above Median'
    if (p >= 25) return 'Below Median'
    return 'Bottom Quartile'
  }

  // Chart data for overview
  const chartData = [...benchmarks]
    .sort((a, b) => b.vertical_percentile - a.vertical_percentile)
    .map(b => ({
      name: b.name,
      percentile: b.vertical_percentile,
      fill: getPercentileColor(b.vertical_percentile),
    }))

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <div className="flex items-center gap-4 mb-2">
          <BarChart3 className="w-8 h-8 text-teal-400" />
          <h1 className="text-4xl font-bold text-[var(--text-primary)]">Competitive Benchmarks</h1>
        </div>
        <p className="text-[var(--text-secondary)] text-lg">
          How each portfolio company ranks against peers in their vertical
        </p>
      </div>

      {/* KPI Row */}
      <div className="grid grid-cols-4 gap-6">
        <div className="glass-card p-6 rounded-xl border border-teal-500/20">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-[var(--text-secondary)] text-sm font-medium">Avg Percentile</h3>
            <Target className="w-5 h-5 text-teal-400" />
          </div>
          <div className="text-4xl font-bold" style={{ color: getPercentileColor(avgPercentile) }}>
            P{avgPercentile.toFixed(0)}
          </div>
          <p className="text-xs text-[var(--text-secondary)] mt-2">Across all verticals</p>
        </div>
        <div className="glass-card p-6 rounded-xl border border-teal-500/20">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-[var(--text-secondary)] text-sm font-medium">Above Vertical Avg</h3>
            <TrendingUp className="w-5 h-5 text-teal-400" />
          </div>
          <div className="text-4xl font-bold text-[var(--text-primary)]">
            {aboveAvg}<span className="text-lg text-[var(--text-muted)]">/{benchmarks.length}</span>
          </div>
          <p className="text-xs text-[var(--text-secondary)] mt-2">Companies outperforming peers</p>
        </div>
        <div className="glass-card p-6 rounded-xl border border-teal-500/20">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-[var(--text-secondary)] text-sm font-medium">Top Quartile</h3>
            <BarChart3 className="w-5 h-5 text-emerald-400" />
          </div>
          <div className="text-4xl font-bold text-emerald-400">{topQuartile}</div>
          <p className="text-xs text-[var(--text-secondary)] mt-2">75th+ percentile in vertical</p>
        </div>
        <div className="glass-card p-6 rounded-xl border border-teal-500/20">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-[var(--text-secondary)] text-sm font-medium">Peer Pool</h3>
            <Users className="w-5 h-5 text-teal-400" />
          </div>
          <div className="text-4xl font-bold text-[var(--text-primary)]">
            {benchmarks.reduce((s, b) => s + b.peer_count, 0)}
          </div>
          <p className="text-xs text-[var(--text-secondary)] mt-2">Total peer comparisons</p>
        </div>
      </div>

      {/* Percentile Overview Chart */}
      <div className="glass-card rounded-xl border border-teal-500/20 p-8">
        <h2 className="text-xl font-bold text-[var(--text-primary)] mb-6">Vertical Percentile Rankings</h2>
        <div style={{ height: '380px' }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 60 }}>
              <XAxis
                dataKey="name"
                stroke="rgba(107, 114, 128, 0.6)"
                tick={{ fontSize: 11, fill: 'rgba(148, 163, 184, 0.8)' }}
                angle={-35}
                textAnchor="end"
                height={80}
              />
              <YAxis
                domain={[0, 100]}
                stroke="rgba(107, 114, 128, 0.6)"
                tick={{ fontSize: 11, fill: 'rgba(148, 163, 184, 0.8)' }}
                tickFormatter={(v: number) => `P${v}`}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'rgba(15, 23, 42, 0.95)',
                  border: '1px solid rgba(20, 184, 166, 0.2)',
                  borderRadius: '8px',
                }}
                formatter={(v: number) => [`P${v.toFixed(1)}`, 'Percentile']}
              />
              <ReferenceLine y={50} stroke="rgba(245, 166, 35, 0.4)" strokeDasharray="5 5" label={{ value: 'Median', fill: 'rgba(245, 166, 35, 0.6)', fontSize: 11 }} />
              <ReferenceLine y={75} stroke="rgba(2, 195, 154, 0.4)" strokeDasharray="5 5" label={{ value: 'Top Quartile', fill: 'rgba(2, 195, 154, 0.6)', fontSize: 11 }} />
              <Bar dataKey="percentile" radius={[6, 6, 0, 0]}>
                {chartData.map((entry, i) => (
                  <Cell key={i} fill={entry.fill} fillOpacity={0.85} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Sort controls */}
      <div className="flex items-center gap-3">
        <span className="text-sm text-[var(--text-muted)]">Sort by:</span>
        {(['percentile', 'score', 'name'] as const).map(s => (
          <button
            key={s}
            onClick={() => setSortBy(s)}
            className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
              sortBy === s
                ? 'bg-teal-500/20 text-teal-400 border border-teal-500/30'
                : 'bg-slate-800/50 text-[var(--text-secondary)] hover:bg-slate-700/50'
            }`}
          >
            {s === 'percentile' ? 'Percentile' : s === 'score' ? 'AI Score' : 'Name'}
          </button>
        ))}
      </div>

      {/* Company Benchmark Cards */}
      <div className="space-y-4">
        {sorted.map(b => {
          const isExpanded = expandedCompany === b.name
          return (
            <div key={b.name} className="glass-card rounded-xl border border-slate-700/50 overflow-hidden">
              <button
                onClick={() => setExpandedCompany(isExpanded ? null : b.name)}
                className="w-full p-6 text-left hover:bg-slate-800/20 transition-colors"
              >
                <div className="flex items-center gap-6">
                  {/* Percentile gauge */}
                  <div className="relative w-16 h-16 flex-shrink-0">
                    <svg viewBox="0 0 36 36" className="w-16 h-16 -rotate-90">
                      <circle cx="18" cy="18" r="15.9" fill="none" stroke="rgba(30,41,59,0.5)" strokeWidth="3" />
                      <circle
                        cx="18" cy="18" r="15.9" fill="none"
                        stroke={getPercentileColor(b.vertical_percentile)}
                        strokeWidth="3"
                        strokeDasharray={`${b.vertical_percentile} ${100 - b.vertical_percentile}`}
                        strokeLinecap="round"
                      />
                    </svg>
                    <div className="absolute inset-0 flex items-center justify-center">
                      <span className="text-sm font-bold" style={{ color: getPercentileColor(b.vertical_percentile) }}>
                        P{b.vertical_percentile.toFixed(0)}
                      </span>
                    </div>
                  </div>

                  {/* Company info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-1">
                      <h3 className="text-lg font-bold text-[var(--text-primary)]">{b.name}</h3>
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${getTierBg(b.tier)}`}>
                        {b.tier}
                      </span>
                      <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-slate-700/50 text-slate-300">
                        Wave {b.wave}
                      </span>
                    </div>
                    <p className="text-sm text-[var(--text-muted)] truncate">
                      vs {b.peer_vertical} ({b.peer_count} peers)
                    </p>
                  </div>

                  {/* Score + rank */}
                  <div className="text-right flex-shrink-0">
                    <div className="text-2xl font-bold" style={{ color: getScoreColor(b.score) }}>
                      {b.score.toFixed(2)}
                    </div>
                    <div className="text-xs text-[var(--text-muted)]">
                      Rank {b.vertical_rank}/{b.peer_count}
                    </div>
                  </div>

                  {/* Percentile label */}
                  <div className="flex-shrink-0 text-right w-32">
                    <div className="text-sm font-semibold" style={{ color: getPercentileColor(b.vertical_percentile) }}>
                      {getPercentileLabel(b.vertical_percentile)}
                    </div>
                    <div className="mt-1 h-2 bg-slate-700 rounded-full overflow-hidden w-full">
                      <div
                        className="h-full rounded-full transition-all"
                        style={{
                          width: `${b.vertical_percentile}%`,
                          backgroundColor: getPercentileColor(b.vertical_percentile),
                        }}
                      />
                    </div>
                  </div>

                  {/* Expand icon */}
                  <div className="flex-shrink-0 text-[var(--text-muted)]">
                    {isExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                  </div>
                </div>
              </button>

              {/* Expanded detail */}
              {isExpanded && (
                <div className="border-t border-slate-700/50 p-6 bg-slate-900/30">
                  <div className="grid grid-cols-3 gap-6">
                    {/* Vertical stats */}
                    <div>
                      <h4 className="text-sm font-semibold text-[var(--text-primary)] mb-3">Vertical Stats</h4>
                      <div className="space-y-3">
                        <div className="flex justify-between">
                          <span className="text-sm text-[var(--text-muted)]">Vertical Avg</span>
                          <span className="text-sm font-bold text-[var(--text-primary)]">{b.vertical_avg.toFixed(2)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm text-[var(--text-muted)]">Vertical Max</span>
                          <span className="text-sm font-bold text-emerald-400">{b.vertical_max.toFixed(2)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm text-[var(--text-muted)]">Vertical Min</span>
                          <span className="text-sm font-bold text-red-400">{b.vertical_min.toFixed(2)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm text-[var(--text-muted)]">Your Score</span>
                          <span className="text-sm font-bold" style={{ color: getScoreColor(b.score) }}>{b.score.toFixed(2)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm text-[var(--text-muted)]">Gap to Max</span>
                          <span className="text-sm font-bold text-amber-400">
                            {b.score < b.vertical_max ? `-${(b.vertical_max - b.score).toFixed(2)}` : 'At max'}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Position visual */}
                    <div>
                      <h4 className="text-sm font-semibold text-[var(--text-primary)] mb-3">Position in Vertical</h4>
                      <div className="relative h-48 flex items-end gap-1">
                        {/* Score range bar */}
                        <div className="flex-1 relative">
                          <div className="absolute inset-x-0 bottom-0 bg-slate-800 rounded" style={{ height: '100%' }}>
                            {/* Vertical range */}
                            <div
                              className="absolute inset-x-0 bg-slate-700/50 rounded"
                              style={{
                                bottom: `${(b.vertical_min / 5) * 100}%`,
                                height: `${((b.vertical_max - b.vertical_min) / 5) * 100}%`,
                              }}
                            />
                            {/* Avg line */}
                            <div
                              className="absolute inset-x-0 h-0.5 bg-amber-400/50"
                              style={{ bottom: `${(b.vertical_avg / 5) * 100}%` }}
                            />
                            {/* Company position */}
                            <div
                              className="absolute inset-x-2 h-2 rounded-full"
                              style={{
                                bottom: `${(b.score / 5) * 100}%`,
                                backgroundColor: getPercentileColor(b.vertical_percentile),
                                boxShadow: `0 0 8px ${getPercentileColor(b.vertical_percentile)}`,
                              }}
                            />
                          </div>
                        </div>
                        {/* Labels */}
                        <div className="w-16 h-full relative text-xs text-[var(--text-muted)]">
                          <div className="absolute" style={{ bottom: `${(b.vertical_max / 5) * 100}%`, transform: 'translateY(50%)' }}>
                            {b.vertical_max.toFixed(1)}
                          </div>
                          <div className="absolute text-amber-400" style={{ bottom: `${(b.vertical_avg / 5) * 100}%`, transform: 'translateY(50%)' }}>
                            Avg {b.vertical_avg.toFixed(1)}
                          </div>
                          <div className="absolute" style={{ bottom: `${(b.vertical_min / 5) * 100}%`, transform: 'translateY(50%)' }}>
                            {b.vertical_min.toFixed(1)}
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Nearest peers */}
                    <div>
                      <h4 className="text-sm font-semibold text-[var(--text-primary)] mb-3">Nearest Peers</h4>
                      <div className="space-y-2">
                        {b.nearest_peers.slice(0, 5).map((peer, i) => (
                          <div key={i} className="flex items-center gap-3 p-2 bg-slate-800/30 rounded-lg">
                            <div className="w-6 text-center text-xs font-bold text-[var(--text-muted)]">{i + 1}</div>
                            <div className="flex-1 min-w-0">
                              <div className="text-sm font-medium text-[var(--text-primary)] truncate">{peer.name}</div>
                              <div className="text-xs text-[var(--text-muted)] truncate">{peer.vertical}</div>
                            </div>
                            <div className="text-sm font-bold" style={{ color: getScoreColor(peer.score) }}>
                              {peer.score.toFixed(2)}
                            </div>
                            <span className={`px-2 py-0.5 rounded-full text-xs ${getTierBg(peer.tier)}`}>
                              {peer.tier.replace('AI-', '')}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Peer verticals tags */}
                  <div className="mt-4 pt-4 border-t border-slate-700/30">
                    <span className="text-xs text-[var(--text-muted)] mr-2">Compared against:</span>
                    {b.peer_verticals.map((v, i) => (
                      <span key={i} className="inline-block bg-slate-800/50 text-[var(--text-secondary)] rounded-full px-3 py-1 text-xs mr-2 mb-1">
                        {v}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
