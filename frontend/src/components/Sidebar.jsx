import { NavLink } from 'react-router-dom'
import { NAV_ITEMS } from '../utils/constants'

const ICONS = {
  '/dashboard': '◉',
  '/tickets': '☰',
  '/replies': '✎',
  '/escalations': '▲',
  '/knowledge-base': '▤',
  '/copilot': '◎',
  '/analytics': '▦',
  '/recommendations': '✦',
  '/settings': '⚙',
}

export default function Sidebar() {
  return (
    <aside className="hidden md:flex flex-col bg-[var(--navy)] text-white min-h-screen border-r border-slate-800">
      <div className="px-4 py-5 border-b border-white/10 flex items-center gap-3">
        <div className="brand-mark">SC</div>
        <div>
          <p className="font-display text-lg leading-none tracking-tight">Support Copilot</p>
          <p className="mt-1.5 text-[11px] text-slate-400 uppercase tracking-[0.12em]">Agent operations</p>
        </div>
      </div>

      <div className="px-4 pt-4 pb-2">
        <div className="ops-strip !bg-white/5 !border-white/10 !shadow-none">
          <span className="live-dot" />
          <div>
            <p className="text-[11px] font-semibold text-emerald-300 uppercase tracking-wide">Queue live</p>
            <p className="text-[11px] text-slate-400">AI assist · human approval</p>
          </div>
        </div>
      </div>

      <nav className="flex-1 p-3 space-y-0.5" aria-label="Primary">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
          >
            <span className="nav-ico" aria-hidden>
              {ICONS[item.to] || '•'}
            </span>
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="p-4 border-t border-white/10 text-[11px] text-slate-500 leading-relaxed">
        Built for support teams — resolve faster without losing control of the reply.
      </div>
    </aside>
  )
}
