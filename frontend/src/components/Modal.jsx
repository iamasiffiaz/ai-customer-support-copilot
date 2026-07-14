import Button from './Button.jsx'

export default function Modal({ open, title, children, onClose, footer }) {
  if (!open) return null
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-[var(--navy)]/45 backdrop-blur-[2px]" onClick={onClose} />
      <div className="relative w-full max-w-lg rounded-[var(--radius)] bg-white border border-[var(--border)] shadow-2xl">
        <div className="flex items-center justify-between border-b border-[var(--border)] px-5 py-4 bg-[var(--surface)]">
          <h3 className="font-semibold text-[var(--ink)]">{title}</h3>
          <Button variant="ghost" onClick={onClose}>
            Close
          </Button>
        </div>
        <div className="px-5 py-4 space-y-3">{children}</div>
        {footer ? (
          <div className="border-t border-[var(--border)] bg-[var(--surface)] px-5 py-4 flex justify-end gap-2">
            {footer}
          </div>
        ) : null}
      </div>
    </div>
  )
}
