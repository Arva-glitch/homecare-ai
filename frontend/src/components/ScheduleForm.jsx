import { useEffect, useState } from 'react'
import { Field, Modal, Select, Spinner } from './ui'
import { useOptions } from '../context/OptionsContext'
import { applianceApi, scheduleApi } from '../api/services'
import { errorMessage } from '../api/client'
import { useToast } from '../context/ToastContext'
import { toLocalInput } from '../utils/format'

const blank = () => ({
  appliance_id: '', title: '', maintenance_type: 'General Servicing', scheduled_at: toLocalInput(Date.now() + 86400000),
  description: '', status: 'Scheduled', priority: 'Normal', technician: '', estimated_cost: '', is_ai_suggested: false,
})

export default function ScheduleForm({ open, onClose, schedule, defaults, onSaved }) {
  const opts = useOptions()
  const toast = useToast()
  const [form, setForm] = useState(blank())
  const [appliances, setAppliances] = useState([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!open) return
    setError('')
    applianceApi.list({ sort_by: 'name', order: 'asc' }).then((r) => setAppliances(r.items)).catch(() => {})
    if (schedule) {
      setForm({ ...blank(), ...Object.fromEntries(Object.entries(schedule).map(([k, v]) => [k, v ?? ''])), scheduled_at: toLocalInput(schedule.scheduled_at) })
    } else {
      setForm({ ...blank(), ...(defaults || {}) })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, schedule, JSON.stringify(defaults || {})])

  const set = (k) => (v) => setForm((f) => ({ ...f, [k]: v?.target ? v.target.value : v }))

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true); setError('')
    const body = {
      appliance_id: Number(form.appliance_id), title: form.title || null, maintenance_type: form.maintenance_type,
      scheduled_at: form.scheduled_at, description: form.description || null, priority: form.priority,
      technician: form.technician || null, estimated_cost: form.estimated_cost === '' ? null : Number(form.estimated_cost),
    }
    try {
      const saved = schedule ? await scheduleApi.update(schedule.id, body)
        : await scheduleApi.create({ ...body, status: form.status, is_ai_suggested: !!form.is_ai_suggested })
      toast.success(schedule ? 'Task updated' : 'Maintenance scheduled')
      onSaved?.(saved)
      onClose()
    } catch (err) { setError(errorMessage(err)) } finally { setBusy(false) }
  }

  return (
    <Modal open={open} onClose={onClose} title={schedule ? 'Edit maintenance task' : 'Schedule maintenance'} size="max-w-xl"
      footer={<><button className="btn-secondary" onClick={onClose} disabled={busy}>Cancel</button>
        <button form="sched-form" className="btn-primary" disabled={busy}>{busy && <Spinner className="h-4 w-4 text-white" />}{schedule ? 'Save' : 'Schedule'}</button></>}>
      <form id="sched-form" onSubmit={submit} className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {error && <div className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700 sm:col-span-2">{error}</div>}
        <Field label="Appliance *" className="sm:col-span-2">
          <Select required value={form.appliance_id} onChange={set('appliance_id')} placeholder="Select appliance"
            options={appliances.map((a) => ({ value: a.id, label: `${a.name} (${a.category})` }))} />
        </Field>
        <Field label="Maintenance type *"><Select value={form.maintenance_type} onChange={set('maintenance_type')} options={opts.maintenance_types} /></Field>
        <Field label="Date & time *"><input className="input" type="datetime-local" required value={form.scheduled_at} onChange={set('scheduled_at')} /></Field>
        <Field label="Title (optional)" className="sm:col-span-2"><input className="input" value={form.title} onChange={set('title')} placeholder="Auto-generated if left blank" /></Field>
        {!schedule && <Field label="Status"><Select value={form.status} onChange={set('status')} options={['Scheduled', 'Pending']} /></Field>}
        <Field label="Priority"><Select value={form.priority} onChange={set('priority')} options={['Low', 'Normal', 'High', 'Urgent']} /></Field>
        <Field label="Technician / service provider"><input className="input" value={form.technician} onChange={set('technician')} /></Field>
        <Field label="Estimated cost (₹)"><input className="input" type="number" min="0" value={form.estimated_cost} onChange={set('estimated_cost')} /></Field>
        <Field label="Description" className="sm:col-span-2"><textarea className="input min-h-[70px]" value={form.description} onChange={set('description')} /></Field>
      </form>
    </Modal>
  )
}
