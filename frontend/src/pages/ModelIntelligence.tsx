import { Brain, Target, Database, Activity, CheckCircle2, XCircle, Cpu, AlertCircle } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Cell } from 'recharts'
import {
  ModelMetrics, TrainingStats, DIMENSION_LABELS,
  CATEGORIES, CATEGORY_COLORS, TIER_COLORS, getTierBg,
} from '../App'

interface Props {
  metrics: ModelMetrics
  trainingStats: TrainingStats | null
}

const fmt = (n: number, d = 2) => n.toFixed(d)
const fmtPillar = (name: string) => DIMENSION_LABELS[name] || name.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())

export default function ModelIntelligence({ metrics, trainingStats }: Props) {
  const featureData = Object.entries(metrics.feature_importance)
    .map(([name, value]) => ({
      name: fmtPillar(name),
      value: parseFloat((value * 100).toFixed(2)),
      key: name,
    }))
    .sort((a, b) => b.value - a.value)

  // Category-level colors for bars
  const dimToCategory: Record<string, string> = {}
  Object.entries(CATEGORIES).forEach(([cat, dims]) => {
    dims.forEach(d => { dimToCategory[d] = cat })
  })

  const catImportance = Object.entries(CATEGORIES).map(([cat, dims]) => ({
    name: cat,
    value: parseFloat((dims.reduce((s, d) => s + (metrics.feature_importance[d] || 0), 0) * 100).toFixed(1)),
    fill: CATEGORY_COLORS[cat],
  })).sort((a, b) => b.value - a.value)

  const backtest = metrics.backtest_results || []

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold text-[var(--text-primary)] mb-2">Model Intelligence</h1>
        <div className="flex items-center gap-3">
          <Cpu className="w-5 h-5 text-cyan-400" />
          <span className="text-cyan-400 font-semibold px-3 py-1 bg-cyan-500/10 border border-cyan-500/30 rounded-full text-sm">
            XGBoost v{metrics.model_version} • {metrics.num_dimensions || 16} dimensions
          </span>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-5 gap-4">
        <div className="glass-card p-6 rounded-xl border border-teal-500/20">
          <div className="flex items-center justify-between mb-3">
            <p className="text-[var(--text-secondary)] text-sm">CV Accuracy</p>
            <Brain className="w-5 h-5 text-teal-400" />
          </div>
          <p className="text-3xl font-bold text-[var(--text-primary)]">{fmt(metrics.cv_accuracy * 100, 1)}%</p>
          <p className="text-xs text-[var(--text-muted)] mt-1">±{fmt(metrics.cv_std * 100, 2)}%</p>
        </div>
        <div className="glass-card p-6 rounded-xl border border-teal-500/20">
          <div className="flex items-center justify-between mb-3">
            <p className="text-[var(--text-secondary)] text-sm">Backtest Exact</p>
            <Target className="w-5 h-5 text-blue-400" />
          </div>
          <p className="text-3xl font-bold text-[var(--text-primary)]">{fmt(metrics.backtest_accuracy * 100, 1)}%</p>
          <p className="text-xs text-[var(--text-muted)] mt-1">{metrics.backtest_count || backtest.length} companies</p>
        </div>
        <div className="glass-card p-6 rounded-xl border border-teal-500/20">
          <div className="flex items-center justify-between mb-3">
            <p className="text-[var(--text-secondary)] text-sm">Adjacent Acc.</p>
            <CheckCircle2 className="w-5 h-5 text-emerald-400" />
          </div>
          <p className="text-3xl font-bold text-emerald-400">{fmt((metrics.backtest_adjacent_accuracy || 0) * 100, 1)}%</p>
          <p className="text-xs text-[var(--text-muted)] mt-1">Within 1 tier</p>
        </div>
        <div className="glass-card p-6 rounded-xl border border-teal-500/20">
          <div className="flex items-center justify-between mb-3">
            <p className="text-[var(--text-secondary)] text-sm">Training Set</p>
            <Database className="w-5 h-5 text-cyan-400" />
          </div>
          <p className="text-3xl font-bold text-[var(--text-primary)]">{metrics.training_set_size}</p>
          <p className="text-xs text-[var(--text-muted)] mt-1">{trainingStats?.verticals || '50+'}  verticals</p>
        </div>
        <div className="glass-card p-6 rounded-xl border border-teal-500/20">
          <div className="flex items-center justify-between mb-3">
            <p className="text-[var(--text-secondary)] text-sm">Avg Deviation</p>
            <Activity className="w-5 h-5 text-amber-400" />
          </div>
          <p className="text-3xl font-bold text-[var(--text-primary)]">{fmt(metrics.backtest_avg_deviation, 3)}</p>
          <p className="text-xs text-[var(--text-muted)] mt-1">Score points</p>
        </div>
      </div>

      {/* Feature Importance + Category */}
      <div className="grid grid-cols-2 gap-6">
        <div className="glass-card p-8 rounded-xl border border-teal-500/20">
          <h2 className="text-xl font-bold text-[var(--text-primary)] mb-6 flex items-center gap-2">
            <Target className="w-5 h-5 text-cyan-400" />
            Dimension Importance (16)
          </h2>
          <ResponsiveContainer width="100%" height={480}>
            <BarChart data={featureData} layout="vertical" margin={{ top: 5, right: 30, left: 150, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.1)" />
              <XAxis type="number" stroke="rgba(148, 163, 184, 0.5)" />
              <YAxis dataKey="name" type="category" width={145} stroke="rgba(148, 163, 184, 0.5)" tick={{ fontSize: 11, fill: 'rgba(148, 163, 184, 0.7)' }} />
              <Tooltip
                contentStyle={{ backgroundColor: 'rgba(15, 23, 42, 0.95)', border: '1px solid rgba(148, 163, 184, 0.2)', borderRadius: '8px' }}
                formatter={(v: number) => [`${fmt(v, 1)}%`, 'Importance']}
                labelStyle={{ color: 'rgba(226, 232, 240, 0.9)' }}
              />
              <Bar dataKey="value" radius={[0, 8, 8, 0]}>
                {featureData.map((entry, i) => (
                  <Cell key={i} fill={CATEGORY_COLORS[dimToCategory[entry.key]] || '#14b8a6'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="space-y-6">
          {/* Category Breakdown */}
          <div className="glass-card p-8 rounded-xl border border-teal-500/20">
            <h2 className="text-xl font-bold text-[var(--text-primary)] mb-6 flex items-center gap-2">
              <Activity className="w-5 h-5 text-blue-400" />
              Category Breakdown
            </h2>
            <div className="space-y-4">
              {catImportance.map(cat => (
                <div key={cat.name}>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm font-semibold" style={{ color: cat.fill }}>{cat.name}</span>
                    <span className="text-sm font-bold text-[var(--text-primary)]">{cat.value.toFixed(1)}%</span>
                  </div>
                  <div className="w-full bg-slate-700/50 rounded-full h-3">
                    <div className="h-full rounded-full transition-all" style={{ width: `${Math.min(cat.value * 2, 100)}%`, backgroundColor: cat.fill }} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Weight Comparison */}
          <div className="glass-card p-8 rounded-xl border border-teal-500/20">
            <h2 className="text-xl font-bold text-[var(--text-primary)] mb-4 flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-amber-400" />
              Derived vs Original Weights
            </h2>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {featureData.slice(0, 10).map(f => {
                const derived = metrics.derived_weights?.[f.key] || 0
                const original = metrics.original_weights?.[f.key] || 0
                const diff = derived - original
                return (
                  <div key={f.key} className="bg-slate-700/30 rounded-lg p-3 border border-slate-600/30">
                    <div className="flex items-center justify-between mb-1">
                      <p className="text-xs font-medium text-[var(--text-secondary)]">{f.name}</p>
                      <span className={`text-xs font-semibold ${diff > 0.05 ? 'text-emerald-400' : diff < -0.05 ? 'text-red-400' : 'text-slate-400'}`}>
                        {diff > 0 ? '+' : ''}{fmt(diff, 2)}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-[10px] text-[var(--text-muted)]">
                      <span>Original: {fmt(original, 2)}</span>
                      <span>Derived: {fmt(derived, 3)}</span>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Backtest Results */}
      <div className="glass-card p-8 rounded-xl border border-teal-500/20">
        <h2 className="text-xl font-bold text-[var(--text-primary)] mb-6 flex items-center gap-2">
          <Database className="w-5 h-5 text-teal-400" />
          Backtest Results ({backtest.length} companies)
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-600/50">
                <th className="px-4 py-3 text-left text-xs font-semibold text-[var(--text-secondary)]">Company</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-[var(--text-secondary)]">Vertical</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-[var(--text-secondary)]">Actual Tier</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-[var(--text-secondary)]">Predicted</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-[var(--text-secondary)]">Actual</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-[var(--text-secondary)]">Predicted</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-[var(--text-secondary)]">Dev</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-[var(--text-secondary)]">Result</th>
              </tr>
            </thead>
            <tbody>
              {backtest.map((r, i) => (
                <tr key={i} className={`border-b border-slate-600/20 hover:bg-slate-700/20 transition-colors ${i % 2 === 0 ? 'bg-slate-700/10' : ''}`}>
                  <td className="px-4 py-3 text-sm text-[var(--text-primary)]">{r.name}</td>
                  <td className="px-4 py-3 text-sm text-[var(--text-muted)]">{r.vertical}</td>
                  <td className="px-4 py-3"><span className={`px-2 py-1 rounded text-xs font-semibold ${getTierBg(r.actual_tier)}`}>{r.actual_tier}</span></td>
                  <td className="px-4 py-3"><span className={`px-2 py-1 rounded text-xs font-semibold ${getTierBg(r.predicted_tier)}`}>{r.predicted_tier}</span></td>
                  <td className="px-4 py-3 text-sm text-right text-[var(--text-secondary)]">{fmt(r.actual_score)}</td>
                  <td className="px-4 py-3 text-sm text-right text-[var(--text-secondary)]">{fmt(r.predicted_score)}</td>
                  <td className="px-4 py-3 text-sm text-right text-[var(--text-muted)]">{fmt(r.deviation, 3)}</td>
                  <td className="px-4 py-3 text-center">
                    {r.correct
                      ? <CheckCircle2 className="w-4 h-4 text-emerald-400 mx-auto" />
                      : r.adjacent_correct
                        ? <AlertCircle className="w-4 h-4 text-amber-400 mx-auto" />
                        : <XCircle className="w-4 h-4 text-red-400 mx-auto" />
                    }
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Architecture */}
      <div className="glass-card p-8 rounded-xl border border-teal-500/20">
        <h2 className="text-xl font-bold text-[var(--text-primary)] mb-6 flex items-center gap-2">
          <Cpu className="w-5 h-5 text-cyan-400" />
          Model Architecture
        </h2>
        <div className="grid grid-cols-6 gap-4">
          {[
            { label: 'Framework', value: 'XGBoost', color: 'text-cyan-400' },
            { label: 'CV Folds', value: '5', color: 'text-blue-400' },
            { label: 'Dimensions', value: '16', color: 'text-teal-400' },
            { label: 'Categories', value: '5', color: 'text-purple-400' },
            { label: 'Output', value: '4-Class', color: 'text-amber-400' },
            { label: 'Estimators', value: '150', color: 'text-pink-400' },
          ].map(item => (
            <div key={item.label} className="bg-slate-700/30 rounded-lg p-4 border border-slate-600/30">
              <p className="text-xs text-[var(--text-muted)] mb-2">{item.label}</p>
              <p className={`text-lg font-semibold ${item.color}`}>{item.value}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
