export const inr = (n) =>
  new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(Number(n || 0))

export const fmtDate = (s) => {
  if (!s) return '—'
  const d = new Date(s.length === 10 ? `${s}T00:00:00` : s)
  return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
}

export const fmtDateTime = (s) => {
  if (!s) return '—'
  return new Date(s).toLocaleString('en-IN', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

export const timeAgo = (s) => {
  if (!s) return ''
  const diff = (Date.now() - new Date(s).getTime()) / 1000
  if (diff < 60) return 'just now'
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  if (diff < 86400 * 30) return `${Math.floor(diff / 86400)}d ago`
  return fmtDate(s)
}

export const daysUntil = (s) => {
  if (!s) return null
  const target = new Date(s.length === 10 ? `${s}T00:00:00` : s)
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return Math.round((target - today) / 86400000)
}

export const todayISO = () => {
  const d = new Date()
  return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 10)
}

// datetime-local input value from a Date / ISO string
export const toLocalInput = (v) => {
  const d = v ? new Date(v) : new Date()
  return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 16)
}

export const RISK_COLORS = { Low: '#2e9d66', Medium: '#e0a526', High: '#ea7a2b', Critical: '#d93f3f' }

export const healthColor = (h) => (h == null ? '#a0a9a9' : h >= 75 ? RISK_COLORS.Low : h >= 55 ? RISK_COLORS.Medium : h >= 35 ? RISK_COLORS.High : RISK_COLORS.Critical)

// Remove empty strings so optional fields are sent as null/omitted
export const clean = (obj) => Object.fromEntries(Object.entries(obj).map(([k, v]) => [k, v === '' ? null : v]))
