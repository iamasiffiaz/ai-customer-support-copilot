import Button from './Button.jsx'
import Select from './Select.jsx'
import Textarea from './Textarea.jsx'
import Badge from './Badge.jsx'
import { REPLY_TONES } from '../utils/constants'
import toast from 'react-hot-toast'

const STEPS = ['drafted', 'edited', 'approved', 'sent']

export default function ReplyEditor({
  value,
  tone,
  status,
  onChange,
  onToneChange,
  onGenerate,
  onRegenerate,
  onSaveDraft,
  onApprove,
  onMarkSent,
  loading,
  insufficientContext,
}) {
  const current = (status || 'drafted').toLowerCase()
  const stepIndex = Math.max(0, STEPS.indexOf(current === 'drafted' ? 'drafted' : current))

  return (
    <div className="panel overflow-hidden">
      <div className="panel-header !items-end">
        <div>
          <h3>AI reply workspace</h3>
          <p className="text-sm text-[var(--muted)] mt-0.5 font-normal">
            Generate → edit → approve → send. Humans stay in control.
          </p>
        </div>
        <Select
          label="Tone"
          value={tone}
          onChange={(e) => onToneChange(e.target.value)}
          options={REPLY_TONES}
          className="min-w-[170px] !mb-0"
        />
      </div>

      <div className="panel-body space-y-4">
        <div className="grid grid-cols-4 gap-2" role="list" aria-label="Reply lifecycle">
          {STEPS.map((step, i) => (
            <div
              key={step}
              role="listitem"
              className={`rounded-lg px-2 py-2 text-center text-[11px] font-bold uppercase tracking-wide ${
                i <= stepIndex
                  ? 'bg-[var(--emerald)] text-white'
                  : 'bg-[var(--surface)] text-[var(--muted)] border border-[var(--border)]'
              }`}
            >
              {step}
            </div>
          ))}
        </div>

        {insufficientContext ? (
          <div className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">
            Limited knowledge base context — verify policy before approving.
          </div>
        ) : null}

        <Textarea label="Reply draft" rows={11} value={value} onChange={(e) => onChange(e.target.value)} />

        <div className="flex flex-wrap gap-2">
          <Button onClick={onGenerate} disabled={loading}>
            {loading ? 'Generating…' : 'Generate AI Reply'}
          </Button>
          <Button variant="secondary" onClick={onRegenerate || onGenerate} disabled={loading}>
            Regenerate
          </Button>
          <Button variant="secondary" onClick={onSaveDraft} disabled={loading || !value}>
            Save Draft
          </Button>
          <Button variant="secondary" onClick={onApprove} disabled={loading || !value}>
            Approve Reply
          </Button>
          <Button onClick={onMarkSent} disabled={loading || !value}>
            Mark as Sent
          </Button>
          <Button
            variant="ghost"
            onClick={() => {
              navigator.clipboard.writeText(value || '')
              toast.success('Reply copied')
            }}
            disabled={!value}
          >
            Copy
          </Button>
          {status ? <Badge tone="accent" className="self-center ml-auto">{status}</Badge> : null}
        </div>
      </div>
    </div>
  )
}
