import React, { useEffect, useState } from 'react';
import { companiesApi, researchApi, scoringApi, Company } from '../api/client';
import { Play } from 'lucide-react';
import JobStatus from '../components/JobStatus';

type PipelineType = 'research' | 'scoring';

export const RunPipeline: React.FC = () => {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [selectedCompanies, setSelectedCompanies] = useState<Set<string>>(new Set());
  const [pipelineType, setPipelineType] = useState<PipelineType>('research');
  const [jobId, setJobId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadCompanies();
  }, []);

  const loadCompanies = async () => {
    try {
      const res = await companiesApi.list();
      setCompanies(res.data);
    } catch (error) {
      console.error('Failed to load companies:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectAll = () => {
    if (selectedCompanies.size === companies.length) {
      setSelectedCompanies(new Set());
    } else {
      setSelectedCompanies(new Set(companies.map((c) => c.id)));
    }
  };

  const handleToggleCompany = (companyId: string) => {
    const newSelected = new Set(selectedCompanies);
    if (newSelected.has(companyId)) {
      newSelected.delete(companyId);
    } else {
      newSelected.add(companyId);
    }
    setSelectedCompanies(newSelected);
  };

  const handleRunPipeline = async () => {
    const companyIds = Array.from(selectedCompanies);
    if (companyIds.length === 0) {
      alert('Select at least one company');
      return;
    }

    try {
      const result =
        pipelineType === 'research'
          ? await researchApi.run(companyIds)
          : await scoringApi.run(companyIds);

      setJobId(result.data.id);
    } catch (error) {
      console.error('Failed to start pipeline:', error);
      alert('Failed to start pipeline');
    }
  };

  if (loading) {
    return <div className="loading text-center py-12">Loading...</div>;
  }

  if (jobId) {
    return (
      <div className="space-y-8">
        <div>
          <h1 className="text-4xl font-bold text-navy mb-2">Pipeline Running</h1>
          <p className="text-gray-600">Watch real-time progress below</p>
        </div>

        <JobStatus
          jobId={jobId}
          onComplete={() => {
            setTimeout(() => {
              setJobId(null);
              setSelectedCompanies(new Set());
            }, 2000);
          }}
        />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold text-navy mb-2">Run Pipeline</h1>
        <p className="text-gray-600">Execute research or scoring pipelines</p>
      </div>

      {/* Pipeline Selection */}
      <div className="card p-6">
        <h2 className="text-xl font-bold text-navy mb-4">Select Pipeline Type</h2>
        <div className="flex space-x-4">
          <button
            onClick={() => setPipelineType('research')}
            className={`flex-1 py-3 px-4 rounded-lg font-semibold transition-colors ${
              pipelineType === 'research'
                ? 'bg-teal text-white'
                : 'bg-gray-100 text-gray-900 hover:bg-gray-200'
            }`}
          >
            Research Pipeline
          </button>
          <button
            onClick={() => setPipelineType('scoring')}
            className={`flex-1 py-3 px-4 rounded-lg font-semibold transition-colors ${
              pipelineType === 'scoring'
                ? 'bg-teal text-white'
                : 'bg-gray-100 text-gray-900 hover:bg-gray-200'
            }`}
          >
            Scoring Pipeline
          </button>
        </div>

        <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue">
          {pipelineType === 'research' ? (
            <div>
              <p className="font-semibold text-navy mb-2">Research Pipeline</p>
              <p className="text-sm text-gray-700">
                Analyzes each company across the 8-pillar framework using AI research agents.
                Gathers intelligence from web sources, company data, and GitHub.
              </p>
            </div>
          ) : (
            <div>
              <p className="font-semibold text-navy mb-2">Scoring Pipeline</p>
              <p className="text-sm text-gray-700">
                Uses ML model to generate AI readiness scores based on research findings.
                Classifies companies into tiers and assigns portfolio waves.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Company Selection */}
      <div className="card p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold text-navy">Select Companies</h2>
          <button
            onClick={handleSelectAll}
            className="text-sm text-teal hover:text-teal/80 font-medium"
          >
            {selectedCompanies.size === companies.length ? 'Deselect All' : 'Select All'}
          </button>
        </div>

        <div className="space-y-2 max-h-64 overflow-y-auto">
          {companies.map((company) => (
            <label key={company.id} className="flex items-center space-x-3 p-3 hover:bg-gray-50 rounded-lg">
              <input
                type="checkbox"
                checked={selectedCompanies.has(company.id)}
                onChange={() => handleToggleCompany(company.id)}
                className="w-4 h-4 text-teal rounded border-gray-300"
              />
              <div className="flex-1">
                <p className="font-medium text-navy">{company.name}</p>
                <p className="text-sm text-gray-600">{company.vertical}</p>
              </div>
            </label>
          ))}
        </div>

        <div className="mt-4 text-sm text-gray-600">
          Selected: {selectedCompanies.size} / {companies.length}
        </div>
      </div>

      {/* Run Button */}
      <div className="flex justify-center">
        <button onClick={handleRunPipeline} className="btn-primary flex items-center space-x-2 text-lg px-8 py-3">
          <Play size={24} />
          <span>Run {pipelineType === 'research' ? 'Research' : 'Scoring'} Pipeline</span>
        </button>
      </div>
    </div>
  );
};

export default RunPipeline;
