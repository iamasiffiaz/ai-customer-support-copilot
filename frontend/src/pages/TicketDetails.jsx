import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import toast from 'react-hot-toast'
import { analysisApi, escalationsApi, repliesApi, ticketsApi, getErrorMessage } from '../api/client'
import Badge from '../components/Badge.jsx'
import Button from '../components/Button.jsx'
import Select from '../components/Select.jsx'
import Modal from '../components/Modal.jsx'
import ReplyEditor from '../components/ReplyEditor.jsx'
import CitationCard from '../components/CitationCard.jsx'
import TicketTimeline from '../components/TicketTimeline.jsx'
import LoadingSpinner from '../components/LoadingSpinner.jsx'
import { PRIORITIES, STATUSES, priorityColor, sentimentColor, statusColor } from '../utils/constants'
import { formatDate, formatMinutes } from '../utils/formatDate'

export default function TicketDetails() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [ticket, setTicket] = useState(null)
  const [analysis, setAnalysis] = useState(null)
  const [replies, setReplies] = useState([])
  const [escalations, setEscalations] = useState([])
  const [tone, setTone] = useState('Professional')
  const [replyText, setReplyText] = useState('')
  const [activeReplyId, setActiveReplyId] = useState(null)
  const [replyStatus, setReplyStatus] = useState(null)
  const [citations, setCitations] = useState([])
  const [insufficientContext, setInsufficientContext] = useState(false)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(false)

  const applyReply = (draft) => {
    if (!draft) return
    setActiveReplyId(draft.id)
    setReplyText(draft.content)
    setReplyStatus(draft.status)
    setTone(draft.tone || 'Professional')
    setCitations(draft.citations || [])
    setInsufficientContext(!(draft.citations && draft.citations.length))
  }

  const load = async () => {
    setLoading(true)
    try {
      const t = await ticketsApi.get(id)
      setTicket(t)
      const replyList = await repliesApi.list({ ticket_id: id })
      setReplies(replyList)
      if (replyList[0]) applyReply(replyList[0])
      else if (t.ai_suggested_reply) setReplyText(t.ai_suggested_reply)
      try {
        const a = await analysisApi.get(id)
        setAnalysis(a)
        if (a.suggested_reply_tone) setTone(a.suggested_reply_tone)
      } catch {
        setAnalysis(null)
      }
      const allEsc = await escalationsApi.list()
      setEscalations(allEsc.filter((e) => String(e.ticket_id) === String(id)))
    } catch (e) {
      toast.error(getErrorMessage(e, 'Ticket not found'))
      navigate('/tickets')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [id])

  const updateTicket = async (patch) => {
    try {
      setTicket(await ticketsApi.update(id, patch))
      toast.success('Ticket updated')
    } catch (e) {
      toast.error(getErrorMessage(e, 'Update failed'))
    }
  }

  const runAnalysis = async () => {
    setBusy(true)
    try {
      const result = await analysisApi.analyze(id)
      setAnalysis(result)
      setTone(result.suggested_reply_tone || tone)
      toast.success('AI analysis complete')
      await load()
    } catch (e) {
      toast.error(getErrorMessage(e, 'Analysis failed'))
    } finally {
      setBusy(false)
    }
  }

  const generateReply = async () => {
    setBusy(true)
    try {
      const draft = await repliesApi.generate(id, tone)
      applyReply(draft)
      toast.success('AI reply generated')
      await load()
    } catch (e) {
      toast.error(getErrorMessage(e, 'Reply generation failed'))
    } finally {
      setBusy(false)
    }
  }

  const saveDraft = async () => {
    if (!activeReplyId) return toast.error('Generate a reply first')
    try {
      const updated = await repliesApi.update(activeReplyId, { content: replyText, status: 'edited' })
      setReplyStatus(updated.status)
      toast.success('Draft saved')
      await load()
    } catch (e) {
      toast.error(getErrorMessage(e, 'Could not save draft'))
    }
  }

  const approveReply = async () => {
    if (!activeReplyId) return toast.error('Generate a reply first')
    try {
      if (replyText) await repliesApi.update(activeReplyId, { content: replyText })
      const updated = await repliesApi.approve(activeReplyId)
      setReplyStatus(updated.status)
      toast.success('Reply approved')
      await load()
    } catch (e) {
      toast.error(getErrorMessage(e, 'Approve failed'))
    }
  }

  const markSent = async () => {
    if (!activeReplyId) return toast.error('Generate a reply first')
    try {
      const updated = await repliesApi.markSent(activeReplyId)
      setReplyStatus(updated.status)
      toast.success('Marked as sent')
      await load()
    } catch (e) {
      toast.error(getErrorMessage(e, 'Could not mark sent'))
    }
  }

  const checkEscalation = async () => {
    setBusy(true)
    try {
      await escalationsApi.check(id)
      toast.success('Escalation checked')
      await load()
    } catch (e) {
      toast.error(getErrorMessage(e, 'Escalation check failed'))
    } finally {
      setBusy(false)
    }
  }

  const removeTicket = async () => {
    try {
      await ticketsApi.remove(id)
      toast.success('Ticket deleted')
      navigate('/tickets')
    } catch (e) {
      toast.error(getErrorMessage(e, 'Delete failed'))
    }
  }

  if (loading || !ticket) return <LoadingSpinner label="Loading ticket…" />

  const priorityReason = analysis?.raw_response?.priority_reason
  const urgent = ticket.priority === 'Urgent' || ticket.sentiment === 'Frustrated'

  return (
    <div className="space-y-5">
      <div className={`panel p-5 ${urgent ? 'ticket-urgent' : ticket.status === 'Escalated' ? 'ticket-escalated' : ''}`}>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <Link to="/tickets" className="text-sm text-[#047857] hover:underline">
              ← Back to inbox
            </Link>
            <h2 className="font-display text-3xl mt-2 tracking-tight">{ticket.subject}</h2>
            <p className="text-[var(--color-ink-muted)] mt-1">
              {ticket.customer_name} · {ticket.customer_email} · {ticket.company || 'No company'}
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              <Badge className={statusColor[ticket.status]}>{ticket.status}</Badge>
              <Badge className={priorityColor[ticket.priority]}>{ticket.priority}</Badge>
              <Badge className={sentimentColor[ticket.sentiment]}>{ticket.sentiment}</Badge>
              {ticket.escalation_recommendation ? <Badge tone="warn">Escalate</Badge> : null}
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button onClick={runAnalysis} disabled={busy}>
              Run AI analysis
            </Button>
            <Button variant="secondary" onClick={checkEscalation} disabled={busy}>
              Check escalation
            </Button>
            <Button variant="danger" onClick={() => setConfirmDelete(true)}>
              Delete
            </Button>
          </div>
        </div>
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.45fr_0.95fr]">
        <div className="space-y-4">
          <div className="panel p-5">
            <h3 className="font-semibold">Customer message</h3>
            <p className="mt-3 prose-reply text-sm">{ticket.message}</p>
            <div className="mt-4 grid gap-3 sm:grid-cols-3">
              <Select label="Status" value={ticket.status} options={STATUSES} onChange={(e) => updateTicket({ status: e.target.value })} />
              <Select label="Priority" value={ticket.priority} options={PRIORITIES} onChange={(e) => updateTicket({ priority: e.target.value })} />
              <Select
                label="Assign agent"
                value={ticket.assigned_agent_id || ''}
                options={[
                  { value: '', label: 'Unassigned' },
                  { value: '1', label: 'Alex Morgan' },
                ]}
                onChange={(e) => updateTicket({ assigned_agent_id: e.target.value ? Number(e.target.value) : null })}
              />
            </div>
            <div className="mt-4 grid gap-2 text-xs text-[var(--color-ink-muted)] sm:grid-cols-2">
              <p>Created: {formatDate(ticket.created_at)}</p>
              <p>Updated: {formatDate(ticket.updated_at)}</p>
              <p>First response: {formatMinutes(ticket.first_response_time_minutes)}</p>
              <p>Resolution: {formatMinutes(ticket.resolution_time_minutes)}</p>
            </div>
          </div>

          {replies.length > 1 ? (
            <div className="panel p-4">
              <h3 className="font-semibold mb-2">Reply versions</h3>
              <div className="flex flex-wrap gap-2">
                {replies.map((r) => (
                  <button
                    key={r.id}
                    type="button"
                    onClick={() => applyReply(r)}
                    className={`rounded-xl border px-3 py-1.5 text-xs font-medium ${
                      activeReplyId === r.id ? 'border-[var(--color-accent)] bg-[var(--color-accent-soft)] text-[#047857]' : 'border-[var(--color-line)]'
                    }`}
                  >
                    #{r.id} · {r.tone} · {r.status}
                  </button>
                ))}
              </div>
            </div>
          ) : null}

          <ReplyEditor
            value={replyText}
            tone={tone}
            status={replyStatus}
            onChange={setReplyText}
            onToneChange={setTone}
            onGenerate={generateReply}
            onRegenerate={generateReply}
            onSaveDraft={saveDraft}
            onApprove={approveReply}
            onMarkSent={markSent}
            loading={busy}
            insufficientContext={insufficientContext}
          />

          <div className="panel p-5 space-y-3">
            <h3 className="font-semibold">RAG citations</h3>
            {citations?.length ? (
              citations.map((c, i) => <CitationCard key={c.chunk_id || i} citation={c} index={i + 1} />)
            ) : (
              <p className="text-sm text-[var(--color-ink-muted)]">
                No citations yet. Generate a reply after knowledge base documents are indexed.
              </p>
            )}
          </div>
        </div>

        <div className="space-y-4 xl:sticky xl:top-20 self-start">
          <div className="panel p-5">
            <h3 className="font-semibold">AI analysis</h3>
            {analysis ? (
              <div className="mt-3 space-y-3 text-sm">
                <p className="leading-relaxed">{analysis.summary}</p>
                <div className="grid gap-2">
                  <p><span className="text-[var(--color-ink-muted)]">Intent:</span> {analysis.customer_intent}</p>
                  <p><span className="text-[var(--color-ink-muted)]">Key issue:</span> {analysis.key_issue}</p>
                  <p><span className="text-[var(--color-ink-muted)]">Risk:</span> {analysis.risk_level}</p>
                  {priorityReason ? (
                    <p><span className="text-[var(--color-ink-muted)]">Priority reason:</span> {priorityReason}</p>
                  ) : null}
                  <p><span className="text-[var(--color-ink-muted)]">Next action:</span> {analysis.suggested_next_action}</p>
                  <div>
                    <p className="text-[var(--color-ink-muted)] mb-1">Confidence</p>
                    <div className="h-2 rounded-full bg-slate-100 overflow-hidden">
                      <div
                        className="h-full bg-[var(--color-accent)]"
                        style={{ width: `${Math.round((analysis.confidence || 0) * 100)}%` }}
                      />
                    </div>
                    <p className="text-xs mt-1">{Math.round((analysis.confidence || 0) * 100)}%</p>
                  </div>
                  <p>
                    <span className="text-[var(--color-ink-muted)]">Escalate:</span>{' '}
                    {analysis.escalate ? 'Yes' : 'No'} — {analysis.escalation_reason}
                  </p>
                </div>
              </div>
            ) : (
              <p className="mt-3 text-sm text-[var(--color-ink-muted)]">
                No analysis yet. Run AI analysis to populate summary, sentiment, priority, and next action.
              </p>
            )}
          </div>

          <div className="panel p-5">
            <h3 className="font-semibold mb-3">Timeline</h3>
            <TicketTimeline ticket={ticket} analysis={analysis} replies={replies} escalations={escalations} />
          </div>
        </div>
      </div>

      <Modal
        open={confirmDelete}
        onClose={() => setConfirmDelete(false)}
        title="Delete ticket?"
        footer={
          <>
            <Button variant="secondary" onClick={() => setConfirmDelete(false)}>
              Cancel
            </Button>
            <Button variant="danger" onClick={removeTicket}>
              Delete
            </Button>
          </>
        }
      >
        <p className="text-sm text-[var(--color-ink-muted)]">
          This permanently removes the ticket, analyses, replies, and escalations.
        </p>
      </Modal>
    </div>
  )
}
