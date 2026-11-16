import { useState } from 'react'
import { Link, useLocation, useNavigate, useSearchParams } from 'react-router-dom'
import { House, KeyRound, Mail, ShieldCheck } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { authApi } from '../api/services'
import { errorMessage } from '../api/client'
import { Field, Spinner } from '../components/ui'

function Shell({ title, subtitle, children }) {
  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <div className="relative hidden flex-col justify-between overflow-hidden bg-charcoal-900 p-12 text-white lg:flex">
        <div className="flex items-center gap-3">
          <div className="rounded-xl bg-brand-500 p-2"><House className="h-6 w-6" /></div>
          <span className="text-lg font-bold">Predictive HomeCare AI</span>
        </div>
        <div className="max-w-md">
          <h2 className="text-3xl font-bold leading-tight text-white">Keep every appliance in your home healthy — before it breaks.</h2>
          <p className="mt-4 text-charcoal-300">Track appliances, get AI-driven health scores and maintenance priorities, schedule servicing,
            log issues and expenses, and ask the HomeCare AI Assistant for help.</p>
          <ul className="mt-8 space-y-3 text-sm text-charcoal-200">
            {['Predictive health scores (0–100) with clear explanations', 'Smart service scheduling and alerts', 'Expense reports and appliance history'].map((t) => (
              <li key={t} className="flex items-center gap-2"><ShieldCheck className="h-4 w-4 text-brand-400" />{t}</li>
            ))}
          </ul>
        </div>
        <p className="text-xs text-charcoal-500">Software Engineering Project · Smart Household Maintenance Manager</p>
        <div className="pointer-events-none absolute -bottom-32 -right-32 h-96 w-96 rounded-full bg-brand-600/20 blur-3xl" />
      </div>
      <div className="flex items-center justify-center p-6">
        <div className="w-full max-w-md">
          <div className="mb-8 flex items-center gap-2 lg:hidden">
            <div className="rounded-xl bg-brand-600 p-2"><House className="h-5 w-5 text-white" /></div>
            <span className="font-bold">Predictive HomeCare AI</span>
          </div>
          <h1 className="text-2xl font-bold">{title}</h1>
          {subtitle && <p className="mt-1 text-sm text-charcoal-500">{subtitle}</p>}
          <div className="mt-6">{children}</div>
        </div>
      </div>
    </div>
  )
}

export function Login() {
  const { login } = useAuth()
  const toast = useToast()
  const navigate = useNavigate()
  const location = useLocation()
  const [form, setForm] = useState({ email: '', password: '' })
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true); setError('')
    try {
      const u = await login(form.email, form.password)
      toast.success(`Welcome, ${u.full_name.split(' ')[0]}!`)
      navigate(location.state?.from?.pathname || '/', { replace: true })
    } catch (err) {
      setError(errorMessage(err, 'Login failed'))
    } finally { setBusy(false) }
  }

  return (
    <Shell title="Sign in" subtitle="Access your household maintenance dashboard.">
      <form onSubmit={submit} className="space-y-4">
        {error && <div className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}
        <Field label="Email"><input className="input" type="email" required autoComplete="email" value={form.email}
          onChange={(e) => setForm({ ...form, email: e.target.value })} /></Field>
        <Field label="Password"><input className="input" type="password" required autoComplete="current-password" value={form.password}
          onChange={(e) => setForm({ ...form, password: e.target.value })} /></Field>
        <div className="flex justify-end"><Link to="/forgot-password" className="text-sm font-medium text-brand-700 hover:underline">Forgot password?</Link></div>
        <button className="btn-primary w-full py-2.5" disabled={busy}>{busy && <Spinner className="h-4 w-4 text-white" />}Sign in</button>
      </form>
      <div className="mt-6 rounded-xl border border-dashed border-brand-300 bg-brand-50 p-4 text-sm">
        <p className="font-semibold text-brand-800">Demo credentials</p>
        <p className="mt-1 text-brand-900">demo@homecare.ai · Demo@1234</p>
        <button type="button" className="btn-secondary btn-sm mt-3" onClick={() => setForm({ email: 'demo@homecare.ai', password: 'Demo@1234' })}>
          Fill demo login
        </button>
      </div>
      <p className="mt-6 text-center text-sm text-charcoal-500">New here? <Link to="/register" className="font-semibold text-brand-700 hover:underline">Create an account</Link></p>
    </Shell>
  )
}

export function Register() {
  const { register } = useAuth()
  const toast = useToast()
  const navigate = useNavigate()
  const [form, setForm] = useState({ full_name: '', email: '', household_name: '', password: '', confirm: '' })
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })

  const submit = async (e) => {
    e.preventDefault()
    if (form.password !== form.confirm) { setError('Passwords do not match'); return }
    setBusy(true); setError('')
    try {
      await register({ full_name: form.full_name, email: form.email, password: form.password, household_name: form.household_name || null })
      toast.success('Account created. Add your first appliance to get started!')
      navigate('/appliances')
    } catch (err) { setError(errorMessage(err, 'Registration failed')) } finally { setBusy(false) }
  }

  return (
    <Shell title="Create your account" subtitle="Your household data is private to your account.">
      <form onSubmit={submit} className="space-y-4">
        {error && <div className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}
        <Field label="Full name"><input className="input" required minLength={2} value={form.full_name} onChange={set('full_name')} /></Field>
        <Field label="Email"><input className="input" type="email" required value={form.email} onChange={set('email')} /></Field>
        <Field label="Household name (optional)"><input className="input" value={form.household_name} onChange={set('household_name')} placeholder="e.g. Sharma Residence" /></Field>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Password"><input className="input" type="password" required minLength={8} value={form.password} onChange={set('password')} /></Field>
          <Field label="Confirm password"><input className="input" type="password" required value={form.confirm} onChange={set('confirm')} /></Field>
        </div>
        <p className="text-xs text-charcoal-400">At least 8 characters, including letters and numbers.</p>
        <button className="btn-primary w-full py-2.5" disabled={busy}>{busy && <Spinner className="h-4 w-4 text-white" />}Create account</button>
      </form>
      <p className="mt-6 text-center text-sm text-charcoal-500">Already registered? <Link to="/login" className="font-semibold text-brand-700 hover:underline">Sign in</Link></p>
    </Shell>
  )
}

export function ForgotPassword() {
  const [email, setEmail] = useState('')
  const [busy, setBusy] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true); setError('')
    try { setResult(await authApi.forgot(email)) } catch (err) { setError(errorMessage(err)) } finally { setBusy(false) }
  }

  return (
    <Shell title="Forgot password" subtitle="We'll send a secure, time-limited reset link to your email.">
      {result ? (
        <div className="space-y-4">
          <div className="flex gap-3 rounded-xl bg-brand-50 p-4 text-sm text-brand-800"><Mail className="h-5 w-5 shrink-0" />{result.message}</div>
          {result.dev_reset_token && (
            <div className="rounded-xl border border-dashed border-amber-300 bg-amber-50 p-4 text-sm text-amber-900">
              <p className="font-semibold">Development mode</p>
              <p className="mt-1">No SMTP server is configured, so the reset link is shown here instead of being emailed.</p>
              <Link className="btn-primary btn-sm mt-3" to={`/reset-password?token=${encodeURIComponent(result.dev_reset_token)}`}>Open reset link</Link>
            </div>
          )}
          <Link to="/login" className="btn-secondary w-full">Back to sign in</Link>
        </div>
      ) : (
        <form onSubmit={submit} className="space-y-4">
          {error && <div className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}
          <Field label="Email"><input className="input" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} /></Field>
          <button className="btn-primary w-full py-2.5" disabled={busy}>{busy && <Spinner className="h-4 w-4 text-white" />}Send reset link</button>
          <Link to="/login" className="block text-center text-sm text-charcoal-500 hover:underline">Back to sign in</Link>
        </form>
      )}
    </Shell>
  )
}

export function ResetPassword() {
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const toast = useToast()
  const [form, setForm] = useState({ password: '', confirm: '' })
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const token = params.get('token') || ''

  const submit = async (e) => {
    e.preventDefault()
    if (form.password !== form.confirm) { setError('Passwords do not match'); return }
    setBusy(true); setError('')
    try {
      await authApi.reset(token, form.password)
      toast.success('Password reset. Please sign in with your new password.')
      navigate('/login')
    } catch (err) { setError(errorMessage(err)) } finally { setBusy(false) }
  }

  return (
    <Shell title="Choose a new password" subtitle="Reset links expire after 30 minutes and can be used once.">
      {!token ? (
        <div className="rounded-xl bg-red-50 p-4 text-sm text-red-700">This reset link is missing its token. <Link className="underline" to="/forgot-password">Request a new one</Link>.</div>
      ) : (
        <form onSubmit={submit} className="space-y-4">
          {error && <div className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}
          <Field label="New password"><input className="input" type="password" required minLength={8} value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} /></Field>
          <Field label="Confirm new password"><input className="input" type="password" required value={form.confirm} onChange={(e) => setForm({ ...form, confirm: e.target.value })} /></Field>
          <button className="btn-primary w-full py-2.5" disabled={busy}>{busy ? <Spinner className="h-4 w-4 text-white" /> : <KeyRound className="h-4 w-4" />}Reset password</button>
        </form>
      )}
    </Shell>
  )
}
