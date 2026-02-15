import { useState, useEffect, useRef, useCallback } from 'react'

const API_BASE = import.meta.env.VITE_API_BASE || ''

// ---- Icons ----
const IconRocket = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
    <path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z"/>
    <path d="m12 15-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"/>
    <path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0"/>
    <path d="M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5"/>
  </svg>
)

const IconDownload = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
    <polyline points="7 10 12 15 17 10"/>
    <line x1="12" y1="15" x2="12" y2="3"/>
  </svg>
)

const IconCheck = () => (
  <svg width={18} height={18} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5} strokeLinecap="round" strokeLinejoin="round">
    <polyline points="20 6 9 17 4 12"/>
  </svg>
)

function formatTokens(n) {
  if (n >= 1000) return `${(n / 1000).toFixed(1)}k`
  return String(n)
}

// ---- Content rendering with CE markers ----
function renderContent(content) {
  if (!content) return null
  return content.split('\n').flatMap((line, i) => {
    const ceMatch = line.match(/<!--\s*CE:\s*(\S+)\s*-->/)
    if (ceMatch) {
      return [
        <span key={`ce-${i}`} className="ce-marker">CE: {ceMatch[1]}</span>,
        <br key={`br-${i}`} />
      ]
    }
    return [<span key={i}>{line}{'\n'}</span>]
  })
}

// ---- Main App ----
export default function App() {
  const [company, setCompany] = useState('')
  const [jobId, setJobId] = useState(null)
  const [status, setStatus] = useState(null)
  const [progress, setProgress] = useState(0)
  const [pagesDone, setPagesDone] = useState(0)
  const [currentPage, setCurrentPage] = useState('')
  const [completedPages, setCompletedPages] = useState([])
  const [pages, setPages] = useState([])
  const [selectedPage, setSelectedPage] = useState(null)
  const [error, setError] = useState(null)
  const [tokens, setTokens] = useState({ input: 0, output: 0, cost: 0, duration: 0 })
  const [elapsed, setElapsed] = useState(0)
  const startTimeRef = useRef(null)
  const timerRef = useRef(null)
  const eventSourceRef = useRef(null)

  const loadPages = useCallback(async (jid) => {
    try {
      const res = await fetch(`${API_BASE}/api/jobs/${jid}/pages`)
      const data = await res.json()
      if (data.pages?.length > 0) {
        setPages(data.pages)
        setSelectedPage(data.pages[0])
      }
    } catch (err) {
      console.error('Failed to load pages:', err)
    }
  }, [])

  const pollStatus = useCallback(async (jid) => {
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/api/jobs/${jid}`)
        const data = await res.json()
        setStatus(data.status)
        setProgress(data.progress)
        setPagesDone(data.pages_done)
        if (data.current_page) setCurrentPage(data.current_page)
        setTokens(t => ({ ...t, input: data.input_tokens, output: data.output_tokens, cost: data.cost_usd }))

        if (data.status === 'completed') { clearInterval(interval); loadPages(jid) }
        else if (data.status === 'failed') { clearInterval(interval); setError(data.error || 'Generation fehlgeschlagen') }
      } catch { clearInterval(interval) }
    }, 2000)
  }, [loadPages])

  const handleGenerate = useCallback(async () => {
    if (!company.trim()) return

    setError(null); setStatus('pending'); setProgress(0)
    setPagesDone(0); setCurrentPage(''); setCompletedPages([]); setPages([]); setSelectedPage(null)
    setTokens({ input: 0, output: 0, cost: 0, duration: 0 })
    startTimeRef.current = Date.now()
    setElapsed(0)

    timerRef.current = setInterval(() => {
      setElapsed(Math.floor((Date.now() - startTimeRef.current) / 1000))
    }, 1000)

    try {
      const res = await fetch(`${API_BASE}/api/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ company: company.trim() }),
      })

      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setJobId(data.job_id)
      setStatus('running')

      const es = new EventSource(`${API_BASE}/api/jobs/${data.job_id}/events`)
      eventSourceRef.current = es

      es.onmessage = (event) => {
        const msg = JSON.parse(event.data)

        if (msg.type === 'log' && msg.event) {
          const evt = msg.event
          if (evt.event === 'page_done') {
            setCompletedPages(prev => [...prev, evt.title])
          }
        }

        if (msg.type === 'status') {
          setStatus(msg.status); setProgress(msg.progress); setPagesDone(msg.pages_done)
          if (msg.current_page) setCurrentPage(msg.current_page)
          setTokens(t => ({
            ...t,
            input: msg.input_tokens || t.input,
            output: msg.output_tokens || t.output,
            cost: msg.cost_usd || t.cost,
          }))
        }

        if (msg.type === 'done') {
          es.close()
          clearInterval(timerRef.current)
          if (msg.status === 'completed') {
            setStatus('completed'); setProgress(100)
            setTokens({
              input: msg.input_tokens || 0,
              output: msg.output_tokens || 0,
              cost: msg.cost_usd || 0,
              duration: msg.duration_sec || 0,
            })
            loadPages(data.job_id)
          } else {
            setStatus('failed'); setError(msg.error || 'Generation fehlgeschlagen')
          }
        }
      }

      es.onerror = () => { es.close(); pollStatus(data.job_id) }

    } catch (err) {
      clearInterval(timerRef.current)
      setError(`Verbindungsfehler: ${err.message}. Läuft das Backend auf ${API_BASE || 'localhost:8000'}?`)
      setStatus(null)
    }
  }, [company, loadPages, pollStatus])

  useEffect(() => {
    return () => {
      if (eventSourceRef.current) eventSourceRef.current.close()
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [])

  const isRunning = status === 'pending' || status === 'running'
  const isCompleted = status === 'completed'

  return (
    <div className="app-container">
      <header className="header">
        <div className="header-badge">
          <span className="dot" />
          TYPO3 Content Generator
        </div>
        <h1>T3 Content <em>Library</em></h1>
        <p>Generiere 20 realistische TYPO3-Seiten mit KI-generierten Inhalten auf Basis deiner Firmenbeschreibung.</p>
      </header>

      <section className="input-section">
        <label className="input-label" htmlFor="company-input">Firma / Thema</label>
        <div className="input-row">
          <input
            id="company-input"
            className="input-field"
            type="text"
            placeholder="z.B. Italienisches Restaurant La Bella Vista in München"
            value={company}
            onChange={e => setCompany(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && !isRunning && handleGenerate()}
            disabled={isRunning}
          />
          <button className="btn-generate" onClick={handleGenerate} disabled={isRunning || !company.trim()}>
            {isRunning
              ? <><span className="spinner" />Generiert...</>
              : <><IconRocket />Generieren</>
            }
          </button>
        </div>
      </section>

      {error && <div className="error-box">{error}</div>}

      {isRunning && (
        <section className="progress-section">
          <div className="progress-header">
            <div className="progress-title"><span className="spinner" />Seiten werden generiert</div>
            <span className="progress-pct">{progress}%</span>
          </div>
          <div className="progress-bar-track">
            <div className="progress-bar-fill" style={{ width: `${Math.max(progress, 2)}%` }} />
          </div>
          <div className="progress-stats">
            <span>{pagesDone}/20 Seiten</span>
            <span>{elapsed}s</span>
            {tokens.input > 0 && <span>{formatTokens(tokens.input + tokens.output)} Tokens</span>}
          </div>

          {completedPages.length > 0 && (
            <div className="page-chips">
              {completedPages.map((title, i) => (
                <span key={i} className="page-chip done">
                  <IconCheck />{title}
                </span>
              ))}
              {pagesDone < 20 && currentPage && (
                <span className="page-chip active">
                  <span className="spinner-sm" />{currentPage}
                </span>
              )}
            </div>
          )}
        </section>
      )}

      {isCompleted && pages.length > 0 && (
        <section className="results-section">
          <div className="results-header">
            <div className="results-title">
              <IconCheck />
              Generierte Seiten
              <span className="results-count">{pages.length} Seiten</span>
            </div>
            <a className="btn-download" href={`${API_BASE}/api/jobs/${jobId}/download`} download>
              <IconDownload />Als ZIP herunterladen
            </a>
          </div>

          <div className="stats-bar">
            <div className="stat-item">
              <span className="stat-label">Dauer</span>
              <span className="stat-value">{tokens.duration.toFixed(1)}s</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Input Tokens</span>
              <span className="stat-value">{tokens.input.toLocaleString()}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Output Tokens</span>
              <span className="stat-value">{tokens.output.toLocaleString()}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Kosten</span>
              <span className="stat-value cost">${tokens.cost.toFixed(4)}</span>
            </div>
          </div>

          <div className="pages-layout">
            <div className="page-list">
              {pages.map((page, i) => (
                <div
                  key={i}
                  className={`page-item ${selectedPage === page ? 'active' : ''}`}
                  onClick={() => setSelectedPage(page)}
                >
                  <div className="page-item-title">{page.title}</div>
                  <div className="page-item-meta">{page.slug || page.filename}</div>
                </div>
              ))}
            </div>

            <div className="page-preview">
              {selectedPage ? (
                <>
                  <div className="preview-meta">
                    {selectedPage.slug && <span className="meta-tag">/{selectedPage.slug}</span>}
                    {selectedPage.layout && <span className="meta-tag layout">{selectedPage.layout}</span>}
                    {selectedPage.meta?.nav_position != null && <span className="meta-tag">Nav: {selectedPage.meta.nav_position}</span>}
                    <span className="meta-tag">{selectedPage.filename}</span>
                  </div>
                  <h2 className="preview-title">{selectedPage.title}</h2>
                  <div className="preview-content">{renderContent(selectedPage.content)}</div>
                </>
              ) : (
                <div className="preview-empty">Seite auswählen, um Vorschau zu sehen</div>
              )}
            </div>
          </div>
        </section>
      )}
    </div>
  )
}
