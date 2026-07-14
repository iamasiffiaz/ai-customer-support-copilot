export const STATUSES = ['New', 'Open', 'Pending', 'Resolved', 'Escalated']
export const PRIORITIES = ['Low', 'Medium', 'High', 'Urgent']
export const SENTIMENTS = ['Positive', 'Neutral', 'Negative', 'Frustrated']
export const CATEGORIES = [
  'Billing',
  'Technical Issue',
  'Account',
  'Feature Request',
  'Bug Report',
  'General Question',
]
export const REPLY_TONES = [
  'Professional',
  'Friendly',
  'Empathetic',
  'Concise',
  'Technical',
  'Apologetic',
]
export const TEAMS = ['Billing', 'Technical', 'Manager', 'Security', 'Product']

export const NAV_ITEMS = [
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/tickets', label: 'Ticket Inbox' },
  { to: '/replies', label: 'AI Replies' },
  { to: '/escalations', label: 'Escalations' },
  { to: '/knowledge-base', label: 'Knowledge Base' },
  { to: '/copilot', label: 'Support Copilot' },
  { to: '/analytics', label: 'Analytics' },
  { to: '/recommendations', label: 'AI Recommendations' },
  { to: '/settings', label: 'Settings' },
]

export const priorityColor = {
  Low: 'badge border bg-slate-50 text-slate-700 border-slate-200',
  Medium: 'badge border bg-slate-100 text-[var(--slate)] border-slate-200',
  High: 'badge border bg-amber-50 text-amber-800 border-amber-200',
  Urgent: 'badge border bg-red-50 text-red-700 border-red-200',
}

export const sentimentColor = {
  Positive: 'badge border bg-emerald-50 text-emerald-800 border-emerald-200',
  Neutral: 'badge border bg-slate-100 text-slate-700 border-slate-200',
  Negative: 'badge border bg-amber-50 text-amber-800 border-amber-200',
  Frustrated: 'badge border bg-red-50 text-red-700 border-red-200',
}

export const statusColor = {
  New: 'badge border bg-slate-100 text-[var(--slate)] border-slate-200',
  Open: 'badge border bg-emerald-50 text-emerald-800 border-emerald-200',
  Pending: 'badge border bg-amber-50 text-amber-800 border-amber-200',
  Resolved: 'badge border bg-emerald-50 text-[#15803d] border-emerald-200',
  Escalated: 'badge border bg-red-50 text-red-700 border-red-200',
}

export const CHART_COLORS = {
  accent: '#10B981',
  navy: '#0F172A',
  slate: '#334155',
  muted: '#64748B',
  warn: '#F59E0B',
  danger: '#EF4444',
  success: '#22C55E',
  line: '#E2E8F0',
}
