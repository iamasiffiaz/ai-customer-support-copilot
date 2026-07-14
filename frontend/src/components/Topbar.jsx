import { useState } from 'react'
import { Link, NavLink, useLocation } from 'react-router-dom'
import { NAV_ITEMS } from '../utils/constants'

export default function Topbar() {
  const location = useLocation()
  const [open, setOpen] = useState(false)
  const current = NAV_ITEMS.find((n) => location.pathname.startsWith(n.to))?.label || 'Workspace'

  return (
    <header className="sticky top-0 z-20 border-b border-[var(--border)] bg-white/95 backdrop-blur px-4 py-3 md:px-6">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-[0.65rem] uppercase tracking-[0.16em] font-semibold text-[var(--muted)]">
            Support workspace
          </p>
          <h1 className="text-lg font-semibold text-[var(--ink)] tracking-tight">{current}</h1>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            className="md:hidden btn btn-secondary !py-1.5"
            onClick={() => setOpen((v) => !v)}
          >
            Menu
          </button>
          <Link to="/" className="hidden sm:inline-flex text-sm text-[var(--muted)] hover:text-[var(--emerald-strong)]">
            Product site
          </Link>
          <div className="hidden sm:flex items-center gap-2 rounded-full border border-[var(--border)] bg-[var(--surface)] pl-1 pr-3 py-1">
            <span className="flex h-7 w-7 items-center justify-center rounded-full bg-[var(--navy)] text-[10px] font-bold text-emerald-300">
              AG
            </span>
            <span className="text-sm font-medium text-[var(--ink)]">Demo Agent</span>
          </div>
        </div>
      </div>
      {open ? (
        <nav className="md:hidden mt-3 grid gap-1 border-t border-[var(--border)] pt-3">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={() => setOpen(false)}
              className={({ isActive }) =>
                `rounded-lg px-3 py-2 text-sm ${
                  isActive ? 'bg-[var(--emerald-soft)] text-[#047857] font-semibold' : 'text-[var(--muted)]'
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      ) : null}
    </header>
  )
}
