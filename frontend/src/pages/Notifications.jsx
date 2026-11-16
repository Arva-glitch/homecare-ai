import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { AlertOctagon, Bell, BellOff, CalendarClock, CheckCheck, Info, RefreshCw, ShieldAlert, ShieldCheck, Trash2, Wrench } from 'lucide-react'
import { notificationApi } from '../api/services'
import { errorMessage } from '../api/client'
import { useApi } from '../hooks'
import { useToast } from '../context/ToastContext'
import { notifyChanged } from '../components/Layout'
import { EmptyState, ErrorState, PageHeader, Select, Spinner } from '../components/ui'
import { timeAgo } from '../utils/format'

const TYPES = [
  { value: 'upcoming_service', label: 'Upcoming servicing', icon: CalendarClock },
  { value: 'warranty', label: 'Warranty', icon: ShieldCheck },
  { value: 'high_risk', label: 'High-risk appliances', icon: ShieldAlert },
  { value: 'pending_maintenance', label: 'Pending maintenance', icon: Wrench },
  { value: 'critical_issue', label: 'Critical issues', icon: AlertOctagon },
  { value: 'system', label: 'System', icon: Info },
]
const ICON = Object.fromEntries(TYPES.map((t) => [t.value, t.icon]))
const TONE = { danger: 'bg-red-50 text-red-600', warning: 'bg-amber-50 text-amber-600', info: 'bg-sky-50 text-sky-600' }

export default function Notifications() {
  const toast = useToast()
  const navigate = useNavigate()
  const [type, setType] = useState('')
  const [unreadOnly, setUnreadOnly] = useState(false)
  const { data, loading, error, reload } = useApi(() => notificationApi.list({ type: type || undefined, unread_only: unreadOnly }), [type, unreadOnly])
  const [busy, setBusy] = useState(false)

  const act = async (fn, msg) => {
    try { await fn(); if (msg) toast.success(msg); reload(true); notifyChanged() } catch (e) { toast.error(errorMessage(e)) }
  }

  const refresh = async () => {
    setBusy(true)
    try { const r = await notificationApi.refresh(); toast.info(r.created ? `${r.created} new alert(s)` : 'No new alerts'); reload(true); notifyChanged() }
    catch (e) { toast.error(errorMessage(e)) } finally { setBusy(false) }
  }

  const open = async (n) => {
    if (!n.is_read) await notificationApi.markRead(n.id).catch(() => {})
    notifyChanged()
    if (n.link) navigate(n.link)
    else reload(true)
  }

  return (
    <>
      <PageHeader title="Notifications" subtitle={data ? `${data.unread_count} unread` : 'Alerts about servicing, warranties, risks and issues'}
        actions={<>
          <button className="btn-secondary" onClick={refresh} disabled={busy}>{busy ? <Spinner className="h-4 w-4" /> : <RefreshCw className="h-4 w-4" />}Check for alerts</button>
          <button className="btn-secondary" onClick={() => act(() => notificationApi.readAll(), 'All marked as read')} disabled={!data?.unread_count}><CheckCheck className="h-4 w-4" />Mark all read</button>
        </>} />
      <div className="card">
        <div className="flex flex-wrap items-center gap-3 border-b border-charcoal-100 p-4">
          <div className="w-56"><Select value={type} onChange={setType} options={TYPES} placeholder="All alert types" aria-label="Type filter" /></div>
          <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={unreadOnly} onChange={(e) => setUnreadOnly(e.target.checked)} />Unread only</label>
        </div>
        {error ? <div className="p-4"><ErrorState message={error} onRetry={reload} /></div>
          : loading ? <div className="flex justify-center p-10"><Spinner /></div>
            : data.items.length === 0 ? <EmptyState icon={BellOff} title="You're all caught up" message="New alerts will appear here." />
              : <ul className="divide-y divide-charcoal-100">
                {data.items.map((n) => {
                  const Icon = ICON[n.type] || Bell
                  return (
                    <li key={n.id} className={`flex items-start gap-3 p-4 ${n.is_read ? '' : 'bg-brand-50/40'}`}>
                      <div className={`rounded-xl p-2 ${TONE[n.severity]}`}><Icon className="h-4 w-4" /></div>
                      <button className="min-w-0 flex-1 text-left" onClick={() => open(n)}>
                        <p className={`text-sm ${n.is_read ? 'font-medium' : 'font-semibold'}`}>{n.title}{!n.is_read && <span className="ml-2 inline-block h-2 w-2 rounded-full bg-brand-500 align-middle" />}</p>
                        <p className="mt-0.5 text-sm text-charcoal-600">{n.message}</p>
                        <p className="mt-1 text-xs text-charcoal-400">{timeAgo(n.created_at)}</p>
                      </button>
                      <div className="flex shrink-0 gap-1">
                        <button className="btn-ghost btn-sm" onClick={() => act(() => notificationApi.markRead(n.id, !n.is_read))}>{n.is_read ? 'Unread' : 'Read'}</button>
                        <button className="btn-ghost btn-sm text-red-600" onClick={() => act(() => notificationApi.remove(n.id), 'Notification deleted')} aria-label="Delete"><Trash2 className="h-3.5 w-3.5" /></button>
                      </div>
                    </li>
                  )
                })}
              </ul>}
      </div>
    </>
  )
}
