import React, { useEffect, useState } from 'react';
import { modelsApi, ModelPerformance } from '../api/client';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import TierBadge from '../components/TierBadge';

export const Models: React.FC = () => {
  const [modelPerf, setModelPerf] = useState<ModelPerformance | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadModelPerformance();
  }, []);

  const loadModelPerformance = async () => {
    try {
      const res = await modelsApi.performance();
      setModelPerf(res.data);
    } catch (error) {
      console.error('Failed to load model performance:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="loading text-center py-12">Loading model data...</div>;
  }

  if (!modelPerf) {
    return <div className="text-center py-12 text-gray-500">No model data available</div>;
  }

  // Prepare pillar weight data
  const weightData = Object.entries(modelPerf.pillar_weights)
    .map(([pillar, weight]) => ({
      name: pillar
        .split('_')
        .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' '),
      weight: (weight * 100).toFixed(1),
    }))
    .sort((a, b) => parseFloat(b.weight) - parseFloat(a.weight));

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold text-navy mb-2">ML Model Performance</h1>
        <p className="text-gray-600">AI readiness classification model metrics</p>
      </div>

      {/* Model Info */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="card p-6">
          <p className="text-gray-600 text-sm">Model Version</p>
          <p className="text-2xl font-bold text-navy">{modelPerf.model_version}</p>
        </div>
        <div className="card p-6">
          <p className="text-gray-600 text-sm">Framework</p>
          <p className="text-2xl font-bold text-teal">{modelPerf.framework}</p>
        </div>
        <div className="card p-6">
          <p className="text-gray-600 text-sm">Accuracy</p>
          <p className="text-2xl font-bold text-green">{(modelPerf.accuracy * 100).toFixed(1)}%</p>
        </div>
        <div className="card p-6">
          <p className="text-gray-600 text-sm">Avg Deviation</p>
          <p className="text-2xl font-bold text-orange">±{modelPerf.avg_tier_deviation.toFixed(2)}</p>
        </div>
      </div>

      {/* Backtest Results */}
      <div className="card p-6">
        <h2 className="text-xl font-bold text-navy mb-4">Backtest Results (8 Ground Truth Companies)</h2>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-3 px-4 font-semibold text-navy">Company</th>
                <th className="text-left py-3 px-4 font-semibold text-navy">Actual</th>
                <th className="text-left py-3 px-4 font-semibold text-navy">Predicted</th>
                <th className="text-left py-3 px-4 font-semibold text-navy">Match</th>
                <th className="text-left py-3 px-4 font-semibold text-navy">Deviation</th>
              </tr>
            </thead>
            <tbody>
              {modelPerf.backtest_results.map((result, idx) => (
                <tr key={idx} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="py-3 px-4 font-medium">{result.company_name}</td>
                  <td className="py-3 px-4">
                    <TierBadge tier={result.actual_tier} />
                  </td>
                  <td className="py-3 px-4">
                    <TierBadge tier={result.predicted_tier} />
                  </td>
                  <td className="py-3 px-4">
                    {result.tier_match ? (
                      <span className="text-green font-semibold">✓</span>
                    ) : (
                      <span className="text-red-600 font-semibold">✗</span>
                    )}
                  </td>
                  <td className="py-3 px-4 text-gray-600">
                    {result.score_deviation ? result.score_deviation.toFixed(2) : '0.00'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue text-sm">
          <p className="font-semibold text-navy mb-2">Results Summary</p>
          <p className="text-gray-700">
            Model correctly classified {modelPerf.correct_predictions} out of {modelPerf.training_samples} companies.
            Average tier deviation of {modelPerf.avg_tier_deviation.toFixed(2)} levels indicates strong tier assignment accuracy.
          </p>
        </div>
      </div>

      {/* Pillar Weights */}
      <div className="card p-6">
        <h2 className="text-xl font-bold text-navy mb-4">Pillar Feature Importance Weights</h2>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={weightData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" angle={-45} textAnchor="end" height={80} />
            <YAxis label={{ value: 'Weight (%)', angle: -90, position: 'insideLeft' }} />
            <Tooltip formatter={(value) => `${value}%`} />
            <Bar dataKey="weight" fill="#02C39A" name="Weight" />
          </BarChart>
        </ResponsiveContainer>

        <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue text-sm">
          <p className="font-semibold text-navy mb-2">Weight Interpretation</p>
          <p className="text-gray-700">
            Weights are derived from XGBoost feature importances trained on 8 ground truth companies.
            Higher weights indicate stronger predictive power for AI readiness classification.
            Data Quality and Workflow Digitization are the most important features.
          </p>
        </div>
      </div>

      {/* Model Architecture */}
      <div className="card p-6">
        <h2 className="text-xl font-bold text-navy mb-4">Model Architecture</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div className="p-3 bg-gray-50 rounded-lg">
            <p className="text-gray-600">Algorithm</p>
            <p className="font-semibold text-navy">{modelPerf.framework}</p>
          </div>
          <div className="p-3 bg-gray-50 rounded-lg">
            <p className="text-gray-600">Input Features</p>
            <p className="font-semibold text-navy">{modelPerf.input_features}</p>
          </div>
          <div className="p-3 bg-gray-50 rounded-lg">
            <p className="text-gray-600">Output Classes</p>
            <p className="font-semibold text-navy">{modelPerf.output_classes}</p>
          </div>
          <div className="p-3 bg-gray-50 rounded-lg">
            <p className="text-gray-600">Training Method</p>
            <p className="font-semibold text-navy">LOO-CV</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Models;
