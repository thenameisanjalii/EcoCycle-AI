import { TELEMETRY_FIELDS, TelemetryRecord } from '../types'
import inputBounds from '../../../configs/prediction_input_bounds.json'

export const LEAKAGE_FIELDS = ['QDischarge', 'SOH', 'RUL', 'max_cycle', 'final_cycle', 'terminal_cycle', 'total_cycles']
export const MAX_RECORDS = 5000
export const INPUT_BOUNDS = inputBounds.fields
export type NumericField = keyof typeof INPUT_BOUNDS
const DECIMAL = /^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$/

export function allowedRange(field: NumericField): string {
  const bounds = INPUT_BOUNDS[field]
  return `Allowed range: ${bounds.min} to ${bounds.max} ${bounds.unit}.`
}

export function inputError(field: string, value: unknown): string {
  if (field === 'battery_id') {
    return (typeof value === 'string' && value.trim() !== '') || (typeof value === 'number' && Number.isInteger(value))
      ? '' : 'Battery ID is required and must be a nonempty string or integer.'
  }
  const name = field as NumericField
  const bounds = INPUT_BOUNDS[name]
  if (value === null || value === undefined || (typeof value === 'string' && value.trim() === '')) return `${field} is required. ${allowedRange(name)}`
  if ((typeof value !== 'number' && typeof value !== 'string') || (typeof value === 'string' && !DECIMAL.test(value.trim())) || !Number.isFinite(Number(value))) {
    return `${field} requires a finite number. ${allowedRange(name)}`
  }
  const number = Number(value)
  if (number < bounds.min || number > bounds.max) return `${field} is out of range. ${allowedRange(name)}`
  if (field === 'cycle' && !Number.isInteger(number)) return `cycle must be a whole number. ${allowedRange(name)}`
  return ''
}

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
    if (leaks.length) errors.push(`Row ${index + 1}: unsupported field(s): ${leaks.join(', ')}.`)
    const normalized = { ...source } as Record<string, number | string>
    TELEMETRY_FIELDS.forEach((field) => {
      const error = inputError(field, source[field])
      if (error) errors.push(`Row ${index + 1}: ${error}`)
      else normalized[field] = field === 'battery_id'
        ? (typeof source[field] === 'string' ? source[field].trim() : source[field]) as number | string
        : Number(source[field])
    })
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
