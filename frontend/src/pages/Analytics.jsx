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
} from 'recharts'
import toast from 'react-hot-toast'
import { analyticsApi } from '../api/client'
import StatCard from '../components/StatCard.jsx'
import ChartCard from '../components/ChartCard.jsx'
import Table from '../components/Table.jsx'
import Badge from '../components/Badge.jsx'
import LoadingSpinner from '../components/LoadingSpinner.jsx'
import { formatDate, formatMinutes } from '../utils/formatDate'
import { priorityColor, CHART_COLORS } from '../utils/constants'

const COLORS = [
  CHART_COLORS.accent,
  CHART_COLORS.navy,
  CHART_COLORS.warn,
  CHART_COLORS.danger,
  CHART_COLORS.muted,
  CHART_COLORS.slate,
]

export default function Analytics() {
  const [data, setData] = useState(null)
  const [response, setResponse] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([analyticsApi.tickets(), analyticsApi.responseTimes()])
      .then(([tickets, times]) => {
        setData(tickets)
        setResponse(times)
      })
      .catch(() => toast.error('Failed to load analytics'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <LoadingSpinner label="Loading analytics…" />
  if (!data) return null

  const toChart = (obj) => Object.entries(obj || {}).map(([name, value]) => ({ name, value }))

  return (
    <div className="space-y-5">
      <div>
        <h2 className="font-display text-3xl">Support analytics</h2>
        <p className="text-[var(--color-ink-muted)] mt-1">Volume, sentiment, escalation, and SLA response metrics.</p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Escalation rate" value={`${Math.round((data.escalation_rate || 0) * 100)}%`} />
        <StatCard label="Resolution rate" value={`${Math.round((data.resolution_rate || 0) * 100)}%`} tone="success" />
        <StatCard label="AI approval rate" value={`${Math.round((data.ai_approval_rate || 0) * 100)}%`} tone="accent" />
        <StatCard label="Avg first response" value={formatMinutes(response?.average_first_response_minutes)} />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <ChartCard title="Tickets by status">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={toChart(data.status_breakdown)}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
              <XAxis dataKey="name" />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="value" fill={CHART_COLORS.accent} radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
        <ChartCard title="Tickets by category">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie data={toChart(data.category_breakdown)} dataKey="value" nameKey="name" outerRadius={90}>
                {toChart(data.category_breakdown).map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </ChartCard>
        <ChartCard title="Tickets by priority">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={toChart(data.priority_breakdown)}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
              <XAxis dataKey="name" />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="value" fill={CHART_COLORS.navy} radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
        <ChartCard title="Tickets by sentiment">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={toChart(data.sentiment_breakdown)}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
              <XAxis dataKey="name" />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="value" fill={CHART_COLORS.warn} radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-2xl border border-[var(--color-line)] bg-white p-4">
          <h3 className="font-semibold mb-3">Top recurring issues</h3>
          <ul className="space-y-2">
            {(data.top_recurring_issues || []).map((item) => (
              <li key={item.issue} className="flex justify-between text-sm border-b border-[var(--color-line)] py-2">
                <span className="capitalize">{item.issue}</span>
                <span className="font-medium">{item.count}</span>
              </li>
            ))}
          </ul>
        </div>
        <div className="rounded-2xl border border-[var(--color-line)] bg-white p-4">
          <h3 className="font-semibold mb-3">SLA by priority</h3>
          <ul className="space-y-2 text-sm">
            {Object.entries(response?.by_priority || {}).map(([priority, info]) => (
              <li key={priority} className="flex justify-between border-b border-[var(--color-line)] py-2">
                <span>
                  {priority} · SLA {info.sla_hours}h
                </span>
                <span>{formatMinutes(info.avg_first_response_minutes)}</span>
              </li>
            ))}
          </ul>
          <p className="mt-3 text-xs text-[var(--color-ink-muted)]">
            Overdue: {response?.overdue_tickets?.length || 0} · SLA risk: {response?.sla_risk_tickets?.length || 0}
          </p>
        </div>
      </div>

      <div className="rounded-2xl border border-[var(--color-line)] bg-white p-2">
        <h3 className="font-semibold px-3 pt-3">Recent urgent tickets</h3>
        <Table
          columns={[
            {
              key: 'subject',
              label: 'Subject',
              render: (row) => (
                <Link to={`/tickets/${row.id}`} className="text-[#047857] hover:underline">
                  {row.subject}
                </Link>
              ),
            },
            {
              key: 'priority',
              label: 'Priority',
              render: (row) => <Badge className={priorityColor[row.priority]}>{row.priority}</Badge>,
            },
            { key: 'customer_name', label: 'Customer' },
            {
              key: 'created_at',
              label: 'Created',
              render: (row) => formatDate(row.created_at),
            },
          ]}
          rows={data.recent_urgent_table || []}
        />
      </div>
    </div>
  )
}
