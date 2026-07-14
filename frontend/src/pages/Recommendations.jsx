import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { recommendationsApi } from '../api/client'
import Button from '../components/Button.jsx'
import Badge from '../components/Badge.jsx'
import LoadingSpinner from '../components/LoadingSpinner.jsx'
import EmptyState from '../components/EmptyState.jsx'
import { priorityColor } from '../utils/constants'

export default function Recommendations() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)

  const load = async () => {
    setLoading(true)
    try {
      setItems(await recommendationsApi.list())
    } catch {
      toast.error('Failed to load recommendations')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const generate = async () => {
    setGenerating(true)
    try {
      setItems(await recommendationsApi.generate())
      toast.success('Recommendations generated')
    } catch {
      toast.error('Generation failed')
    } finally {
      setGenerating(false)
    }
  }

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="font-display text-3xl">AI recommendations</h2>
          <p className="text-[var(--color-ink-muted)] mt-1">
            Operational guidance for urgency, retention risk, recurring issues, and KB gaps.
          </p>
        </div>
        <Button onClick={generate} disabled={generating}>
          {generating ? 'Generating…' : 'Generate recommendations'}
        </Button>
      </div>

      {loading ? (
        <LoadingSpinner />
      ) : !items.length ? (
        <EmptyState
          title="No recommendations yet"
          description="Generate a fresh set based on current ticket volume and analytics."
          actionLabel="Generate"
          onAction={generate}
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {items.map((item) => (
            <div key={item.id} className="rounded-2xl border border-[var(--color-line)] bg-white p-5">
              <div className="flex items-start justify-between gap-3">
                <h3 className="font-semibold">{item.title}</h3>
                <Badge className={priorityColor[item.priority] || 'bg-slate-100 text-slate-700'}>
                  {item.priority}
                </Badge>
              </div>
              <p className="mt-1 text-xs uppercase tracking-wide text-[var(--color-ink-muted)]">{item.category}</p>
              <p className="mt-3 text-sm text-[var(--color-ink-muted)] leading-relaxed">{item.description}</p>
              {item.action_items?.length ? (
                <ul className="mt-4 space-y-1.5 text-sm">
                  {item.action_items.map((action) => (
                    <li key={action} className="flex gap-2">
                      <span className="mt-2 h-1.5 w-1.5 rounded-full bg-[var(--color-accent)] shrink-0" />
                      {action}
                    </li>
                  ))}
                </ul>
              ) : null}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
