import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import toast from 'react-hot-toast'
import { analysisApi, ticketsApi, getErrorMessage } from '../api/client'
import Button from '../components/Button.jsx'
import Input from '../components/Input.jsx'
import Select from '../components/Select.jsx'
import Textarea from '../components/Textarea.jsx'
import Modal from '../components/Modal.jsx'
import Table from '../components/Table.jsx'
import Badge from '../components/Badge.jsx'
import LoadingSpinner from '../components/LoadingSpinner.jsx'
import EmptyState from '../components/EmptyState.jsx'
import {
  CATEGORIES,
  PRIORITIES,
  SENTIMENTS,
  STATUSES,
  priorityColor,
  sentimentColor,
  statusColor,
} from '../utils/constants'
import { formatDate } from '../utils/formatDate'

const emptyForm = {
  customer_name: '',
  customer_email: '',
  company: '',
  subject: '',
  message: '',
  category: 'General Question',
  status: 'New',
  priority: 'Medium',
  sentiment: 'Neutral',
}

export default function Tickets() {
  const [tickets, setTickets] = useState([])
  const [loading, setLoading] = useState(true)
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState(emptyForm)
  const [selected, setSelected] = useState([])
  const [busy, setBusy] = useState(false)
  const [filters, setFilters] = useState({
    q: '',
    status: '',
    priority: '',
    sentiment: '',
    category: '',
    escalated: '',
    sort_by: 'created_at',
    sort_dir: 'desc',
  })

  const load = async (nextFilters = filters) => {
    setLoading(true)
    try {
      const params = Object.fromEntries(
        Object.entries(nextFilters).filter(([, v]) => v !== '' && v !== null && v !== undefined),
      )
      if (params.escalated !== undefined && params.escalated !== '') {
        params.escalated = params.escalated === 'true'
      }
      setTickets(await ticketsApi.list(params))
      setSelected([])
    } catch (e) {
      toast.error(getErrorMessage(e, 'Failed to load tickets'))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  useEffect(() => {
    const t = setTimeout(() => {
      if (filters.q !== undefined) load()
    }, 350)
    return () => clearTimeout(t)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters.q])

  const columns = useMemo(
    () => [
      {
        key: 'select',
        label: '',
        render: (row) => (
          <input
            type="checkbox"
            checked={selected.includes(row.id)}
            onChange={(e) => {
              setSelected((prev) =>
                e.target.checked ? [...prev, row.id] : prev.filter((id) => id !== row.id),
              )
            }}
          />
        ),
      },
      {
        key: 'subject',
        label: 'Ticket',
        render: (row) => (
          <div className={row.priority === 'Urgent' || row.status === 'Escalated' ? 'pl-1' : ''}>
            <Link className="font-medium text-[#047857] hover:underline" to={`/tickets/${row.id}`}>
              {row.subject}
            </Link>
            <p className="text-xs text-[var(--color-ink-muted)] mt-0.5">
              {row.customer_name} · {row.company || '—'}
            </p>
          </div>
        ),
      },
      {
        key: 'status',
        label: 'Status',
        render: (row) => <Badge className={statusColor[row.status]}>{row.status}</Badge>,
      },
      {
        key: 'priority',
        label: 'Priority',
        render: (row) => <Badge className={priorityColor[row.priority]}>{row.priority}</Badge>,
      },
      {
        key: 'sentiment',
        label: 'Sentiment',
        render: (row) => <Badge className={sentimentColor[row.sentiment]}>{row.sentiment}</Badge>,
      },
      { key: 'category', label: 'Category' },
      {
        key: 'escalation_recommendation',
        label: 'Escalate',
        render: (row) =>
          row.escalation_recommendation ? <Badge tone="warn">Yes</Badge> : <Badge tone="muted">No</Badge>,
      },
      {
        key: 'created_at',
        label: 'Created',
        render: (row) => formatDate(row.created_at),
      },
    ],
    [selected],
  )

  const createTicket = async () => {
    if (!form.customer_name || !form.customer_email || !form.subject || !form.message) {
      toast.error('Name, email, subject, and message are required')
      return
    }
    try {
      const created = await ticketsApi.create(form)
      toast.success('Ticket created')
      setOpen(false)
      setForm(emptyForm)
      await load()
      return created
    } catch (e) {
      toast.error(getErrorMessage(e, 'Could not create ticket'))
    }
  }

  const bulkAnalyze = async () => {
    if (!selected.length) {
      toast.error('Select tickets to analyze')
      return
    }
    setBusy(true)
    try {
      const res = await analysisApi.bulk(selected)
      toast.success(res.message || 'Bulk analysis complete')
      await load()
    } catch (e) {
      toast.error(getErrorMessage(e, 'Bulk analysis failed'))
    } finally {
      setBusy(false)
    }
  }

  const clearFilters = () => {
    const cleared = {
      q: '',
      status: '',
      priority: '',
      sentiment: '',
      category: '',
      escalated: '',
      sort_by: 'created_at',
      sort_dir: 'desc',
    }
    setFilters(cleared)
    load(cleared)
  }

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="font-display text-3xl tracking-tight text-[var(--navy)]">Ticket inbox</h2>
          <p className="text-[var(--muted)] mt-1">
            Search, filter, and triage customer conversations. Urgent and escalated items are highlighted.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="secondary" onClick={bulkAnalyze} disabled={busy}>
            {busy ? 'Analyzing…' : `Bulk AI analyze${selected.length ? ` (${selected.length})` : ''}`}
          </Button>
          <Button onClick={() => setOpen(true)}>Create ticket</Button>
        </div>
      </div>

      <div className="panel p-4 grid gap-3 md:grid-cols-3 xl:grid-cols-4">
        <Input
          label="Search"
          placeholder="Name, subject, message…"
          value={filters.q}
          onChange={(e) => setFilters({ ...filters, q: e.target.value })}
        />
        <Select
          label="Status"
          value={filters.status}
          onChange={(e) => setFilters({ ...filters, status: e.target.value })}
          options={[{ value: '', label: 'All' }, ...STATUSES.map((s) => ({ value: s, label: s }))]}
        />
        <Select
          label="Priority"
          value={filters.priority}
          onChange={(e) => setFilters({ ...filters, priority: e.target.value })}
          options={[{ value: '', label: 'All' }, ...PRIORITIES.map((s) => ({ value: s, label: s }))]}
        />
        <Select
          label="Sentiment"
          value={filters.sentiment}
          onChange={(e) => setFilters({ ...filters, sentiment: e.target.value })}
          options={[{ value: '', label: 'All' }, ...SENTIMENTS.map((s) => ({ value: s, label: s }))]}
        />
        <Select
          label="Category"
          value={filters.category}
          onChange={(e) => setFilters({ ...filters, category: e.target.value })}
          options={[{ value: '', label: 'All' }, ...CATEGORIES.map((s) => ({ value: s, label: s }))]}
        />
        <Select
          label="Escalation"
          value={filters.escalated}
          onChange={(e) => setFilters({ ...filters, escalated: e.target.value })}
          options={[
            { value: '', label: 'All' },
            { value: 'true', label: 'Recommended' },
            { value: 'false', label: 'Not recommended' },
          ]}
        />
        <Select
          label="Sort by"
          value={filters.sort_by}
          onChange={(e) => setFilters({ ...filters, sort_by: e.target.value })}
          options={[
            { value: 'created_at', label: 'Created date' },
            { value: 'priority', label: 'Priority' },
            { value: 'sentiment', label: 'Sentiment' },
          ]}
        />
        <Select
          label="Direction"
          value={filters.sort_dir}
          onChange={(e) => setFilters({ ...filters, sort_dir: e.target.value })}
          options={[
            { value: 'desc', label: 'Descending' },
            { value: 'asc', label: 'Ascending' },
          ]}
        />
        <div className="flex items-end gap-2 xl:col-span-2">
          <Button className="flex-1" onClick={() => load()}>
            Apply filters
          </Button>
          <Button variant="ghost" onClick={clearFilters}>
            Clear
          </Button>
        </div>
      </div>

      <div className="panel p-4">
        {loading ? (
          <LoadingSpinner />
        ) : tickets.length ? (
          <Table
            columns={columns}
            rows={tickets.map((t) => ({
              ...t,
              _rowClass:
                t.priority === 'Urgent'
                  ? 'ticket-urgent'
                  : t.status === 'Escalated'
                    ? 'ticket-escalated'
                    : '',
            }))}
          />
        ) : (
          <EmptyState
            title="No tickets found"
            description="Adjust filters or create a new support ticket."
            actionLabel="Create ticket"
            onAction={() => setOpen(true)}
          />
        )}
      </div>

      <Modal
        open={open}
        onClose={() => setOpen(false)}
        title="Create support ticket"
        footer={
          <>
            <Button variant="secondary" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button onClick={createTicket}>Create</Button>
          </>
        }
      >
        <Input label="Customer name" value={form.customer_name} onChange={(e) => setForm({ ...form, customer_name: e.target.value })} />
        <Input label="Customer email" value={form.customer_email} onChange={(e) => setForm({ ...form, customer_email: e.target.value })} />
        <Input label="Company" value={form.company} onChange={(e) => setForm({ ...form, company: e.target.value })} />
        <Input label="Subject" value={form.subject} onChange={(e) => setForm({ ...form, subject: e.target.value })} />
        <Textarea label="Message" value={form.message} onChange={(e) => setForm({ ...form, message: e.target.value })} />
        <Select label="Category" value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} options={CATEGORIES} />
      </Modal>
    </div>
  )
}
