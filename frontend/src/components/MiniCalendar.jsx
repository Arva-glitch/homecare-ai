import { useMemo, useState } from 'react'
import { ChevronLeft, ChevronRight } from 'lucide-react'

const key = (d) => `${d.getFullYear()}-${d.getMonth()}-${d.getDate()}`

export default function MiniCalendar({ events = [], onSelectDay }) {
  const [cursor, setCursor] = useState(() => { const d = new Date(); d.setDate(1); return d })
  const byDay = useMemo(() => {
    const m = {}
    events.forEach((e) => { const k = key(new Date(e.scheduled_at)); (m[k] = m[k] || []).push(e) })
    return m
  }, [events])

  const year = cursor.getFullYear()
  const month = cursor.getMonth()
  const startOffset = (new Date(year, month, 1).getDay() + 6) % 7 // Monday-first
  const days = new Date(year, month + 1, 0).getDate()
  const cells = [...Array(startOffset).fill(null), ...Array.from({ length: days }, (_, i) => new Date(year, month, i + 1))]
  const todayKey = key(new Date())

  return (
    <div className="min-w-0">
      <div className="mb-2 flex items-center justify-between">
        <button className="btn-ghost p-1.5" onClick={() => setCursor(new Date(year, month - 1, 1))} aria-label="Previous month"><ChevronLeft className="h-4 w-4" /></button>
        <p className="text-sm font-semibold">{cursor.toLocaleDateString('en-IN', { month: 'long', year: 'numeric' })}</p>
        <button className="btn-ghost p-1.5" onClick={() => setCursor(new Date(year, month + 1, 1))} aria-label="Next month"><ChevronRight className="h-4 w-4" /></button>
      </div>
      <div className="grid grid-cols-7 gap-1 text-center text-[11px] font-semibold text-charcoal-400">
        {['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su'].map((d) => <div key={d}>{d}</div>)}
      </div>
      <div className="mt-1 grid grid-cols-7 gap-1">
        {cells.map((d, i) => {
          if (!d) return <div key={i} />
          const k = key(d)
          const ev = byDay[k]
          return (
            <button key={i} type="button" onClick={() => ev && onSelectDay?.(d, ev)}
              title={ev ? ev.map((e) => e.title).join('\n') : undefined}
              className={`relative aspect-square rounded-lg text-xs transition ${k === todayKey ? 'ring-2 ring-brand-400' : ''} ${
                ev ? 'bg-brand-600 font-semibold text-white hover:bg-brand-700' : 'text-charcoal-600 hover:bg-charcoal-100'}`}>
              {d.getDate()}
              {ev && ev.length > 1 && <span className="absolute right-0.5 top-0.5 text-[9px]">{ev.length}</span>}
            </button>
          )
        })}
      </div>
    </div>
  )
}
