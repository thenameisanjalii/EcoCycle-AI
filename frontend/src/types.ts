export const TELEMETRY_FIELDS = [
  'IR', 'QCharge', 'Tavg', 'Tmax', 'Tmin', 'chargetime', 'cycle',
  'IR_is_zero', 'temp_sensor_fault', 'IR_lag1', 'IR_delta', 'QCharge_lag1',
  'QCharge_delta', 'Tavg_lag1', 'Tavg_delta', 'chargetime_lag1',
  'chargetime_delta', 'battery_id',
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
    rul: { raw: number; display: number; units: string }
  }
  interpretation?: Record<string, unknown> | string
  models?: Record<string, unknown>
}
