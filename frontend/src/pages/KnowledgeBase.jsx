import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { kbApi, getErrorMessage } from '../api/client'
import Button from '../components/Button.jsx'
import Input from '../components/Input.jsx'
import Select from '../components/Select.jsx'
import UploadBox from '../components/UploadBox.jsx'
import CitationCard from '../components/CitationCard.jsx'
import Table from '../components/Table.jsx'
import Badge from '../components/Badge.jsx'
import LoadingSpinner from '../components/LoadingSpinner.jsx'
import EmptyState from '../components/EmptyState.jsx'
import Modal from '../components/Modal.jsx'
import { formatDate } from '../utils/formatDate'

export default function KnowledgeBase() {
  const [docs, setDocs] = useState([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [searching, setSearching] = useState(false)
  const [title, setTitle] = useState('')
  const [query, setQuery] = useState('How do we handle refund requests?')
  const [topK, setTopK] = useState(5)
  const [results, setResults] = useState([])
  const [selected, setSelected] = useState(null)
  const [deleteId, setDeleteId] = useState(null)

  const load = async () => {
    setLoading(true)
    try {
      setDocs(await kbApi.documents())
    } catch (e) {
      toast.error(getErrorMessage(e, 'Failed to load knowledge base'))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const upload = async (file) => {
    setUploading(true)
    try {
      await kbApi.upload(file, title || undefined)
      toast.success('Document uploaded and indexed')
      setTitle('')
      load()
    } catch (e) {
      toast.error(getErrorMessage(e, 'Upload failed'))
    } finally {
      setUploading(false)
    }
  }

  const search = async () => {
    setSearching(true)
    try {
      setResults(await kbApi.search(query, Number(topK) || 5))
    } catch (e) {
      toast.error(getErrorMessage(e, 'Search failed'))
    } finally {
      setSearching(false)
    }
  }

  const viewDoc = async (id) => {
    try {
      setSelected(await kbApi.get(id))
    } catch (e) {
      toast.error(getErrorMessage(e, 'Could not open document'))
    }
  }

  const remove = async () => {
    try {
      await kbApi.remove(deleteId)
      toast.success('Document deleted')
      if (selected?.id === deleteId) setSelected(null)
      setDeleteId(null)
      load()
    } catch (e) {
      toast.error(getErrorMessage(e, 'Delete failed'))
    }
  }

  return (
    <div className="space-y-5">
      <div>
        <h2 className="font-display text-3xl tracking-tight">Knowledge base</h2>
        <p className="text-[var(--color-ink-muted)] mt-1">
          Upload support policies, chunk + embed them, and retrieve ranked citations for RAG replies.
        </p>
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.15fr_0.85fr]">
        <div className="space-y-4">
          <div className="panel p-5 space-y-3">
            <h3 className="font-semibold">Upload document</h3>
            <Input label="Title (optional)" value={title} onChange={(e) => setTitle(e.target.value)} />
            <UploadBox onFile={upload} label={uploading ? 'Uploading…' : 'Upload PDF, TXT, DOCX, or MD'} />
          </div>

          <div className="panel p-5">
            <h3 className="font-semibold mb-3">Documents</h3>
            {loading ? (
              <LoadingSpinner />
            ) : docs.length ? (
              <Table
                columns={[
                  { key: 'title', label: 'Title' },
                  { key: 'file_type', label: 'Type' },
                  { key: 'chunk_count', label: 'Chunks' },
                  {
                    key: 'status',
                    label: 'Status',
                    render: (row) => <Badge tone="accent">{row.status}</Badge>,
                  },
                  {
                    key: 'created_at',
                    label: 'Created',
                    render: (row) => formatDate(row.created_at),
                  },
                  {
                    key: 'actions',
                    label: 'Actions',
                    render: (row) => (
                      <div className="flex gap-2">
                        <Button variant="secondary" onClick={() => viewDoc(row.id)}>
                          View
                        </Button>
                        <Button variant="danger" onClick={() => setDeleteId(row.id)}>
                          Delete
                        </Button>
                      </div>
                    ),
                  },
                ]}
                rows={docs}
              />
            ) : (
              <EmptyState
                title="No documents yet"
                description="Upload a refund, payment, or login policy to power RAG citations."
              />
            )}
          </div>
        </div>

        <div className="space-y-4">
          <div className="panel p-5 space-y-3">
            <h3 className="font-semibold">Semantic search</h3>
            <Input label="Query" value={query} onChange={(e) => setQuery(e.target.value)} />
            <Select
              label="Top-k results"
              value={String(topK)}
              onChange={(e) => setTopK(Number(e.target.value))}
              options={[
                { value: '3', label: '3' },
                { value: '5', label: '5' },
                { value: '8', label: '8' },
                { value: '10', label: '10' },
              ]}
            />
            <Button onClick={search} disabled={searching}>
              {searching ? 'Searching…' : 'Search knowledge base'}
            </Button>
            <div className="space-y-2 max-h-[28rem] overflow-auto">
              {!searching && !results.length ? (
                <p className="text-sm text-[var(--color-ink-muted)]">Search results and citation snippets appear here.</p>
              ) : null}
              {results.map((r, i) => (
                <CitationCard key={`${r.chunk_id}-${r.score}`} citation={r} index={i + 1} />
              ))}
            </div>
          </div>

          {selected ? (
            <div className="panel p-5">
              <div className="flex items-center justify-between gap-3">
                <h3 className="font-semibold">Citation viewer · {selected.title}</h3>
                <Button variant="ghost" onClick={() => setSelected(null)}>
                  Close
                </Button>
              </div>
              <p className="mt-3 whitespace-pre-wrap text-sm text-[var(--color-ink-muted)] leading-relaxed max-h-96 overflow-auto">
                {selected.content}
              </p>
            </div>
          ) : null}
        </div>
      </div>

      <Modal
        open={!!deleteId}
        onClose={() => setDeleteId(null)}
        title="Delete document?"
        footer={
          <>
            <Button variant="secondary" onClick={() => setDeleteId(null)}>
              Cancel
            </Button>
            <Button variant="danger" onClick={remove}>
              Delete
            </Button>
          </>
        }
      >
        <p className="text-sm text-[var(--color-ink-muted)]">This removes the document and its vector chunks.</p>
      </Modal>
    </div>
  )
}
