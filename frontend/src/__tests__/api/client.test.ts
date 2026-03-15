import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import axios from 'axios'
import { companiesApi, researchApi, scoringApi, jobsApi, modelsApi } from '../../api/client'

vi.mock('axios', async () => {
  const mockClient = {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  }
  return {
    default: {
      create: vi.fn(() => mockClient),
      ...mockClient,
    },
  }
})

// Get the mock axios client instance
const mockAxios = axios.create()

describe('companiesApi', () => {
  beforeEach(() => vi.clearAllMocks())

  it('list calls GET /api/companies', () => {
    companiesApi.list()
    expect(mockAxios.get).toHaveBeenCalledWith('/api/companies')
  })

  it('get calls GET /api/companies/:id', () => {
    companiesApi.get('co_abc123')
    expect(mockAxios.get).toHaveBeenCalledWith('/api/companies/co_abc123')
  })

  it('create calls POST /api/companies with data', () => {
    const payload = { name: 'Test Corp', vertical: 'SaaS' }
    companiesApi.create(payload)
    expect(mockAxios.post).toHaveBeenCalledWith('/api/companies', payload)
  })

  it('update calls PUT /api/companies/:id with data', () => {
    const payload = { name: 'Updated Corp' }
    companiesApi.update('co_abc123', payload)
    expect(mockAxios.put).toHaveBeenCalledWith('/api/companies/co_abc123', payload)
  })

  it('delete calls DELETE /api/companies/:id', () => {
    companiesApi.delete('co_abc123')
    expect(mockAxios.delete).toHaveBeenCalledWith('/api/companies/co_abc123')
  })
})

describe('researchApi', () => {
  beforeEach(() => vi.clearAllMocks())

  it('run calls POST /api/research/run with company_ids', () => {
    researchApi.run(['co_1', 'co_2'])
    expect(mockAxios.post).toHaveBeenCalledWith('/api/research/run', { company_ids: ['co_1', 'co_2'] })
  })

  it('get calls GET /api/research/:companyId', () => {
    researchApi.get('co_abc123')
    expect(mockAxios.get).toHaveBeenCalledWith('/api/research/co_abc123')
  })
})

describe('scoringApi', () => {
  beforeEach(() => vi.clearAllMocks())

  it('run calls POST /api/scoring/run with company_ids', () => {
    scoringApi.run(['co_1'])
    expect(mockAxios.post).toHaveBeenCalledWith('/api/scoring/run', { company_ids: ['co_1'] })
  })

  it('get calls GET /api/scoring/:companyId', () => {
    scoringApi.get('co_abc123')
    expect(mockAxios.get).toHaveBeenCalledWith('/api/scoring/co_abc123')
  })
})

describe('jobsApi', () => {
  beforeEach(() => vi.clearAllMocks())

  it('list calls GET /api/jobs', () => {
    jobsApi.list()
    expect(mockAxios.get).toHaveBeenCalledWith('/api/jobs')
  })

  it('get calls GET /api/jobs/:id', () => {
    jobsApi.get('job_abc123')
    expect(mockAxios.get).toHaveBeenCalledWith('/api/jobs/job_abc123')
  })

  it('subscribe returns a WebSocket', () => {
    const ws = jobsApi.subscribe('job_abc123')
    expect(ws).toBeInstanceOf(WebSocket)
    ws.close()
  })
})

describe('modelsApi', () => {
  beforeEach(() => vi.clearAllMocks())

  it('performance calls GET /api/models/performance', () => {
    modelsApi.performance()
    expect(mockAxios.get).toHaveBeenCalledWith('/api/models/performance')
  })
})
