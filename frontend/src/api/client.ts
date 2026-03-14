import axios, { AxiosInstance } from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const client: AxiosInstance = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// API Types
export interface Company {
  id: string;
  name: string;
  vertical?: string;
  website?: string;
  github_org?: string;
  description?: string;
  founded_year?: number;
  employee_count?: number;
  created_at: string;
  updated_at: string;
}

export interface Score {
  id: string;
  company_id: string;
  composite_score: number;
  tier: string;
  wave?: number;
  pillar_scores?: Record<string, number>;
  pillar_breakdown?: Record<string, any>;
  model_version: string;
  created_at: string;
}

export interface Research {
  id: string;
  company_id: string;
  pillar_data?: Record<string, any>;
  raw_summary?: string;
  created_at: string;
}

export interface Job {
  id: string;
  job_type: string;
  status: string;
  progress: number;
  total_companies: number;
  completed_companies: number;
  error_message?: string;
  created_at: string;
  updated_at: string;
  completed_at?: string;
}

export interface ModelPerformance {
  model_version: string;
  training_samples: number;
  accuracy: number;
  correct_predictions: number;
  avg_tier_deviation: number;
  framework: string;
  input_features: number;
  output_classes: number;
  pillar_weights: Record<string, number>;
  backtest_results: any[];
  last_trained: string;
}

// Companies API
export const companiesApi = {
  list: () => client.get<Company[]>('/api/companies'),
  create: (data: Partial<Company>) => client.post<Company>('/api/companies', data),
  get: (id: string) => client.get<Company>(`/api/companies/${id}`),
  update: (id: string, data: Partial<Company>) => client.put<Company>(`/api/companies/${id}`, data),
  delete: (id: string) => client.delete(`/api/companies/${id}`),
};

// Research API
export const researchApi = {
  run: (companyIds: string[]) => client.post<Job>('/api/research/run', { company_ids: companyIds }),
  get: (companyId: string) => client.get<Research>(`/api/research/${companyId}`),
};

// Scoring API
export const scoringApi = {
  run: (companyIds: string[]) => client.post<Job>('/api/scoring/run', { company_ids: companyIds }),
  get: (companyId: string) => client.get<Score>(`/api/scoring/${companyId}`),
};

// Jobs API
export const jobsApi = {
  list: () => client.get<Job[]>('/api/jobs'),
  get: (id: string) => client.get<Job>(`/api/jobs/${id}`),
  subscribe: (id: string): WebSocket => {
    const wsUrl = import.meta.env.VITE_API_URL?.replace('http', 'ws') || 'ws://localhost:8000';
    return new WebSocket(`${wsUrl}/api/jobs/ws/${id}`);
  },
};

// Models API
export const modelsApi = {
  performance: () => client.get<ModelPerformance>('/api/models/performance'),
};

export default client;
