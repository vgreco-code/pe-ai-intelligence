import React from 'react';
import {
  Building2,
  TrendingUp,
  Brain,
  Database,
  Layers,
  Zap,
} from 'lucide-react';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';
import { PortfolioCompany, ModelMetrics, TrainingStats, WaveData } from '../App';

interface Props {
  portfolio: PortfolioCompany[];
  metrics: ModelMetrics | null;
  trainingStats: TrainingStats | null;
  waveData: WaveData;
}

const getTierColor = (tier: string): string => {
  switch (tier) {
    case 'AI-Ready':
      return '#02C39A';
    case 'AI-Buildable':
      return '#F5A623';
    case 'AI-Emerging':
      return '#F24E1E';
    case 'AI-Limited':
      return '#ef4444';
    default:
      return '#6B7280';
  }
};

const getTierBgColor = (tier: string): string => {
  switch (tier) {
    case 'AI-Ready':
      return 'bg-emerald-500/20 text-emerald-400';
    case 'AI-Buildable':
      return 'bg-amber-500/20 text-amber-400';
    case 'AI-Emerging':
      return 'bg-orange-500/20 text-orange-400';
    case 'AI-Limited':
      return 'bg-red-500/20 text-red-400';
    default:
      return 'bg-gray-500/20 text-gray-400';
  }
};

export default function Dashboard(props: Props) {
  const { portfolio, metrics, trainingStats, waveData } = props;

  const portfolioCount = portfolio.length;
  const avgAIScore =
    portfolio.length > 0
      ? (portfolio.reduce((sum, c) => sum + c.composite_score, 0) /
          portfolio.length).toFixed(2)
      : '0.00';

  const modelAccuracy = metrics
    ? (metrics.cv_accuracy * 100).toFixed(1)
    : '0.0';

  const trainingSetCount = trainingStats?.total_companies || 0;

  const sortedPortfolio = [...portfolio].sort(
    (a, b) => b.composite_score - a.composite_score
  );

  const tierDistribution = portfolio.reduce(
    (acc, company) => {
      const tierName = company.tier;
      const existing = acc.find((t) => t.name === tierName);
      if (existing) {
        existing.value += 1;
      } else {
        acc.push({ name: tierName, value: 1 });
      }
      return acc;
    },
    [] as Array<{ name: string; value: number }>
  );

  const featureImportanceData = metrics
    ? metrics.feature_importance.map((weight, index) => ({
        name: `Pillar ${index + 1}`,
        value: parseFloat((weight * 100).toFixed(1)),
      }))
    : [];

  const waveTimingData = [
    {
      name: 'Wave 1',
      companies: waveData.wave_1_count,
      scoreRange: waveData.wave_1_score_range,
    },
    {
      name: 'Wave 2',
      companies: waveData.wave_2_count,
      scoreRange: waveData.wave_2_score_range,
    },
    {
      name: 'Wave 3',
      companies: waveData.wave_3_count,
      scoreRange: waveData.wave_3_score_range,
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-8">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="stagger">
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-5xl font-bold text-[var(--text-primary)] mb-2">
                AI Investment Intelligence
              </h1>
              <p className="text-xl text-[var(--text-secondary)]">
                Solen Software Group — Portfolio AI Readiness Platform
              </p>
            </div>
            <div className="glass-card px-4 py-2 rounded-lg text-sm text-teal-400 border border-teal-500/30">
              Model v3.0 • 515 companies trained
            </div>
          </div>
        </div>

        {/* KPI Row */}
        <div className="grid grid-cols-4 gap-6 stagger">
          {/* Portfolio Companies KPI */}
          <div className="glass-card p-6 rounded-xl border border-teal-500/20 hover:border-teal-500/40 transition-all duration-300">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-[var(--text-secondary)] text-sm font-medium">
                Portfolio Companies
              </h3>
              <Building2 className="w-5 h-5 text-teal-400" />
            </div>
            <div className="text-4xl font-bold text-[var(--text-primary)]">
              {portfolioCount}
            </div>
            <p className="text-xs text-[var(--text-secondary)] mt-2">
              Active investments
            </p>
          </div>

          {/* Avg AI Score KPI */}
          <div className="glass-card p-6 rounded-xl border border-teal-500/20 hover:border-teal-500/40 transition-all duration-300">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-[var(--text-secondary)] text-sm font-medium">
                Avg AI Score
              </h3>
              <TrendingUp className="w-5 h-5 text-teal-400" />
            </div>
            <div className="text-4xl font-bold text-[var(--text-primary)]">
              {avgAIScore}
            </div>
            <div className="mt-3 h-2 bg-slate-700 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-teal-500 to-emerald-400"
                style={{ width: `${parseFloat(avgAIScore) * 10}%` }}
              />
            </div>
          </div>

          {/* Model Accuracy KPI */}
          <div className="glass-card p-6 rounded-xl border border-teal-500/20 hover:border-teal-500/40 transition-all duration-300">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-[var(--text-secondary)] text-sm font-medium">
                Model Accuracy
              </h3>
              <Brain className="w-5 h-5 text-teal-400" />
            </div>
            <div className="text-4xl font-bold text-[var(--text-primary)]">
              {modelAccuracy}%
            </div>
            <p className="text-xs text-[var(--text-secondary)] mt-2">
              Cross-validation
            </p>
          </div>

          {/* Training Set KPI */}
          <div className="glass-card p-6 rounded-xl border border-teal-500/20 hover:border-teal-500/40 transition-all duration-300">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-[var(--text-secondary)] text-sm font-medium">
                Training Set
              </h3>
              <Database className="w-5 h-5 text-teal-400" />
            </div>
            <div className="text-4xl font-bold text-[var(--text-primary)]">
              {trainingSetCount}
            </div>
            <p className="text-xs text-[var(--text-secondary)] mt-2">
              Companies analyzed
            </p>
          </div>
        </div>

        {/* Two-Column Layout */}
        <div className="grid grid-cols-3 gap-6 stagger">
          {/* Left Column - Portfolio Scoreboard */}
          <div className="col-span-2">
            <div className="glass-card rounded-xl border border-teal-500/20 p-6">
              <h2 className="text-xl font-bold text-[var(--text-primary)] mb-4 flex items-center gap-2">
                <Layers className="w-5 h-5 text-teal-400" />
                Portfolio Scoreboard
              </h2>
              <div className="space-y-3 max-h-96 overflow-y-auto custom-scrollbar">
                {sortedPortfolio.map((company, index) => (
                  <div
                    key={company.id}
                    className="flex items-center gap-4 p-3 hover:bg-slate-800/30 rounded-lg transition-colors duration-200"
                  >
                    <div className="text-sm font-bold text-teal-400 w-6">
                      {index + 1}
                    </div>
                    <div className="flex-1">
                      <div className="font-medium text-[var(--text-primary)]">
                        {company.name}
                      </div>
                      <div className="text-xs text-[var(--text-secondary)]">
                        {company.vertical}
                      </div>
                    </div>
                    <div className="flex-1">
                      <div className="relative h-2 bg-slate-700 rounded-full overflow-hidden">
                        <div
                          className="h-full transition-all duration-300"
                          style={{
                            width: `${company.composite_score * 10}%`,
                            backgroundColor: getTierColor(company.tier),
                          }}
                        />
                      </div>
                    </div>
                    <div className="w-16 text-right">
                      <span className="text-sm font-bold text-[var(--text-primary)]">
                        {company.composite_score.toFixed(2)}
                      </span>
                    </div>
                    <div className={`px-3 py-1 rounded-full text-xs font-medium ${getTierBgColor(company.tier)}`}>
                      {company.tier}
                    </div>
                    <div className="px-3 py-1 rounded-full text-xs font-medium bg-slate-700/50 text-slate-300">
                      {company.wave}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Right Column - Tier Distribution & Wave Sequencing */}
          <div className="space-y-6">
            {/* Tier Distribution */}
            <div className="glass-card rounded-xl border border-teal-500/20 p-6">
              <h2 className="text-lg font-bold text-[var(--text-primary)] mb-4 flex items-center gap-2">
                <Zap className="w-5 h-5 text-teal-400" />
                Tier Distribution
              </h2>
              <div style={{ height: '200px' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={tierDistribution}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={90}
                      paddingAngle={2}
                      dataKey="value"
                    >
                      {tierDistribution.map((entry, index) => (
                        <Cell
                          key={`cell-${index}`}
                          fill={getTierColor(entry.name)}
                        />
                      ))}
                    </Pie>
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="mt-4 space-y-2 text-sm">
                {tierDistribution.map((tier) => (
                  <div key={tier.name} className="flex justify-between items-center">
                    <div className="flex items-center gap-2">
                      <div
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: getTierColor(tier.name) }}
                      />
                      <span className="text-[var(--text-secondary)]">
                        {tier.name}
                      </span>
                    </div>
                    <span className="font-bold text-[var(--text-primary)]">
                      {tier.value}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Wave Sequencing */}
            <div className="glass-card rounded-xl border border-teal-500/20 p-6">
              <h2 className="text-lg font-bold text-[var(--text-primary)] mb-4 flex items-center gap-2">
                <Layers className="w-5 h-5 text-teal-400" />
                Wave Sequencing
              </h2>
              <div className="space-y-3">
                {waveTimingData.map((wave) => (
                  <div key={wave.name} className="space-y-1">
                    <div className="flex justify-between items-center text-sm">
                      <span className="font-medium text-[var(--text-primary)]">
                        {wave.name}
                      </span>
                      <span className="text-teal-400 font-bold">
                        {wave.companies} companies
                      </span>
                    </div>
                    <div className="text-xs text-[var(--text-secondary)]">
                      Score: {wave.scoreRange}
                    </div>
                    <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-teal-500 to-emerald-400"
                        style={{
                          width: `${(wave.companies / portfolioCount) * 100}%`,
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Feature Importance Chart */}
        <div className="glass-card rounded-xl border border-teal-500/20 p-8 stagger">
          <h2 className="text-xl font-bold text-[var(--text-primary)] mb-6 flex items-center gap-2">
            <Brain className="w-5 h-5 text-teal-400" />
            Feature Importance Analysis
          </h2>
          <div style={{ height: '300px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={featureImportanceData}
                layout="vertical"
                margin={{ top: 5, right: 30, left: 150, bottom: 5 }}
              >
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="rgba(15, 23, 42, 0.5)"
                />
                <XAxis type="number" stroke="rgba(107, 114, 128, 0.6)" />
                <YAxis
                  dataKey="name"
                  type="category"
                  width={140}
                  stroke="rgba(107, 114, 128, 0.6)"
                  tick={{ fontSize: 12, fill: 'rgba(107, 114, 128, 0.8)' }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'rgba(15, 23, 42, 0.95)',
                    border: '1px solid rgba(20, 184, 166, 0.2)',
                    borderRadius: '8px',
                  }}
                  cursor={{ fill: 'rgba(20, 184, 166, 0.1)' }}
                  formatter={(value) => [`${value.toFixed(1)}%`, 'Weight']}
                />
                <Bar
                  dataKey="value"
                  fill="url(#colorGradient)"
                  radius={[0, 8, 8, 0]}
                  animationDuration={800}
                >
                  <defs>
                    <linearGradient id="colorGradient" x1="0" y1="0" x2="1" y2="0">
                      <stop offset="0%" stopColor="#14b8a6" />
                      <stop offset="100%" stopColor="#06b6d4" />
                    </linearGradient>
                  </defs>
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-4 text-xs text-[var(--text-secondary)]">
            These weights represent the relative importance of each pillar in the
            AI readiness model prediction.
          </div>
        </div>
      </div>

      <style jsx>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 6px;
        }

        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }

        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(20, 184, 166, 0.3);
          border-radius: 3px;
        }

        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgba(20, 184, 166, 0.5);
        }
      `}</style>
    </div>
  );
}
