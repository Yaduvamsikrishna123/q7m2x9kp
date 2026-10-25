import { useEffect, useMemo, useState, type ReactNode } from 'react'
import { Activity, AlertTriangle, CalendarDays, CheckCircle2, Clock3, Download, RefreshCw, Wind, Zap } from 'lucide-react'
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { getComparison, type ComparisonResponse } from './api'

const fmt = (value: number | null | undefined) => value == null ? '—' : `${value.toLocaleString(undefined, { maximumFractionDigits: 1 })} MW`
const timeLabel = (iso: string) => new Date(iso).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', timeZone: 'UTC' })

export default function App() {
  const [date, setDate] = useState('2026-01-15')
  const [cutoff, setCutoff] = useState(18)
  const [data, setData] = useState<ComparisonResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function load() {
    setLoading(true); setError('')
    try { setData(await getComparison(date, cutoff)) }
    catch (e) { setError(e instanceof Error ? e.message : 'Unable to load data') }
    finally { setLoading(false) }
  }
  useEffect(() => { void load() }, []) // initial load only; filters load on button click

  const chartData = useMemo(() => (data?.records || [])
    .filter(r => r.forecast_mw != null || r.actual_mw != null)
    .map(r => ({ time: timeLabel(r.startTime), forecast: r.forecast_mw, actual: r.actual_mw })), [data])

  function exportCsv() {
    if (!data) return
    const header = ['startTime', 'publishTime', 'forecast_mw', 'actual_mw', 'error_mw', 'status']
    const lines = [header.join(','), ...data.records.map(row => header.map(key => {
      const value = row[key as keyof typeof row]
      return value == null ? '' : `"${String(value).replaceAll('"', '""')}"`
    }).join(','))]
    const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob); const link = document.createElement('a')
    link.href = url; link.download = `wind-analysis-${date}.csv`; link.click(); URL.revokeObjectURL(url)
  }

  const m = data?.metrics
  return <div className="app-shell">
    <aside className="sidebar">
      <div className="brand"><div className="brand-icon"><Wind size={22}/></div><div><strong>WindLens</strong><span>ENERGY INTELLIGENCE</span></div></div>
      <div className="nav-label">WORKSPACE</div>
      <div className="nav-item active"><Activity size={17}/> Forecast overview</div>
      <div className="nav-item"><Zap size={17}/> Accuracy analysis <span className="soon">LIVE VIEW</span></div>
      <div className="sidebar-bottom"><div className="status-dot"/><div><strong>Prototype mode</strong><span>Historical analysis · Jan 2026</span></div></div>
    </aside>
    <main className="main">
      <header className="topbar"><div><div className="eyebrow">UK POWER MARKET / WIND</div><h1>Forecast intelligence</h1><p>Understand forecast availability and quantify wind generation error.</p></div><div className="source-chip"><span className="green-dot"/> Elexon BMRS source</div></header>
      <section className="controls panel">
        <div className="control-group"><label><CalendarDays size={14}/> DELIVERY DATE</label><input type="date" min="2026-01-01" max="2026-01-31" value={date} onChange={e=>setDate(e.target.value)}/></div>
        <div className="control-group"><label><Clock3 size={14}/> DECISION CUTOFF (UK)</label><select value={cutoff} onChange={e=>setCutoff(Number(e.target.value))}>{[12,14,16,18,20,22].map(h=><option key={h} value={h}>{String(h).padStart(2,'0')}:00 GMT previous day</option>)}</select></div>
        <button className="primary-btn" onClick={load} disabled={loading}><RefreshCw size={15} className={loading?'spin':''}/>{loading?'Loading…':'Run analysis'}</button>
        <button className="icon-btn" onClick={exportCsv} disabled={!data} title="Export CSV"><Download size={17}/></button>
      </section>
      {error && <div className="error-banner"><AlertTriangle size={18}/><div><strong>Could not load live source data</strong><p>{error}</p><span>Check backend connectivity or the Elexon API response. No sample results are substituted.</span></div></div>}
      {loading && <div className="loading panel">Retrieving Elexon records and calculating forecast accuracy…</div>}
      <section className="metric-grid">
        <Metric icon={<Activity/>} label="MEAN ABSOLUTE ERROR" value={m?.mae_mw == null?'—':fmt(m.mae_mw)} hint="Lower is generally better"/>
        <Metric icon={<Zap/>} label="ROOT MEAN SQUARED ERROR" value={m?.rmse_mw == null?'—':fmt(m.rmse_mw)} hint="Highlights larger errors"/>
        <Metric icon={<Wind/>} label="FORECAST BIAS" value={m?.bias_mw == null?'—':fmt(m.bias_mw)} hint="Positive = overforecast"/>
        <Metric icon={<CheckCircle2/>} label="MATCHED INTERVALS" value={m?String(m.matched_intervals):'—'} hint={m?`${m.coverage_pct}% of 1,488 monthly intervals`:'January coverage measure'}/>
      </section>
      <section className="content-grid">
        <div className="panel chart-panel">
          <div className="panel-heading"><div><h2>Wind generation · forecast vs actual</h2><p>30-minute delivery intervals · MW</p></div><span className="legend"><i className="legend-forecast"/> Forecast <i className="legend-actual"/> Actual</span></div>
          {chartData.length ? <div className="chart"><ResponsiveContainer width="100%" height="100%"><LineChart data={chartData} margin={{top:15,right:15,left:0,bottom:4}}><CartesianGrid strokeDasharray="3 3" stroke="#233047"/><XAxis dataKey="time" tick={{fill:'#8b9bb4',fontSize:11}} interval={5} axisLine={false} tickLine={false}/><YAxis tick={{fill:'#8b9bb4',fontSize:11}} axisLine={false} tickLine={false} width={60}/><Tooltip contentStyle={{background:'#111b2d',border:'1px solid #29364c',borderRadius:10,color:'#eef4ff'}} formatter={(v)=>fmt(Number(v))}/><Line type="monotone" dataKey="forecast" name="Forecast" stroke="#5b9cff" strokeWidth={2.5} dot={false} connectNulls={false}/><Line type="monotone" dataKey="actual" name="Actual" stroke="#49d6ae" strokeWidth={2.5} dot={false} connectNulls={false}/></LineChart></ResponsiveContainer></div> : <EmptyState text={error?'Chart unavailable until source data is reachable.':'Run analysis to load the selected delivery day.'}/>}
          <div className="chart-foot"><span>Selected day: {date}</span><span>Source: FUELHH + WINDFOR</span></div>
        </div>
        <div className="panel insight-panel"><div className="panel-heading"><div><h2>Decision context</h2><p>What was available at the cutoff?</p></div></div>
          <div className="insight-item"><div className="insight-icon blue"><Clock3 size={18}/></div><div><strong>Decision cutoff</strong><p>{data ? new Date(data.decision_cutoff).toLocaleString('en-GB',{timeZone:'UTC',dateStyle:'medium',timeStyle:'short'})+' GMT' : `Previous day at ${String(cutoff).padStart(2,'0')}:00 GMT`}</p></div></div>
          <div className="insight-item"><div className="insight-icon green"><CheckCircle2 size={18}/></div><div><strong>Forecast selection</strong><p>Latest publication on or before the cutoff, matched by delivery start time.</p></div></div>
          <div className="notice"><AlertTriangle size={17}/><p><strong>Prototype assumption</strong><br/>The cutoff hour is configurable for demonstration. Confirm the actual trading deadline with the client before operational use.</p></div>
          <div className="notice neutral"><Activity size={17}/><p><strong>Scope boundary</strong><br/>Demand is not included, so this tool evaluates wind forecasts; it does not calculate an actual electricity purchase requirement.</p></div>
        </div>
      </section>
      <section className="panel table-panel">
        <div className="panel-heading"><div><h2>Delivery interval details</h2><p>Selected forecast publication, actual generation and error</p></div><span className="record-count">{data?.records.length ?? 0} records</span></div>
        <div className="table-wrap"><table><thead><tr><th>DELIVERY TIME (UTC)</th><th>FORECAST PUBLISHED</th><th>FORECAST</th><th>ACTUAL</th><th>ERROR</th><th>STATUS</th></tr></thead><tbody>
          {(data?.records || []).slice(0,48).map((r,i)=><tr key={`${r.startTime}-${i}`}><td>{new Date(r.startTime).toLocaleString('en-GB',{timeZone:'UTC',month:'short',day:'2-digit',hour:'2-digit',minute:'2-digit'})}</td><td>{r.publishTime?new Date(r.publishTime).toLocaleString('en-GB',{timeZone:'UTC',hour:'2-digit',minute:'2-digit'}):'—'}</td><td>{fmt(r.forecast_mw)}</td><td>{fmt(r.actual_mw)}</td><td className={r.error_mw==null?'muted':r.error_mw>0?'positive':'negative'}>{r.error_mw==null?'—':`${r.error_mw>0?'+':''}${r.error_mw.toFixed(1)} MW`}</td><td><span className={`status ${r.status}`}>{r.status.replace('_',' ')}</span></td></tr>)}
        </tbody></table>{!data?.records.length && <EmptyState text="No interval records to display yet." />}</div>
        {data && data.records.length>48 && <div className="table-note">Showing first 48 intervals. Export CSV to inspect all returned records.</div>}
      </section>
      <footer>WindLens pilot · Historical January 2026 analysis · Forecast error = forecast − actual · All timestamps shown in UTC/GMT</footer>
    </main>
  </div>
}

function Metric({icon,label,value,hint}:{icon:ReactNode,label:string,value:string,hint:string}) {
  return <div className="panel metric"><div className="metric-top"><span className="metric-icon">{icon}</span><span className="metric-label">{label}</span></div><div className="metric-value">{value}</div><div className="metric-hint">{hint}</div></div>
}
function EmptyState({text}:{text:string}) { return <div className="empty-state"><Wind size={27}/><p>{text}</p></div> }
