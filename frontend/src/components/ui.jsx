import { useEffect } from 'react'
import { AlertTriangle, Inbox, Loader2, X } from 'lucide-react'
import { healthColor } from '../utils/format'

export function Spinner({ className = 'h-5 w-5' }) {
  return <Loader2 className={`animate-spin text-brand-600 ${className}`} aria-label="Loading" />
}

export function PageLoader({ label = 'Loading…' }) {
  return (
    <div className="flex min-h-[40vh] flex-col items-center justify-center gap-3 text-sm text-charcoal-500">
      <Spinner className="h-7 w-7" />
      {label}
    </div>
  )
}

export function ErrorState({ message, onRetry }) {
  return (
    <div className="card flex flex-col items-center gap-3 p-10 text-center">
      <AlertTriangle className="h-8 w-8 text-red-500" />
      <p className="text-sm text-charcoal-600">{message}</p>
      {onRetry && <button className="btn-secondary" onClick={onRetry}>Try again</button>}
    </div>
  )
}

export function EmptyState({ icon: Icon = Inbox, title, message, action }) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 px-6 py-12 text-center">
      <div className="rounded-2xl bg-brand-50 p-3"><Icon className="h-7 w-7 text-brand-600" /></div>
      <h3 className="mt-1 font-semibold">{title}</h3>
      {message && <p className="max-w-sm text-sm text-charcoal-500">{message}</p>}
      {action && <div className="mt-3">{action}</div>}
    </div>
  )
}

export function PageHeader({ title, subtitle, actions }) {
  return (
    <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">{title}</h1>
        {subtitle && <p className="mt-1 text-sm text-charcoal-500">{subtitle}</p>}
      </div>
      {actions && <div className="flex flex-wrap gap-2">{actions}</div>}
    </div>
  )
}

export function Modal({ open, onClose, title, children, footer, size = 'max-w-lg' }) {
  useEffect(() => {
    if (!open) return
    const onKey = (e) => e.key === 'Escape' && onClose?.()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onClose])
  if (!open) return null
  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-charcoal-950/40 p-0 backdrop-blur-sm sm:items-center sm:p-4" onMouseDown={onClose}>
      <div role="dialog" aria-modal="true" aria-label={title}
        className={`card flex max-h-[92vh] w-full ${size} flex-col rounded-b-none sm:rounded-2xl`} onMouseDown={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between border-b border-charcoal-100 px-5 py-4">
          <h2 className="text-lg font-semibold">{title}</h2>
          <button className="btn-ghost p-1.5" onClick={onClose} aria-label="Close"><X className="h-5 w-5" /></button>
        </div>
        <div className="overflow-y-auto px-5 py-4">{children}</div>
        {footer && <div className="flex justify-end gap-2 border-t border-charcoal-100 px-5 py-3">{footer}</div>}
      </div>
    </div>
  )
}

export function ConfirmDialog({ open, title = 'Are you sure?', message, confirmLabel = 'Confirm', danger = true, busy, onConfirm, onCancel }) {
  return (
    <Modal open={open} onClose={onCancel} title={title} size="max-w-md"
      footer={<>
        <button className="btn-secondary" onClick={onCancel} disabled={busy}>Cancel</button>
        <button className={danger ? 'btn-danger' : 'btn-primary'} onClick={onConfirm} disabled={busy}>
          {busy && <Spinner className="h-4 w-4 text-white" />}{confirmLabel}
        </button>
      </>}>
      <p className="text-sm text-charcoal-600">{message}</p>
    </Modal>
  )
}

const RISK_STYLE = {
  Low: 'bg-brand-50 text-brand-700 ring-brand-200',
  Medium: 'bg-amber-50 text-amber-700 ring-amber-200',
  High: 'bg-orange-50 text-orange-700 ring-orange-200',
  Critical: 'bg-red-50 text-red-700 ring-red-200',
}
export function RiskBadge({ risk }) {
  if (!risk) return <span className="text-xs text-charcoal-400">Not assessed</span>
  return <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ring-1 ring-inset ${RISK_STYLE[risk]}`}>{risk}</span>
}

const STATUS_STYLE = {
  Pending: 'bg-amber-50 text-amber-700', Scheduled: 'bg-sky-50 text-sky-700', 'In Progress': 'bg-violet-50 text-violet-700',
  Completed: 'bg-brand-50 text-brand-700', Cancelled: 'bg-charcoal-100 text-charcoal-500',
  Open: 'bg-red-50 text-red-700', Resolved: 'bg-brand-50 text-brand-700',
  P1: 'bg-red-600 text-white', P2: 'bg-orange-500 text-white', P3: 'bg-amber-400 text-charcoal-900', P4: 'bg-charcoal-200 text-charcoal-700',
}
export function StatusBadge({ status }) {
  return <span className={`inline-flex whitespace-nowrap rounded-full px-2.5 py-0.5 text-xs font-semibold ${STATUS_STYLE[status] || 'bg-charcoal-100'}`}>{status}</span>
}

export function HealthBar({ score }) {
  const pct = Math.max(0, Math.min(100, score ?? 0))
  return (
    <div className="flex items-center gap-2">
      <div className="h-2 w-full min-w-[60px] overflow-hidden rounded-full bg-charcoal-100">
        <div className="h-full rounded-full transition-all" style={{ width: `${pct}%`, background: healthColor(score) }} />
      </div>
      <span className="w-9 text-right text-xs font-semibold tabular-nums">{score == null ? '—' : Math.round(score)}</span>
    </div>
  )
}

export function StatCard({ icon: Icon, label, value, hint, tone = 'brand' }) {
  const tones = {
    brand: 'bg-brand-50 text-brand-600', amber: 'bg-amber-50 text-amber-600', red: 'bg-red-50 text-red-600',
    sky: 'bg-sky-50 text-sky-600', charcoal: 'bg-charcoal-100 text-charcoal-700', violet: 'bg-violet-50 text-violet-600',
  }
  return (
    <div className="card flex items-start gap-4 p-5">
      <div className={`rounded-xl p-2.5 ${tones[tone]}`}><Icon className="h-5 w-5" /></div>
      <div className="min-w-0">
        <p className="text-xs font-medium text-charcoal-500">{label}</p>
        <p className="mt-0.5 truncate text-2xl font-bold tabular-nums text-charcoal-900">{value}</p>
        {hint && <p className="mt-0.5 text-xs text-charcoal-400">{hint}</p>}
      </div>
    </div>
  )
}

export function Field({ label, error, children, className = '' }) {
  return (
    <label className={`block ${className}`}>
      <span className="label">{label}</span>
      {children}
      {error && <span className="mt-1 block text-xs text-red-600">{error}</span>}
    </label>
  )
}

export function Select({ value, onChange, options, placeholder, ...rest }) {
  return (
    <select className="input" value={value ?? ''} onChange={(e) => onChange(e.target.value)} {...rest}>
      {placeholder !== undefined && <option value="">{placeholder}</option>}
      {options.map((o) => typeof o === 'string'
        ? <option key={o} value={o}>{o}</option>
        : <option key={o.value} value={o.value}>{o.label}</option>)}
    </select>
  )
}

// Minimal, safe markdown renderer for assistant replies (bold, italics, lists, paragraphs).
function inline(text, keyBase) {
  const parts = text.split(/(\*\*[^*]+\*\*|_[^_]+_|\*[^*]+\*|`[^`]+`)/g)
  return parts.map((p, i) => {
    const k = `${keyBase}-${i}`
    if (/^\*\*[^*]+\*\*$/.test(p)) return <strong key={k}>{p.slice(2, -2)}</strong>
    if (/^`[^`]+`$/.test(p)) return <code key={k}>{p.slice(1, -1)}</code>
    if (/^(_[^_]+_|\*[^*]+\*)$/.test(p)) return <em key={k}>{p.slice(1, -1)}</em>
    return p
  })
}
export function Markdown({ text }) {
  const lines = (text || '').split('\n')
  const blocks = []
  let list = null
  lines.forEach((raw, idx) => {
    const line = raw.trimEnd()
    const ul = line.match(/^\s*[-*•]\s+(.*)/)
    const ol = line.match(/^\s*\d+[.)]\s+(.*)/)
    if (ul || ol) {
      const type = ul ? 'ul' : 'ol'
      if (!list || list.type !== type) { list = { type, items: [] }; blocks.push(list) }
      list.items.push((ul || ol)[1])
      return
    }
    list = null
    if (line.trim() === '') return
    const h = line.match(/^#{1,4}\s+(.*)/)
    blocks.push({ type: 'p', text: h ? `**${h[1]}**` : line, idx })
  })
  return (
    <div className="md text-sm leading-relaxed">
      {blocks.map((b, i) => b.type === 'p'
        ? <p key={i}>{inline(b.text, i)}</p>
        : b.type === 'ul'
          ? <ul key={i}>{b.items.map((it, j) => <li key={j}>{inline(it, `${i}-${j}`)}</li>)}</ul>
          : <ol key={i}>{b.items.map((it, j) => <li key={j}>{inline(it, `${i}-${j}`)}</li>)}</ol>)}
    </div>
  )
}
