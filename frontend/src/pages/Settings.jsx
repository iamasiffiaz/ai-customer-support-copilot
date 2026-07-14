import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { settingsApi } from '../api/client'
import Button from '../components/Button.jsx'
import Input from '../components/Input.jsx'
import Select from '../components/Select.jsx'
import LoadingSpinner from '../components/LoadingSpinner.jsx'
import { REPLY_TONES, TEAMS } from '../utils/constants'

export default function Settings() {
  const [form, setForm] = useState(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    settingsApi
      .get()
      .then(setForm)
      .catch(() => toast.error('Failed to load settings'))
      .finally(() => setLoading(false))
  }, [])

  const save = async () => {
    setSaving(true)
    try {
      const updated = await settingsApi.update({
        business_name: form.business_name,
        support_email: form.support_email,
        default_reply_tone: form.default_reply_tone,
        sla_urgent_hours: Number(form.sla_urgent_hours),
        sla_high_hours: Number(form.sla_high_hours),
        sla_medium_hours: Number(form.sla_medium_hours),
        sla_low_hours: Number(form.sla_low_hours),
        ai_provider: form.ai_provider,
        api_key_placeholder: form.api_key_placeholder,
        chat_model: form.chat_model,
        embedding_model: form.embedding_model,
        default_escalation_team: form.default_escalation_team,
      })
      setForm(updated)
      toast.success('Settings saved')
    } catch {
      toast.error('Save failed')
    } finally {
      setSaving(false)
    }
  }

  if (loading || !form) return <LoadingSpinner label="Loading settings…" />

  const set = (key) => (e) => setForm({ ...form, [key]: e.target.value })

  return (
    <div className="space-y-5 max-w-3xl">
      <div>
        <h2 className="font-display text-3xl">Settings</h2>
        <p className="text-[var(--color-ink-muted)] mt-1">Business defaults, SLA rules, and AI provider placeholders.</p>
      </div>

      <div className="rounded-2xl border border-[var(--color-line)] bg-white p-5 space-y-4">
        <Input label="Business name" value={form.business_name} onChange={set('business_name')} />
        <Input label="Support email" value={form.support_email} onChange={set('support_email')} />
        <Select
          label="Default reply tone"
          value={form.default_reply_tone}
          onChange={set('default_reply_tone')}
          options={REPLY_TONES}
        />
        <Select
          label="Default escalation team"
          value={form.default_escalation_team}
          onChange={set('default_escalation_team')}
          options={TEAMS}
        />

        <div className="grid gap-3 sm:grid-cols-2">
          <Input label="SLA urgent (hours)" type="number" value={form.sla_urgent_hours} onChange={set('sla_urgent_hours')} />
          <Input label="SLA high (hours)" type="number" value={form.sla_high_hours} onChange={set('sla_high_hours')} />
          <Input label="SLA medium (hours)" type="number" value={form.sla_medium_hours} onChange={set('sla_medium_hours')} />
          <Input label="SLA low (hours)" type="number" value={form.sla_low_hours} onChange={set('sla_low_hours')} />
        </div>

        <Input label="AI provider" value={form.ai_provider} onChange={set('ai_provider')} />
        <Input
          label="API key placeholder"
          value={form.api_key_placeholder || ''}
          onChange={set('api_key_placeholder')}
          placeholder="Stored in settings UI only — use .env for real keys"
        />
        <Input label="Chat model" value={form.chat_model} onChange={set('chat_model')} />
        <Input label="Embedding model" value={form.embedding_model} onChange={set('embedding_model')} />

        <Button onClick={save} disabled={saving}>
          {saving ? 'Saving…' : 'Save settings'}
        </Button>
      </div>
    </div>
  )
}
