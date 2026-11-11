import { TELEMETRY_FIELDS, TelemetryRecord } from '../types'
import { LEAKAGE_FIELDS } from './validation'

function parseCsv(text: string): Record<string, unknown>[] {
  const lines = text.trim().split(/\r?\n/).filter(Boolean)
  if (lines.length < 2) throw new Error('CSV must include a header and at least one data row.')
  const headers = lines[0].split(',').map((header) => header.trim())
  return lines.slice(1).map((line) => {
    const values = line.split(',').map((value) => value.trim().replace(/^"|"$/g, ''))
    return Object.fromEntries(headers.map((header, index) => [header, values[index] ?? '']))
  })
}

export async function parseUpload(file: File): Promise<unknown[]> {
  const text = await file.text()
  const extension = file.name.toLowerCase().split('.').pop()
  let parsed: unknown
  try { parsed = extension === 'csv' ? parseCsv(text) : JSON.parse(text) } catch { throw new Error('Could not parse this file. Upload valid CSV or JSON.') }
  const records = Array.isArray(parsed) ? parsed : (parsed as { records?: unknown[] })?.records
  if (!Array.isArray(records)) throw new Error('JSON must be an array or an object containing a records array.')
  const unknownFields = [...new Set(records.flatMap((record) => Object.keys(record as object)).filter((key) => !TELEMETRY_FIELDS.includes(key as never) && key !== 'row_id'))]
  const leakage = unknownFields.filter((field) => LEAKAGE_FIELDS.includes(field))
  if (leakage.length) throw new Error(`Data leakage rejected: ${leakage.join(', ')}.`)
  if (unknownFields.length) throw new Error(`Unsupported field(s): ${unknownFields.join(', ')}. Upload raw telemetry only.`)
  return records
}
