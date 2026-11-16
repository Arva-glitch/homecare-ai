import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft, Activity, CalendarPlus, ImageOff, Pencil, Plus, Refrigerator, Trash2, Upload, Wrench } from 'lucide-react'
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { applianceApi, predictionApi } from '../api/services'
import { assetUrl, errorMessage } from '../api/client'
import { useApi } from '../hooks'
import { useOptions } from '../context/OptionsContext'
import { useToast } from '../context/ToastContext'
import ApplianceForm from '../components/ApplianceForm'
import ScheduleForm from '../components/ScheduleForm'
import { ConfirmDialog, EmptyState, ErrorState, Field, HealthBar, Modal, PageLoader, RiskBadge, Select, Spinner } from '../components/ui'
import { fmtDate, inr, todayISO } from '../utils/format'

function Info({ label, value }) {
  return <div><p className="text-xs text-charcoal-400">{label}</p><p className="text-sm font-medium">{value ?? '—'}</p></div>
}

export default function ApplianceDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const toast = useToast()
  const opts = useOptions()
  const { data: a, loading, error, reload } = useApi(() => applianceApi.get(id), [id])
  const { data: hist, reload: reloadHist } = useApi(() => predictionApi.history({ appliance_id: id, limit: 30 }), [id])
  const [editOpen, setEditOpen] = useState(false)
  const [schedOpen, setSchedOpen] = useState(false)
  const [recordOpen, setRecordOpen] = useState(false)
  const [confirm, setConfirm] = useState(null)
  const [busy, setBusy] = useState(false)
  const [record, setRecord] = useState({ service_date: todayISO(), maintenance_type: 'General Servicing', description: '', technician: '', cost: '', was_breakdown: false })

  if (loading) return <PageLoader />
  if (error) return <ErrorState message={error} onRetry={reload} />

  const refresh = () => { reload(true); reloadHist(true) }
  const latest = hist?.[0]

  const run = async (fn, okMsg) => {
    setBusy(true)
    try { await fn(); if (okMsg) toast.success(okMsg); refresh() } catch (e) { toast.error(errorMessage(e)) } finally { setBusy(false) }
  }

  const uploadImage = (e) => {
    const f = e.target.files?.[0]
    if (f) run(() => applianceApi.uploadImage(a.id, f), 'Image uploaded')
    e.target.value = ''
  }

  const saveRecord = async (e) => {
    e.preventDefault()
    await run(() => applianceApi.addRecord(a.id, { ...record, cost: Number(record.cost || 0), technician: record.technician || null }),
      'Maintenance recorded — health re-assessed')
    setRecordOpen(false)
  }

  const doConfirm = async () => {
    if (confirm.type === 'appliance') {
      setBusy(true)
      try { await applianceApi.remove(a.id); toast.success('Appliance deleted'); navigate('/appliances') } catch (e) { toast.error(errorMessage(e)) } finally { setBusy(false) }
    } else if (confirm.type === 'record') {
      await run(() => applianceApi.deleteRecord(a.id, confirm.id), 'Record deleted')
    }
    setConfirm(null)
  }

  const trend = [...(hist || [])].reverse().map((p) => ({ date: fmtDate(p.created_at), health: p.health_score }))

  return (
    <>
      <Link to="/appliances" className="mb-4 inline-flex items-center gap-1 text-sm text-charcoal-500 hover:text-charcoal-800"><ArrowLeft className="h-4 w-4" />Back to appliances</Link>
      <div className="card mb-4 flex flex-col gap-5 p-5 md:flex-row">
        <div className="relative h-40 w-full shrink-0 overflow-hidden rounded-2xl bg-brand-50 md:w-48">
          {a.image_url ? <img src={assetUrl(a.image_url)} alt={a.name} className="h-full w-full object-cover" />
            : <div className="flex h-full items-center justify-center"><Refrigerator className="h-12 w-12 text-brand-500" /></div>}
          <div className="absolute bottom-2 right-2 flex gap-1">
            <label className="btn-secondary btn-sm cursor-pointer"><Upload className="h-3.5 w-3.5" />Photo
              <input type="file" accept="image/png,image/jpeg,image/webp,image/gif" className="hidden" onChange={uploadImage} /></label>
            {a.image_url && <button className="btn-secondary btn-sm" onClick={() => run(() => applianceApi.removeImage(a.id), 'Image removed')} aria-label="Remove image"><ImageOff className="h-3.5 w-3.5" /></button>}
          </div>
        </div>
        <div className="flex-1">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h1 className="text-2xl font-bold">{a.name}</h1>
              <p className="text-sm text-charcoal-500">{a.category}{a.brand && ` · ${a.brand}`}{a.model_number && ` · ${a.model_number}`}{a.location && ` · ${a.location}`}</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <button className="btn-secondary" disabled={busy} onClick={() => run(() => predictionApi.runOne(a.id), 'Prediction updated')}>{busy ? <Spinner className="h-4 w-4" /> : <Activity className="h-4 w-4" />}Re-assess</button>
              <button className="btn-secondary" onClick={() => setSchedOpen(true)}><CalendarPlus className="h-4 w-4" />Schedule</button>
              <button className="btn-secondary" onClick={() => setEditOpen(true)}><Pencil className="h-4 w-4" />Edit</button>
              <button className="btn-ghost text-red-600 hover:bg-red-50" onClick={() => setConfirm({ type: 'appliance' })}><Trash2 className="h-4 w-4" />Delete</button>
            </div>
          </div>
          <div className="mt-4 grid grid-cols-1 items-center gap-4 sm:grid-cols-3">
            <div className="sm:col-span-2"><p className="mb-1 text-xs text-charcoal-400">Health score</p><HealthBar score={a.health_score} /></div>
            <div><p className="mb-1 text-xs text-charcoal-400">Risk level</p><RiskBadge risk={a.risk_level} /></div>
          </div>
          <div className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-4">
            <Info label="Age" value={a.age_years != null ? `${a.age_years} yrs (of ~${a.expected_lifespan_years})` : null} />
            <Info label="Usage" value={a.usage_frequency} />
            <Info label="Condition" value={a.condition} />
            <Info label="Next service (AI)" value={fmtDate(a.next_service_date)} />
            <Info label="Purchased" value={fmtDate(a.purchase_date)} />
            <Info label="Installed" value={fmtDate(a.installation_date)} />
            <Info label="Warranty" value={a.warranty_expiry ? `${a.warranty_active ? 'Active' : 'Expired'} · ${fmtDate(a.warranty_expiry)}` : null} />
            <Info label="Last service" value={fmtDate(a.last_service_date)} />
            <Info label="Open issues" value={a.open_issues} />
            <Info label="Total spent" value={inr(a.total_expenses)} />
          </div>
          {a.notes && <p className="mt-4 rounded-xl bg-charcoal-50 p-3 text-sm text-charcoal-600">{a.notes}</p>}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="card p-5">
          <h2 className="mb-1 font-semibold">Latest assessment</h2>
          {latest ? (
            <>
              <p className="mb-3 text-xs text-charcoal-500">{latest.priority} · {latest.model_used === 'random_forest' ? 'Random Forest (synthetic-trained)' : 'Rule-based engine'} · {fmtDate(latest.created_at)}</p>
              <ul className="space-y-2 text-sm">
                {latest.explanation.map((l, i) => <li key={i} className="flex gap-2"><span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-brand-500" />{l}</li>)}
              </ul>
            </>
          ) : <p className="text-sm text-charcoal-500">No assessment yet.</p>}
        </div>
        <div className="card p-5">
          <h2 className="mb-3 font-semibold">Health score trend</h2>
          <div className="h-56">
            <ResponsiveContainer>
              <LineChart data={trend} margin={{ left: -20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e5e5" vertical={false} />
                <XAxis dataKey="date" tick={{ fontSize: 10 }} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 10 }} />
                <Tooltip />
                <Line type="monotone" dataKey="health" stroke="#2e9d66" strokeWidth={2.5} dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="card mt-4">
        <div className="flex items-center justify-between border-b border-charcoal-100 p-5">
          <h2 className="font-semibold">Maintenance history</h2>
          <button className="btn-primary btn-sm" onClick={() => setRecordOpen(true)}><Plus className="h-3.5 w-3.5" />Log maintenance</button>
        </div>
        {a.maintenance_records.length === 0 ? <EmptyState icon={Wrench} title="No maintenance recorded" message="Log past servicing so predictions are more accurate." />
          : <div className="overflow-x-auto">
            <table className="w-full">
              <thead><tr><th className="table-th">Date</th><th className="table-th">Type</th><th className="table-th">Details</th><th className="table-th">Technician</th><th className="table-th text-right">Cost</th><th className="table-th" /></tr></thead>
              <tbody>
                {a.maintenance_records.map((r) => (
                  <tr key={r.id}>
                    <td className="table-td whitespace-nowrap">{fmtDate(r.service_date)}</td>
                    <td className="table-td whitespace-nowrap">{r.maintenance_type}{r.was_breakdown && <span className="ml-2 rounded bg-red-50 px-1.5 py-0.5 text-[10px] font-semibold text-red-700">Breakdown</span>}</td>
                    <td className="table-td text-charcoal-600">{r.description || '—'}</td>
                    <td className="table-td">{r.technician || '—'}</td>
                    <td className="table-td text-right tabular-nums">{inr(r.cost)}</td>
                    <td className="table-td text-right"><button className="btn-ghost btn-sm text-red-600" onClick={() => setConfirm({ type: 'record', id: r.id })} aria-label="Delete record"><Trash2 className="h-3.5 w-3.5" /></button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>}
      </div>

      <ApplianceForm open={editOpen} appliance={a} onClose={() => setEditOpen(false)} onSaved={refresh} />
      <ScheduleForm open={schedOpen} onClose={() => setSchedOpen(false)} defaults={{ appliance_id: a.id }} onSaved={() => toast.info('View it in the Maintenance Scheduler')} />
      <Modal open={recordOpen} onClose={() => setRecordOpen(false)} title="Log completed maintenance"
        footer={<><button className="btn-secondary" onClick={() => setRecordOpen(false)}>Cancel</button><button form="rec-form" className="btn-primary" disabled={busy}>{busy && <Spinner className="h-4 w-4 text-white" />}Save</button></>}>
        <form id="rec-form" onSubmit={saveRecord} className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Field label="Service date"><input className="input" type="date" required max={todayISO()} value={record.service_date} onChange={(e) => setRecord({ ...record, service_date: e.target.value })} /></Field>
          <Field label="Type"><Select value={record.maintenance_type} onChange={(v) => setRecord({ ...record, maintenance_type: v })} options={opts.maintenance_types} /></Field>
          <Field label="Technician"><input className="input" value={record.technician} onChange={(e) => setRecord({ ...record, technician: e.target.value })} /></Field>
          <Field label="Cost (₹) — added to expenses"><input className="input" type="number" min="0" step="1" value={record.cost} onChange={(e) => setRecord({ ...record, cost: e.target.value })} /></Field>
          <Field label="Description" className="sm:col-span-2"><textarea className="input" value={record.description} onChange={(e) => setRecord({ ...record, description: e.target.value })} /></Field>
          <label className="flex items-center gap-2 text-sm sm:col-span-2"><input type="checkbox" checked={record.was_breakdown} onChange={(e) => setRecord({ ...record, was_breakdown: e.target.checked })} />This was a breakdown repair</label>
        </form>
      </Modal>
      <ConfirmDialog open={!!confirm} busy={busy} confirmLabel="Delete"
        title={confirm?.type === 'appliance' ? 'Delete appliance?' : 'Delete maintenance record?'}
        message={confirm?.type === 'appliance' ? 'This permanently removes the appliance with its history, schedules, issues and predictions.' : 'The record will be removed and the health score re-assessed. Linked expenses are not deleted.'}
        onConfirm={doConfirm} onCancel={() => setConfirm(null)} />
    </>
  )
}
