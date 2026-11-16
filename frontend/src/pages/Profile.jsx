import { useState } from 'react'
import { KeyRound, Save, UserRound } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { userApi } from '../api/services'
import { errorMessage } from '../api/client'
import { Field, PageHeader, Spinner } from '../components/ui'
import { fmtDate } from '../utils/format'

export default function Profile() {
  const { user, setUser, handleToken } = useAuth()
  const toast = useToast()
  const [form, setForm] = useState({
    full_name: user.full_name, phone: user.phone || '', address: user.address || '', household_name: user.household_name || '',
    email_notifications: user.email_notifications,
  })
  const [pw, setPw] = useState({ current_password: '', new_password: '', confirm: '' })
  const [busy, setBusy] = useState(null)

  const save = async (e) => {
    e.preventDefault()
    setBusy('profile')
    try {
      const u = await userApi.update({ ...form, phone: form.phone || null, address: form.address || null, household_name: form.household_name || null })
      setUser(u); toast.success('Profile updated')
    } catch (err) { toast.error(errorMessage(err)) } finally { setBusy(null) }
  }

  const changePw = async (e) => {
    e.preventDefault()
    if (pw.new_password !== pw.confirm) { toast.error('New passwords do not match'); return }
    setBusy('pw')
    try {
      handleToken(await userApi.changePassword({ current_password: pw.current_password, new_password: pw.new_password }))
      setPw({ current_password: '', new_password: '', confirm: '' })
      toast.success('Password changed. Other sessions have been signed out.')
    } catch (err) { toast.error(errorMessage(err)) } finally { setBusy(null) }
  }

  return (
    <>
      <PageHeader title="Profile" subtitle={`Member since ${fmtDate(user.created_at)}`} />
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <form onSubmit={save} className="card space-y-4 p-5 lg:col-span-2">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-brand-600 text-lg font-bold text-white">{user.full_name[0]}</div>
            <div><p className="font-semibold">{user.full_name}</p><p className="text-sm text-charcoal-500">{user.email}</p></div>
          </div>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Field label="Full name"><input className="input" required minLength={2} value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} /></Field>
            <Field label="Email (login)"><input className="input" value={user.email} disabled /></Field>
            <Field label="Phone"><input className="input" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} /></Field>
            <Field label="Household name"><input className="input" value={form.household_name} onChange={(e) => setForm({ ...form, household_name: e.target.value })} /></Field>
            <Field label="Address" className="sm:col-span-2"><textarea className="input" value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} /></Field>
          </div>
          <label className="flex items-start gap-3 rounded-xl border border-charcoal-100 p-3 text-sm">
            <input type="checkbox" className="mt-0.5" checked={form.email_notifications} onChange={(e) => setForm({ ...form, email_notifications: e.target.checked })} />
            <span><span className="font-medium">Email me critical alerts</span><br /><span className="text-charcoal-500">Requires SMTP to be configured on the server. In-app notifications are always on.</span></span>
          </label>
          <div className="flex justify-end"><button className="btn-primary" disabled={busy === 'profile'}>{busy === 'profile' ? <Spinner className="h-4 w-4 text-white" /> : <Save className="h-4 w-4" />}Save profile</button></div>
        </form>

        <form onSubmit={changePw} className="card h-fit space-y-4 p-5">
          <div className="flex items-center gap-2"><KeyRound className="h-5 w-5 text-brand-600" /><h2 className="font-semibold">Change password</h2></div>
          <Field label="Current password"><input className="input" type="password" required value={pw.current_password} onChange={(e) => setPw({ ...pw, current_password: e.target.value })} /></Field>
          <Field label="New password"><input className="input" type="password" required minLength={8} value={pw.new_password} onChange={(e) => setPw({ ...pw, new_password: e.target.value })} /></Field>
          <Field label="Confirm new password"><input className="input" type="password" required value={pw.confirm} onChange={(e) => setPw({ ...pw, confirm: e.target.value })} /></Field>
          <button className="btn-primary w-full" disabled={busy === 'pw'}>{busy === 'pw' ? <Spinner className="h-4 w-4 text-white" /> : <UserRound className="h-4 w-4" />}Update password</button>
        </form>
      </div>
    </>
  )
}
