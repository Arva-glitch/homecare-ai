import { useEffect, useState } from 'react'
import { Award, CalendarRange, Pencil, Plus, Trash2, Wallet } from 'lucide-react'
import { Bar, BarChart, CartesianGrid, Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { applianceApi, expenseApi } from '../api/services'
import { errorMessage } from '../api/client'
import { useApi } from '../hooks'
import { useOptions } from '../context/OptionsContext'
import { useToast } from '../context/ToastContext'
import { ConfirmDialog, EmptyState, ErrorState, Field, Modal, PageHeader, PageLoader, Select, Spinner, StatCard } from '../components/ui'
import { fmtDate, inr, todayISO } from '../utils/format'

const TYPE_COLORS = { Repair: '#d93f3f', Servicing: '#2e9d66', Replacement: '#6d5bd0', Parts: '#e0a526', Other: '#7b8686' }
const blank = () => ({ appliance_id: '', expense_type: 'Servicing', amount: '', expense_date: todayISO(), vendor: '', description: '' })

export default function Expenses() {
  const opts = useOptions()
  const toast = useToast()
  const thisYear = new Date().getFullYear()
  const [year, setYear] = useState(thisYear)
  const [filters, setFilters] = useState({ appliance_id: '', expense_type: '' })
  const { data: summary, loading: sLoading, error: sError, reload: reloadSummary } = useApi(() => expenseApi.summary(year), [year])
  const { data: list, loading, reload } = useApi(
    () => expenseApi.list({ year, ...Object.fromEntries(Object.entries(filters).filter(([, v]) => v)) }), [year, filters])
  const { data: apps } = useApi(() => applianceApi.list({ sort_by: 'name', order: 'asc' }), [])
  const [formOpen, setFormOpen] = useState(false)
  const [editing, setEditing] = useState(null)
  const [form, setForm] = useState(blank())
  const [busy, setBusy] = useState(false)
  const [deleting, setDeleting] = useState(null)

  useEffect(() => {
    if (!formOpen) return
    setForm(editing ? { ...blank(), ...Object.fromEntries(Object.entries(editing).map(([k, v]) => [k, v ?? ''])) } : blank())
  }, [formOpen, editing])

  const refresh = () => { reload(true); reloadSummary(true) }
  const set = (k) => (v) => setForm((f) => ({ ...f, [k]: v?.target ? v.target.value : v }))

  const save = async (e) => {
    e.preventDefault()
    setBusy(true)
    const body = { appliance_id: form.appliance_id ? Number(form.appliance_id) : null, expense_type: form.expense_type, amount: Number(form.amount),
      expense_date: form.expense_date, vendor: form.vendor || null, description: form.description || null }
    try {
      if (editing) await expenseApi.update(editing.id, body); else await expenseApi.create(body)
      toast.success(editing ? 'Expense updated' : 'Expense added')
      setFormOpen(false); setEditing(null); refresh()
    } catch (err) { toast.error(errorMessage(err)) } finally { setBusy(false) }
  }

  const doDelete = async () => {
    setBusy(true)
    try { await expenseApi.remove(deleting.id); toast.success('Expense deleted'); setDeleting(null); refresh() } catch (e) { toast.error(errorMessage(e)) } finally { setBusy(false) }
  }

  if (sLoading && !summary) return <PageLoader label="Loading expenses…" />
  if (sError) return <ErrorState message={sError} onRetry={reloadSummary} />

  const years = Array.from(new Set([thisYear, ...(summary?.yearly || []).map((y) => y.year)])).sort((a, b) => b - a)
  const appRows = summary.by_appliance.filter((x) => x.year_total > 0)

  return (
    <>
      <PageHeader title="Expenses" subtitle="Track repair, servicing and replacement costs."
        actions={<>
          <div className="w-28"><Select value={year} onChange={(v) => setYear(Number(v))} options={years.map((y) => ({ value: y, label: String(y) }))} aria-label="Year" /></div>
          <button className="btn-primary" onClick={() => { setEditing(null); setFormOpen(true) }}><Plus className="h-4 w-4" />Add expense</button>
        </>} />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard icon={Wallet} label="Total maintenance expenditure" value={inr(summary.total_all_time)} hint="All time" />
        <StatCard icon={CalendarRange} tone="sky" label={`Spent in ${year}`} value={inr(summary.total_year)} />
        <StatCard icon={Award} tone="red" label="Highest-cost appliance" value={summary.highest_cost_appliance?.appliance_name || '—'}
          hint={summary.highest_cost_appliance ? `${inr(summary.highest_cost_appliance.total)} all time` : undefined} />
        <StatCard icon={Wallet} tone="charcoal" label="Avg. per month" value={inr(summary.total_year / (year === thisYear ? new Date().getMonth() + 1 : 12))} hint={String(year)} />
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="card p-5 lg:col-span-2">
          <h2 className="font-semibold">Monthly expenditure — {year}</h2>
          <p className="mb-3 text-xs text-charcoal-500">Stacked by expense type</p>
          <div className="h-72">
            <ResponsiveContainer>
              <BarChart data={summary.monthly} margin={{ left: -10 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e5e5" />
                <XAxis dataKey="month" tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
                <YAxis tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
                <Tooltip formatter={(v) => inr(v)} cursor={{ fill: '#effaf3' }} />
                <Legend wrapperStyle={{ fontSize: 12 }} iconType="circle" />
                {opts.expense_types.map((t, i) => (
                  <Bar key={t} dataKey={t} stackId="a" fill={TYPE_COLORS[t]} radius={i === opts.expense_types.length - 1 ? [5, 5, 0, 0] : 0} />
                ))}
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="card p-5">
          <h2 className="font-semibold">By type — {year}</h2>
          {summary.by_type.length === 0 ? <EmptyState icon={Wallet} title="No expenses this year" /> : (
            <div className="h-72">
              <ResponsiveContainer>
                <PieChart>
                  <Pie data={summary.by_type} dataKey="total" nameKey="type" innerRadius={50} outerRadius={85} paddingAngle={2}>
                    {summary.by_type.map((d) => <Cell key={d.type} fill={TYPE_COLORS[d.type]} />)}
                  </Pie>
                  <Tooltip formatter={(v) => inr(v)} />
                  <Legend wrapperStyle={{ fontSize: 12 }} iconType="circle" />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="card p-5">
          <h2 className="mb-3 font-semibold">Appliance-wise expenses</h2>
          {summary.by_appliance.length === 0 ? <p className="text-sm text-charcoal-500">No expenses recorded.</p> : (
            <ul className="space-y-3">
              {summary.by_appliance.map((x) => {
                const max = summary.by_appliance[0].total || 1
                return (
                  <li key={x.appliance_id ?? 'none'}>
                    <div className="flex justify-between text-sm"><span className="truncate pr-2">{x.appliance_name}</span><span className="font-semibold tabular-nums">{inr(x.total)}</span></div>
                    <div className="mt-1 h-2 rounded-full bg-charcoal-100"><div className="h-full rounded-full bg-brand-500" style={{ width: `${(x.total / max) * 100}%` }} /></div>
                    <p className="mt-0.5 text-[11px] text-charcoal-400">{x.count} entr{x.count === 1 ? 'y' : 'ies'} · {inr(x.year_total)} in {year}</p>
                  </li>
                )
              })}
            </ul>
          )}
          {summary.yearly.length > 0 && (
            <>
              <h3 className="mb-2 mt-6 text-sm font-semibold">Yearly report</h3>
              <table className="w-full text-sm"><tbody>
                {summary.yearly.slice().reverse().map((y) => <tr key={y.year}><td className="py-1 text-charcoal-500">{y.year}</td><td className="py-1 text-right font-medium tabular-nums">{inr(y.total)}</td></tr>)}
              </tbody></table>
            </>
          )}
          {appRows.length === 0 && null}
        </div>

        <div className="card lg:col-span-2">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-charcoal-100 p-4">
            <h2 className="font-semibold">Expense records — {year}</h2>
            <div className="flex gap-2">
              <div className="w-44"><Select value={filters.appliance_id} onChange={(v) => setFilters({ ...filters, appliance_id: v })} placeholder="All appliances" aria-label="Appliance filter"
                options={(apps?.items || []).map((a) => ({ value: a.id, label: a.name }))} /></div>
              <div className="w-36"><Select value={filters.expense_type} onChange={(v) => setFilters({ ...filters, expense_type: v })} options={opts.expense_types} placeholder="All types" aria-label="Type filter" /></div>
            </div>
          </div>
          {loading && !list ? <div className="flex justify-center p-8"><Spinner /></div>
            : list.length === 0 ? <EmptyState icon={Wallet} title="No expenses found" message="Add one, or complete a maintenance task with a cost." />
              : <div className="overflow-x-auto"><table className="w-full">
                <thead><tr><th className="table-th">Date</th><th className="table-th">Appliance</th><th className="table-th">Type</th><th className="table-th">Details</th><th className="table-th text-right">Amount</th><th className="table-th" /></tr></thead>
                <tbody>
                  {list.map((e) => (
                    <tr key={e.id} className="hover:bg-charcoal-50/50">
                      <td className="table-td whitespace-nowrap">{fmtDate(e.expense_date)}</td>
                      <td className="table-td">{e.appliance_name || <span className="text-charcoal-400">General</span>}</td>
                      <td className="table-td"><span className="inline-flex items-center gap-1.5 text-xs font-medium"><span className="h-2 w-2 rounded-full" style={{ background: TYPE_COLORS[e.expense_type] }} />{e.expense_type}</span></td>
                      <td className="table-td max-w-[220px] truncate text-charcoal-600">{e.description || e.vendor || '—'}</td>
                      <td className="table-td text-right font-semibold tabular-nums">{inr(e.amount)}</td>
                      <td className="table-td whitespace-nowrap text-right">
                        <button className="btn-ghost btn-sm" onClick={() => { setEditing(e); setFormOpen(true) }} aria-label="Edit"><Pencil className="h-3.5 w-3.5" /></button>
                        <button className="btn-ghost btn-sm text-red-600" onClick={() => setDeleting(e)} aria-label="Delete"><Trash2 className="h-3.5 w-3.5" /></button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table></div>}
        </div>
      </div>

      <Modal open={formOpen} onClose={() => { setFormOpen(false); setEditing(null) }} title={editing ? 'Edit expense' : 'Add expense'}
        footer={<><button className="btn-secondary" onClick={() => { setFormOpen(false); setEditing(null) }}>Cancel</button>
          <button form="exp-form" className="btn-primary" disabled={busy}>{busy && <Spinner className="h-4 w-4 text-white" />}Save</button></>}>
        <form id="exp-form" onSubmit={save} className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Field label="Appliance" className="sm:col-span-2"><Select value={form.appliance_id} onChange={set('appliance_id')} placeholder="General / not linked"
            options={(apps?.items || []).map((a) => ({ value: a.id, label: `${a.name} (${a.category})` }))} /></Field>
          <Field label="Type *"><Select value={form.expense_type} onChange={set('expense_type')} options={opts.expense_types} /></Field>
          <Field label="Amount (₹) *"><input className="input" type="number" min="1" step="0.01" required value={form.amount} onChange={set('amount')} /></Field>
          <Field label="Date *"><input className="input" type="date" required max={todayISO()} value={form.expense_date} onChange={set('expense_date')} /></Field>
          <Field label="Vendor"><input className="input" value={form.vendor} onChange={set('vendor')} /></Field>
          <Field label="Description" className="sm:col-span-2"><textarea className="input" value={form.description} onChange={set('description')} /></Field>
        </form>
      </Modal>
      <ConfirmDialog open={!!deleting} busy={busy} title="Delete expense?" confirmLabel="Delete"
        message={`${deleting ? inr(deleting.amount) : ''} on ${deleting ? fmtDate(deleting.expense_date) : ''} will be permanently deleted.`}
        onConfirm={doDelete} onCancel={() => setDeleting(null)} />
    </>
  )
}
