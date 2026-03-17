import {
  TrendingUp, Building2, Brain, Layers, Target, Shield, Zap,
  ChevronRight, ExternalLink, Award, BarChart3, GitBranch
} from 'lucide-react'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  PieChart, Pie, Cell,
} from 'recharts'
import {
  PortfolioCompany, TIER_COLORS, getTierBg,
  DIMENSION_LABELS, CATEGORIES, CATEGORY_COLORS,
} from '../App'

interface Props {
  portfolio: PortfolioCompany[]
  onCompanyClick?: (name: string) => void
}

const WAVE_CONFIG: Record<number, { label: string; color: string; desc: string }> = {
  1: { label: 'Deploy Now', color: '#02C39A', desc: 'Highest AI readiness — ready for immediate AI product investment' },
  2: { label: 'Build Foundation', color: '#F5A623', desc: 'Strong fundamentals — need targeted infrastructure before AI deployment' },
  3: { label: 'Groundwork', color: '#F24E1E', desc: 'Significant modernization required — focus on data & cloud foundations' },
}

export default function ExecutiveSummary({ portfolio, onCompanyClick }: Props) {
  const sorted = [...portfolio].sort((a, b) => b.composite_score - a.composite_score)
  const avgScore = (portfolio.reduce((s, c) => s + c.composite_score, 0) / portfolio.length).toFixed(2)
  const tierCounts = portfolio.reduce((acc, c) => {
    acc[c.tier] = (acc[c.tier] || 0) + 1
    return acc
  }, {} as Record<string, number>)
  // Category averages across portfolio
  const categoryAvgs = Object.entries(CATEGORIES).map(([cat, dims]) => {
    const avg = portfolio.reduce((sum, co) => {
      const catAvg = dims.reduce((s, d) => s + (co.pillar_scores[d] || 0), 0) / dims.length
      return sum + catAvg
    }, 0) / portfolio.length
    return { category: cat, score: parseFloat(avg.toFixed(2)), fill: CATEGORY_COLORS[cat] }
  })

  // Top strengths and weaknesses across portfolio
  const dimAvgs = Object.keys(DIMENSION_LABELS).map(dim => {
    const avg = portfolio.reduce((s, c) => s + (c.pillar_scores[dim] || 0), 0) / portfolio.length
    return { dim, label: DIMENSION_LABELS[dim], avg: parseFloat(avg.toFixed(2)) }
  }).sort((a, b) => b.avg - a.avg)

  const topStrengths = dimAvgs.slice(0, 5)
  const topWeaknesses = [...dimAvgs].sort((a, b) => a.avg - b.avg).slice(0, 5)

  // Radar data for category averages
  const radarData = categoryAvgs.map(c => ({
    category: c.category.replace('&', '\n&'),
    score: c.score,
    fullMark: 5,
  }))

  // Ranking bar chart data
  const rankingData = sorted.map((c, i) => ({
    name: c.name,
    score: c.composite_score,
    fill: c.wave === 1 ? '#02C39A' : c.wave === 2 ? '#F5A623' : '#F24E1E',
    rank: i + 1,
  }))

  // Tier distribution for pie
  const tierPieData = Object.entries(tierCounts).map(([tier, count]) => ({
    name: tier,
    value: count,
    fill: TIER_COLORS[tier] || '#6b7280',
  }))

  return (
    <div className="space-y-8 max-w-5xl">
      {/* Hero */}
      <div className="relative glass-card rounded-2xl border border-teal-500/20 overflow-hidden">
        <div className="absolute top-0 left-0 w-full h-full">
          <div className="absolute top-[-50%] left-[-20%] w-[60%] h-[200%] bg-teal-500/5 rounded-full blur-3xl" />
          <div className="absolute bottom-[-50%] right-[-10%] w-[40%] h-[200%] bg-blue-500/3 rounded-full blur-3xl" />
        </div>
        <div className="relative p-8 lg:p-10">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: 'var(--teal)' }}>
              <TrendingUp className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">Executive Summary</h1>
              <p className="text-xs font-medium" style={{ color: 'var(--teal)' }}>PE AI Intelligence Platform — Solen Software Group</p>
            </div>
          </div>
          <p className="text-sm text-[var(--text-secondary)] max-w-3xl leading-relaxed">
            This platform evaluates AI maturity and investment readiness across Solen Software Group's portfolio of {portfolio.length} vertical
            market software (VMS) companies. Using a 17-dimension scoring model trained on 200+ enterprise software companies and validated
            by XGBoost feature importance analysis, each company is assessed across 6 categories and classified into implementation tiers
            and deployment waves to guide capital allocation and AI strategy.
          </p>
          {/* Key stats row */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
            {[
              { label: 'Portfolio Companies', value: portfolio.length.toString(), icon: Building2, color: '#02C39A' },
              { label: 'Avg AI Maturity', value: avgScore, icon: Brain, color: '#F5A623' },
              { label: 'Scoring Dimensions', value: '17', icon: Layers, color: '#8b5cf6' },
              { label: 'Training Set', value: '200+', icon: BarChart3, color: '#1ABCFE' },
            ].map(stat => (
              <div key={stat.label} className="bg-white/[0.04] rounded-xl p-4 border border-white/[0.06]">
                <stat.icon className="w-4 h-4 mb-2" style={{ color: stat.color }} />
                <div className="text-xl font-bold text-white">{stat.value}</div>
                <div className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider mt-0.5">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Section 1: Methodology Overview */}
      <section className="space-y-4">
        <SectionHeader icon={Brain} title="Scoring Methodology" subtitle="How companies are evaluated" />
        <div className="card p-6">
          <div className="text-sm text-[var(--text-secondary)] space-y-3 max-w-3xl">
            <p>
              Each company is scored on a <strong className="text-white">1.0 – 5.0 scale</strong> across 17 dimensions grouped into
              6 categories: Data & Analytics, Technology & Infrastructure, AI Product & Value, Organization & Talent, Governance & Risk,
              and Velocity & Momentum.
            </p>
            <p>
              Scores are derived from <strong className="text-white">web-verified evidence</strong> including company websites, press releases,
              job postings, regulatory filings (FCC, DCAA, HIPAA), G2/Capterra reviews, LinkedIn profiles, and industry databases. An
              <strong className="text-white"> Execution Capacity Factor (ECF)</strong> normalizes talent scores for company size, recognizing
              that PE portfolio companies leverage shared services rather than building large in-house AI teams.
            </p>
            <p>
              Dimension weights were initially derived from <strong className="text-white">XGBoost feature importance</strong> trained on 200+
              enterprise software companies, then manually rebalanced (v4) to correct scraping artifacts and align with PE domain expertise.
              The model achieves <strong className="text-white">93.8% cross-validated accuracy</strong> on tier classification.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
            {/* Tier definitions */}
            <div>
              <h3 className="text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-3">Tier Classification</h3>
              <div className="space-y-2">
                {[
                  { tier: 'AI-Ready', range: '≥ 3.5', desc: 'Can deploy AI features immediately' },
                  { tier: 'AI-Buildable', range: '≥ 2.8', desc: 'Strong foundation — targeted investment yields AI products' },
                  { tier: 'AI-Emerging', range: '≥ 2.0', desc: 'Needs foundational work before AI investment' },
                  { tier: 'AI-Limited', range: '< 2.0', desc: 'Significant modernization required' },
                ].map(t => (
                  <div key={t.tier} className="flex items-center gap-3">
                    <span className={`text-xs font-semibold px-2 py-0.5 rounded ${getTierBg(t.tier)}`}>{t.tier}</span>
                    <span className="text-xs font-mono text-[var(--text-muted)]">{t.range}</span>
                    <span className="text-xs text-[var(--text-secondary)]">{t.desc}</span>
                  </div>
                ))}
              </div>
            </div>
            {/* Category radar */}
            <div>
              <h3 className="text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-3">Portfolio Category Averages</h3>
              <ResponsiveContainer width="100%" height={200}>
                <RadarChart data={radarData}>
                  <PolarGrid stroke="rgba(255,255,255,0.06)" />
                  <PolarAngleAxis dataKey="category" tick={{ fill: 'var(--text-muted)', fontSize: 9 }} />
                  <PolarRadiusAxis angle={30} domain={[0, 5]} tick={{ fill: 'var(--text-muted)', fontSize: 8 }} />
                  <Radar dataKey="score" stroke="#02C39A" fill="#02C39A" fillOpacity={0.15} strokeWidth={2} />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </section>

      {/* Section 2: Portfolio Rankings */}
      <section className="space-y-4">
        <SectionHeader icon={Award} title="Portfolio Rankings" subtitle="All 14 companies ranked by composite AI maturity score" />
        <div className="card p-6">
          <ResponsiveContainer width="100%" height={420}>
            <BarChart data={rankingData} layout="vertical" margin={{ left: 100, right: 30, top: 5, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" horizontal={false} />
              <XAxis type="number" domain={[0, 4]} tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
              <YAxis
                type="category"
                dataKey="name"
                tick={{ fill: 'var(--text-secondary)', fontSize: 11 }}
                width={95}
              />
              <Tooltip
                contentStyle={{ background: '#1a1d2e', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, fontSize: 12 }}
                formatter={(value: number) => [value.toFixed(2), 'AI Maturity Score']}
              />
              <Bar dataKey="score" radius={[0, 6, 6, 0]} barSize={20}>
                {rankingData.map((entry, i) => (
                  <Cell key={i} fill={entry.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <div className="flex items-center gap-6 mt-3 justify-center">
            {Object.entries(WAVE_CONFIG).map(([w, cfg]) => (
              <div key={w} className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-sm" style={{ background: cfg.color }} />
                <span className="text-[10px] text-[var(--text-muted)]">Wave {w}: {cfg.label}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Section 3: Tier & Wave Distribution */}
      <section className="space-y-4">
        <SectionHeader icon={Target} title="Tier & Wave Distribution" subtitle="Classification breakdown and investment sequencing" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Tier pie */}
          <div className="card p-6">
            <h3 className="text-sm font-semibold text-white mb-4">Tier Distribution</h3>
            <div className="flex items-center gap-6">
              <ResponsiveContainer width={160} height={160}>
                <PieChart>
                  <Pie data={tierPieData} dataKey="value" cx="50%" cy="50%" innerRadius={40} outerRadius={70} paddingAngle={3}>
                    {tierPieData.map((entry, i) => (
                      <Cell key={i} fill={entry.fill} />
                    ))}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
              <div className="space-y-2">
                {tierPieData.map(t => (
                  <div key={t.name} className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-sm" style={{ background: t.fill }} />
                    <span className="text-xs text-[var(--text-secondary)]">{t.name}</span>
                    <span className="text-xs font-bold text-white">{t.value}</span>
                  </div>
                ))}
              </div>
            </div>
            <p className="text-xs text-[var(--text-muted)] mt-3">
              {tierCounts['AI-Buildable'] || 0} companies are AI-Buildable (strong candidates for near-term AI investment).
              {tierCounts['AI-Emerging'] || 0} are AI-Emerging (need foundational work first). No companies currently reach AI-Ready status,
              which represents the opportunity for a CAIO-led transformation.
            </p>
          </div>
          {/* Wave cards */}
          <div className="card p-6">
            <h3 className="text-sm font-semibold text-white mb-4">Wave Sequencing</h3>
            <div className="space-y-3">
              {[1, 2, 3].map(w => {
                const cfg = WAVE_CONFIG[w]
                const companies = portfolio.filter(c => c.wave === w).sort((a, b) => b.composite_score - a.composite_score)
                return (
                  <div key={w} className="bg-white/[0.03] rounded-lg p-3 border border-white/[0.06]">
                    <div className="flex items-center gap-2 mb-2">
                      <div className="w-6 h-6 rounded-md flex items-center justify-center text-xs font-bold text-white" style={{ background: cfg.color }}>
                        {w}
                      </div>
                      <span className="text-xs font-semibold text-white">{cfg.label}</span>
                      <span className="text-[10px] text-[var(--text-muted)] ml-auto">{companies.length} companies</span>
                    </div>
                    <p className="text-[10px] text-[var(--text-muted)] mb-2">{cfg.desc}</p>
                    <div className="flex flex-wrap gap-1.5">
                      {companies.map(c => (
                        <button
                          key={c.name}
                          onClick={() => onCompanyClick?.(c.name)}
                          className="text-[10px] font-medium px-2 py-0.5 rounded-full border hover:bg-white/[0.06] transition-colors cursor-pointer"
                          style={{ borderColor: cfg.color + '40', color: cfg.color }}
                        >
                          {c.name} ({c.composite_score.toFixed(2)})
                        </button>
                      ))}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      </section>

      {/* Section 4: Portfolio Strengths & Gaps */}
      <section className="space-y-4">
        <SectionHeader icon={BarChart3} title="Portfolio Strengths & Gaps" subtitle="Aggregate dimension analysis across all 14 companies" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="card p-6">
            <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-emerald-400" /> Top Strengths
            </h3>
            <div className="space-y-2.5">
              {topStrengths.map((d, i) => (
                <div key={d.dim} className="flex items-center gap-3">
                  <span className="text-xs font-bold text-emerald-400 w-5">{i + 1}</span>
                  <span className="text-xs text-[var(--text-secondary)] flex-1">{d.label}</span>
                  <div className="w-24 h-2 bg-white/[0.04] rounded-full overflow-hidden">
                    <div className="h-full rounded-full bg-emerald-400" style={{ width: `${(d.avg / 5) * 100}%` }} />
                  </div>
                  <span className="text-xs font-mono text-white w-8 text-right">{d.avg}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="card p-6">
            <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
              <Target className="w-4 h-4 text-orange-400" /> Key Gaps (Investment Opportunities)
            </h3>
            <div className="space-y-2.5">
              {topWeaknesses.map((d, i) => (
                <div key={d.dim} className="flex items-center gap-3">
                  <span className="text-xs font-bold text-orange-400 w-5">{i + 1}</span>
                  <span className="text-xs text-[var(--text-secondary)] flex-1">{d.label}</span>
                  <div className="w-24 h-2 bg-white/[0.04] rounded-full overflow-hidden">
                    <div className="h-full rounded-full bg-orange-400" style={{ width: `${(d.avg / 5) * 100}%` }} />
                  </div>
                  <span className="text-xs font-mono text-white w-8 text-right">{d.avg}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
        <div className="card p-6">
          <h3 className="text-sm font-semibold text-white mb-4">Category Averages Across Portfolio</h3>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={categoryAvgs} margin={{ left: 10, right: 10, top: 5, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis dataKey="category" tick={{ fill: 'var(--text-muted)', fontSize: 10 }} interval={0} angle={-15} textAnchor="end" height={50} />
              <YAxis domain={[0, 5]} tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
              <Tooltip
                contentStyle={{ background: '#1a1d2e', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, fontSize: 12 }}
                formatter={(value: number) => [value.toFixed(2), 'Avg Score']}
              />
              <Bar dataKey="score" radius={[6, 6, 0, 0]} barSize={40}>
                {categoryAvgs.map((entry, i) => (
                  <Cell key={i} fill={entry.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>

      {/* Section 5: Wave Detail — Company Profiles */}
      <section className="space-y-4">
        <SectionHeader icon={Layers} title="Wave Detail" subtitle="Company profiles by deployment wave" />
        {[1, 2, 3].map(w => {
          const cfg = WAVE_CONFIG[w]
          const companies = sorted.filter(c => c.wave === w)
          return (
            <div key={w} className="space-y-3">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold text-white" style={{ background: cfg.color }}>
                  {w}
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-white">Wave {w}: {cfg.label}</h3>
                  <p className="text-[10px] text-[var(--text-muted)]">{cfg.desc}</p>
                </div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {companies.map((c) => {
                  const overallRank = sorted.findIndex(s => s.name === c.name) + 1
                  const topCat = c.category_scores
                    ? Object.entries(c.category_scores).sort((a, b) => b[1] - a[1])[0]
                    : null
                  const weakCat = c.category_scores
                    ? Object.entries(c.category_scores).sort((a, b) => a[1] - b[1])[0]
                    : null
                  return (
                    <button
                      key={c.name}
                      onClick={() => onCompanyClick?.(c.name)}
                      className="card p-4 text-left hover:border-white/20 transition-colors cursor-pointer group"
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-bold text-[var(--text-muted)]">#{overallRank}</span>
                            <h4 className="text-sm font-semibold text-white group-hover:text-teal-400 transition-colors">{c.name}</h4>
                          </div>
                          <span className="text-[10px] text-[var(--text-muted)]">{c.vertical}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className={`text-[10px] font-semibold px-2 py-0.5 rounded ${getTierBg(c.tier)}`}>{c.tier}</span>
                          <span className="text-lg font-bold" style={{ color: cfg.color }}>{c.composite_score.toFixed(2)}</span>
                        </div>
                      </div>
                      <p className="text-[11px] text-[var(--text-secondary)] line-clamp-2 mb-2">{c.description}</p>
                      <div className="flex items-center gap-3 text-[10px] text-[var(--text-muted)]">
                        {topCat && (
                          <span>
                            <span className="text-emerald-400">▲</span> {topCat[0]}: {topCat[1].toFixed(2)}
                          </span>
                        )}
                        {weakCat && (
                          <span>
                            <span className="text-orange-400">▼</span> {weakCat[0]}: {weakCat[1].toFixed(2)}
                          </span>
                        )}
                        <span className="ml-auto">{c.employee_count} employees · Est. {c.founded_year}</span>
                      </div>
                    </button>
                  )
                })}
              </div>
            </div>
          )
        })}
      </section>

      {/* Section 6: AI Use Case Opportunities */}
      <section className="space-y-4">
        <SectionHeader icon={Zap} title="Cross-Portfolio AI Opportunities" subtitle="Recurring themes and shared patterns across verticals" />
        <div className="card p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {[
              {
                theme: 'Intelligent Document Processing',
                companies: ['SMRTR', 'Dash', 'Champ', 'TrackIt Transit'],
                desc: 'OCR/NLP-based extraction across invoices, health records, compliance documents, and transit forms. Shared IDP pipeline could serve 4+ portcos.',
                impact: 'High',
              },
              {
                theme: 'Predictive Analytics & Forecasting',
                companies: ['Track Star', 'ThingTech', 'FMSI', 'Spokane'],
                desc: 'ML models for fleet maintenance prediction, branch staffing optimization, produce demand forecasting, and asset lifecycle planning.',
                impact: 'High',
              },
              {
                theme: 'AI-Powered Speech & NLP',
                companies: ['NexTalk', 'Champ', 'FMSI'],
                desc: 'Speech-to-text (SpeechPath), clinical note summarization, and conversational AI for banking member interactions.',
                impact: 'Medium',
              },
              {
                theme: 'Compliance Automation',
                companies: ['AutoTime', 'Champ', 'SMRTR', 'TrackIt Transit'],
                desc: 'Automated DCAA audit trails, HIPAA compliance monitoring, food safety regulatory checks, and PTASP safety plan generation.',
                impact: 'Medium',
              },
              {
                theme: 'Route & Resource Optimization',
                companies: ['Cairn Applications', 'SMRTR', 'Track Star'],
                desc: 'AI-driven route optimization for waste hauling, F&B distribution, and fleet management — shared optimization engine.',
                impact: 'Medium',
              },
              {
                theme: 'Talent & Performance Intelligence',
                companies: ['ViaPeople', 'AutoTime'],
                desc: 'ML-driven performance insights, succession prediction, compensation benchmarking, and workforce planning analytics.',
                impact: 'Medium',
              },
            ].map(opp => (
              <div key={opp.theme} className="bg-white/[0.03] rounded-lg p-4 border border-white/[0.06]">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-xs font-semibold text-white">{opp.theme}</h4>
                  <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${
                    opp.impact === 'High' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-amber-500/20 text-amber-400'
                  }`}>{opp.impact} Impact</span>
                </div>
                <p className="text-[11px] text-[var(--text-secondary)] mb-2">{opp.desc}</p>
                <div className="flex flex-wrap gap-1">
                  {opp.companies.map(name => (
                    <button
                      key={name}
                      onClick={() => onCompanyClick?.(name)}
                      className="text-[9px] font-medium px-1.5 py-0.5 rounded bg-white/[0.06] text-[var(--text-muted)] hover:text-white hover:bg-white/[0.1] transition-colors cursor-pointer"
                    >
                      {name}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Section 7: Key Findings & Signals */}
      <section className="space-y-4">
        <SectionHeader icon={Shield} title="Key Research Findings" subtitle="Critical signals from public data collection" />
        <div className="card p-6">
          <div className="space-y-4">
            {[
              {
                signal: 'Solen Building AI Center of Excellence (COE)',
                detail: 'Solen is hiring a COE AI Software Engineer and COE Technical Lead in São Paulo, Brazil — building a shared AI engineering team to serve all portfolio companies. Combined with the CAIO role, this signals committed budget and organizational structure for AI transformation.',
                type: 'Organizational',
                strength: 'strong',
              },
              {
                signal: 'CAIO Role Validates Portfolio-Wide AI Strategy',
                detail: 'The Chief AI Officer job description explicitly calls for "identifying, scaling, and operationalizing practical AI use cases across a portfolio of vertical market software companies" with "shared AI patterns, frameworks, and reference architectures."',
                type: 'Strategic',
                strength: 'strong',
              },
              {
                signal: 'NexTalk SpeechPath: Most Advanced AI in Portfolio',
                detail: 'FCC-approved AI speech-to-text achieving industry-leading Word Error Rate. Real AI in production — not marketing claims. This is the strongest existing AI product across all 14 companies.',
                type: 'Product',
                strength: 'strong',
              },
              {
                signal: 'Track Star AI Video Telematics in Production',
                detail: 'AI-powered dash cameras detecting phone use, fatigue, tailgating, smoking, and seatbelt violations in real-time. Second-strongest existing AI product after NexTalk.',
                type: 'Product',
                strength: 'strong',
              },
              {
                signal: 'Spokane: Legacy AS/400 but Highest Product Differentiation',
                detail: '64% of US orange varieties and 80% of lemon varieties flow through the Spokane System. Extraordinary market lock-in (4.20 differentiation score) but AS/400/RPG architecture requires full modernization before AI.',
                type: 'Architecture',
                strength: 'mixed',
              },
              {
                signal: 'Zero Patents Across 13 of 14 Companies',
                detail: 'Patent scan confirmed these are execution-focused companies, not IP-driven. The value is in vertical domain expertise and customer lock-in, not defensible technology — aligning with PE value-creation thesis.',
                type: 'IP',
                strength: 'neutral',
              },
            ].map(f => (
              <div key={f.signal} className="flex gap-4">
                <div className={`w-2 rounded-full flex-shrink-0 ${
                  f.strength === 'strong' ? 'bg-emerald-400' : f.strength === 'mixed' ? 'bg-amber-400' : 'bg-blue-400'
                }`} />
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <h4 className="text-xs font-semibold text-white">{f.signal}</h4>
                    <span className="text-[9px] font-medium px-1.5 py-0.5 rounded bg-white/[0.06] text-[var(--text-muted)]">{f.type}</span>
                  </div>
                  <p className="text-[11px] text-[var(--text-secondary)] leading-relaxed">{f.detail}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Section 8: Data Sources & Methodology Confidence */}
      <section className="space-y-4">
        <SectionHeader icon={GitBranch} title="Data Sources & Confidence" subtitle="Evidence collection methodology and scoring reliability" />
        <div className="card p-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <h3 className="text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-3">Primary Sources</h3>
              <div className="space-y-1.5">
                {[
                  'Company websites & product pages',
                  'Press releases (BusinessWire, PRNewswire)',
                  'LinkedIn profiles & org charts',
                  'Regulatory filings (FCC, SEC, DCAA)',
                  'G2 / Capterra / Glassdoor reviews',
                  'Job postings (Indeed, Glassdoor, Breezy.hr)',
                  'Patent databases (USPTO, Google Patents)',
                  'Solen Software Group website',
                ].map(s => (
                  <div key={s} className="flex items-center gap-2">
                    <ChevronRight className="w-3 h-3 text-teal-400 flex-shrink-0" />
                    <span className="text-[11px] text-[var(--text-secondary)]">{s}</span>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <h3 className="text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-3">Validation Methods</h3>
              <div className="space-y-1.5">
                {[
                  'XGBoost 5-fold cross-validation (93.8%)',
                  'Leave-one-out backtesting on training set',
                  'Manual expert review of all 17×14 scores',
                  'Cross-reference vs Solen portfolio page',
                  'Entity verification (Dash correction)',
                  'v4 weight rebalancing for PE context',
                ].map(s => (
                  <div key={s} className="flex items-center gap-2">
                    <ChevronRight className="w-3 h-3 text-teal-400 flex-shrink-0" />
                    <span className="text-[11px] text-[var(--text-secondary)]">{s}</span>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <h3 className="text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-3">Confidence Notes</h3>
              <div className="space-y-1.5 text-[11px] text-[var(--text-secondary)]">
                <p>Average confidence across portfolio: <strong className="text-white">
                  {(portfolio.reduce((s, c) => s + ((c as any).confidence_score || 0), 0) / portfolio.length).toFixed(0)}%
                </strong></p>
                <p>Highest confidence: AutoTime, FMSI, Track Star (97%+) — extensive public evidence available.</p>
                <p>Lowest confidence: Dash (74%) — limited web presence post-merger. Thought Foundry (96%) — minimal public info but Solen-sourced data filled gaps.</p>
                <p className="text-[var(--text-muted)] mt-2 italic">
                  All evidence items include clickable source URLs for verification during interview walkthrough.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <div className="card p-6 border-teal-500/20">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold text-white">PE AI Intelligence Platform</h3>
            <p className="text-[10px] text-[var(--text-muted)]">Built for Solen Software Group CAIO Interview · Model v4.2 · {portfolio.length} Portfolio Companies · 17 Dimensions</p>
          </div>
          <div className="flex items-center gap-3">
            <a
              href="https://github.com/vgreco-code/pe-ai-intelligence"
              target="_blank"
              rel="noopener noreferrer"
              className="text-[10px] text-[var(--text-muted)] hover:text-white transition-colors flex items-center gap-1"
            >
              <ExternalLink className="w-3 h-3" /> Source Code
            </a>
          </div>
        </div>
      </div>
    </div>
  )
}

function SectionHeader({ icon: Icon, title, subtitle }: { icon: any; title: string; subtitle: string }) {
  return (
    <div className="flex items-center gap-3">
      <div className="w-8 h-8 rounded-lg flex items-center justify-center bg-white/[0.06]">
        <Icon className="w-4 h-4 text-teal-400" />
      </div>
      <div>
        <h2 className="text-lg font-semibold text-white">{title}</h2>
        <p className="text-[11px] text-[var(--text-muted)]">{subtitle}</p>
      </div>
    </div>
  )
}
