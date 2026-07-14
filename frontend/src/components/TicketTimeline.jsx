import { formatDate } from '../utils/formatDate'

export default function TicketTimeline({ ticket, analysis, replies = [], escalations = [] }) {
  const events = [
    { label: 'Ticket created', at: ticket?.created_at, detail: ticket?.subject },
    analysis
      ? {
          label: 'AI analysis completed',
          at: analysis.updated_at || analysis.created_at,
          detail: `${analysis.priority} · ${analysis.sentiment}`,
        }
      : null,
    ...replies.map((r) => ({
      label: `Reply ${r.status}`,
      at: r.updated_at || r.created_at,
      detail: `${r.tone} tone`,
    })),
    ...escalations.map((e) => ({
      label: `Escalation ${e.status}`,
      at: e.created_at,
      detail: e.recommended_team,
    })),
    ticket?.first_response_at
      ? { label: 'First response', at: ticket.first_response_at, detail: null }
      : null,
    ticket?.resolved_at ? { label: 'Resolved', at: ticket.resolved_at, detail: null } : null,
  ]
    .filter(Boolean)
    .sort((a, b) => new Date(a.at) - new Date(b.at))

  return (
    <ol className="space-y-3">
      {events.map((ev, i) => (
        <li key={`${ev.label}-${i}`} className="flex gap-3">
          <div className="mt-1 h-2.5 w-2.5 rounded-full bg-[var(--emerald)] shrink-0" />
          <div>
            <p className="text-sm font-medium text-[var(--ink)]">{ev.label}</p>
            <p className="text-xs text-[var(--muted)]">{formatDate(ev.at)}</p>
            {ev.detail ? <p className="text-xs text-[var(--muted)] mt-0.5">{ev.detail}</p> : null}
          </div>
        </li>
      ))}
    </ol>
  )
}
