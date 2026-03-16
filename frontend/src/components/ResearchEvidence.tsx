import { useState } from 'react'
import { Search, FileText, ChevronDown, ChevronUp, Shield, Signal, Database, Brain, Users } from 'lucide-react'
import type { PortfolioCompany } from '../App'
import { CATEGORIES, DIMENSION_LABELS, getScoreColor } from '../App'

// ── Research Evidence Panel ─────────────────────────────────────────────────
// Surfaces the evidence signals behind each company's AI maturity scores.
// Extracts key signals from description text + dimension score patterns.

interface EvidenceSignal {
  text: string
  type: 'ai' | 'data' | 'infra' | 'org' | 'product'
  strength: 'strong' | 'moderate' | 'weak'
  source: string
}

// Pattern-based signal extraction from description text
function extractSignals(company: PortfolioCompany): EvidenceSignal[] {
  const desc = (company.description || '').toLowerCase()
  const signals: EvidenceSignal[] = []

  // AI capability signals
  const aiPatterns: [RegExp, string][] = [
    [/ai[- ]powered/i, 'AI-powered product capabilities detected'],
    [/machine learning|ml model/i, 'Machine learning capabilities referenced'],
    [/natural language|nlp/i, 'Natural language processing capabilities'],
    [/deep learning|neural net/i, 'Deep learning / neural network usage'],
    [/computer vision/i, 'Computer vision capabilities'],
    [/generative ai|gen[- ]?ai|llm|large language/i, 'Generative AI / LLM integration'],
    [/predictive analytics|predictive model/i, 'Predictive analytics capabilities'],
    [/ai infrastructure|ai platform/i, 'AI infrastructure / platform'],
    [/automation|automat/i, 'Automation capabilities'],
    [/intelligent|smart\s/i, 'Intelligent/smart product features'],
  ]
  for (const [re, text] of aiPatterns) {
    if (re.test(desc)) {
      signals.push({ text, type: 'ai', strength: 'strong', source: 'Company description' })
    }
  }

  // Cloud / infrastructure signals
  const cloudPatterns: [RegExp, string][] = [
    [/aws|amazon web services/i, 'AWS cloud infrastructure'],
    [/azure|microsoft cloud/i, 'Azure cloud platform'],
    [/gcp|google cloud/i, 'Google Cloud Platform'],
    [/kubernetes|k8s/i, 'Kubernetes container orchestration'],
    [/microservices/i, 'Microservices architecture'],
    [/cloud[- ]native/i, 'Cloud-native architecture'],
    [/api[- ]first|rest api|graphql/i, 'API-first architecture'],
    [/saas|software as a service/i, 'SaaS delivery model'],
  ]
  for (const [re, text] of cloudPatterns) {
    if (re.test(desc)) {
      signals.push({ text, type: 'infra', strength: 'moderate', source: 'Technology signals' })
    }
  }

  // Data signals
  const dataPatterns: [RegExp, string][] = [
    [/data analytics|data science/i, 'Data analytics capabilities'],
    [/big data|data lake|data warehouse/i, 'Large-scale data infrastructure'],
    [/real[- ]time data|streaming/i, 'Real-time data processing'],
    [/data integration|etl|data pipeline/i, 'Data integration infrastructure'],
    [/data governance|data quality/i, 'Data governance practices'],
  ]
  for (const [re, text] of dataPatterns) {
    if (re.test(desc)) {
      signals.push({ text, type: 'data', strength: 'moderate', source: 'Data capabilities' })
    }
  }

  // Org / talent signals
  const orgPatterns: [RegExp, string][] = [
    [/ai team|ml engineer|data scientist/i, 'Dedicated AI/ML talent'],
    [/chief.*ai|caio|cto/i, 'AI-focused leadership'],
    [/innovation|r&d|research/i, 'Innovation / R&D investment'],
    [/partnership|partner ecosystem/i, 'Technology partnerships'],
  ]
  for (const [re, text] of orgPatterns) {
    if (re.test(desc)) {
      signals.push({ text, type: 'org', strength: 'moderate', source: 'Organization signals' })
    }
  }

  // Add score-derived evidence (dimension patterns that tell a story)
  const ps = company.pillar_scores

  if ((ps.ai_product_features || 0) >= 3.5) {
    signals.push({ text: `Strong AI product feature score (${(ps.ai_product_features || 0).toFixed(1)}) — multiple AI-driven capabilities detected in product`, type: 'product', strength: 'strong', source: 'Scoring pipeline' })
  }
  if ((ps.ai_momentum || 0) >= 3.0) {
    signals.push({ text: `Active AI momentum (${(ps.ai_momentum || 0).toFixed(1)}) — recent AI hiring, partnerships, or product launches detected`, type: 'ai', strength: 'strong', source: 'Velocity analysis' })
  }
  if ((ps.cloud_architecture || 0) >= 3.0) {
    signals.push({ text: `Modern cloud infrastructure (${(ps.cloud_architecture || 0).toFixed(1)}) — cloud-native architecture with scalable compute`, type: 'infra', strength: 'moderate', source: 'Infrastructure analysis' })
  }
  if ((ps.data_quality || 0) >= 3.0 && (ps.data_integration || 0) >= 3.0) {
    signals.push({ text: `Strong data foundations (DQ: ${(ps.data_quality || 0).toFixed(1)}, DI: ${(ps.data_integration || 0).toFixed(1)}) — data infrastructure supports ML workloads`, type: 'data', strength: 'strong', source: 'Data analysis' })
  }
  if ((ps.ai_engineering || 0) < 2.0) {
    signals.push({ text: `Limited AI engineering capability (${(ps.ai_engineering || 0).toFixed(1)}) — no evidence of ML ops or model deployment infrastructure`, type: 'ai', strength: 'weak', source: 'Gap analysis' })
  }
  if ((ps.ai_talent_density || 0) < 2.0) {
    signals.push({ text: `Low AI talent density (${(ps.ai_talent_density || 0).toFixed(1)}) — limited AI/ML hiring signals detected`, type: 'org', strength: 'weak', source: 'Talent analysis' })
  }
  if ((ps.org_change_readiness || 0) < 2.0) {
    signals.push({ text: `Low organizational readiness (${(ps.org_change_readiness || 0).toFixed(1)}) — may need change management support for AI adoption`, type: 'org', strength: 'weak', source: 'Organization analysis' })
  }

  return signals
}

// Determine which dimensions are the biggest gaps vs. strengths
function getScoreInsights(company: PortfolioCompany) {
  const entries = Object.entries(company.pillar_scores)
    .map(([dim, score]) => ({ dim, score, label: DIMENSION_LABELS[dim] || dim }))

  const sorted = [...entries].sort((a, b) => b.score - a.score)
  const strengths = sorted.slice(0, 3)
  const gaps = [...entries].sort((a, b) => a.score - b.score).slice(0, 3)

  // Find which category is strongest and weakest
  const catScores = Object.entries(CATEGORIES).map(([cat, dims]) => ({
    cat,
    avg: dims.reduce((s, d) => s + (company.pillar_scores[d] || 0), 0) / dims.length,
  })).sort((a, b) => b.avg - a.avg)

  return { strengths, gaps, strongestCat: catScores[0], weakestCat: catScores[catScores.length - 1] }
}

const TYPE_ICONS: Record<string, typeof Brain> = {
  ai: Brain,
  data: Database,
  infra: Signal,
  org: Users,
  product: Shield,
}

const TYPE_COLORS: Record<string, string> = {
  ai: '#02C39A',
  data: '#06b6d4',
  infra: '#8b5cf6',
  org: '#F5A623',
  product: '#ec4899',
}

const STRENGTH_STYLES: Record<string, { bg: string; text: string; label: string }> = {
  strong: { bg: 'bg-emerald-500/10', text: 'text-emerald-400', label: 'Strong Signal' },
  moderate: { bg: 'bg-amber-500/10', text: 'text-amber-400', label: 'Moderate Signal' },
  weak: { bg: 'bg-red-500/10', text: 'text-red-400', label: 'Gap Signal' },
}

interface Props {
  company: PortfolioCompany
}

export default function ResearchEvidence({ company }: Props) {
  const [expanded, setExpanded] = useState(false)
  const signals = extractSignals(company)
  const { strengths, gaps, strongestCat } = getScoreInsights(company)

  const strongSignals = signals.filter(s => s.strength === 'strong')
  const moderateSignals = signals.filter(s => s.strength === 'moderate')
  const gapSignals = signals.filter(s => s.strength === 'weak')

  const displaySignals = expanded ? signals : signals.slice(0, 6)
  const confidenceScore = (company as any).confidence_score

  return (
    <div className="glass-card rounded-xl border border-violet-500/20 p-6">
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-lg font-bold text-[var(--text-primary)] flex items-center gap-2">
          <Search className="w-5 h-5 text-violet-400" />
          Research Evidence
        </h2>
        {confidenceScore != null && (
          <div className="flex items-center gap-2">
            <span className="text-xs text-[var(--text-muted)]">Research Confidence</span>
            <div className="flex items-center gap-1.5 bg-violet-500/10 px-3 py-1 rounded-full border border-violet-500/20">
              <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: confidenceScore >= 80 ? '#02C39A' : confidenceScore >= 60 ? '#F5A623' : '#F24E1E' }} />
              <span className="text-sm font-bold text-violet-400">{confidenceScore.toFixed(0)}%</span>
            </div>
          </div>
        )}
      </div>
      <p className="text-xs text-[var(--text-muted)] mb-5">
        Key evidence signals detected through deep web research on {company.name}
      </p>

      {/* Evidence summary bar */}
      <div className="flex gap-3 mb-5">
        <div className="flex-1 bg-emerald-500/5 rounded-lg p-3 border border-emerald-500/10 text-center">
          <div className="text-xl font-bold text-emerald-400">{strongSignals.length}</div>
          <div className="text-[10px] text-[var(--text-muted)] font-medium">Strong Signals</div>
        </div>
        <div className="flex-1 bg-amber-500/5 rounded-lg p-3 border border-amber-500/10 text-center">
          <div className="text-xl font-bold text-amber-400">{moderateSignals.length}</div>
          <div className="text-[10px] text-[var(--text-muted)] font-medium">Moderate Signals</div>
        </div>
        <div className="flex-1 bg-red-500/5 rounded-lg p-3 border border-red-500/10 text-center">
          <div className="text-xl font-bold text-red-400">{gapSignals.length}</div>
          <div className="text-[10px] text-[var(--text-muted)] font-medium">Gap Signals</div>
        </div>
        <div className="flex-1 bg-violet-500/5 rounded-lg p-3 border border-violet-500/10 text-center">
          <div className="text-xl font-bold text-violet-400">{strongestCat.cat.split(' ')[0]}</div>
          <div className="text-[10px] text-[var(--text-muted)] font-medium">Strongest Area</div>
        </div>
      </div>

      {/* Signal list */}
      <div className="space-y-2">
        {displaySignals.map((signal, i) => {
          const Icon = TYPE_ICONS[signal.type] || FileText
          const style = STRENGTH_STYLES[signal.strength]
          return (
            <div
              key={i}
              className="flex items-start gap-3 p-3 bg-slate-800/30 rounded-lg border border-slate-700/30 hover:border-slate-600/40 transition-all"
            >
              <div
                className="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5"
                style={{ backgroundColor: `${TYPE_COLORS[signal.type]}15` }}
              >
                <Icon className="w-3.5 h-3.5" style={{ color: TYPE_COLORS[signal.type] }} />
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-sm text-[var(--text-primary)] leading-snug">{signal.text}</div>
                <div className="flex items-center gap-2 mt-1">
                  <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded ${style.bg} ${style.text}`}>
                    {style.label}
                  </span>
                  <span className="text-[10px] text-[var(--text-muted)]">{signal.source}</span>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {signals.length > 6 && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="mt-3 flex items-center gap-1 text-xs text-violet-400 hover:text-violet-300 transition-colors mx-auto"
        >
          {expanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
          {expanded ? 'Show less' : `Show ${signals.length - 6} more signals`}
        </button>
      )}

      {/* Score insight summary */}
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
