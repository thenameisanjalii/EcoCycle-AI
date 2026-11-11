import { HealthResponse, PredictionResponse, TelemetryRecord } from '../types'

const BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '')

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, { ...options, headers: { 'Content-Type': 'application/json', ...(options?.headers || {}) } })
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    const detail = body?.detail || body?.message || `Request failed with status ${response.status}.`
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail))
  }
  return response.json() as Promise<T>
}

export const api = {
  predict: (records: TelemetryRecord[]) => request<PredictionResponse>('/predict', { method: 'POST', body: JSON.stringify({ records }) }),
  health: () => request<HealthResponse>('/health'),
  baseUrl: BASE_URL,
}
