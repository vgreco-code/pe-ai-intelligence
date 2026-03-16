import { useState } from 'react'
import {
  Search, ChevronDown, ChevronUp, Brain, Users, ExternalLink,
  Cpu, Briefcase, Newspaper, Code2, UserCheck,
} from 'lucide-react'
import type { PortfolioCompany } from '../App'
import { CATEGORIES, DIMENSION_LABELS, getScoreColor } from '../App'

// ── Research Evidence Panel ─────────────────────────────────────────────────
// Displays enrichment data from the Tavily deep research pipeline.
// Shows: AI initiatives, tech stack, key evidence, hiring signals,
//        executives, customers, news events, and score insights.

interface Props {
  company: PortfolioCompany
  evidence?: {
    ai_initiatives?: { text: string; type: string }[]
    tech_stack?: string[]
    named_customers?: string[]
    recent_news?: string[]
    executives?: { name: string; role: string }[]
    hiring_signals?: string[]
    key_evidence?: { text: string; source: string; url: string }[]
    enrichment_stats?: Record<string, number>
  }
}

function getScoreInsights(company: PortfolioCompany) {
  const entries = Object.entries(company.pillar_scores)
    .map(([dim, score]) => ({ dim, score, label: DIMENSION_LABELS[dim] || dim }))
  const strengths = [...entries].sort((a, b) => b.score - a.score).slice(0, 3)
  const gaps = [...entries].sort((a, b) => a.score - b.score).slice(0, 3)
  const catScores = Object.entries(CATEGORIES).map(([cat, dims]) => ({
    cat,
    avg: dims.reduce((s, d) => s + (company.pillar_scores[d] || 0), 0) / dims.length,
  })).sort((a, b) => b.avg - a.avg)
  return { strengths, gaps, strongestCat: catScores[0] }
}

// Tech stack category colors
const TECH_COLORS: Record<string, string> = {
  AWS: '#FF9900', Azure: '#0078D4', GCP: '#4285F4', Kubernetes: '#326CE5',
  Docker: '#2496ED', Python: '#3776AB', TypeScript: '#3178C6', React: '#61DAFB',
  'Node.js': '#339933', Java: '#ED8B00', '.NET': '#512BD4', Go: '#00ADD8',
  PostgreSQL: '#4169E1', MongoDB: '#47A248', Redis: '#DC382D', Elasticsearch: '#005571',
  Snowflake: '#29B5E8', Databricks: '#FF3621', TensorFlow: '#FF6F00', PyTorch: '#EE4C2C',
  OpenAI: '#412991', Anthropic: '#D4A574', 'Hugging Face': '#FFD21E',
  Terraform: '#7B42BC', Salesforce: '#00A1E0', Stripe: '#635BFF',
}

const INITIATIVE_TYPE_LABELS: Record<string, string> = {
  product_launch: 'Product Launch',
  ai_feature: 'AI Feature',
  genai_feature: 'GenAI',
  ml_capability: 'ML Capability',
}

export default function ResearchEvidence({ company, evidence }: Props) {
  const [showAllEvidence, setShowAllEvidence] = useState(false)
  const { strengths, gaps, strongestCat } = getScoreInsights(company)
  const confidenceScore = (company as any).confidence_score

  const ev = evidence || {}
  const aiInits = ev.ai_initiatives || []
  const techStack = ev.tech_stack || []
  const customers = ev.named_customers || []
  const news = ev.recent_news || []
  const executives = ev.executives || []
  const hiring = ev.hiring_signals || []
  const keyEvidence = ev.key_evidence || []
  const stats = ev.enrichment_stats

  const hasEnrichment = aiInits.length > 0 || techStack.length > 0 || keyEvidence.length > 0

  return (
    <div className="glass-card rounded-xl border border-violet-500/20 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-lg font-bold text-[var(--text-primary)] flex items-center gap-2">
          <Search className="w-5 h-5 text-violet-400" />
          Research Evidence
        </h2>
        <div className="flex items-center gap-3">
          {stats && (
            <span className="text-[10px] text-[var(--text-muted)]">
              {stats.total_results} sources analyzed
            </span>
          )}
          {confidenceScore != null && (
            <div className="flex items-center gap-1.5 bg-violet-500/10 px-3 py-1 rounded-full border border-violet-500/20">
              <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: confidenceScore >= 80 ? '#02C39A' : confidenceScore >= 60 ? '#F5A623' : '#F24E1E' }} />
              <span className="text-sm font-bold text-violet-400">{confidenceScore.toFixed(0)}% confidence</span>
            </div>
          )}
        </div>
      </div>
      <p className="text-xs text-[var(--text-muted)] mb-5">
        Evidence gathered from {hasEnrichment ? '14 targeted web research queries' : 'deep web research'} on {company.name}
      </p>

      {/* Summary stats row */}
      <div className="flex gap-3 mb-5">
        <div className="flex-1 bg-cyan-500/5 rounded-lg p-3 border border-cyan-500/10 text-center">
          <div className="text-xl font-bold text-cyan-400">{aiInits.length}</div>
          <div className="text-[10px] text-[var(--text-muted)] font-medium">AI Initiatives</div>
        </div>
        <div className="flex-1 bg-violet-500/5 rounded-lg p-3 border border-violet-500/10 text-center">
          <div className="text-xl font-bold text-violet-400">{techStack.length}</div>
          <div className="text-[10px] text-[var(--text-muted)] font-medium">Tech Signals</div>
        </div>
        <div className="flex-1 bg-amber-500/5 rounded-lg p-3 border border-amber-500/10 text-center">
          <div className="text-xl font-bold text-amber-400">{hiring.length}</div>
          <div className="text-[10px] text-[var(--text-muted)] font-medium">Hiring Roles</div>
        </div>
        <div className="flex-1 bg-emerald-500/5 rounded-lg p-3 border border-emerald-500/10 text-center">
          <div className="text-xl font-bold text-emerald-400">{strongestCat.cat.split(' ')[0]}</div>
          <div className="text-[10px] text-[var(--text-muted)] font-medium">Strongest Area</div>
        </div>
      </div>

      {hasEnrichment ? (
        <div className="space-y-5">
          {/* Tech Stack */}
          {techStack.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Code2 className="w-4 h-4 text-violet-400" />
                <span className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider">Detected Tech Stack</span>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {techStack.map((tech, i) => (
                  <span
                    key={i}
                    className="px-2.5 py-1 rounded-full text-[11px] font-semibold border"
                    style={{
                      color: TECH_COLORS[tech] || '#94a3b8',
                      backgroundColor: `${TECH_COLORS[tech] || '#94a3b8'}12`,
                      borderColor: `${TECH_COLORS[tech] || '#94a3b8'}25`,
                    }}
                  >
                    {tech}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* AI Initiatives */}
          {aiInits.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Brain className="w-4 h-4 text-cyan-400" />
                <span className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider">AI Initiatives Detected</span>
              </div>
              <div className="space-y-1.5">
                {aiInits.slice(0, 5).map((init, i) => (
                  <div key={i} className="flex items-start gap-2 p-2 bg-slate-800/30 rounded-lg border border-slate-700/20">
                    <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-cyan-500/10 text-cyan-400 flex-shrink-0 mt-0.5">
                      {INITIATIVE_TYPE_LABELS[init.type] || init.type}
                    </span>
                    <span className="text-xs text-[var(--text-secondary)] leading-snug">{init.text}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Hiring Signals */}
          {hiring.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-2">
                <UserCheck className="w-4 h-4 text-amber-400" />
                <span className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider">Active Hiring Roles</span>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {hiring.map((role, i) => (
                  <span key={i} className="px-2.5 py-1 rounded-full text-[11px] font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20">
                    {role}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Two-column: Executives + Customers/News */}
          <div className="grid grid-cols-2 gap-4">
            {/* Executives */}
            {executives.length > 0 && (
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <Briefcase className="w-4 h-4 text-purple-400" />
                  <span className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider">Leadership</span>
                </div>
                <div className="space-y-1">
                  {executives.map((exec, i) => (
                    <div key={i} className="flex items-center gap-2 text-xs">
                      <Users className="w-3 h-3 text-purple-400 flex-shrink-0" />
                      <span className="text-[var(--text-primary)] font-medium">{exec.name}</span>
                      <span className="text-[var(--text-muted)]">— {exec.role}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Customers + News combined */}
            <div>
              {customers.length > 0 && (
                <div className="mb-3">
                  <div className="flex items-center gap-2 mb-2">
                    <Cpu className="w-4 h-4 text-emerald-400" />
                    <span className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider">Named Customers</span>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {customers.map((cust, i) => (
                      <span key={i} className="px-2 py-0.5 rounded text-[11px] font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        {cust}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {news.length > 0 && (
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <Newspaper className="w-4 h-4 text-blue-400" />
                    <span className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider">Recent News</span>
                  </div>
                  <div className="space-y-1">
                    {news.slice(0, 3).map((item, i) => (
                      <div key={i} className="text-xs text-[var(--text-secondary)] leading-snug p-1.5 bg-slate-800/20 rounded">
                        {item}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Key Evidence Snippets */}
          {keyEvidence.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Search className="w-4 h-4 text-violet-400" />
                <span className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider">Key Evidence Snippets</span>
              </div>
              <div className="space-y-2">
                {(showAllEvidence ? keyEvidence : keyEvidence.slice(0, 3)).map((ev, i) => (
                  <div key={i} className="p-3 bg-slate-800/30 rounded-lg border border-slate-700/20 hover:border-violet-500/20 transition-all">
                    <p className="text-xs text-[var(--text-secondary)] leading-relaxed">&ldquo;{ev.text}&rdquo;</p>
                    {ev.source && (
                      <div className="flex items-center gap-1 mt-1.5">
                        <ExternalLink className="w-3 h-3 text-[var(--text-muted)]" />
                        <span className="text-[10px] text-[var(--text-muted)]">{ev.source}</span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
              {keyEvidence.length > 3 && (
                <button
                  onClick={() => setShowAllEvidence(!showAllEvidence)}
                  className="mt-2 flex items-center gap-1 text-xs text-violet-400 hover:text-violet-300 transition-colors mx-auto"
                >
                  {showAllEvidence ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                  {showAllEvidence ? 'Show less' : `Show ${keyEvidence.length - 3} more`}
                </button>
              )}
            </div>
          )}
        </div>
      ) : (
        /* Fallback: score-based insights when no enrichment data */
        <div className="text-xs text-[var(--text-muted)] italic">
          Enrichment data not available. Showing score-derived insights only.
        </div>
      )}

      {/* Score insight summary — always shown */}
      <div className="mt-5 grid grid-cols-2 gap-3">
        <div className="bg-slate-800/30 rounded-lg p-3 border border-slate-700/30">
          <div className="text-[10px] font-semibold uppercase tracking-wider text-emerald-400 mb-2">Top Dimensions</div>
          {strengths.map((s, i) => (
            <div key={i} className="flex justify-between items-center mb-1">
              <span className="text-xs text-[var(--text-secondary)]">{s.label}</span>
              <span className="text-xs font-bold" style={{ color: getScoreColor(s.score) }}>{s.score.toFixed(1)}</span>
            </div>
          ))}
        </div>
        <div className="bg-slate-800/30 rounded-lg p-3 border border-slate-700/30">
          <div className="text-[10px] font-semibold uppercase tracking-wider text-red-400 mb-2">Largest Gaps</div>
          {gaps.map((g, i) => (
            <div key={i} className="flex justify-between items-center mb-1">
              <span className="text-xs text-[var(--text-secondary)]">{g.label}</span>
              <span className="text-xs font-bold" style={{ color: getScoreColor(g.score) }}>{g.score.toFixed(1)}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
