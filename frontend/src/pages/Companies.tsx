import React, { useEffect, useState } from 'react';
import { companiesApi, scoringApi, Company, Score } from '../api/client';
import { Plus } from 'lucide-react';
import CompanyCard from '../components/CompanyCard';

interface CreateForm {
  name: string;
  vertical?: string;
  website?: string;
  employee_count?: number;
}

export const Companies: React.FC<Props> = ({ onSelectCompany }) => {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [scores, setScores] = useState<Record<string, Score>>({});
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<CreateForm>({
    name: '',
    vertical: '',
    website: '',
  });
  const [selectedTier, setSelectedTier] = useState<string | null>(null);

  useEffect(() => {
    loadCompanies();
  }, []);

  const loadCompanies = async () => {
    setLoading(true);
    try {
      const res = await companiesApi.list();
      setCompanies(res.data);

      // Load scores
      const scoresMap: Record<string, Score> = {};
      for (const company of res.data) {
        try {
          const scoreRes = await scoringApi.get(company.id);
          scoresMap[company.id] = scoreRes.data;
        } catch {
          // No score yet
        }
      }
      setScores(scoresMap);
    } catch (error) {
      console.error('Failed to load companies:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    if (!form.name.trim()) return;

    try {
      await companiesApi.create({
        name: form.name,
        vertical: form.vertical || undefined,
        website: form.website || undefined,
        employee_count: form.employee_count,
      });

      setForm({ name: '', vertical: '', website: '' });
      setShowForm(false);
      loadCompanies();
    } catch (error) {
      console.error('Failed to create company:', error);
    }
  };

  const handleDelete = async (id: string) => {
    if (confirm('Delete this company?')) {
      try {
        await companiesApi.delete(id);
        loadCompanies();
      } catch (error) {
        console.error('Failed to delete company:', error);
      }
    }
  };

  const filteredCompanies = selectedTier
    ? companies.filter((c) => scores[c.id]?.tier === selectedTier)
    : companies;

  if (loading) {
    return <div className="loading text-center py-12">Loading companies...</div>;
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-4xl font-bold text-navy mb-2">Companies</h1>
          <p className="text-gray-600">Manage your portfolio companies</p>
        </div>
        <button onClick={() => setShowForm(true)} className="btn-primary flex items-center space-x-2">
          <Plus size={20} />
          <span>Add Company</span>
        </button>
      </div>

      {/* Add Company Form */}
      {showForm && (
        <div className="card p-6 bg-blue-50 border-2 border-blue">
          <h2 className="text-xl font-bold text-navy mb-4">Add New Company</h2>
          <div className="space-y-4">
            <input
              type="text"
              placeholder="Company Name"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-teal"
            />
            <input
              type="text"
              placeholder="Vertical (e.g., SaaS, FinTech)"
              value={form.vertical || ''}
              onChange={(e) => setForm({ ...form, vertical: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-teal"
            />
            <input
              type="text"
              placeholder="Website"
              value={form.website || ''}
              onChange={(e) => setForm({ ...form, website: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-teal"
            />
            <input
              type="number"
              placeholder="Employee Count"
              value={form.employee_count || ''}
              onChange={(e) => setForm({ ...form, employee_count: parseInt(e.target.value) || undefined })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-teal"
            />

            <div className="flex space-x-3">
              <button onClick={handleCreate} className="btn-primary flex-1">
                Create
              </button>
              <button onClick={() => setShowForm(false)} className="btn-secondary flex-1">
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Tier Filter */}
      <div className="flex space-x-2">
        <button
          onClick={() => setSelectedTier(null)}
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            selectedTier === null ? 'bg-navy text-white' : 'bg-gray-200 text-gray-900 hover:bg-gray-300'
          }`}
        >
          All
        </button>
        {['AI-Ready', 'AI-Buildable', 'AI-Emerging', 'AI-Limited'].map((tier) => (
          <button
            key={tier}
            onClick={() => setSelectedTier(tier)}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              selectedTier === tier ? 'bg-navy text-white' : 'bg-gray-200 text-gray-900 hover:bg-gray-300'
            }`}
          >
            {tier}
          </button>
        ))}
      </div>

      {/* Companies Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredCompanies.map((company) => (
          <CompanyCard
            key={company.id}
            company={company}
            score={scores[company.id] || null}
            onClick={() => onSelectCompany?.(company.id)}
            onDelete={() => handleDelete(company.id)}
          />
        ))}
      </div>

      {filteredCompanies.length === 0 && (
        <div className="text-center py-12">
          <p className="text-gray-500 text-lg">No companies found</p>
        </div>
      )}
    </div>
  );
};

interface Props {
  onSelectCompany?: (companyId: string) => void;
}

export default Companies;
