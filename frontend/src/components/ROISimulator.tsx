import { useState, useMemo } from 'react'
import { Zap, ChevronDown, ChevronUp, Sparkles, Calculator } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, CartesianGrid } from 'recharts'
import type { PortfolioCompany } from '../App'
import { TIER_COLORS, getTierBg } from '../App'

interface Props {
  portfolio: PortfolioCompany[]
}

// ── PE valuation assumptions ───────────────────────────────────────────────
// These are reasonable SaaS multiples for Solen's mid-market vertical SaaS portcos

const WAVE_DEFAULTS = {
  1: { revenueUplift: 15, marginImprovement: 8, timeToValue: '6-12 mo', investmentPct: 3 },
  2: { revenueUplift: 8, marginImprovement: 5, timeToValue: '12-18 mo', investmentPct: 5 },
  3: { revenueUplift: 3, marginImprovement: 2, timeToValue: '18-30 mo', investmentPct: 8 },
}

// Estimated revenue tiers based on employee count (rough SaaS heuristic: $150-250K rev/employee)
function estimateRevenue(company: PortfolioCompany): number {
  const revPerEmployee = company.vertical.includes('SaaS') || company.vertical.includes('Software')
    ? 200000
    : 180000
  return company.employee_count * revPerEmployee
}

function formatDollars(val: number): string {
  if (val >= 1e9) return `$${(val / 1e9).toFixed(1)}B`
  if (val >= 1e6) return `$${(val / 1e6).toFixed(1)}M`
  if (val >= 1e3) return `$${(val / 1e3).toFixed(0)}K`
  return `$${val.toFixed(0)}`
}

export default function ROISimulator({ portfolio }: Props) {
  const [expanded, setExpanded] = useState(true)
  const [ebitdaMultiple, setEbitdaMultiple] = useState(12)
  const [baseMargin, setBaseMargin] = useState(25)
  const [w1RevUplift, setW1RevUplift] = useState(WAVE_DEFAULTS[1].revenueUplift)
  const [w2RevUplift, setW2RevUplift] = useState(WAVE_DEFAULTS[2].revenueUplift)
  const [w3RevUplift, setW3RevUplift] = useState(WAVE_DEFAULTS[3].revenueUplift)
  const [w1MarginImp, setW1MarginImp] = useState(WAVE_DEFAULTS[1].marginImprovement)
  const [w2MarginImp, setW2MarginImp] = useState(WAVE_DEFAULTS[2].marginImprovement)
  const [w3MarginImp, setW3MarginImp] = useState(WAVE_DEFAULTS[3].marginImprovement)

  const analysis = useMemo(() => {
    const companies = portfolio.map(c => {
      const estRevenue = estimateRevenue(c)
      const wave = c.wave as 1 | 2 | 3
      const revUplift = wave === 1 ? w1RevUplift : wave === 2 ? w2RevUplift : w3RevUplift
      const marginImp = wave === 1 ? w1MarginImp : wave === 2 ? w2MarginImp : w3MarginImp

      const newRevenue = estRevenue * (1 + revUplift / 100)
      const revenueGain = newRevenue - estRevenue
      const currentEbitda = estRevenue * (baseMargin / 100)
      const newEbitda = newRevenue * ((baseMargin + marginImp) / 100)
      const ebitdaGain = newEbitda - currentEbitda
      const valueCreation = ebitdaGain * ebitdaMultiple

      return {
        name: c.name,
        wave: c.wave,
        tier: c.tier,
        score: c.composite_score,
        estRevenue,
        revenueGain,
        currentEbitda,
        newEbitda,
        ebitdaGain,
        valueCreation,
        revUplift,
        marginImp,
      }
    }).sort((a, b) => b.valueCreation - a.valueCreation)

    const totalCurrentRevenue = companies.reduce((s, c) => s + c.estRevenue, 0)
    const totalRevenueGain = companies.reduce((s, c) => s + c.revenueGain, 0)
    const totalCurrentEbitda = companies.reduce((s, c) => s + c.currentEbitda, 0)
    const totalNewEbitda = companies.reduce((s, c) => s + c.newEbitda, 0)
    const totalEbitdaGain = companies.reduce((s, c) => s + c.ebitdaGain, 0)
    const totalValueCreation = companies.reduce((s, c) => s + c.valueCreation, 0)

    const wave1Value = companies.filter(c => c.wave === 1).reduce((s, c) => s + c.valueCreation, 0)
    const wave2Value = companies.filter(c => c.wave === 2).reduce((s, c) => s + c.valueCreation, 0)
    const wave3Value = companies.filter(c => c.wave === 3).reduce((s, c) => s + c.valueCreation, 0)

    return {
      companies,
      totalCurrentRevenue,
      totalRevenueGain,
      totalCurrentEbitda,
      totalNewEbitda,
      totalEbitdaGain,
      totalValueCreation,
      wave1Value,
      wave2Value,
      wave3Value,
    }
  }, [portfolio, ebitdaMultiple, baseMargin, w1RevUplift, w2RevUplift, w3RevUplift, w1MarginImp, w2MarginImp, w3MarginImp])

  const chartData = analysis.companies.map(c => ({
    name: c.name,
    value: c.valueCreation,
    tier: c.tier,
  }))

  const waveChartData = [
    { name: 'Wave 1', value: analysis.wave1Value, color: '#02C39A' },
    { name: 'Wave 2', value: analysis.wave2Value, color: '#F5A623' },
    { name: 'Wave 3', value: analysis.wave3Value, color: '#94a3b8' },
  ]

  return (
    <div className="glass-card rounded-2xl border border-purple-500/20 overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full p-6 flex items-center justify-between hover:bg-white/[0.02] transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: 'linear-gradient(135deg, rgba(168,85,247,0.2), rgba(2,195,154,0.2))' }}>
            <Calculator className="w-5 h-5 text-purple-400" />
          </div>
          <div className="text-left">
            <h2 className="text-xl font-bold text-[var(--text-primary)] flex items-center gap-2">
              AI Value Creation Simulator
              <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-purple-500/15 text-purple-400 uppercase tracking-wider">
                Interactive
              </span>
            </h2>
            <p className="text-xs text-[var(--text-muted)] mt-0.5">
              Model portfolio-level returns from AI investments across waves
            </p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-right">
            <div className="text-xs text-[var(--text-muted)]">Est. Total Value Creation</div>
            <div className="text-2xl font-bold text-purple-400">{formatDollars(analysis.totalValueCreation)}</div>
          </div>
          {expanded ? <ChevronUp className="w-5 h-5 text-[var(--text-muted)]" /> : <ChevronDown className="w-5 h-5 text-[var(--text-muted)]" />}
        </div>
      </button>

      {expanded && (
        <div className="px-6 pb-6 space-y-6">
          {/* KPI Row */}
          <div className="grid grid-cols-5 gap-3">
            <div className="bg-slate-800/40 rounded-xl p-4 border border-slate-700/30 text-center">
              <div className="text-[10px] uppercase tracking-wider text-[var(--text-muted)] mb-1">Est. Portfolio Revenue</div>
              <div className="text-lg font-bold text-[var(--text-primary)]">{formatDollars(analysis.totalCurrentRevenue)}</div>
            </div>
            <div className="bg-slate-800/40 rounded-xl p-4 border border-slate-700/30 text-center">
              <div className="text-[10px] uppercase tracking-wider text-[var(--text-muted)] mb-1">Revenue Uplift</div>
              <div className="text-lg font-bold text-emerald-400">+{formatDollars(analysis.totalRevenueGain)}</div>
            </div>
            <div className="bg-slate-800/40 rounded-xl p-4 border border-slate-700/30 text-center">
              <div className="text-[10px] uppercase tracking-wider text-[var(--text-muted)] mb-1">Current EBITDA</div>
              <div className="text-lg font-bold text-[var(--text-primary)]">{formatDollars(analysis.totalCurrentEbitda)}</div>
            </div>
            <div className="bg-slate-800/40 rounded-xl p-4 border border-slate-700/30 text-center">
              <div className="text-[10px] uppercase tracking-wider text-[var(--text-muted)] mb-1">EBITDA Gain</div>
              <div className="text-lg font-bold text-emerald-400">+{formatDollars(analysis.totalEbitdaGain)}</div>
            </div>
            <div className="bg-purple-500/10 rounded-xl p-4 border border-purple-500/30 text-center">
              <div className="text-[10px] uppercase tracking-wider text-purple-300 mb-1">Enterprise Value Add</div>
              <div className="text-lg font-bold text-purple-400">{formatDollars(analysis.totalValueCreation)}</div>
              <div className="text-[10px] text-[var(--text-muted)]">at {ebitdaMultiple}x EBITDA</div>
            </div>
          </div>

          {/* Controls */}
          <div className="grid grid-cols-3 gap-4">
            {/* Global Assumptions */}
            <div className="bg-slate-800/30 rounded-xl p-4 border border-slate-700/30">
              <h3 className="text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-3">
                Valuation Assumptions
              </h3>
              <div className="space-y-3">
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-[var(--text-secondary)]">EBITDA Multiple</span>
                    <span className="font-bold text-[var(--text-primary)]">{ebitdaMultiple}x</span>
                  </div>
                  <input type="range" min="6" max="20" step="1" value={ebitdaMultiple} onChange={e => setEbitdaMultiple(+e.target.value)}
                    className="w-full h-1.5 rounded-full appearance-none bg-slate-700 cursor-pointer accent-purple-500" />
                  <div className="flex justify-between text-[9px] text-[var(--text-muted)] mt-0.5"><span>6x</span><span>20x</span></div>
                </div>
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-[var(--text-secondary)]">Base EBITDA Margin</span>
                    <span className="font-bold text-[var(--text-primary)]">{baseMargin}%</span>
                  </div>
                  <input type="range" min="10" max="45" step="1" value={baseMargin} onChange={e => setBaseMargin(+e.target.value)}
                    className="w-full h-1.5 rounded-full appearance-none bg-slate-700 cursor-pointer accent-purple-500" />
                  <div className="flex justify-between text-[9px] text-[var(--text-muted)] mt-0.5"><span>10%</span><span>45%</span></div>
                </div>
              </div>
            </div>

            {/* Wave 1 Controls */}
            <div className="bg-slate-800/30 rounded-xl p-4 border border-emerald-500/20">
              <h3 className="text-xs font-semibold text-emerald-400 uppercase tracking-wider mb-3 flex items-center gap-1.5">
                <Zap className="w-3 h-3" /> Wave 1 — Deploy Now
              </h3>
              <div className="space-y-3">
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-[var(--text-secondary)]">Revenue Uplift</span>
                    <span className="font-bold text-emerald-400">+{w1RevUplift}%</span>
                  </div>
                  <input type="range" min="0" max="30" step="1" value={w1RevUplift} onChange={e => setW1RevUplift(+e.target.value)}
                    className="w-full h-1.5 rounded-full appearance-none bg-slate-700 cursor-pointer accent-emerald-500" />
                </div>
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-[var(--text-secondary)]">Margin Improvement</span>
                    <span className="font-bold text-emerald-400">+{w1MarginImp}pp</span>
                  </div>
                  <input type="range" min="0" max="15" step="1" value={w1MarginImp} onChange={e => setW1MarginImp(+e.target.value)}
                    className="w-full h-1.5 rounded-full appearance-none bg-slate-700 cursor-pointer accent-emerald-500" />
                </div>
                <div className="text-[10px] text-[var(--text-muted)] pt-1 border-t border-slate-700/50">
                  Value: <span className="font-bold text-emerald-400">{formatDollars(analysis.wave1Value)}</span> · {portfolio.filter(c => c.wave === 1).length} companies · 6-12 mo
                </div>
              </div>
            </div>

            {/* Wave 2+3 Controls */}
            <div className="space-y-3">
              <div className="bg-slate-800/30 rounded-xl p-3 border border-amber-500/20">
                <h3 className="text-[10px] font-semibold text-amber-400 uppercase tracking-wider mb-2 flex items-center gap-1">
                  Wave 2 — Build Foundation
                </h3>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <div className="flex justify-between text-[10px] mb-0.5">
                      <span className="text-[var(--text-muted)]">Rev</span>
                      <span className="font-bold text-amber-400">+{w2RevUplift}%</span>
                    </div>
                    <input type="range" min="0" max="20" step="1" value={w2RevUplift} onChange={e => setW2RevUplift(+e.target.value)}
                      className="w-full h-1 rounded-full appearance-none bg-slate-700 cursor-pointer accent-amber-500" />
                  </div>
                  <div>
                    <div className="flex justify-between text-[10px] mb-0.5">
                      <span className="text-[var(--text-muted)]">Margin</span>
                      <span className="font-bold text-amber-400">+{w2MarginImp}pp</span>
                    </div>
                    <input type="range" min="0" max="12" step="1" value={w2MarginImp} onChange={e => setW2MarginImp(+e.target.value)}
                      className="w-full h-1 rounded-full appearance-none bg-slate-700 cursor-pointer accent-amber-500" />
                  </div>
                </div>
                <div className="text-[9px] text-[var(--text-muted)] mt-1">
                  Value: <span className="font-bold text-amber-400">{formatDollars(analysis.wave2Value)}</span> · {portfolio.filter(c => c.wave === 2).length} companies
                </div>
              </div>
              <div className="bg-slate-800/30 rounded-xl p-3 border border-slate-500/20">
                <h3 className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1">
                  Wave 3 — Groundwork
                </h3>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <div className="flex justify-between text-[10px] mb-0.5">
                      <span className="text-[var(--text-muted)]">Rev</span>
                      <span className="font-bold text-slate-400">+{w3RevUplift}%</span>
                    </div>
                    <input type="range" min="0" max="15" step="1" value={w3RevUplift} onChange={e => setW3RevUplift(+e.target.value)}
                      className="w-full h-1 rounded-full appearance-none bg-slate-700 cursor-pointer accent-slate-400" />
                  </div>
                  <div>
                    <div className="flex justify-between text-[10px] mb-0.5">
                      <span className="text-[var(--text-muted)]">Margin</span>
                      <span className="font-bold text-slate-400">+{w3MarginImp}pp</span>
                    </div>
                    <input type="range" min="0" max="8" step="1" value={w3MarginImp} onChange={e => setW3MarginImp(+e.target.value)}
                      className="w-full h-1 rounded-full appearance-none bg-slate-700 cursor-pointer accent-slate-400" />
                  </div>
                </div>
                <div className="text-[9px] text-[var(--text-muted)] mt-1">
                  Value: <span className="font-bold text-slate-400">{formatDollars(analysis.wave3Value)}</span> · {portfolio.filter(c => c.wave === 3).length} companies
                </div>
              </div>
            </div>
          </div>

          {/* Charts Row */}
          <div className="grid grid-cols-3 gap-4">
            {/* Value creation by company */}
            <div className="col-span-2 bg-slate-800/30 rounded-xl p-4 border border-slate-700/30">
              <h3 className="text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-3">
                Value Creation by Company
              </h3>
              <div style={{ height: '280px' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData} layout="vertical" margin={{ left: 100, right: 60, top: 5, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" horizontal={false} />
                    <XAxis type="number" tick={{ fill: 'rgba(148,163,184,0.5)', fontSize: 10 }}
                      tickFormatter={(v: number) => formatDollars(v)} />
                    <YAxis dataKey="name" type="category" width={95}
                      tick={{ fill: 'rgba(148,163,184,0.7)', fontSize: 10 }} />
                    <Tooltip
                      contentStyle={{ background: '#1a2744', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8 }}
                      labelStyle={{ color: 'white', fontWeight: 600 }}
                      formatter={(v: number) => [formatDollars(v), 'Value Add']}
                    />
                    <Bar dataKey="value" radius={[0, 4, 4, 0]} barSize={16}>
                      {chartData.map((entry, i) => (
                        <Cell key={i} fill={TIER_COLORS[entry.tier] || '#6B7280'} fillOpacity={0.8} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Wave breakdown */}
            <div className="bg-slate-800/30 rounded-xl p-4 border border-slate-700/30">
              <h3 className="text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-3">
                Value by Wave
              </h3>
              <div style={{ height: '200px' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={waveChartData} margin={{ left: 10, right: 10, top: 5, bottom: 5 }}>
                    <XAxis dataKey="name" tick={{ fill: 'rgba(148,163,184,0.7)', fontSize: 10 }} axisLine={false} />
                    <YAxis tick={{ fill: 'rgba(148,163,184,0.5)', fontSize: 9 }}
                      tickFormatter={(v: number) => formatDollars(v)} axisLine={false} />
                    <Tooltip
                      contentStyle={{ background: '#1a2744', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8 }}
                      formatter={(v: number) => [formatDollars(v), 'Value']}
                    />
                    <Bar dataKey="value" radius={[4, 4, 0, 0]} barSize={40}>
                      {waveChartData.map((entry, i) => (
                        <Cell key={i} fill={entry.color} fillOpacity={0.7} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Wave % breakdown */}
              <div className="mt-3 space-y-1.5">
                {waveChartData.map(w => {
                  const pct = analysis.totalValueCreation > 0 ? (w.value / analysis.totalValueCreation) * 100 : 0
                  return (
                    <div key={w.name} className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full" style={{ backgroundColor: w.color }} />
                      <span className="text-[10px] text-[var(--text-secondary)] flex-1">{w.name}</span>
                      <span className="text-[10px] font-bold" style={{ color: w.color }}>{pct.toFixed(0)}%</span>
                    </div>
                  )
                })}
              </div>
            </div>
          </div>

          {/* Company-level detail table */}
          <div className="bg-slate-800/30 rounded-xl border border-slate-700/30 overflow-hidden">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-slate-700/30">
                  <th className="text-left py-2.5 px-4 text-[var(--text-muted)] font-semibold uppercase tracking-wider">Company</th>
                  <th className="text-center py-2.5 px-2 text-[var(--text-muted)] font-semibold uppercase tracking-wider">Wave</th>
                  <th className="text-center py-2.5 px-2 text-[var(--text-muted)] font-semibold uppercase tracking-wider">Score</th>
                  <th className="text-right py-2.5 px-3 text-[var(--text-muted)] font-semibold uppercase tracking-wider">Est. Revenue</th>
                  <th className="text-right py-2.5 px-3 text-[var(--text-muted)] font-semibold uppercase tracking-wider">Rev Uplift</th>
                  <th className="text-right py-2.5 px-3 text-[var(--text-muted)] font-semibold uppercase tracking-wider">EBITDA Gain</th>
                  <th className="text-right py-2.5 px-4 text-[var(--text-muted)] font-semibold uppercase tracking-wider">Value Add</th>
                </tr>
              </thead>
              <tbody>
                {analysis.companies.map((c, i) => (
                  <tr key={c.name} className={`border-b border-slate-700/20 ${i % 2 === 0 ? 'bg-white/[0.01]' : ''} hover:bg-white/[0.03] transition-colors`}>
                    <td className="py-2 px-4 font-medium text-[var(--text-primary)]">
                      <div className="flex items-center gap-2">
                        <span>{c.name}</span>
                        <span className={`text-[9px] font-semibold px-1.5 py-0.5 rounded-full ${getTierBg(c.tier)}`}>
                          {c.tier.replace('AI-', '')}
                        </span>
                      </div>
                    </td>
                    <td className="py-2 px-2 text-center">
                      <span className="font-bold" style={{ color: c.wave === 1 ? '#02C39A' : c.wave === 2 ? '#F5A623' : '#94a3b8' }}>
                        W{c.wave}
                      </span>
                    </td>
                    <td className="py-2 px-2 text-center font-bold text-[var(--text-primary)]">{c.score.toFixed(2)}</td>
                    <td className="py-2 px-3 text-right text-[var(--text-secondary)]">{formatDollars(c.estRevenue)}</td>
                    <td className="py-2 px-3 text-right text-emerald-400">+{formatDollars(c.revenueGain)}</td>
                    <td className="py-2 px-3 text-right text-emerald-400">+{formatDollars(c.ebitdaGain)}</td>
                    <td className="py-2 px-4 text-right font-bold text-purple-400">{formatDollars(c.valueCreation)}</td>
                  </tr>
                ))}
                <tr className="bg-purple-500/5 border-t-2 border-purple-500/30">
                  <td className="py-3 px-4 font-bold text-[var(--text-primary)]" colSpan={3}>Portfolio Total</td>
                  <td className="py-3 px-3 text-right font-bold text-[var(--text-primary)]">{formatDollars(analysis.totalCurrentRevenue)}</td>
                  <td className="py-3 px-3 text-right font-bold text-emerald-400">+{formatDollars(analysis.totalRevenueGain)}</td>
                  <td className="py-3 px-3 text-right font-bold text-emerald-400">+{formatDollars(analysis.totalEbitdaGain)}</td>
                  <td className="py-3 px-4 text-right font-bold text-purple-400 text-sm">{formatDollars(analysis.totalValueCreation)}</td>
                </tr>
              </tbody>
            </table>
          </div>

          {/* CAIO Insight */}
          <div className="bg-purple-500/5 rounded-xl p-4 border border-purple-500/15">
            <div className="flex items-start gap-3">
              <Sparkles className="w-4 h-4 text-purple-400 mt-0.5 flex-shrink-0" />
              <div className="text-xs text-[var(--text-secondary)] leading-relaxed">
                <span className="font-semibold text-purple-400">CAIO Insight: </span>
                At a {ebitdaMultiple}x EBITDA multiple with {baseMargin}% base margins, AI-driven improvements across the portfolio
                project <span className="font-bold text-purple-400">{formatDollars(analysis.totalValueCreation)}</span> in enterprise value creation.
                {analysis.wave1Value > analysis.wave2Value + analysis.wave3Value
                  ? ` Wave 1 companies drive ${((analysis.wave1Value / analysis.totalValueCreation) * 100).toFixed(0)}% of total value — confirming the prioritization thesis.`
                  : ` Wave 2 companies represent the largest value pool — foundational investments today unlock the majority of returns.`
                }
                {' '}Revenue uplift from AI product features compounds with margin improvement from operational AI, creating a dual value lever at exit.
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
