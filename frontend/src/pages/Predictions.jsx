import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Activity, BrainCircuit, CalendarPlus, ChevronDown, Info, RefreshCw } from 'lucide-react'
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { predictionApi, scheduleApi } from '../api/services'
import { errorMessage } from '../api/client'
import { useApi } from '../hooks'
import { useToast } from '../context/ToastContext'
import { notifyChanged } from '../components/Layout'
import { EmptyState, ErrorState, HealthBar, PageHeader, PageLoader, RiskBadge, Spinner } from '../components/ui'
import { daysUntil, fmtDate, fmtDateTime, healthColor } from '../utils/format'

const FEATURE_LABEL = {
  lifespan_ratio: 'Age vs lifespan', age_years: 'Age (years)', service_overdue_ratio: 'Service overdue ratio',
  days_since_service: 'Days since service', max_open_severity: 'Open issue severity', open_issues: 'Open issues',
  condition_level: 'Condition', breakdowns_total: 'Breakdowns', usage_level: 'Usage level', services_last_2y: 'Services (2 yrs)',
}

export default function Predictions() {
  const toast = useToast()
  const { data, loading, error, reload } = useApi(() => predictionApi.latest(), [])
  const { data: info } = useApi(() => predictionApi.modelInfo(), [])
  const [running, setRunning] = useState(false)
  const [expanded, setExpanded] = useState(null)
  const [booking, setBooking] = useState(null)

  const runAll = async () => {
    setRunning(true)
    try {
      const r = await predictionApi.runAll()
      toast.success(`Re-assessed ${r.length} appliance(s)`)
      reload(true); notifyChanged()
    } catch (e) { toast.error(errorMessage(e)) } finally { setRunning(false) }
  }

  const book = async (p) => {
    setBooking(p.appliance_id)
    try {
      await scheduleApi.accept(p.appliance_id)
      toast.success(`Service for ${p.appliance_name} added to the scheduler (Pending)`)
      notifyChanged()
    } catch (e) { toast.error(errorMessage(e)) } finally { setBooking(null) }
  }

  if (loading) return <PageLoader label="Loading predictions…" />
  if (error) return <ErrorState message={error} onRetry={reload} />

  const importances = info?.feature_importances
    ? Object.entries(info.feature_importances).map(([k, v]) => ({ name: FEATURE_LABEL[k] || k, value: Math.round(v * 1000) / 10 }))
    : []

  return (
    <>
      <PageHeader title="Predictive Maintenance" subtitle="Health scores, risk levels and recommended service dates for every appliance."
        actions={<button className="btn-primary" onClick={runAll} disabled={running}>{running ? <Spinner className="h-4 w-4 text-white" /> : <RefreshCw className="h-4 w-4" />}Run prediction for all</button>} />

      <div className="mb-4 flex gap-3 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
        <Info className="mt-0.5 h-5 w-5 shrink-0" />
        <div>
          <p className="font-semibold">How to read these scores</p>
          <p className="mt-0.5">{info?.disclaimer || 'Scores are maintenance-priority estimates.'} The model considers age, usage, service history,
            time since last service, expected lifespan, reported problems and previous breakdowns.</p>
        </div>
      </div>

      {data.length === 0 ? (
        <div className="card"><EmptyState icon={Activity} title="No predictions yet" message="Add appliances — each one is assessed automatically."
          action={<Link className="btn-primary" to="/appliances?new=1">Add appliance</Link>} /></div>
      ) : (
        <div className="space-y-3">
          {data.map((p) => {
            const open = expanded === p.id
            const dd = daysUntil(p.recommended_service_date)
            return (
              <div key={p.id} className="card overflow-hidden">
                <button className="grid w-full grid-cols-12 items-center gap-3 p-4 text-left hover:bg-charcoal-50/50" onClick={() => setExpanded(open ? null : p.id)} aria-expanded={open}>
                  <div className="col-span-12 flex items-center gap-3 sm:col-span-4">
                    <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full text-sm font-bold text-white" style={{ background: healthColor(p.health_score) }}>
                      {Math.round(p.health_score)}
                    </div>
                    <div className="min-w-0"><p className="truncate font-semibold">{p.appliance_name}</p><p className="text-xs text-charcoal-500">{p.appliance_category}</p></div>
                  </div>
                  <div className="col-span-4 sm:col-span-2"><RiskBadge risk={p.risk_level} /></div>
                  <div className="col-span-8 text-sm sm:col-span-3"><p className="text-xs text-charcoal-400">Priority</p><p className="font-medium">{p.priority}</p></div>
                  <div className="col-span-10 text-sm sm:col-span-2"><p className="text-xs text-charcoal-400">Service by</p>
                    <p className="font-medium">{fmtDate(p.recommended_service_date)} <span className="text-xs text-charcoal-400">({dd}d)</span></p></div>
                  <ChevronDown className={`col-span-2 h-5 w-5 justify-self-end text-charcoal-400 transition sm:col-span-1 ${open ? 'rotate-180' : ''}`} />
                </button>
                {open && (
                  <div className="grid gap-5 border-t border-charcoal-100 bg-charcoal-50/40 p-5 md:grid-cols-2">
                    <div>
                      <h3 className="mb-2 text-sm font-semibold">Why this recommendation</h3>
                      <ul className="space-y-2 text-sm">
                        {p.explanation.map((l, i) => <li key={i} className="flex gap-2"><span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-brand-500" />{l}</li>)}
                      </ul>
                      <p className="mt-3 text-xs text-charcoal-400">Assessed {fmtDateTime(p.created_at)} · {p.model_used === 'random_forest' ? 'Random Forest' : 'Rule-based'}</p>
                      <div className="mt-4 flex flex-wrap gap-2">
                        <button className="btn-primary btn-sm" onClick={() => book(p)} disabled={booking === p.appliance_id}>
                          {booking === p.appliance_id ? <Spinner className="h-3.5 w-3.5 text-white" /> : <CalendarPlus className="h-3.5 w-3.5" />}Book recommended service</button>
                        <Link to={`/appliances/${p.appliance_id}`} className="btn-secondary btn-sm">View appliance</Link>
                      </div>
                    </div>
                    <div className="space-y-4">
                      <div>
                        <h3 className="mb-2 text-sm font-semibold">Risk factors (points deducted from 100)</h3>
                        {p.factors.length === 0 ? <p className="text-sm text-charcoal-500">No notable risk factors.</p> : (
                          <div className="space-y-2">
                            {p.factors.map((f) => (
                              <div key={f.factor}>
                                <div className="flex justify-between text-xs"><span className="font-medium">{f.factor}</span><span className="tabular-nums">−{f.impact}</span></div>
                                <div className="mt-1 h-1.5 rounded-full bg-charcoal-100"><div className="h-full rounded-full bg-orange-400" style={{ width: `${Math.min(100, f.impact * 3)}%` }} /></div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                      {p.class_probabilities && (
                        <div>
                          <h3 className="mb-2 text-sm font-semibold">Model class probabilities</h3>
                          <div className="grid grid-cols-4 gap-2 text-center text-xs">
                            {['Low', 'Medium', 'High', 'Critical'].map((c) => (
                              <div key={c} className="rounded-lg bg-white p-2 ring-1 ring-charcoal-100"><p className="text-charcoal-500">{c}</p>
                                <p className="font-bold tabular-nums">{Math.round((p.class_probabilities[c] || 0) * 100)}%</p></div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}

      {info && (
        <div className="card mt-6 grid gap-6 p-5 md:grid-cols-2">
          <div>
            <div className="mb-2 flex items-center gap-2"><BrainCircuit className="h-5 w-5 text-brand-600" /><h2 className="font-semibold">About the model</h2></div>
            <dl className="space-y-2 text-sm">
              <div className="flex justify-between gap-4"><dt className="text-charcoal-500">Engine</dt><dd className="font-medium">{info.ml_available ? info.model_type : 'Rule-based fallback'}</dd></div>
              <div className="flex justify-between gap-4"><dt className="text-charcoal-500">Training data</dt><dd className="text-right font-medium">{info.trained_on}</dd></div>
              {info.n_samples && <div className="flex justify-between"><dt className="text-charcoal-500">Synthetic samples</dt><dd className="font-medium">{info.n_samples.toLocaleString()}</dd></div>}
              {info.holdout_accuracy && <div className="flex justify-between"><dt className="text-charcoal-500">Hold-out accuracy (on synthetic data)</dt><dd className="font-medium">{Math.round(info.holdout_accuracy * 100)}%</dd></div>}
              {info.holdout_macro_f1 && <div className="flex justify-between"><dt className="text-charcoal-500">Macro F1 (synthetic)</dt><dd className="font-medium">{info.holdout_macro_f1}</dd></div>}
            </dl>
            <p className="mt-3 text-xs text-charcoal-400">Accuracy is measured against the same simulated labelling heuristic, so it shows how well the model learned that heuristic — not real-world reliability.</p>
          </div>
          {importances.length > 0 && (
            <div>
              <h3 className="mb-2 text-sm font-semibold">Feature importance (%)</h3>
              <div className="h-64">
                <ResponsiveContainer>
                  <BarChart data={importances} layout="vertical" margin={{ left: 40 }}>
                    <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e2e5e5" />
                    <XAxis type="number" tick={{ fontSize: 10 }} />
                    <YAxis type="category" dataKey="name" tick={{ fontSize: 10 }} width={110} />
                    <Tooltip />
                    <Bar dataKey="value" radius={[0, 4, 4, 0]}>{importances.map((_, i) => <Cell key={i} fill={i < 3 ? '#207e51' : '#81d2a7'} />)}</Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}
        </div>
      )}
    </>
  )
}
