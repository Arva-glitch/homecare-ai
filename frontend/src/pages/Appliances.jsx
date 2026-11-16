import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { Pencil, Plus, Refrigerator, Search, Trash2 } from 'lucide-react'
import { applianceApi } from '../api/services'
import { assetUrl, errorMessage } from '../api/client'
import { useApi } from '../hooks'
import { useOptions } from '../context/OptionsContext'
import { useToast } from '../context/ToastContext'
import ApplianceForm from '../components/ApplianceForm'
import { ConfirmDialog, EmptyState, ErrorState, HealthBar, PageHeader, RiskBadge, Select, Spinner } from '../components/ui'
import { fmtDate } from '../utils/format'

export default function Appliances() {
  const opts = useOptions()
  const toast = useToast()
  const [params, setParams] = useSearchParams()
  const [filters, setFilters] = useState({ search: '', category: '', risk_level: '', condition: '', sort_by: 'created_at', order: 'desc' })
  const [debounced, setDebounced] = useState(filters)
  const [formOpen, setFormOpen] = useState(params.get('new') === '1')
  const [editing, setEditing] = useState(null)
  const [deleting, setDeleting] = useState(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => { const t = setTimeout(() => setDebounced(filters), 250); return () => clearTimeout(t) }, [filters])
  const { data, loading, error, reload } = useApi(
    () => applianceApi.list(Object.fromEntries(Object.entries(debounced).filter(([, v]) => v))), [debounced])

  const set = (k) => (v) => setFilters((f) => ({ ...f, [k]: v }))
  const closeForm = () => { setFormOpen(false); setEditing(null); if (params.get('new')) setParams({}) }

  const doDelete = async () => {
    setBusy(true)
    try {
      await applianceApi.remove(deleting.id)
      toast.success(`${deleting.name} deleted`)
      setDeleting(null)
      reload(true)
    } catch (e) { toast.error(errorMessage(e)) } finally { setBusy(false) }
  }

  const [sortField, sortOrder] = [filters.sort_by, filters.order]
  return (
    <>
      <PageHeader title="My Appliances" subtitle="Register, search and manage every appliance in your home."
        actions={<button className="btn-primary" onClick={() => setFormOpen(true)}><Plus className="h-4 w-4" />Add appliance</button>} />

      <div className="card mb-4 grid grid-cols-1 gap-3 p-4 sm:grid-cols-2 lg:grid-cols-6">
        <div className="relative sm:col-span-2">
          <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-charcoal-400" />
          <input className="input pl-9" placeholder="Search name, brand or model…" value={filters.search} onChange={(e) => set('search')(e.target.value)} aria-label="Search appliances" />
        </div>
        <Select value={filters.category} onChange={set('category')} options={opts.appliance_categories} placeholder="All categories" aria-label="Category filter" />
        <Select value={filters.risk_level} onChange={set('risk_level')} options={opts.risk_levels} placeholder="Any risk" aria-label="Risk filter" />
        <Select value={filters.condition} onChange={set('condition')} options={opts.conditions} placeholder="Any condition" aria-label="Condition filter" />
        <Select value={`${sortField}:${sortOrder}`} aria-label="Sort"
          onChange={(v) => { const [s, o] = v.split(':'); setFilters((f) => ({ ...f, sort_by: s, order: o })) }}
          options={[
            { value: 'created_at:desc', label: 'Newest first' }, { value: 'name:asc', label: 'Name A–Z' },
            { value: 'health_score:asc', label: 'Health: lowest first' }, { value: 'health_score:desc', label: 'Health: highest first' },
            { value: 'purchase_date:asc', label: 'Oldest purchase' }, { value: 'last_service_date:asc', label: 'Longest since service' },
            { value: 'warranty_expiry:asc', label: 'Warranty ending soonest' },
          ]} />
      </div>

      {error ? <ErrorState message={error} onRetry={reload} />
        : loading && !data ? <div className="flex justify-center p-10"><Spinner className="h-7 w-7" /></div>
          : data.items.length === 0 ? (
            <div className="card">
              <EmptyState icon={Refrigerator} title={Object.values(debounced).some((v, i) => i < 4 && v) ? 'No matching appliances' : 'No appliances yet'}
                message="Add appliances to start tracking their health and maintenance."
                action={<button className="btn-primary" onClick={() => setFormOpen(true)}><Plus className="h-4 w-4" />Add appliance</button>} />
            </div>
          ) : (
            <>
              <p className="mb-3 text-xs text-charcoal-500">{data.total} appliance(s){loading && ' · refreshing…'}</p>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
                {data.items.map((a) => (
                  <div key={a.id} className="card flex flex-col overflow-hidden">
                    <Link to={`/appliances/${a.id}`} className="flex gap-4 p-4">
                      <div className="flex h-16 w-16 shrink-0 items-center justify-center overflow-hidden rounded-xl bg-brand-50">
                        {a.image_url ? <img src={assetUrl(a.image_url)} alt={a.name} className="h-full w-full object-cover" /> : <Refrigerator className="h-7 w-7 text-brand-600" />}
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-start justify-between gap-2">
                          <p className="truncate font-semibold">{a.name}</p>
                          <RiskBadge risk={a.risk_level} />
                        </div>
                        <p className="text-xs text-charcoal-500">{a.category}{a.brand && ` · ${a.brand}`}{a.model_number && ` ${a.model_number}`}</p>
                        <div className="mt-2"><HealthBar score={a.health_score} /></div>
                      </div>
                    </Link>
                    <div className="grid grid-cols-3 gap-2 border-t border-charcoal-100 px-4 py-3 text-xs">
                      <div><p className="text-charcoal-400">Last service</p><p className="font-medium">{fmtDate(a.last_service_date)}</p></div>
                      <div><p className="text-charcoal-400">Next service</p><p className="font-medium">{fmtDate(a.next_service_date)}</p></div>
                      <div><p className="text-charcoal-400">Condition</p><p className="font-medium">{a.condition}</p></div>
                    </div>
                    <div className="mt-auto flex justify-end gap-1 border-t border-charcoal-100 px-3 py-2">
                      <button className="btn-ghost btn-sm" onClick={() => { setEditing(a); setFormOpen(true) }}><Pencil className="h-3.5 w-3.5" />Edit</button>
                      <button className="btn-ghost btn-sm text-red-600 hover:bg-red-50" onClick={() => setDeleting(a)}><Trash2 className="h-3.5 w-3.5" />Delete</button>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}

      <ApplianceForm open={formOpen} appliance={editing} onClose={closeForm} onSaved={() => reload(true)} />
      <ConfirmDialog open={!!deleting} busy={busy} title="Delete appliance?" confirmLabel="Delete"
        message={`"${deleting?.name}" and its maintenance history, schedules, issues and predictions will be permanently deleted. Expenses are kept but unlinked.`}
        onConfirm={doDelete} onCancel={() => setDeleting(null)} />
    </>
  )
}
