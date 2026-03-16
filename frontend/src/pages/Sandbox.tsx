import { useState, useEffect, useRef } from 'react'
import {
  Search, Loader2, Trash2, ChevronDown, ChevronUp, Zap, Building2,
  Users, DollarSign, Globe, Cloud, Cpu, Shield, TrendingUp,
  Sparkles, Target, AlertTriangle
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
  confidence_score?: number
  confidence_breakdown?: {
    search_coverage: number
    scrape_depth: number
    corpus_volume: number
    structured_extraction: number
    signal_richness: number
  }
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

// ── Animated counter hook ───────────────────────────────────────────────────

function useAnimatedScore(target: number, duration = 1200) {
  const [current, setCurrent] = useState(0)
  const startTime = useRef<number>(0)
  const rafId = useRef<number>(0)

  useEffect(() => {
    if (target === 0) { setCurrent(0); return }
    startTime.current = performance.now()

    const animate = (now: number) => {
      const elapsed = now - startTime.current
      const progress = Math.min(elapsed / duration, 1)
      // Ease-out cubic
      const eased = 1 - Math.pow(1 - progress, 3)
      setCurrent(eased * target)
      if (progress < 1) {
        rafId.current = requestAnimationFrame(animate)
      }
    }
    rafId.current = requestAnimationFrame(animate)
    return () => cancelAnimationFrame(rafId.current)
  }, [target, duration])

  return current
}

// ── Deep research pipeline steps ────────────────────────────────────────────

const PIPELINE_STEPS = [
  { label: 'Launching deep research across 8 dimensions...', icon: '🔍', duration: 2000 },
  { label: 'Analyzing AI capabilities & engineering signals...', icon: '🤖', duration: 2500 },
  { label: 'Scraping company pages for richer data...', icon: '🌐', duration: 3000 },
  { label: 'Extracting features from research corpus...', icon: '⚡', duration: 2000 },
  { label: 'Running 17-dimension scoring model...', icon: '📊', duration: 2000 },
  { label: 'Computing tier & wave classification...', icon: '🏆', duration: 1500 },
]

// ── Helper: top strengths and weaknesses ────────────────────────────────────

function getInsights(details: SandboxResult['dimension_details']) {
  const sorted = [...details].sort((a, b) => b.score - a.score)
  return {
    strengths: sorted.slice(0, 3),
    weaknesses: sorted.slice(-3).reverse(),
  }
}

// ── Helper: format funding ──────────────────────────────────────────────────

function formatFunding(usd: number): string {
  if (usd >= 1e9) return `$${(usd / 1e9).toFixed(1)}B`
  if (usd >= 1e6) return `$${(usd / 1e6).toFixed(0)}M`
  return `$${usd.toLocaleString()}`
}

export default function Sandbox() {
  const [companyName, setCompanyName] = useState('')
  const [scoring, setScoring] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<SandboxResult | null>(null)
  const [history, setHistory] = useState<SandboxCompany[]>([])
  const [historyLoaded, setHistoryLoaded] = useState(false)
  const [expandedResult, setExpandedResult] = useState(true)
  const [pipelineIdx, setPipelineIdx] = useState(-1)
  const [showResult, setShowResult] = useState(false)

  const animatedScore = useAnimatedScore(showResult && result ? result.composite_score : 0, 1400)

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
    setShowResult(false)
    setPipelineIdx(0)

    // Advance pipeline steps on timers
    let stepIdx = 0
    const advanceStep = () => {
      stepIdx++
      if (stepIdx < PIPELINE_STEPS.length) {
        setPipelineIdx(stepIdx)
      }
    }
    const timers: ReturnType<typeof setTimeout>[] = []
    let cumulative = 0
    for (let i = 1; i < PIPELINE_STEPS.length; i++) {
      cumulative += PIPELINE_STEPS[i - 1].duration
      timers.push(setTimeout(advanceStep, cumulative))
    }

    try {
      const resp = await fetch(`${API}/api/sandbox/score`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ company_name: companyName.trim() }),
      })

      timers.forEach(clearTimeout)

      if (!resp.ok) {
        const err = await resp.json()
        throw new Error(err.detail || 'Scoring failed')
      }

      const data: SandboxResult = await resp.json()
      setResult(data)
      setCompanyName('')

      // Brief pause then reveal with animation
      setTimeout(() => setShowResult(true), 300)
      loadHistory()
    } catch (e: any) {
      setError(e.message || 'Failed to score company')
    } finally {
      setScoring(false)
      setPipelineIdx(-1)
    }
  }

  const deleteCompany = async (id: string) => {
    try {
      await fetch(`${API}/api/sandbox/companies/${id}`, { method: 'DELETE' })
      setHistory(h => h.filter(c => c.id !== id))
      if (result?.id === id) { setResult(null); setShowResult(false) }
    } catch { /* ignore */ }
  }

  // Load history on mount
  if (!historyLoaded) loadHistory()

  // Radar chart data
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

  const insights = result ? getInsights(result.dimension_details) : null

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
          Deep research any company — 8 dimension-specific queries, page scraping, and full 17-dimension AI maturity scoring
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
                Researching...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                Score Company
              </>
            )}
          </button>
        </div>

        {/* Pipeline progress — enhanced for deep research */}
        {scoring && pipelineIdx >= 0 && (
          <div className="mt-5">
            <div className="flex gap-1.5 mb-3">
              {PIPELINE_STEPS.map((_, i) => (
                <div
                  key={i}
                  className="h-1.5 flex-1 rounded-full transition-all duration-700"
                  style={{
                    background: i <= pipelineIdx
                      ? 'var(--teal)'
                      : 'rgba(255,255,255,0.08)',
                    boxShadow: i === pipelineIdx ? '0 0 8px rgba(2,195,154,0.4)' : 'none',
                  }}
                />
              ))}
            </div>
            <div className="flex items-center gap-2">
              <span className="text-base">{PIPELINE_STEPS[pipelineIdx]?.icon}</span>
              <span className="text-xs text-[var(--teal)] font-medium">{PIPELINE_STEPS[pipelineIdx]?.label}</span>
              <span className="text-[10px] text-[var(--text-muted)] ml-auto">Step {pipelineIdx + 1}/{PIPELINE_STEPS.length}</span>
            </div>
          </div>
        )}

        {error && (
          <div className="mt-4 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 flex-shrink-0" />
            {error}
          </div>
        )}
      </div>

      {/* Result card */}
      {result && showResult && (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-700">
          {/* Score hero — with animated counter */}
          <div className="card-dark p-6 relative overflow-hidden">
            {/* Subtle gradient glow behind score */}
            <div className="absolute -top-20 -right-20 w-64 h-64 rounded-full opacity-[0.07]"
                 style={{ background: `radial-gradient(circle, ${TIER_COLORS[result.tier]}, transparent)` }} />

            <div className="flex items-start justify-between mb-6 relative">
              <div className="flex items-center gap-5">
                {/* Animated score circle */}
                <div className="relative">
                  <svg width="80" height="80" viewBox="0 0 80 80">
                    <circle cx="40" cy="40" r="35" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="4" />
                    <circle
                      cx="40" cy="40" r="35"
                      fill="none"
                      stroke={TIER_COLORS[result.tier]}
                      strokeWidth="4"
                      strokeLinecap="round"
                      strokeDasharray={`${(animatedScore / 5) * 220} 220`}
                      transform="rotate(-90 40 40)"
                      style={{ transition: 'stroke-dasharray 0.1s ease-out' }}
                    />
                  </svg>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-2xl font-bold" style={{ color: TIER_COLORS[result.tier] }}>
                      {animatedScore.toFixed(1)}
                    </span>
                  </div>
                </div>
                <div>
                  <h2 className="text-xl font-bold text-white">{result.name}</h2>
                  <div className="flex items-center gap-2 mt-1.5">
                    <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${getTierBg(result.tier)}`}>
                      {result.tier}
                    </span>
                    <span className="text-xs text-[var(--text-muted)]">{result.vertical}</span>
                    <span className="text-xs text-[var(--text-muted)]">·</span>
                    <span className="text-xs font-medium" style={{ color: 'var(--teal)' }}>Wave {result.wave}</span>
                    {result.confidence_score != null && (
                      <>
                        <span className="text-xs text-[var(--text-muted)]">·</span>
                        <span className="text-xs font-medium" style={{
                          color: result.confidence_score >= 75 ? '#10b981'
                               : result.confidence_score >= 50 ? '#f59e0b'
                               : '#ef4444'
                        }}>
                          {result.confidence_score}% confidence
                        </span>
                      </>
                    )}
                  </div>
                </div>
              </div>
              <button
                onClick={() => setExpandedResult(!expandedResult)}
                className="p-2 rounded-lg text-[var(--text-muted)] hover:text-white hover:bg-white/5 transition-all"
              >
                {expandedResult ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
              </button>
            </div>

            {/* Extracted features chips */}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-2.5 mb-6">
              {result.employee_count && (
                <div className="flex items-center gap-2 px-3 py-2.5 rounded-lg bg-white/[0.03] border border-white/[0.06]">
                  <Users className="w-3.5 h-3.5 text-cyan-400" />
                  <span className="text-xs text-[var(--text-secondary)]">{result.employee_count.toLocaleString()} employees</span>
                </div>
              )}
              {result.funding_total_usd && (
                <div className="flex items-center gap-2 px-3 py-2.5 rounded-lg bg-white/[0.03] border border-white/[0.06]">
                  <DollarSign className="w-3.5 h-3.5 text-green-400" />
                  <span className="text-xs text-[var(--text-secondary)]">{formatFunding(result.funding_total_usd)} funding</span>
                </div>
              )}
              {result.website && (
                <div className="flex items-center gap-2 px-3 py-2.5 rounded-lg bg-white/[0.03] border border-white/[0.06]">
                  <Globe className="w-3.5 h-3.5 text-blue-400" />
                  <a href={result.website} target="_blank" rel="noopener" className="text-xs text-[var(--teal)] truncate">
                    {result.website.replace('https://', '').replace('http://', '')}
                  </a>
                </div>
              )}
              {result.has_ai_features && (
                <div className="flex items-center gap-2 px-3 py-2.5 rounded-lg bg-purple-500/10 border border-purple-500/20">
                  <Cpu className="w-3.5 h-3.5 text-purple-400" />
                  <span className="text-xs text-purple-400 font-medium">AI Features</span>
                </div>
              )}
              {result.cloud_native && (
                <div className="flex items-center gap-2 px-3 py-2.5 rounded-lg bg-blue-500/10 border border-blue-500/20">
                  <Cloud className="w-3.5 h-3.5 text-blue-400" />
                  <span className="text-xs text-blue-400 font-medium">Cloud Native</span>
                </div>
              )}
              {result.is_public && (
                <div className="flex items-center gap-2 px-3 py-2.5 rounded-lg bg-amber-500/10 border border-amber-500/20">
                  <Shield className="w-3.5 h-3.5 text-amber-400" />
                  <span className="text-xs text-amber-400 font-medium">Public Company</span>
                </div>
              )}
            </div>

            {/* Category scores — horizontal bars */}
            <div className="grid grid-cols-6 gap-2">
              {categoryData.map(({ category, score, color }) => (
                <div key={category} className="text-center">
                  <div className="text-[10px] text-[var(--text-muted)] mb-1 truncate" title={category}>
                    {category.split(' ')[0]}
                  </div>
                  <div className="h-2 rounded-full bg-white/[0.06] overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-1000 ease-out"
                      style={{ width: `${(score / 5) * 100}%`, background: color }}
                    />
                  </div>
                  <div className="text-[10px] font-semibold mt-0.5" style={{ color }}>{score.toFixed(1)}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Strengths & Weaknesses — NEW */}
          {expandedResult && insights && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="card-dark p-5">
                <h3 className="text-xs font-semibold text-emerald-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                  <TrendingUp className="w-3.5 h-3.5" />
                  Top Strengths
                </h3>
                <div className="space-y-2.5">
                  {insights.strengths.map((d, i) => (
                    <div key={d.dimension} className="flex items-center gap-3">
                      <div className="w-5 h-5 rounded-md flex items-center justify-center text-[10px] font-bold bg-emerald-500/15 text-emerald-400">
                        {i + 1}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <span className="text-xs text-[var(--text-secondary)] truncate">{d.label}</span>
                          <span className="text-xs font-bold text-emerald-400 ml-2">{d.score.toFixed(1)}</span>
                        </div>
                        <div className="h-1 rounded-full bg-white/[0.06] mt-1 overflow-hidden">
                          <div className="h-full rounded-full bg-emerald-400/60 transition-all duration-1000"
                               style={{ width: `${(d.score / 5) * 100}%` }} />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              <div className="card-dark p-5">
                <h3 className="text-xs font-semibold text-orange-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                  <Target className="w-3.5 h-3.5" />
                  Key Development Areas
                </h3>
                <div className="space-y-2.5">
                  {insights.weaknesses.map((d, i) => (
                    <div key={d.dimension} className="flex items-center gap-3">
                      <div className="w-5 h-5 rounded-md flex items-center justify-center text-[10px] font-bold bg-orange-500/15 text-orange-400">
                        {i + 1}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <span className="text-xs text-[var(--text-secondary)] truncate">{d.label}</span>
                          <span className="text-xs font-bold text-orange-400 ml-2">{d.score.toFixed(1)}</span>
                        </div>
                        <div className="h-1 rounded-full bg-white/[0.06] mt-1 overflow-hidden">
                          <div className="h-full rounded-full bg-orange-400/60 transition-all duration-1000"
                               style={{ width: `${(d.score / 5) * 100}%` }} />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Charts */}
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

          {/* Investment thesis — NEW */}
          {expandedResult && insights && (
            <div className="card-dark p-6">
              <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3 flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-[var(--teal)]" />
                Quick Assessment
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.06]">
                  <div className="text-[10px] uppercase tracking-wider text-[var(--text-muted)] mb-1.5">Wave Placement</div>
                  <div className="text-lg font-bold" style={{ color: 'var(--teal)' }}>Wave {result.wave}</div>
                  <div className="text-xs text-[var(--text-secondary)] mt-1">
                    {result.wave === 1 ? 'Priority investment — ready for immediate AI acceleration'
                     : result.wave === 2 ? 'Near-term opportunity — build foundations first'
                     : 'Long-term play — significant enablement needed'}
                  </div>
                </div>
                <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.06]">
                  <div className="text-[10px] uppercase tracking-wider text-[var(--text-muted)] mb-1.5">Strongest Category</div>
                  <div className="text-lg font-bold" style={{ color: categoryData[0]?.color }}>
                    {categoryData[0]?.category?.split('&')[0]?.trim()}
                  </div>
                  <div className="text-xs text-[var(--text-secondary)] mt-1">
                    Scoring {categoryData[0]?.score.toFixed(1)}/5.0 — {categoryData[0]?.score >= 4 ? 'exceptional' : categoryData[0]?.score >= 3 ? 'strong' : 'developing'}
                  </div>
                </div>
                <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.06]">
                  <div className="text-[10px] uppercase tracking-wider text-[var(--text-muted)] mb-1.5">Priority Focus</div>
                  <div className="text-lg font-bold text-orange-400">
                    {insights.weaknesses[0]?.label}
                  </div>
                  <div className="text-xs text-[var(--text-secondary)] mt-1">
                    At {insights.weaknesses[0]?.score.toFixed(1)}/5.0 — biggest opportunity for improvement
                  </div>
                </div>
                {result.confidence_score != null && (
                  <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.06]">
                    <div className="text-[10px] uppercase tracking-wider text-[var(--text-muted)] mb-1.5">Research Confidence</div>
                    <div className="text-lg font-bold" style={{
                      color: result.confidence_score >= 75 ? '#10b981'
                           : result.confidence_score >= 50 ? '#f59e0b'
                           : '#ef4444'
                    }}>
                      {result.confidence_score}%
                    </div>
                    {result.confidence_breakdown && (
                      <div className="mt-2 space-y-1">
                        {[
                          { key: 'search_coverage', label: 'Search', max: 25 },
                          { key: 'scrape_depth', label: 'Scrape', max: 20 },
                          { key: 'corpus_volume', label: 'Corpus', max: 15 },
                          { key: 'structured_extraction', label: 'Facts', max: 25 },
                          { key: 'signal_richness', label: 'Signals', max: 15 },
                        ].map(({ key, label, max }) => {
                          const val = (result.confidence_breakdown as Record<string, number>)?.[key] ?? 0
                          return (
                            <div key={key} className="flex items-center gap-1.5">
                              <span className="text-[9px] text-[var(--text-muted)] w-10">{label}</span>
                              <div className="flex-1 h-1 rounded-full bg-white/[0.06] overflow-hidden">
                                <div
                                  className="h-full rounded-full transition-all duration-700"
                                  style={{
                                    width: `${(val / max) * 100}%`,
                                    background: val / max >= 0.7 ? '#10b981' : val / max >= 0.4 ? '#f59e0b' : '#ef4444',
                                  }}
                                />
                              </div>
                              <span className="text-[9px] text-[var(--text-muted)] w-7 text-right">{val}/{max}</span>
                            </div>
                          )
                        })}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Research context — cleaned up */}
          {expandedResult && result.research_summary && (
            <div className="card-dark p-6">
              <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3 flex items-center gap-2">
                <Search className="w-4 h-4 text-[var(--text-muted)]" />
                Research Context
              </h3>
              <div className="text-xs text-[var(--text-secondary)] leading-relaxed space-y-3">
                {result.research_summary.split('\n\n').filter(Boolean).map((para, i) => (
                  <p key={i} className="pl-3 border-l-2 border-white/[0.06]">{para}</p>
                ))}
              </div>
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
                      <span className="text-[10px] text-[var(--text-muted)]">·</span>
                      <span className="text-[10px] text-[var(--text-muted)]">Wave {company.wave}</span>
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
            Enter a company name above and our deep research pipeline will analyze it across 8 dimensions,
            scrape key pages, and generate a full 17-dimension maturity assessment.
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
