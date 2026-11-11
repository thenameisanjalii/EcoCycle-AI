export const TELEMETRY_FIELDS = [
  'IR', 'QCharge', 'Tavg', 'Tmax', 'Tmin', 'chargetime', 'cycle',
  'battery_id',
] as const

export type TelemetryField = typeof TELEMETRY_FIELDS[number]
export type TelemetryRecord = Record<TelemetryField, number | string> & { row_id?: number | string }
export type HealthResponse = {
  status: string
  service?: string
  pipeline_version?: string
  models_available?: { soh?: boolean; rul?: boolean }
}
export type PredictionResponse = {
  status: string
  metadata?: { battery_id?: string | number; row_id?: string | number }
  predictions: {
    soh: { raw: number; display: number; units: string }
    rul: { raw: number; display: number; units: string } | null
  }
  interpretation?: Record<string, unknown> | string
  models?: Record<string, unknown>
  reliability?: { status: string; warnings: string[] }
}
