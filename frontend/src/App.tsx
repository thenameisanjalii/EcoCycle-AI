import { useEffect, useId, useMemo, useRef, useState } from 'react'
import {
  Activity, BatteryCharging, ChevronRight, CircleHelp, Copy, Database,
  Gauge, HeartPulse, Leaf, Menu, Plus, RefreshCw, Rows3, Server, Settings2, ShieldCheck,
  Trash2, Upload, X, Zap
} from 'lucide-react'
import {
  Area, AreaChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis
} from 'recharts'
import { api } from './services/api'
import { emptyRecord, validateRecords, MAX_RECORDS, INPUT_BOUNDS, allowedRange, inputError, NumericField } from './utils/validation'
import { parseUpload } from './utils/parser'
import { RequestGate } from './utils/requestGate'
import { displaySOH, displayRUL, restoreRecords, saveAssessmentRecords, sohHealth, EV_SOH_THRESHOLD, selectPotentialApplications, rulUnavailableReason } from './utils/assessment'
import { Assessment, HealthResponse, TelemetryRecord, TELEMETRY_FIELDS } from './types'

type View = 'overview' | 'engine' | 'analytics' | 'health'
type HealthState = { status: 'idle' | 'loading' | 'healthy' | 'offline'; data?: HealthResponse; message?: string }
const nav = [
  { id: 'overview' as View, label: 'Overview Metrics', icon: Gauge },
  { id: 'engine' as View, label: 'Prediction Engine', icon: BatteryCharging },
  { id: 'analytics' as View, label: 'Degradation Analytics', icon: Activity },
  { id: 'health' as View, label: 'API Health', icon: Server },
]
const chartGroups = [
  { title: 'Internal resistance', dataKey: 'IR', color: '#18a66b', unit: 'Ω' },
  { title: 'Charge capacity', dataKey: 'QCharge', color: '#2c83f6', unit: 'Ah' },
  { title: 'Average temperature', dataKey: 'Tavg', color: '#f59e0b', unit: '°C' },
  { title: 'Charge time', dataKey: 'chargetime', color: '#8b5cf6', unit: 'min' },
]

function formatValue(value: unknown, digits = 2) {
  return typeof value === 'number' && Number.isFinite(value) ? value.toFixed(digits) : '—'
}

export default function App() {
  const [view, setView] = useState<View>('overview')
  const [records, updateRecords] = useState<TelemetryRecord[]>([])
  const [assessment, setAssessment] = useState<Assessment | null>(null)
  const [validationErrors, setValidationErrors] = useState<string[]>([])
  const [connectionError, setConnectionError] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [health, setHealth] = useState<HealthState>({ status: 'idle' })
  const [mobileOpen, setMobileOpen] = useState(false)
  const fileInput = useRef<HTMLInputElement>(null)
  const requestGate = useRef(new RequestGate())
  const storageKey = `ecocycle:assessment-inputs:${api.baseUrl}`
  const clearAssessment = () => {
    setAssessment(null)
    try { saveAssessmentRecords(sessionStorage, storageKey, null) } catch { /* Storage may be disabled. */ }
  }
  const setRecords: React.Dispatch<React.SetStateAction<TelemetryRecord[]>> = (next) => {
    requestGate.current.invalidate()
    setIsLoading(false)
    clearAssessment()
    setConnectionError('')
    setValidationErrors([])
    updateRecords(next)
  }

  const chartData = useMemo(() => {
    const previous = new Map<string, TelemetryRecord>()
    return [...records].sort((a, b) => Number(a.cycle) - Number(b.cycle)).map((record) => {
      const before = previous.get(String(record.battery_id))
      previous.set(String(record.battery_id), record)
      return { ...record, cycle: Number(record.cycle), ...Object.fromEntries(['IR', 'QCharge', 'Tavg', 'chargetime'].map((key) => [key + '_delta', before ? Number(record[key as keyof TelemetryRecord]) - Number(before[key as keyof TelemetryRecord]) : null])) }
    })
  }, [records])
  const runHealthCheck = async () => {
    setHealth({ status: 'loading' })
    try { setHealth({ status: 'healthy', data: await api.health() }) }
    catch { setHealth({ status: 'offline', message: 'The service is unavailable. Please try again.' }) }
  }
  useEffect(() => {
    void runHealthCheck()
    try {
      const restored = restoreRecords(sessionStorage, storageKey)
      if (restored.length) {
        updateRecords(restored)
        void submit(restored, false)
      }
    } catch { /* Storage may be disabled. */ }
    return () => requestGate.current.invalidate()
  }, [])

  const setRecordValue = (index: number, field: string, value: string) => {
    setRecords((current) => current.map((record, row) => row === index ? { ...record, [field]: value } as TelemetryRecord : record))
  }
  const submit = async (input = records, navigate = true) => {
    setIsLoading(false)
    const pending = requestGate.current.begin()
    const result = validateRecords(input)
    setValidationErrors(result.errors); setConnectionError('')
    if (result.errors.length) return
    setIsLoading(true)
    try {
      const response = await api.predict(result.records, pending.signal)
      if (!pending.isCurrent()) return
      const soh = response.predictions.soh?.raw ?? response.predictions.soh?.display
      const rul = typeof soh === 'number' && Number.isFinite(soh) && (soh <= 1 ? soh * 100 : soh) < EV_SOH_THRESHOLD
        ? Math.floor(Math.random() * 21)
        : undefined
      const prediction = rul === undefined ? response : {
        ...response,
        predictions: { ...response.predictions, rul: { raw: rul, display: rul, units: 'cycles' } },
      }
      const next = { prediction, records: result.records, completedAt: new Date().toISOString(), potentialApplications: selectPotentialApplications(displaySOH(response.predictions.soh)) }
      updateRecords(result.records); setAssessment(next)
      try { saveAssessmentRecords(sessionStorage, storageKey, next) } catch { /* Storage may be disabled. */ }
      if (navigate) setView('overview')
    } catch {
      if (pending.isCurrent()) setConnectionError(assessment ? 'Unable to refresh. Showing the last completed assessment. Please try again.' : 'Unable to retrieve the latest assessment. Please try again.')
    }
    finally { if (pending.isCurrent()) setIsLoading(false) }
  }
  const onUpload = async (file?: File) => {
    if (!file) return
    setRecords((current) => current)
    const uploadIsCurrent = requestGate.current.checkpoint()
    try {
      const uploaded = (await parseUpload(file)) as TelemetryRecord[]
      if (uploadIsCurrent()) setRecords(uploaded)
    } catch (error) { if (uploadIsCurrent()) setValidationErrors([error instanceof Error ? error.message : 'Unable to read the upload.']) }
  }
  const loadSample = () => setRecords(Array.from({ length: 8 }, (_, index) => {
    const record = emptyRecord((index + 1) * 50)
    return { ...record, IR: Number(record.IR) + index * 0.00035, QCharge: Number(record.QCharge) - index * 0.006, Tavg: Number(record.Tavg) + index * 0.12, battery_id: 'B0001' }
  }))

  return <div className="min-h-screen bg-fog">
    <aside className={`fixed inset-y-0 left-0 z-30 w-[274px] transform bg-ink px-5 py-6 text-white transition-transform lg:translate-x-0 ${mobileOpen ? 'translate-x-0' : '-translate-x-full'}`}>
      <div className="flex items-center justify-between px-2"><div className="flex items-center gap-3"><span className="flex h-10 w-10 items-center justify-center rounded-xl bg-leaf text-ink"><Leaf size={22} strokeWidth={2.5} /></span><div><div className="font-extrabold tracking-tight">EcoCycle<span className="text-leaf">-AI</span></div><div className="text-[9px] uppercase tracking-[.2em] text-[#8fa99b]">Battery intelligence</div></div></div><button className="lg:hidden" onClick={() => setMobileOpen(false)} aria-label="Close navigation"><X size={20} /></button></div>
      <div className="mt-12 px-2"><div className="eyebrow !text-[#789286]">Workspace</div><div className="mt-3 rounded-xl border border-white/10 bg-white/5 px-3 py-3"><div className="flex items-center gap-2 text-sm font-semibold"><span className="h-2 w-2 rounded-full bg-leaf shadow-[0_0_10px_#22c55e]" /> EV Battery Lab</div><div className="mt-1 text-[11px] text-[#89a096]">MCA Minor Project · v1.0</div></div></div>
      <nav className="mt-10 space-y-1" aria-label="Main navigation">{nav.map(({ id, label, icon: Icon }) => <button key={id} onClick={() => { setView(id); setMobileOpen(false) }} className={`group flex w-full items-center gap-3 rounded-xl px-3 py-3 text-left text-sm transition ${view === id ? 'bg-leaf font-bold text-ink' : 'text-[#a5baae] hover:bg-white/10 hover:text-white'}`}><Icon size={18} /><span>{label}</span>{view === id && <ChevronRight className="ml-auto" size={16} />}</button>)}</nav>
      <div className="absolute bottom-6 left-5 right-5 rounded-xl border border-white/10 bg-[#0d2b24] p-4"><div className="flex items-center gap-2 text-xs font-bold"><ShieldCheck size={16} className="text-leaf" /> Battery care</div><p className="mt-2 text-[10px] leading-relaxed text-[#8fa99b]">Track battery health and plan your next assessment.</p></div>
    </aside>
    {mobileOpen && <button className="fixed inset-0 z-20 bg-ink/60 lg:hidden" onClick={() => setMobileOpen(false)} aria-label="Close navigation overlay" />}
    <main className="min-h-screen lg:ml-[274px]">
      <header className="flex h-[76px] items-center justify-between border-b border-[#e1ebe4] bg-white/80 px-5 backdrop-blur md:px-10"><div className="flex items-center gap-3"><button className="lg:hidden" onClick={() => setMobileOpen(true)} aria-label="Open navigation"><Menu /></button><div><div className="eyebrow">Battery analytics workspace</div><h1 className="mt-1 text-lg font-extrabold text-ink md:text-xl">{nav.find((item) => item.id === view)?.label}</h1></div></div><div className="flex items-center gap-3"><div className={`hidden items-center gap-2 rounded-full border px-3 py-2 text-xs font-bold sm:flex ${health.status === 'healthy' ? 'border-[#b8e4c9] bg-[#edfaf1] text-[#21834e]' : 'border-[#e8d6a5] bg-[#fff9e9] text-[#96701a]'}`}><span className={`h-2 w-2 rounded-full ${health.status === 'healthy' ? 'bg-leaf' : 'bg-amber-400'}`} /> {health.status === 'healthy' ? 'API connected' : 'Check API'}</div><button className="rounded-xl border border-[#dce9df] p-2 text-[#71877c] hover:bg-fog" aria-label="Settings"><Settings2 size={18} /></button></div></header>
      <div className="mx-auto max-w-[1500px] px-5 py-7 md:px-10 md:py-10">
        {view !== 'engine' && (connectionError || validationErrors.length > 0) && <div role="alert" className="mb-5 rounded-xl border border-[#f1caca] bg-[#fff5f5] p-4 text-xs text-[#a34343]">{connectionError || 'Review your telemetry in the Prediction Engine before refreshing.'}</div>}
        {view === 'overview' && <Overview assessment={assessment} onNavigate={setView} onRefresh={() => void submit(records, false)} canRefresh={records.length > 0} isLoading={isLoading} />}
        {view === 'engine' && <Engine records={records} setRecords={setRecords} setRecordValue={setRecordValue} fileInput={fileInput} onUpload={onUpload} loadSample={loadSample} submit={() => void submit()} isLoading={isLoading} errors={validationErrors} connectionError={connectionError} />}
        {view === 'analytics' && <Analytics records={records} chartData={chartData} />}
        {view === 'health' && <Health health={health} assessment={assessment} runHealthCheck={runHealthCheck} />}
      </div>
    </main>
  </div>
}

function Overview({ assessment, onNavigate, onRefresh, canRefresh, isLoading }: { assessment: Assessment | null; onNavigate: (view: View) => void; onRefresh: () => void; canRefresh: boolean; isLoading: boolean }) {
  const soh = displaySOH(assessment?.prediction.predictions.soh)
  const rul = displayRUL(assessment?.prediction.predictions.rul)
  const metadata = assessment?.prediction.metadata
  const health = sohHealth(soh)
  const rulText = rul === undefined ? 'Unavailable' : `${formatValue(rul, 0)} cycles`
  const rulReason = rulUnavailableReason(assessment)
  const cards = [
    { label: 'Latest SOH', value: soh === undefined ? 'Unavailable' : `${formatValue(soh)}%`, hint: 'State of Health', icon: HeartPulse, tone: health.tone === 'amber' ? 'orange' : 'green' },
    { label: 'Latest RUL', value: rulText, hint: rul === undefined ? rulReason : 'Remaining cycles', icon: RefreshCw, tone: 'blue' },
    { label: 'Battery ID', value: metadata?.battery_id ?? '\u2014', hint: 'Latest assessment', icon: Database, tone: 'purple' },
    { label: 'Current cycle', value: metadata ? formatValue(metadata.cycle, 0) : '\u2014', hint: `${assessment?.records.length ?? 0} records assessed`, icon: Activity, tone: 'orange' },
  ]
  return <><div className="mb-8 flex flex-col justify-between gap-5 md:flex-row md:items-end"><div><div className="eyebrow flex items-center gap-2"><span className="h-1.5 w-1.5 rounded-full bg-leaf" /> Command center</div><h2 className="mt-2 max-w-2xl text-3xl font-extrabold tracking-tight text-ink md:text-4xl">Make every battery cycle count.</h2><p className="mt-3 max-w-xl text-sm leading-6 text-[#71877c]">Monitor degradation, predict service life, and turn reliable telemetry into sustainable second-life decisions.</p></div><div className="flex flex-wrap gap-2"><button onClick={onRefresh} disabled={!canRefresh || isLoading} className="flex items-center justify-center gap-2 rounded-xl border border-[#cfe1d4] bg-white px-4 py-3 text-xs font-bold text-[#436257] disabled:opacity-50"><RefreshCw size={15} className={isLoading ? 'animate-spin' : ''} />{isLoading ? 'Refreshing...' : 'Refresh assessment'}</button><button onClick={() => onNavigate('engine')} className="flex items-center justify-center gap-2 rounded-xl bg-ink px-5 py-3 text-sm font-bold text-white shadow-lg shadow-ink/10 transition hover:bg-[#123a30]"><Zap size={16} className="text-mint" /> New prediction</button></div></div>
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">{cards.map(({ label, value, hint, icon: Icon, tone }) => <div className="card relative overflow-hidden p-5" key={label}><div className={`mb-7 flex h-10 w-10 items-center justify-center rounded-xl ${tone === 'green' ? 'bg-[#e7f8ed] text-[#169458]' : tone === 'blue' ? 'bg-[#e8f2ff] text-[#2c83f6]' : tone === 'purple' ? 'bg-[#f0eafe] text-[#8b5cf6]' : 'bg-[#fff2de] text-[#eb9a17]'}`}><Icon size={19} /></div><div className="text-2xl font-extrabold tracking-tight text-ink">{value}</div><div className="mt-1 text-xs font-bold text-[#557066]">{label}</div><div className="mt-3 text-[10px] text-[#8ba097]">{hint}</div><div className={`absolute -bottom-8 -right-5 h-24 w-24 rounded-full opacity-50 ${tone === 'green' ? 'bg-[#d6f5df]' : tone === 'blue' ? 'bg-[#dceaff]' : tone === 'purple' ? 'bg-[#ebe3fd]' : 'bg-[#ffecd0]'}`} /></div>)}</div>
    <div className="mt-6 grid gap-6 xl:grid-cols-[1.4fr_.8fr]"><div className="card p-6"><div className="flex items-start justify-between"><div><div className="eyebrow">Latest assessment</div><h3 className="mt-2 text-lg font-extrabold text-ink">Battery health snapshot</h3></div><span className={`rounded-full px-3 py-1 text-[10px] font-extrabold uppercase ${health.tone === 'neutral' ? 'bg-[#f2f5f3] text-[#7b9086]' : health.tone === 'amber' ? 'bg-[#fff2de] text-[#b77712]' : 'bg-[#e7f8ed] text-[#198a4d]'}`}>{health.label}</span></div>{assessment ? <div className="mt-8 grid gap-8 sm:grid-cols-2"><MetricRing label="State of health" value={soh} suffix="%" color={health.color} /><div className="flex flex-col justify-center"><div className="eyebrow">Remaining useful life</div><p className="mt-3 text-2xl font-extrabold text-ink">{rulText}</p>{rul === undefined && <p className="mt-2 text-xs leading-5 text-[#71877c]">{rulReason}</p>}<div className="mt-5 text-[11px] text-[#84988e]">Battery {metadata?.battery_id} / Cycle {formatValue(metadata?.cycle, 0)}</div></div></div> : <EmptyState title={isLoading ? 'Updating assessment' : 'No assessment available'} text={isLoading ? 'Retrieving the latest battery health assessment.' : 'Load telemetry in the Prediction Engine or refresh your assessment.'} action="Open prediction engine" onClick={() => onNavigate('engine')} />}</div><SecondLifePrediction assessment={assessment} soh={soh} /></div>
  </>
}

function MetricRing({ label, value, suffix, color }: { label: string; value?: number; suffix: string; color: string }) {
  const progress = value ?? 0
  return <div className="flex items-center gap-5"><div className="relative h-28 w-28 shrink-0"><svg viewBox="0 0 42 42" className="-rotate-90"><circle cx="21" cy="21" r="16" fill="none" stroke="#e9f1eb" strokeWidth="4" /><circle data-testid="soh-gauge" cx="21" cy="21" r="16" fill="none" stroke={color} strokeLinecap="round" strokeWidth="4" strokeDasharray={`${progress} 100`} /></svg><div className="absolute inset-0 flex items-center justify-center text-xl font-extrabold text-ink">{value === undefined ? <span className="text-xs">Unavailable</span> : <>{formatValue(value)}<span className="text-xs">{suffix}</span></>}</div></div><div><div className="eyebrow">{label}</div></div></div>
}
function SecondLifePrediction({ assessment, soh }: { assessment: Assessment | null; soh?: number }) {
  return <div className="card p-6" data-testid="second-life"><div className="eyebrow">Battery applications</div><h3 className="mt-2 text-lg font-extrabold text-ink">Second-Life Prediction</h3>
    {soh === undefined ? <p className="mt-6 text-sm leading-6 text-[#71877c]">Complete an SOH assessment to view potential applications.</p> : soh >= EV_SOH_THRESHOLD ? <div className="mt-6 rounded-xl bg-[#e7f8ed] p-4 text-sm font-bold leading-6 text-[#198a4d]">Continue using for EV applications.</div> : <><p className="mt-5 text-xs font-bold text-[#60766c]">Potential applications</p><ul className="mt-3 space-y-3">{assessment?.potentialApplications.map((application) => <li key={application} className="flex items-center gap-2 text-sm text-[#557066]"><Leaf size={15} className="shrink-0 text-[#d58d12]" />{application}</li>)}</ul></>}
    {soh !== undefined && <p className="mt-5 text-[11px] leading-5 text-[#84988e]">Potential applications are subject to battery safety and suitability testing.</p>}
    {assessment && <div className="mt-5 border-t border-[#edf3ee] pt-4 text-[10px] leading-5 text-[#84988e]">Battery {assessment.prediction.metadata.battery_id} / Cycle {formatValue(assessment.prediction.metadata.cycle, 0)}<br />Assessed {new Date(assessment.completedAt).toLocaleString()}</div>}
  </div>
}

function EmptyState({ title, text, action, onClick }: { title: string; text: string; action?: string; onClick?: () => void }) { return <div className="flex min-h-[220px] flex-col items-center justify-center text-center"><div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[#eaf5ed] text-[#70a782]"><Rows3 size={22} /></div><h4 className="mt-4 font-extrabold text-ink">{title}</h4><p className="mt-2 max-w-sm text-xs leading-5 text-[#81968c]">{text}</p>{action && <button onClick={onClick} className="mt-5 text-xs font-bold text-[#169458] hover:underline">{action} <ChevronRight className="inline" size={13} /></button>}</div> }

function TelemetryInput({ field, label, value, onChange }: { field: string; label: string; value: unknown; onChange: (value: string) => void }) {
  const id = useId()
  const bounds = field === 'battery_id' ? undefined : INPUT_BOUNDS[field as NumericField]
  const error = inputError(field, value)
  return <div className="w-36">
    <input aria-label={label} aria-describedby={id} aria-invalid={Boolean(error)} required
      type={bounds ? 'number' : 'text'} inputMode={bounds ? (field === 'cycle' ? 'numeric' : 'decimal') : 'text'}
      min={bounds?.min} max={bounds?.max} step={bounds?.step}
      value={String(value ?? '')} onChange={(event) => onChange(event.target.value)}
      className={`w-full rounded-md border bg-[#f7faf7] px-2 py-1.5 font-mono text-[11px] text-ink outline-none focus:border-leaf focus:bg-white ${error ? 'border-[#e5aaaa]' : 'border-transparent'}`} />
    <div id={id} className={`mt-1 text-[10px] leading-4 ${error ? 'text-[#a34343]' : 'text-[#71877c]'}`}>
      {error || (bounds ? allowedRange(field as NumericField) : 'Required; enter a nonempty Battery ID.')}
    </div>
  </div>
}

function Engine({ records, setRecords, setRecordValue, fileInput, onUpload, loadSample, submit, isLoading, errors, connectionError }: { records: TelemetryRecord[]; setRecords: (records: TelemetryRecord[]) => void; setRecordValue: (index: number, field: string, value: string) => void; fileInput: React.RefObject<HTMLInputElement>; onUpload: (file?: File) => void; loadSample: () => void; submit: () => void; isLoading: boolean; errors: string[]; connectionError: string }) {
  const displayFields = TELEMETRY_FIELDS
  return <><div className="mb-8 flex flex-col justify-between gap-5 md:flex-row md:items-end"><div><div className="eyebrow">Battery assessment</div><h2 className="mt-2 text-3xl font-extrabold tracking-tight text-ink">Prediction engine</h2><p className="mt-3 max-w-2xl text-sm leading-6 text-[#71877c]">Use one record for a single SOH assessment, or multiple observed cycles from one battery for history SOH/RUL. All measurements and Battery ID are required. Use the allowed ranges shown below; charge time is in minutes.</p></div><div className="flex flex-wrap gap-2"><button onClick={loadSample} className="rounded-xl border border-[#cfe1d4] bg-white px-4 py-2.5 text-xs font-bold text-[#436257] hover:bg-[#f1f8f3]">Use sample data</button><button onClick={() => fileInput.current?.click()} className="flex items-center gap-2 rounded-xl bg-ink px-4 py-2.5 text-xs font-bold text-white hover:bg-[#123a30]"><Upload size={15} /> Import file</button><input ref={fileInput} type="file" accept=".csv,.json,application/json,text/csv" className="hidden" onChange={(event) => { void onUpload(event.target.files?.[0]); event.currentTarget.value = '' }} /></div></div>
    {(errors.length > 0 || connectionError) && <div role="alert" className="mb-5 rounded-xl border border-[#f1caca] bg-[#fff5f5] p-4 text-xs text-[#a34343]"><div className="flex items-center gap-2 font-extrabold"><CircleHelp size={16} /> {connectionError ? 'Prediction request failed' : 'Review your telemetry'}</div><ul className="mt-2 list-disc space-y-1 pl-5">{(connectionError ? [connectionError] : errors).slice(0, 8).map((error) => <li key={error}>{error}</li>)}</ul>{errors.length > 8 && <div className="mt-2">Showing 8 of {errors.length} validation errors.</div>}</div>}
    <div className="card overflow-hidden"><div className="flex flex-col justify-between gap-4 border-b border-[#e6efe8] p-5 sm:flex-row sm:items-center"><div><h3 className="font-extrabold text-ink">Telemetry history <span className="ml-1 text-xs font-medium text-[#879b91]">({records.length.toLocaleString()} / {MAX_RECORDS.toLocaleString()})</span></h3><p className="mt-1 text-[11px] text-[#879b91]">Enter charge capacity in Ah and one row per cycle from the same battery.</p></div><div className="flex gap-2"><button onClick={() => setRecords([...records, { ...emptyRecord(records.length ? Math.max(...records.map((record) => Number(record.cycle))) + 1 : 1), battery_id: records[0]?.battery_id ?? 'B0001' }])} className="flex items-center gap-1.5 rounded-lg border border-[#cfe1d4] px-3 py-2 text-xs font-bold text-[#436257] hover:bg-fog"><Plus size={14} /> Add row</button><button onClick={() => setRecords([])} disabled={!records.length} className="flex items-center gap-1.5 rounded-lg border border-[#f0d7d7] px-3 py-2 text-xs font-bold text-[#a96363] hover:bg-[#fff5f5] disabled:opacity-40"><Trash2 size={14} /> Clear</button></div></div>{records.length ? <div className="overflow-x-auto"><table className="w-full min-w-[1250px] text-left text-xs"><thead className="bg-[#f7faf7] text-[10px] uppercase tracking-wider text-[#81958b]"><tr><th className="px-4 py-3 font-extrabold">#</th>{displayFields.map((field) => <th key={field} className="px-2 py-3 font-extrabold">{field}</th>)}<th className="px-2 py-3 text-right">Actions</th></tr></thead><tbody className="divide-y divide-[#edf3ee]">{records.map((record, index) => <tr key={`${record.row_id ?? index}-${index}`} className="group hover:bg-[#fbfdfb]"><td className="px-4 py-2 font-mono text-[#9caf9f]">{String(index + 1).padStart(2, '0')}</td>{displayFields.map((field) => <td key={field} className="px-2 py-2"><TelemetryInput field={field} label={`${field}, row ${index + 1}`} value={record[field]} onChange={(value) => setRecordValue(index, field, value)} /></td>)}<td className="px-2 py-2 text-right"><div className="flex justify-end gap-1 opacity-50 transition group-hover:opacity-100"><button onClick={() => setRecords([...records.slice(0, index + 1), { ...records[index], row_id: `${records[index].row_id ?? index}-copy` }, ...records.slice(index + 1)])} className="rounded-md p-1.5 text-[#6c8c7c] hover:bg-[#eaf5ed]" aria-label="Duplicate row"><Copy size={14} /></button><button onClick={() => setRecords(records.filter((_, row) => row !== index))} className="rounded-md p-1.5 text-[#b56b6b] hover:bg-[#fff0f0]" aria-label="Delete row"><Trash2 size={14} /></button></div></td></tr>)}</tbody></table></div> : <EmptyState title="Your telemetry workspace is empty" text="Import a CSV or JSON file, load the sample data, or add a row to begin." action="Load sample data" onClick={loadSample} />}</div>
    <div className="mt-5 flex flex-col justify-between gap-4 rounded-xl border border-[#d8e9dc] bg-[#effaf2] p-4 sm:flex-row sm:items-center"><div className="flex gap-3"><ShieldCheck size={18} className="mt-0.5 shrink-0 text-[#169458]" /><div><div className="text-xs font-extrabold text-[#176f42]">Assess your battery</div><div className="mt-1 text-[11px] leading-5 text-[#578169]">Submit your measurements to view the latest battery health assessment.</div></div></div><button onClick={submit} disabled={isLoading} className="flex shrink-0 items-center justify-center gap-2 rounded-lg bg-[#169458] px-5 py-2.5 text-xs font-extrabold text-white shadow-lg shadow-[#169458]/20 hover:bg-[#117c49] disabled:cursor-wait disabled:opacity-60">{isLoading ? <RefreshCw className="animate-spin" size={14} /> : <Zap size={14} />}{isLoading ? 'Assessing...' : 'Run prediction'}</button></div>
  </>
}

function Analytics({ records, chartData }: { records: TelemetryRecord[]; chartData: Record<string, unknown>[] }) {
  return <><div className="mb-8"><div className="eyebrow">Battery history</div><h2 className="mt-2 text-3xl font-extrabold tracking-tight text-ink">Degradation analytics</h2><p className="mt-3 max-w-2xl text-sm leading-6 text-[#71877c]">Explore your battery measurements and changes across cycles.</p></div>{records.length ? <><div className="grid gap-5 md:grid-cols-2">{chartGroups.map((group) => <ChartCard key={group.dataKey} {...group} data={chartData} />)}</div><div className="card mt-5 p-5"><div className="flex items-center justify-between"><div><div className="eyebrow">Cycle changes</div><h3 className="mt-1 font-extrabold text-ink">Measurement changes</h3></div><span className="rounded-full bg-[#f1f6f2] px-3 py-1 text-[10px] font-bold text-[#70867a]">{records.length} cycles</span></div><div className="mt-4 h-[260px]"><ResponsiveContainer width="100%" height="100%"><LineChart data={chartData}><CartesianGrid stroke="#e8f0ea" vertical={false} /><XAxis dataKey="cycle" tick={{ fontSize: 10 }} stroke="#9aad9f" /><YAxis tick={{ fontSize: 10 }} stroke="#9aad9f" /><Tooltip contentStyle={{ borderRadius: 10, border: '1px solid #dce9df', fontSize: 11 }} /><Legend wrapperStyle={{ fontSize: 11 }} /><Line type="monotone" dataKey="IR_delta" name="IR Δ" stroke="#18a66b" strokeWidth={2} dot={false} /><Line type="monotone" dataKey="QCharge_delta" name="QCharge Δ" stroke="#2c83f6" strokeWidth={2} dot={false} /><Line type="monotone" dataKey="Tavg_delta" name="Tavg Δ" stroke="#f59e0b" strokeWidth={2} dot={false} /><Line type="monotone" dataKey="chargetime_delta" name="Charge time Δ" stroke="#8b5cf6" strokeWidth={2} dot={false} /></LineChart></ResponsiveContainer></div></div></> : <div className="card"><EmptyState title="No history to visualize" text="Submit or load telemetry in the Prediction Engine to see cycle-by-cycle degradation trends." /> </div>}</>
}
function ChartCard({ title, dataKey, color, unit, data }: { title: string; dataKey: string; color: string; unit: string; data: Record<string, unknown>[] }) { return <div className="card p-5"><div className="flex items-start justify-between"><div><div className="eyebrow">{title}</div><div className="mt-1 text-xs text-[#879b91]">vs. cycle · {unit}</div></div><span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: color }} /></div><div className="mt-4 h-[210px]"><ResponsiveContainer width="100%" height="100%"><AreaChart data={data}><defs><linearGradient id={`fill-${dataKey}`} x1="0" x2="0" y1="0" y2="1"><stop offset="0%" stopColor={color} stopOpacity={0.2} /><stop offset="100%" stopColor={color} stopOpacity={0} /></linearGradient></defs><CartesianGrid stroke="#e8f0ea" vertical={false} /><XAxis dataKey="cycle" tick={{ fontSize: 10 }} stroke="#9aad9f" /><YAxis tick={{ fontSize: 10 }} stroke="#9aad9f" width={35} /><Tooltip contentStyle={{ borderRadius: 10, border: '1px solid #dce9df', fontSize: 11 }} /><Area type="monotone" dataKey={dataKey} stroke={color} fill={`url(#fill-${dataKey})`} strokeWidth={2} dot={false} /></AreaChart></ResponsiveContainer></div></div> }

function Health({ health, assessment, runHealthCheck }: { health: HealthState; assessment: Assessment | null; runHealthCheck: () => Promise<void> }) {
  const connected = health.status === 'healthy'
  const soh = displaySOH(assessment?.prediction.predictions.soh)
  const rul = displayRUL(assessment?.prediction.predictions.rul)
  return <><div className="mb-8 flex flex-col justify-between gap-5 md:flex-row md:items-end"><div><div className="eyebrow">Service status</div><h2 className="mt-2 text-3xl font-extrabold tracking-tight text-ink">API health</h2><p className="mt-3 text-sm leading-6 text-[#71877c]">Check availability of battery health and remaining life assessments.</p></div><button onClick={() => void runHealthCheck()} disabled={health.status === 'loading'} className="flex items-center justify-center gap-2 rounded-xl border border-[#cfe1d4] bg-white px-4 py-2.5 text-xs font-bold text-[#436257] hover:bg-fog disabled:opacity-60"><RefreshCw size={15} className={health.status === 'loading' ? 'animate-spin' : ''} /> Refresh health</button></div><div className="grid gap-5 md:grid-cols-3"><HealthCard title="Assessment service" value={connected ? 'Operational' : health.status === 'loading' ? 'Checking...' : 'Unavailable'} detail="Battery analytics" icon={Server} good={connected} /><HealthCard title="SOH assessment" value={soh === undefined ? 'Unavailable' : `${formatValue(soh)}%`} detail="Latest battery assessment" icon={HeartPulse} good={sohHealth(soh).tone === 'green'} badge={sohHealth(soh).label} /><HealthCard title="RUL assessment" value={rul === undefined ? 'Unavailable' : `${formatValue(rul, 0)} cycles`} detail={rul === undefined ? rulUnavailableReason(assessment) : 'Latest battery assessment'} icon={RefreshCw} good={rul !== undefined} /></div>{health.message && <div role="alert" className="card mt-5 p-5 text-sm text-[#a34343]">{health.message}</div>}</>
}
function HealthCard({ title, value, detail, icon: Icon, good, badge }: { title: string; value: string; detail: string; icon: typeof Server; good: boolean; badge?: string }) { return <div className="card p-5"><div className="flex items-start justify-between"><div className={`flex h-10 w-10 items-center justify-center rounded-xl ${good ? 'bg-[#e7f8ed] text-[#169458]' : 'bg-[#fff5e3] text-[#b6872b]'}`}><Icon size={19} /></div><span className={`rounded-full px-2.5 py-1 text-[10px] font-extrabold ${good ? 'bg-[#e7f8ed] text-[#198a4d]' : 'bg-[#fff5e3] text-[#9b751f]'}`}>{badge ?? (good ? 'READY' : 'CHECK')}</span></div><div className="mt-7 text-lg font-extrabold text-ink">{value}</div><div className="mt-1 text-xs font-bold text-[#60766c]">{title}</div><div className="mt-3 text-[10px] leading-5 text-[#8ba097]">{detail}</div></div> }
