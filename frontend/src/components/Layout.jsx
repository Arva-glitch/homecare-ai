import { useCallback, useEffect, useState } from 'react'
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import {
  Bell, Bot, CalendarClock, LayoutDashboard, LogOut, Menu, Refrigerator, TriangleAlert,
  UserRound, Wallet, Activity, X, House,
} from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { notificationApi } from '../api/services'
import { ConfirmDialog } from './ui'

const NAV = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/appliances', label: 'My Appliances', icon: Refrigerator },
  { to: '/predictions', label: 'Predictive Maintenance', icon: Activity },
  { to: '/scheduler', label: 'Maintenance Scheduler', icon: CalendarClock },
  { to: '/issues', label: 'Report an Issue', icon: TriangleAlert },
  { to: '/expenses', label: 'Expenses', icon: Wallet },
  { to: '/assistant', label: 'AI HomeCare Assistant', icon: Bot },
  { to: '/notifications', label: 'Notifications', icon: Bell, badge: true },
  { to: '/profile', label: 'Profile', icon: UserRound },
]

export default function Layout() {
  const { user, logout } = useAuth()
  const [open, setOpen] = useState(false)
  const [unread, setUnread] = useState(0)
  const [confirmLogout, setConfirmLogout] = useState(false)
  const location = useLocation()
  const navigate = useNavigate()

  const loadUnread = useCallback(() => {
    notificationApi.unread().then((r) => setUnread(r.unread_count)).catch(() => {})
  }, [])

  useEffect(() => { setOpen(false); loadUnread() }, [location.pathname, loadUnread])
  useEffect(() => {
    const t = setInterval(loadUnread, 60000)
    window.addEventListener('notifications:changed', loadUnread)
    return () => { clearInterval(t); window.removeEventListener('notifications:changed', loadUnread) }
  }, [loadUnread])

  const doLogout = async () => { await logout(); navigate('/login') }

  const sidebar = (
    <div className="flex h-full flex-col bg-charcoal-900 text-charcoal-200">
      <div className="flex items-center gap-3 px-5 py-5">
        <div className="rounded-xl bg-brand-500 p-2"><House className="h-5 w-5 text-white" /></div>
        <div className="leading-tight">
          <p className="text-sm font-bold text-white">HomeCare AI</p>
          <p className="text-[11px] text-charcoal-400">Predictive maintenance</p>
        </div>
        <button className="ml-auto rounded-lg p-1 text-charcoal-400 hover:bg-charcoal-800 lg:hidden" onClick={() => setOpen(false)} aria-label="Close menu">
          <X className="h-5 w-5" />
        </button>
      </div>
      <nav className="flex-1 space-y-0.5 overflow-y-auto px-3 py-2">
        {NAV.map(({ to, label, icon: Icon, end, badge }) => (
          <NavLink key={to} to={to} end={end}
            className={({ isActive }) => `flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition ${
              isActive ? 'bg-brand-600 text-white' : 'hover:bg-charcoal-800 hover:text-white'}`}>
            <Icon className="h-[18px] w-[18px]" />
            <span className="flex-1">{label}</span>
            {badge && unread > 0 && (
              <span className="rounded-full bg-red-500 px-1.5 py-0.5 text-[10px] font-bold text-white">{unread > 99 ? '99+' : unread}</span>
            )}
          </NavLink>
        ))}
        <button onClick={() => setConfirmLogout(true)}
          className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition hover:bg-charcoal-800 hover:text-white">
          <LogOut className="h-[18px] w-[18px]" /> Logout
        </button>
      </nav>
      <div className="border-t border-charcoal-800 px-5 py-4">
        <p className="truncate text-sm font-semibold text-white">{user?.full_name}</p>
        <p className="truncate text-xs text-charcoal-400">{user?.household_name || user?.email}</p>
      </div>
    </div>
  )

  return (
    <div className="min-h-screen">
      <aside className="fixed inset-y-0 left-0 z-40 hidden w-64 lg:block">{sidebar}</aside>
      {open && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div className="absolute inset-0 bg-charcoal-950/50" onClick={() => setOpen(false)} />
          <aside className="absolute inset-y-0 left-0 w-72 max-w-[85%]">{sidebar}</aside>
        </div>
      )}
      <div className="lg:pl-64">
        <header className="sticky top-0 z-30 flex items-center gap-3 border-b border-charcoal-100 bg-white/80 px-4 py-3 backdrop-blur sm:px-6">
          <button className="btn-ghost p-2 lg:hidden" onClick={() => setOpen(true)} aria-label="Open menu"><Menu className="h-5 w-5" /></button>
          <p className="text-sm text-charcoal-500">Welcome back, <span className="font-semibold text-charcoal-800">{user?.full_name?.split(' ')[0]}</span></p>
          <button className="btn-ghost relative ml-auto p-2" onClick={() => navigate('/notifications')} aria-label="Notifications">
            <Bell className="h-5 w-5" />
            {unread > 0 && <span className="absolute right-1 top-1 h-2.5 w-2.5 rounded-full bg-red-500 ring-2 ring-white" />}
          </button>
        </header>
        <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
          <Outlet />
        </main>
      </div>
      <ConfirmDialog open={confirmLogout} title="Log out?" message="You will need to sign in again to access your household."
        confirmLabel="Log out" danger={false} onConfirm={doLogout} onCancel={() => setConfirmLogout(false)} />
    </div>
  )
}

export const notifyChanged = () => window.dispatchEvent(new Event('notifications:changed'))
