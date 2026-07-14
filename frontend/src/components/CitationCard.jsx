export default function CitationCard({ citation, index }) {
  const score = citation.score != null ? Number(citation.score).toFixed(2) : null
  return (
    <div className="rounded-[var(--radius)] border border-[var(--border)] bg-[var(--surface)] p-3.5">
      <div className="flex items-center justify-between gap-2">
        <p className="text-sm font-semibold text-[var(--ink)]">
          <span className="inline-flex h-5 min-w-5 items-center justify-center rounded-md bg-[var(--navy)] text-[10px] text-emerald-300 px-1 mr-1.5">
            {index || '•'}
          </span>
          {citation.document_title || 'Knowledge Base'}
        </p>
        {score ? <span className="text-[11px] font-medium text-[var(--muted)]">score {score}</span> : null}
      </div>
      <p className="mt-2 text-sm text-[var(--muted)] leading-relaxed">{citation.content || citation.snippet}</p>
    </div>
  )
}
