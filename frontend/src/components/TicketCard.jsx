import { Link } from 'react-router-dom'
import Badge from './Badge.jsx'
import { formatDate } from '../utils/formatDate'
import { priorityColor, sentimentColor, statusColor } from '../utils/constants'

export default function TicketCard({ ticket }) {
  return (
    <Link
      to={`/tickets/${ticket.id}`}
      className={`block rounded-2xl border bg-white p-4 hover:border-[var(--color-accent)]/40 transition ${
        ticket.priority === 'Urgent' || ticket.status === 'Escalated'
          ? 'border-rose-200 shadow-[inset_3px_0_0_0_#e11d48]'
          : 'border-[var(--color-line)]'
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="font-medium text-[var(--color-ink)]">{ticket.subject}</p>
          <p className="mt-1 text-sm text-[var(--color-ink-muted)]">
            {ticket.customer_name} · {ticket.company || '—'}
          </p>
        </div>
        <p className="text-xs text-[var(--color-ink-muted)] whitespace-nowrap">{formatDate(ticket.created_at)}</p>
      </div>
      <div className="mt-3 flex flex-wrap gap-2">
        <Badge className={statusColor[ticket.status]}>{ticket.status}</Badge>
        <Badge className={priorityColor[ticket.priority]}>{ticket.priority}</Badge>
        <Badge className={sentimentColor[ticket.sentiment]}>{ticket.sentiment}</Badge>
      </div>
    </Link>
  )
}
