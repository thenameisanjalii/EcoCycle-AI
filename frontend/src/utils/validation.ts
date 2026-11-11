import { TELEMETRY_FIELDS, TelemetryRecord } from '../types'

export const LEAKAGE_FIELDS = ['QDischarge', 'SOH', 'RUL', 'max_cycle', 'final_cycle', 'terminal_cycle', 'total_cycles']
export const MAX_RECORDS = 5000

export function validateRecords(input: unknown[]): { records: TelemetryRecord[]; errors: string[] } {
  const errors: string[] = []
  if (!input.length) return { records: [], errors: ['Add at least one telemetry record before submitting.'] }
  if (input.length > MAX_RECORDS) return { records: [], errors: [`A maximum of ${MAX_RECORDS.toLocaleString()} records is supported.`] }

  const records = input.map((raw, index) => {
    if (!raw || typeof raw !== 'object' || Array.isArray(raw)) {
      errors.push(`Row ${index + 1}: expected an object.`)
      return null
    }
    const source = raw as Record<string, unknown>
    const leaks = Object.keys(source).filter((key) => LEAKAGE_FIELDS.includes(key))
    if (leaks.length) errors.push(`Row ${index + 1}: leakage field(s) rejected: ${leaks.join(', ')}.`)
    const missing = TELEMETRY_FIELDS.filter((field) => source[field] === undefined || source[field] === '')
    if (missing.length) errors.push(`Row ${index + 1}: missing ${missing.join(', ')}.`)
    const normalized = { ...source } as Record<string, number | string>
    TELEMETRY_FIELDS.forEach((field) => {
      if (field !== 'battery_id' && source[field] !== undefined && source[field] !== '') {
        const value = Number(source[field])
        if (!Number.isFinite(value)) errors.push(`Row ${index + 1}: ${field} must be a finite number.`)
        else normalized[field] = value
      }
    })
    if (normalized.cycle !== undefined && Number(normalized.cycle) < 1) errors.push(`Row ${index + 1}: cycle must be at least 1.`)
    return normalized as TelemetryRecord
  }).filter((record): record is TelemetryRecord => record !== null)
  return { records: records.sort((a, b) => Number(a.cycle) - Number(b.cycle)), errors }
}

export function emptyRecord(cycle = 1): TelemetryRecord {
  return {
    IR: 0.008, QCharge: 1.075, Tavg: 28, Tmax: 29.5, Tmin: 26.5, chargetime: 43,
    cycle, IR_is_zero: 0, temp_sensor_fault: 0, IR_lag1: 0.0079, IR_delta: 0.0001,
    QCharge_lag1: 1.076, QCharge_delta: -0.001, Tavg_lag1: 27.9, Tavg_delta: 0.1,
    chargetime_lag1: 43.1, chargetime_delta: -0.1, battery_id: 'B0001',
  }
}
