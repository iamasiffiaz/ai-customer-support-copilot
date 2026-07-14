import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import toast from 'react-hot-toast'
import { escalationsApi } from '../api/client'
import Table from '../components/Table.jsx'
import Badge from '../components/Badge.jsx'
import Button from '../components/Button.jsx'
import LoadingSpinner from '../components/LoadingSpinner.jsx'
import { formatDate } from '../utils/formatDate'

export default function Escalations() {
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(true)

  const load = async () => {
    setLoading(true)
    try {
      setRows(await escalationsApi.list())
    } catch {
      toast.error('Failed to load escalations')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  return (
    <div className="space-y-5">
      <div>
        <h2 className="font-display text-3xl">Escalations</h2>
        <p className="text-[var(--color-ink-muted)] mt-1">
          Review recommended team routing, reasons, and internal notes for high-risk tickets.
        </p>
      </div>
      <div className="rounded-2xl border border-[var(--color-line)] bg-white p-2">
        {loading ? (
          <LoadingSpinner />
        ) : (
          <Table
            columns={[
              {
                key: 'ticket_id',
                label: 'Ticket',
                render: (row) => (
                  <Link className="text-[#047857] hover:underline" to={`/tickets/${row.ticket_id}`}>
                    #{row.ticket_id}
                  </Link>
                ),
              },
              {
                key: 'escalate',
                label: 'Escalate',
                render: (row) => (row.escalate ? 'Yes' : 'No'),
              },
              { key: 'recommended_team', label: 'Team' },
              {
                key: 'status',
                label: 'Status',
                render: (row) => (
                  <Badge className={row.status === 'open' ? 'bg-rose-100 text-rose-800' : 'bg-emerald-100 text-emerald-800'}>
                    {row.status}
                  </Badge>
                ),
              },
              {
                key: 'reason',
                label: 'Reason',
                render: (row) => <p className="max-w-sm text-[var(--color-ink-muted)]">{row.reason}</p>,
              },
              {
                key: 'created_at',
                label: 'Created',
                render: (row) => formatDate(row.created_at),
              },
              {
                key: 'actions',
                label: 'Actions',
                render: (row) =>
                  row.status !== 'resolved' ? (
                    <Button
                      variant="secondary"
                      onClick={async () => {
                        await escalationsApi.resolve(row.id)
                        toast.success('Escalation resolved')
                        load()
                      }}
                    >
                      Resolve
                    </Button>
                  ) : (
                    '—'
                  ),
              },
            ]}
            rows={rows}
          />
        )}
      </div>
    </div>
  )
}
