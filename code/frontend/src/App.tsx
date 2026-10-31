import { useEffect, useState } from 'react'

type Portfolio = {
  available: boolean
  reason: string | null
  cash: string | null
  equity: string | null
  positions: Array<Record<string, string>>
  orders: Array<Record<string, string>>
}

type ControlSurface = {
  observed_at: string
  source: string
  freshness: string
  modules: Array<{ name: string; status: string; last_run: string | null; error_summary: string | null }>
  runtime: Record<string, string>
  config: Record<string, unknown>
  events: Array<Record<string, string>>
}

type Snapshot = {
  observed_at: string
  source: string
  freshness: string
  portfolio: Portfolio
  watchlist: Array<Record<string, string>>
  events: Array<Record<string, string>>
  modules: Record<string, string>
}

const apiBase = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

function StatusPill({ children, tone = 'quiet' }: { children: string; tone?: 'quiet' | 'good' | 'warn' }) {
  return <span className={`pill pill-${tone}`}><span className="dot" />{children}</span>
}

function EmptyPanel({ title, reason }: { title: string; reason: string }) {
  return <div className="empty"><strong>{title}</strong><span>{reason}</span></div>
}

export function App() {
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null)
  const [controlSurface, setControlSurface] = useState<ControlSurface | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [controlError, setControlError] = useState<string | null>(null)
  const [updatedAt, setUpdatedAt] = useState<Date | null>(null)

  useEffect(() => {
    let active = true
    const refresh = async () => {
      try {
        const [dashboardResponse, controlResponse] = await Promise.all([
          fetch(`${apiBase}/api/dashboard`),
          fetch(`${apiBase}/api/control-surface`),
        ])
        if (!dashboardResponse.ok) throw new Error(`Dashboard responded ${dashboardResponse.status}`)
        const next = (await dashboardResponse.json()) as Snapshot
        if (active) {
          setSnapshot(next)
          setError(null)
          if (controlResponse.ok) {
            setControlSurface((await controlResponse.json()) as ControlSurface)
            setControlError(null)
          } else {
            setControlError(`Control surface responded ${controlResponse.status}`)
          }
          setUpdatedAt(new Date())
        }
      } catch (requestError) {
        if (active) setError(requestError instanceof Error ? requestError.message : 'Backend unavailable')
      }
    }
    refresh()
    const timer = window.setInterval(refresh, 15_000)
    return () => { active = false; window.clearInterval(timer) }
  }, [])

  const portfolio = snapshot?.portfolio
  return (
    <main>
      <header className="topbar">
        <a className="brand" href="/">TA<span>/</span>cockpit</a>
        <div className="top-meta"><StatusPill tone={error ? 'warn' : snapshot ? 'good' : 'quiet'}>{error ? 'backend offline' : snapshot ? 'read-only link' : 'connecting'}</StatusPill><span>refresh 15s</span></div>
      </header>
      <section className="hero">
        <div><p className="kicker">Trading Agent · observability</p><h1>See what is true<br /><em>before you act.</em></h1><p className="lede">A quiet surface for portfolio state, source freshness, and the work still waiting to be connected.</p></div>
        <div className="signal"><span className="signal-line" /><span>paper system<br /><b>read only</b></span></div>
      </section>
      {error && <div className="alert"><strong>Data source unavailable.</strong><span>{error}. The view stays honest and does not substitute demo values.</span></div>}
      <section className="section-grid">
        <div className="section-head"><span>Portfolio</span><StatusPill tone={portfolio?.available ? 'good' : 'quiet'}>{portfolio?.available ? 'connected' : 'not connected'}</StatusPill></div>
        <div className="metric-grid">
          <article className="metric"><span>Equity</span><strong>{portfolio?.equity ?? '—'}</strong><small>{snapshot?.freshness ?? 'waiting for source'}</small></article>
          <article className="metric"><span>Cash</span><strong>{portfolio?.cash ?? '—'}</strong><small>cash, not buying power</small></article>
          <article className="metric"><span>Positions</span><strong>{portfolio?.positions.length ?? '—'}</strong><small>open holdings</small></article>
        </div>
        {!portfolio?.available && <EmptyPanel title="Portfolio read model is not connected" reason={portfolio?.reason ?? 'Loading the Python backend read model.'} />}
      </section>
      <section className="split-grid">
        <article className="panel"><div className="section-head"><span>Watchlist</span><span className="muted">universe</span></div>{snapshot?.watchlist.length ? <p>{snapshot.watchlist.length} symbols</p> : <EmptyPanel title="No watchlist data" reason="The persistent read model will provide symbols and their last analysis." />}</article>
        <article className="panel"><div className="section-head"><span>System map</span><span className="muted">capabilities</span></div><ul className="capabilities">{Object.entries(snapshot?.modules ?? {portfolio: 'loading', decisions: 'loading', benchmark: 'loading'}).map(([name, state]) => <li key={name}><span>{name.replace('_', ' ')}</span><StatusPill tone={state === 'unavailable' || state === 'post-mvp' ? 'quiet' : 'good'}>{state}</StatusPill></li>)}</ul></article>
      </section>
      <section className="section-grid">
        <div className="section-head"><span>Control surface</span><StatusPill tone={controlError ? 'warn' : controlSurface ? 'quiet' : 'quiet'}>{controlError ? 'unavailable' : controlSurface?.runtime.status ?? 'loading'}</StatusPill></div>
        {controlError && <div className="alert"><strong>Control plane unavailable.</strong><span>{controlError}. Observation only; no controls are exposed.</span></div>}
        <div className="split-grid control-grid">
          <article className="panel"><div className="section-head"><span>Modules</span><span className="muted">runtime</span></div>{controlSurface?.modules.length ? <ul className="capabilities">{controlSurface.modules.map((module) => <li key={module.name}><span>{module.name}</span><StatusPill tone={module.status === 'healthy' ? 'good' : 'quiet'}>{module.status}</StatusPill></li>)}</ul> : <EmptyPanel title="No module health yet" reason={controlSurface?.runtime.reason ?? 'Waiting for the runtime read model.'} />}</article>
          <article className="panel"><div className="section-head"><span>Recent events</span><span className="muted">observed</span></div>{controlSurface?.events.length ? <p>{controlSurface.events.length} events</p> : <EmptyPanel title="No events available" reason="Events will appear when the persisted read model is connected." />}</article>
        </div>
        <p className="source-note">source: {controlSurface?.source ?? 'not available'} · freshness: {controlSurface?.freshness ?? 'not available'} · configuration is observed, never changed here</p>
      </section>
      <footer><span>source: {snapshot?.source ?? 'not available'}</span><span>{updatedAt ? `checked ${updatedAt.toLocaleTimeString()}` : 'waiting for first check'}</span><span>no broker writes</span></footer>
    </main>
  )
}
