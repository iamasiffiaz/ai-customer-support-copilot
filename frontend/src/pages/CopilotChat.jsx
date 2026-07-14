import { useEffect, useRef, useState } from 'react'
import toast from 'react-hot-toast'
import { copilotApi, getErrorMessage } from '../api/client'
import Button from '../components/Button.jsx'
import Textarea from '../components/Textarea.jsx'
import CitationCard from '../components/CitationCard.jsx'
import EmptyState from '../components/EmptyState.jsx'
import { formatDate } from '../utils/formatDate'

const suggestions = [
  'How do we handle refund requests?',
  'What is the policy for failed payments?',
  'How should I respond to login issues?',
  'What should I do if a customer wants to cancel?',
]

export default function CopilotChat() {
  const [sessionId, setSessionId] = useState(null)
  const [messages, setMessages] = useState([])
  const [question, setQuestion] = useState('')
  const [citations, setCitations] = useState([])
  const [loading, setLoading] = useState(false)
  const [sessions, setSessions] = useState([])
  const bottomRef = useRef(null)

  const loadSessions = async () => {
    try {
      setSessions(await copilotApi.sessions())
    } catch {
      /* optional */
    }
  }

  useEffect(() => {
    loadSessions()
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const ask = async (text = question) => {
    if (!text.trim() || loading) return
    const content = text.trim()
    setLoading(true)
    setMessages((prev) => [...prev, { role: 'user', content, id: `u-${Date.now()}` }])
    setQuestion('')
    try {
      const res = await copilotApi.ask(content, sessionId)
      setSessionId(res.session_id)
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: res.answer,
          id: res.message?.id || `a-${Date.now()}`,
          citations: res.citations || [],
        },
      ])
      setCitations(res.citations || [])
      loadSessions()
    } catch (e) {
      toast.error(getErrorMessage(e, 'Copilot request failed'))
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: 'I could not retrieve an answer right now. Check that the API is running and try again.',
          id: `err-${Date.now()}`,
          error: true,
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  const openSession = async (id) => {
    try {
      const session = await copilotApi.session(id)
      setSessionId(session.id)
      const msgs = (session.messages || []).map((m) => ({
        ...m,
        citations: m.citations || [],
      }))
      setMessages(msgs)
      const lastAssistant = [...msgs].reverse().find((m) => m.role === 'assistant')
      setCitations(lastAssistant?.citations || [])
    } catch (e) {
      toast.error(getErrorMessage(e, 'Could not open session'))
    }
  }

  return (
    <div className="space-y-5">
      <div>
        <h2 className="font-display text-3xl tracking-tight">Support Copilot</h2>
        <p className="text-[var(--color-ink-muted)] mt-1">
          Ask internal policy questions and get RAG-backed answers with clear citations.
        </p>
      </div>

      <div className="grid gap-4 xl:grid-cols-[240px_minmax(0,1fr)_300px]">
        <div className="panel p-3">
          <div className="flex items-center justify-between mb-2 px-1">
            <h3 className="text-sm font-semibold">Sessions</h3>
            <Button
              variant="ghost"
              onClick={() => {
                setSessionId(null)
                setMessages([])
                setCitations([])
              }}
            >
              New
            </Button>
          </div>
          <div className="space-y-1 max-h-[70vh] overflow-auto">
            {sessions.length ? (
              sessions.map((s) => (
                <button
                  key={s.id}
                  type="button"
                  onClick={() => openSession(s.id)}
                  className={`w-full text-left rounded-xl px-2.5 py-2 hover:bg-slate-50 ${
                    sessionId === s.id ? 'bg-[var(--color-accent-soft)] text-[#047857]' : ''
                  }`}
                >
                  <p className="text-sm font-medium line-clamp-2">{s.title}</p>
                  <p className="text-[11px] text-[var(--color-ink-muted)] mt-0.5">{formatDate(s.updated_at)}</p>
                </button>
              ))
            ) : (
              <p className="text-xs text-[var(--color-ink-muted)] px-2 py-4">No sessions yet.</p>
            )}
          </div>
        </div>

        <div className="panel p-4 flex flex-col min-h-[70vh]">
          <div className="flex-1 space-y-3 overflow-auto mb-4 pr-1">
            {!messages.length ? (
              <div className="space-y-2">
                <p className="text-sm text-[var(--color-ink-muted)]">Try a starter question:</p>
                {suggestions.map((s) => (
                  <button
                    key={s}
                    type="button"
                    className="block w-full text-left rounded-xl border border-[var(--color-line)] px-3 py-2.5 text-sm hover:border-[var(--color-accent)]/40"
                    onClick={() => ask(s)}
                  >
                    {s}
                  </button>
                ))}
              </div>
            ) : (
              messages.map((m) => (
                <button
                  key={m.id || `${m.role}-${m.content.slice(0, 24)}`}
                  type="button"
                  className={`w-full text-left rounded-2xl px-3.5 py-2.5 text-sm whitespace-pre-wrap ${
                    m.role === 'user'
                      ? 'bg-[var(--color-navy)] text-white ml-8'
                      : m.error
                        ? 'bg-rose-50 text-rose-900 mr-8 border border-rose-200'
                        : 'bg-slate-100 text-[var(--color-ink)] mr-8'
                  }`}
                  onClick={() => {
                    if (m.role === 'assistant' && m.citations) setCitations(m.citations)
                  }}
                >
                  {m.content}
                </button>
              ))
            )}
            {loading ? (
              <div className="mr-8 rounded-2xl bg-slate-100 px-3.5 py-2.5 text-sm text-[var(--color-ink-muted)]">
                Thinking with knowledge base context…
              </div>
            ) : null}
            <div ref={bottomRef} />
          </div>
          <Textarea
            rows={3}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                ask()
              }
            }}
            placeholder="Ask the support copilot… (Enter to send)"
          />
          <div className="mt-2">
            <Button onClick={() => ask()} disabled={loading}>
              {loading ? 'Thinking…' : 'Ask Copilot'}
            </Button>
          </div>
        </div>

        <div className="panel p-4 space-y-3">
          <h3 className="font-semibold">Citations</h3>
          {citations?.length ? (
            citations.map((c, i) => <CitationCard key={c.chunk_id || i} citation={c} index={i + 1} />)
          ) : (
            <EmptyState
              title="No citations yet"
              description="Ask a policy question. Click an assistant message to review its sources."
            />
          )}
        </div>
      </div>
    </div>
  )
}
