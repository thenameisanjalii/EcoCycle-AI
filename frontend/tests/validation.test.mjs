import assert from 'node:assert/strict'
import test from 'node:test'
import { loadTs } from './loadTs.mjs'

const { INPUT_BOUNDS, allowedRange, emptyRecord, inputError, validateRecords } = await import(await loadTs(new URL('../src/utils/validation.ts', import.meta.url)))
const fields = Object.keys(INPUT_BOUNDS)

test('all numeric inputs accept both exact dataset endpoints and decimal strings', () => {
  for (const field of fields) {
    for (const value of [INPUT_BOUNDS[field].min, INPUT_BOUNDS[field].max]) {
      for (const input of [value, String(value)]) {
        assert.deepEqual(validateRecords([{ ...emptyRecord(), [field]: input }]).errors, [], `${field}: ${input}`)
      }
    }
  }
})

test('every numeric input rejects missing, nonnumeric, nonfinite and out-of-range values with its allowed range', () => {
  for (const field of fields) {
    const { min, max } = INPUT_BOUNDS[field]
    for (const value of [null, undefined, '', '  ', 'abc', 'NaN', 'Infinity', NaN, Infinity, -Infinity, true, false, [], {}, '0x10', '1_000', min - 0.000001, max + 0.000001]) {
      const result = validateRecords([{ ...emptyRecord(), [field]: value }])
      assert.ok(result.errors.some((error) => error.includes(field) && error.includes(allowedRange(field))), `${field}: ${String(value)}`)
    }
    const record = emptyRecord()
    delete record[field]
    assert.ok(validateRecords([record]).errors.some((error) => error.includes(`${field} is required`)))
  }
})

test('cycles require integers; sensor measurements preserve arbitrary decimal precision', () => {
  assert.match(inputError('cycle', 2.5), /whole number/)
  assert.equal(INPUT_BOUNDS.cycle.step, 1)
  for (const field of fields.filter((field) => field !== 'cycle')) {
    assert.equal(INPUT_BOUNDS[field].step, 'any')
    assert.equal(inputError(field, (INPUT_BOUNDS[field].min + INPUT_BOUNDS[field].max) / 2), '')
  }
})

test('Battery ID is required, trimmed and independent of numeric dataset limits', () => {
  for (const id of [undefined, null, '', ' \t ', true, false, [], {}, NaN, Infinity, 1.5]) {
    assert.match(inputError('battery_id', id), /Battery ID.*required/)
  }
  for (const id of [0, -1, 10000, 'new-cell', '0', '  cell-A  ']) {
    const result = validateRecords([{ ...emptyRecord(), battery_id: id }])
    assert.deepEqual(result.errors, [])
    assert.equal(result.records[0].battery_id, typeof id === 'string' ? id.trim() : id)
  }
})

test('history identity and cycle checks operate on normalized records', () => {
  assert.ok(validateRecords([emptyRecord(1), emptyRecord(1)]).errors.some((error) => /Duplicate/.test(error)))
  assert.ok(validateRecords([emptyRecord(1), { ...emptyRecord(2), battery_id: 'other' }]).errors.some((error) => /exactly one battery/.test(error)))
  assert.deepEqual(validateRecords([{ ...emptyRecord(2), battery_id: ' A ' }, { ...emptyRecord(1), battery_id: 'A' }]).errors, [])
})
