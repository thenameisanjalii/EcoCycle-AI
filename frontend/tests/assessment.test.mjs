import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'
import { loadTs } from './loadTs.mjs'

const { displaySOH, displayRUL, mapLatestPrediction, restoreRecords, saveAssessmentRecords, sohHealth, selectPotentialApplications, rulUnavailableReason } = await import(await loadTs(new URL('../src/utils/assessment.ts', import.meta.url)))
const { validateRecords } = await import(await loadTs(new URL('../src/utils/validation.ts', import.meta.url)))
const { api } = await import(await loadTs(new URL('../src/services/api.ts', import.meta.url)))
const records = [10, 20, 30].map((cycle) => ({ battery_id: 'new-battery', cycle, QCharge: 1.2, IR: 0.02, Tmin: 31, Tavg: 34, Tmax: 38, chargetime: 10.3 }))
const metric = (value) => ({ raw: value, display: value, units: '%' })

test('SOH subtracts exactly one percentage point without changing the returned values', () => {
  for (const [raw, expected] of [[80, 79], [50.25, 49.25], [1, 0], [0, 0], [-3, 0], [103, 100]]) {
    const input = Object.freeze(metric(raw))
    assert.equal(displaySOH(input), expected)
    assert.equal(displaySOH(input), expected)
    assert.equal(input.raw, raw)
    assert.equal(input.display, raw)
  }
  assert.equal(displaySOH({ display: 80 }), 79)
  assert.equal(displaySOH({ raw: 101, display: 100 }), 100)
})

test('missing and nonnumeric metrics stay unavailable, and zero RUL remains valid', () => {
  for (const input of [null, undefined, {}, { raw: null }, { raw: NaN }, { raw: Infinity }, { raw: '80' }]) {
    assert.equal(displaySOH(input), undefined)
    assert.equal(displayRUL(input), undefined)
  }
  assert.equal(displayRUL(metric(-1)), undefined)
  assert.equal(displayRUL(metric(0)), 0)
  assert.equal(displayRUL({ raw: 125.4 }), 125.4)
})

test('unordered API results bind SOH, RUL, battery ID and cycle to the latest observation', () => {
  const results = [
    { row_index: 0, metadata: { battery_id: 'new-battery' }, soh: metric(90), rul: metric(900) },
    { row_index: 2, soh: metric(70), rul: metric(123) },
    { row_index: 1, soh: metric(80), rul: metric(400) },
  ]
  const prediction = mapLatestPrediction(results, records)
  assert.deepEqual(prediction.metadata, { battery_id: 'new-battery', cycle: 30 })
  assert.equal(displaySOH(prediction.predictions.soh), 69)
  assert.equal(displayRUL(prediction.predictions.rul), 123)
})

test('newest timestamp for the same observation wins; missing RUL never falls back to an older result', () => {
  const prediction = mapLatestPrediction([
    { row_index: 2, timestamp: '2026-11-12T09:00:00Z', soh: metric(70), rul: null },
    { row_index: 2, timestamp: '2026-11-12T08:00:00Z', soh: metric(80), rul: metric(400) },
    { row_index: 0, timestamp: '2026-11-12T10:00:00Z', soh: metric(90), rul: metric(900) },
  ], records)
  assert.equal(displaySOH(prediction.predictions.soh), 69)
  assert.equal(displayRUL(prediction.predictions.rul), undefined)
})

test('missing metadata is recovered from submitted data, including numeric battery ID zero', () => {
  const input = [{ ...records[0], battery_id: 0 }]
  const prediction = mapLatestPrediction([{ soh: metric(81), rul: null }], input)
  assert.equal(prediction.metadata.battery_id, 0)
  assert.equal(prediction.metadata.cycle, 10)
  assert.equal(displayRUL(prediction.predictions.rul), undefined)
})

test('mismatched, absent, or ambiguous latest results cannot reuse an older prediction', () => {
  for (const results of [[], null, [{ row_index: 0 }], [{ metadata: { battery_id: 'old-battery' } }], [{ metadata: { cycle: 20 } }], [{}, {}]]) {
    assert.throws(() => mapLatestPrediction(results, records), /latest cycle/)
  }
})

test('existing CSV data selects the highest cycle even when input order is reversed', async () => {
  const text = await readFile(new URL('../../presentation_inputs/battery_2_near_80_soh.csv', import.meta.url), 'utf8')
  const [header, ...lines] = text.trim().split(/\r?\n/)
  const columns = header.split(',')
  const input = lines.map((line) => Object.fromEntries(line.split(',').map((value, index) => [columns[index], value])))
  const validated = validateRecords(input.reverse())
  assert.deepEqual(validated.errors, [])
  const expected = validated.records.at(-1)
  const prediction = mapLatestPrediction([{ row_index: validated.records.length - 1, soh: metric(80), rul: null }], validated.records)
  assert.equal(String(prediction.metadata.battery_id), String(expected.battery_id))
  assert.equal(prediction.metadata.cycle, Number(expected.cycle))
})

test('reload storage contains inputs only; corrupted data and disabled storage are safe', () => {
  const data = new Map()
  const storage = { getItem: (key) => data.get(key) ?? null, setItem: (key, value) => data.set(key, value), removeItem: (key) => data.delete(key) }
  saveAssessmentRecords(storage, 'test', { records, prediction: { predictions: { soh: metric(80), rul: metric(99) } }, completedAt: 'old' })
  const saved = JSON.parse(data.get('test'))
  assert.equal(saved.prediction, undefined)
  assert.equal(saved.completedAt, undefined)
  assert.deepEqual(restoreRecords(storage, 'test'), records)
  data.set('test', 'corrupt json')
  assert.deepEqual(restoreRecords(storage, 'test'), [])
  data.set('test', JSON.stringify({ version: 1, records: [null] }))
  assert.deepEqual(restoreRecords(storage, 'test'), [])
  const disabled = { getItem() { throw Error() }, setItem() { throw Error() }, removeItem() { throw Error() } }
  assert.deepEqual(restoreRecords(disabled, 'test'), [])
  assert.doesNotThrow(() => saveAssessmentRecords(disabled, 'test', { records }))
  saveAssessmentRecords(storage, 'test', null)
  assert.equal(data.has('test'), false)
})

test('each API refresh bypasses the cache and maps the fresh response', async () => {
  const originalFetch = globalThis.fetch
  const calls = []
  globalThis.fetch = async (url, options) => {
    calls.push({ url, options })
    return new Response(JSON.stringify({ results: [{ row_index: 2, soh: metric(80), rul: metric(calls.length * 10) }] }))
  }
  try {
    const first = await api.predict(records)
    const latest = await api.predict(records)
    assert.equal(displayRUL(first.predictions.rul), 10)
    assert.equal(displayRUL(latest.predictions.rul), 20)
    assert.equal(calls.length, 2)
    assert.equal(calls[0].options.cache, 'no-store')
    assert.equal(calls[1].options.cache, 'no-store')
    assert.equal(JSON.parse(calls[0].options.body).contract, 'history')
    assert.deepEqual(latest.metadata, { battery_id: 'new-battery', cycle: 30 })
  } finally { globalThis.fetch = originalFetch }
})

test('gauge and badge health share the 81% threshold using adjusted SOH', () => {
  for (const [raw, tone] of [[81.99, 'amber'], [82, 'green'], [0, 'amber'], [110, 'green']]) {
    assert.equal(sohHealth(displaySOH(metric(raw))).tone, tone)
  }
  assert.equal(sohHealth(undefined).tone, 'neutral')
})

test('second-life selections have 3-5 unique applications below 81% and none for EV or missing SOH', () => {
  for (const random of [() => 0, () => 0.5, () => 0.99999, Math.random]) {
    const selected = selectPotentialApplications(80.99, random)
    assert.ok(selected.length >= 3 && selected.length <= 5)
    assert.equal(new Set(selected).size, selected.length)
  }
  assert.deepEqual(selectPotentialApplications(81), [])
  assert.deepEqual(selectPotentialApplications(undefined), [])
})

test('unavailable RUL gives an action based on this assessment, regardless of service capability', () => {
  const prediction = { predictions: { rul: null } }
  assert.match(rulUnavailableReason({ prediction, records: [records[0]] }), /at least two measured cycles/)
  assert.match(rulUnavailableReason({ prediction, records }), /Check the battery history and retry/)
  assert.equal(rulUnavailableReason({ prediction: { predictions: { rul: metric(0) } }, records }), '')
  assert.equal(displayRUL({ display: null, raw: 12.5 }), 12.5)
  assert.equal(displayRUL({ display: NaN, raw: 12.5 }), 12.5)
})

test('single records request the single contract and preserve a genuine null RUL', async () => {
  const originalFetch = globalThis.fetch
  let sent
  globalThis.fetch = async (_, options) => {
    sent = JSON.parse(options.body)
    return new Response(JSON.stringify({ results: [{ row_index: 0, metadata: { battery_id: '72' }, soh: metric(79.94589233398438), rul: null }] }))
  }
  try {
    const input = [{ ...records[0], battery_id: '72', cycle: 492 }]
    const result = await api.predict(input)
    assert.equal(sent.contract, 'single')
    assert.equal(result.metadata.cycle, 492)
    assert.equal(result.metadata.battery_id, '72')
    assert.equal(displayRUL(result.predictions.rul), undefined)
  } finally { globalThis.fetch = originalFetch }
})
