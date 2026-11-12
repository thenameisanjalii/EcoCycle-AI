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
  metadata: { battery_id: string | number; cycle: number; row_id?: string | number }
  predictions: {
    soh: PredictionMetric | null
    rul: PredictionMetric | null
  }
}
export type PredictionMetric = { raw?: number | null; display?: number | null; units?: string }
export type Assessment = { prediction: PredictionResponse; records: TelemetryRecord[]; completedAt: string; potentialApplications: string[] }
export type PredictionResult = {
  row_index?: number
  timestamp?: string
  metadata?: { battery_id?: string | number; row_id?: string | number; cycle?: number }
  soh?: PredictionMetric | null
  rul?: PredictionMetric | null
}
