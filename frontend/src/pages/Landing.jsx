import { Link } from 'react-router-dom'

const features = [
  {
    title: 'AI ticket analysis',
    body: 'Summarize intent, detect sentiment, classify priority, and flag escalation risk in one pass.',
  },
  {
    title: 'Human-approved replies',
    body: 'Generate empathetic drafts with RAG citations, then edit, approve, and mark sent.',
  },
  {
    title: 'Knowledge base RAG',
    body: 'Upload policies, retrieve relevant chunks, and ground every answer in your docs.',
  },
  {
    title: 'Escalation detection',
    body: 'Catch cancellation, refund, legal, security, and SLA risk before customers churn.',
  },
]

const useCases = [
  'SaaS companies handling billing and product tickets',
  'Ecommerce stores managing refunds and delivery issues',
  'Agencies operating shared inboxes for clients',
  'Support teams prioritizing urgent conversations',
]

const plans = [
  {
    name: 'Starter',
    price: '$49',
    detail: 'For early support teams',
    items: ['Ticket inbox', 'AI analysis', 'Reply drafts', 'Basic analytics'],
  },
  {
    name: 'Growth',
    price: '$149',
    detail: 'For scaling SaaS support',
    items: ['Everything in Starter', 'Knowledge base RAG', 'Escalation routing', 'Copilot chat'],
    featured: true,
  },
  {
    name: 'Scale',
    price: '$349',
    detail: 'For multi-team operations',
    items: ['Everything in Growth', 'SLA risk views', 'Recommendations', 'Priority support'],
  },
]

export default function Landing() {
  return (
    <div className="min-h-screen hero-atmosphere text-[var(--ink)] landing-grid">
      <header className="mx-auto flex max-w-6xl items-center justify-between px-5 py-5">
        <div className="flex items-center gap-3">
          <div className="brand-mark">SC</div>
          <div>
            <p className="font-display text-xl leading-none tracking-tight">Support Copilot</p>
            <p className="text-[11px] text-[var(--muted)] uppercase tracking-[0.14em] mt-1">Enterprise Trust</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <a href="#features" className="hidden sm:inline text-sm text-[var(--muted)] hover:text-[var(--emerald-strong)]">
            Features
          </a>
          <Link to="/dashboard" className="btn btn-primary">
            Open workspace
          </Link>
        </div>
      </header>

      <section className="relative mx-auto max-w-6xl px-5 pb-20 pt-12 md:pt-16">
        <p className="animate-fade-up text-[0.7rem] font-bold uppercase tracking-[0.18em] text-[var(--emerald-strong)]">
          AI customer support operations
        </p>
        <p className="font-display animate-fade-up animate-delay-1 text-5xl md:text-7xl leading-[0.95] tracking-tight max-w-3xl mt-4 text-[var(--navy)]">
          Support Copilot
        </p>
        <h1 className="animate-fade-up animate-delay-2 mt-6 max-w-2xl text-2xl md:text-3xl font-semibold leading-snug text-[var(--ink)]">
          The agent console that drafts answers — while your team keeps the send button
        </h1>
        <p className="animate-fade-up animate-delay-3 mt-4 max-w-xl text-[var(--muted)] text-lg leading-relaxed">
          Analyze tickets, detect frustrated customers, retrieve policy answers with RAG, and approve every AI reply
          before it goes out.
        </p>
        <div className="animate-fade-up animate-delay-3 mt-8 flex flex-wrap gap-3">
          <Link to="/dashboard" className="btn btn-primary !px-5 !py-3">
            Launch live demo
          </Link>
          <a href="#pricing" className="btn btn-secondary !px-5 !py-3">
            View pricing
          </a>
        </div>
        <div className="mt-14 ops-strip max-w-xl">
          <span className="live-dot" />
          <p className="text-sm text-[var(--ink)]">
            Built for <strong>support ops</strong> — not another generic AI chatbot landing page.
          </p>
        </div>
      </section>

      <section id="features" className="mx-auto max-w-6xl px-5 py-16">
        <h2 className="font-display text-3xl md:text-4xl text-[var(--navy)]">Built like a support product</h2>
        <p className="mt-3 max-w-2xl text-[var(--muted)]">
          Clear hierarchy, status coding, and approval workflows agents already understand.
        </p>
        <div className="mt-10 grid gap-6 md:grid-cols-2">
          {features.map((f) => (
            <div key={f.title} className="panel p-5 border-l-4 border-l-[var(--emerald)]">
              <h3 className="text-lg font-semibold text-[var(--ink)]">{f.title}</h3>
              <p className="mt-2 text-[var(--muted)] leading-relaxed">{f.body}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-5 py-16">
        <h2 className="font-display text-3xl md:text-4xl text-[var(--navy)]">Use cases</h2>
        <p className="mt-3 text-[var(--muted)]">For teams that live in the inbox every day.</p>
        <ul className="mt-8 space-y-3">
          {useCases.map((item) => (
            <li key={item} className="flex gap-3 text-[var(--ink)]">
              <span className="mt-2 h-1.5 w-1.5 rounded-full bg-[var(--emerald)] shrink-0" />
              <span>{item}</span>
            </li>
          ))}
        </ul>
      </section>

      <section id="pricing" className="mx-auto max-w-6xl px-5 py-16">
        <h2 className="font-display text-3xl md:text-4xl text-[var(--navy)]">Pricing</h2>
        <p className="mt-3 text-[var(--muted)]">Simple plans for demos and pilot rollouts.</p>
        <div className="mt-10 grid gap-6 md:grid-cols-3">
          {plans.map((plan) => (
            <div
              key={plan.name}
              className={`panel p-6 ${plan.featured ? 'ring-2 ring-[var(--emerald)]' : ''}`}
            >
              <p className="text-xs uppercase tracking-wide text-[var(--muted)] font-semibold">{plan.name}</p>
              <p className="mt-2 font-display text-4xl text-[var(--navy)]">
                {plan.price}
                <span className="text-base font-sans text-[var(--muted)]">/mo</span>
              </p>
              <p className="mt-2 text-sm text-[var(--muted)]">{plan.detail}</p>
              <ul className="mt-5 space-y-2 text-sm text-[var(--ink)]">
                {plan.items.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
              <Link
                to="/dashboard"
                className={`mt-6 inline-flex btn ${plan.featured ? 'btn-primary' : 'btn-secondary'}`}
              >
                Start free demo
              </Link>
            </div>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-5 py-20">
        <div className="rounded-[calc(var(--radius)+8px)] bg-[var(--navy)] px-8 py-12 text-white relative overflow-hidden">
          <div className="absolute right-0 top-0 w-56 h-56 rounded-full bg-[var(--emerald)]/20 blur-3xl" />
          <p className="font-display text-3xl md:text-4xl max-w-xl relative">
            Ready to cut response time without losing quality?
          </p>
          <p className="mt-3 max-w-lg text-slate-400 relative">
            Open the demo workspace and walk through analysis, RAG replies, escalations, and approval workflows.
          </p>
          <Link to="/dashboard" className="btn btn-primary mt-6 relative">
            Enter the dashboard
          </Link>
        </div>
      </section>
    </div>
  )
}
