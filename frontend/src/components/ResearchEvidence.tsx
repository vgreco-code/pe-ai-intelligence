import { useState } from 'react'
import {
  Search, ChevronDown, ChevronUp, Brain, Users, ExternalLink,
  Cpu, Briefcase, Newspaper, Code2, UserCheck,
  GitBranch, Star, Building2,
} from 'lucide-react'
import type { PortfolioCompany } from '../App'
import { CATEGORIES, DIMENSION_LABELS, getScoreColor } from '../App'

// ── Research Evidence Panel ─────────────────────────────────────────────────
// Displays enrichment data from the Tavily deep research pipeline.
// Shows: AI initiatives, tech stack, key evidence, hiring signals,
//        executives, customers, news events, and score insights.

interface GitHubData {
  found: boolean
  org_login?: string
  org_url?: string
  total_public_repos?: number
  total_stars?: number
  total_forks?: number
  recently_active_repos?: number
  primary_languages?: { language: string; repo_count: number }[]
  top_repos?: { name: string; description: string; language: string; stars: number; forks: number; updated: string }[]
}

interface CareersData {
  found: boolean
  careers_url?: string
  total_openings?: number
  ai_ml_openings?: number
  departments?: Record<string, number>
  sample_roles?: string[]
  ai_roles?: string[]
}

interface TalentPerson {
  name: string
  role: string
}

interface TalentData {
  found: boolean
  total_profiles_found?: number
  linkedin_profiles_discovered?: number
  leadership?: TalentPerson[]
  ai_ml_talent?: TalentPerson[]
  senior_engineers?: TalentPerson[]
  engineering_team?: TalentPerson[]
  management?: TalentPerson[]
  team_skills?: string[]
  estimated_total_employees?: number
  estimated_eng_team?: number
  talent_summary?: {
    has_cto: boolean
    has_vp_eng: boolean
    has_ai_leadership: boolean
    ai_ml_headcount: number
    eng_headcount_discovered: number
    leadership_headcount: number
    total_discovered: number
  }
}

interface Props {
  company: PortfolioCompany
  evidence?: {
    ai_initiatives?: { text: string; type: string }[]
    tech_stack?: string[]
    tech_stack_github_confirmed?: string[]
    named_customers?: string[]
    recent_news?: string[]
    executives?: { name: string; role: string }[]
    hiring_signals?: string[]
    key_evidence?: { text: string; source: string; url: string }[]
    enrichment_stats?: Record<string, number>
    narrative_summary?: string
    github?: GitHubData
    careers?: CareersData
    talent?: TalentData
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
  const githubConfirmedTech = new Set(ev.tech_stack_github_confirmed || [])
  const customers = ev.named_customers || []
  const rawNews = ev.recent_news || []
  // Normalize news: accept both string[] and {title,summary,url,date}[]
  const news = rawNews.map((item: any) => typeof item === 'string' ? item : (item.summary || item.title || ''))
  const executives = ev.executives || []
  // Support both hiring_signals and careers.titles
  const hiring = ev.hiring_signals || ((ev.careers as any)?.titles) || []
  const keyEvidence = ev.key_evidence || []
  const stats = ev.enrichment_stats
  const github = ev.github
  const careers = ev.careers
  const talent = ev.talent

  // Filter noise from talent data (e.g. "View Post", company names as people)
  const TALENT_NAME_BLOCKLIST = ['view post', 'moser consulting', 'palantir foundry', 'linkedin', 'unknown']
  const isValidPerson = (p: TalentPerson) => {
    const lower = p.name.toLowerCase()
    if (TALENT_NAME_BLOCKLIST.some(b => lower.includes(b))) return false
    if (p.name.length < 3 || p.name.length > 50) return false
    // Must have at least 2 words (first + last name)
    if (p.name.trim().split(/\s+/).length < 2) return false
    return true
  }
  const talentLeadership = (talent?.leadership || []).filter(isValidPerson)
  const talentAiMl = (talent?.ai_ml_talent || []).filter(isValidPerson)
  const talentEngineers = [...(talent?.senior_engineers || []), ...(talent?.engineering_team || [])].filter(isValidPerson)
  const talentSkills = talent?.team_skills || []
  const talentSummary = talent?.talent_summary
  const hasTalent = talent?.found && (talentLeadership.length > 0 || talentAiMl.length > 0 || talentEngineers.length > 0 || talentSkills.length > 0)

  const hasEnrichment = !!ev.narrative_summary || aiInits.length > 0 || techStack.length > 0 || keyEvidence.length > 0

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
              {stats.relevant_results || stats.total_results}/{stats.total_results} relevant sources
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
        Evidence gathered from {hasEnrichment ? '20 targeted web research queries' : 'deep web research'}
        {github?.found ? ', GitHub API' : ''}{careers?.found ? ', careers page' : ''}{hasTalent ? ', LinkedIn talent analysis' : ''} on {company.name}
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
          {/* Narrative Summary */}
          {ev.narrative_summary && (
            <div className="bg-gradient-to-r from-violet-500/5 to-blue-500/5 rounded-lg p-4 border border-violet-500/15">
              <div className="flex items-center gap-2 mb-2">
                <Brain className="w-4 h-4 text-violet-400" />
                <span className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider">AI Readiness Assessment</span>
              </div>
              <p className="text-sm text-[var(--text-secondary)] leading-relaxed">
                {ev.narrative_summary}
              </p>
            </div>
          )}

          {/* Tech Stack */}
          {techStack.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Code2 className="w-4 h-4 text-violet-400" />
                <span className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider">Detected Tech Stack</span>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {techStack.map((tech, i) => {
                  const isConfirmed = githubConfirmedTech.has(tech)
                  return (
                    <span
                      key={i}
                      className="px-2.5 py-1 rounded-full text-[11px] font-semibold border flex items-center gap-1"
                      style={{
                        color: TECH_COLORS[tech] || '#94a3b8',
                        backgroundColor: `${TECH_COLORS[tech] || '#94a3b8'}12`,
                        borderColor: `${TECH_COLORS[tech] || '#94a3b8'}25`,
                      }}
                      title={isConfirmed ? 'Confirmed via GitHub repos' : 'Detected from web sources'}
                    >
                      {tech}
                      {isConfirmed && <GitBranch className="w-3 h-3 opacity-70" />}
                    </span>
                  )
                })}
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
                {hiring.map((role: string, i: number) => (
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

          {/* GitHub + Careers Row */}
          {(github?.found || careers?.found) && (
            <div className="grid grid-cols-2 gap-4">
              {/* GitHub Presence */}
              {github?.found && (
                <div className="bg-slate-800/30 rounded-lg p-4 border border-slate-700/30">
                  <div className="flex items-center gap-2 mb-3">
                    <GitBranch className="w-4 h-4 text-green-400" />
                    <span className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider">GitHub Presence</span>
                    <a href={github.org_url} target="_blank" rel="noopener noreferrer" className="ml-auto text-[10px] text-green-400 hover:text-green-300 flex items-center gap-1">
                      @{github.org_login} <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                  <div className="grid grid-cols-3 gap-2 mb-3">
                    <div className="text-center">
                      <div className="text-lg font-bold text-green-400">{github.total_public_repos}</div>
                      <div className="text-[9px] text-[var(--text-muted)]">Public Repos</div>
                    </div>
                    <div className="text-center">
                      <div className="text-lg font-bold text-yellow-400 flex items-center justify-center gap-1">
                        <Star className="w-3 h-3" />{github.total_stars}
                      </div>
                      <div className="text-[9px] text-[var(--text-muted)]">Total Stars</div>
                    </div>
                    <div className="text-center">
                      <div className="text-lg font-bold text-blue-400">{github.recently_active_repos || 0}</div>
                      <div className="text-[9px] text-[var(--text-muted)]">Recent Active</div>
                    </div>
                  </div>
                  {github.primary_languages && github.primary_languages.length > 0 && (
                    <div className="flex flex-wrap gap-1 mb-2">
                      {github.primary_languages.slice(0, 5).map((lang, i) => (
                        <span key={i} className="px-2 py-0.5 rounded text-[10px] font-medium bg-green-500/10 text-green-400 border border-green-500/20">
                          {lang.language} ({lang.repo_count})
                        </span>
                      ))}
                    </div>
                  )}
                  {github.top_repos && github.top_repos.length > 0 && (
                    <div className="space-y-1 mt-2">
                      {github.top_repos.slice(0, 3).map((repo, i) => (
                        <div key={i} className="text-[11px] text-[var(--text-muted)] flex items-center gap-1.5">
                          <Code2 className="w-3 h-3 flex-shrink-0 text-green-400/60" />
                          <span className="text-green-400/80 font-medium">{repo.name}</span>
                          {repo.stars > 0 && <span className="text-yellow-400/60 text-[9px]">({repo.stars}★)</span>}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Careers / Open Positions */}
              {careers?.found && (
                <div className="bg-slate-800/30 rounded-lg p-4 border border-slate-700/30">
                  <div className="flex items-center gap-2 mb-3">
                    <Building2 className="w-4 h-4 text-rose-400" />
                    <span className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider">Open Positions</span>
                    <a href={careers.careers_url} target="_blank" rel="noopener noreferrer" className="ml-auto text-[10px] text-rose-400 hover:text-rose-300 flex items-center gap-1">
                      Careers page <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                  <div className="grid grid-cols-2 gap-2 mb-3">
                    <div className="text-center">
                      <div className="text-lg font-bold text-rose-400">{careers.total_openings}</div>
                      <div className="text-[9px] text-[var(--text-muted)]">Total Openings</div>
                    </div>
                    <div className="text-center">
                      <div className="text-lg font-bold text-cyan-400">{careers.ai_ml_openings || 0}</div>
                      <div className="text-[9px] text-[var(--text-muted)]">AI/ML Roles</div>
                    </div>
                  </div>
                  {careers.departments && Object.keys(careers.departments).length > 0 && (
                    <div className="mb-2">
                      <div className="text-[10px] text-[var(--text-muted)] mb-1">By Department:</div>
                      <div className="flex flex-wrap gap-1">
                        {Object.entries(careers.departments).map(([dept, count], i) => (
                          <span key={i} className="px-2 py-0.5 rounded text-[10px] font-medium bg-rose-500/10 text-rose-400 border border-rose-500/20">
                            {dept} ({count})
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  {careers.sample_roles && careers.sample_roles.length > 0 && (
                    <div className="space-y-0.5 mt-2">
                      {careers.sample_roles.slice(0, 5).map((role, i) => (
                        <div key={i} className="text-[11px] text-[var(--text-muted)] flex items-center gap-1.5">
                          <Users className="w-3 h-3 flex-shrink-0 text-rose-400/60" />
                          <span>{role}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* GitHub-only: fill second column with summary if no careers */}
              {github?.found && !careers?.found && (
                <div className="bg-slate-800/30 rounded-lg p-4 border border-slate-700/30 flex flex-col items-center justify-center text-center">
                  <Building2 className="w-5 h-5 text-[var(--text-muted)] mb-2 opacity-40" />
                  <div className="text-[11px] text-[var(--text-muted)]">No public careers page found</div>
                  <div className="text-[10px] text-[var(--text-muted)] mt-1 opacity-60">Hiring signals from web research shown above</div>
                </div>
              )}
            </div>
          )}

          {/* Tech Talent (LinkedIn) */}
          {hasTalent && (
            <div className="bg-gradient-to-r from-blue-500/5 to-teal-500/5 rounded-lg p-4 border border-blue-500/15">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Users className="w-4 h-4 text-blue-400" />
                  <span className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider">Tech Talent Profile</span>
                </div>
                <div className="flex items-center gap-2">
                  {talent?.estimated_total_employees && talent.estimated_total_employees > 0 && (
                    <span className="text-[10px] text-[var(--text-muted)] bg-slate-800/40 px-2 py-0.5 rounded-full">
                      ~{talent.estimated_total_employees.toLocaleString()} employees
                    </span>
                  )}
                  {talent?.estimated_eng_team && talent.estimated_eng_team > 0 && (
                    <span className="text-[10px] text-[var(--text-muted)] bg-blue-500/10 px-2 py-0.5 rounded-full">
                      ~{talent.estimated_eng_team.toLocaleString()} eng (est.)
                    </span>
                  )}
                </div>
              </div>

              {/* Leadership indicators */}
              {talentSummary && (
                <div className="flex gap-2 mb-3">
                  <span className={`px-2 py-0.5 rounded text-[10px] font-medium border ${talentSummary.has_cto ? 'bg-green-500/10 text-green-400 border-green-500/20' : 'bg-slate-800/30 text-[var(--text-muted)] border-slate-700/20'}`}>
                    CTO {talentSummary.has_cto ? '✓' : '—'}
                  </span>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-medium border ${talentSummary.has_vp_eng ? 'bg-green-500/10 text-green-400 border-green-500/20' : 'bg-slate-800/30 text-[var(--text-muted)] border-slate-700/20'}`}>
                    VP Eng {talentSummary.has_vp_eng ? '✓' : '—'}
                  </span>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-medium border ${talentSummary.has_ai_leadership ? 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20' : 'bg-slate-800/30 text-[var(--text-muted)] border-slate-700/20'}`}>
                    AI Leadership {talentSummary.has_ai_leadership ? '✓' : '—'}
                  </span>
                  {talentSummary.ai_ml_headcount > 0 && (
                    <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                      {talentSummary.ai_ml_headcount} AI/ML
                    </span>
                  )}
                </div>
              )}

              {/* People grid */}
              <div className="grid grid-cols-2 gap-3">
                {/* Tech Leadership */}
                {talentLeadership.length > 0 && (
                  <div>
                    <div className="text-[10px] font-semibold text-blue-400 uppercase tracking-wider mb-1.5">Tech Leadership</div>
                    <div className="space-y-1">
                      {talentLeadership.map((p, i) => (
                        <div key={i} className="flex items-center gap-1.5 text-[11px]">
                          <Briefcase className="w-3 h-3 text-blue-400/60 flex-shrink-0" />
                          <span className="text-[var(--text-primary)] font-medium">{p.name}</span>
                          <span className="text-[var(--text-muted)]">— {p.role}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* AI/ML Talent */}
                {talentAiMl.length > 0 && (
                  <div>
                    <div className="text-[10px] font-semibold text-cyan-400 uppercase tracking-wider mb-1.5">AI/ML Talent</div>
                    <div className="space-y-1">
                      {talentAiMl.map((p, i) => (
                        <div key={i} className="flex items-center gap-1.5 text-[11px]">
                          <Brain className="w-3 h-3 text-cyan-400/60 flex-shrink-0" />
                          <span className="text-[var(--text-primary)] font-medium">{p.name}</span>
                          <span className="text-[var(--text-muted)]">— {p.role}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Engineers */}
                {talentEngineers.length > 0 && (
                  <div>
                    <div className="text-[10px] font-semibold text-green-400 uppercase tracking-wider mb-1.5">Engineering Team</div>
                    <div className="space-y-1">
                      {talentEngineers.slice(0, 5).map((p, i) => (
                        <div key={i} className="flex items-center gap-1.5 text-[11px]">
                          <Code2 className="w-3 h-3 text-green-400/60 flex-shrink-0" />
                          <span className="text-[var(--text-primary)] font-medium">{p.name}</span>
                          <span className="text-[var(--text-muted)]">— {p.role}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Team Skills */}
                {talentSkills.length > 0 && (
                  <div>
                    <div className="text-[10px] font-semibold text-teal-400 uppercase tracking-wider mb-1.5">Team Skills (LinkedIn)</div>
                    <div className="flex flex-wrap gap-1">
                      {talentSkills.slice(0, 12).map((skill, i) => (
                        <span key={i} className="px-2 py-0.5 rounded text-[10px] font-medium bg-teal-500/10 text-teal-400 border border-teal-500/20">
                          {skill}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

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
