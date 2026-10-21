import { useEffect, useState } from 'react'
import { getHealth, getMetrics, predict, traceNlp } from './api/client'
import { Icon } from './components/Icon'
import type { IconName } from './components/Icon'
import { useAnalysis, useRemote } from './hooks/useRemote'
import { reviewProblem } from './lib/format'
import { AboutPage } from './pages/AboutPage'
import { ModelsPage } from './pages/ModelsPage'
import { NlpLabPage } from './pages/NlpLabPage'
import { PredictPage } from './pages/PredictPage'
import './App.css'

const navigation: { id: string; name: string; icon: IconName }[] = [
  { id: 'prediccion', name: 'Predicción', icon: 'analyze' },
  { id: 'laboratorio', name: 'Laboratorio NLP', icon: 'nlp' },
  { id: 'modelos', name: 'Modelos y métricas', icon: 'chart' },
  { id: 'metodologia', name: 'Metodología', icon: 'book' },
]
const currentPage = () =>
  navigation.some((item) => item.id === window.location.hash.replace(/^#\/?/, ''))
    ? window.location.hash.replace(/^#\/?/, '')
    : 'prediccion'

function App() {
  const [page, setPage] = useState(currentPage)
  const [text, setText] = useState('')
  const health = useRemote(getHealth)
  const metrics = useRemote(getMetrics)
  const prediction = useAnalysis(predict)
  const trace = useAnalysis(traceNlp)
  const reloadHealth = health.reload

  useEffect(() => {
    const navigate = () => setPage(currentPage())
    window.addEventListener('hashchange', navigate)
    return () => window.removeEventListener('hashchange', navigate)
  }, [])
  useEffect(() => {
    document.title = `${navigation.find((item) => item.id === page)?.name} · ReviewIQ`
    window.scrollTo({ top: 0 })
    document.querySelector<HTMLElement>('main h1')?.focus({ preventScroll: true })
  }, [page])
  useEffect(() => {
    const refresh = () => {
      if (document.visibilityState === 'visible') void reloadHealth()
    }
    const timer = window.setInterval(refresh, 30_000)
    document.addEventListener('visibilitychange', refresh)
    return () => {
      clearInterval(timer)
      document.removeEventListener('visibilitychange', refresh)
    }
  }, [reloadHealth])

  function changeText(value: string) {
    setText(value)
    prediction.reset()
    trace.reset()
  }
  function refreshIdentity(modelId: string) {
    if (health.data?.model_id !== modelId) void health.reload()
    if (metrics.data?.model_id !== modelId) void metrics.reload()
  }
  async function analyze() {
    if (reviewProblem(text)) return
    const result = await prediction.run(text)
    if (result) {
      refreshIdentity(result.model_id)
      requestAnimationFrame(() => document.getElementById('analysis-result-title')?.focus())
    } else void health.reload()
  }
  async function analyzeTrace() {
    if (reviewProblem(text)) return
    const result = await trace.run(text)
    if (result) {
      refreshIdentity(result.model_id)
      requestAnimationFrame(() => document.getElementById('trace-result-title')?.focus())
    } else void health.reload()
  }
  const online = Boolean(health.data)
  const statusLabel = health.pending
    ? 'Comprobando servicio'
    : online
      ? 'API conectada'
      : health.error?.code === 'model_unavailable'
        ? 'Modelo no disponible'
        : 'Sin conexión'
  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">
        Saltar al contenido
      </a>
      <aside className="sidebar">
        <a href="#/prediccion" className="brand" aria-label="ReviewIQ, ir a predicción">
          <span className="brand-symbol">
            <Icon name="star" />
          </span>
          <span>
            Review<span className="brand-iq">IQ</span>
            <small>Análisis de reseñas</small>
          </span>
        </a>
        <span className="nav-caption">ESPACIO DE ANÁLISIS</span>
        <nav aria-label="Navegación principal">
          {navigation.map((item) => (
            <a
              key={item.id}
              href={`#/${item.id}`}
              aria-current={page === item.id ? 'page' : undefined}
              className={page === item.id ? 'active' : ''}
            >
              <Icon name={item.icon} />
              <span>{item.name}</span>
            </a>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="sidebar-domain">
            <span>1</span>
            <span>2</span>
            <span>3</span>
            <span>4</span>
            <span>
              5<Icon name="star" />
            </span>
          </div>
          <strong>De texto a evidencia</strong>
          <p>
            Modelos clásicos.
            <br />
            Sin historial de reseñas.
          </p>
          <span className="academic-label">PROYECTO ACADÉMICO</span>
        </div>
      </aside>
      <div className="workspace">
        <header className="topbar">
          <div className="breadcrumb">
            <span>ReviewIQ</span>
            <span aria-hidden="true">/</span>
            <strong>{navigation.find((item) => item.id === page)?.name}</strong>
          </div>
          <div className="connection">
            <span
              className={`connection-indicator ${health.pending ? 'checking' : online ? 'connected' : 'disconnected'}`}
              aria-hidden="true"
            />
            <span role="status">
              {statusLabel}
              {online && health.data?.mode === 'quick' && ' · Quick'}
            </span>
            <button
              className="icon-button"
              disabled={health.pending}
              onClick={() => {
                void health.reload()
                void metrics.reload()
              }}
              aria-label="Comprobar conexión"
              title="Comprobar conexión"
            >
              <Icon name="refresh" />
            </button>
          </div>
        </header>
        <main className="content" id="main-content" tabIndex={-1}>
          {page === 'prediccion' && (
            <PredictPage
              text={text}
              onChange={changeText}
              onSubmit={() => void analyze()}
              pending={prediction.pending}
              result={prediction.data}
              error={prediction.error}
              inspect={() => {
                window.location.hash = '/laboratorio'
                if (!trace.data || trace.data.model_id !== prediction.data?.model_id)
                  void analyzeTrace()
              }}
            />
          )}
          {page === 'laboratorio' && (
            <NlpLabPage
              text={text}
              onChange={changeText}
              onSubmit={() => void analyzeTrace()}
              pending={trace.pending}
              result={trace.data}
              error={trace.error}
              metrics={metrics.data}
            />
          )}
          {page === 'modelos' && (
            <ModelsPage
              key={metrics.data?.model_id || 'metrics'}
              data={metrics.data}
              pending={metrics.pending}
              error={metrics.error}
              reload={() => void metrics.reload()}
            />
          )}
          {page === 'metodologia' && <AboutPage />}
        </main>
        <footer className="app-footer">
          <span>ReviewIQ · Análisis comercial en español</span>
          <span>
            {health.data ? (
              <>
                <span className="footer-mode">
                  {health.data.mode === 'full' ? 'Modelo completo' : 'Modelo rápido experimental'}
                </span>
                <code>{health.data.model_id}</code>
              </>
            ) : (
              'Servicio sin verificar'
            )}
          </span>
        </footer>
      </div>
    </div>
  )
}

export default App
