export default function LoadingSpinner({ label = 'Loading…' }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-16 text-[var(--muted)]">
      <div className="spinner" />
      <p className="text-sm">{label}</p>
    </div>
  )
}
