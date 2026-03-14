import React, { useState, useMemo } from 'react';
import {
  Database,
  Search,
  Filter,
  Building2,
  Users,
  Calendar,
  Cloud,
  Cpu,
  TrendingUp,
  ArrowUpDown,
  ChevronDown,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Cell,
} from 'recharts';
import { TrainingCompany } from '../App';

interface Props {
  companies: TrainingCompany[];
}

const TIER_COLORS: Record<string, string> = {
  'AI-Ready': '#02C39A',
  'AI-Buildable': '#F5A623',
  'AI-Emerging': '#F24E1E',
  'AI-Limited': '#ef4444',
};

export default function TrainingExplorer({ companies }: Props) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTier, setSelectedTier] = useState<string | null>(null);
  const [sortOption, setSortOption] = useState<string>('score-desc');
  const [displayedRows, setDisplayedRows] = useState(50);

  // Calculate stats
  const uniqueVerticals = useMemo(() => {
    return new Set(companies.map((c) => c.vertical)).size;
  }, [companies]);

  const avgScore = useMemo(() => {
    if (companies.length === 0) return 0;
    const sum = companies.reduce((acc, c) => acc + c.composite_score, 0);
    return (sum / companies.length).toFixed(2);
  }, [companies]);

  const scoreRange = useMemo(() => {
    if (companies.length === 0) return { min: 0, max: 0 };
    const scores = companies.map((c) => c.composite_score);
    return {
      min: Math.min(...scores).toFixed(2),
      max: Math.max(...scores).toFixed(2),
    };
  }, [companies]);

  // Count tiers
  const tierCounts = useMemo(() => {
    return {
      'AI-Ready': companies.filter((c) => c.tier === 'AI-Ready').length,
      'AI-Buildable': companies.filter((c) => c.tier === 'AI-Buildable').length,
      'AI-Emerging': companies.filter((c) => c.tier === 'AI-Emerging').length,
      'AI-Limited': companies.filter((c) => c.tier === 'AI-Limited').length,
    };
  }, [companies]);

  // Filter and sort companies
  const filteredAndSorted = useMemo(() => {
    let filtered = companies.filter((company) => {
      const matchesSearch =
        searchTerm === '' ||
        company.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        company.vertical.toLowerCase().includes(searchTerm.toLowerCase());

      const matchesTier = selectedTier === null || company.tier === selectedTier;

      return matchesSearch && matchesTier;
    });

    // Sort
    switch (sortOption) {
      case 'score-desc':
        filtered.sort((a, b) => b.composite_score - a.composite_score);
        break;
      case 'score-asc':
        filtered.sort((a, b) => a.composite_score - b.composite_score);
        break;
      case 'name-asc':
        filtered.sort((a, b) => a.name.localeCompare(b.name));
        break;
      case 'employees':
        filtered.sort((a, b) => (b.employees || 0) - (a.employees || 0));
        break;
      case 'founded':
        filtered.sort((a, b) => (b.founded_year || 0) - (a.founded_year || 0));
        break;
      default:
        break;
    }

    return filtered;
  }, [companies, searchTerm, selectedTier, sortOption]);

  // Calculate score distribution for histogram
  const scoreDistribution = useMemo(() => {
    const bins = [
      { range: '1.0-1.25', min: 1.0, max: 1.25, count: 0, tier: 'AI-Limited' },
      { range: '1.25-1.5', min: 1.25, max: 1.5, count: 0, tier: 'AI-Limited' },
      {
        range: '1.5-1.75',
        min: 1.5,
        max: 1.75,
        count: 0,
        tier: 'AI-Emerging',
      },
      {
        range: '1.75-2.0',
        min: 1.75,
        max: 2.0,
        count: 0,
        tier: 'AI-Emerging',
      },
      {
        range: '2.0-2.25',
        min: 2.0,
        max: 2.25,
        count: 0,
        tier: 'AI-Buildable',
      },
      {
        range: '2.25-2.5',
        min: 2.25,
        max: 2.5,
        count: 0,
        tier: 'AI-Buildable',
      },
      {
        range: '2.5-2.75',
        min: 2.5,
        max: 2.75,
        count: 0,
        tier: 'AI-Buildable',
      },
      {
        range: '2.75-3.0',
        min: 2.75,
        max: 3.0,
        count: 0,
        tier: 'AI-Buildable',
      },
      {
        range: '3.0-3.25',
        min: 3.0,
        max: 3.25,
        count: 0,
        tier: 'AI-Ready',
      },
      {
        range: '3.25-3.5',
        min: 3.25,
        max: 3.5,
        count: 0,
        tier: 'AI-Ready',
      },
      {
        range: '3.5-3.75',
        min: 3.5,
        max: 3.75,
        count: 0,
        tier: 'AI-Ready',
      },
      {
        range: '3.75-4.0',
        min: 3.75,
        max: 4.0,
        count: 0,
        tier: 'AI-Ready',
      },
      {
        range: '4.0-4.25',
        min: 4.0,
        max: 4.25,
        count: 0,
        tier: 'AI-Ready',
      },
      {
        range: '4.25-4.5',
        min: 4.25,
        max: 4.5,
        count: 0,
        tier: 'AI-Ready',
      },
    ];

    companies.forEach((company) => {
      const score = company.composite_score;
      const bin = bins.find((b) => score >= b.min && score <= b.max);
      if (bin) bin.count++;
    });

    return bins.filter((b) => b.count > 0);
  }, [companies]);

  // Visible rows
  const visibleRows = filteredAndSorted.slice(0, displayedRows);
  const hasMore = displayedRows < filteredAndSorted.length;

  const formatFunding = (funding: number | undefined) => {
    if (!funding) return 'N/A';
    if (funding >= 1000) return `$${(funding / 1000).toFixed(1)}B`;
    return `$${funding}M`;
  };

  const formatEmployees = (employees: number | undefined) => {
    if (!employees) return 'N/A';
    return employees.toLocaleString();
  };

  const getScoreColor = (score: number) => {
    if (score >= 3.5) return '#02C39A';
    if (score >= 2.5) return '#F5A623';
    if (score >= 1.75) return '#F24E1E';
    return '#ef4444';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <Database className="w-8 h-8 text-emerald-400" />
          <h1 className="text-4xl font-bold text-white">Training Data Explorer</h1>
        </div>
        <p className="text-slate-400">
          515 companies across 50+ verticals • Comprehensive AI readiness analysis
        </p>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-4 gap-4 mb-8">
        <div className="glass-card p-6 rounded-xl border border-slate-700">
          <div className="text-slate-400 text-sm mb-2">Total Companies</div>
          <div className="text-3xl font-bold text-white">{companies.length}</div>
        </div>
        <div className="glass-card p-6 rounded-xl border border-slate-700">
          <div className="text-slate-400 text-sm mb-2">Unique Verticals</div>
          <div className="text-3xl font-bold text-white">{uniqueVerticals}</div>
        </div>
        <div className="glass-card p-6 rounded-xl border border-slate-700">
          <div className="text-slate-400 text-sm mb-2">Avg Score</div>
          <div className="text-3xl font-bold text-emerald-400">{avgScore}</div>
        </div>
        <div className="glass-card p-6 rounded-xl border border-slate-700">
          <div className="text-slate-400 text-sm mb-2">Score Range</div>
          <div className="text-2xl font-bold text-white">
            {scoreRange.min} — {scoreRange.max}
          </div>
        </div>
      </div>

      {/* Tier Distribution */}
      <div className="glass-card p-6 rounded-xl border border-slate-700 mb-8">
        <h3 className="text-lg font-semibold text-white mb-4">Tier Distribution</h3>
        <div className="flex items-center gap-2 mb-4">
          {['AI-Ready', 'AI-Buildable', 'AI-Emerging', 'AI-Limited'].map((tier) => {
            const count = tierCounts[tier as keyof typeof tierCounts];
            const percentage = ((count / companies.length) * 100).toFixed(1);
            const width = (count / companies.length) * 100;
            return (
              <div
                key={tier}
                className="relative flex-1 h-12 rounded-lg overflow-hidden group"
                style={{
                  backgroundColor: `${TIER_COLORS[tier]}20`,
                  border: `1px solid ${TIER_COLORS[tier]}`,
                }}
              >
                <div
                  className="h-full transition-all"
                  style={{ width: `${width}%`, backgroundColor: TIER_COLORS[tier] }}
                />
                <div className="absolute inset-0 flex items-center justify-center text-xs font-semibold text-white pointer-events-none">
                  <span className="drop-shadow-lg">
                    {count} ({percentage}%)
                  </span>
                </div>
              </div>
            );
          })}
        </div>
        <div className="flex gap-4 text-sm text-slate-400">
          {['AI-Ready', 'AI-Buildable', 'AI-Emerging', 'AI-Limited'].map((tier) => (
            <div key={tier} className="flex items-center gap-2">
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: TIER_COLORS[tier] }}
              />
              <span>{tier}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Filter/Search Bar */}
      <div className="glass-card p-6 rounded-xl border border-slate-700 mb-8">
        <div className="mb-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-500" />
            <input
              type="text"
              placeholder="Search by company name or vertical..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg pl-10 pr-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
            />
          </div>
        </div>

        <div className="mb-4">
          <div className="text-sm text-slate-400 mb-2">Tier Filter</div>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => setSelectedTier(null)}
              className={`px-4 py-2 rounded-lg font-medium transition-all ${
                selectedTier === null
                  ? 'bg-emerald-500 text-white'
                  : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
              }`}
            >
              All ({companies.length})
            </button>
            {['AI-Ready', 'AI-Buildable', 'AI-Emerging', 'AI-Limited'].map((tier) => {
              const count = tierCounts[tier as keyof typeof tierCounts];
              return (
                <button
                  key={tier}
                  onClick={() => setSelectedTier(tier)}
                  className={`px-4 py-2 rounded-lg font-medium transition-all ${
                    selectedTier === tier
                      ? 'text-white'
                      : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
                  }`}
                  style={{
                    backgroundColor:
                      selectedTier === tier ? TIER_COLORS[tier] : undefined,
                  }}
                >
                  {tier} ({count})
                </button>
              );
            })}
          </div>
        </div>

        <div>
          <div className="text-sm text-slate-400 mb-2">Sort By</div>
          <div className="relative w-full sm:w-64">
            <select
              value={sortOption}
              onChange={(e) => setSortOption(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 appearance-none pr-10"
            >
              <option value="score-desc">Score (High to Low)</option>
              <option value="score-asc">Score (Low to High)</option>
              <option value="name-asc">Name (A-Z)</option>
              <option value="employees">Employees (High to Low)</option>
              <option value="founded">Founded Year (Newest)</option>
            </select>
            <ChevronDown className="absolute right-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-500 pointer-events-none" />
          </div>
        </div>
      </div>

      {/* Company Table */}
      <div className="glass-card rounded-xl border border-slate-700 overflow-hidden mb-8">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-slate-800/50 border-b border-slate-700">
                <th className="px-4 py-3 text-left text-sm font-semibold text-slate-300 w-12">
                  #
                </th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-slate-300">
                  Company
                </th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-slate-300">
                  Vertical
                </th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-slate-300 w-24">
                  Founded
                </th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-slate-300 w-32">
                  Employees
                </th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-slate-300 w-24">
                  Funding
                </th>
                <th className="px-4 py-3 text-center text-sm font-semibold text-slate-300 w-16">
                  Cloud
                </th>
                <th className="px-4 py-3 text-center text-sm font-semibold text-slate-300 w-16">
                  AI
                </th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-slate-300 w-32">
                  Score
                </th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-slate-300 w-32">
                  Tier
                </th>
              </tr>
            </thead>
            <tbody>
              {visibleRows.map((company, index) => (
                <tr
                  key={company.name}
                  className={`border-b border-slate-700/50 transition-colors hover:bg-slate-800/30 ${
                    index % 2 === 0 ? 'bg-slate-900/20' : 'bg-slate-800/10'
                  }`}
                >
                  <td className="px-4 py-3 text-sm text-slate-400 font-medium w-12">
                    {companies.indexOf(company) + 1}
                  </td>
                  <td className="px-4 py-3 text-sm text-white font-medium">
                    {company.name}
                  </td>
                  <td className="px-4 py-3 text-sm text-slate-300">{company.vertical}</td>
                  <td className="px-4 py-3 text-sm text-slate-400">
                    {company.founded_year || 'N/A'}
                  </td>
                  <td className="px-4 py-3 text-sm text-slate-400">
                    {formatEmployees(company.employees)}
                  </td>
                  <td className="px-4 py-3 text-sm text-slate-400">
                    {formatFunding(company.total_funding_usd)}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <div
                      className={`w-3 h-3 rounded-full mx-auto ${
                        company.uses_cloud ? 'bg-emerald-500' : 'bg-red-500'
                      }`}
                    />
                  </td>
                  <td className="px-4 py-3 text-center">
                    <div
                      className={`w-3 h-3 rounded-full mx-auto ${
                        company.uses_ai ? 'bg-emerald-500' : 'bg-red-500'
                      }`}
                    />
                  </td>
                  <td className="px-4 py-3 text-sm">
                    <div className="flex items-center gap-2">
                      <div className="flex-1 bg-slate-700 rounded-full h-6 overflow-hidden">
                        <div
                          className="h-full transition-all"
                          style={{
                            width: `${(company.composite_score / 4.5) * 100}%`,
                            backgroundColor: getScoreColor(company.composite_score),
                          }}
                        />
                      </div>
                      <span className="text-white font-semibold w-12">
                        {company.composite_score.toFixed(2)}
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm">
                    <span
                      className="px-3 py-1 rounded-full text-white font-semibold text-xs"
                      style={{ backgroundColor: TIER_COLORS[company.tier] }}
                    >
                      {company.tier}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Table Footer */}
        <div className="px-6 py-4 border-t border-slate-700 bg-slate-800/30 flex items-center justify-between">
          <div className="text-sm text-slate-400">
            Showing {visibleRows.length} of {filteredAndSorted.length} companies
          </div>
          {hasMore && (
            <button
              onClick={() => setDisplayedRows((prev) => prev + 50)}
              className="px-4 py-2 bg-emerald-500 hover:bg-emerald-600 text-white font-semibold rounded-lg transition-colors"
            >
              Load More
            </button>
          )}
        </div>
      </div>

      {/* Score Distribution Histogram */}
      <div className="glass-card p-6 rounded-xl border border-slate-700">
        <h3 className="text-lg font-semibold text-white mb-4">Score Distribution</h3>
        {scoreDistribution.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={scoreDistribution}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis
                dataKey="range"
                tick={{ fill: '#cbd5e1', fontSize: 12 }}
                stroke="#475569"
              />
              <YAxis tick={{ fill: '#cbd5e1', fontSize: 12 }} stroke="#475569" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1e293b',
                  border: '1px solid #475569',
                  borderRadius: '8px',
                  color: '#fff',
                }}
                cursor={{ fill: 'rgba(255, 255, 255, 0.1)' }}
              />
              <Bar dataKey="count" radius={[8, 8, 0, 0]}>
                {scoreDistribution.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={TIER_COLORS[entry.tier]}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="text-center py-12 text-slate-400">
            No data available for histogram
          </div>
        )}
      </div>
    </div>
  );
}
