import React, { useEffect, useState } from 'react';
import { companiesApi, scoringApi, Company, Score } from '../api/client';
import { TrendingUp, Users, Award, Zap } from 'lucide-react';
import WaveChart from '../components/WaveChart';
import TierBadge from '../components/TierBadge';

export const Dashboard: React.FC = () => {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [scores, setScores] = useState<Record<string, Score>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const companiesRes = await companiesApi.list();
      setCompanies(companiesRes.data);

      // Load scores for all companies
      const scoresMap: Record<string, Score> = {};
      for (const company of companiesRes.data) {
        try {
          const scoreRes = await scoringApi.get(company.id);
          scoresMap[company.id] = scoreRes.data;
        } catch {
          // No score yet
        }
      }
      setScores(scoresMap);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const stats = {
    totalCompanies: companies.length,
    avgScore: companies.length > 0
      ? (Object.values(scores).reduce((sum, s) => sum + s.composite_score, 0) / Object.values(scores).length).toFixed(2)
      : '0.00',
    aiReady: Object.values(scores).filter((s) => s.tier === 'AI-Ready').length,
    aiBuildable: Object.values(scores).filter((s) => s.tier === 'AI-Buildable').length,
  };

  const waveData = [
    { wave: 1, count: Object.values(scores).filter((s) => s.wave === 1).length },
    { wave: 2, count: Object.values(scores).filter((s) => s.wave === 2).length },
    { wave: 3, count: Object.values(scores).filter((s) => s.wave === 3).length },
  ];

  if (loading) {
    return <div className="loading text-center py-12">Loading dashboard...</div>;
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold text-navy mb-2">Dashboard</h1>
        <p className="text-gray-600">Portfolio AI Readiness Overview</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Total Companies</p>
              <p className="text-3xl font-bold text-navy">{stats.totalCompanies}</p>
            </div>
            <Users className="text-teal opacity-20" size={40} />
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Avg AI Readiness</p>
              <p className="text-3xl font-bold text-teal">{stats.avgScore}</p>
            </div>
            <TrendingUp className="text-teal opacity-20" size={40} />
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">AI-Ready</p>
              <p className="text-3xl font-bold text-green">{stats.aiReady}</p>
            </div>
            <Award className="text-green opacity-20" size={40} />
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">AI-Buildable</p>
              <p className="text-3xl font-bold text-gold">{stats.aiBuildable}</p>
            </div>
            <Zap className="text-gold opacity-20" size={40} />
          </div>
        </div>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Wave Distribution */}
        <div className="card p-6">
          <h2 className="text-xl font-bold text-navy mb-4">Portfolio Waves</h2>
          <WaveChart data={waveData} />
        </div>

        {/* Score Distribution */}
        <div className="card p-6">
          <h2 className="text-xl font-bold text-navy mb-4">Tier Distribution</h2>
          <div className="space-y-4">
            {[
              { tier: 'AI-Ready', count: stats.aiReady, color: 'bg-teal' },
              { tier: 'AI-Buildable', count: stats.aiBuildable, color: 'bg-gold' },
              { tier: 'AI-Emerging', count: Object.values(scores).filter((s) => s.tier === 'AI-Emerging').length, color: 'bg-orange' },
              { tier: 'AI-Limited', count: Object.values(scores).filter((s) => s.tier === 'AI-Limited').length, color: 'bg-red-500' },
            ].map((item) => (
              <div key={item.tier}>
                <div className="flex justify-between mb-1">
                  <span className="font-medium text-gray-700">{item.tier}</span>
                  <span className="text-gray-600">{item.count}</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`${item.color} h-2 rounded-full`}
                    style={{ width: `${stats.totalCompanies > 0 ? (item.count / stats.totalCompanies) * 100 : 0}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Scores Table */}
      <div className="card p-6">
        <h2 className="text-xl font-bold text-navy mb-4">Recent Scores</h2>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-3 px-4 font-semibold text-navy">Company</th>
                <th className="text-left py-3 px-4 font-semibold text-navy">Score</th>
                <th className="text-left py-3 px-4 font-semibold text-navy">Tier</th>
                <th className="text-left py-3 px-4 font-semibold text-navy">Wave</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(scores)
                .sort(([, a], [, b]) => b.composite_score - a.composite_score)
                .slice(0, 10)
                .map(([companyId, score]) => {
                  const company = companies.find((c) => c.id === companyId);
                  return (
                    <tr key={companyId} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-3 px-4">{company?.name}</td>
                      <td className="py-3 px-4 font-semibold text-teal">{score.composite_score.toFixed(2)}</td>
                      <td className="py-3 px-4">
                        <TierBadge tier={score.tier} />
                      </td>
                      <td className="py-3 px-4">Wave {score.wave || 3}</td>
                    </tr>
                  );
                })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
