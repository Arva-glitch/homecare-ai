import { Link } from 'react-router-dom'
import {
  Activity, AlertTriangle, CalendarCheck2, CalendarClock, CheckCircle2, ClipboardList, IndianRupee, Refrigerator,
  Wrench, TriangleAlert, Wallet, Plus,
} from 'lucide-react'
import { Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis, Legend } from 'recharts'
import { dashboardApi } from '../api/services'
import { useApi } from '../hooks'
import { EmptyState, ErrorState, HealthBar, PageHeader, PageLoader, RiskBadge, StatCard, StatusBadge } from '../components/ui'
import { RISK_COLORS, daysUntil, fmtDate, inr, timeAgo } from '../utils/format'
import MiniCalendar from '../components/MiniCalendar'

const ACT_ICON = { maintenance: Wrench, issue: TriangleAlert, expense: Wallet, schedule: CalendarClock, appliance: Refrigerator }
const ALERT_TONE = { danger: 'border-red-200 bg-red-50 text-red-800', warning: 'border-amber-200 bg-amber-50 text-amber-800', info: 'border-sky-200 bg-sky-50 text-sky-800' }

export default function Dashboard() {
  const { data, loading, error, reload } = useApi(() => dashboardApi.summary(), [])
  if (loading) return <PageLoader label="Loading dashboard…" />
  if (error) return <ErrorState message={error} onRetry={reload} />
  const { stats } = data

  if (stats.total_appliances === 0) {
    return (
      <>
        <PageHeader title="Dashboard" subtitle="Your household at a glance" />
        <div className="card">
          <EmptyState icon={Refrigerator} title="No appliances yet"
            message="Register your household appliances to unlock health scores, maintenance predictions and alerts."
            action={<Link to="/appliances?new=1" className="btn-primary"><Plus className="h-4 w-4" />Add your first appliance</Link>} />
        </div>
      </>
    )
  }

  const pie = data.health_distribution.filter((d) => d.count > 0)

  return (
    <>
      <PageHeader title="Dashboard" subtitle="Your household at a glance — every figure is live from your records."
        actions={<Link to="/predictions" className="btn-primary"><Activity className="h-4 w-4" />View predictions</Link>} />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard icon={Refrigerator} label="Registered appliances" value={stats.total_appliances}
          hint={stats.average_health != null ? `Avg. health ${Math.round(stats.average_health)}/100` : undefined} />
        <StatCard icon={AlertTriangle} tone="red" label="Need maintenance" value={stats.needs_maintenance} hint={`${stats.open_issues} open issue(s)`} />
        <StatCard icon={CalendarClock} tone="sky" label="Upcoming tasks" value={stats.upcoming_tasks}
          hint={stats.overdue_tasks ? `${stats.overdue_tasks} overdue` : 'None overdue'} />
        <StatCard icon={CheckCircle2} tone="violet" label="Completed tasks" value={stats.completed_tasks} />
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="card p-5 lg:col-span-2">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h2 className="font-semibold">Monthly maintenance expenses</h2>
              <p className="text-xs text-charcoal-500">Last 12 months</p>
            </div>
            <div className="text-right">
              <p className="text-xs text-charcoal-500">All-time total</p>
              <p className="flex items-center justify-end text-lg font-bold"><IndianRupee className="h-4 w-4" />{inr(stats.total_expenses).replace('₹', '')}</p>
            </div>
          </div>
          <div className="h-64">
            <ResponsiveContainer>
              <BarChart data={data.monthly_expenses} margin={{ left: -10 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e5e5" />
                <XAxis dataKey="month" tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
                <YAxis tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
                <Tooltip formatter={(v) => inr(v)} cursor={{ fill: '#effaf3' }} />
                <Bar dataKey="total" name="Expenses" fill="#2e9d66" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="card p-5">
          <h2 className="font-semibold">Appliance health distribution</h2>
          <p className="text-xs text-charcoal-500">By predicted risk level</p>
          <div className="h-64">
            <ResponsiveContainer>
              <PieChart>
                <Pie data={pie} dataKey="count" nameKey="risk" innerRadius={55} outerRadius={85} paddingAngle={3}>
                  {pie.map((d) => <Cell key={d.risk} fill={RISK_COLORS[d.risk]} />)}
                </Pie>
                <Tooltip formatter={(v, n) => [`${v} appliance(s)`, `${n} risk`]} />
                <Legend iconType="circle" wrapperStyle={{ fontSize: 12 }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="card p-5 lg:col-span-2">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="font-semibold">Appliance health status</h2>
            <Link to="/appliances" className="text-sm font-medium text-brand-700 hover:underline">All appliances</Link>
          </div>
          <div className="divide-y divide-charcoal-100">
            {data.appliance_health.map((a) => {
              const dd = daysUntil(a.next_service_date)
              return (
                <Link key={a.id} to={`/appliances/${a.id}`} className="grid grid-cols-12 items-center gap-3 py-3 hover:bg-charcoal-50/60">
                  <div className="col-span-12 min-w-0 sm:col-span-4">
                    <p className="truncate text-sm font-medium">{a.name}</p>
                    <p className="text-xs text-charcoal-400">{a.category}</p>
                  </div>
                  <div className="col-span-6 sm:col-span-4"><HealthBar score={a.health_score} /></div>
                  <div className="col-span-3 sm:col-span-2"><RiskBadge risk={a.risk_level} /></div>
                  <div className="col-span-3 text-right text-xs text-charcoal-500 sm:col-span-2">
                    {dd == null ? '—' : dd <= 0 ? 'Due now' : `in ${dd}d`}
                  </div>
                </Link>
              )
            })}
          </div>
        </div>

        <div className="card p-5">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="font-semibold">AI maintenance alerts</h2>
            <Link to="/notifications" className="text-sm font-medium text-brand-700 hover:underline">All</Link>
          </div>
          {data.alerts.length === 0
            ? <EmptyState icon={CheckCircle2} title="All clear" message="No unread high-priority alerts." />
            : <div className="space-y-2">
              {data.alerts.map((a) => (
                <Link key={a.id} to={a.link || '/notifications'} className={`block rounded-xl border px-3 py-2.5 text-sm ${ALERT_TONE[a.severity]}`}>
                  <p className="font-semibold">{a.title}</p>
                  <p className="mt-0.5 line-clamp-2 text-xs opacity-90">{a.message}</p>
                </Link>
              ))}
            </div>}
        </div>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="card p-5 lg:col-span-2">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="font-semibold">Upcoming maintenance calendar</h2>
            <Link to="/scheduler" className="text-sm font-medium text-brand-700 hover:underline">Open scheduler</Link>
          </div>
          {data.calendar.length === 0
            ? <EmptyState icon={CalendarCheck2} title="Nothing scheduled" message="Nothing is booked in the next 60 days."
              action={<Link to="/scheduler" className="btn-secondary">Schedule maintenance</Link>} />
            : <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
              <MiniCalendar events={data.calendar} />
              <ul className="space-y-2">
                {data.calendar.slice(0, 6).map((s) => {
                  const overdue = new Date(s.scheduled_at) < new Date()
                  return (
                    <li key={s.id} className="flex items-start gap-3 rounded-xl border border-charcoal-100 p-3">
                      <div className={`rounded-lg px-2 py-1 text-center text-xs font-bold ${overdue ? 'bg-red-50 text-red-700' : 'bg-brand-50 text-brand-700'}`}>
                        {new Date(s.scheduled_at).toLocaleDateString('en-IN', { day: '2-digit', month: 'short' })}
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-sm font-medium">{s.title}</p>
                        <p className="text-xs text-charcoal-500">{s.appliance_name}{overdue && ' · overdue'}</p>
                      </div>
                      <StatusBadge status={s.status} />
                    </li>
                  )
                })}
              </ul>
            </div>}
        </div>

        <div className="card p-5">
          <h2 className="mb-3 font-semibold">Recent activity</h2>
          {data.recent_activities.length === 0
            ? <EmptyState icon={ClipboardList} title="No activity yet" />
            : <ul className="space-y-3">
              {data.recent_activities.map((a, i) => {
                const Icon = ACT_ICON[a.type] || ClipboardList
                return (
                  <li key={i}>
                    <Link to={a.link} className="flex items-start gap-3">
                      <div className="rounded-lg bg-charcoal-100 p-1.5"><Icon className="h-4 w-4 text-charcoal-600" /></div>
                      <div className="min-w-0">
                        <p className="text-sm leading-snug">{a.title}</p>
                        <p className="text-xs text-charcoal-400">{timeAgo(a.at)}</p>
                      </div>
                    </Link>
                  </li>
                )
              })}
            </ul>}
        </div>
      </div>
      <p className="mt-6 text-center text-xs text-charcoal-400">Next recommended service dates are predictions as of {fmtDate(new Date().toISOString())}.</p>
    </>
  )
}
