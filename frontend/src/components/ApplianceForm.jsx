import { useEffect, useState } from 'react'
import { ImagePlus } from 'lucide-react'
import { Field, Modal, Select, Spinner } from './ui'
import { useOptions } from '../context/OptionsContext'
import { applianceApi } from '../api/services'
import { errorMessage } from '../api/client'
import { useToast } from '../context/ToastContext'
import { clean, todayISO } from '../utils/format'

const EMPTY = {
  name: '', category: '', brand: '', model_number: '', purchase_date: '', installation_date: '', warranty_expiry: '',
  expected_lifespan_years: '', last_service_date: '', usage_frequency: 'Medium', condition: 'Good', location: '', notes: '',
}

export default function ApplianceForm({ open, onClose, appliance, onSaved }) {
  const opts = useOptions()
  const toast = useToast()
  const [form, setForm] = useState(EMPTY)
  const [file, setFile] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!open) return
    setError(''); setFile(null)
    setForm(appliance ? Object.fromEntries(Object.keys(EMPTY).map((k) => [k, appliance[k] ?? ''])) : EMPTY)
  }, [open, appliance])

  const set = (k) => (v) => setForm((f) => ({ ...f, [k]: typeof v === 'object' && v?.target ? v.target.value : v }))

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true); setError('')
    try {
      const body = clean({ ...form, expected_lifespan_years: form.expected_lifespan_years === '' ? '' : Number(form.expected_lifespan_years) })
      let saved = appliance ? await applianceApi.update(appliance.id, body) : await applianceApi.create(body)
      if (file) saved = await applianceApi.uploadImage(saved.id, file)
      toast.success(appliance ? 'Appliance updated and re-assessed' : `${saved.name} added — health score ${Math.round(saved.health_score)}/100`)
      onSaved?.(saved)
      onClose()
    } catch (err) { setError(errorMessage(err)) } finally { setBusy(false) }
  }

  const lifespanHint = form.category && opts.default_lifespan_years?.[form.category]
  return (
    <Modal open={open} onClose={onClose} title={appliance ? 'Edit appliance' : 'Add appliance'} size="max-w-2xl"
      footer={<>
        <button type="button" className="btn-secondary" onClick={onClose} disabled={busy}>Cancel</button>
        <button form="appliance-form" className="btn-primary" disabled={busy}>{busy && <Spinner className="h-4 w-4 text-white" />}{appliance ? 'Save changes' : 'Add appliance'}</button>
      </>}>
      <form id="appliance-form" onSubmit={submit} className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {error && <div className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700 sm:col-span-2">{error}</div>}
        <Field label="Appliance name *"><input className="input" required value={form.name} onChange={set('name')} placeholder="e.g. Kitchen Refrigerator" /></Field>
        <Field label="Category *"><Select required value={form.category} onChange={set('category')} options={opts.appliance_categories} placeholder="Select category" /></Field>
        <Field label="Brand"><input className="input" value={form.brand} onChange={set('brand')} /></Field>
        <Field label="Model number"><input className="input" value={form.model_number} onChange={set('model_number')} /></Field>
        <Field label="Purchase date"><input className="input" type="date" max={todayISO()} value={form.purchase_date} onChange={set('purchase_date')} /></Field>
        <Field label="Installation date"><input className="input" type="date" value={form.installation_date} onChange={set('installation_date')} /></Field>
        <Field label="Warranty expiry date"><input className="input" type="date" value={form.warranty_expiry} onChange={set('warranty_expiry')} /></Field>
        <Field label={`Expected lifespan (years)${lifespanHint ? ` · typical ${lifespanHint}` : ''}`}>
          <input className="input" type="number" min="1" max="50" step="0.5" value={form.expected_lifespan_years} onChange={set('expected_lifespan_years')} placeholder={lifespanHint ? String(lifespanHint) : ''} />
        </Field>
        <Field label="Last servicing date"><input className="input" type="date" max={todayISO()} value={form.last_service_date} onChange={set('last_service_date')} /></Field>
        <Field label="Usage frequency"><Select value={form.usage_frequency} onChange={set('usage_frequency')} options={opts.usage_frequencies} /></Field>
        <Field label="Condition"><Select value={form.condition} onChange={set('condition')} options={opts.conditions} /></Field>
        <Field label="Location in home"><input className="input" value={form.location} onChange={set('location')} placeholder="e.g. Kitchen" /></Field>
        <Field label="Notes" className="sm:col-span-2"><textarea className="input min-h-[70px]" value={form.notes} onChange={set('notes')} /></Field>
        <div className="sm:col-span-2">
          <span className="label">Appliance image</span>
          <label className="flex cursor-pointer items-center gap-3 rounded-xl border border-dashed border-charcoal-200 p-3 text-sm text-charcoal-500 hover:bg-charcoal-50">
            <ImagePlus className="h-5 w-5 text-brand-600" />
            <span className="flex-1 truncate">{file ? file.name : 'Choose a JPEG, PNG or WEBP image (max 5 MB)'}</span>
            <input type="file" accept="image/png,image/jpeg,image/webp,image/gif" className="hidden" onChange={(e) => setFile(e.target.files?.[0] || null)} />
          </label>
        </div>
      </form>
    </Modal>
  )
}
