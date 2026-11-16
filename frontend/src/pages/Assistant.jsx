import { useEffect, useRef, useState } from 'react'
import { Bot, MessageSquarePlus, SendHorizonal, Trash2, User } from 'lucide-react'
import { chatApi } from '../api/services'
import { errorMessage } from '../api/client'
import { useApi } from '../hooks'
import { useToast } from '../context/ToastContext'
import { ConfirmDialog, Markdown, PageHeader, Spinner } from '../components/ui'
import { timeAgo } from '../utils/format'

const SUGGESTIONS = [
  'Why is my refrigerator making unusual noise?',
  'When should I service my AC?',
  'Why is my washing machine leaking?',
  'How can I reduce electricity consumption?',
  'Which appliance requires immediate maintenance?',
  'What maintenance tasks should I perform this month?',
]

export default function Assistant() {
  const toast = useToast()
  const { data: status } = useApi(() => chatApi.status(), [])
  const { data: sessions, reload: reloadSessions } = useApi(() => chatApi.sessions(), [])
  const [sessionId, setSessionId] = useState(null)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [loadingHistory, setLoadingHistory] = useState(false)
  const [deleting, setDeleting] = useState(null)
  const endRef = useRef(null)

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages, sending])

  const openSession = async (sid) => {
    setSessionId(sid); setLoadingHistory(true)
    try { setMessages(await chatApi.history(sid)) } catch (e) { toast.error(errorMessage(e)) } finally { setLoadingHistory(false) }
  }

  const newChat = () => { setSessionId(null); setMessages([]) }

  const send = async (text) => {
    const msg = (text ?? input).trim()
    if (!msg || sending) return
    setInput('')
    setMessages((m) => [...m, { id: `tmp-${Date.now()}`, role: 'user', message: msg, created_at: new Date().toISOString() }])
    setSending(true)
    try {
      const r = await chatApi.send(msg, sessionId)
      setSessionId(r.session_id)
      setMessages((m) => [...m, r.reply])
      reloadSessions(true)
    } catch (e) {
      toast.error(errorMessage(e))
      setMessages((m) => m.slice(0, -1))
      setInput(msg)
    } finally { setSending(false) }
  }

  const doDelete = async () => {
    try {
      await chatApi.removeSession(deleting)
      if (deleting === sessionId) newChat()
      toast.success('Conversation deleted')
      reloadSessions(true)
    } catch (e) { toast.error(errorMessage(e)) } finally { setDeleting(null) }
  }

  return (
    <>
      <PageHeader title="AI HomeCare Assistant" subtitle="Ask about appliance problems, servicing, energy saving and priorities."
        actions={<span className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-semibold ${status?.llm_enabled ? 'bg-brand-50 text-brand-700' : 'bg-amber-50 text-amber-700'}`}>
          <span className={`h-2 w-2 rounded-full ${status?.llm_enabled ? 'bg-brand-500' : 'bg-amber-500'}`} />{status ? status.mode : 'Checking…'}</span>} />
      <div className="grid h-[calc(100vh-12rem)] min-h-[520px] grid-cols-1 gap-4 lg:grid-cols-4">
        <aside className="card hidden flex-col overflow-hidden lg:flex">
          <div className="border-b border-charcoal-100 p-3"><button className="btn-primary w-full" onClick={newChat}><MessageSquarePlus className="h-4 w-4" />New conversation</button></div>
          <ul className="flex-1 space-y-1 overflow-y-auto p-2">
            {(sessions || []).length === 0 && <li className="p-3 text-xs text-charcoal-400">No conversations yet.</li>}
            {(sessions || []).map((s) => (
              <li key={s.session_id} className={`group flex items-center gap-1 rounded-xl ${sessionId === s.session_id ? 'bg-brand-50' : 'hover:bg-charcoal-50'}`}>
                <button className="min-w-0 flex-1 px-3 py-2 text-left" onClick={() => openSession(s.session_id)}>
                  <p className="truncate text-sm font-medium">{s.title}</p>
                  <p className="text-[11px] text-charcoal-400">{s.message_count} messages · {timeAgo(s.last_message_at)}</p>
                </button>
                <button className="mr-1 rounded-lg p-1.5 text-charcoal-400 opacity-0 hover:bg-red-50 hover:text-red-600 group-hover:opacity-100" onClick={() => setDeleting(s.session_id)} aria-label="Delete conversation"><Trash2 className="h-3.5 w-3.5" /></button>
              </li>
            ))}
          </ul>
        </aside>

        <section className="card flex flex-col overflow-hidden lg:col-span-3">
          <div className="flex items-center justify-between border-b border-charcoal-100 px-4 py-3 lg:hidden">
            <span className="text-sm font-semibold">Conversation</span>
            <button className="btn-secondary btn-sm" onClick={newChat}><MessageSquarePlus className="h-3.5 w-3.5" />New</button>
          </div>
          <div className="flex-1 space-y-4 overflow-y-auto p-4 sm:p-6">
            {loadingHistory ? <div className="flex justify-center p-10"><Spinner /></div>
              : messages.length === 0 ? (
                <div className="mx-auto flex max-w-xl flex-col items-center pt-6 text-center">
                  <div className="rounded-2xl bg-brand-50 p-3"><Bot className="h-8 w-8 text-brand-600" /></div>
                  <h2 className="mt-3 text-lg font-semibold">How can I help with your home today?</h2>
                  <p className="mt-1 text-sm text-charcoal-500">I use your registered appliances, their health scores and schedules to tailor my answers.
                    I'll suggest possible causes, not certain diagnoses, and tell you when to call a professional.</p>
                  <div className="mt-5 grid w-full gap-2 sm:grid-cols-2">
                    {SUGGESTIONS.map((s) => <button key={s} onClick={() => send(s)} className="rounded-xl border border-charcoal-100 px-3 py-2.5 text-left text-sm hover:border-brand-300 hover:bg-brand-50">{s}</button>)}
                  </div>
                </div>
              ) : messages.map((m) => (
                <div key={m.id} className={`flex gap-3 ${m.role === 'user' ? 'flex-row-reverse' : ''}`}>
                  <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${m.role === 'user' ? 'bg-charcoal-800 text-white' : 'bg-brand-600 text-white'}`}>
                    {m.role === 'user' ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
                  </div>
                  <div className={`max-w-[85%] rounded-2xl px-4 py-3 ${m.role === 'user' ? 'bg-charcoal-800 text-white' : 'bg-charcoal-50 ring-1 ring-charcoal-100'}`}>
                    {m.role === 'user' ? <p className="whitespace-pre-wrap text-sm">{m.message}</p> : <Markdown text={m.message} />}
                    {m.role === 'assistant' && m.source && <p className="mt-2 text-[10px] uppercase tracking-wide text-charcoal-400">{m.source === 'llm' ? 'LLM response' : 'Rule-based response'}</p>}
                  </div>
                </div>
              ))}
            {sending && <div className="flex items-center gap-3 text-sm text-charcoal-500"><div className="flex h-8 w-8 items-center justify-center rounded-full bg-brand-600"><Bot className="h-4 w-4 text-white" /></div><Spinner className="h-4 w-4" />Thinking…</div>}
            <div ref={endRef} />
          </div>
          <form className="flex gap-2 border-t border-charcoal-100 p-3" onSubmit={(e) => { e.preventDefault(); send() }}>
            <input className="input flex-1" value={input} onChange={(e) => setInput(e.target.value)} placeholder="Ask about any appliance…" maxLength={2000} aria-label="Message" />
            <button className="btn-primary" disabled={sending || !input.trim()} aria-label="Send"><SendHorizonal className="h-4 w-4" /></button>
          </form>
        </section>
      </div>
      <ConfirmDialog open={!!deleting} title="Delete conversation?" message="This conversation will be permanently deleted." confirmLabel="Delete"
        onConfirm={doDelete} onCancel={() => setDeleting(null)} />
    </>
  )
}
