import { useState } from 'react'
import { CalendarClock, CalendarPlus, Check, Pencil, Play, Sparkles, Trash2, XCircle } from 'lucide-react'
import { scheduleApi } from '../api/services'
import { errorMessage } from '../api/client'
import { useApi } from '../hooks'
import { useToast } from '../context/ToastContext'
import { notifyChanged } from '../components/Layout'
import ScheduleForm from '../components/ScheduleForm'
import MiniCalendar from '../components/MiniCalendar'
import { ConfirmDialog, EmptyState, ErrorState, Field, Modal, PageHeader, RiskBadge, Spinner, StatusBadge } from '../components/ui'
import { fmtDate, fmtDateTime, inr } from '../utils/format'

const TABS = [
  { key: 'upcoming', label: 'Upcoming' }, { key: 'overdue', label: 'Overdue' }, { key: 'completed', label: 'Completed' },
  { key: 'cancelled', label: 'Cancelled' }, { key: 'all', label: 'All' },
]

export default function Scheduler() {
  const toast = useToast()
  const [tab, setTab] = useState('upcoming')
  const { data, loading, error, reload } = useApi(() => scheduleApi.list({ view: tab }), [tab])
  const { data: calendarData, reload: reloadCal } = useApi(() => scheduleApi.list({ view: 'all' }), [])
  const { data: sugg, reload: reloadSugg } = useApi(() => scheduleApi.suggestions(), [])
  const [formOpen, setFormOpen] = useState(false)
  const [editing, setEditing] = useState(null)
  const [completing, setCompleting] = useState(null)
  const [completion, setCompletion] = useState({ actual_cost: '', notes: '', was_breakdown: false })
  const [confirm, setConfirm] = useState(null)
  const [busy, setBusy] = useState(null)

  const refreshAll = () => { reload(true); reloadCal(true); reloadSugg(true); notifyChanged() }

  const act = async (key, fn, msg) => {
    setBusy(key)
    try { await fn(); toast.success(msg); refreshAll() } catch (e) { toast.error(errorMessage(e)) } finally { setBusy(null) }
  }

  const complete = async (e) => {
    e.preventDefault()
    await act(`c${completing.id}`, () => scheduleApi.setStatus(completing.id, {
      status: 'Completed', actual_cost: completion.actual_cost === '' ? null : Number(completion.actual_cost),
      notes: completion.notes || null, was_breakdown: completion.was_breakdown,
    }), 'Task completed — history, expenses and health score updated')
    setCompleting(null)
  }

  const doConfirm = async () => {
    const { type, s } = confirm
    if (type === 'cancel') await act(`x${s.id}`, () => scheduleApi.cancel(s.id), 'Task cancelled')
    else await act(`d${s.id}`, () => scheduleApi.remove(s.id), 'Task deleted')
    setConfirm(null)
  }

  const calEvents = (calendarData || []).filter((s) => ['Pending', 'Scheduled', 'In Progress'].includes(s.status))

  return (
    <>
      <PageHeader title="Maintenance Scheduler" subtitle="Plan, track and complete maintenance tasks."
        actions={<button className="btn-primary" onClick={() => { setEditing(null); setFormOpen(true) }}><CalendarPlus className="h-4 w-4" />Schedule maintenance</button>} />

      {sugg?.length > 0 && (
        <div className="card mb-4 p-5">
          <div className="mb-3 flex items-center gap-2"><Sparkles className="h-5 w-5 text-brand-600" /><h2 className="font-semibold">AI-suggested schedules</h2>
            <span className="text-xs text-charcoal-500">from the latest predictive analysis</span></div>
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {sugg.map((s) => (
              <div key={s.appliance_id} className="flex flex-col rounded-xl border border-charcoal-100 p-4">
                <div className="flex items-start justify-between gap-2"><p className="font-semibold">{s.appliance_name}</p><RiskBadge risk={s.risk_level} /></div>
                <p className="mt-1 text-xs text-charcoal-500">{s.maintenance_type} · by {fmtDate(s.suggested_date)} · {s.priority} priority</p>
                <p className="mt-2 flex-1 text-sm text-charcoal-600">{s.reason}</p>
                <button className="btn-primary btn-sm mt-3 self-start" disabled={busy === `s${s.appliance_id}`}
                  onClick={() => act(`s${s.appliance_id}`, () => scheduleApi.accept(s.appliance_id), `Added for ${s.appliance_name}`)}>
                  {busy === `s${s.appliance_id}` ? <Spinner className="h-3.5 w-3.5 text-white" /> : <Check className="h-3.5 w-3.5" />}Accept suggestion</button>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="card lg:col-span-2">
          <div className="flex gap-1 overflow-x-auto border-b border-charcoal-100 p-2" role="tablist">
            {TABS.map((t) => (
              <button key={t.key} role="tab" aria-selected={tab === t.key} onClick={() => setTab(t.key)}
                className={`whitespace-nowrap rounded-lg px-3 py-1.5 text-sm font-medium ${tab === t.key ? 'bg-brand-600 text-white' : 'text-charcoal-600 hover:bg-charcoal-100'}`}>{t.label}</button>
            ))}
          </div>
          {error ? <div className="p-4"><ErrorState message={error} onRetry={reload} /></div>
            : loading ? <div className="flex justify-center p-10"><Spinner className="h-6 w-6" /></div>
              : data.length === 0 ? <EmptyState icon={CalendarClock} title={`No ${tab === 'all' ? '' : tab} tasks`} message="Scheduled maintenance will appear here." />
                : <ul className="divide-y divide-charcoal-100">
                  {data.map((s) => {
                    const active = ['Pending', 'Scheduled', 'In Progress'].includes(s.status)
                    return (
                      <li key={s.id} className="flex flex-col gap-3 p-4 sm:flex-row sm:items-center">
                        <div className="min-w-0 flex-1">
                          <div className="flex flex-wrap items-center gap-2">
                            <p className="font-semibold">{s.title}</p><StatusBadge status={s.status} />
                            {s.is_ai_suggested && <span className="inline-flex items-center gap-1 rounded-full bg-brand-50 px-2 py-0.5 text-[11px] font-semibold text-brand-700"><Sparkles className="h-3 w-3" />AI</span>}
                            {s.priority !== 'Normal' && <span className="text-[11px] font-semibold text-charcoal-500">{s.priority} priority</span>}
                          </div>
                          <p className="mt-0.5 text-sm text-charcoal-500">{s.appliance_name} · {s.maintenance_type} · {fmtDateTime(s.scheduled_at)}</p>
                          {(s.technician || s.estimated_cost) && <p className="text-xs text-charcoal-400">{s.technician}{s.technician && s.estimated_cost ? ' · ' : ''}{s.estimated_cost ? `est. ${inr(s.estimated_cost)}` : ''}</p>}
                          {s.description && <p className="mt-1 line-clamp-2 text-xs text-charcoal-500">{s.description}</p>}
                          {s.completed_at && <p className="text-xs text-brand-700">Completed {fmtDateTime(s.completed_at)}</p>}
                        </div>
                        <div className="flex flex-wrap gap-1">
                          {s.status === 'Pending' && <button className="btn-secondary btn-sm" disabled={!!busy} onClick={() => act(`st${s.id}`, () => scheduleApi.setStatus(s.id, { status: 'Scheduled' }), 'Marked as scheduled')}>Confirm</button>}
                          {['Pending', 'Scheduled'].includes(s.status) && <button className="btn-secondary btn-sm" disabled={!!busy} onClick={() => act(`p${s.id}`, () => scheduleApi.setStatus(s.id, { status: 'In Progress' }), 'Marked in progress')}><Play className="h-3.5 w-3.5" />Start</button>}
                          {active && <button className="btn-primary btn-sm" onClick={() => { setCompleting(s); setCompletion({ actual_cost: s.estimated_cost ?? '', notes: '', was_breakdown: false }) }}><Check className="h-3.5 w-3.5" />Complete</button>}
                          {active && <button className="btn-ghost btn-sm" onClick={() => { setEditing(s); setFormOpen(true) }} aria-label="Edit"><Pencil className="h-3.5 w-3.5" /></button>}
                          {active && <button className="btn-ghost btn-sm text-amber-700" onClick={() => setConfirm({ type: 'cancel', s })}><XCircle className="h-3.5 w-3.5" />Cancel</button>}
                          {s.status === 'Cancelled' && <button className="btn-secondary btn-sm" disabled={!!busy} onClick={() => act(`r${s.id}`, () => scheduleApi.setStatus(s.id, { status: 'Scheduled' }), 'Task restored')}>Restore</button>}
                          {!active && <button className="btn-ghost btn-sm text-red-600" onClick={() => setConfirm({ type: 'delete', s })} aria-label="Delete"><Trash2 className="h-3.5 w-3.5" /></button>}
                        </div>
                      </li>
                    )
                  })}
                </ul>}
        </div>
        <div className="card h-fit p-5">
          <h2 className="mb-3 font-semibold">Calendar</h2>
          <MiniCalendar events={calEvents} onSelectDay={(d, ev) => toast.info(`${d.toLocaleDateString('en-IN')}: ${ev.map((e) => e.title).join(', ')}`)} />
          <p className="mt-3 text-xs text-charcoal-400">Highlighted days have active tasks. Click a day to see them.</p>
        </div>
      </div>

      <ScheduleForm open={formOpen} schedule={editing} onClose={() => { setFormOpen(false); setEditing(null) }} onSaved={refreshAll} />
      <Modal open={!!completing} onClose={() => setCompleting(null)} title="Complete maintenance task"
        footer={<><button className="btn-secondary" onClick={() => setCompleting(null)}>Cancel</button>
          <button form="complete-form" className="btn-primary" disabled={!!busy}>{busy && <Spinner className="h-4 w-4 text-white" />}Mark completed</button></>}>
        <form id="complete-form" onSubmit={complete} className="space-y-4">
          <p className="text-sm text-charcoal-600">This adds a record to <b>{completing?.appliance_name}</b>'s maintenance history, logs the cost as an expense, and re-runs the health prediction.</p>
          <Field label="Actual cost (₹)"><input className="input" type="number" min="0" value={completion.actual_cost} onChange={(e) => setCompletion({ ...completion, actual_cost: e.target.value })} /></Field>
          <Field label="Work notes"><textarea className="input" value={completion.notes} onChange={(e) => setCompletion({ ...completion, notes: e.target.value })} /></Field>
          <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={completion.was_breakdown} onChange={(e) => setCompletion({ ...completion, was_breakdown: e.target.checked })} />This was a breakdown repair</label>
        </form>
      </Modal>
      <ConfirmDialog open={!!confirm} busy={!!busy}
        title={confirm?.type === 'cancel' ? 'Cancel this task?' : 'Delete this task?'}
        confirmLabel={confirm?.type === 'cancel' ? 'Cancel task' : 'Delete'}
        message={confirm?.type === 'cancel' ? `"${confirm?.s.title}" will be marked as cancelled. You can restore it later.` : `"${confirm?.s.title}" will be permanently removed.`}
        onConfirm={doConfirm} onCancel={() => setConfirm(null)} />
    </>
  )
}
