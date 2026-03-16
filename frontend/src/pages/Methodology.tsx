import { DIMENSION_LABELS, CATEGORIES, CATEGORY_COLORS } from '../App'

const WEIGHTS: Record<string, number> = {
  data_quality: 1.10, data_integration: 1.00, analytics_maturity: 1.20,
  cloud_architecture: 0.80, tech_stack_modernity: 0.60, ai_engineering: 1.00,
  ai_product_features: 2.80, revenue_ai_upside: 1.50, margin_ai_upside: 0.80,
  product_differentiation: 0.70, ai_talent_density: 1.80, leadership_ai_vision: 1.50,
  org_change_readiness: 0.80, partner_ecosystem: 0.90, ai_governance: 0.50,
  regulatory_readiness: 0.50, ai_momentum: 0.80,
}

const TOTAL_WEIGHT = Object.values(WEIGHTS).reduce((a, b) => a + b, 0)

export default function Methodology() {
  const sortedDims = Object.entries(WEIGHTS).sort((a, b) => b[1] - a[1])

  const getCategoryForDim = (dim: string): string => {
    for (const [cat, dims] of Object.entries(CATEGORIES)) {
      if (dims.includes(dim)) return cat
    }
    return ''
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white mb-2">Scoring Methodology</h1>
        <p className="text-[var(--text-secondary)] text-sm max-w-3xl">
          How the AI Maturity Model scores, tiers, and prioritizes Solen's portfolio companies for AI investment.
        </p>
      </div>

      {/* Overview */}
      <div className="card p-6">
        <h2 className="text-lg font-semibold text-white mb-3">Model Overview</h2>
        <div className="text-sm text-[var(--text-secondary)] space-y-3 max-w-3xl">
          <p>
            The AI Maturity Model evaluates each portfolio company across <strong className="text-white">17 dimensions</strong> grouped
            into <strong className="text-white">6 categories</strong>. Each dimension is scored 1.0–5.0 based on web-verified evidence
            from company websites, press releases, job postings, regulatory filings, and industry databases.
          </p>
          <p>
            Dimension scores are combined into a <strong className="text-white">weighted composite score</strong> that determines
            the company's tier classification and implementation wave. Weights are derived from XGBoost feature importance
            analysis (v3) and then manually rebalanced (v4) to correct for scraping artifacts and ensure domain-expert sensibility.
          </p>
          <p>
            An <strong className="text-white">Execution Capacity Factor (ECF)</strong> gates talent and engineering dimensions
            by company size, acknowledging that PE portfolio companies leverage Solen's shared services platform rather than
            maintaining large in-house AI teams.
          </p>
        </div>
      </div>

      {/* Dimension Weights */}
      <div className="card p-6">
        <h2 className="text-lg font-semibold text-white mb-1">v4 Dimension Weights</h2>
        <p className="text-xs text-[var(--text-muted)] mb-4">
          Rebalanced from XGBoost-derived v3 weights. Total weight: {TOTAL_WEIGHT.toFixed(1)}. Higher weight = greater influence on composite score.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {sortedDims.map(([dim, weight]) => {
            const pct = (weight / TOTAL_WEIGHT) * 100
            const cat = getCategoryForDim(dim)
            const color = CATEGORY_COLORS[cat] || '#6b7280'
            return (
              <div key={dim} className="flex items-center gap-3">
                <div className="w-28 text-xs text-[var(--text-secondary)] truncate" title={dim}>
                  {DIMENSION_LABELS[dim] || dim}
                </div>
                <div className="flex-1 h-5 bg-white/[0.04] rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all"
                    style={{ width: `${Math.min(pct * 3.5, 100)}%`, background: color }}
                  />
                </div>
                <div className="w-12 text-right text-xs font-mono text-[var(--text-secondary)]">
                  {weight.toFixed(2)}
                </div>
                <div className="w-12 text-right text-xs font-mono text-[var(--text-muted)]">
                  {pct.toFixed(1)}%
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Categories */}
      <div className="card p-6">
        <h2 className="text-lg font-semibold text-white mb-4">Scoring Categories</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Object.entries(CATEGORIES).map(([cat, dims]) => {
            const catWeight = dims.reduce((sum, d) => sum + (WEIGHTS[d] || 0), 0)
            const catPct = (catWeight / TOTAL_WEIGHT) * 100
            return (
              <div key={cat} className="p-4 rounded-xl border border-white/[0.06] bg-white/[0.02]">
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-3 h-3 rounded-full" style={{ background: CATEGORY_COLORS[cat] }} />
                  <h3 className="text-sm font-semibold text-white">{cat}</h3>
                </div>
                <div className="text-xs text-[var(--text-muted)] mb-2">
                  {catPct.toFixed(1)}% of composite • {dims.length} dimension{dims.length > 1 ? 's' : ''}
                </div>
                <div className="space-y-1">
                  {dims.map(d => (
                    <div key={d} className="flex justify-between text-xs">
                      <span className="text-[var(--text-secondary)]">{DIMENSION_LABELS[d]}</span>
                      <span className="font-mono text-[var(--text-muted)]">{WEIGHTS[d]?.toFixed(2)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Tier Classification */}
      <div className="card p-6">
        <h2 className="text-lg font-semibold text-white mb-4">Tier Classification</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { tier: 'AI-Ready', range: '≥ 3.50', color: '#02C39A', desc: 'Strong AI foundation. Deploy immediately with targeted investments.' },
            { tier: 'AI-Buildable', range: '2.80 – 3.49', color: '#F5A623', desc: 'Solid base with gaps. Build foundation over 6-12 months, then deploy AI.' },
            { tier: 'AI-Emerging', range: '2.00 – 2.79', color: '#F24E1E', desc: 'Early stage. Significant infrastructure and capability building needed (12-24 months).' },
            { tier: 'AI-Limited', range: '< 2.00', color: '#ef4444', desc: 'Major gaps. Full modernization required before AI is feasible.' },
          ].map(t => (
            <div key={t.tier} className="p-4 rounded-xl border border-white/[0.06]" style={{ background: `${t.color}10` }}>
              <div className="text-sm font-bold mb-1" style={{ color: t.color }}>{t.tier}</div>
              <div className="text-xs font-mono text-[var(--text-secondary)] mb-2">{t.range}</div>
              <p className="text-xs text-[var(--text-muted)]">{t.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Wave Sequencing */}
      <div className="card p-6">
        <h2 className="text-lg font-semibold text-white mb-4">Implementation Waves</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            { wave: 1, range: '≥ 3.00', label: 'Deploy Now', color: '#02C39A', desc: 'AI-ready for investment. Prioritize for immediate AI feature development and market positioning.' },
            { wave: 2, range: '2.65 – 2.99', label: 'Build Foundation', color: '#F5A623', desc: 'Invest in data infrastructure, cloud modernization, and talent before deploying AI features (6-12 months).' },
            { wave: 3, range: '< 2.65', label: 'Groundwork', color: '#F24E1E', desc: 'Requires significant modernization investment. Focus on tech stack, data quality, and organizational readiness (12-24 months).' },
          ].map(w => (
            <div key={w.wave} className="p-4 rounded-xl border border-white/[0.06]" style={{ background: `${w.color}10` }}>
              <div className="flex items-center gap-2 mb-1">
                <span className="text-lg font-bold" style={{ color: w.color }}>Wave {w.wave}</span>
                <span className="text-xs font-mono text-[var(--text-muted)]">{w.range}</span>
              </div>
              <div className="text-sm font-semibold text-white mb-1">{w.label}</div>
              <p className="text-xs text-[var(--text-muted)]">{w.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* ECF */}
      <div className="card p-6">
        <h2 className="text-lg font-semibold text-white mb-3">Execution Capacity Factor (ECF)</h2>
        <div className="text-sm text-[var(--text-secondary)] space-y-3 max-w-3xl">
          <p>
            PE portfolio companies are typically small (5–50 employees) and don't maintain dedicated AI teams.
            The ECF adjusts talent and engineering dimension expectations based on company size, with a floor
            of <strong className="text-white">0.65</strong> to avoid over-penalizing sub-15-employee companies.
          </p>
          <p>
            This reflects the reality that Solen provides shared services — portfolio companies can access
            centralized AI engineering and data science resources rather than building everything in-house.
          </p>
          <div className="font-mono text-xs bg-white/[0.04] p-3 rounded-lg border border-white/[0.06]">
            <div className="text-[var(--text-muted)] mb-1">ECF Formula:</div>
            <div>ECF = max(0.65, min(1.0, 0.5 + emp_count / 200))</div>
            <div className="text-[var(--text-muted)] mt-1">Applied to: ai_talent_density, ai_engineering</div>
          </div>
        </div>
      </div>

      {/* Audit Methodology */}
      <div className="card p-6">
        <h2 className="text-lg font-semibold text-white mb-3">Audit & Validation</h2>
        <div className="text-sm text-[var(--text-secondary)] space-y-3 max-w-3xl">
          <p>
            Scores are initially generated via automated web scraping (Tavily API) and then undergo
            <strong className="text-white"> three rounds of manual audit</strong> cross-referencing each dimension
            against primary sources:
          </p>
          <div className="space-y-2 ml-4">
            <div className="flex gap-2">
              <span className="text-[var(--teal)] font-bold">v4.0</span>
              <span>Rebalanced XGBoost weights, corrected entity confusion (Dash), fixed Tavily keyword contamination for 8 companies</span>
            </div>
            <div className="flex gap-2">
              <span className="text-[var(--teal)] font-bold">v4.1</span>
              <span>Cross-checked all dimensions ≥4.0 against evidence. Corrected Primate (SCADA ≠ AI), ThingTech (Salesforce ≠ own cloud), TrackIt (forms ≠ AI)</span>
            </div>
            <div className="flex gap-2">
              <span className="text-[var(--teal)] font-bold">v4.2</span>
              <span>Fresh web research on company sites. Verified SMRTR shows no ML (AP automation only), FMSI uses partner AI (Appli + Posh), ViaPeople's AI Insights is LLM-wrapped</span>
            </div>
          </div>
          <p>
            <strong className="text-white">Key principle:</strong> Every score ≥4.0 must be justified by specific, verifiable evidence.
            Only three ≥4.0 scores remain: NexTalk's FCC-certified ASR (4.20), Dash's AWS Advanced Tech Partner status (4.00),
            and Spokane's citrus market monopoly (4.20). All companies with real shipping AI rank in the top 4.
          </p>
        </div>
      </div>

      {/* Data Sources */}
      <div className="card p-6">
        <h2 className="text-lg font-semibold text-white mb-3">Data Sources</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {[
            { source: 'Company Websites', desc: 'Product pages, feature lists, tech documentation' },
            { source: 'Press Releases', desc: 'Acquisitions, partnerships, product launches' },
            { source: 'LinkedIn', desc: 'Executive backgrounds, team composition, job postings' },
            { source: 'Regulatory Filings', desc: 'FCC certifications, NERC compliance, SOC 2 reports' },
            { source: 'Solen Portfolio Page', desc: 'Company descriptions, leadership quotes, investment thesis' },
            { source: 'Industry Databases', desc: 'Crunchbase, PitchBook, D&B, AppExchange listings' },
          ].map(s => (
            <div key={s.source} className="p-3 rounded-lg bg-white/[0.03] border border-white/[0.06]">
              <div className="text-xs font-semibold text-white mb-1">{s.source}</div>
              <div className="text-xs text-[var(--text-muted)]">{s.desc}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
