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
    const required = ['QCharge', 'cycle', 'battery_id']
    const missing = required.filter((field) => source[field] === undefined || source[field] === '' || source[field] === null)
    if (missing.length) errors.push(`Row ${index + 1}: missing ${missing.join(', ')}.`)
    const normalized = { ...source } as Record<string, number | string>
    TELEMETRY_FIELDS.forEach((field) => {
      if (field !== 'battery_id' && source[field] !== undefined && source[field] !== '' && source[field] !== null) {
        const value = Number(source[field])
        if (!Number.isFinite(value)) errors.push(`Row ${index + 1}: ${field} must be a finite number.`)
        else normalized[field] = value
      }
    })
    if (normalized.cycle !== undefined && Number(normalized.cycle) < 1) errors.push(`Row ${index + 1}: cycle must be at least 1.`)
    const observed = ['IR', 'QCharge', 'Tavg', 'Tmax', 'Tmin', 'chargetime'].filter((field) => source[field] !== undefined && source[field] !== '' && source[field] !== null)
    if (observed.length < 2) errors.push(`Row ${index + 1}: supply at least two sensor measurements including QCharge.`)
    if (Number(normalized.QCharge) <= 0) errors.push(`Row ${index + 1}: QCharge must be positive.`)
    if (source.IR !== undefined && source.IR !== '' && Number(source.IR) < 0) errors.push(`Row ${index + 1}: IR cannot be negative.`)
    return normalized as TelemetryRecord
  }).filter((record): record is TelemetryRecord => record !== null)
  if (new Set(records.map((r) => String(r.battery_id))).size > 1) errors.push('History must contain exactly one battery.')
  const keys = records.map((r) => `${r.battery_id}:${r.cycle}`)
  if (new Set(keys).size !== keys.length) errors.push('Duplicate battery cycles are ambiguous.')
  return { records: records.sort((a, b) => Number(a.cycle) - Number(b.cycle)), errors }
}

export function emptyRecord(cycle = 1): TelemetryRecord {
  return {
    IR: 0.016, QCharge: 1.075, Tavg: 34, Tmax: 38, Tmin: 31, chargetime: 10.3,
    cycle, battery_id: 'B0001',
  }
}
