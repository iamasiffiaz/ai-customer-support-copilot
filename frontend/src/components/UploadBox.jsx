export default function UploadBox({ onFile, accept = '.pdf,.txt,.docx,.md', label = 'Upload document' }) {
  return (
    <label className="flex cursor-pointer flex-col items-center justify-center rounded-[var(--radius)] border border-dashed border-[var(--emerald)]/45 bg-[var(--emerald-soft)]/40 px-6 py-10 text-center hover:bg-[var(--emerald-soft)] transition">
      <div className="mb-2 flex h-10 w-10 items-center justify-center rounded-xl bg-white border border-emerald-200 text-[var(--emerald-strong)] font-bold">
        ↑
      </div>
      <p className="font-semibold text-[var(--ink)]">{label}</p>
      <p className="mt-1 text-sm text-[var(--muted)]">PDF, TXT, DOCX, or MD — indexed for RAG</p>
      <input
        type="file"
        className="hidden"
        accept={accept}
        onChange={(e) => {
          const file = e.target.files?.[0]
          if (file) onFile(file)
          e.target.value = ''
        }}
      />
    </label>
  )
}
