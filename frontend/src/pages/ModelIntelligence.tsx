import React from 'react';
import { Brain, Target, Database, Activity, ArrowUp, ArrowDown, CheckCircle2, XCircle, Cpu } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Cell } from 'recharts';
import { ModelMetrics, TrainingStats } from '../App';

interface Props {
  metrics: ModelMetrics;
  trainingStats: TrainingStats | null;
}

// Original weights mapping
const ORIGINAL_WEIGHTS: Record<string, number> = {
  'data_quality': 2,
  'workflow_digitization': 2,
  'infrastructure': 1.5,
  'competitive_position': 2,
  'revenue_upside': 1.5,
  'margin_upside': 1.5,
  'org_readiness': 1,
  'risk_compliance': 1,
};

// Tier colors
const TIER_COLORS: Record<string, string> = {
  'Tier 1': 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30',
  'Tier 2': 'bg-blue-500/20 text-blue-400 border border-blue-500/30',
  'Tier 3': 'bg-amber-500/20 text-amber-400 border border-amber-500/30',
  'Tier 4': 'bg-red-500/20 text-red-400 border border-red-500/30',
};

// Format pillar name (replace underscores with spaces, title case)
const formatPillarName = (name: string): string => {
  return name
    .replace(/_/g, ' ')
    .split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
};

// Format number with appropriate decimals
const formatNumber = (num: number, decimals: number = 2): string => {
  return num.toFixed(decimals);
};

export default function ModelIntelligence({ metrics, trainingStats }: Props) {
  // Prepare feature importance data sorted by importance descending
  const featureImportanceData = Object.entries(metrics.feature_importance)
    .map(([name, value]) => ({
      name: formatPillarName(name),
      value: parseFloat((value * 100).toFixed(2)),
      originalName: name,
    }))
    .sort((a, b) => b.value - a.value);

  // Gradient colors for feature importance bars
  const gradientColors = [
    '#14b8a6', // teal-500
    '#06b6d4', // cyan-500
    '#0ea5e9', // sky-500
    '#3b82f6', // blue-500
    '#1d4ed8', // blue-600
    '#1e40af', // blue-700
    '#1e3a8a', // blue-800
    '#0c2340', // blue-900
  ];

  // Backtest results data
  const backtestResults = metrics.backtest_results || [];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-8">
      {/* Header */}
      <div className="mb-12">
        <h1 className="text-4xl font-bold text-white mb-2">Model Intelligence</h1>
        <div className="flex items-center gap-3">
          <Cpu className="w-5 h-5 text-cyan-400" />
          <span className="text-cyan-400 font-semibold px-3 py-1 bg-cyan-500/10 border border-cyan-500/30 rounded-full text-sm">
            XGBoost v3.0
          </span>
        </div>
      </div>

      {/* KPI Cards - Model Performance */}
      <div className="grid grid-cols-4 gap-6 mb-12">
        {/* CV Accuracy */}
        <div className="glass-card p-6">
          <div className="flex items-center justify-between mb-4">
            <p className="text-slate-300 text-sm font-medium">CV Accuracy</p>
            <Brain className="w-5 h-5 text-teal-400" />
          </div>
          <p className="text-3xl font-bold text-white mb-2">
            {formatNumber(metrics.cv_accuracy * 100, 1)}%
          </p>
          <p className="text-xs text-slate-400">
            ±{formatNumber(metrics.cv_std * 100, 2)}%
          </p>
        </div>

        {/* Backtest Accuracy */}
        <div className="glass-card p-6">
          <div className="flex items-center justify-between mb-4">
            <p className="text-slate-300 text-sm font-medium">Backtest Accuracy</p>
            <Target className="w-5 h-5 text-blue-400" />
          </div>
          <p className="text-3xl font-bold text-white">
            {formatNumber(metrics.backtest_accuracy * 100, 1)}%
          </p>
        </div>

        {/* Training Samples */}
        <div className="glass-card p-6">
          <div className="flex items-center justify-between mb-4">
            <p className="text-slate-300 text-sm font-medium">Training Samples</p>
            <Database className="w-5 h-5 text-cyan-400" />
          </div>
          <p className="text-3xl font-bold text-white">
            {metrics.training_set_size.toLocaleString()}
          </p>
        </div>

        {/* Avg Deviation */}
        <div className="glass-card p-6">
          <div className="flex items-center justify-between mb-4">
            <p className="text-slate-300 text-sm font-medium">Avg Deviation</p>
            <Activity className="w-5 h-5 text-amber-400" />
          </div>
          <p className="text-3xl font-bold text-white">
            {formatNumber(metrics.backtest_avg_deviation, 3)}
          </p>
        </div>
      </div>

      {/* Two-column layout: Feature Importance + Derived Weights */}
      <div className="grid grid-cols-[1fr_1fr] gap-8 mb-12" style={{ gridTemplateColumns: '1fr 0.82fr' }}>
        {/* Feature Importance Chart */}
        <div className="glass-card p-8">
          <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
            <Target className="w-5 h-5 text-cyan-400" />
            Feature Importance
          </h2>
          <ResponsiveContainer width="100%" height={320}>
            <BarChart
              data={featureImportanceData}
              layout="vertical"
              margin={{ top: 5, right: 30, left: 180, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.1)" />
              <XAxis type="number" stroke="rgba(148, 163, 184, 0.5)" />
              <YAxis dataKey="name" type="category" width={175} stroke="rgba(148, 163, 184, 0.5)" tick={{ fontSize: 12, fill: 'rgba(148, 163, 184, 0.7)' }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'rgba(15, 23, 42, 0.95)',
                  border: '1px solid rgba(148, 163, 184, 0.2)',
                  borderRadius: '8px',
                }}
                formatter={(value) => `${formatNumber(value as number, 1)}%`}
                labelStyle={{ color: 'rgba(226, 232, 240, 0.9)' }}
              />
              <Bar dataKey="value" fill="#0ea5e9" radius={[0, 8, 8, 0]}>
                {featureImportanceData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={gradientColors[index % gradientColors.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Derived Weights */}
        <div className="glass-card p-8">
          <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
            <Activity className="w-5 h-5 text-blue-400" />
            Weight Comparison
          </h2>
          <div className="space-y-3 max-h-80 overflow-y-auto">
            {featureImportanceData.map((feature, idx) => {
              const derivedWeight = metrics.derived_weights[feature.originalName] || 0;
              const originalWeight = ORIGINAL_WEIGHTS[feature.originalName] || 0;
              const isIncrease = derivedWeight > originalWeight;
              const difference = Math.abs(derivedWeight - originalWeight);

              return (
                <div key={idx} className="bg-slate-700/30 rounded-lg p-3 border border-slate-600/30">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-sm font-medium text-slate-200">{feature.name}</p>
                    <div className="flex items-center gap-2">
                      {isIncrease ? (
                        <ArrowUp className="w-4 h-4 text-green-400" />
                      ) : (
                        <ArrowDown className="w-4 h-4 text-red-400" />
                      )}
                      <span className={`text-xs font-semibold ${isIncrease ? 'text-green-400' : 'text-red-400'}`}>
                        {isIncrease ? '+' : '-'}{formatNumber(difference, 2)}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between text-xs text-slate-400">
                    <span>Original: {formatNumber(originalWeight, 2)}</span>
                    <span>Derived: {formatNumber(derivedWeight, 2)}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Backtest Results Table */}
      <div className="glass-card p-8 mb-12">
        <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
          <Database className="w-5 h-5 text-teal-400" />
          Backtest Results
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-600/50">
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-300">Company</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-300">Vertical</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-300">Actual Tier</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-300">Predicted Tier</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-300">Actual Score</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-300">Predicted Score</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-300">Deviation</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-slate-300">Result</th>
              </tr>
            </thead>
            <tbody>
              {backtestResults.map((result, idx) => {
                const isCorrect = result.actual_tier === result.predicted_tier;
                const rowClass = idx % 2 === 0 ? 'bg-slate-700/10' : 'bg-transparent';

                return (
                  <tr key={idx} className={`${rowClass} border-b border-slate-600/20 hover:bg-slate-700/20 transition-colors`}>
                    <td className="px-4 py-3 text-sm text-slate-200">{result.company}</td>
                    <td className="px-4 py-3 text-sm text-slate-400">{result.vertical}</td>
                    <td className="px-4 py-3 text-sm">
                      <span className={`px-2 py-1 rounded text-xs font-semibold ${TIER_COLORS[result.actual_tier]}`}>
                        {result.actual_tier}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm">
                      <span className={`px-2 py-1 rounded text-xs font-semibold ${TIER_COLORS[result.predicted_tier]}`}>
                        {result.predicted_tier}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-right text-slate-300">{formatNumber(result.actual_score, 2)}</td>
                    <td className="px-4 py-3 text-sm text-right text-slate-300">{formatNumber(result.predicted_score, 2)}</td>
                    <td className="px-4 py-3 text-sm text-right text-slate-400">{formatNumber(result.deviation, 3)}</td>
                    <td className="px-4 py-3 text-center">
                      {isCorrect ? (
                        <CheckCircle2 className="w-4 h-4 text-green-400 mx-auto" />
                      ) : (
                        <XCircle className="w-4 h-4 text-red-400 mx-auto" />
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        {backtestResults.length === 0 && (
          <div className="text-center py-8 text-slate-400">
            <p>No backtest results available</p>
          </div>
        )}
      </div>

      {/* Model Architecture Card */}
      <div className="glass-card p-8">
        <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
          <Cpu className="w-5 h-5 text-cyan-400" />
          Model Architecture
        </h2>
        <div className="grid grid-cols-5 gap-6">
          <div className="bg-slate-700/30 rounded-lg p-4 border border-slate-600/30">
            <p className="text-xs text-slate-400 font-medium mb-2">Framework</p>
            <p className="text-lg font-semibold text-cyan-400">XGBoost</p>
          </div>
          <div className="bg-slate-700/30 rounded-lg p-4 border border-slate-600/30">
            <p className="text-xs text-slate-400 font-medium mb-2">CV Folds</p>
            <p className="text-lg font-semibold text-blue-400">5</p>
          </div>
          <div className="bg-slate-700/30 rounded-lg p-4 border border-slate-600/30">
            <p className="text-xs text-slate-400 font-medium mb-2">Features</p>
            <p className="text-lg font-semibold text-teal-400">8 Pillars</p>
          </div>
          <div className="bg-slate-700/30 rounded-lg p-4 border border-slate-600/30">
            <p className="text-xs text-slate-400 font-medium mb-2">Output</p>
            <p className="text-lg font-semibold text-purple-400">4-Class</p>
          </div>
          <div className="bg-slate-700/30 rounded-lg p-4 border border-slate-600/30">
            <p className="text-xs text-slate-400 font-medium mb-2">Objective</p>
            <p className="text-lg font-semibold text-amber-400">multi:softmax</p>
          </div>
        </div>
      </div>
    </div>
  );
}
