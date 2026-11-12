import { HealthResponse, PredictionResponse, PredictionResult, TelemetryRecord } from '../types'
import { mapLatestPrediction } from '../utils/assessment'

const BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '')

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, { ...options, cache: 'no-store', headers: { 'Content-Type': 'application/json', ...(options?.headers || {}) } })
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    const detail = body?.detail || body?.message || `Request failed with status ${response.status}.`
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail))
  }
  return response.json() as Promise<T>
}

type V2Response = {
  results: PredictionResult[]
}

export const api = {
  predict: async (records: TelemetryRecord[], signal?: AbortSignal): Promise<PredictionResponse> => {
    const raw = records.map((r) => Object.fromEntries(Object.entries(r).filter(([, value]) => value !== '' && value !== null)))
    const result = await request<V2Response>('/v2/predict', { method: 'POST', signal, body: JSON.stringify({ contract: records.length > 1 ? 'history' : 'single', records: raw }) })
    return mapLatestPrediction(result.results, records)
  },
  health: () => request<HealthResponse>('/v2/health'),
  baseUrl: BASE_URL,
}
