import React, { useState, useMemo } from 'react';
import { Building2, Users, Filter, ArrowUpDown } from 'lucide-react';
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
} from 'recharts';
import { PortfolioCompany } from '../App';

type TierType = 'AI-Ready' | 'AI-Buildable' | 'AI-Emerging' | 'AI-Limited';
type SortType = 'score' | 'name' | 'wave';

interface Props {
  portfolio: PortfolioCompany[];
}

const TIER_COLORS: Record<TierType, string> = {
  'AI-Ready': '#02C39A',
  'AI-Buildable': '#F5A623',
  'AI-Emerging': '#F24E1E',
  'AI-Limited': '#ef4444',
};

const PILLAR_LABELS = {
  DataQuality: 'DQ',
  WorkflowDigitization: 'WD',
  InfrastructureReadiness: 'IR',
  CloudPenetration: 'CP',
  RevenueUpsideOpportunity: 'RU',
  MarginUpsideOpportunity: 'MU',
  OperationalComplexity: 'OR',
  RegulatoryComplexity: 'RC',
};

const FULL_PILLAR_NAMES = {
  DataQuality: 'Data Quality',
  WorkflowDigitization: 'Workflow Digitization',
  InfrastructureReadiness: 'Infrastructure Readiness',
  CloudPenetration: 'Cloud Penetration',
  RevenueUpsideOpportunity: 'Revenue Upside Opportunity',
  MarginUpsideOpportunity: 'Margin Upside Opportunity',
  OperationalComplexity: 'Operational Complexity',
  RegulatoryComplexity: 'Regulatory Complexity',
};

const getPillarColor = (score: number): string => {
  if (score > 4) return '#02C39A';
  if (score > 3) return '#F5A623';
  if (score > 2) return '#F24E1E';
  return '#ef4444';
};

const getRecommendation = (tier: TierType): string => {
  switch (tier) {
    case 'AI-Ready':
      return 'High priority for immediate AI implementation. Strong fundamentals and readiness across all pillars.';
    case 'AI-Buildable':
      return 'Strong candidate for AI deployment with targeted improvements. Address key gaps in specific areas.';
    case 'AI-Emerging':
      return 'Moderate potential with significant development needed. Plan phased approach to AI integration.';
    case 'AI-Limited':
      return 'Requires substantial foundational work before AI deployment. Focus on core infrastructure improvements.';
  }
};

export default function Portfolio({ portfolio }: Props) {
  const [activeFilter, setActiveFilter] = useState<TierType | 'All'>('All');
  const [sortBy, setSortBy] = useState<SortType>('score');
  const [expandedCard, setExpandedCard] = useState<string | null>(null);

  const filteredAndSorted = useMemo(() => {
    let filtered = portfolio;

    if (activeFilter !== 'All') {
      filtered = portfolio.filter((company) => company.tier === activeFilter);
    }

    return filtered.sort((a, b) => {
      switch (sortBy) {
        case 'score':
          return b.compositeScore - a.compositeScore;
        case 'name':
          return a.name.localeCompare(b.name);
        case 'wave':
          return a.wave - b.wave;
        default:
          return 0;
      }
    });
  }, [portfolio, activeFilter, sortBy]);

  const radarData = (company: PortfolioCompany) => [
    {
      name: PILLAR_LABELS.DataQuality,
      value: company.pillars.DataQuality,
    },
    {
      name: PILLAR_LABELS.WorkflowDigitization,
      value: company.pillars.WorkflowDigitization,
    },
    {
      name: PILLAR_LABELS.InfrastructureReadiness,
      value: company.pillars.InfrastructureReadiness,
    },
    {
      name: PILLAR_LABELS.CloudPenetration,
      value: company.pillars.CloudPenetration,
    },
    {
      name: PILLAR_LABELS.RevenueUpsideOpportunity,
      value: company.pillars.RevenueUpsideOpportunity,
    },
    {
      name: PILLAR_LABELS.MarginUpsideOpportunity,
      value: company.pillars.MarginUpsideOpportunity,
    },
    {
      name: PILLAR_LABELS.OperationalComplexity,
      value: company.pillars.OperationalComplexity,
    },
    {
      name: PILLAR_LABELS.RegulatoryComplexity,
      value: company.pillars.RegulatoryComplexity,
    },
  ];

  return (
    <div className="min-h-screen bg-slate-950 text-white p-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-4 mb-2">
          <Building2 className="w-8 h-8 text-teal-400" />
          <h1 className="text-4xl font-bold">Portfolio Companies</h1>
          <span className="ml-2 bg-teal-900 text-teal-200 rounded-full px-4 py-1 text-lg font-semibold">
            {filteredAndSorted.length}
          </span>
        </div>
        <p className="text-slate-400 text-lg">
          AI Intelligence Analysis across {portfolio.length} portfolio companies
        </p>
      </div>

      {/* Filter and Sort Bar */}
      <div className="mb-8 flex flex-wrap gap-4 items-center">
        <div className="flex gap-2 items-center">
          <Filter className="w-5 h-5 text-slate-400" />
          <div className="flex gap-2 flex-wrap">
            {(['All', 'AI-Ready', 'AI-Buildable', 'AI-Emerging', 'AI-Limited'] as const).map((tier) => (
              <button
                key={tier}
                onClick={() => setActiveFilter(tier)}
                className={`px-4 py-2 rounded-full font-medium transition-all ${
                  activeFilter === tier
                    ? 'bg-teal-500 text-white'
                    : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                }`}
              >
                {tier}
              </button>
            ))}
          </div>
        </div>

        <div className="ml-auto flex gap-2 items-center">
          <ArrowUpDown className="w-5 h-5 text-slate-400" />
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as SortType)}
            className="px-4 py-2 bg-slate-800 text-white rounded-full font-medium cursor-pointer hover:bg-slate-700 transition-all"
          >
            <option value="score">By Score</option>
            <option value="name">By Name</option>
            <option value="wave">By Wave</option>
          </select>
        </div>
      </div>

      {/* Company Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredAndSorted.map((company, index) => (
          <div
            key={company.id}
            className={`stagger animate-fade-in-up`}
            style={{ animationDelay: `${index * 50}ms` }}
          >
            {expandedCard === company.id ? (
              // Expanded Detail View
              <div className="glass-card rounded-2xl p-8 border border-slate-700/50 bg-slate-900/50 backdrop-blur-xl">
                <button
                  onClick={() => setExpandedCard(null)}
                  className="mb-4 text-slate-400 hover:text-white transition-colors underline text-sm"
                >
                  ← Back to Grid
                </button>

                <div className="mb-6">
                  <h2 className="text-2xl font-bold mb-2">{company.name}</h2>
                  <span className="inline-block bg-slate-800 text-slate-300 rounded-full px-3 py-1 text-sm mb-4">
                    {company.vertical}
                  </span>

                  <div className="grid grid-cols-2 gap-4 mb-6">
                    <div>
                      <p className="text-slate-500 text-sm">Employees</p>
                      <p className="text-xl font-semibold flex items-center gap-2">
                        <Users className="w-5 h-5 text-teal-400" />
                        {company.employeeCount.toLocaleString()}
                      </p>
                    </div>
                    <div>
                      <p className="text-slate-500 text-sm">Composite Score</p>
                      <p className="text-xl font-semibold" style={{ color: TIER_COLORS[company.tier] }}>
                        {company.compositeScore.toFixed(2)}
                      </p>
                    </div>
                  </div>

                  <div className="flex gap-2 mb-6">
                    <span
                      className="rounded-full px-3 py-1 text-sm font-medium text-white"
                      style={{ backgroundColor: TIER_COLORS[company.tier] }}
                    >
                      {company.tier}
                    </span>
                    <span className="bg-slate-800 text-slate-300 rounded-full px-3 py-1 text-sm font-medium">
                      Wave {company.wave}
                    </span>
                  </div>
                </div>

                {/* Full Pillar Descriptions */}
                <div className="mb-6">
                  <h3 className="text-lg font-bold mb-4 text-slate-200">Pillar Analysis</h3>
                  <div className="space-y-4">
                    {Object.entries(company.pillars).map(([key, value]) => (
                      <div key={key}>
                        <div className="flex justify-between mb-2">
                          <span className="text-sm font-medium text-slate-300">
                            {FULL_PILLAR_NAMES[key as keyof typeof FULL_PILLAR_NAMES]}
                          </span>
                          <span className="text-sm font-semibold" style={{ color: getPillarColor(value) }}>
                            {value.toFixed(1)}/5.0
                          </span>
                        </div>
                        <div className="w-full bg-slate-800 rounded-full h-2">
                          <div
                            className="h-full rounded-full transition-all"
                            style={{
                              width: `${(value / 5) * 100}%`,
                              backgroundColor: getPillarColor(value),
                            }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Recommendation */}
                <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700/50">
                  <p className="text-sm text-slate-300">
                    <span className="font-semibold text-teal-400">Recommendation: </span>
                    {getRecommendation(company.tier)}
                  </p>
                </div>
              </div>
            ) : (
              // Collapsed Card View
              <button
                onClick={() => setExpandedCard(company.id)}
                className="glass-card rounded-2xl p-6 border border-slate-700/50 bg-slate-900/50 backdrop-blur-xl h-full hover:border-teal-500/50 transition-all cursor-pointer group"
              >
                {/* Company Name and Vertical */}
                <div className="mb-4">
                  <h3 className="text-xl font-bold mb-2 group-hover:text-teal-400 transition-colors">
                    {company.name}
                  </h3>
                  <span className="inline-block bg-slate-800 text-slate-400 rounded-full px-3 py-1 text-xs font-medium">
                    {company.vertical}
                  </span>
                </div>

                {/* Employee Count */}
                <div className="mb-4 flex items-center gap-2 text-sm text-slate-400">
                  <Users className="w-4 h-4" />
                  <span>{company.employeeCount.toLocaleString()} employees</span>
                </div>

                {/* Composite Score */}
                <div className="mb-4">
                  <p className="text-slate-500 text-xs font-medium mb-1">Composite Score</p>
                  <p
                    className="text-4xl font-bold"
                    style={{ color: TIER_COLORS[company.tier] }}
                  >
                    {company.compositeScore.toFixed(2)}
                  </p>
                </div>

                {/* Tier and Wave Badges */}
                <div className="flex gap-2 mb-6">
                  <span
                    className="rounded-full px-3 py-1 text-xs font-bold text-white"
                    style={{ backgroundColor: TIER_COLORS[company.tier] }}
                  >
                    {company.tier.replace('AI-', '')}
                  </span>
                  <span className="bg-slate-800 text-slate-300 rounded-full px-3 py-1 text-xs font-bold">
                    Wave {company.wave}
                  </span>
                </div>

                {/* Radar Chart */}
                <div className="mb-6 bg-slate-800/30 rounded-lg p-3">
                  <ResponsiveContainer width="100%" height={180}>
                    <RadarChart data={radarData(company)}>
                      <PolarGrid stroke="#334155" strokeDasharray="0" />
                      <PolarAngleAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                      <PolarRadiusAxis angle={90} domain={[0, 5]} tick={{ fill: '#64748b', fontSize: 10 }} />
                      <Radar
                        name="Score"
                        dataKey="value"
                        stroke="#02C39A"
                        fill="#02C39A"
                        fillOpacity={0.2}
                      />
                    </RadarChart>
                  </ResponsiveContainer>
                </div>

                {/* Pillar Score Bars */}
                <div className="space-y-3">
                  {Object.entries(company.pillars).map(([key, value]) => (
                    <div key={key}>
                      <div className="flex justify-between items-center mb-1">
                        <span className="text-xs font-semibold text-slate-400">
                          {PILLAR_LABELS[key as keyof typeof PILLAR_LABELS]}
                        </span>
                        <span className="text-xs font-bold" style={{ color: getPillarColor(value) }}>
                          {value.toFixed(1)}
                        </span>
                      </div>
                      <div className="w-full bg-slate-800 rounded-full h-1.5">
                        <div
                          className="h-full rounded-full transition-all"
                          style={{
                            width: `${(value / 5) * 100}%`,
                            backgroundColor: getPillarColor(value),
                          }}
                        />
                      </div>
                    </div>
                  ))}
                </div>

                {/* Expand Hint */}
                <div className="mt-4 text-center">
                  <p className="text-xs text-slate-500 group-hover:text-teal-400 transition-colors">
                    Click to expand
                  </p>
                </div>
              </button>
            )}
          </div>
        ))}
      </div>

      {/* Empty State */}
      {filteredAndSorted.length === 0 && (
        <div className="text-center py-16">
          <Building2 className="w-16 h-16 text-slate-700 mx-auto mb-4" />
          <p className="text-slate-400 text-lg">
            No companies found matching the selected filter.
          </p>
        </div>
      )}

      <style jsx>{`
        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .animate-fade-in-up {
          animation: fadeInUp 0.6s ease-out forwards;
        }

        .glass-card {
          background: linear-gradient(135deg, rgba(15, 23, 42, 0.8) 0%, rgba(2, 195, 154, 0.05) 100%);
        }
      `}</style>
    </div>
  );
}
