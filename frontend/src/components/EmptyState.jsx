import Button from './Button.jsx'

export default function EmptyState({ title, description, actionLabel, onAction }) {
  return (
    <div className="rounded-[var(--radius)] border border-dashed border-[var(--border)] bg-white px-6 py-14 text-center">
      <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-[var(--emerald-soft)] border border-emerald-200">
        <span className="text-[var(--emerald-strong)] text-lg font-bold">?</span>
      </div>
      <h3 className="font-semibold text-[var(--ink)]">{title}</h3>
      {description ? <p className="mt-2 text-sm text-[var(--muted)] max-w-md mx-auto leading-relaxed">{description}</p> : null}
      {actionLabel && onAction ? (
        <div className="mt-5">
          <Button onClick={onAction}>{actionLabel}</Button>
        </div>
      ) : null}
    </div>
  )
}
