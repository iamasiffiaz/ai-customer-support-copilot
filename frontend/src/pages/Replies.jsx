import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import toast from 'react-hot-toast'
import { repliesApi } from '../api/client'
import Table from '../components/Table.jsx'
import Badge from '../components/Badge.jsx'
import Button from '../components/Button.jsx'
import LoadingSpinner from '../components/LoadingSpinner.jsx'
import { formatDate } from '../utils/formatDate'

export default function Replies() {
  const [replies, setReplies] = useState([])
  const [loading, setLoading] = useState(true)

  const load = async () => {
    setLoading(true)
    try {
      setReplies(await repliesApi.list())
    } catch {
      toast.error('Failed to load replies')
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
        <h2 className="font-display text-3xl">AI reply workflow</h2>
        <p className="text-[var(--color-ink-muted)] mt-1">
          Track drafts through approval: drafted → edited → approved → sent.
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
              { key: 'tone', label: 'Tone' },
              {
                key: 'status',
                label: 'Status',
                render: (row) => <Badge className="bg-slate-100 text-slate-700">{row.status}</Badge>,
              },
              {
                key: 'content',
                label: 'Preview',
                render: (row) => <p className="max-w-md line-clamp-2 text-[var(--color-ink-muted)]">{row.content}</p>,
              },
              {
                key: 'created_at',
                label: 'Created',
                render: (row) => formatDate(row.created_at),
              },
              {
                key: 'actions',
                label: 'Actions',
                render: (row) => (
                  <div className="flex gap-2">
                    <Button
                      variant="secondary"
                      onClick={async () => {
                        await repliesApi.approve(row.id)
                        toast.success('Approved')
                        load()
                      }}
                    >
                      Approve
                    </Button>
                    <Button
                      onClick={async () => {
                        await repliesApi.markSent(row.id)
                        toast.success('Marked sent')
                        load()
                      }}
                    >
                      Mark sent
                    </Button>
                  </div>
                ),
              },
            ]}
            rows={replies}
          />
        )}
      </div>
    </div>
  )
}
