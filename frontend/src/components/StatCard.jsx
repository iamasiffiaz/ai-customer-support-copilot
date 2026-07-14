export default function StatCard({ label, value, hint, tone = 'default' }) {
  const toneClass = {
    default: '',
    accent: 'tone-accent',
    success: 'tone-success',
    urgent: 'tone-urgent',
    navy: 'tone-navy',
    warn: 'tone-warn',
  }[tone] || ''

  return (
    <div className={`stat-card ${toneClass}`}>
      <p className="text-[0.7rem] uppercase tracking-[0.08em] font-semibold text-[var(--muted)] pl-1">{label}</p>
      <p className="mt-1.5 text-[1.65rem] font-semibold tracking-tight text-[var(--ink)] pl-1">{value}</p>
      {hint ? <p className="mt-1 text-xs text-[var(--muted)] pl-1">{hint}</p> : null}
    </div>
  )
}
