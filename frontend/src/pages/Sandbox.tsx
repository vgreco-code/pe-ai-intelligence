import { useState } from 'react'
import {
  Search, Loader2, Trash2, ChevronDown, ChevronUp, Zap, Building2,
  Users, DollarSign, Globe, Cloud, Cpu, Shield
} from 'lucide-react'
import {
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LabelList, Cell
} from 'recharts'
import { TIER_COLORS, CATEGORY_COLORS, DIMENSION_LABELS, getTierBg, getScoreColor } from '../App'

interface SandboxResult {
  id: string
  name: string
  vertical: string
  website?: string
  description?: string
  employee_count?: number
  funding_total_usd?: number
  is_public: boolean
  has_ai_features: boolean
  cloud_native: boolean
  composite_score: number
  tier: string
  wave: number
  pillar_scores: Record<string, number>
  category_scores: Record<string, number>
  dimension_details: {
    dimension: string
    label: string
    score: number
    category: string
    weight: number
  }[]
  research_summary: string
}

interface SandboxCompany {
  id: string
  name: string
  vertical: string
  composite_score: number
  tier: string
  wave: number
  pillar_scores: Record<string, number>
  category_scores: Record<string, number>
  created_at: string
}

const API = import.meta.env.VITE_API_URL || ''

export default function Sandbox() {
  const [companyName, setCompanyName] = useState('')
  const [scoring, setScoring] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<SandboxResult | null>(null)
  const [history, setHistory] = useState<SandboxCompany[]>([])
  const [historyLoaded, setHistoryLoaded] = useState(false)
  const [expandedResult, setExpandedResult] = useState(true)
  const [pipelineStep, setPipelineStep] = useState('')

  const loadHistory = async () => {
    try {
      const resp = await fetch(`${API}/api/sandbox/companies`)
      if (resp.ok) {
        const data = await resp.json()
        setHistory(data)
        setHistoryLoaded(true)
      }
    } catch { /* ignore */ }
  }

  const scoreCompany = async () => {
    if (!companyName.trim()) return
    setScoring(true)
    setError(null)
    setResult(null)

    // Simulate pipeline steps for UX
    const steps = [
      'Searching web for company data...',
      'Extracting features & signals...',
      'Running 17-dimension scoring model...',
      'Computing tier classification...',
    ]
    let stepIdx = 0
    setPipelineStep(steps[0])
    const interval = setInterval(() => {
      stepIdx++
      if (stepIdx < steps.length) {
        setPipelineStep(steps[stepIdx])
      }
    }, 2500)

    try {
      const resp = await fetch(`${API}/api/sandbox/score`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ company_name: companyName.trim() }),
      })

      clearInterval(interval)

      if (!resp.ok) {
        const err = await resp.json()
        throw new Error(err.detail || 'Scoring failed')
      }

      const data: SandboxResult = await resp.json()
      setResult(data)
      setCompanyName('')
      loadHistory()
    } catch (e: any) {
      setError(e.message || 'Failed to score company')
    } finally {
      setScoring(false)
      setPipelineStep('')
    }
  }

  const deleteCompany = async (id: string) => {
    try {
      await fetch(`${API}/api/sandbox/companies/${id}`, { method: 'DELETE' })
      setHistory(h => h.filter(c => c.id !== id))
      if (result?.id === id) setResult(null)
    } catch { /* ignore */ }
  }

  // Load history on mount
  if (!historyLoaded) loadHistory()

  // Radar chart data for scored result
  const radarData = result
    ? Object.entries(result.pillar_scores).map(([dim, score]) => ({
        dimension: DIMENSION_LABELS[dim] || dim,
        score,
        fullMark: 5,
      }))
    : []

  // Category bar data
  const categoryData = result
    ? Object.entries(result.category_scores)
        .sort(([, a], [, b]) => b - a)
        .map(([cat, score]) => ({ category: cat, score, color: CATEGORY_COLORS[cat] || '#666' }))
    : []

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-[var(--text-primary)] flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #A259FF, #1ABCFE)' }}>
            <Zap className="w-5 h-5 text-white" />
          </div>
          AI Scoring Sandbox
        </h1>
        <p className="text-[var(--text-secondary)] mt-1 text-sm">
          Enter any company name — we'll research it and run it through the full 17-dimension AI maturity pipeline
        </p>
      </div>

      {/* Input area */}
      <div className="card-dark p-6">
        <div className="flex gap-3">
          <div className="flex-1 relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[var(--text-muted)]" />
            <input
              type="text"
              value={companyName}
              onChange={e => setCompanyName(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && !scoring && scoreCompany()}
              placeholder="Enter a company name (e.g., Stripe, Datadog, Palantir)..."
              disabled={scoring}
              className="w-full pl-12 pr-4 py-3.5 rounded-xl text-sm text-white placeholder-[var(--text-muted)]
                         bg-white/[0.05] border border-white/[0.1] focus:border-[var(--teal)] focus:outline-none
                         focus:ring-2 focus:ring-[var(--teal)]/20 transition-all disabled:opacity-50"
            />
          </div>
          <button
            onClick={scoreCompany}
            disabled={scoring || !companyName.trim()}
            className="px-6 py-3.5 rounded-xl font-semibold text-sm transition-all flex items-center gap-2
                       disabled:opacity-40 disabled:cursor-not-allowed"
            style={{
              background: scoring ? 'rgba(2,195,154,0.2)' : 'var(--teal)',
              color: scoring ? 'var(--teal)' : 'var(--navy)',
            }}
          >
            {scoring ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Scoring...
              </>
            ) : (
              <>
                <Zap className="w-4 h-4" />
                Score Company
              </>
            )}
          </button>
        </div>

        {/* Pipeline progress */}
        {scoring && pipelineStep && (
          <div className="mt-4 flex items-center gap-3">
            <div className="flex gap-1">
              {[0, 1, 2, 3].map(i => (
                <div
                  key={i}
                  className="h-1 w-8 rounded-full transition-all duration-500"
                  style={{
                    background: i <= ['Searching', 'Extracting', 'Running', 'Computing'].findIndex(s => pipelineStep.startsWith(s))
                      ? 'var(--teal)' : 'rgba(255,255,255,0.1)',
                  }}
                />
              ))}
            </div>
            <span className="text-xs text-[var(--teal)] font-medium animate-pulse">{pipelineStep}</span>
          </div>
        )}

        {error && (
          <div className="mt-4 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
            {error}
          </div>
        )}
      </div>

      {/* Result card */}
      {result && (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
          {/* Score hero */}
          <div className="card-dark p-6">
            <div className="flex items-start justify-between mb-6">
              <div className="flex items-center gap-4">
                <div
                  className="w-16 h-16 rounded-2xl flex items-center justify-center text-2xl font-bold"
                  style={{
                    background: `${TIER_COLORS[result.tier]}15`,
                    color: TIER_COLORS[result.tier],
                    border: `2px solid ${TIER_COLORS[result.tier]}30`,
                  }}
                >
                  {result.composite_score.toFixed(1)}
                </div>
                <div>
                  <h2 className="text-xl font-bold text-white">{result.name}</h2>
                  <div className="flex items-center gap-2 mt-1">
                    <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${getTierBg(result.tier)}`}>
                      {result.tier}
                    </span>
                    <span className="text-xs text-[var(--text-muted)]">{result.vertical}</span>
                    <span className="text-xs text-[var(--text-muted)]">·</span>
                    <span className="text-xs text-[var(--text-muted)]">Wave {result.wave}</span>
                  </div>
                </div>
              </div>
              <button
                onClick={() => setExpandedResult(!expandedResult)}
                className="p-2 rounded-lg text-[var(--text-muted)] hover:text-white hover:bg-white/5"
              >
                {expandedResult ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
              </button>
            </div>

            {/* Extracted features summary */}
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3 mb-6">
              {result.employee_count && (
                <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/[0.03] border border-white/[0.06]">
                  <Users className="w-3.5 h-3.5 text-[var(--text-muted)]" />
                  <span className="text-xs text-[var(--text-secondary)]">{result.employee_count.toLocaleString()} employees</span>
                </div>
              )}
              {result.funding_total_usd && (
                <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/[0.03] border border-white/[0.06]">
                  <DollarSign className="w-3.5 h-3.5 text-[var(--text-muted)]" />
                  <span className="text-xs text-[var(--text-secondary)]">
                    ${result.funding_total_usd >= 1e9
                      ? `${(result.funding_total_usd / 1e9).toFixed(1)}B`
                      : `${(result.funding_total_usd / 1e6).toFixed(0)}M`}
                  </span>
                </div>
              )}
              {result.website && (
                <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/[0.03] border border-white/[0.06]">
                  <Globe className="w-3.5 h-3.5 text-[var(--text-muted)]" />
                  <a href={result.website} target="_blank" rel="noopener" className="text-xs text-[var(--teal)] truncate">{result.website.replace('https://', '')}</a>
                </div>
              )}
              {result.has_ai_features && (
                <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-purple-500/10 border border-purple-500/20">
                  <Cpu className="w-3.5 h-3.5 text-purple-400" />
                  <span className="text-xs text-purple-400 font-medium">AI Features</span>
                </div>
              )}
              {result.cloud_native && (
                <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-blue-500/10 border border-blue-500/20">
                  <Cloud className="w-3.5 h-3.5 text-blue-400" />
                  <span className="text-xs text-blue-400 font-medium">Cloud Native</span>
                </div>
              )}
              {result.is_public && (
                <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-amber-500/10 border border-amber-500/20">
                  <Shield className="w-3.5 h-3.5 text-amber-400" />
                  <span className="text-xs text-amber-400 font-medium">Public Company</span>
                </div>
              )}
            </div>

            {/* Category scores bar */}
            <div className="grid grid-cols-6 gap-2 mb-2">
              {categoryData.map(({ category, score, color }) => (
                <div key={category} className="text-center">
                  <div className="text-[10px] text-[var(--text-muted)] mb-1 truncate" title={category}>
                    {category.split(' ')[0]}
                  </div>
                  <div className="h-2 rounded-full bg-white/[0.06] overflow-hidden">
                    <div className="h-full rounded-full transition-all duration-1000" style={{ width: `${(score / 5) * 100}%`, background: color }} />
                  </div>
                  <div className="text-[10px] font-semibold mt-0.5" style={{ color }}>{score.toFixed(1)}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Expanded charts */}
          {expandedResult && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Radar */}
              <div className="card-dark p-6">
                <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-4">17-Dimension Profile</h3>
                <ResponsiveContainer width="100%" height={350}>
                  <RadarChart data={radarData} cx="50%" cy="50%" outerRadius="70%">
                    <PolarGrid stroke="rgba(255,255,255,0.08)" />
                    <PolarAngleAxis
                      dataKey="dimension"
                      tick={{ fill: 'rgba(148,163,184,0.7)', fontSize: 8 }}
                    />
                    <PolarRadiusAxis angle={90} domain={[0, 5]} tick={false} axisLine={false} />
                    <Radar
                      dataKey="score"
                      stroke={TIER_COLORS[result.tier]}
                      fill={TIER_COLORS[result.tier]}
                      fillOpacity={0.15}
                      strokeWidth={2}
                    />
                  </RadarChart>
                </ResponsiveContainer>
              </div>

              {/* Dimension bar chart */}
              <div className="card-dark p-6">
                <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-4">Dimension Scores</h3>
                <ResponsiveContainer width="100%" height={350}>
                  <BarChart
                    data={result.dimension_details}
                    layout="vertical"
                    margin={{ left: 110, right: 40, top: 5, bottom: 5 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" horizontal={false} />
                    <XAxis type="number" domain={[0, 5]} tick={{ fill: 'rgba(148,163,184,0.5)', fontSize: 10 }} />
                    <YAxis
                      type="category"
                      dataKey="label"
                      tick={{ fill: 'rgba(148,163,184,0.7)', fontSize: 10 }}
                      width={105}
                    />
                    <Tooltip
                      contentStyle={{ background: '#1a2744', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8 }}
                      labelStyle={{ color: 'white', fontWeight: 600 }}
                      itemStyle={{ color: 'rgba(148,163,184,0.9)' }}
                      formatter={(v: number) => [v.toFixed(2) + ' / 5.0', 'Score']}
                    />
                    <Bar dataKey="score" radius={[0, 4, 4, 0]} barSize={14}>
                      {result.dimension_details.map((entry, i) => (
                        <Cell key={i} fill={getScoreColor(entry.score)} fillOpacity={0.8} />
                      ))}
                      <LabelList
                        dataKey="score"
                        position="right"
                        formatter={(v: number) => v.toFixed(1)}
                        style={{ fill: 'rgba(148,163,184,0.9)', fontSize: 10, fontWeight: 600 }}
                      />
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* Research context */}
          {expandedResult && result.research_summary && (
            <div className="card-dark p-6">
              <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3">Research Context</h3>
              <p className="text-xs text-[var(--text-secondary)] leading-relaxed whitespace-pre-wrap">
                {result.research_summary}
              </p>
            </div>
          )}
        </div>
      )}

      {/* Previously scored companies */}
      {history.length > 0 && (
        <div className="card-dark p-6">
          <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-4 flex items-center gap-2">
            <Building2 className="w-4 h-4 text-[var(--text-muted)]" />
            Previously Scored ({history.length})
          </h3>
          <div className="space-y-2">
            {history.map(company => (
              <div
                key={company.id}
                className="flex items-center justify-between px-4 py-3 rounded-lg bg-white/[0.02] border border-white/[0.06]
                           hover:bg-white/[0.04] transition-all group"
              >
                <div className="flex items-center gap-4">
                  <div
                    className="w-10 h-10 rounded-lg flex items-center justify-center text-sm font-bold"
                    style={{ background: `${TIER_COLORS[company.tier]}15`, color: TIER_COLORS[company.tier] }}
                  >
                    {company.composite_score.toFixed(1)}
                  </div>
                  <div>
                    <div className="text-sm font-semibold text-white">{company.name}</div>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded-full ${getTierBg(company.tier)}`}>
                        {company.tier}
                      </span>
                      <span className="text-[10px] text-[var(--text-muted)]">{company.vertical}</span>
                    </div>
                  </div>
                </div>
                <button
                  onClick={() => deleteCompany(company.id)}
                  className="p-2 rounded-lg text-[var(--text-muted)] hover:text-red-400 hover:bg-red-500/10
                             opacity-0 group-hover:opacity-100 transition-all"
                  title="Remove from sandbox"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty state */}
      {!result && history.length === 0 && !scoring && (
        <div className="card-dark p-12 text-center">
          <div className="w-16 h-16 rounded-2xl mx-auto mb-4 flex items-center justify-center"
               style={{ background: 'linear-gradient(135deg, rgba(162,89,255,0.1), rgba(26,188,254,0.1))' }}>
            <Zap className="w-8 h-8 text-purple-400" />
          </div>
          <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">Score any company</h3>
          <p className="text-sm text-[var(--text-muted)] max-w-md mx-auto">
            Enter a company name above and our pipeline will research it across the web,
            extract AI-readiness signals, and generate a full 17-dimension maturity assessment.
          </p>
          <div className="flex items-center justify-center gap-2 mt-6">
            {['Stripe', 'Datadog', 'Snowflake', 'UiPath'].map(name => (
              <button
                key={name}
                onClick={() => { setCompanyName(name); }}
                className="text-xs px-3 py-1.5 rounded-full bg-white/[0.05] border border-white/[0.1]
                           text-[var(--text-secondary)] hover:text-white hover:border-white/[0.2] transition-all"
              >
                {name}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
