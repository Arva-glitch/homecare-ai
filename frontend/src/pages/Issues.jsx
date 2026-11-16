import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Bot, CalendarPlus, CheckCircle2, ChevronDown, ImagePlus, Send, Trash2, TriangleAlert } from 'lucide-react'
import { applianceApi, issueApi, scheduleApi } from '../api/services'
import { assetUrl, errorMessage } from '../api/client'
import { useApi } from '../hooks'
import { useOptions } from '../context/OptionsContext'
import { useToast } from '../context/ToastContext'
import { notifyChanged } from '../components/Layout'
import { ConfirmDialog, EmptyState, ErrorState, Field, HealthBar, Markdown, PageHeader, RiskBadge, Select, Spinner, StatusBadge } from '../components/ui'
import { fmtDate, todayISO } from '../utils/format'

const blank = () => ({ appliance_id: '', problem_category: '', description: '', severity: 'Medium', reported_date: todayISO() })

export default function Issues() {
  const opts = useOptions()
  const toast = useToast()
  const { data: apps } = useApi(() => applianceApi.list({ sort_by: 'name', order: 'asc' }), [])
  const [statusFilter, setStatusFilter] = useState('')
  const { data, loading, error, reload } = useApi(() => issueApi.list(statusFilter ? { status_filter: statusFilter } : {}), [statusFilter])
  const [form, setForm] = useState(blank())
  const [file, setFile] = useState(null)
  const [busy, setBusy] = useState(false)
  const [result, setResult] = useState(null)
  const [expanded, setExpanded] = useState(null)
  const [deleting, setDeleting] = useState(null)
  const [scheduling, setScheduling] = useState(false)

  const set = (k) => (v) => setForm((f) => ({ ...f, [k]: v?.target ? v.target.value : v }))

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    try {
      const r = await issueApi.create({ ...form, appliance_id: Number(form.appliance_id) })
      if (file) r.issue = await issueApi.uploadImage(r.issue.id, file)
      setResult(r)
      setForm(blank()); setFile(null)
      toast.success(`Issue saved with priority ${r.issue.priority}`)
      reload(true); notifyChanged()
    } catch (err) { toast.error(errorMessage(err)) } finally { setBusy(false) }
  }

  const scheduleRecommended = async () => {
    const rec = result.recommended_schedule
    setScheduling(true)
    try {
      await scheduleApi.create({
        appliance_id: rec.appliance_id, maintenance_type: rec.maintenance_type, scheduled_at: `${rec.suggested_date}T10:00`,
        priority: rec.priority, status: 'Pending', is_ai_suggested: true,
        description: `Recommended after issue report: ${rec.reason}`,
      })
      toast.success('Maintenance scheduled (Pending) — see the Maintenance Scheduler')
      setResult({ ...result, recommended_schedule: { ...rec, booked: true } })
      notifyChanged()
    } catch (err) { toast.error(errorMessage(err)) } finally { setScheduling(false) }
  }

  const updateStatus = async (i, status) => {
    try { await issueApi.update(i.id, { status }); toast.success(`Issue marked ${status.toLowerCase()}`); reload(true); notifyChanged() } catch (e) { toast.error(errorMessage(e)) }
  }

  const doDelete = async () => {
    setBusy(true)
    try { await issueApi.remove(deleting.id); toast.success('Issue deleted'); setDeleting(null); reload(true) } catch (e) { toast.error(errorMessage(e)) } finally { setBusy(false) }
  }

  const noAppliances = apps && apps.items.length === 0

  return (
    <>
      <PageHeader title="Report an Issue" subtitle="Log a problem to get AI troubleshooting suggestions and an updated risk assessment." />
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-5">
        <form onSubmit={submit} className="card space-y-4 p-5 lg:col-span-2">
          <h2 className="font-semibold">New issue</h2>
          {noAppliances && <p className="rounded-xl bg-amber-50 p-3 text-sm text-amber-800">Add an appliance first. <Link to="/appliances?new=1" className="underline">Add appliance</Link></p>}
          <Field label="Appliance *"><Select required value={form.appliance_id} onChange={set('appliance_id')} placeholder="Select appliance"
            options={(apps?.items || []).map((a) => ({ value: a.id, label: `${a.name} (${a.category})` }))} /></Field>
          <Field label="Problem category *"><Select required value={form.problem_category} onChange={set('problem_category')} options={opts.problem_categories} placeholder="Select category" /></Field>
          <Field label="Problem description *"><textarea className="input min-h-[100px]" required minLength={5} value={form.description} onChange={set('description')}
            placeholder="What is happening? When did it start? Any sounds, smells or error codes?" /></Field>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Severity *"><Select value={form.severity} onChange={set('severity')} options={opts.severities} /></Field>
            <Field label="Reported date"><input className="input" type="date" max={todayISO()} value={form.reported_date} onChange={set('reported_date')} /></Field>
          </div>
          <label className="flex cursor-pointer items-center gap-3 rounded-xl border border-dashed border-charcoal-200 p-3 text-sm text-charcoal-500 hover:bg-charcoal-50">
            <ImagePlus className="h-5 w-5 text-brand-600" /><span className="flex-1 truncate">{file ? file.name : 'Attach a photo (optional)'}</span>
            <input type="file" accept="image/png,image/jpeg,image/webp,image/gif" className="hidden" onChange={(e) => setFile(e.target.files?.[0] || null)} />
          </label>
          <button className="btn-primary w-full" disabled={busy || noAppliances}>{busy ? <Spinner className="h-4 w-4 text-white" /> : <Send className="h-4 w-4" />}Submit issue</button>
        </form>

        <div className="card p-5 lg:col-span-3">
          {!result ? (
            <EmptyState icon={Bot} title="AI analysis appears here" message="After you submit, you'll see troubleshooting suggestions, the assigned priority, the updated health score and a recommended service date." />
          ) : (
            <div className="space-y-4">
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="font-semibold">Analysis for {result.issue.appliance_name}</h2>
                <StatusBadge status={result.issue.priority} />
                <span className="text-xs text-charcoal-400">via {result.issue.suggestion_source === 'llm' ? 'LLM' : 'rule-based knowledge base'}</span>
              </div>
              <div className="grid gap-3 rounded-xl bg-charcoal-50 p-4 sm:grid-cols-3">
                <div className="sm:col-span-2"><p className="mb-1 text-xs text-charcoal-500">Updated health score</p><HealthBar score={result.prediction.health_score} /></div>
                <div><p className="mb-1 text-xs text-charcoal-500">Risk level</p><RiskBadge risk={result.prediction.risk_level} /></div>
              </div>
              <div className="rounded-xl border border-charcoal-100 p-4"><Markdown text={result.issue.ai_suggestions} /></div>
              {result.recommended_schedule && (
                <div className="flex flex-col gap-3 rounded-xl border border-brand-200 bg-brand-50 p-4 sm:flex-row sm:items-center">
                  <div className="flex-1 text-sm">
                    <p className="font-semibold text-brand-800">Recommended: {result.recommended_schedule.maintenance_type} by {fmtDate(result.recommended_schedule.suggested_date)}</p>
                    <p className="text-brand-900/80">{result.recommended_schedule.reason}</p>
                  </div>
                  {result.recommended_schedule.booked
                    ? <span className="inline-flex items-center gap-1 text-sm font-semibold text-brand-700"><CheckCircle2 className="h-4 w-4" />Scheduled</span>
                    : <button className="btn-primary" onClick={scheduleRecommended} disabled={scheduling}>{scheduling ? <Spinner className="h-4 w-4 text-white" /> : <CalendarPlus className="h-4 w-4" />}Schedule it</button>}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="card mt-4">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-charcoal-100 p-5">
          <h2 className="font-semibold">Reported issues</h2>
          <div className="w-44"><Select value={statusFilter} onChange={setStatusFilter} options={opts.issue_statuses} placeholder="All statuses" aria-label="Status filter" /></div>
        </div>
        {error ? <div className="p-4"><ErrorState message={error} onRetry={reload} /></div>
          : loading ? <div className="flex justify-center p-8"><Spinner /></div>
            : data.length === 0 ? <EmptyState icon={TriangleAlert} title="No issues reported" message="Great — nothing is broken right now." />
              : <ul className="divide-y divide-charcoal-100">
                {data.map((i) => (
                  <li key={i.id} className="p-4">
                    <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
                      <button className="flex min-w-0 flex-1 items-start gap-3 text-left" onClick={() => setExpanded(expanded === i.id ? null : i.id)} aria-expanded={expanded === i.id}>
                        <StatusBadge status={i.priority} />
                        <div className="min-w-0">
                          <p className="font-medium">{i.problem_category} — {i.appliance_name}</p>
                          <p className="line-clamp-1 text-sm text-charcoal-500">{i.description}</p>
                          <p className="text-xs text-charcoal-400">{fmtDate(i.reported_date)} · {i.severity} severity</p>
                        </div>
                        <ChevronDown className={`ml-auto mt-1 h-4 w-4 shrink-0 text-charcoal-400 transition ${expanded === i.id ? 'rotate-180' : ''}`} />
                      </button>
                      <div className="flex items-center gap-2">
                        <StatusBadge status={i.status} />
                        <select className="input w-36 py-1.5 text-xs" value={i.status} onChange={(e) => updateStatus(i, e.target.value)} aria-label="Update status">
                          {opts.issue_statuses.map((s) => <option key={s}>{s}</option>)}
                        </select>
                        <button className="btn-ghost btn-sm text-red-600" onClick={() => setDeleting(i)} aria-label="Delete issue"><Trash2 className="h-3.5 w-3.5" /></button>
                      </div>
                    </div>
                    {expanded === i.id && (
                      <div className="mt-3 grid gap-4 rounded-xl bg-charcoal-50 p-4 md:grid-cols-3">
                        <div className="md:col-span-2"><p className="mb-1 text-xs font-semibold text-charcoal-500">Description</p><p className="text-sm">{i.description}</p>
                          <p className="mb-1 mt-3 text-xs font-semibold text-charcoal-500">AI troubleshooting suggestions</p><Markdown text={i.ai_suggestions} /></div>
                        {i.image_url && <img src={assetUrl(i.image_url)} alt="Issue" className="max-h-60 w-full rounded-xl object-cover" />}
                      </div>
                    )}
                  </li>
                ))}
              </ul>}
      </div>
      <ConfirmDialog open={!!deleting} busy={busy} title="Delete issue?" confirmLabel="Delete"
        message="The issue will be removed and the appliance's risk re-assessed." onConfirm={doDelete} onCancel={() => setDeleting(null)} />
    </>
  )
}
