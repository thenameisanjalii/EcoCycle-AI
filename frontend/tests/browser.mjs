// Optional browser regression: node tests/browser.mjs
// Uses an installed Chrome or BROWSER_PATH, and mocks only the API boundary.
import assert from 'node:assert/strict'
import { spawn } from 'node:child_process'
import { mkdtemp, writeFile, access, readFile } from 'node:fs/promises'
import { fileURLToPath, pathToFileURL } from 'node:url'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { setTimeout as delay } from 'node:timers/promises'
import { createServer } from 'vite'
import { loadTs } from './loadTs.mjs'

const chromePath = process.env.BROWSER_PATH || 'C:/Program Files/Google/Chrome/Application/chrome.exe'
await access(chromePath)
const profile = await mkdtemp(join(tmpdir(), 'ecocycle-browser-'))
const server = await createServer({ server: { host: '127.0.0.1', port: 0 }, logLevel: 'error' })
await server.listen()
const url = server.resolvedUrls.local[0]
const chrome = spawn(chromePath, ['--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check', '--remote-debugging-port=0', `--user-data-dir=${profile}`, '--window-size=1440,1100', 'about:blank'], { windowsHide: true, stdio: ['ignore', 'ignore', 'pipe'] })
let socket
try {
  const endpoint = await new Promise((resolve, reject) => {
    let output = ''
    const timer = setTimeout(() => reject(new Error('Chrome did not start')), 15000)
    chrome.on('error', reject)
    chrome.stderr.on('data', (chunk) => {
      output += chunk
      const match = output.match(/DevTools listening on (ws:\/\/[^\s]+)/)
      if (match) { clearTimeout(timer); resolve(match[1]) }
    })
  })
  socket = new WebSocket(endpoint)
  await new Promise((resolve, reject) => { socket.onopen = resolve; socket.onerror = reject })
  let id = 0
  const pending = new Map()
  const handlers = new Map()
  const send = (method, params = {}, sessionId) => new Promise((resolve, reject) => {
    const key = ++id
    pending.set(key, { resolve, reject })
    socket.send(JSON.stringify({ id: key, method, params, ...(sessionId ? { sessionId } : {}) }))
  })
  socket.onmessage = ({ data }) => {
    const message = JSON.parse(data)
    if (message.id) {
      const callback = pending.get(message.id)
      pending.delete(message.id)
      if (message.error) callback?.reject(Error(JSON.stringify(message.error)))
      else callback?.resolve(message.result)
    } else handlers.get(message.method)?.(message.params)
  }
  const target = await send('Target.createTarget', { url: 'about:blank' })
  const { sessionId } = await send('Target.attachToTarget', { targetId: target.targetId, flatten: true })
  const page = (method, params) => send(method, params, sessionId)
  await page('Runtime.enable')
  const errors = []
  handlers.set('Runtime.exceptionThrown', (event) => errors.push(event.exceptionDetails.text))
  let soh = 80
  let rul = 123
  let fail = false
  let responseDelay = 0
  let predictionCalls = 0
  let liveApi = false
  handlers.set('Fetch.requestPaused', async ({ requestId, request }) => {
    if (request.method === 'OPTIONS') {
      await page('Fetch.fulfillRequest', { requestId, responseCode: 204, responseHeaders: [{ name: 'Access-Control-Allow-Origin', value: '*' }, { name: 'Access-Control-Allow-Headers', value: '*' }, { name: 'Access-Control-Allow-Methods', value: 'POST,GET,OPTIONS' }] })
      return
    }
    if (liveApi) {
      if (request.url.endsWith('/predict')) predictionCalls++
      const response = await fetch(request.url, { method: request.method, headers: { 'Content-Type': 'application/json' }, ...(request.postData ? { body: request.postData } : {}) })
      await page('Fetch.fulfillRequest', { requestId, responseCode: response.status, responseHeaders: [{ name: 'Content-Type', value: 'application/json' }, { name: 'Access-Control-Allow-Origin', value: '*' }], body: Buffer.from(await response.text()).toString('base64') })
      return
    }
    let result = { status: 'healthy', models_available: { soh: true, rul: true } }
    const status = fail && request.url.endsWith('/predict') ? 503 : 200
    if (request.url.endsWith('/predict')) {
      predictionCalls++
      const records = JSON.parse(request.postData).records
      const latest = records.reduce((best, record, index) => Number(record.cycle) > Number(records[best].cycle) ? index : best, 0)
      // Deliberately omit metadata: the submitted battery ID must be preserved.
      result = { results: [{ row_index: latest, soh: soh === null ? null : { raw: soh, display: Math.max(0, Math.min(100, soh)) }, rul: rul === null ? null : { raw: rul, display: rul } }] }
    }
    if (responseDelay) await delay(responseDelay)
    await page('Fetch.fulfillRequest', { requestId, responseCode: status, responseHeaders: [{ name: 'Content-Type', value: 'application/json' }, { name: 'Access-Control-Allow-Origin', value: '*' }], body: Buffer.from(JSON.stringify(result)).toString('base64') }).catch(() => {})
  })
  await page('Fetch.enable', { patterns: [{ urlPattern: '*/v2/*' }] })
  const evaluate = async (expression) => {
    const result = await page('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true })
    if (result.exceptionDetails) throw Error(result.exceptionDetails.text)
    return result.result.value
  }
  const until = async (expression) => {
    const deadline = Date.now() + 15000
    do { if (await evaluate(expression)) return; await delay(75) } while (Date.now() < deadline)
    throw Error(`Timed out: ${expression}`)
  }
  const click = async (label) => {
    await until(`Array.from(document.querySelectorAll('button')).some(b => b.textContent.trim() === ${JSON.stringify(label)} && !b.disabled)`)
    await evaluate(`Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim() === ${JSON.stringify(label)}).click()`)
  }
  const card = (label) => `Array.from(document.querySelectorAll('.card')).find(c => Array.from(c.querySelectorAll('div')).some(d => d.textContent === ${JSON.stringify(label)}))?.innerText`
  const hasCard = (label, value) => `${card(label)}?.includes(${JSON.stringify(value)})`
  const input = async (label, value) => evaluate(`(() => { const field = document.querySelector('input[aria-label=${JSON.stringify(label)}]'); Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set.call(field, ${JSON.stringify(value)}); field.dispatchEvent(new Event('input', { bubbles: true })); })()`)
  const noInternalCopy = async () => assert.equal(await evaluate(`/model interpretation|pipeline|provenance|regression artifact|confidence|selection bias|display.safe|engineered features/i.test(document.body.innerText)`), false)

  const readRul = async (label) => {
    const text = await evaluate(card(label))
    const value = Number(text?.match(/(\d+) cycles/)?.[1])
    assert.ok(Number.isInteger(value) && value >= 0 && value <= 20)
    return value
  }

  await page('Page.navigate', { url })
  await until(`document.body.innerText.includes('No assessment available')`)
  if (process.argv.includes('--validation-only')) {
    const { INPUT_BOUNDS, emptyRecord } = await import(await loadTs(new URL('../src/utils/validation.ts', import.meta.url)))
    await click('New prediction')
    await click('Add row')
    const baseline = emptyRecord()
    for (const [field, bounds] of Object.entries(INPUT_BOUNDS)) {
      const label = `${field}, row 1`
      const selector = `input[aria-label=${JSON.stringify(label)}]`
      const attributes = await evaluate(`(() => { const e = document.querySelector(${JSON.stringify(selector)}); return { type: e.type, min: e.min, max: e.max, step: e.step, required: e.required, hint: document.getElementById(e.getAttribute('aria-describedby')).textContent }; })()`)
      assert.deepEqual(attributes, { type: 'number', min: String(bounds.min), max: String(bounds.max), step: String(bounds.step), required: true, hint: `Allowed range: ${bounds.min} to ${bounds.max} ${bounds.unit}.` })
      for (const endpoint of [bounds.min, bounds.max]) {
        await input(label, String(endpoint))
        assert.equal(await evaluate(`document.querySelector(${JSON.stringify(selector)}).checkValidity()`), true)
      }
      for (const value of ['', String(bounds.min - 1), String(bounds.max + 1), ...(field === 'cycle' ? ['1.5'] : [])]) {
        await input(label, value)
        await until(`document.querySelector(${JSON.stringify(selector)}).getAttribute('aria-invalid') === 'true'`)
        await click('Run prediction')
        assert.equal(predictionCalls, 0)
      }
      await input(label, String(baseline[field]))
    }
    for (const value of ['', '   ']) {
      await input('battery_id, row 1', value)
      await click('Run prediction')
      assert.equal(predictionCalls, 0)
      assert.equal(await evaluate(`document.body.innerText.includes('Battery ID is required')`), true)
    }
    await input('battery_id, row 1', '  new-cell-10000  ')
    await click('Run prediction')
    await until(hasCard('Battery ID', 'new-cell-10000'))
    assert.equal(predictionCalls, 1)
    const upload = async (path) => {
      await click('Prediction Engine')
      const { root } = await page('DOM.getDocument')
      const { nodeId } = await page('DOM.querySelector', { nodeId: root.nodeId, selector: 'input[type="file"]' })
      await page('DOM.setFileInputFiles', { nodeId, files: [fileURLToPath(new URL(path, import.meta.url))] })
    }
    await upload('../../examples/pipeline_v2/history.csv')
    await until(`Array.from(document.querySelectorAll('input[aria-invalid="true"]')).length > 0`)
    await click('Run prediction')
    assert.equal(predictionCalls, 1)
    assert.equal(await evaluate(`document.body.innerText.includes('IR is out of range')`), true)
    await upload('../../presentation_inputs/battery_2_near_80_soh.csv')
    await until(`Number(document.querySelector('input[aria-label="cycle, row 1"]').value) === 1177`)
    await click('Run prediction')
    await until(hasCard('Battery ID', '2'))
    assert.equal(predictionCalls, 2)
    console.log('PASS input types, ranges, decimal endpoints, required values, integer cycles, Battery ID and CSV validation')
  } else {
  await click('New prediction')
  await click('Use sample data')
  await click('Run prediction')
  await until(hasCard('Latest SOH', '79.00%'))
  await readRul('Latest RUL')
  assert.equal(await evaluate(hasCard('Battery ID', 'B0001')), true)
  assert.equal(await evaluate(hasCard('Current cycle', '400')), true)
  assert.equal(await evaluate(`document.querySelector('[data-testid="soh-gauge"]').getAttribute('stroke-dasharray')`), '79 100')
  await noInternalCopy()
  assert.equal(await evaluate(`document.querySelector('[data-testid="soh-gauge"]').getAttribute('stroke')`), '#f59e0b')
  assert.equal(await evaluate(`Array.from(document.querySelectorAll('span')).find(s => s.textContent === 'Monitor')?.className.includes('text-[#b77712]')`), true)
  const applicationList = `Array.from(document.querySelectorAll('[data-testid="second-life"] li')).map(li => li.textContent)`
  const selected = await evaluate(applicationList)
  assert.ok(selected.length >= 3 && selected.length <= 5)
  assert.equal(new Set(selected).size, selected.length)
  await click('API Health')
  await click('Refresh health')
  await click('Overview Metrics')
  assert.deepEqual(await evaluate(applicationList), selected)
  responseDelay = 300
  await click('Refresh assessment')
  assert.deepEqual(await evaluate(applicationList), selected)
  await until(`!Array.from(document.querySelectorAll('button')).some(b => b.textContent.includes('Refreshing'))`)
  responseDelay = 0
  soh = 81.99
  await click('Refresh assessment')
  await until(hasCard('Latest SOH', '80.99%'))
  assert.equal(await evaluate(`document.querySelector('[data-testid="soh-gauge"]').getAttribute('stroke')`), '#f59e0b')
  soh = 82
  await click('Refresh assessment')
  await until(hasCard('Latest SOH', '81.00%'))
  assert.equal(await evaluate(`document.querySelector('[data-testid="soh-gauge"]').getAttribute('stroke')`), '#18a66b')
  assert.equal(await evaluate(`document.body.innerText.includes('Continue using for EV applications.')`), true)
  assert.deepEqual(await evaluate(applicationList), [])
  console.log('PASS 81% gauge/badge threshold, stable unique recommendations, EV recommendation')

  soh = 65.5; rul = 45
  await click('Refresh assessment')
  await until(hasCard('Latest SOH', '64.50%'))
  await readRul('Latest RUL')
  const beforeReload = predictionCalls
  soh = 51; rul = 22
  await page('Page.reload')
  await until(hasCard('Latest SOH', '50.00%'))
  assert.ok(predictionCalls > beforeReload)
  await readRul('Latest RUL')
  console.log('PASS sample assessment, fresh refresh, page reload, card/gauge consistency')

  await click('Prediction Engine')
  const csvPath = fileURLToPath(new URL('../../presentation_inputs/battery_2_near_80_soh.csv', import.meta.url))
  const csv = (await readFile(csvPath, 'utf8')).trim().split(/\r?\n/)
  const columns = csv.shift().split(',')
  const latestRow = csv.map((line) => line.split(',')).sort((a, b) => Number(a[columns.indexOf('cycle')]) - Number(b[columns.indexOf('cycle')])).at(-1)
  const { root } = await page('DOM.getDocument')
  const { nodeId } = await page('DOM.querySelector', { nodeId: root.nodeId, selector: 'input[type="file"]' })
  await page('DOM.setFileInputFiles', { nodeId, files: [csvPath] })
  await until(`document.querySelectorAll('tbody tr').length === ${csv.length}`)
  await click('Run prediction')
  await until(hasCard('Battery ID', latestRow[columns.indexOf('battery_id')]))
  assert.equal(await evaluate(hasCard('Current cycle', String(Number(latestRow[columns.indexOf('cycle')])))), true)
  console.log('PASS importing existing battery CSV with matching battery ID and latest cycle')

  await click('Prediction Engine')
  await click('Clear')
  await click('Add row')
  await input('battery_id, row 1', 'submitted-42')
  await input('cycle, row 1', '900')
  soh = 0.5; rul = null
  await click('Run prediction')
  await until(hasCard('Battery ID', 'submitted-42'))
  assert.equal(await evaluate(hasCard('Current cycle', '900')), true)
  assert.equal(await evaluate(hasCard('Latest SOH', '0.00%')), true)
  const cycles = await readRul('Latest RUL')
  await click('API Health')
  assert.equal(await readRul('RUL assessment'), cycles)
  await click('Overview Metrics')
  soh = null
  await click('Refresh assessment')
  await until(hasCard('Latest SOH', 'Unavailable'))
  await until(`document.querySelector('[data-testid="soh-gauge"]') !== null`)
  assert.equal(await evaluate(`document.querySelector('[data-testid="soh-gauge"]').getAttribute('stroke-dasharray')`), '0 100')
  console.log('PASS new battery identity, synchronized cycle, SOH lower clamp, missing SOH/RUL')

  fail = true
  await click('Refresh assessment')
  await until(`document.body.innerText.includes('Unable to refresh. Showing the last completed assessment')`)
  assert.equal(await evaluate(hasCard('Latest RUL', 'Unavailable')), true)
  fail = false; soh = 105; rul = 0
  await click('Refresh assessment')
  await until(hasCard('Latest SOH', '100.00%'))
  assert.equal(await evaluate(hasCard('Latest RUL', '0')), true)
  await click('Degradation Analytics')
  await until(`document.body.innerText.includes('Measurement changes')`)
  await noInternalCopy()
  await click('API Health')
  await until(`document.body.innerText.includes('Assessment service')`)
  await noInternalCopy()
  await click('Overview Metrics')
  assert.equal(await evaluate(hasCard('Latest SOH', '100.00%')), true)
  const screenshot = await page('Page.captureScreenshot', { format: 'png', captureBeyondViewport: false })
  const screenshotPath = join(profile, 'overview.png')
  await writeFile(screenshotPath, Buffer.from(screenshot.data, 'base64'))
  console.log('PASS refresh failure and retry, upper clamp, zero RUL, navigation, removed internal copy')

  responseDelay = 700
  await click('Refresh assessment')
  await click('Prediction Engine')
  await input('battery_id, row 1', 'edited-during-request')
  await delay(900)
  await click('Overview Metrics')
  assert.equal(await evaluate(hasCard('Latest SOH', 'Unavailable')), true)
  assert.equal(await evaluate(hasCard('Battery ID', 'submitted-42')), false)
  assert.equal(await evaluate(`sessionStorage.length`), 0)
  console.log('PASS input edits invalidate delayed responses and saved assessment inputs')
  if (process.argv.includes('--live-api')) {
    liveApi = true
    responseDelay = 0
    const importLive = async (path) => {
      await click('Prediction Engine')
      const { root } = await page('DOM.getDocument')
      const { nodeId } = await page('DOM.querySelector', { nodeId: root.nodeId, selector: 'input[type="file"]' })
      await page('DOM.setFileInputFiles', { nodeId, files: [fileURLToPath(new URL(path, import.meta.url))] })
    }
    const battery72 = (await readFile(new URL('../../presentation_inputs/battery_72_near_80_soh.csv', import.meta.url), 'utf8')).trim().split(/\r?\n/)
    const singlePath = join(profile, 'battery_72_single.csv')
    await writeFile(singlePath, `${battery72[0]}\n${battery72.at(-1)}\n`)
    await importLive(pathToFileURL(singlePath))
    await until(`document.querySelector('input[aria-label="battery_id, row 1"]').value === '72'`)
    await click('Run prediction')
    await until(hasCard('Battery ID', '72'))
    assert.equal(await evaluate(hasCard('Current cycle', '492')), true)
    assert.equal(await evaluate(hasCard('Latest SOH', '78.95%')), true)
    const singleCycles = await readRul('Latest RUL')
    await click('API Health')
    assert.equal(await readRul('RUL assessment'), singleCycles)
    await importLive('../../examples/pipeline_v2/battery_72_history_to_cycle_492.csv')
    await until(`document.querySelectorAll('tbody tr').length === 492`)
    await click('Run prediction')
    await until(hasCard('Latest SOH', '78.90%'))
    assert.equal(await evaluate(hasCard('Battery ID', '72')), true)
    assert.equal(await evaluate(hasCard('Current cycle', '492')), true)
    const historyCycles = await readRul('Latest RUL')
    assert.equal(await evaluate(`Array.from(document.querySelectorAll('p')).some(p => p.textContent === '${historyCycles} cycles')`), true)
    const priorCalls = predictionCalls
    await click('Refresh assessment')
    await until(`!Array.from(document.querySelectorAll('button')).some(b => b.textContent.includes('Refreshing'))`)
    assert.ok(predictionCalls > priorCalls)
    const latestCycles = await readRul('Latest RUL')
    await click('API Health')
    assert.equal(await readRul('RUL assessment'), latestCycles)
    assert.equal(await evaluate(`${card('SOH assessment')}?.includes('Monitor')`), true)
    await click('Overview Metrics')
    const liveScreenshot = await page('Page.captureScreenshot', { format: 'png', captureBeyondViewport: false })
    await writeFile(join(profile, 'live-battery-72.png'), Buffer.from(liveScreenshot.data, 'base64'))
    console.log('PASS LIVE API battery 72: single record and 492 real cycles; refresh and all screens agree')
  }
  console.log(`Screenshot: ${screenshotPath}`)
  }
  assert.deepEqual(errors, [])
  console.log('PASS no uncaught browser errors')
} finally {
  socket?.close()
  chrome.kill()
  await server.close()
}
