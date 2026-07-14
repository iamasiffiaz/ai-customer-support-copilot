import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Legend,
} from 'recharts'
import toast from 'react-hot-toast'
import { analyticsApi, getErrorMessage } from '../api/client'
import StatCard from '../components/StatCard.jsx'
import ChartCard from '../components/ChartCard.jsx'
import LoadingSpinner from '../components/LoadingSpinner.jsx'
import Badge from '../components/Badge.jsx'
import EmptyState from '../components/EmptyState.jsx'
import { formatDate, formatMinutes } from '../utils/formatDate'
import { CHART_COLORS, priorityColor, sentimentColor } from '../utils/constants'

const SENTIMENT_COLORS = {
  Positive: CHART_COLORS.success,
  Neutral: CHART_COLORS.muted,
  Negative: CHART_COLORS.warn,
  Frustrated: CHART_COLORS.danger,
}

const PRIORITY_BAR_COLORS = {
  Low: CHART_COLORS.muted,
  Medium: CHART_COLORS.slate,
  High: CHART_COLORS.warn,
  Urgent: CHART_COLORS.danger,
}

export default function Dashboard() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    analyticsApi
      .dashboard()
      .then(setData)
      .catch((e) => toast.error(getErrorMessage(e, 'Failed to load dashboard. Is the API running?')))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <LoadingSpinner label="Loading operations overview…" />
  if (!data) {
    return (
      <EmptyState
        title="Could not load analytics"
        description="Start the FastAPI backend and refresh this page."
      />
    )
  }

  const sentimentData = Object.entries(data.sentiment_breakdown || {}).map(([name, value]) => ({ name, value }))
  const priorityData = Object.entries(data.priority_breakdown || {}).map(([name, value]) => ({ name, value }))

  return (
    <div className="space-y-5">
      <div className="page-hero relative z-[1] flex flex-wrap items-end justify-between gap-4">
        <div className="relative z-[1]">
          <p className="eyebrow">Support operations · Enterprise Trust</p>
          <h2 className="font-display text-3xl tracking-tight text-white mt-2">Command center</h2>
          <p className="sub">Queue health, sentiment risk, and AI draft activity for your support team.</p>
        </div>
        <Link to="/tickets" className="btn btn-primary relative z-[1]">
          Open ticket inbox →
        </Link>
      </div>

      <div className="ops-strip">
        <span className="live-dot" />
        <p className="text-sm text-[var(--ink)]">
          <span className="font-semibold">{data.open_tickets + data.new_tickets}</span> active ·{' '}
          <span className="font-semibold text-[var(--danger)]">{data.escalated_tickets}</span> escalated ·{' '}
          <span className="font-semibold text-[var(--emerald-strong)]">{data.resolved_tickets}</span> resolved
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Total tickets" value={data.total_tickets} tone="navy" />
        <StatCard label="Open" value={data.open_tickets} tone="accent" />
        <StatCard label="Pending" value={data.pending_tickets} tone="warn" />
        <StatCard label="Resolved" value={data.resolved_tickets} tone="success" />
        <StatCard label="Escalated" value={data.escalated_tickets} tone="urgent" hint="Route to specialists" />
        <StatCard label="Avg first response" value={formatMinutes(data.average_response_time_minutes)} tone="navy" />
        <StatCard label="Customer satisfaction" value={`${data.customer_satisfaction}/5`} hint="Demo metric" tone="accent" />
        <StatCard label="SLA risk" value={data.sla_risk_tickets} hint={`${data.overdue_tickets} overdue`} tone="urgent" />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <ChartCard title="Sentiment risk map">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie data={sentimentData} dataKey="value" nameKey="name" innerRadius={52} outerRadius={88} paddingAngle={2}>
                {sentimentData.map((entry) => (
                  <Cell key={entry.name} fill={SENTIMENT_COLORS[entry.name] || CHART_COLORS.muted} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </ChartCard>
        <ChartCard title="Priority distribution">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={priorityData}>
              <CartesianGrid strokeDasharray="3 3" stroke={CHART_COLORS.line} />
              <XAxis dataKey="name" stroke={CHART_COLORS.muted} />
              <YAxis allowDecimals={false} stroke={CHART_COLORS.muted} />
              <Tooltip />
              <Bar dataKey="value" radius={[8, 8, 0, 0]}>
                {priorityData.map((entry) => (
                  <Cell key={entry.name} fill={PRIORITY_BAR_COLORS[entry.name] || CHART_COLORS.accent} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="panel overflow-hidden">
          <div className="panel-header">
            <h3>
              <span className="inline-block h-2 w-2 rounded-full bg-[var(--danger)] mr-2 align-middle" />
              Urgent queue
            </h3>
          </div>
          <div className="panel-body space-y-3">
            {(data.recent_urgent || []).length ? (
              data.recent_urgent.map((t) => (
                <Link
                  key={t.id}
                  to={`/tickets/${t.id}`}
                  className="block rounded-[var(--radius)] border border-red-200 ticket-urgent p-3 hover:border-red-400 transition"
                >
                  <div className="flex items-center justify-between gap-2">
                    <p className="font-medium text-sm text-[var(--ink)]">{t.subject}</p>
                    <span className={priorityColor[t.priority]}>{t.priority}</span>
                  </div>
                  <div className="mt-2 flex flex-wrap gap-2">
                    <span className={sentimentColor[t.sentiment]}>{t.sentiment}</span>
                    {t.escalation_recommendation ? <Badge tone="warn">Escalate</Badge> : null}
                  </div>
                  <p className="text-xs text-[var(--muted)] mt-2">
                    {t.customer_name} · {formatDate(t.created_at)}
                  </p>
                </Link>
              ))
            ) : (
              <p className="text-sm text-[var(--muted)]">No urgent tickets right now.</p>
            )}
          </div>
        </div>

        <div className="panel overflow-hidden">
          <div className="panel-header">
            <h3>
              <span className="inline-block h-2 w-2 rounded-full bg-[var(--emerald)] mr-2 align-middle" />
              AI drafts awaiting review
            </h3>
          </div>
          <div className="panel-body space-y-3">
            {(data.recent_replies || []).length ? (
              data.recent_replies.map((r) => (
                <Link
                  key={r.id}
                  to={`/tickets/${r.ticket_id}`}
                  className="block rounded-[var(--radius)] border border-emerald-200 bg-[var(--emerald-soft)]/35 p-3 hover:border-[var(--emerald)] transition"
                >
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-sm font-medium text-[var(--ink)]">Ticket #{r.ticket_id}</p>
                    <Badge tone="accent">{r.status}</Badge>
                  </div>
                  <p className="mt-1 text-xs text-[var(--muted)] line-clamp-2">{r.content}</p>
                </Link>
              ))
            ) : (
              <EmptyState title="No AI drafts yet" description="Open a ticket and generate a reply to populate this feed." />
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
