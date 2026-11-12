import type { Assessment, PredictionMetric, PredictionResponse, PredictionResult, TelemetryRecord } from '../types'
import { validateRecords } from './validation'

function finite(value: unknown): value is number {
  return typeof value === 'number' && Number.isFinite(value)
}

/** The only SOH presentation conversion. Never mutate the API response. */
export function displaySOH(metric?: PredictionMetric | null): number | undefined {
  const value = metric?.raw ?? metric?.display
  return finite(value) ? Math.max(0, Math.min(100, value - 1)) : undefined
}

export function displayRUL(metric?: PredictionMetric | null): number | undefined {
  return [metric?.display, metric?.raw].find((value): value is number => finite(value) && value >= 0)
}

export const EV_SOH_THRESHOLD = 81

export function sohHealth(soh?: number) {
  if (!finite(soh)) return { label: 'Awaiting assessment', color: '#9aad9f', tone: 'neutral' }
  return soh >= EV_SOH_THRESHOLD
    ? { label: 'Healthy', color: '#18a66b', tone: 'green' }
    : { label: 'Monitor', color: '#f59e0b', tone: 'amber' }
}

const POTENTIAL_APPLICATIONS = [
  'Solar energy storage', 'Home backup', 'Telecom backup', 'Off-grid lighting',
  'Low-power stationary storage', 'Community energy storage', 'Emergency lighting',
]

/** Select once when a successful assessment arrives, never during rendering. */
export function selectPotentialApplications(soh?: number, random = Math.random): string[] {
  if (!finite(soh) || soh >= EV_SOH_THRESHOLD) return []
  const shuffled = [...POTENTIAL_APPLICATIONS]
  for (let index = shuffled.length - 1; index > 0; index--) {
    const other = Math.floor(random() * (index + 1))
    ;[shuffled[index], shuffled[other]] = [shuffled[other], shuffled[index]]
  }
  return shuffled.slice(0, 3 + Math.floor(random() * 3))
}

export function rulUnavailableReason(assessment: Assessment | null): string {
  if (!assessment) return 'Submit battery measurements to estimate remaining cycles.'
  if (displayRUL(assessment.prediction.predictions.rul) !== undefined) return ''
  if (assessment.records.length < 2) return 'Import at least two measured cycles for this battery, then run again.'
  return 'No remaining-life estimate was returned. Check the battery history and retry.'
}

/** Bind the result to the submitted observation, never to response array order. */
export function mapLatestPrediction(results: PredictionResult[], records: TelemetryRecord[]): PredictionResponse {
  const latestIndex = records.reduce((best, record, index) => Number(record.cycle) > Number(records[best].cycle) ? index : best, 0)
  const latest = records[latestIndex]
  if (!latest || !Array.isArray(results)) throw new Error('No assessment was returned for the latest cycle.')
  const candidates = results.filter((result) => {
    if (!result || typeof result !== 'object') return false
    const meta = result.metadata
    if (meta?.battery_id != null && String(meta.battery_id) !== String(latest.battery_id)) return false
    if (meta?.row_id != null && latest.row_id != null && String(meta.row_id) !== String(latest.row_id)) return false
    if (meta?.cycle != null && meta.cycle !== Number(latest.cycle)) return false
    if (result.row_index != null) return result.row_index === latestIndex
    if (meta?.cycle != null) return true
    if (meta?.row_id != null && latest.row_id != null) return String(meta.row_id) === String(latest.row_id)
    // The v2 history contract returns one result for the latest submitted cycle.
    return results.length === 1
  })
  const timestamp = (result: PredictionResult) => {
    const time = typeof result.timestamp === 'string' ? Date.parse(result.timestamp) : NaN
    return Number.isFinite(time) ? time : -Infinity
  }
  const result = candidates.reduce<PredictionResult | undefined>((best, next) => !best || timestamp(next) >= timestamp(best) ? next : best, undefined)
  if (!result) throw new Error('No assessment was returned for the latest cycle.')
  return {
    status: 'success',
    metadata: { battery_id: latest.battery_id, cycle: Number(latest.cycle), ...(latest.row_id != null ? { row_id: latest.row_id } : {}) },
    predictions: { soh: result.soh ?? null, rul: result.rul ?? null },
  }
}

// Keep only the submitted observations across reloads. Predictions are always fetched afresh.
export function restoreRecords(storage: Pick<Storage, 'getItem'>, key: string): TelemetryRecord[] {
  try {
    const saved = JSON.parse(storage.getItem(key) || 'null')
    if (saved?.version !== 1 || !Array.isArray(saved.records)) return []
    const validated = validateRecords(saved.records)
    return validated.errors.length ? [] : validated.records
  } catch { return [] }
}

export function saveAssessmentRecords(storage: Pick<Storage, 'setItem' | 'removeItem'>, key: string, assessment: Assessment | null) {
  try {
    if (assessment) storage.setItem(key, JSON.stringify({ version: 1, records: assessment.records }))
    else storage.removeItem(key)
  } catch { /* A disabled or full storage must not prevent a prediction. */ }
}
