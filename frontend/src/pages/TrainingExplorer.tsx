import { useState, useMemo } from 'react'
import { Database, Search, ChevronDown } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Cell } from 'recharts'
import { TrainingCompany, TIER_COLORS, getScoreColor } from '../App'

interface Props {
  companies: TrainingCompany[]
}

export default function TrainingExplorer({ companies }: Props) {
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedTier, setSelectedTier] = useState<string | null>(null)
  const [sortOption, setSortOption] = useState('score-desc')
  const [displayedRows, setDisplayedRows] = useState(50)

  const uniqueVerticals = useMemo(() => new Set(companies.map(c => c.vertical)).size, [companies])
  const avgScore = useMemo(() => companies.length > 0 ? (companies.reduce((s, c) => s + c.composite_score, 0) / companies.length).toFixed(2) : '0', [companies])
  const scoreRange = useMemo(() => {
    if (!companies.length) return { min: '0', max: '0' }
    const scores = companies.map(c => c.composite_score)
    return { min: Math.min(...scores).toFixed(2), max: Math.max(...scores).toFixed(2) }
  }, [companies])

  const tierCounts = useMemo(() => ({
    'AI-Ready': companies.filter(c => c.tier === 'AI-Ready').length,
    'AI-Buildable': companies.filter(c => c.tier === 'AI-Buildable').length,
    'AI-Emerging': companies.filter(c => c.tier === 'AI-Emerging').length,
    'AI-Limited': companies.filter(c => c.tier === 'AI-Limited').length,
  }), [companies])

  const filteredAndSorted = useMemo(() => {
    let filtered = companies.filter(c => {
      const matchesSearch = !searchTerm || c.name.toLowerCase().includes(searchTerm.toLowerCase()) || c.vertical.toLowerCase().includes(searchTerm.toLowerCase())
      const matchesTier = !selectedTier || c.tier === selectedTier
      return matchesSearch && matchesTier
    })
    switch (sortOption) {
      case 'score-desc': filtered.sort((a, b) => b.composite_score - a.composite_score); break
      case 'score-asc': filtered.sort((a, b) => a.composite_score - b.composite_score); break
      case 'name-asc': filtered.sort((a, b) => a.name.localeCompare(b.name)); break
      case 'employees': filtered.sort((a, b) => (b.employee_count || 0) - (a.employee_count || 0)); break
      case 'founded': filtered.sort((a, b) => (b.founded_year || 0) - (a.founded_year || 0)); break
    }
    return filtered
  }, [companies, searchTerm, selectedTier, sortOption])

  const scoreDistribution = useMemo(() => {
    const bins = Array.from({ length: 14 }, (_, i) => {
      const min = 1.0 + i * 0.25
      return { range: `${min.toFixed(1)}-${(min + 0.25).toFixed(1)}`, min, max: min + 0.25, count: 0 }
    })
    companies.forEach(c => {
      const bin = bins.find(b => c.composite_score >= b.min && c.composite_score < b.max)
      if (bin) bin.count++
    })
    return bins.filter(b => b.count > 0).map(b => ({
      ...b,
      color: b.min >= 4.0 ? TIER_COLORS['AI-Ready'] : b.min >= 3.2 ? TIER_COLORS['AI-Buildable'] : b.min >= 2.5 ? TIER_COLORS['AI-Emerging'] : TIER_COLORS['AI-Limited'],
    }))
  }, [companies])

  const visible = filteredAndSorted.slice(0, displayedRows)
  const hasMore = displayedRows < filteredAndSorted.length

  const fmtFunding = (f: number) => !f ? 'N/A' : f >= 1000 ? `$${(f / 1000).toFixed(1)}B` : `$${f}M`

  return (
    <div className="space-y-8">
      <div>
        <div className="flex items-center gap-3 mb-2">
          <Database className="w-8 h-8 text-emerald-400" />
          <h1 className="text-4xl font-bold text-[var(--text-primary)]">Training Data Explorer</h1>
        </div>
        <p className="text-[var(--text-secondary)]">{companies.length} companies across {uniqueVerticals} verticals • 16-dimension AI readiness analysis</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4">
        <div className="glass-card p-6 rounded-xl border border-slate-700">
          <div className="text-[var(--text-muted)] text-sm mb-2">Total Companies</div>
          <div className="text-3xl font-bold text-[var(--text-primary)]">{companies.length}</div>
        </div>
        <div className="glass-card p-6 rounded-xl border border-slate-700">
          <div className="text-[var(--text-muted)] text-sm mb-2">Unique Verticals</div>
          <div className="text-3xl font-bold text-[var(--text-primary)]">{uniqueVerticals}</div>
        </div>
        <div className="glass-card p-6 rounded-xl border border-slate-700">
          <div className="text-[var(--text-muted)] text-sm mb-2">Avg Score</div>
          <div className="text-3xl font-bold text-emerald-400">{avgScore}</div>
        </div>
        <div className="glass-card p-6 rounded-xl border border-slate-700">
          <div className="text-[var(--text-muted)] text-sm mb-2">Score Range</div>
          <div className="text-2xl font-bold text-[var(--text-primary)]">{scoreRange.min} — {scoreRange.max}</div>
        </div>
      </div>

      {/* Tier Distribution */}
      <div className="glass-card p-6 rounded-xl border border-slate-700">
        <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">Tier Distribution</h3>
        <div className="flex items-center gap-2 mb-4">
          {(['AI-Ready', 'AI-Buildable', 'AI-Emerging', 'AI-Limited'] as const).map(tier => {
            const count = tierCounts[tier]
            const pct = ((count / companies.length) * 100).toFixed(1)
            return (
              <div key={tier} className="relative flex-1 h-12 rounded-lg overflow-hidden" style={{ backgroundColor: `${TIER_COLORS[tier]}20`, border: `1px solid ${TIER_COLORS[tier]}` }}>
                <div className="h-full" style={{ width: `${(count / companies.length) * 100}%`, backgroundColor: TIER_COLORS[tier] }} />
                <div className="absolute inset-0 flex items-center justify-center text-xs font-semibold text-white pointer-events-none">
                  <span className="drop-shadow-lg">{count} ({pct}%)</span>
                </div>
              </div>
            )
          })}
        </div>
        <div className="flex gap-4 text-sm text-[var(--text-muted)]">
          {(['AI-Ready', 'AI-Buildable', 'AI-Emerging', 'AI-Limited'] as const).map(tier => (
            <div key={tier} className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full" style={{ backgroundColor: TIER_COLORS[tier] }} />
              <span>{tier}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Filters */}
      <div className="glass-card p-6 rounded-xl border border-slate-700 space-y-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
          <input
            type="text"
            placeholder="Search by company name or vertical..."
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 rounded-lg pl-10 pr-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
          />
        </div>
        <div className="flex flex-wrap gap-2">
          <button onClick={() => setSelectedTier(null)} className={`px-4 py-2 rounded-lg font-medium text-sm transition-all ${!selectedTier ? 'bg-emerald-500 text-white' : 'bg-slate-800 text-slate-400 hover:bg-slate-700'}`}>
            All ({companies.length})
          </button>
          {(['AI-Ready', 'AI-Buildable', 'AI-Emerging', 'AI-Limited'] as const).map(tier => (
            <button
              key={tier}
              onClick={() => setSelectedTier(tier)}
              className={`px-4 py-2 rounded-lg font-medium text-sm transition-all ${selectedTier === tier ? 'text-white' : 'bg-slate-800 text-slate-400 hover:bg-slate-700'}`}
              style={selectedTier === tier ? { backgroundColor: TIER_COLORS[tier] } : {}}
            >
              {tier} ({tierCounts[tier]})
            </button>
          ))}
        </div>
        <div className="relative w-64">
          <select value={sortOption} onChange={e => setSortOption(e.target.value)} className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-emerald-500 appearance-none pr-10 text-sm">
            <option value="score-desc">Score (High → Low)</option>
            <option value="score-asc">Score (Low → High)</option>
            <option value="name-asc">Name (A-Z)</option>
            <option value="employees">Employees</option>
            <option value="founded">Founded</option>
          </select>
          <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500 pointer-events-none" />
        </div>
      </div>

      {/* Table */}
      <div className="glass-card rounded-xl border border-slate-700 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-slate-800/50 border-b border-slate-700">
                {['#', 'Company', 'Vertical', 'Founded', 'Employees', 'Funding', 'Cloud', 'AI', 'Score', 'Tier'].map(h => (
                  <th key={h} className={`px-4 py-3 text-sm font-semibold text-[var(--text-secondary)] ${h === 'Score' ? 'text-left w-40' : h === '#' ? 'w-12 text-left' : 'text-left'}`}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {visible.map((c, i) => (
                <tr key={c.name} className={`border-b border-slate-700/50 hover:bg-slate-800/30 transition-colors ${i % 2 === 0 ? 'bg-slate-900/20' : ''}`}>
                  <td className="px-4 py-3 text-sm text-[var(--text-muted)]">{i + 1}</td>
                  <td className="px-4 py-3 text-sm text-white font-medium">{c.name}</td>
                  <td className="px-4 py-3 text-sm text-[var(--text-secondary)]">{c.vertical}</td>
                  <td className="px-4 py-3 text-sm text-[var(--text-muted)]">{c.founded_year || 'N/A'}</td>
                  <td className="px-4 py-3 text-sm text-[var(--text-muted)]">{c.employee_count?.toLocaleString() || 'N/A'}</td>
                  <td className="px-4 py-3 text-sm text-[var(--text-muted)]">{fmtFunding(c.funding_total_usd)}</td>
                  <td className="px-4 py-3 text-center"><div className={`w-3 h-3 rounded-full mx-auto ${c.cloud_native ? 'bg-emerald-500' : 'bg-red-500'}`} /></td>
                  <td className="px-4 py-3 text-center"><div className={`w-3 h-3 rounded-full mx-auto ${c.has_ai_features ? 'bg-emerald-500' : 'bg-red-500'}`} /></td>
                  <td className="px-4 py-3 text-sm">
                    <div className="flex items-center gap-2">
                      <div className="flex-1 bg-slate-700 rounded-full h-5 overflow-hidden">
                        <div className="h-full" style={{ width: `${(c.composite_score / 4.5) * 100}%`, backgroundColor: getScoreColor(c.composite_score) }} />
                      </div>
                      <span className="text-white font-semibold w-12 text-right">{c.composite_score.toFixed(2)}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span className="px-3 py-1 rounded-full text-white font-semibold text-xs" style={{ backgroundColor: TIER_COLORS[c.tier] }}>{c.tier}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="px-6 py-4 border-t border-slate-700 bg-slate-800/30 flex items-center justify-between">
          <div className="text-sm text-[var(--text-muted)]">Showing {visible.length} of {filteredAndSorted.length}</div>
          {hasMore && (
            <button onClick={() => setDisplayedRows(p => p + 50)} className="px-4 py-2 bg-emerald-500 hover:bg-emerald-600 text-white font-semibold rounded-lg transition-colors text-sm">
              Load More
            </button>
          )}
        </div>
      </div>

      {/* Histogram */}
      <div className="glass-card p-6 rounded-xl border border-slate-700">
        <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">Score Distribution</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={scoreDistribution}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="range" tick={{ fill: '#cbd5e1', fontSize: 12 }} stroke="#475569" />
            <YAxis tick={{ fill: '#cbd5e1', fontSize: 12 }} stroke="#475569" />
            <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569', borderRadius: '8px', color: '#fff' }} cursor={{ fill: 'rgba(255,255,255,0.1)' }} />
            <Bar dataKey="count" radius={[8, 8, 0, 0]}>
              {scoreDistribution.map((entry, i) => <Cell key={i} fill={entry.color} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
