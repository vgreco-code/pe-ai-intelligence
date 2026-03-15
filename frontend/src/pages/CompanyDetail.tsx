import {
  ArrowLeft, ExternalLink, Users, Calendar, MapPin, TrendingUp,
  Zap, Target, AlertTriangle, CheckCircle2, Lightbulb, BarChart3,
} from 'lucide-react'
import {
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, Tooltip, Cell,
} from 'recharts'
import {
  PortfolioCompany, TIER_COLORS, DIMENSION_LABELS,
  CATEGORIES, CATEGORY_COLORS, getScoreColor, getTierBg,
} from '../App'
import type { BenchmarkCompany } from './CompetitiveBenchmarks'

interface Props {
  company: PortfolioCompany
  benchmark?: BenchmarkCompany
  onBack: () => void
}

const TIER_DESCRIPTIONS: Record<string, { headline: string; description: string; icon: typeof CheckCircle2 }> = {
  'AI-Ready': {
    headline: 'Strong AI Foundation',
    description: 'This company has mature data infrastructure, existing AI capabilities, and organizational readiness for immediate AI-driven value creation.',
    icon: CheckCircle2,
  },
  'AI-Buildable': {
    headline: 'High AI Potential',
    description: 'Solid fundamentals with clear pathways to AI integration. Targeted investments in key dimensions can unlock significant value within 6-12 months.',
    icon: TrendingUp,
  },
  'AI-Emerging': {
    headline: 'Developing AI Readiness',
    description: 'Moderate foundation with meaningful gaps to address. A phased 12-18 month roadmap focusing on infrastructure and data quality will build AI capability.',
    icon: Lightbulb,
  },
  'AI-Limited': {
    headline: 'Foundational Work Required',
    description: 'Significant investment in core infrastructure, data practices, and organizational capability needed before AI can deliver reliable value.',
    icon: AlertTriangle,
  },
}

function getStrengths(company: PortfolioCompany): { dim: string; score: number; label: string }[] {
  return Object.entries(company.pillar_scores)
    .map(([dim, score]) => ({ dim, score, label: DIMENSION_LABELS[dim] || dim }))
    .sort((a, b) => b.score - a.score)
    .slice(0, 5)
}

function getWeaknesses(company: PortfolioCompany): { dim: string; score: number; label: string }[] {
  return Object.entries(company.pillar_scores)
    .map(([dim, score]) => ({ dim, score, label: DIMENSION_LABELS[dim] || dim }))
    .sort((a, b) => a.score - b.score)
    .slice(0, 5)
}

function getActionableRecs(company: PortfolioCompany): string[] {
  const recs: string[] = []
  const ps = company.pillar_scores

  if ((ps.data_quality || 0) < 2.5)
    recs.push('Invest in data quality infrastructure — implement data validation, cataloging, and governance tools to create a reliable foundation for AI/ML.')
  if ((ps.ai_engineering || 0) < 2.5)
    recs.push('Build AI/ML engineering capability — hire or upskill engineers with ML ops experience, establish model development and deployment pipelines.')
  if ((ps.cloud_architecture || 0) < 2.5)
    recs.push('Modernize cloud architecture — migrate to cloud-native infrastructure to enable scalable AI workloads and reduce infrastructure friction.')
  if ((ps.ai_product_features || 0) < 3.0)
    recs.push('Identify quick-win AI product features — analyze customer workflows for automation opportunities and predictive capabilities that drive immediate value.')
  if ((ps.data_integration || 0) < 2.5)
    recs.push('Strengthen API and data integration layer — build robust ETL pipelines and API infrastructure to unify data sources for AI training and inference.')
  if ((ps.ai_talent_density || 0) < 2.5)
    recs.push('Develop AI talent strategy — create AI-focused roles, upskilling programs, and partnerships with AI consultancies to build internal capability.')
  if ((ps.leadership_ai_vision || 0) < 2.5)
    recs.push('Align leadership on AI vision — establish an AI steering committee and develop a clear AI strategy linked to business outcomes and ROI targets.')
  if ((ps.ai_momentum || 0) >= 3.0)
    recs.push('Capitalize on AI momentum — the company shows strong signals of AI adoption activity; accelerate investment to maintain competitive advantage.')

  if (company.tier === 'AI-Buildable' || company.tier === 'AI-Ready') {
    recs.push('Prioritize Wave 1 deployment — this company is ready for immediate AI value creation; focus on revenue-generating AI features first.')
  }

  return recs.slice(0, 4)
}

export default function CompanyDetail({ company, benchmark, onBack }: Props) {
  const tierInfo = TIER_DESCRIPTIONS[company.tier] || TIER_DESCRIPTIONS['AI-Limited']
  const TierIcon = tierInfo.icon
  const strengths = getStrengths(company)
  const weaknesses = getWeaknesses(company)
  const recommendations = getActionableRecs(company)

  const radarData = Object.entries(company.pillar_scores).map(([key, value]) => ({
    dimension: DIMENSION_LABELS[key] || key,
    score: value,
    fullMark: 5,
  }))

  const dimensionBarData = Object.entries(CATEGORIES).flatMap(([cat, dims]) =>
    dims.map(d => ({
      name: DIMENSION_LABELS[d] || d,
      score: company.pillar_scores[d] || 0,
      fill: CATEGORY_COLORS[cat] || '#6B7280',
      category: cat,
    }))
  )

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Back button */}
      <button
        onClick={onBack}
        className="flex items-center gap-2 text-[var(--text-muted)] hover:text-teal-400 transition-colors text-sm"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Portfolio
      </button>

      {/* Hero Header */}
      <div className="glass-card rounded-2xl border border-slate-700/50 overflow-hidden">
        <div className="relative p-8">
          {/* Glow backdrop */}
          <div
            className="absolute top-0 right-0 w-96 h-96 rounded-full blur-3xl opacity-10"
            style={{ backgroundColor: TIER_COLORS[company.tier] }}
          />

          <div className="relative flex items-start justify-between">
            <div>
              <div className="flex items-center gap-4 mb-3">
                <h1 className="text-4xl font-bold text-[var(--text-primary)]">{company.name}</h1>
                {company.website && (
                  <a
                    href={company.website.startsWith('http') ? company.website : `https://${company.website}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-[var(--text-muted)] hover:text-teal-400 transition-colors"
                  >
                    <ExternalLink className="w-5 h-5" />
                  </a>
                )}
              </div>

              <div className="flex items-center gap-4 text-sm text-[var(--text-secondary)] mb-4">
                <span className="flex items-center gap-1.5">
                  <MapPin className="w-4 h-4" /> {company.vertical}
                </span>
                <span className="flex items-center gap-1.5">
                  <Users className="w-4 h-4" /> {company.employee_count} employees
                </span>
                {company.founded_year > 0 && (
                  <span className="flex items-center gap-1.5">
                    <Calendar className="w-4 h-4" /> Founded {company.founded_year}
                  </span>
                )}
              </div>

              {company.description && (
                <p className="text-[var(--text-secondary)] max-w-2xl mb-6">{company.description}</p>
              )}

              {/* Tier assessment */}
              <div className="flex items-start gap-3 p-4 rounded-xl" style={{ backgroundColor: `${TIER_COLORS[company.tier]}10`, border: `1px solid ${TIER_COLORS[company.tier]}30` }}>
                <TierIcon className="w-5 h-5 flex-shrink-0 mt-0.5" style={{ color: TIER_COLORS[company.tier] }} />
                <div>
                  <h3 className="font-semibold mb-1" style={{ color: TIER_COLORS[company.tier] }}>
                    {tierInfo.headline}
                  </h3>
                  <p className="text-sm text-[var(--text-secondary)]">{tierInfo.description}</p>
                </div>
              </div>
            </div>

            {/* Score card */}
            <div className="flex-shrink-0 text-center">
              <div
                className="w-32 h-32 rounded-2xl flex flex-col items-center justify-center border"
                style={{
                  backgroundColor: `${TIER_COLORS[company.tier]}15`,
                  borderColor: `${TIER_COLORS[company.tier]}40`,
                }}
              >
                <div className="text-4xl font-bold" style={{ color: TIER_COLORS[company.tier] }}>
                  {company.composite_score.toFixed(2)}
                </div>
                <div className="text-xs font-medium mt-1" style={{ color: TIER_COLORS[company.tier] }}>
                  / 5.00
                </div>
              </div>
              <div className="mt-3 flex justify-center gap-2">
                <span className={`px-3 py-1 rounded-full text-xs font-bold ${getTierBg(company.tier)}`}>
                  {company.tier}
                </span>
                <span className="px-3 py-1 rounded-full text-xs font-bold bg-slate-700/50 text-slate-300">
                  Wave {company.wave}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Two-column: Radar + Categories */}
      <div className="grid grid-cols-2 gap-6">
        {/* Radar Chart */}
        <div className="glass-card rounded-xl border border-slate-700/50 p-6">
          <h2 className="text-lg font-bold text-[var(--text-primary)] mb-4 flex items-center gap-2">
            <Target className="w-5 h-5 text-teal-400" />
            17-Dimension Profile
          </h2>
          <div style={{ height: '350px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart data={radarData}>
                <PolarGrid stroke="rgba(255,255,255,0.08)" />
                <PolarAngleAxis dataKey="dimension" tick={{ fill: '#94a3b8', fontSize: 9 }} />
                <PolarRadiusAxis angle={90} domain={[0, 5]} tick={false} />
                <Radar name="Score" dataKey="score" stroke={TIER_COLORS[company.tier]} fill={TIER_COLORS[company.tier]} fillOpacity={0.2} strokeWidth={2} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* All dimensions bar chart */}
        <div className="glass-card rounded-xl border border-slate-700/50 p-6">
          <h2 className="text-lg font-bold text-[var(--text-primary)] mb-4 flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-teal-400" />
            Dimension Scores
          </h2>
          <div style={{ height: '350px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={dimensionBarData} layout="vertical" margin={{ top: 5, right: 20, left: 120, bottom: 5 }}>
                <XAxis type="number" domain={[0, 5]} stroke="rgba(107,114,128,0.6)" tick={{ fontSize: 10, fill: 'rgba(148,163,184,0.8)' }} />
                <YAxis dataKey="name" type="category" width={115} stroke="rgba(107,114,128,0.6)" tick={{ fontSize: 10, fill: 'rgba(148,163,184,0.8)' }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'rgba(15, 23, 42, 0.95)',
                    border: '1px solid rgba(20, 184, 166, 0.2)',
                    borderRadius: '8px',
                  }}
                  formatter={(v: number) => [v.toFixed(1), 'Score']}
                />
                <Bar dataKey="score" radius={[0, 6, 6, 0]}>
                  {dimensionBarData.map((entry, i) => (
                    <Cell key={i} fill={entry.fill} fillOpacity={0.85} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Category deep-dive */}
      <div className="glass-card rounded-xl border border-slate-700/50 p-6">
        <h2 className="text-lg font-bold text-[var(--text-primary)] mb-6 flex items-center gap-2">
          <Zap className="w-5 h-5 text-teal-400" />
          Category Breakdown
        </h2>
        <div className="grid grid-cols-3 gap-4">
          {Object.entries(CATEGORIES).map(([cat, dims]) => {
            const catAvg = dims.reduce((s, d) => s + (company.pillar_scores[d] || 0), 0) / dims.length
            return (
              <div key={cat} className="bg-slate-800/30 rounded-xl p-4 border border-slate-700/30">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-semibold" style={{ color: CATEGORY_COLORS[cat] }}>{cat}</h3>
                  <span className="text-lg font-bold" style={{ color: getScoreColor(catAvg) }}>{catAvg.toFixed(1)}</span>
                </div>
                <div className="space-y-2">
                  {dims.map(d => (
                    <div key={d}>
                      <div className="flex justify-between mb-1">
                        <span className="text-xs text-[var(--text-secondary)]">{DIMENSION_LABELS[d]}</span>
                        <span className="text-xs font-bold" style={{ color: getScoreColor(company.pillar_scores[d] || 0) }}>
                          {(company.pillar_scores[d] || 0).toFixed(1)}
                        </span>
                      </div>
                      <div className="w-full bg-slate-700/50 rounded-full h-1.5">
                        <div
                          className="h-full rounded-full animate-bar"
                          style={{
                            width: `${((company.pillar_scores[d] || 0) / 5) * 100}%`,
                            backgroundColor: CATEGORY_COLORS[cat],
                          }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Strengths, Weaknesses, and Benchmark */}
      <div className="grid grid-cols-3 gap-6">
        {/* Strengths */}
        <div className="glass-card rounded-xl border border-emerald-500/20 p-6">
          <h2 className="text-lg font-bold text-emerald-400 mb-4 flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5" />
            Key Strengths
          </h2>
          <div className="space-y-3">
            {strengths.map((s, i) => (
              <div key={i} className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-emerald-500/10 flex items-center justify-center text-emerald-400 font-bold text-sm">
                  {s.score.toFixed(1)}
                </div>
                <div>
                  <div className="text-sm font-medium text-[var(--text-primary)]">{s.label}</div>
                  <div className="h-1.5 w-24 bg-slate-700 rounded-full mt-1">
                    <div className="h-full bg-emerald-500 rounded-full" style={{ width: `${(s.score / 5) * 100}%` }} />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Weaknesses */}
        <div className="glass-card rounded-xl border border-orange-500/20 p-6">
          <h2 className="text-lg font-bold text-orange-400 mb-4 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5" />
            Key Gaps
          </h2>
          <div className="space-y-3">
            {weaknesses.map((w, i) => (
              <div key={i} className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-orange-500/10 flex items-center justify-center text-orange-400 font-bold text-sm">
                  {w.score.toFixed(1)}
                </div>
                <div>
                  <div className="text-sm font-medium text-[var(--text-primary)]">{w.label}</div>
                  <div className="h-1.5 w-24 bg-slate-700 rounded-full mt-1">
                    <div className="h-full bg-orange-500 rounded-full" style={{ width: `${(w.score / 5) * 100}%` }} />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Competitive Position */}
        <div className="glass-card rounded-xl border border-blue-500/20 p-6">
          <h2 className="text-lg font-bold text-blue-400 mb-4 flex items-center gap-2">
            <BarChart3 className="w-5 h-5" />
            Competitive Position
          </h2>
          {benchmark ? (
            <div className="space-y-4">
              <div className="text-center">
                <div className="relative w-20 h-20 mx-auto mb-2">
                  <svg viewBox="0 0 36 36" className="w-20 h-20 -rotate-90">
                    <circle cx="18" cy="18" r="15.9" fill="none" stroke="rgba(30,41,59,0.5)" strokeWidth="3" />
                    <circle
                      cx="18" cy="18" r="15.9" fill="none"
                      stroke="#1ABCFE"
                      strokeWidth="3"
                      strokeDasharray={`${benchmark.vertical_percentile} ${100 - benchmark.vertical_percentile}`}
                      strokeLinecap="round"
                    />
                  </svg>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-lg font-bold text-blue-400">P{benchmark.vertical_percentile.toFixed(0)}</span>
                  </div>
                </div>
                <p className="text-xs text-[var(--text-muted)]">
                  Rank {benchmark.vertical_rank} of {benchmark.peer_count} peers
                </p>
              </div>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-[var(--text-muted)]">Vertical Avg</span>
                  <span className="font-bold text-[var(--text-primary)]">{benchmark.vertical_avg.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[var(--text-muted)]">vs Avg</span>
                  <span className={`font-bold ${company.composite_score > benchmark.vertical_avg ? 'text-emerald-400' : 'text-red-400'}`}>
                    {company.composite_score > benchmark.vertical_avg ? '+' : ''}{(company.composite_score - benchmark.vertical_avg).toFixed(2)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[var(--text-muted)]">Gap to Max</span>
                  <span className="font-bold text-amber-400">
                    {(benchmark.vertical_max - company.composite_score).toFixed(2)}
                  </span>
                </div>
              </div>
              <div className="pt-2 border-t border-slate-700/30">
                <p className="text-xs text-[var(--text-muted)] mb-1">Peer verticals:</p>
                <div className="flex flex-wrap gap-1">
                  {benchmark.peer_verticals.slice(0, 3).map((v, i) => (
                    <span key={i} className="bg-slate-800/50 text-[var(--text-secondary)] rounded-full px-2 py-0.5 text-xs">{v}</span>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <p className="text-sm text-[var(--text-muted)]">Benchmark data not available.</p>
          )}
        </div>
      </div>

      {/* Recommendations */}
      <div className="glass-card rounded-xl border border-purple-500/20 p-6">
        <h2 className="text-lg font-bold text-purple-400 mb-4 flex items-center gap-2">
          <Lightbulb className="w-5 h-5" />
          Strategic Recommendations
        </h2>
        <div className="grid grid-cols-2 gap-4">
          {recommendations.map((rec, i) => (
            <div key={i} className="flex items-start gap-3 p-4 bg-slate-800/30 rounded-xl border border-slate-700/30">
              <div className="w-6 h-6 rounded-full bg-purple-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                <span className="text-xs font-bold text-purple-400">{i + 1}</span>
              </div>
              <p className="text-sm text-[var(--text-secondary)]">{rec}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Wave Assignment */}
      <div className="glass-card rounded-xl border border-slate-700/50 p-6">
        <h2 className="text-lg font-bold text-[var(--text-primary)] mb-3 flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-teal-400" />
          Implementation Wave
        </h2>
        <div className="flex items-center gap-6">
          {[1, 2, 3].map(w => (
            <div
              key={w}
              className={`flex-1 p-4 rounded-xl border text-center transition-all ${
                company.wave === w
                  ? 'border-teal-500/50 bg-teal-500/10'
                  : 'border-slate-700/30 bg-slate-800/20 opacity-40'
              }`}
            >
              <div className={`text-2xl font-bold mb-1 ${company.wave === w ? 'text-teal-400' : 'text-[var(--text-muted)]'}`}>
                Wave {w}
              </div>
              <div className="text-xs text-[var(--text-secondary)]">
                {w === 1 ? 'Q1-Q2 (Immediate)' : w === 2 ? 'Q3-Q4 (Near-term)' : 'Year 2 (Build)'}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
