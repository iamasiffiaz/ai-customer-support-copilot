export default function Badge({ children, className = '', tone }) {
  const tones = {
    urgent: 'bg-red-50 text-[#b91c1c] border-red-200',
    high: 'bg-amber-50 text-[#b45309] border-amber-200',
    medium: 'bg-slate-100 text-[var(--slate)] border-slate-200',
    low: 'bg-slate-50 text-[var(--muted)] border-slate-200',
    success: 'bg-emerald-50 text-[#15803d] border-emerald-200',
    warn: 'bg-amber-50 text-[#b45309] border-amber-200',
    danger: 'bg-red-50 text-[#b91c1c] border-red-200',
    muted: 'bg-slate-100 text-[var(--muted)] border-slate-200',
    accent: 'bg-[var(--emerald-soft)] text-[#047857] border-emerald-200',
    navy: 'bg-slate-800/10 text-[var(--navy)] border-slate-300',
  }
  return (
    <span className={`badge border ${tone ? tones[tone] || tones.muted : ''} ${className}`}>
      {children}
    </span>
  )
}
