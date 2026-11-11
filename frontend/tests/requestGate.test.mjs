import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'
import ts from 'typescript'

// Execute the actual TS utility with the project's installed compiler.
const source = await readFile(new URL('../src/utils/requestGate.ts', import.meta.url), 'utf8')
const js = ts.transpileModule(source, { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ES2022 } }).outputText
const { RequestGate } = await import(`data:text/javascript;base64,${Buffer.from(js).toString('base64')}`)

test('input edits abort the request and reject its delayed response', async () => {
  const gate = new RequestGate()
  const request = gate.begin()
  let resolve
  const delayed = new Promise((done) => { resolve = done })
  let displayed = null
  const update = delayed.then((result) => { if (request.isCurrent()) displayed = result })
  gate.invalidate()
  resolve('stale prediction')
  await update
  assert.equal(request.signal.aborted, true)
  assert.equal(displayed, null)
})

test('new submissions supersede older requests even if fetch ignores abort', () => {
  const gate = new RequestGate()
  const older = gate.begin()
  const latest = gate.begin()
  assert.equal(older.isCurrent(), false)
  assert.equal(latest.isCurrent(), true)
  gate.invalidate() // clear, delete, upload, edit, sample replacement or unmount
  assert.equal(latest.isCurrent(), false)
})

test('a slow upload cannot overwrite more recent edits or another upload', () => {
  const gate = new RequestGate()
  const oldUpload = gate.checkpoint()
  gate.invalidate()
  const newUpload = gate.checkpoint()
  assert.equal(oldUpload(), false)
  assert.equal(newUpload(), true)
  gate.invalidate()
  assert.equal(newUpload(), false)
})
